import json

from fastapi.testclient import TestClient

import app.planner as planner_module
from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n4,,south\n"


def _temp_env(tmp_path, monkeypatch):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    # Tests must not pick up a real key from the environment.
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def _case_with_profile(client) -> tuple[str, str]:
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    return case_id, dataset_id


def test_plan_is_created_and_retrievable(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_profile(client)
        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")

    assert response.status_code == 201, response.text
    plan = response.json()
    assert plan["case_id"] == case_id
    assert plan["dataset_id"] == dataset_id
    assert plan["question"] == "Why did revenue decline?"
    assert plan["source"] == planner_module.SOURCE_DETERMINISTIC
    body = plan["plan"]
    assert body["objective"] == "Why did revenue decline?"
    assert body["sub_questions"]
    assert all("statement" in h and "check" in h for h in body["hypotheses"])
    plan_id = plan["id"]

    # The plan survives a new session.
    with TestClient(app) as client:
        stored = client.get(f"/cases/{case_id}/datasets/{dataset_id}/plan")

    assert stored.status_code == 200
    assert stored.json()["id"] == plan_id
    assert stored.json()["plan"] == body


def test_plan_references_real_columns(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_profile(client)
        body = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/plan"
        ).json()["plan"]

    # The plan is derived from the profile, not generic: every sub-question and
    # hypothesis should mention at least one real column or a real property.
    text = json.dumps(body)
    for column in ("revenue", "region"):
        assert column in text
    # The profiled null in revenue is surfaced as a missingness hypothesis.
    assert "null" in text.lower()


def test_plan_without_profile_returns_400(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        ).json()["id"]
        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")

    assert response.status_code == 400
    assert "profile" in response.json()["detail"]


def test_plan_unknown_dataset_returns_404(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "s.csv"}
        ).json()["id"]
        response = client.post(f"/cases/{case_id}/datasets/nope/plan")

    assert response.status_code == 404


def test_list_plans_newest_first(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_profile(client)
        first = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan").json()["id"]
        second = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan").json()["id"]
        listed = client.get(f"/cases/{case_id}/datasets/{dataset_id}/plans").json()

    assert [p["id"] for p in listed] == [second, first]
    # Summaries omit the plan body.
    assert all("plan" not in p for p in listed)

    # The latest endpoint agrees with the head of the list.
    with TestClient(app) as client:
        latest = client.get(f"/cases/{case_id}/datasets/{dataset_id}/plan").json()
    assert latest["id"] == second


class _FailingLLM:
    def plan(self, question, profile):
        raise RuntimeError("LLM unavailable")


class _MalformedLLM:
    def plan(self, question, profile):
        return {"objective": "", "sub_questions": "not a list"}


class _GoodLLM:
    def plan(self, question, profile):
        return {
            "objective": question,
            "primary_question": question,
            "sub_questions": ["LLM sub-question one?"],
            "hypotheses": [
                {"statement": "LLM hypothesis", "rationale": "why", "check": "how"}
            ],
            "data_requirements": [{"requirement": "columns", "detail": "revenue"}],
            "analysis_steps": [{"action": "measure", "detail": "sum revenue"}],
        }


def test_llm_failure_falls_back_to_deterministic(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(planner_module, "_configured_llm", lambda: _FailingLLM())

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_profile(client)
        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")

    assert response.status_code == 201
    assert response.json()["source"] == planner_module.SOURCE_DETERMINISTIC


def test_malformed_llm_output_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(planner_module, "_configured_llm", lambda: _MalformedLLM())

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_profile(client)
        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")

    assert response.status_code == 201
    assert response.json()["source"] == planner_module.SOURCE_DETERMINISTIC


def test_valid_llm_output_is_persisted_as_llm(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(planner_module, "_configured_llm", lambda: _GoodLLM())

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_profile(client)
        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")

    assert response.status_code == 201
    plan = response.json()
    assert plan["source"] == planner_module.SOURCE_LLM
    assert plan["plan"]["sub_questions"] == ["LLM sub-question one?"]


def test_validate_plan_rejects_malformed_shapes() -> None:
    assert planner_module.validate_plan("not an object")
    assert planner_module.validate_plan({"objective": ""})
    assert planner_module.validate_plan({"objective": "x", "sub_questions": ["ok", 5]})
    assert planner_module.validate_plan(
        {
            "objective": "x",
            "primary_question": "x",
            "sub_questions": ["q"],
            "hypotheses": [{"statement": "s"}],
            "data_requirements": [],
            "analysis_steps": [],
        }
    )
    assert planner_module.validate_plan(
        {
            "objective": "x",
            "primary_question": "x",
            "sub_questions": ["q"],
            "hypotheses": [
                {"statement": "s", "rationale": "r", "check": "c"}
            ],
            "data_requirements": [],
            "analysis_steps": [{"action": "a", "detail": "d"}],
        }
    ) == []


def test_plan_survives_case_duplicate_and_delete(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)

    with TestClient(app) as client:
        case_id, dataset_id = _case_with_profile(client)
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
        copy_id = client.post(f"/cases/{case_id}/duplicate").json()["id"]
        copy_dataset = client.get(f"/cases/{copy_id}/datasets").json()[0]["id"]
        copy_plan = client.get(f"/cases/{copy_id}/datasets/{copy_dataset}/plan")

    assert copy_plan.status_code == 200
    assert copy_plan.json()["source"] == planner_module.SOURCE_DETERMINISTIC

    with TestClient(app) as client:
        client.delete(f"/cases/{case_id}")
        assert client.get(f"/cases/{case_id}/datasets/{dataset_id}/plan").status_code == 404
