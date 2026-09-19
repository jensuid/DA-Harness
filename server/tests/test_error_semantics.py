"""Error semantics: an input error answers 400, a server fault answers 500
(P4-RELIABILITY-002).

Before this task every engine endpoint ended in `except Exception: raise 400`,
which flattened a genuine server fault into a client error that blamed the
analyst. These tests pin both directions of the contract:

- input the engines reject (bad SQL, an unknown column, a sandbox rejection)
  still answer 400 with the engine's own message - narrowing the catch must
  not turn bad input into a 500;
- a fault inside the harness answers 500, so a real bug can never hide inside
  a 400.

The 500s need a TestClient with `raise_server_exceptions=False`; with the
default, Starlette re-raises unhandled exceptions in the test instead of
letting the response carry the status. The propagating exception is what makes
the 500 honest - a real run logs the traceback in the server console - and the
body is Starlette's plain-text "Internal Server Error" rather than a JSON
envelope. Giving a 500 a JSON body is an API-consistency concern for the UX
work, not part of this task: what matters here is the status code.
"""

import logging

import pytest
from fastapi.testclient import TestClient

import app.main as main_module
import app.planner as planner_module
from app.db import get_connection
from app.main import app, get_db

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"


def _temp_env(tmp_path, monkeypatch):
    """Point the app at a fresh DB and data dir, and keep the LLM off."""
    import app.db as db_module

    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    db_path = tmp_path / "test.db"
    db_module.DATA_DIR = tmp_path / "data"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_dataset(client) -> tuple[str, str]:
    case = client.post(
        "/cases",
        json={"question": "Why did revenue decline?", "dataset": "sales.csv"},
    )
    case_id = case.json()["id"]
    dataset = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    )
    return case_id, dataset.json()["id"]


def _case_with_profile(client, monkeypatch) -> tuple[str, str]:
    case_id, dataset_id = _case_with_dataset(client)
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    return case_id, dataset_id


def _client():
    return TestClient(app, raise_server_exceptions=False)


class _Boom:
    """A harness-side fault: not the input's fault, so never a 400."""

    def __call__(self, *args, **kwargs):
        raise KeyError("the harness itself broke")


# --- input errors stay 400 --------------------------------------------------


def test_sql_syntax_error_answers_400(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with _client() as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT FROM read_csv_auto(?)"},
        )
    assert response.status_code == 400
    # The engine's own message, not the old "query failed: ..." wrapper.
    assert "query failed" not in response.json()["detail"]


def test_unknown_column_answers_400(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with _client() as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT no_such_column FROM read_csv_auto(?)"},
        )
    assert response.status_code == 400


def test_multi_dataset_bad_sql_answers_400(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with _client() as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/runs",
            json={
                "sql": "SELECT no_such_column FROM read_csv_auto(?)",
                "dataset_ids": [dataset_id, dataset_id],
            },
        )
    assert response.status_code == 400


def test_python_sandbox_rejection_answers_400(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with _client() as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
            json={"code": "result = 1 + 1"},
        )
    assert response.status_code == 400
    assert "result" in response.json()["detail"]


def test_eda_unknown_op_answers_400(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with _client() as client:
        case_id, dataset_id = _case_with_dataset(client)
        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/eda",
            json={"op": "regress"},
        )
    assert response.status_code == 400


def test_chart_unknown_kind_answers_400(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with _client() as client:
        case_id, dataset_id = _case_with_dataset(client)
        run = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT region, COUNT(*) AS n FROM read_csv_auto(?) GROUP BY region"},
        )
        response = client.post(
            f"/cases/{case_id}/runs/{run.json()['id']}/charts",
            json={"kind": "pie", "x": "region", "y": "n"},
        )
    assert response.status_code == 400


# --- harness faults become 500 ---------------------------------------------


@pytest.mark.parametrize(
    "engine, path_builder",
    [
        ("run_query", "single SQL run"),
        ("run_query_multi", "multi-dataset SQL run"),
        ("run_python", "Python run"),
        ("run_eda", "EDA"),
        ("render_chart", "chart render"),
    ],
)
def test_harness_fault_answers_500(
    tmp_path, monkeypatch, engine, path_builder
) -> None:
    """A fault inside the harness is a server error, never the input's fault."""
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(main_module, engine, _Boom())
    with _client() as client:
        case_id, dataset_id = _case_with_dataset(client)
        if engine == "run_query":
            response = client.post(
                f"/cases/{case_id}/datasets/{dataset_id}/runs",
                json={"sql": "SELECT * FROM read_csv_auto(?)"},
            )
        elif engine == "run_query_multi":
            response = client.post(
                f"/cases/{case_id}/runs",
                json={"sql": "SELECT * FROM read_csv_auto(?)", "dataset_ids": [dataset_id]},
            )
        elif engine == "run_python":
            response = client.post(
                f"/cases/{case_id}/datasets/{dataset_id}/runs/python",
                json={"code": "result = []"},
            )
        elif engine == "run_eda":
            response = client.post(
                f"/cases/{case_id}/datasets/{dataset_id}/eda",
                json={"op": "distribution", "column": "region"},
            )
        else:
            run = client.post(
                f"/cases/{case_id}/datasets/{dataset_id}/runs",
                json={"sql": "SELECT * FROM read_csv_auto(?)"},
            )
            # render_chart is reached with monkeypatched in the caller.
            response = client.post(
                f"/cases/{case_id}/runs/{run.json()['id']}/charts",
                json={"kind": "bar", "x": "region", "y": "order_id"},
            )
    assert response.status_code == 500, path_builder
    assert b"Internal Server Error" in response.content


# --- the LLM fallback stays broad, but stops being silent ------------------


def test_llm_fallback_logs_the_reason(tmp_path, monkeypatch, caplog) -> None:
    """Any failure still degrades to deterministic - and now leaves a trace."""
    _temp_env(tmp_path, monkeypatch)

    class _Broken:
        def plan(self, question, profile):
            raise RuntimeError("the LLM endpoint exploded")

    monkeypatch.setattr(planner_module, "_configured_llm", lambda: _Broken())
    with caplog.at_level(logging.WARNING, logger="app.planner"):
        with TestClient(app) as client:
            case_id, dataset_id = _case_with_profile(client, monkeypatch)
            response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")

    assert response.status_code == 201
    assert response.json()["source"] == planner_module.SOURCE_DETERMINISTIC
    assert any(
        "falling back to deterministic" in record.message and record.levelno == logging.WARNING
        for record in caplog.records
    )
