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


def _client(db_path):
    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    return TestClient(app)


def test_search_filters_question_case_insensitively(tmp_path) -> None:
    """`q` matches the question, ignoring case (P3-CASE-007)."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        client.post("/cases", json={"question": "Why did REVENUE decline?",
                                    "dataset": "sales.csv"})
        client.post("/cases", json={"question": "Churn drivers",
                                    "dataset": "users.csv"})
        hits = client.get("/cases", params={"q": "revenue"}).json()

    assert len(hits) == 1
    assert "REVENUE" in hits[0]["question"]

    app.dependency_overrides.clear()


def test_search_matches_dataset_label(tmp_path) -> None:
    """`q` also matches the dataset label."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        client.post("/cases", json={"question": "one", "dataset": "sales_q3.csv"})
        client.post("/cases", json={"question": "two", "dataset": "users.csv"})
        hits = client.get("/cases", params={"q": "SALES"}).json()

    assert len(hits) == 1
    assert hits[0]["dataset"] == "sales_q3.csv"

    app.dependency_overrides.clear()


def test_search_treats_term_as_literal_not_wildcard(tmp_path) -> None:
    """A `%` or `_` in the term is literal, not a LIKE wildcard."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        client.post("/cases", json={"question": "Growth 50% in q3",
                                    "dataset": "a.csv"})
        client.post("/cases", json={"question": "Growth 50x in q3",
                                    "dataset": "b.csv"})
        client.post("/cases", json={"question": "code q1_1 run",
                                    "dataset": "c.csv"})
        client.post("/cases", json={"question": "code q1a1 run",
                                    "dataset": "d.csv"})
        percent = client.get("/cases", params={"q": "50%"}).json()
        underscore = client.get("/cases", params={"q": "q1_1"}).json()

    assert [hit["question"] for hit in percent] == ["Growth 50% in q3"]
    # A wildcard `_` would match either; escaped, it matches only the literal.
    assert [hit["question"] for hit in underscore] == ["code q1_1 run"]

    app.dependency_overrides.clear()


def test_search_without_q_lists_everything(tmp_path) -> None:
    """Absent or blank `q` is not a filter."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        client.post("/cases", json={"question": "one", "dataset": "a.csv"})
        client.post("/cases", json={"question": "two", "dataset": "b.csv"})
        all_cases = client.get("/cases").json()
        blank = client.get("/cases", params={"q": "  "}).json()
        no_hits = client.get("/cases", params={"q": "zzz"}).json()

    assert len(all_cases) == 2
    assert len(blank) == 2
    assert no_hits == []

    app.dependency_overrides.clear()
