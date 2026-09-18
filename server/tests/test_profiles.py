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


def _attach(client, case_id: str, filename: str = "data.csv",
             content: bytes = CSV) -> str:
    response = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": (filename, content, "text/csv")},
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

DEEP_CSV = (
    b"id,name,score,joined\n"
    b"1,alice,90,2023-01-01\n"
    b"2,bob,,2023-01-02\n"
    b"3,alice,90,2023-01-01\n"
    b"4,,75,2023-01-03\n"
    b"1,alice,90,2023-01-01\n"
)


def test_deep_profile_stats(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "deep.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, "deep.csv", DEEP_CSV)
        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        assert response.status_code == 201
        profile = response.json()

        # rows 1 and 5 are identical; row 3 shares name/score/date but has
        # a different id, so it is not a full-row duplicate.
        assert profile["rows"] == 5
        assert profile["duplicate_rows"] == 1

        score = profile["stats"]["score"]
        assert score["type"] == "numeric"
        assert score["null_count"] == 1
        assert score["null_percentage"] == 20.0
        # AVG ignores NULLs: four non-null scores 90+90+75+90 = 86.25.
        assert score["distinct_count"] == 2
        assert score["min"] == 75
        assert score["max"] == 90
        assert score["avg"] == 86.25

        name = profile["stats"]["name"]
        assert name["type"] == "other"
        assert name["distinct_count"] == 2
        assert "min" not in name
        assert "avg" not in name

        joined = profile["stats"]["joined"]
        assert joined["type"] == "temporal"
        assert joined["min"] == "2023-01-01"


def test_header_only_dataset_profiles_cleanly(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "empty.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, "only_headers.csv",
                             b"id,name,score\n")
        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        assert response.status_code == 201
        profile = response.json()

        assert profile["rows"] == 0
        assert profile["duplicate_rows"] == 0
        assert profile["stats"]["score"]["null_percentage"] == 0.0


def test_deep_profile_survives_reopen(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "deep.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, "deep.csv", DEEP_CSV)
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")

    with TestClient(app) as client:
        stored = client.get(f"/cases/{case_id}/datasets/{dataset_id}/profile")

    assert stored.status_code == 200
    assert stored.json()["duplicate_rows"] == 1
    assert stored.json()["stats"]["score"]["avg"] == 86.25
