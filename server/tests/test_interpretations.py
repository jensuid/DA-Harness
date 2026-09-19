"""Result interpretation tests for P3-AI-011.

The loop could run, chart, validate and export a result; reading one still meant
re-deriving it. These cover the deterministic read, the LLM path and its three
failure modes, persistence, the 404 contract, and survival through duplicate
and delete.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module
import app.interpreter as interpreter_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
SQL = (
    "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) "
    "GROUP BY region ORDER BY region"
)
PY = "result = [[row['region'], row['revenue']] for row in dataset.rows]"


def _temp_env(tmp_path, monkeypatch):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    # No key by default, so the deterministic engine speaks unless a test
    # installs a fake one - the suite never makes a live call.
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def _case_with_sql_run(client):
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "sales.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
    ).json()["id"]
    return case_id, run_id


class _GoodInterpreter:
    def interpret(self, question, kind, source_text, columns, rows, profile):
        return {
            "summary": "The north region leads on revenue.",
            "observations": ["revenue is highest for the north region"],
            "caveats": ["three rows is a small basis for a claim"],
        }


class _FailingInterpreter:
    def interpret(self, *args, **kwargs):
        raise RuntimeError("LLM unavailable")


class _MalformedInterpreter:
    def interpret(self, *args, **kwargs):
        return {"summary": "", "observations": "not a list"}


def test_deterministic_interpretation_is_created(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/interpret")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["source"] == interpreter_module.SOURCE_DETERMINISTIC
    assert body["run_id"] == run_id
    assert "2 row(s)" in body["summary"]
    assert body["observations"]


def test_observations_reference_values_the_result_actually_contains(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        body = client.post(f"/cases/{case_id}/runs/{run_id}/interpret").json()

    joined = " ".join([body["summary"], *body["observations"]])
    # Every figure quoted must come from the result itself: the two aggregated
    # totals are 80.5 and 325.0, so no other number may appear.
    for value in ("80.5", "325.0", "region", "total"):
        assert value in joined
    assert "999" not in joined


def test_a_python_run_can_be_interpreted(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "sales.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        ).json()["id"]
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs/python", json={"code": PY}
        ).json()["id"]

        response = client.post(f"/cases/{case_id}/runs/{run_id}/interpret")

    assert response.status_code == 201, response.text
    assert response.json()["source"] == interpreter_module.SOURCE_DETERMINISTIC


def test_llm_interpretation_is_persisted(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(
        interpreter_module, "_configured_llm", lambda: _GoodInterpreter()
    )
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/interpret")

    assert response.status_code == 201, response.text
    body = response.json()
    assert body["source"] == interpreter_module.SOURCE_LLM
    assert body["summary"] == "The north region leads on revenue."
    assert body["observations"] == ["revenue is highest for the north region"]


def test_llm_failure_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(
        interpreter_module, "_configured_llm", lambda: _FailingInterpreter()
    )
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/interpret")

    assert response.status_code == 201
    assert response.json()["source"] == interpreter_module.SOURCE_DETERMINISTIC


def test_malformed_llm_output_falls_back(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    monkeypatch.setattr(
        interpreter_module, "_configured_llm", lambda: _MalformedInterpreter()
    )
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        response = client.post(f"/cases/{case_id}/runs/{run_id}/interpret")

    assert response.status_code == 201
    assert response.json()["source"] == interpreter_module.SOURCE_DETERMINISTIC


def test_interpretation_survives_a_restart_and_lists_newest_first(
    tmp_path, monkeypatch
) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        first = client.post(f"/cases/{case_id}/runs/{run_id}/interpret").json()
        # Force the first reading to be genuinely older, so ordering is exact.
        with get_connection(db_module.DATA_DIR.parent / "test.db") as conn:
            conn.execute(
                "UPDATE interpretations SET created_at = ? WHERE id = ?",
                ("2000-01-01T00:00:00+00:00", first["id"]),
            )
            conn.commit()
        second = client.post(f"/cases/{case_id}/runs/{run_id}/interpret").json()

    # A fresh session sees the persisted readings.
    with TestClient(app) as client:
        latest = client.get(f"/cases/{case_id}/runs/{run_id}/interpret")
        history = client.get(f"/cases/{case_id}/runs/{run_id}/interpretations")

    assert latest.status_code == 200
    assert latest.json()["id"] == second["id"]
    assert [item["id"] for item in history.json()] == [second["id"], first["id"]]


def test_404s_for_unknown_and_cross_case_runs(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        other_case = client.post(
            "/cases", json={"question": "Other?", "dataset": "o.csv"}
        ).json()["id"]

        assert client.post(f"/cases/no-such-case/runs/{run_id}/interpret").status_code == 404
        assert client.post(f"/cases/{case_id}/runs/no-such-run/interpret").status_code == 404
        # A run belonging to another case is not reachable through this path.
        assert client.post(f"/cases/{other_case}/runs/{run_id}/interpret").status_code == 404
        # And the latest-reading endpoint 404s when nothing was recorded.
        assert client.get(f"/cases/{case_id}/runs/no-such-run/interpret").status_code == 404


def test_interpretations_survive_duplicate_and_delete(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id, run_id = _case_with_sql_run(client)
        client.post(f"/cases/{case_id}/runs/{run_id}/interpret")

        copy_id = client.post(f"/cases/{case_id}/duplicate").json()["id"]
        copy_runs = client.get(f"/cases/{copy_id}/runs").json()
        assert len(copy_runs) == 1
        # The copy's reading hangs off the copy's own run, not the original's.
        copied = client.get(
            f"/cases/{copy_id}/runs/{copy_runs[0]['id']}/interpret"
        )
        assert copied.status_code == 200
        assert copied.json()["run_id"] == copy_runs[0]["id"]

        client.delete(f"/cases/{copy_id}")
        with get_connection(db_module.DATA_DIR.parent / "test.db") as conn:
            leftover = conn.execute(
                "SELECT COUNT(*) FROM interpretations WHERE case_id = ?",
                (copy_id,),
            ).fetchone()[0]
        assert leftover == 0, "delete left the copy's interpretations behind"
        # The original is untouched: its reading still resolves.
        assert client.get(f"/cases/{case_id}/runs/{run_id}/interpret").status_code == 200

