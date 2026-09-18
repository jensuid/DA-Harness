from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"id,name,score\n1,alice,90\n2,,75\n3,bob,\n"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _attach(client, case_id: str) -> str:
    response = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("data.csv", CSV, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_profile_and_reopen(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "data.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id)

        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        assert response.status_code == 201
        profile = response.json()
        assert profile["rows"] == 3
        assert profile["columns"] == ["id", "name", "score"]
        assert profile["stats"]["name"]["null_count"] == 1

    # Reopen: the stored profile survives a fresh client.
    with TestClient(app) as client:
        stored = client.get(f"/cases/{case_id}/datasets/{dataset_id}/profile")

    assert stored.status_code == 200
    assert stored.json()["rows"] == 3
    assert stored.json()["stats"]["score"]["null_count"] == 1


def test_profile_unknown_dataset_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "data.csv"}
        ).json()["id"]
        response = client.post(
            f"/cases/{case_id}/datasets/does-not-exist/profile"
        )

    assert response.status_code == 404


def test_get_profile_before_profiling_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "data.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id)
        response = client.get(f"/cases/{case_id}/datasets/{dataset_id}/profile")

    assert response.status_code == 404
