"""EVALUATE mode tests for P7-EVAL-001.

The user hands DAH work that came from elsewhere - a query or a script and the
claim it was offered to support - and the core answers the nine questions the
specification names, each against the data rather than against the claim's own
confidence.

Every test drives the HTTP endpoint, so what is pinned is the contract a user
sees: the verdicts, the sentences, the persistence, and the refusal of work the
store must not execute. The two chart branches are the exception - a chart
cannot exist for a run the request itself just created, so the axis-matching
check is exercised against the pure module, which is where the endpoint gets
it.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.evaluator import (
    AxisFinding,
    Evaluation,
    evaluate as evaluate_artifact,
)
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"

# A clean artifact over a clean dataset. Two ordered groups whose sums are
# known by construction (325.0 and 80.5), so the expectations below are
# arithmetic rather than captured values that could drift.
CLEAN_SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)
# The same shape without the ORDER BY: a ranking whose order is not pinned.
UNORDERED_SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region"
)
# Six of ten regions unknown - a claim over `region` is a claim over a column
# that is mostly empty.
NULL_HEAVY = (
    b"order_id,revenue,region\n"
    b"1,125.0,north\n2,80.5,south\n3,200.0,\n4,10.0,\n5,30.0,\n"
)
CLEAN_CLAIM = "Revenue is higher in north than south because north totals 325.0"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_dataset(client, csv: bytes = CSV, label: str = "sales.csv"):
    """A case with an attached, profiled dataset ready to be audited."""
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": label}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": (label, csv, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    return case_id, dataset_id


def _evaluate(client, case_id, dataset_id, code, claim, kind="sql"):
    return client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/evaluate",
        json={"code": code, "claim": claim, "kind": kind},
    )


def _verdicts(response):
    return {
        finding["axis"]: finding for finding in response.json()["findings"]
    }


def test_clean_artifact_passes_all_nine_axes(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(client, case_id, dataset_id, CLEAN_SQL, CLEAN_CLAIM)

    assert response.status_code == 201, response.text
    body = response.json()
    assert [finding["axis"] for finding in body["findings"]] == [
        "question", "data", "quality", "method", "calculation",
        "evidence", "claim", "visualization", "limitations",
    ]
    # The contract's baseline: a clean artifact over a clean dataset passes
    # every axis, including the ones that only report the absence of a problem.
    verdicts = {finding["axis"]: finding["verdict"] for finding in body["findings"]}
    assert verdicts == {axis: "pass" for axis in verdicts}, verdicts

    # The audit is recorded as the artifact's own run, so it is itself
    # inspectable and reproducible - the standard every other artifact meets.
    assert body["run_id"]
    assert body["artifact_kind"] == "sql"
    assert body["claim"] == CLEAN_CLAIM
    assert body["source"] == "deterministic"

    app.dependency_overrides.clear()


def test_unknown_column_is_flagged_on_data(tmp_path) -> None:
    """A column the dataset lacks is a Data fail, never a silent pass."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id,
            "SELECT region, profit FROM read_csv_auto(?)",
            "Revenue is higher in north than south",
        )

    assert response.status_code == 201, response.text
    data = _verdicts(response)["data"]
    assert data["verdict"] == "fail"
    assert "profit" in data["detail"]
    assert "does not have" in data["detail"]

    app.dependency_overrides.clear()


def test_invented_magnitude_is_flagged_on_evidence(tmp_path) -> None:
    """A claim quoting a number the run does not contain is the commonest lie."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id, CLEAN_SQL,
            "North totals 999.0, which is more than south",
        )

    assert response.status_code == 201, response.text
    evidence = _verdicts(response)["evidence"]
    assert evidence["verdict"] == "fail"
    assert "999" in evidence["detail"]

    app.dependency_overrides.clear()


def test_quoted_magnitude_from_the_result_passes_evidence(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id, CLEAN_SQL,
            "North totals 325.0 against south's 80.5",
        )

    assert response.status_code == 201, response.text
    assert _verdicts(response)["evidence"]["verdict"] == "pass"

    app.dependency_overrides.clear()


def test_vague_claim_is_flagged_on_claim(tmp_path) -> None:
    """A claim that cannot be wrong cannot be audited."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id, CLEAN_SQL, "revenue was analysed"
        )

    assert response.status_code == 201, response.text
    claim = _verdicts(response)["claim"]
    assert claim["verdict"] == "concern"
    assert "contradict" in claim["detail"]

    app.dependency_overrides.clear()


def test_unordered_ranking_is_flagged_on_method(tmp_path) -> None:
    """A result whose order is not pinned cannot be checked by being redone."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id, UNORDERED_SQL, CLEAN_CLAIM
        )

    assert response.status_code == 201, response.text
    method = _verdicts(response)["method"]
    assert method["verdict"] == "concern"
    assert "unordered" in method["detail"]

    app.dependency_overrides.clear()


def test_single_row_result_is_deterministic_without_an_order(tmp_path) -> None:
    """One row has no row order to disagree about, so no ORDER BY is required."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id,
            "SELECT SUM(revenue) AS grand_total FROM read_csv_auto(?)",
            "Total revenue across every region is 405.5",
        )

    assert response.status_code == 201, response.text
    assert _verdicts(response)["method"]["verdict"] == "pass"

    app.dependency_overrides.clear()


def test_null_heavy_column_is_flagged_on_quality(tmp_path) -> None:
    """A claim over a mostly-empty column is a Quality limitation, not a pass."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(
            client, csv=NULL_HEAVY, label="messy.csv"
        )
        response = _evaluate(
            client, case_id, dataset_id, CLEAN_SQL, CLEAN_CLAIM
        )

    assert response.status_code == 201, response.text
    quality = _verdicts(response)["quality"]
    assert quality["verdict"] == "concern"
    assert "region" in quality["detail"]
    assert "null" in quality["detail"]
    # The share is stated, so a reader can weigh it rather than guessing.
    assert "60" in quality["detail"]

    app.dependency_overrides.clear()


def test_non_reproducing_artifact_is_flagged_on_calculation(tmp_path) -> None:
    """Two executions that disagree mean no claim resting on it can be checked."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id,
            "SELECT random() AS r FROM read_csv_auto(?)",
            "Revenue is higher in north than south",
        )

    assert response.status_code == 201, response.text
    calculation = _verdicts(response)["calculation"]
    assert calculation["verdict"] == "fail"
    assert "disagree" in calculation["detail"]

    app.dependency_overrides.clear()


def test_artifact_that_does_not_run_is_a_calculation_finding(tmp_path) -> None:
    """A read-only artifact that fails at run time is reported, not 400ed.

    The work is not the user's to fix - it came from elsewhere - so the audit
    records that it does not run rather than refusing the request.
    """
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id,
            "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
            "GROUP BY nonexistent_dimension ORDER BY region",
            CLEAN_CLAIM,
        )

    assert response.status_code == 201, response.text
    body = response.json()
    calculation = _verdicts(response)["calculation"]
    assert calculation["verdict"] == "fail"
    assert "does not run" in calculation["detail"]
    # The audit is still recorded, with no run to attach it to.
    assert body["run_id"] is None

    app.dependency_overrides.clear()


def test_non_read_only_artifact_is_refused_before_execution(tmp_path) -> None:
    """A mutation is not an artifact to audit; the store must never run it."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id,
            "DELETE FROM read_csv_auto(?)",
            "Revenue is higher in north",
        )
        listed = client.get(
            f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
        ).json()
        runs = client.get(f"/cases/{case_id}/runs").json()

    assert response.status_code == 400
    assert "read-only" in response.json()["detail"]
    # Refused before anything executed: no audit row, no run row.
    assert listed == []
    assert runs == []

    app.dependency_overrides.clear()


def test_empty_code_and_claim_are_400(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        empty_code = _evaluate(client, case_id, dataset_id, "   ", CLEAN_CLAIM)
        empty_claim = _evaluate(client, case_id, dataset_id, CLEAN_SQL, "   ")
        bad_kind = _evaluate(
            client, case_id, dataset_id, CLEAN_SQL, CLEAN_CLAIM, kind="notebook"
        )

    assert empty_code.status_code == 400
    assert empty_claim.status_code == 400
    assert bad_kind.status_code == 400

    app.dependency_overrides.clear()


def test_python_artifact_is_audited(tmp_path) -> None:
    """The same nine axes answer a submitted script, not only a query."""
    _temp_env(tmp_path)
    code = (
        "totals = {}\n"
        "for row in dataset.rows:\n"
        "    totals[row['region']] = totals.get(row['region'], 0) + row['revenue']\n"
        "result = [{'region': k, 'total': v} for k, v in sorted(totals.items())]\n"
    )
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id, code,
            "Revenue is higher in north than south because north totals 325.0",
            kind="python",
        )

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["artifact_kind"] == "python"
    assert body["run_id"]
    verdicts = {finding["axis"]: finding["verdict"] for finding in body["findings"]}
    assert verdicts["data"] == "pass"
    assert verdicts["calculation"] == "pass"
    assert verdicts["evidence"] == "pass"

    app.dependency_overrides.clear()


def test_python_artifact_reading_a_missing_column_is_flagged(tmp_path) -> None:
    _temp_env(tmp_path)
    code = (
        "result = [\n"
        "    {'region': row['region'], 'profit': row['profit']}\n"
        "    for row in dataset.rows\n"
        "]\n"
    )
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(
            client, case_id, dataset_id, code,
            "Revenue is higher in north than south",
            kind="python",
        )

    assert response.status_code == 201, response.text
    data = _verdicts(response)["data"]
    assert data["verdict"] == "fail"
    assert "profit" in data["detail"]

    app.dependency_overrides.clear()


def test_evaluation_is_persisted_and_listed_newest_first(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        first = _evaluate(client, case_id, dataset_id, CLEAN_SQL, CLEAN_CLAIM)
        second = _evaluate(
            client, case_id, dataset_id, CLEAN_SQL,
            "North totals 999.0, which is more than south",
        )
        listed = client.get(
            f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
        ).json()

    assert first.status_code == 201
    assert second.status_code == 201
    assert [item["id"] for item in listed] == [
        second.json()["id"], first.json()["id"]
    ]
    # The stored findings survive the round trip with their sentences.
    stored = listed[0]
    assert stored["claim"] == "North totals 999.0, which is more than south"
    assert {f["axis"] for f in stored["findings"]} == {
        "question", "data", "quality", "method", "calculation",
        "evidence", "claim", "visualization", "limitations",
    }
    evidence = {
        f["axis"]: f for f in stored["findings"]
    }["evidence"]
    assert evidence["verdict"] == "fail"
    assert "999" in evidence["detail"]

    app.dependency_overrides.clear()


def test_evaluation_never_mutates_another_artifact(tmp_path) -> None:
    """An audit appends its own row and changes nothing else."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        # Give the case artifacts an evaluation must not disturb.
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": CLEAN_SQL}
        ).json()["id"]
        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "North leads revenue"},
        ).json()["id"]
        before = {
            "runs": len(client.get(f"/cases/{case_id}/runs").json()),
            "findings": len(client.get(f"/cases/{case_id}/findings").json()),
            "evaluations": len(
                client.get(
                    f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
                ).json()
            ),
        }
        _evaluate(client, case_id, dataset_id, CLEAN_SQL, CLEAN_CLAIM)
        after = {
            "runs": len(client.get(f"/cases/{case_id}/runs").json()),
            "findings": len(client.get(f"/cases/{case_id}/findings").json()),
            "evaluations": len(
                client.get(
                    f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
                ).json()
            ),
        }
        finding = client.get(f"/cases/{case_id}/findings/{finding_id}").json()

    assert after["runs"] == before["runs"] + 1
    assert after["findings"] == before["findings"]
    assert after["evaluations"] == before["evaluations"] + 1
    # The pre-existing finding and its validation state are untouched.
    assert finding["statement"] == "North leads revenue"
    assert finding["validation_status"] == "not_evaluated"

    app.dependency_overrides.clear()


def test_404s_including_a_cross_case_dataset(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        other_case_id, other_dataset_id = _case_with_dataset(
            client, label="other.csv"
        )
        unknown_case = _evaluate(
            client, "nope", dataset_id, CLEAN_SQL, CLEAN_CLAIM
        )
        unknown_dataset = _evaluate(
            client, case_id, "nope", CLEAN_SQL, CLEAN_CLAIM
        )
        # The dataset is real, but it belongs to another case.
        cross_case = _evaluate(
            client, case_id, other_dataset_id, CLEAN_SQL, CLEAN_CLAIM
        )
        listed = client.get("/cases/nope/datasets/nope/evaluations")

    assert unknown_case.status_code == 404
    assert unknown_dataset.status_code == 404
    assert cross_case.status_code == 404
    assert listed.status_code == 404

    app.dependency_overrides.clear()


def test_evaluation_without_a_profile_reports_unknown_columns(tmp_path) -> None:
    """An unprofiled dataset has no columns to check a claim against."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "sales.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        ).json()["id"]
        response = _evaluate(client, case_id, dataset_id, CLEAN_SQL, CLEAN_CLAIM)

    assert response.status_code == 201, response.text
    data = _verdicts(response)["data"]
    assert data["verdict"] == "fail"
    assert "no profile" in data["detail"]

    app.dependency_overrides.clear()


def test_every_verdict_carries_an_actionable_sentence(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = _evaluate(client, case_id, dataset_id, CLEAN_SQL, CLEAN_CLAIM)

    for finding in response.json()["findings"]:
        assert finding["verdict"] in ("pass", "concern", "fail")
        # A sentence, not a code: the reader can act on it.
        assert len(finding["detail"]) > 20, finding

    app.dependency_overrides.clear()


# The chart branches are exercised against the pure module: a chart cannot
# exist for the run the request itself creates, so the endpoint cannot reach
# them, but the check is what the endpoint consults when one does.


def _audit(**overrides):
    kwargs = dict(
        artifact_kind="sql",
        code=CLEAN_SQL,
        claim=CLEAN_CLAIM,
        profile={
            "rows": 3,
            "columns": ["order_id", "revenue", "region"],
            "stats": {
                "revenue": {"type": "numeric", "null_percentage": 0.0},
                "region": {"type": "other", "null_percentage": 0.0},
            },
            "duplicate_rows": 0,
        },
        run={
            "columns": ["region", "total"],
            "rows": [["north", 325.0], ["south", 80.5]],
            "truncated": False,
        },
        reproduced=True,
        run_error=None,
        deterministic=True,
        chart_axes=None,
    )
    kwargs.update(overrides)
    return evaluate_artifact(**kwargs)


def test_pure_module_matches_and_mismatches_a_chart() -> None:
    matching = _audit(chart_axes=["region", "total"])
    assert matching.findings[7] == AxisFinding(
        "visualization",
        "pass",
        "a chart exists over this run's own columns: region, total",
    )

    mismatched = _audit(chart_axes=["region", "median_price"])
    assert mismatched.verdicts["visualization"] == "fail"
    assert "median_price" in mismatched.findings[7].detail


def test_pure_module_reports_an_execution_error_on_calculation() -> None:
    audit = _audit(reproduced=False, run_error="Binder Error: no such column")
    detail = audit.findings[4].detail
    assert audit.verdicts["calculation"] == "fail"
    assert "does not run" in detail and "no such column" in detail
    # The other axes still answer; an artifact that does not run is not a
    # reason to stop auditing it.
    assert len(audit.findings) == 9


def test_pure_module_returns_an_evaluation_of_nine_findings() -> None:
    audit = _audit()
    assert isinstance(audit, Evaluation)
    assert [finding.axis for finding in audit.findings] == [
        "question", "data", "quality", "method", "calculation",
        "evidence", "claim", "visualization", "limitations",
    ]
    assert set(audit.verdicts) == set([
        "question", "data", "quality", "method", "calculation",
        "evidence", "claim", "visualization", "limitations",
    ])
