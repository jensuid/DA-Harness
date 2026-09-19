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
    assert check_names["reproducibility"] is True
    assert check_names["missing_data"] is True
    assert check_names["evidence_integrity"] is True

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
    assert checks["reproducibility"]["passed"] is True
    assert checks["missing_data"]["passed"] is False


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
    assert checks["reproducibility"]["passed"] is False


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
    assert checks["reproducibility"]["passed"] is True


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
    assert checks["reproducibility"]["passed"] is True
    assert checks["reproducibility"]["detail"] == "rerun matches stored result"


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
    assert checks["reproducibility"]["passed"] is False
    assert checks["reproducibility"]["detail"] == "rerun differs"


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
    assert checks["reproducibility"]["passed"] is False


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
    repro = {c["name"]: c for c in result.json()["checks"]}["reproducibility"]
    assert repro["passed"] is False
    assert "script rejected" in repro["detail"]
