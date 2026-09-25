"""Code generation tests for P3-AI-013.

Writing the analysis is the part of the loop a non-programmer analyst cannot do
alone, so this slice proposes the computation that would answer a question - and
stops one step short of running it. These cover the deterministic proposal, the
column-honesty budget (a proposal may only read columns the dataset has), the
read-only constraint, the LLM path and its failure modes, the no-state property,
the accept-then-run round trip through the existing endpoints, and the 404/400
contract.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module
import app.generator as generator_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"


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


def _case_with_dataset(client):
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    return case_id, dataset_id


class _GoodGenerator:
    def generate(self, question, profile, kind):
        return {
            "kind": "sql",
            "code": (
                "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
                "GROUP BY region ORDER BY total DESC"
            ),
            "explanation": "Sums revenue by region so the leaders can be compared.",
        }


class _InventingGenerator:
    def generate(self, question, profile, kind):
        return {
            "kind": "sql",
            "code": (
                "SELECT region, revenue, lifetime_value FROM read_csv_auto(?) "
                "GROUP BY region"
            ),
            "explanation": "Reads a column the dataset does not have.",
        }


class _DeletingGenerator:
    def generate(self, question, profile, kind):
        return {
            "kind": "sql",
            "code": "DELETE FROM read_csv_auto(?)",
            "explanation": "Not a read-only statement.",
        }


class _FailingGenerator:
    def generate(self, *args, **kwargs):
        raise RuntimeError("LLM unavailable")


class _MalformedGenerator:
    def generate(self, *args, **kwargs):
        return {"kind": "sql", "code": "", "explanation": ""}


def test_deterministic_proposal_names_the_datasets_real_columns(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads on revenue?"},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == generator_module.SOURCE_DETERMINISTIC
    assert body["dataset_id"] == dataset_id
    for field in ("code", "explanation"):
        assert body[field].strip(), f"{field} must be non-empty"
    # revenue is the measure and region the dimension - not order_id, which is a
    # unique identifier and so nothing to sum.
    assert "SUM(revenue)" in body["code"]
    assert "region" in body["code"]
    assert "order_id" not in body["code"]
    assert set(body["columns_used"]) <= {"revenue", "region"}


def test_every_column_the_proposal_reads_is_a_real_profiled_column(
    tmp_path, monkeypatch
) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        body = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads?", "kind": "python"},
        ).json()
        profile = client.get(
            f"/cases/{case_id}/datasets/{dataset_id}/profile"
        ).json()

    profiled = set(profile["columns"])
    assert body["columns_used"]
    assert set(body["columns_used"]) <= profiled


def test_a_generated_sql_proposal_runs_as_is(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        proposal = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads on revenue?"},
        ).json()

        # Acceptance is the existing runs endpoint - the only path that persists
        # a run, which is what keeps the human in charge of what executes.
        run = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": proposal["code"]},
        )

    assert run.status_code == 201, run.text
    body = run.json()
    assert body["columns"]
    assert body["row_count"] >= 1


def test_a_generated_python_proposal_runs_and_tabulates(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        proposal = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads on revenue?", "kind": "python"},
        ).json()
        assert proposal["kind"] == "python"

        run = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
            json={"code": proposal["code"]},
        )

    assert run.status_code == 201, run.text
    body = run.json()
    # The snippet leaves a list of dicts in `result`, which the runner tabulates.
    assert "total_revenue" in body["columns"]
    assert body["row_count"] == 2


def test_the_deterministic_proposal_is_a_single_read_only_statement(
    tmp_path, monkeypatch
) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        body = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Anything"},
        ).json()

    code = body["code"].strip()
    assert ";" not in code
    assert code.lower().startswith("select")


def test_an_llm_proposal_reading_real_columns_is_accepted(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(generator_module, "_configured_llm", lambda: _GoodGenerator())
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads?"},
        )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["source"] == generator_module.SOURCE_LLM
    assert body["code"].startswith("SELECT region")
    assert body["columns_used"] == ["revenue", "region"]


def test_an_llm_proposal_that_invents_a_column_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(generator_module, "_configured_llm", lambda: _InventingGenerator())
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads?"},
        ).json()

    # lifetime_value is nowhere in the dataset, so the LLM cannot be trusted to
    # write the computation that answers the question.
    assert response["source"] == generator_module.SOURCE_DETERMINISTIC_FALLBACK
    assert "lifetime_value" not in response["code"]


def test_an_llm_proposal_that_is_not_read_only_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(generator_module, "_configured_llm", lambda: _DeletingGenerator())
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Clean up?"},
        ).json()

    assert response["source"] == generator_module.SOURCE_DETERMINISTIC_FALLBACK
    assert "DELETE" not in response["code"]


def test_an_llm_failure_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(generator_module, "_configured_llm", lambda: _FailingGenerator())
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads?"},
        )

    assert response.status_code == 200
    assert response.json()["source"] == generator_module.SOURCE_DETERMINISTIC_FALLBACK


def test_malformed_llm_output_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(generator_module, "_configured_llm", lambda: _MalformedGenerator())
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads?"},
        )

    assert response.status_code == 200
    assert response.json()["source"] == generator_module.SOURCE_DETERMINISTIC_FALLBACK


def test_generation_writes_no_state(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads?"},
        )
        for kind in ("sql", "python"):
            client.post(
                f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
                json={"question": "Again", "kind": kind},
            )
        # A proposal is not a run: generating for both kinds created nothing.
        runs = client.get(f"/cases/{case_id}/runs")

    assert runs.status_code == 200
    assert runs.json() == []


def test_generation_refuses_an_unprofiled_dataset(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "sales.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        ).json()["id"]

        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "Which region leads?"},
        )

    assert response.status_code == 400
    assert "profile" in response.json()["detail"]


def test_404s_for_unknown_and_cross_case_datasets(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, dataset_id = _case_with_dataset(client)
        other_case = client.post(
            "/cases", json={"question": "Other?", "dataset": "o.csv"}
        ).json()["id"]

        assert (
            client.post(
                f"/cases/no-such-case/datasets/{dataset_id}/generate-code",
                json={"question": "q"},
            ).status_code
            == 404
        )
        assert (
            client.post(
                f"/cases/{case_id}/datasets/no-such-dataset/generate-code",
                json={"question": "q"},
            ).status_code
            == 404
        )
        # A dataset belonging to another case is not reachable through this path.
        assert (
            client.post(
                f"/cases/{other_case}/datasets/{dataset_id}/generate-code",
                json={"question": "q"},
            ).status_code
            == 404
        )
