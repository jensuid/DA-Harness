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


# W2X-010: the second walk-test's last finding. The list showed two rows for
# the same question and the same dataset with nothing to tell them apart but a
# timestamp nobody reads, and the gap was that nobody said so. The pair is not
# a constraint - a duplicate is a case in its own right and re-running an old
# question is a normal thing to do - so the answer is a name, not a refusal.
def test_a_first_case_is_no_ones_duplicate(tmp_path) -> None:
    """A case with no predecessor carries a null `duplicate_of`."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        response = client.post(
            "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
        )
        reopened = client.get(f"/cases/{response.json()['id']}")

    assert response.status_code == 201
    assert response.json()["duplicate_of"] is None
    assert reopened.json()["duplicate_of"] is None

    app.dependency_overrides.clear()


def test_a_second_identical_case_names_the_first(tmp_path) -> None:
    """The same question+dataset answers with the existing case's id."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        first = client.post(
            "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
        ).json()
        second = client.post(
            "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
        ).json()

    assert second["id"] != first["id"]
    assert second["duplicate_of"] == first["id"]

    app.dependency_overrides.clear()


def test_a_case_is_flagged_in_the_listing_and_on_reopen(tmp_path) -> None:
    """Both reads carry the pointer: the list is where the rows collided."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        first = client.post(
            "/cases", json={"question": "q", "dataset": "sales.csv"}
        ).json()
        second = client.post(
            "/cases", json={"question": "q", "dataset": "sales.csv"}
        ).json()
        listed = client.get("/cases").json()
        reopened = client.get(f"/cases/{second['id']}").json()

    by_id = {case["id"]: case for case in listed}
    assert by_id[second["id"]]["duplicate_of"] == first["id"]
    assert by_id[first["id"]]["duplicate_of"] is None
    assert reopened["duplicate_of"] == first["id"]

    app.dependency_overrides.clear()


def test_a_question_alone_is_not_a_duplicate(tmp_path) -> None:
    """The pair must match exactly; a shared question is a different case."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        client.post("/cases", json={"question": "q", "dataset": "sales.csv"})
        other = client.post("/cases", json={"question": "q", "dataset": "users.csv"})

    assert other.json()["duplicate_of"] is None

    app.dependency_overrides.clear()


def test_a_dataset_alone_is_not_a_duplicate(tmp_path) -> None:
    """And a shared dataset is a different case the same way."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        client.post("/cases", json={"question": "one", "dataset": "sales.csv"})
        other = client.post("/cases", json={"question": "two", "dataset": "sales.csv"})

    assert other.json()["duplicate_of"] is None

    app.dependency_overrides.clear()


def test_the_pair_is_compared_exactly_not_caselessly(tmp_path) -> None:
    """A difference only in case is a real difference the flag does not paper over."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        client.post("/cases", json={"question": "Why?", "dataset": "sales.csv"})
        other = client.post("/cases", json={"question": "WHY?", "dataset": "sales.csv"})

    assert other.json()["duplicate_of"] is None

    app.dependency_overrides.clear()


def test_the_flag_points_at_the_most_recent_predecessor(tmp_path) -> None:
    """Two predecessors name the newer one, so the notice reaches the nearest case."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        first = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()
        second = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()
        third = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()

    assert second["duplicate_of"] == first["id"]
    assert third["duplicate_of"] == second["id"]

    app.dependency_overrides.clear()


def test_the_flag_survives_a_store_reopen(tmp_path) -> None:
    """The pointer is a column, not an in-memory derivation, so it persists."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        first = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()
        second_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]

    # A brand-new client simulates reopening the application later.
    with _client(db_path) as client:
        reopened = client.get(f"/cases/{second_id}").json()
        listed = client.get("/cases").json()

    assert reopened["duplicate_of"] == first["id"]
    assert [case["duplicate_of"] for case in listed
            if case["id"] == second_id] == [first["id"]]

    app.dependency_overrides.clear()


def test_a_duplicated_case_keeps_the_flag_the_source_carried(tmp_path) -> None:
    """A duplicate-of-duplicate is a case in its own right (P2-CASE-010) and
    keeps the lineage it repeated rather than naming the case it was made
    from."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        first = client.post("/cases", json={"question": "q", "dataset": "s.csv"}).json()
        second = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()
        copy = client.post(f"/cases/{second['id']}/duplicate").json()

    assert copy["id"] != second["id"]
    # The copy repeats the case its source repeated, not its source.
    assert copy["duplicate_of"] == second["duplicate_of"] == first["id"]

    app.dependency_overrides.clear()


def test_a_duplicated_case_with_no_predecessor_is_no_ones_duplicate(
    tmp_path,
) -> None:
    """The same path on a case with nothing to repeat carries no pointer."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        first = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()
        copy = client.post(f"/cases/{first['id']}/duplicate").json()

    assert copy["duplicate_of"] is None

    app.dependency_overrides.clear()


def test_the_flag_degrades_to_none_when_its_case_is_deleted(tmp_path) -> None:
    """The pointer is advisory: deleting the case it names leaves no error."""
    db_path = _temp_db(tmp_path)
    with _client(db_path) as client:
        first = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()
        second_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        client.delete(f"/cases/{first['id']}")
        reopened = client.get(f"/cases/{second_id}").json()
        listed = [case for case in client.get("/cases").json()
                  if case["id"] == second_id]

    # A dangling pointer still reads, because nothing joins on it.
    assert reopened["duplicate_of"] == first["id"]
    assert listed[0]["duplicate_of"] == first["id"]

    app.dependency_overrides.clear()
