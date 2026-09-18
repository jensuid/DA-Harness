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
