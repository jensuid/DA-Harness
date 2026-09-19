"""Single-dataset deletion tests for P3-DATA-009.

A case could already be deleted wholesale; nothing could remove one dataset.
These cover removing a dataset cleanly, the evidence-preserving refusal while a
run still binds it (single- and multi-dataset), and the 404 contract.
"""

from pathlib import Path

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

SALES = b"order_id,region,revenue\n1,north,100.0\n2,south,60.0\n3,north,80.0\n"
TARGETS = b"region,target\nnorth,150.0\nsouth,150.0\n"
JOIN_SQL = (
    "SELECT a.region, SUM(a.revenue) AS revenue, b.target "
    "FROM read_csv_auto(?) a JOIN read_csv_auto(?) b ON a.region = b.region "
    "GROUP BY a.region, b.target ORDER BY a.region"
)


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_datasets(client):
    case_id = client.post(
        "/cases", json={"question": "Did regions hit target?", "dataset": "sales.csv"}
    ).json()["id"]
    sales = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", SALES, "text/csv")},
    ).json()["id"]
    targets = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("targets.csv", TARGETS, "text/csv")},
    ).json()["id"]
    return case_id, sales, targets


def _delete(client, case_id, dataset_id):
    return client.delete(f"/cases/{case_id}/datasets/{dataset_id}")


def _dataset(client, case_id, dataset_id):
    """One dataset's metadata, found by id - the listing is newest-first."""
    for row in client.get(f"/cases/{case_id}/datasets").json():
        if row["id"] == dataset_id:
            return row
    raise AssertionError(f"dataset {dataset_id} is not attached to case {case_id}")


def test_deleting_a_dataset_leaves_the_case_and_siblings_alive(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        response = _delete(client, case_id, sales)

        assert response.status_code == 204, response.text
        # The case and the untouched dataset are exactly as they were.
        assert client.get(f"/cases/{case_id}").status_code == 200
        remaining = client.get(f"/cases/{case_id}/datasets").json()
        assert [d["id"] for d in remaining] == [targets]
        assert _dataset(client, case_id, targets)["id"] == targets


def test_delete_removes_the_profile_and_the_plans(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _ = _case_with_datasets(client)
        client.post(f"/cases/{case_id}/datasets/{sales}/profile")
        client.post(f"/cases/{case_id}/datasets/{sales}/plan")
        assert client.get(f"/cases/{case_id}/datasets/{sales}/plan").status_code == 200

        assert _delete(client, case_id, sales).status_code == 204

        # Both the derived profile and the plan died with the dataset.
        assert client.get(f"/cases/{case_id}/datasets/{sales}/profile").status_code == 404
        assert client.get(f"/cases/{case_id}/datasets/{sales}/plan").status_code == 404


def test_delete_removes_the_file_on_disk(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _ = _case_with_datasets(client)
        stored = _dataset(client, case_id, sales)["stored_path"]
        assert Path(stored).is_file()

        assert _delete(client, case_id, sales).status_code == 204

        assert not Path(stored).exists(), "the dataset file was left on disk"


def test_a_single_dataset_run_blocks_deletion(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _ = _case_with_datasets(client)
        client.post(
            f"/cases/{case_id}/datasets/{sales}/runs",
            json={"sql": "SELECT region, COUNT(*) AS n FROM read_csv_auto(?) GROUP BY region"},
        )

        response = _delete(client, case_id, sales)

        assert response.status_code == 400, response.text
        assert "1 run" in response.json()["detail"]
        # Nothing was removed: the dataset and its file survive.
        assert _dataset(client, case_id, sales)["id"] == sales


def test_a_multi_dataset_run_blocks_deletion(tmp_path) -> None:
    """A join run binds several datasets; the non-primary one is blocked too."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        client.post(
            f"/cases/{case_id}/runs",
            json={"dataset_ids": [sales, targets], "sql": JOIN_SQL},
        )

        response = _delete(client, case_id, targets)

        assert response.status_code == 400, response.text
        assert "1 run" in response.json()["detail"]
        assert len(client.get(f"/cases/{case_id}/datasets").json()) == 2


def test_deleting_the_blocking_run_frees_the_dataset(tmp_path) -> None:
    """The gate is live data, not a stored flag: once no run binds it, it opens."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _ = _case_with_datasets(client)
        run_id = client.post(
            f"/cases/{case_id}/datasets/{sales}/runs",
            json={"sql": "SELECT COUNT(*) AS n FROM read_csv_auto(?)"},
        ).json()["id"]
        assert _delete(client, case_id, sales).status_code == 400

        # No run-delete endpoint exists, so the row goes straight to SQLite.
        with get_connection(tmp_path / "test.db") as connection:
            connection.execute("DELETE FROM runs WHERE id = ?", (run_id,))

        assert _delete(client, case_id, sales).status_code == 204
        # The blocker is gone, so the dataset goes - its sibling is untouched.
        remaining = [d["id"] for d in client.get(f"/cases/{case_id}/datasets").json()]
        assert sales not in remaining


def test_deleting_the_last_dataset_leaves_a_valid_empty_case(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        assert _delete(client, case_id, sales).status_code == 204
        assert _delete(client, case_id, targets).status_code == 204

        # An empty case is still a case, and it accepts fresh data again.
        assert client.get(f"/cases/{case_id}/datasets").json() == []
        assert client.get(f"/cases/{case_id}").status_code == 200
        new_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", SALES, "text/csv")},
        ).json()["id"]
        assert client.post(
            f"/cases/{case_id}/datasets/{new_id}/profile"
        ).status_code == 201


def test_404s_for_unknown_and_cross_case_datasets(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _ = _case_with_datasets(client)
        other_case = client.post(
            "/cases", json={"question": "Other?", "dataset": "o.csv"}
        ).json()["id"]

        assert _delete(client, "no-such-case", sales).status_code == 404
        assert _delete(client, case_id, "no-such-dataset").status_code == 404
        # A dataset belonging to another case is not reachable through this path.
        assert _delete(client, other_case, sales).status_code == 404
        assert _dataset(client, case_id, sales)["id"] == sales
