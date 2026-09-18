from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_dataset(client) -> tuple[str, str]:
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    return case_id, dataset_id


def test_run_aggregation_and_reopen(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region ORDER BY region"},
        )
        assert response.status_code == 201
        run = response.json()
        assert run["columns"] == ["region", "total"]
        assert run["row_count"] == 2
        assert run["rows"] == [["north", 325.0], ["south", 80.5]]
        assert run["truncated"] is False
        run_id = run["id"]

    # Reopen in a fresh client - the run and its rows must survive.
    with TestClient(app) as client:
        stored = client.get(f"/cases/{case_id}/runs/{run_id}")

    assert stored.status_code == 200
    assert stored.json()["rows"] == [["north", 325.0], ["south", 80.5]]
    assert stored.json()["sql"].startswith("SELECT region")


def test_list_runs_excludes_rows(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT COUNT(*) FROM read_csv_auto(?)"},
        )
        listed = client.get(f"/cases/{case_id}/runs")

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert "rows" not in listed.json()[0]


def test_rejects_write_query(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "DELETE FROM read_csv_auto(?)"},
        )

    assert response.status_code == 400


def test_rejects_multi_statement(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT 1; SELECT 2"},
        )

    assert response.status_code == 400


def test_run_unknown_dataset_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        response = client.post(
            f"/cases/{case_id}/datasets/nope/runs",
            json={"sql": "SELECT 1"},
        )

    assert response.status_code == 404
