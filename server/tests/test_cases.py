from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db


def _temp_db(tmp_path):
    """Point the app at a fresh on-disk SQLite file for this test."""
    db_path = tmp_path / "test.db"

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    return db_path


def test_create_and_reopen_case(tmp_path) -> None:
    """The golden test: a case survives being saved and reopened."""
    _temp_db(tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/cases",
            json={"question": "Why did revenue decline?", "dataset": "sales.csv"},
        )
        assert response.status_code == 201
        created = response.json()
        case_id = created["id"]

    # A brand-new client simulates reopening the application later.
    with TestClient(app) as client:
        reopened = client.get(f"/cases/{case_id}")

    assert reopened.status_code == 200
    assert reopened.json()["question"] == "Why did revenue decline?"
    assert reopened.json()["dataset"] == "sales.csv"
    assert reopened.json()["id"] == case_id

    app.dependency_overrides.clear()


def test_get_unknown_case_returns_404(tmp_path) -> None:
    _temp_db(tmp_path)

    with TestClient(app) as client:
        response = client.get("/cases/does-not-exist")

    assert response.status_code == 404

    app.dependency_overrides.clear()


def test_list_cases(tmp_path) -> None:
    _temp_db(tmp_path)

    with TestClient(app) as client:
        client.post("/cases", json={"question": "first", "dataset": "a.csv"})
        client.post("/cases", json={"question": "second", "dataset": "b.csv"})
        response = client.get("/cases")

    assert response.status_code == 200
    assert len(response.json()) == 2

    app.dependency_overrides.clear()
