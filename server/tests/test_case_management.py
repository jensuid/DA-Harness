from fastapi.testclient import TestClient
from pathlib import Path

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
SQL = "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region ORDER BY region"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _full_case(client) -> str:
    """A case with a dataset, profile, run, finding and chart attached."""
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
        json={"run_id": run_id, "statement": "north leads revenue"},
    ).json()["id"]
    client.post(
        f"/cases/{case_id}/runs/{run_id}/charts",
        json={"kind": "bar", "x": "region", "y": "total"},
    )
    return case_id


def _counts(client, case_id: str) -> dict:
    counts = {}
    for name in ("datasets", "runs"):
        counts[name] = len(
            client.get(f"/cases/{case_id}/{name}").json()
        )
    counts["charts"] = len(
        client.get(f"/cases/{case_id}/runs/{_first_run(client, case_id)}/charts").json()
    )
    counts["findings"] = len(
        client.get(f"/cases/{case_id}/findings").json()
    )
    return counts


def _first_run(client, case_id: str) -> str:
    return client.get(f"/cases/{case_id}/runs").json()[0]["id"]


def test_rename_case(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        response = client.patch(
            f"/cases/{case_id}",
            json={"question": "Why did Q3 revenue decline?", "dataset": "q3_sales.csv"},
        )

    assert response.status_code == 200, response.text
    renamed = response.json()
    assert renamed["id"] == case_id
    assert renamed["question"] == "Why did Q3 revenue decline?"
    assert renamed["dataset"] == "q3_sales.csv"

    # The rename survives a new session and does not touch the case's data.
    with TestClient(app) as client:
        stored = client.get(f"/cases/{case_id}").json()
        assert stored["question"] == "Why did Q3 revenue decline?"
        assert len(client.get(f"/cases/{case_id}/runs").json()) == 1


def test_rename_one_field_leaves_the_other(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        response = client.patch(
            f"/cases/{case_id}", json={"question": "New question"}
        )

    assert response.status_code == 200
    assert response.json()["question"] == "New question"
    assert response.json()["dataset"] == "sales.csv"


def test_rename_unknown_case_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        response = client.patch("/cases/nope", json={"question": "x"})

    assert response.status_code == 404


def test_duplicate_is_deep_and_independent(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        original_counts = _counts(client, case_id)
        response = client.post(f"/cases/{case_id}/duplicate")

    assert response.status_code == 201, response.text
    copy = response.json()
    assert copy["id"] != case_id
    assert copy["question"] == "Why did revenue decline?"

    with TestClient(app) as client:
        assert _counts(client, copy["id"]) == original_counts
        original = client.get(f"/cases/{case_id}").json()
        assert original["question"] == "Why did revenue decline?"

        # IDs are all new: no child is shared with the original.
        copy_runs = client.get(f"/cases/{copy['id']}/runs").json()
        original_runs = client.get(f"/cases/{case_id}/runs").json()
        assert {r["id"] for r in copy_runs}.isdisjoint(
            {r["id"] for r in original_runs}
        )

        # Mutating the copy leaves the original untouched.
        client.patch(f"/cases/{copy['id']}", json={"question": "copy question"})
        assert client.get(f"/cases/{case_id}").json()["question"] == \
            "Why did revenue decline?"


def test_duplicate_copies_dataset_bytes_and_chart_artifacts(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        copy_id = client.post(f"/cases/{case_id}/duplicate").json()["id"]

        copy_dataset = client.get(f"/cases/{copy_id}/datasets").json()[0]
        original_dataset = client.get(f"/cases/{case_id}/datasets").json()[0]

    assert copy_dataset["id"] != original_dataset["id"]
    copy_file = Path(copy_dataset["stored_path"])
    original_file = Path(original_dataset["stored_path"])
    assert copy_file.read_bytes() == original_file.read_bytes()
    # The copy's files live in its own directory, never the original's.
    assert copy_file.parent != original_file.parent
    assert len(list((db_module.DATA_DIR / copy_id).glob("chart_*.svg"))) == 1


def test_duplicate_unknown_case_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        response = client.post("/cases/nope/duplicate")

    assert response.status_code == 404


def test_delete_removes_case_and_its_data(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _full_case(client)
        run_id = _first_run(client, case_id)
        response = client.delete(f"/cases/{case_id}")

    assert response.status_code == 204

    with TestClient(app) as client:
        assert client.get(f"/cases/{case_id}").status_code == 404
        assert client.get(f"/cases/{case_id}/datasets").status_code == 404
        assert client.get(f"/cases/{case_id}/runs").status_code == 404
        assert client.get(f"/cases/{case_id}/runs/{run_id}").status_code == 404
        assert client.get(f"/cases").json() == []

    # The on-disk directory is gone, along with the dataset and chart files.
    assert not (db_module.DATA_DIR / case_id).exists()


def test_delete_is_idempotent_for_unknown_case(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        response = client.delete("/cases/nope")

    assert response.status_code == 404


def test_delete_does_not_touch_other_cases(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        keep_id = _full_case(client)
        delete_id = _full_case(client)
        client.delete(f"/cases/{delete_id}")

    with TestClient(app) as client:
        assert client.get(f"/cases/{keep_id}").status_code == 200
        assert len(client.get(f"/cases/{keep_id}/runs").json()) == 1
