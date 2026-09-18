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


def _case_with_run(client) -> tuple[str, str]:
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
    ).json()["id"]
    return case_id, run_id


def test_create_finding_and_trace_evidence(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        response = client.post(
            f"/cases/{case_id}/findings",
            json={
                "run_id": run_id,
                "statement": "North region revenue is 325.0",
                "interpretation": "North leads revenue",
                "caveat": "three rows only",
            },
        )
        assert response.status_code == 201
        finding = response.json()
        assert finding["validation_status"] == "not_evaluated"
        finding_id = finding["id"]

        chain = client.get(f"/cases/{case_id}/findings/{finding_id}/evidence")

    assert chain.status_code == 200
    body = chain.json()
    assert body["finding"]["statement"] == "North region revenue is 325.0"
    assert body["sql"] == SQL
    assert body["rows"] == [["north", 325.0], ["south", 80.5]]
    assert body["dataset_filename"] == "sales.csv"


def test_findings_survive_reopen(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "a finding"},
        )
        listed = client.get(f"/cases/{case_id}/findings")

    assert listed.status_code == 200

    with TestClient(app) as client:
        reopened = client.get(f"/cases/{case_id}/findings")

    assert reopened.status_code == 200
    assert len(reopened.json()) == 1


def test_finding_unknown_run_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        response = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": "nope", "statement": "x"},
        )

    assert response.status_code == 404


def test_set_validation_status(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, run_id = _case_with_run(client)
        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "x"},
        ).json()["id"]

        ok = client.patch(
            f"/cases/{case_id}/findings/{finding_id}/validation?status=supported"
        )
        assert ok.status_code == 200
        assert ok.json()["validation_status"] == "supported"

        bad = client.patch(
            f"/cases/{case_id}/findings/{finding_id}/validation?status=nonsense"
        )
    assert bad.status_code == 400
