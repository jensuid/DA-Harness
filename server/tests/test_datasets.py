from fastapi.testclient import TestClient

from app.db import DATA_DIR, get_connection
from app.main import app, get_db


def _temp_env(tmp_path):
    """Point the app at a fresh DB and on-disk data dir for this test."""
    import app.db as db_module

    db_path = tmp_path / "test.db"
    data_dir = tmp_path / "data"
    db_module.DATA_DIR = data_dir
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    return data_dir


CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n"


def _make_case(client) -> str:
    response = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    )
    return response.json()["id"]


def test_attach_and_reopen_dataset(tmp_path) -> None:
    data_dir = _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )
        assert response.status_code == 201
        dataset = response.json()
        assert dataset["filename"] == "sales.csv"
        assert (data_dir / case_id / f"{dataset['id']}.csv").exists()

    # Reopen in a fresh client - the dataset must still be listed.
    with TestClient(app) as client:
        listed = client.get(f"/cases/{case_id}/datasets")

    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["filename"] == "sales.csv"


def test_attach_to_unknown_case_returns_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        response = client.post(
            "/cases/does-not-exist/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        )

    assert response.status_code == 404


def test_attach_rejects_non_csv(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("notes.txt", b"hello", "text/plain")},
        )

    assert response.status_code == 400


def test_attach_rejects_empty_file(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _make_case(client)
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("empty.csv", b"   ", "text/csv")},
        )

    assert response.status_code == 400
