"""P8-CONTEXT-001: a case carries the analyst's stated intent.

The primary question stays on the case row; this is what a question alone
cannot carry - why the analysis matters, what it would answer in pieces, what
it would test, and what it is assuming.
"""
from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"id,name,score\n1,alice,90\n2,,75\n3,bob,60\n"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case(client, question: str = "q") -> str:
    return client.post("/cases", json={"question": question, "dataset": "d.csv"}).json()["id"]


def test_context_defaults_to_empty_without_a_404(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client)
        response = client.get(f"/cases/{case_id}/context")

    assert response.status_code == 200
    body = response.json()
    assert body["case_id"] == case_id
    assert body["purpose"] == ""
    assert body["sub_questions"] == []
    # An unset context is the honest empty, not an error the analyst caused.
    assert body["updated_at"] is None


def test_context_persists_and_reopens(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client)
        put = client.put(
            f"/cases/{case_id}/context",
            json={
                "purpose": "Understand the Q3 revenue dip",
                "sub_questions": ["Is it west?", "Is it Q3 only?"],
                "hypotheses": ["West drove the decline"],
                "constraints": ["Customer-level data unavailable"],
            },
        )
        assert put.status_code == 200
        assert put.json()["updated_at"] is not None

    # Reopen: the stored context survives a fresh client, like every artifact.
    with TestClient(app) as client:
        stored = client.get(f"/cases/{case_id}/context")

    assert stored.status_code == 200
    body = stored.json()
    assert body["purpose"] == "Understand the Q3 revenue dip"
    assert body["sub_questions"] == ["Is it west?", "Is it Q3 only?"]
    assert body["hypotheses"] == ["West drove the decline"]
    assert body["constraints"] == ["Customer-level data unavailable"]


def test_editing_replaces_wholesale_and_persists(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client)
        client.put(
            f"/cases/{case_id}/context",
            json={"purpose": "first", "sub_questions": ["a"], "hypotheses": [],
                  "constraints": []},
        )
        second = client.put(
            f"/cases/{case_id}/context",
            json={"purpose": "second", "sub_questions": ["b", "c"],
                  "hypotheses": ["h2"], "constraints": []},
        )
        assert second.json()["purpose"] == "second"
        assert second.json()["sub_questions"] == ["b", "c"]

    with TestClient(app) as client:
        body = client.get(f"/cases/{case_id}/context").json()

    # The latest version is what reopen restores, not a merge of the two.
    assert body["purpose"] == "second"
    assert body["sub_questions"] == ["b", "c"]
    assert body["hypotheses"] == ["h2"]


def test_context_is_rejected_for_an_unknown_case(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        missing = client.get("/cases/nope/context")
        assert missing.status_code == 404

        put = client.put("/cases/nope/context", json={"purpose": "x"})
        assert put.status_code == 404


def test_malformed_context_answers_400_and_changes_nothing(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client)
        # An empty entry is not a sub-question.
        bad = client.put(
            f"/cases/{case_id}/context",
            json={"purpose": "p", "sub_questions": ["ok", "   "], "hypotheses": [],
                  "constraints": []},
        )
        assert bad.status_code == 400

        # Nothing was written: the 400 changed no state.
        assert client.get(f"/cases/{case_id}/context").json()["purpose"] == ""

        # Too many entries is a 400 naming the limit, not a silent truncation.
        many = client.put(
            f"/cases/{case_id}/context",
            json={"purpose": "p", "sub_questions": [f"q{i}" for i in range(50)],
                  "hypotheses": [], "constraints": []},
        )
        assert many.status_code == 400
        assert "sub_questions" in many.json()["detail"]


def test_plan_records_the_context_fields_it_read(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client, "Why did revenue dip?")
        dataset_id = client.post(
            "/cases/{case_id}/datasets".replace("{case_id}", case_id),
            files={"file": ("d.csv", CSV, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        client.put(
            f"/cases/{case_id}/context",
            json={
                "purpose": "Understand the dip",
                "sub_questions": ["Is it concentrated in one region?"],
                "hypotheses": ["A single region drove it"],
                "constraints": [],
            },
        )
        plan = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/plan"
        ).json()["plan"]

        # The analyst's intent is recorded as the basis, and their sub-question
        # outranks the ones the profile suggested.
        assert "purpose" in plan["context_basis"]
        assert any("sub_questions" in part for part in plan["context_basis"])
        assert plan["sub_questions"][0] == "Is it concentrated in one region?"
        # A hypothesis recorded as intent is carried as the analyst's own.
        assert any(
            h["statement"] == "A single region drove it" for h in plan["hypotheses"]
        )


def test_plan_without_context_records_no_basis(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client, "Why did revenue dip?")
        dataset_id = client.post(
            "/cases/{case_id}/datasets".replace("{case_id}", case_id),
            files={"file": ("d.csv", CSV, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        plan = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/plan"
        ).json()["plan"]

    assert plan["context_basis"] == []


def test_context_survives_the_export_round_trip(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client, "Why did revenue dip?")
        client.put(
            f"/cases/{case_id}/context",
            json={
                "purpose": "Understand the dip",
                "sub_questions": ["Is it west?", "Is it Q3?", "Is it one product?"],
                "hypotheses": ["West drove it", "A price change explains it"],
                "constraints": ["No customer-level data"],
            },
        )
        package = client.get(f"/cases/{case_id}/export").json()
        assert package["context"]["purpose"] == "Understand the dip"
        assert len(package["context"]["sub_questions"]) == 3
        assert len(package["context"]["hypotheses"]) == 2

        restored = client.post("/cases/import", json=package).json()

    with TestClient(app) as client:
        body = client.get(f"/cases/{restored['id']}/context").json()

    # Three sub-questions and two hypotheses land intact on the restored case.
    assert body["purpose"] == "Understand the dip"
    assert body["sub_questions"] == ["Is it west?", "Is it Q3?", "Is it one product?"]
    assert body["hypotheses"] == ["West drove it", "A price change explains it"]
    assert body["constraints"] == ["No customer-level data"]


def test_an_older_package_without_context_degrades_to_empty(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client, "q")
        package = client.get(f"/cases/{case_id}/export").json()
        # A package exported before the context object existed has no section.
        package.pop("context", None)
        restored = client.post("/cases/import", json=package).json()

    with TestClient(app) as client:
        body = client.get(f"/cases/{restored['id']}/context").json()

    assert body["purpose"] == ""
    assert body["sub_questions"] == []


def test_duplicate_carries_the_context(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client, "q")
        client.put(
            f"/cases/{case_id}/context",
            json={"purpose": "p", "sub_questions": ["s"], "hypotheses": [],
                  "constraints": []},
        )
        duplicate = client.post(f"/cases/{case_id}/duplicate").json()
        body = client.get(f"/cases/{duplicate['id']}/context").json()

    assert body["purpose"] == "p"
    assert body["sub_questions"] == ["s"]


def test_delete_removes_the_context(tmp_path) -> None:
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client, "q")
        client.put(
            f"/cases/{case_id}/context",
            json={"purpose": "p", "sub_questions": [], "hypotheses": [],
                  "constraints": []},
        )
        client.delete(f"/cases/{case_id}")
        assert client.get(f"/cases/{case_id}/context").status_code == 404


def test_a_pre_v10_store_upgrades_and_keeps_its_rows(tmp_path) -> None:
    """A store written at schema 9 opens, gains the contexts table, and loses
    nothing it already held."""
    import sqlite3

    db_path = tmp_path / "v9.db"
    conn = sqlite3.connect(db_path)
    conn.executescript(
        "CREATE TABLE cases (id TEXT PRIMARY KEY, question TEXT NOT NULL, "
        "dataset TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);"
        "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "applied_at TEXT NOT NULL);"
        "INSERT INTO cases VALUES ('c1', 'why?', 'd.csv', '2026-01-01', '2026-01-01');"
        "INSERT INTO schema_migrations VALUES (9, 'agent_steps role', '2026-01-01');"
    )
    conn.execute("PRAGMA user_version = 9")
    conn.commit()
    conn.close()

    db_module.DATA_DIR = tmp_path / "data"
    from app.db import LATEST_SCHEMA_VERSION, get_connection

    with get_connection(db_path) as upgraded:
        version = upgraded.execute("PRAGMA user_version").fetchone()[0]
        table = upgraded.execute(
            "SELECT name FROM sqlite_master WHERE name = 'contexts'"
        ).fetchone()
        kept = upgraded.execute("SELECT question FROM cases").fetchone()

    # The store reaches whatever the current build's schema is, not a number
    # pinned here: a later migration lands and this assertion stays true while
    # still proving the upgrade ran and the row survived.
    assert version == LATEST_SCHEMA_VERSION
    assert table is not None
    assert kept["question"] == "why?"
