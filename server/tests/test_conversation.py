"""Conversational memory tests for P3-AI-014.

The last assistant slice: the case can be asked questions and answers cite the
artifact behind each claim. These cover the deterministic answer for counts,
columns and the case stage, the citation-honesty budget, the LLM path and its
failure modes, memory (the prior turn reaches the LLM), persistence
oldest-first, cleanup on case deletion, and the 404 contract.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module
import app.assistant as assistant_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)


def _temp_env(tmp_path, monkeypatch):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:  # pragma: no cover - generator
            yield connection

    app.dependency_overrides[get_db] = override
    # No key by default, so the deterministic engine speaks unless a test
    # installs a fake one - the suite never makes a live call.
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def _case_with_data(client):
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    return case_id, dataset_id


def _ask(client, case_id, message):
    return client.post(f"/cases/{case_id}/chat", json={"message": message}).json()


class _CapturingAssistant:
    """Records the turns it was given, so a test can prove memory reached it."""

    def __init__(self, seen):
        self._seen = seen

    def answer(self, message, history, facts):
        self._seen["message"] = message
        self._seen["history"] = list(history)
        self._seen["facts"] = facts
        return {
            "answer": f"The case has {len(facts.get('runs') or [])} run(s).",
            "grounds": [f"dataset:{facts['datasets'][0]['label']}"],
        }


class _InventingAssistant:
    def answer(self, message, history, facts):
        return {
            "answer": "The revenue is 9999.0.",
            "grounds": ["run:does-not-exist"],
        }


class _FailingAssistant:
    def answer(self, *args, **kwargs):
        raise RuntimeError("LLM unavailable")


class _MalformedAssistant:
    def answer(self, *args, **kwargs):
        return {"answer": "Some answer."}


def test_count_question_is_answered_with_real_counts(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_data(client)
        client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        )
        body = _ask(client, case_id, "How many runs have I done?")

    assert body["source"] == assistant_module.SOURCE_DETERMINISTIC
    assert "1 run(s)" in body["answer"]
    assert "1 dataset(s)" in body["answer"]


def test_column_question_is_answered_with_the_columns_real_stats(
    tmp_path, monkeypatch
) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        body = _ask(client, case_id, "What does the revenue column look like?")

    assert body["source"] == assistant_module.SOURCE_DETERMINISTIC
    # Every figure comes from the profile: revenue spans 80.5 to 200.0.
    assert "revenue" in body["answer"]
    assert "80.5" in body["answer"]
    assert "200.0" in body["answer"]
    assert "999" not in body["answer"]


def test_an_unspecific_question_gets_the_case_stage_and_next_action(
    tmp_path, monkeypatch
) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        body = _ask(client, case_id, "So what now?")

    assert body["source"] == assistant_module.SOURCE_DETERMINISTIC
    # The stage is derived from the artifacts, so the answer cannot claim a step
    # the data does not support: profiled but not yet planned.
    assert "plan" in body["answer"]
    assert "Next action" in body["answer"]


def test_every_ground_cites_an_artifact_the_case_has(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        for question in (
            "How many findings?",
            "Tell me about revenue",
            "What should I do next?",
        ):
            body = _ask(client, case_id, question)
            references = _references_for(case_id)
            for ground in body["grounds"]:
                kind, name = assistant_module.parse_ground(ground)
                assert name in references[kind], (
                    f"{ground} cites an artifact the case does not have"
                )


def _references_for(case_id):
    """The names a ground may cite, read from the same rows the API served."""
    with get_connection(db_module.DATA_DIR.parent / "test.db") as connection:
        facts = assistant_module.summarize_case(connection, case_id)
    return assistant_module._references(facts)


def test_an_llm_answer_citing_real_artifacts_is_accepted(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    seen: dict = {}
    monkeypatch.setattr(
        assistant_module, "_configured_llm", lambda: _CapturingAssistant(seen)
    )
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        body = _ask(client, case_id, "Summarise where things stand")

    assert body["source"] == assistant_module.SOURCE_LLM
    assert body["grounds"] == ["dataset:sales.csv"]


def test_the_llm_sees_the_prior_turns(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    seen: dict = {}
    monkeypatch.setattr(
        assistant_module, "_configured_llm", lambda: _CapturingAssistant(seen)
    )
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        _ask(client, case_id, "How many datasets?")
        _ask(client, case_id, "And what about revenue?")

    assert seen["message"] == "And what about revenue?"
    # The memory is the conversation, not just the last message.
    assert [turn["message"] for turn in seen["history"]] == ["How many datasets?"]


def test_an_llm_answer_that_invents_a_citation_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(
        assistant_module, "_configured_llm", lambda: _InventingAssistant()
    )
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        body = _ask(client, case_id, "What is the revenue?")

    # run:does-not-exist points at evidence the case does not have, so the LLM
    # cannot be the voice of this answer.
    assert body["source"] == assistant_module.SOURCE_DETERMINISTIC
    assert body["grounds"] != ["run:does-not-exist"]


def test_an_llm_failure_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(assistant_module, "_configured_llm", lambda: _FailingAssistant())
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        response = client.post(
            f"/cases/{case_id}/chat", json={"message": "Anything"}
        )

    assert response.status_code == 201, response.text
    assert response.json()["source"] == assistant_module.SOURCE_DETERMINISTIC


def test_malformed_llm_output_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(
        assistant_module, "_configured_llm", lambda: _MalformedAssistant()
    )
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        response = client.post(
            f"/cases/{case_id}/chat", json={"message": "Anything"}
        )

    assert response.status_code == 201
    assert response.json()["source"] == assistant_module.SOURCE_DETERMINISTIC


def test_the_conversation_persists_oldest_first(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        first = _ask(client, case_id, "How many runs?")
        second = _ask(client, case_id, "And revenue?")

        # A fresh session sees the whole conversation in order.
        history = client.get(f"/cases/{case_id}/chat")

    assert history.status_code == 200
    turns = history.json()
    assert [turn["message"] for turn in turns] == ["How many runs?", "And revenue?"]
    assert turns[0]["id"] == first["id"]
    assert turns[1]["id"] == second["id"]


def test_deleting_the_case_removes_its_conversation(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)
        _ask(client, case_id, "How many runs?")
        client.delete(f"/cases/{case_id}")

        # The conversation is gone with the case - asserted at the row level,
        # because no endpoint serves a deleted case.
        with get_connection(db_module.DATA_DIR.parent / "test.db") as connection:
            rows = connection.execute(
                "SELECT COUNT(*) FROM conversations WHERE case_id = ?", (case_id,)
            ).fetchone()
        assert rows[0] == 0


def test_404_for_an_unknown_case(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, _ = _case_with_data(client)

        assert (
            client.post(
                "/cases/no-such-case/chat", json={"message": "Hello"}
            ).status_code
            == 404
        )
        assert client.get("/cases/no-such-case/chat").status_code == 404
        # A real case's conversation is reachable.
        assert client.get(f"/cases/{case_id}/chat").status_code == 200
