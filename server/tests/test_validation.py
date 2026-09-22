import json

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"

SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _full_setup(client) -> tuple[str, str]:
    """Case + dataset + profile + run + finding. Returns case and finding ids."""
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
    ).json()["id"]
    finding_id = client.post(
        f"/cases/{case_id}/findings",
        json={"run_id": run_id, "statement": "North leads revenue"},
    ).json()["id"]
    return case_id, finding_id


def test_validate_supported(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, finding_id = _full_setup(client)
        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200
    body = result.json()
    assert body["status"] == "supported"
    check_names = {c["name"]: c["passed"] for c in body["checks"]}
    assert check_names["calculation"] is True
    assert check_names["data"] is True
    assert check_names["evidence"] is True

    # The finding's own status must reflect the validation outcome.
    with TestClient(app) as client:
        finding = client.get(f"/cases/{case_id}/findings/{finding_id}")
    assert finding.json()["validation_status"] == "supported"


def test_validate_partially_supported_when_nulls_exist(tmp_path) -> None:
    _temp_env(tmp_path)

    messy = b"order_id,revenue,region\n1,125.0,north\n2,,south\n3,200.0,north\n"
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "m.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("m.csv", messy, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        ).json()["id"]
        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "North leads revenue"},
        ).json()["id"]

        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200
    assert result.json()["status"] == "partially_supported"
    checks = {c["name"]: c for c in result.json()["checks"]}
    assert checks["calculation"]["passed"] is True
    assert checks["data"]["passed"] is False


def test_validate_fails_when_result_drifts(tmp_path) -> None:
    """The core guarantee: if the persisted result no longer matches a rerun,
    validation must not mark the finding supported."""
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, finding_id = _full_setup(client)
        run_id = client.get(f"/cases/{case_id}/findings/{finding_id}").json()["run_id"]

        # Corrupt the stored result so the rerun cannot match it.
        with get_connection(db_module.DATA_DIR.parent / "test.db") as conn:
            conn.execute(
                "UPDATE runs SET rows_json = ? WHERE id = ?",
                (json.dumps([["north", 999.0]]), run_id),
            )
            conn.commit()

        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200
    assert result.json()["status"] == "insufficient_evidence"
    checks = {c["name"]: c for c in result.json()["checks"]}
    assert checks["calculation"]["passed"] is False


def test_validate_accepts_reordered_unordered_result(tmp_path) -> None:
    """A GROUP BY without ORDER BY must not fail reproduction for getting its
    rows back in a different order (P4-VALID-005).

    DuckDB does not promise a row order for unordered results - the same query
    can return its groups in either order across connections - so reproduction
    compares rows as a multiset. Reversing the stored rows is the failure this
    pins: before the fix it validated as a drift roughly half the time.
    """
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, finding_id = _full_setup(client)
        run_id = client.get(f"/cases/{case_id}/findings/{finding_id}").json()["run_id"]

        with get_connection(db_module.DATA_DIR.parent / "test.db") as conn:
            stored = json.loads(
                conn.execute("SELECT rows_json FROM runs WHERE id = ?", (run_id,)).fetchone()["rows_json"]
            )
            conn.execute(
                "UPDATE runs SET rows_json = ? WHERE id = ?",
                (json.dumps(list(reversed(stored))), run_id),
            )
            conn.commit()

        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200
    assert result.json()["status"] == "supported"
    checks = {c["name"]: c for c in result.json()["checks"]}
    assert checks["calculation"]["passed"] is True


UNORDERED_SQL = (
    # No ORDER BY: DuckDB may return these two groups in either order on any
    # given connection, which is exactly the instability reproduction must
    # tolerate. This is the query that flipped verdicts in the live smoke.
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region"
)


def test_validate_unordered_groupby_is_stable_across_reruns(tmp_path) -> None:
    """The same unordered query, validated repeatedly, must always agree.

    This is the flake the live UI smoke exposed: a GROUP BY without ORDER BY
    returned its groups in a different order on a later connection, and the
    positional comparison turned that into a drift it was not, flipping the
    verdict between supported and insufficient_evidence on identical inputs.
    Repetition is the only honest way to pin it - the order is not under the
    test's control.
    """
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": UNORDERED_SQL},
        ).json()["id"]
        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "North leads revenue"},
        ).json()["id"]

        verdicts = set()
        for _ in range(12):
            response = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")
            assert response.status_code == 200
            verdicts.add(response.json()["status"])

    assert verdicts == {"supported"}, verdicts


# Python-run validation (P3-VALID-010). Re-execution is safe because the script
# runs in the hard sandbox (P3-SEC-001), so the gate is the same one SQL gets.

PY = "result = [[row['region'], row['revenue']] for row in dataset.rows]"


def _python_setup(client) -> tuple[str, str]:
    """Case + dataset + profile + Python run + finding."""
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs/python", json={"code": PY}
    ).json()["id"]
    finding_id = client.post(
        f"/cases/{case_id}/findings",
        json={"run_id": run_id, "statement": "Rows survive the round trip"},
    ).json()["id"]
    return case_id, finding_id


def _tamper(tmp_path, column: str, value: str, run_id: str) -> None:
    with get_connection(db_module.DATA_DIR.parent / "test.db") as conn:
        conn.execute(f"UPDATE runs SET {column} = ? WHERE id = ?", (value, run_id))
        conn.commit()


def test_validate_python_run_supported(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, finding_id = _python_setup(client)
        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200, result.text
    assert result.json()["status"] == "supported"
    checks = {c["name"]: c for c in result.json()["checks"]}
    assert checks["calculation"]["passed"] is True
    assert checks["calculation"]["detail"] == "rerun matches stored result"


def test_validate_python_run_detects_row_drift(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, finding_id = _python_setup(client)
        run_id = client.get(f"/cases/{case_id}/findings/{finding_id}").json()["run_id"]
        _tamper(tmp_path, "rows_json", json.dumps([["north", 999.0]]), run_id)

        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200
    assert result.json()["status"] == "insufficient_evidence"
    checks = {c["name"]: c for c in result.json()["checks"]}
    assert checks["calculation"]["passed"] is False
    assert checks["calculation"]["detail"] == "rerun differs"


def test_validate_python_run_detects_shape_drift(tmp_path) -> None:
    """A changed result shape shows up as a column change even when values line up."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, finding_id = _python_setup(client)
        run_id = client.get(f"/cases/{case_id}/findings/{finding_id}").json()["run_id"]
        _tamper(tmp_path, "columns_json", json.dumps(["other", "columns"]), run_id)

        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200
    checks = {c["name"]: c for c in result.json()["checks"]}
    assert checks["calculation"]["passed"] is False


def test_validate_python_run_whose_script_now_fails(tmp_path) -> None:
    """A script that no longer runs is a verdict, never a 500."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, finding_id = _python_setup(client)
        run_id = client.get(f"/cases/{case_id}/findings/{finding_id}").json()["run_id"]
        _tamper(tmp_path, "code", "result = 1 / 0", run_id)

        result = client.post(f"/cases/{case_id}/findings/{finding_id}/validate")

    assert result.status_code == 200, result.text
    assert result.json()["status"] == "insufficient_evidence"
    repro = {c["name"]: c for c in result.json()["checks"]}["calculation"]
    assert repro["passed"] is False
    assert "script rejected" in repro["detail"]


# --- P8-VALID-003: the six new dimensions ------------------------------------
# Each fixture plants exactly one defect, so a test that sees the concern on the
# right dimension and a pass everywhere else is evidence the detector fires for
# the reason it exists rather than by accident.

from app import validation  # noqa: E402


def _dimension(results, name: str) -> dict:
    return {c["dimension"]: c for c in results}[name]


def test_every_dimension_is_answered() -> None:
    """AT-17: every finding's validation carries all nine dimensions."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="north leads revenue",
        interpretation="",
        question="Why did revenue decline?",
        sql="SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region",
        columns=["region", "total"],
        rows=[["north", 325.0], ["south", 80.5]],
        profile={
            "rows": 3,
            "columns": ["order_id", "revenue", "region"],
            "stats": {
                "order_id": {"type": "numeric", "null_count": 0, "distinct_count": 3},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "region": {"type": "other", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
    )
    answered = {check.dimension for check in checks}
    assert answered == set(validation.DIMENSIONS)
    assert len(checks) == 9
    # The checks are in the PRD's order, whatever order they were built in.
    assert [check.dimension for check in checks] == list(validation.DIMENSIONS)


def test_a_clean_finding_is_supported() -> None:
    """The three pre-existing behaviours are preserved: clean data, a
    reproducing computation and no overclaim is `supported`."""
    status, _ = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="north leads revenue with 325.0",
        interpretation="",
        question="Why did revenue decline?",
        sql="SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region",
        columns=["region", "total"],
        rows=[["north", 325.0], ["south", 80.5]],
        profile={
            "rows": 3,
            "columns": ["order_id", "revenue", "region"],
            "stats": {
                "order_id": {"type": "numeric", "null_count": 0, "distinct_count": 3},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "region": {"type": "other", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
    )
    assert status == "supported"


def test_an_undecidable_check_passes_and_says_it_skipped() -> None:
    """A check that cannot decide must not punish the finding - a skipped check
    that fails is indistinguishable from a finding that is wrong."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="a finding",
        interpretation="",
        question="why?",
        sql="",
        columns=[],
        rows=[],
        profile=None,
    )
    # No query, no profile: every check that needed either skipped rather than
    # failed, and the verdict is not punished for the validator's blindness.
    assert status == "supported"
    skipped = [check for check in checks if "skipped" in check.detail]
    assert skipped
    assert all(check.passed for check in skipped)


def test_a_finding_quoting_an_invented_magnitude_fails_evidence() -> None:
    """The drafter's honesty budget, applied to the finding's own statement."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="north leads revenue with 9000.0",
        interpretation="",
        question="Why did revenue decline?",
        sql="SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region",
        columns=["region", "total"],
        rows=[["north", 325.0], ["south", 80.5]],
        profile={
            "rows": 2,
            "columns": ["region", "revenue"],
            "stats": {
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "region": {"type": "other", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
    )
    evidence = _dimension([c.to_dict() for c in checks], "evidence")
    assert evidence["passed"] is False
    assert "9000" in evidence["detail"]
    assert status == "insufficient_evidence"


def test_causal_language_from_a_correlation_is_flagged() -> None:
    """AT-18's weakest form: the check names the gap, the full guard is later."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="marketing spend drives signups",
        interpretation="",
        question="Do signups follow marketing spend?",
        sql="SELECT spend, signups FROM read_csv_auto(?)",
        columns=["spend", "signups"],
        rows=[[100.0, 40.0], [200.0, 85.0]],
        profile={
            "rows": 2,
            "columns": ["spend", "signups"],
            "stats": {
                "spend": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "signups": {"type": "numeric", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
    )
    causality = _dimension([c.to_dict() for c in checks], "causality")
    assert causality["passed"] is False
    assert "association" in causality["detail"]
    # A concern, not a refusal: the finding stands, labelled.
    assert status == "partially_supported"


def test_associative_language_is_not_flagged_as_causal() -> None:
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="signups are higher where spend is higher",
        interpretation="",
        question="Do signups follow marketing spend?",
        sql="SELECT spend, signups FROM read_csv_auto(?)",
        columns=["spend", "signups"],
        rows=[[100.0, 40.0], [200.0, 85.0]],
        profile={
            "rows": 2,
            "columns": ["spend", "signups"],
            "stats": {
                "spend": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "signups": {"type": "numeric", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
    )
    causality = _dimension([c.to_dict() for c in checks], "causality")
    assert causality["passed"] is True


def test_a_filtered_group_by_is_flagged_on_population() -> None:
    """A GROUP BY over a filtered table compares a subset while reading like a
    population."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="north leads revenue",
        interpretation="",
        question="Why did revenue decline?",
        sql="SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
        "WHERE region <> 'south' GROUP BY region",
        columns=["region", "total"],
        rows=[["north", 325.0], ["west", 60.0]],
        profile={
            "rows": 500,
            "columns": ["order_id", "revenue", "region"],
            "stats": {
                "order_id": {"type": "numeric", "null_count": 0, "distinct_count": 500},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 400},
                "region": {"type": "other", "null_count": 0, "distinct_count": 3},
            },
            "quality": [],
        },
    )
    population = _dimension([c.to_dict() for c in checks], "population")
    assert population["passed"] is False
    assert "subset" in population["detail"]
    assert status == "insufficient_evidence"


def test_a_trend_claim_over_a_single_period_is_flagged_on_timeframe() -> None:
    """One period cannot support a trend, however many rows hold it."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="revenue declined in the quarter",
        interpretation="",
        question="What is the revenue trend?",
        sql="SELECT quarter, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY quarter",
        columns=["quarter", "total"],
        rows=[["2024q3", 900.0]],
        profile={
            "rows": 300,
            "columns": ["quarter", "revenue"],
            "stats": {
                "quarter": {"type": "temporal", "null_count": 0, "distinct_count": 1},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 250},
            },
            "quality": [],
        },
    )
    timeframe = _dimension([c.to_dict() for c in checks], "timeframe")
    assert timeframe["passed"] is False
    assert "no earlier period" in timeframe["detail"]


def test_a_trend_claim_over_a_gappy_series_is_flagged_on_timeframe() -> None:
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="revenue trended down over time",
        interpretation="",
        question="What is the revenue trend?",
        sql="SELECT day, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY day",
        columns=["day", "total"],
        rows=[["2024-01-01", 300.0], ["2024-01-05", 290.0]],
        profile={
            "rows": 300,
            "columns": ["day", "revenue"],
            "stats": {
                "day": {"type": "temporal", "null_count": 0, "distinct_count": 2},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 250},
            },
            "quality": [
                {
                    "kind": "date_gaps",
                    "column": "day",
                    "severity": "medium",
                    "observed": "day has 1 interval at least twice the usual step",
                    "impact": "A period-over-period comparison over day may compare "
                    "non-adjacent windows.",
                }
            ],
        },
    )
    timeframe = _dimension([c.to_dict() for c in checks], "timeframe")
    assert timeframe["passed"] is False
    assert "non-adjacent" in timeframe["detail"]


def test_a_non_time_claim_skips_the_timeframe_check() -> None:
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="north leads revenue",
        interpretation="",
        question="Which region leads?",
        sql="SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region",
        columns=["region", "total"],
        rows=[["north", 325.0], ["south", 80.5]],
        profile={
            "rows": 3,
            "columns": ["region", "revenue"],
            "stats": {
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "region": {"type": "other", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
    )
    timeframe = _dimension([c.to_dict() for c in checks], "timeframe")
    assert timeframe["passed"] is True
    assert "no claim about change over time" in timeframe["detail"]


def test_an_average_over_an_extreme_column_is_flagged_on_method() -> None:
    """The mean is the first thing a generator reaches for and the one an
    outlier moves most."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="the typical revenue is 400",
        interpretation="",
        question="What is the typical revenue?",
        sql="SELECT AVG(revenue) AS avg_revenue FROM read_csv_auto(?)",
        columns=["avg_revenue"],
        rows=[[400.0]],
        profile={
            "rows": 8,
            "columns": ["revenue"],
            "stats": {
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 4},
            },
            "quality": [
                {
                    "kind": "extreme_values",
                    "column": "revenue",
                    "severity": "medium",
                    "observed": "The largest value in revenue (999999.0) is 123.5x "
                    "the next-largest value.",
                    "impact": "Averages over revenue are pulled by this extreme value.",
                }
            ],
        },
    )
    method = _dimension([c.to_dict() for c in checks], "method")
    assert method["passed"] is False
    assert "extreme" in method["detail"]


def test_a_query_that_ignores_the_questions_column_is_flagged_on_method() -> None:
    """A question about revenue answered by a query that never reads revenue is
    an answer to a different question."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="the regions differ",
        interpretation="",
        question="How does revenue vary by region?",
        sql="SELECT region, COUNT(*) AS n FROM read_csv_auto(?) GROUP BY region",
        columns=["region", "n"],
        rows=[["north", 5], ["south", 3]],
        profile={
            "rows": 8,
            "columns": ["region", "revenue"],
            "stats": {
                "region": {"type": "other", "null_count": 0, "distinct_count": 2},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 4},
            },
            "quality": [],
        },
    )
    method = _dimension([c.to_dict() for c in checks], "method")
    assert method["passed"] is False
    assert "revenue" in method["detail"]


def test_a_sum_over_a_column_with_nulls_is_flagged_on_assumptions() -> None:
    """The total is of the values present, not of the column, unless the
    finding states that missing means zero."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="the total revenue is 900",
        interpretation="",
        question="What is the total revenue?",
        sql="SELECT SUM(revenue) AS total FROM read_csv_auto(?)",
        columns=["total"],
        rows=[[900.0]],
        profile={
            "rows": 8,
            "columns": ["revenue"],
            "stats": {
                "revenue": {"type": "numeric", "null_count": 2, "distinct_count": 4},
            },
            "quality": [
                {
                    "kind": "missing_values",
                    "column": "revenue",
                    "severity": "medium",
                    "observed": "2 of 8 values are missing.",
                    "impact": "revenue contains 25.0% missing values; totals may be "
                    "understated.",
                }
            ],
        },
    )
    assumptions = _dimension([c.to_dict() for c in checks], "assumptions")
    assert assumptions["passed"] is False
    assert "missing means zero" in assumptions["detail"]


def test_an_unread_categorical_column_is_flagged_on_alternatives() -> None:
    """A group-by that ignores a categorical column the data varies on cannot
    separate its own effect from that column's."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="the regions differ in revenue",
        interpretation="",
        question="How does revenue vary by region?",
        sql="SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region",
        columns=["region", "total"],
        rows=[["north", 325.0], ["south", 80.5]],
        profile={
            "rows": 8,
            "columns": ["region", "revenue", "country"],
            "stats": {
                "region": {"type": "other", "null_count": 0, "distinct_count": 2},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 4},
                "country": {"type": "other", "null_count": 0, "distinct_count": 3},
            },
            "quality": [],
        },
    )
    alternatives = _dimension([c.to_dict() for c in checks], "alternative_explanations")
    assert alternatives["passed"] is False
    assert "country" in alternatives["detail"]


def test_an_unread_identifier_is_not_an_alternative_explanation() -> None:
    """An id distinguishes rows, it does not compete with the finding."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="the regions differ in revenue",
        interpretation="",
        question="How does revenue vary by region?",
        sql="SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region",
        columns=["region", "total"],
        rows=[["north", 325.0], ["south", 80.5]],
        profile={
            "rows": 8,
            "columns": ["order_id", "region", "revenue"],
            "stats": {
                "order_id": {"type": "numeric", "null_count": 0, "distinct_count": 8},
                "region": {"type": "other", "null_count": 0, "distinct_count": 2},
                "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 4},
            },
            "quality": [],
        },
    )
    alternatives = _dimension([c.to_dict() for c in checks], "alternative_explanations")
    assert alternatives["passed"] is True


def test_a_concern_yields_partially_supported_not_failure() -> None:
    """The verdict that says the numbers reproduce and the claim is phrased
    within them, but the analysis carries a stated limitation."""
    status, _ = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="marketing spend drives signups",
        interpretation="",
        question="Do signups follow marketing spend?",
        sql="SELECT spend, signups FROM read_csv_auto(?)",
        columns=["spend", "signups"],
        rows=[[100.0, 40.0], [200.0, 85.0]],
        profile={
            "rows": 2,
            "columns": ["spend", "signups"],
            "stats": {
                "spend": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "signups": {"type": "numeric", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
    )
    assert status == "partially_supported"


def test_validation_executes_the_finding_once_not_once_per_check(tmp_path) -> None:
    """Nine dimensions, one execution (the contract's budget).

    The checks are pure functions of the stored run and the stored profile; the
    only thing validation executes is the single rerun that Calculation reads.
    A regression that re-ran the query inside a check would show up as a second
    call here, and a finding would cost nine executions instead of one.
    """
    from app import main as main_module

    _temp_env(tmp_path)
    calls = {"count": 0}
    real_run_query = main_module.run_query

    def counting_run_query(*args, **kwargs):
        calls["count"] += 1
        return real_run_query(*args, **kwargs)

    monkey_target = "app.main.run_query"
    original = main_module.run_query
    main_module.run_query = counting_run_query
    try:
        with TestClient(app) as client:
            case_id, finding_id = _full_setup(client)
            # The run itself is one execution; the budget is about what a
            # validate adds on top of it.
            calls["count"] = 0
            result = client.post(
                f"/cases/{case_id}/findings/{finding_id}/validate"
            )
    finally:
        main_module.run_query = original

    assert result.status_code == 200, result.text
    assert len(result.json()["checks"]) == len(validation.DIMENSIONS)
    assert calls["count"] == 1, (
        f"validation executed the finding {calls['count']} time(s); the nine "
        "checks must read one rerun, not run one each"
    )
    assert monkey_target  # kept the name honest if the import path moves
