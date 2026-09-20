"""Agentic analysis tests for P6-AGENT-002.

The loop already existed as endpoints; the agent is the driver over them. These
tests pin the contract that makes that safe:

- nothing is written without an approval, and each approval performs exactly one
  write through the endpoint that owns it (so the read-only gate, the row cap and
  the single finding-creation path are all still in force for an agent-run case),
- the next step is derived from the case's artifacts, so an interrupted agent
  resumes where it stopped rather than at a stored counter,
- iteration is a *different* query, the budget is bounded, and both a dead end
  and a closed loop are stated rather than silent,
- the audit trail travels with the case: delete removes it, export carries it,
  and a duplicate keeps it with remapped references.

Every case is built through the public API, so the loop runs against real rows
rather than rows a test inserted by hand.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.agent as agent_module
import app.db as db_module

# A dataset with a clear measure and a repeating categorical dimension: the
# deterministic generator proposes a GROUP BY over `region`, which returns rows,
# so the happy walk reaches a finding without any LLM call.
CSV = (
    b"order_id,revenue,region\n"
    b"1,125.0,north\n2,80.5,south\n3,200.0,north\n4,60.0,east\n"
)
# Four categorical columns and no measure: every variant proposes a different
# GROUP BY and every one returns nothing, so this is how the budget is spent.
EMPTY_4COL_CSV = b"v1,v2,g1,g2\n"
# One categorical column, no measure: every variant is the same query, so there
# is no second proposal to make once the first returns nothing.
ONE_COL_CSV = b"label\n"


def _temp_env(tmp_path, monkeypatch):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override
    # The deterministic path is what these tests pin; an ambient key would make
    # the proposals slow and non-deterministic for no gain here.
    monkeypatch.delenv("DAH_LLM_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)


def _case(client, csv=CSV, question="Why did revenue decline?") -> str:
    case_id = client.post(
        "/cases", json={"question": question, "dataset": "s.csv"}
    ).json()["id"]
    client.post(
        f"/cases/{case_id}/datasets", files={"file": ("s.csv", csv, "text/csv")}
    )
    return case_id


def _profiled(client, case_id) -> str:
    dataset_id = client.get(f"/cases/{case_id}/datasets").json()[0]["id"]
    response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    assert response.status_code == 201, response.text
    return dataset_id


def _propose(client, case_id) -> dict:
    response = client.post(f"/cases/{case_id}/agent")
    assert response.status_code == 200, response.text
    return response.json()


def _approve(client, case_id, state) -> dict:
    pending = state["pending"]
    assert pending is not None, "nothing pending to approve"
    response = client.post(
        f"/cases/{case_id}/agent/approve", json={"step_id": pending["id"]}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _step(client, case_id) -> dict:
    """Propose and approve one step, returning the state after the write."""
    return _approve(client, case_id, _propose(client, case_id))


def _walk(client, case_id, limit: int = 15) -> dict:
    """Approve every proposal until the loop states it is done."""
    state = None
    for _ in range(limit):
        state = _propose(client, case_id)
        if state["pending"] is None:
            return state
        state = _approve(client, case_id, state)
    state = _propose(client, case_id)
    assert state["pending"] is None, "the agent did not terminate within the limit"
    return state


def _counts(client, case_id) -> dict:
    return client.get(f"/cases/{case_id}/progress").json()["counts"]


# ---------------------------------------------------------------------------
# The happy walk: the full loop, through the public API alone.
# ---------------------------------------------------------------------------


def test_starting_an_agent_writes_nothing_until_approved(tmp_path, monkeypatch) -> None:
    """A proposal is recorded, not performed; the case gains no artifact."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        before = _counts(client, case_id)

        state = _propose(client, case_id)

    assert state["pending"]["kind"] == "profile"
    assert state["pending"]["status"] == "pending"
    # Proposing is the one thing the agent does write: its own audit row.
    assert state["history"] == []
    # ...and it changed nothing in the case itself.
    assert _counts(client, case_id) == before
    assert before["runs"] == 0 and before["findings"] == 0 and before["plans"] == 0


def test_the_full_loop_reaches_a_validated_finding(tmp_path, monkeypatch) -> None:
    """profile -> plan -> analyze -> interpret -> accept -> chart -> validate."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        state = _walk(client, case_id)

        kinds = [step["kind"] for step in reversed(state["history"])]
        progress = client.get(f"/cases/{case_id}/progress").json()

    assert kinds == ["profile", "plan", "analyze", "interpret", "accept", "chart", "validate"]
    assert state["pending"] is None
    assert progress["loop_closed"] is True
    counts = progress["counts"]
    assert counts["runs"] == 1
    assert counts["findings"] == 1
    assert counts["charts"] == 1
    # The finding the agent accepted went through validation, not assertion.
    findings = client.get(f"/cases/{case_id}/findings").json()
    assert findings[0]["validation_status"] == "supported"


def test_every_step_carries_the_source_of_its_proposal(tmp_path, monkeypatch) -> None:
    """A reviewer of an agent-run case can see which engine spoke at each step."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        state = _walk(client, case_id)

    sources = {step["kind"]: step["source"] for step in state["history"]}
    # No LLM key is configured, so every proposal is the deterministic engine.
    assert set(sources.values()) == {"deterministic"}
    assert sources["analyze"] == "deterministic"


def test_each_approval_performs_exactly_one_write(tmp_path, monkeypatch) -> None:
    """One approval, one artifact - the loop cannot batch writes behind a yes."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)

        state = _approve(client, case_id, _propose(client, case_id))
        assert state["history"][0]["kind"] == "profile"
        assert _counts(client, case_id)["profiles"] == 1

        state = _approve(client, case_id, _propose(client, case_id))
        assert state["history"][0]["kind"] == "plan"
        assert _counts(client, case_id)["plans"] == 1

        state = _approve(client, case_id, _propose(client, case_id))
        assert state["history"][0]["kind"] == "analyze"
        assert _counts(client, case_id)["runs"] == 1


# ---------------------------------------------------------------------------
# The approval gate.
# ---------------------------------------------------------------------------


def test_an_approval_id_must_name_the_current_pending_step(tmp_path, monkeypatch) -> None:
    """A stale id from an old page is a 409, never a second write."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        first = _propose(client, case_id)["pending"]
        _approve(client, case_id, _propose(client, case_id))
        # `first` is now a settled step; approving it again must be refused.
        response = client.post(
            f"/cases/{case_id}/agent/approve", json={"step_id": first["id"]}
        )

    assert response.status_code == 409
    assert response.json()["detail"]["given"] == first["id"]


def test_an_unknown_approval_id_is_refused(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        _propose(client, case_id)
        response = client.post(
            f"/cases/{case_id}/agent/approve", json={"step_id": "no-such-step"}
        )

    assert response.status_code == 409
    # Nothing was written by the refused approval.
    assert _counts(client, case_id)["profiles"] == 0


def test_approving_with_nothing_pending_is_a_409(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        _walk(client, case_id)
        # The loop has closed; there is no pending step to approve.
        response = client.post(
            f"/cases/{case_id}/agent/approve", json={"step_id": "anything"}
        )

    assert response.status_code == 409


def test_rejecting_records_the_reason_and_writes_nothing(tmp_path, monkeypatch) -> None:
    """The human's no is recorded with their note, and never performs a write."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        pending = _propose(client, case_id)["pending"]
        before = _counts(client, case_id)

        response = client.post(
            f"/cases/{case_id}/agent/reject",
            json={"step_id": pending["id"], "reason": "wrong direction"},
        )

    assert response.status_code == 200, response.text
    rejected = response.json()["history"][0]
    assert rejected["status"] == "rejected"
    assert rejected["note"] == "wrong direction"
    assert _counts(client, case_id) == before


def test_rejecting_a_stale_id_is_a_409(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        first = _propose(client, case_id)["pending"]
        _approve(client, case_id, _propose(client, case_id))
        response = client.post(
            f"/cases/{case_id}/agent/reject", json={"step_id": first["id"]}
        )

    assert response.status_code == 409


def test_get_state_writes_nothing_and_creates_no_proposal(tmp_path, monkeypatch) -> None:
    """A read that wrote would mean a page refresh commits work.

    GET and POST share one path - the state and the advance of it - so the GET
    half must stay strictly read-only even after the POST half has been used.
    """
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        # Advancing once, then polling: a poll that proposed would mean a
        # background refresh of the page commits a step the human never saw.
        _propose(client, case_id)
        for _ in range(3):
            state = client.get(f"/cases/{case_id}/agent").json()

    assert state["pending"] is not None
    assert state["pending"]["kind"] == "profile"
    assert state["history"] == []
    assert _counts(client, case_id)["runs"] == 0
    assert _counts(client, case_id)["profiles"] == 0


def test_propose_is_idempotent(tmp_path, monkeypatch) -> None:
    """Two proposals before a decision yield one pending step, not two."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        first = _propose(client, case_id)
        second = _propose(client, case_id)

    assert first["pending"]["id"] == second["pending"]["id"]
    assert len(second["history"]) == 0


def test_agent_endpoints_404_for_an_unknown_case(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        assert client.get("/cases/nope/agent").status_code == 404
        assert client.post("/cases/nope/agent").status_code == 404
        assert client.post(
            "/cases/nope/agent/approve", json={"step_id": "x"}
        ).status_code == 404
        assert client.post(
            "/cases/nope/agent/reject", json={"step_id": "x"}
        ).status_code == 404


# ---------------------------------------------------------------------------
# Iteration, budget and termination.
# ---------------------------------------------------------------------------


def test_an_empty_result_iterates_to_a_different_query(tmp_path, monkeypatch) -> None:
    """A query that returns nothing makes the next proposal a different one."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client, csv=EMPTY_4COL_CSV)
        _step(client, case_id)  # profile
        _step(client, case_id)  # plan
        first = _propose(client, case_id)["pending"]
        first_code = first["payload"]["code"]
        _approve(client, case_id, {"pending": first})

        second = _propose(client, case_id)["pending"]

    assert second["kind"] == "analyze"
    assert second["payload"]["code"] != first_code
    assert second["payload"]["variant"] == 1
    # The retry is stated as a retry, not as a first read.
    assert "no rows" in second["note"]


def test_the_budget_is_bounded_and_its_end_is_stated(tmp_path, monkeypatch) -> None:
    """Exhausting the retries ends the run with a reason, not a silent stop."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client, csv=EMPTY_4COL_CSV)
        state = _walk(client, case_id)

    assert state["pending"] is None
    end = next(step for step in state["history"] if step["kind"] == "end")
    assert "no rows" in end["note"]
    analyze = [step for step in state["history"] if step["kind"] == "analyze"]
    # The cap is what makes the agent terminate; it spent all of it.
    assert len(analyze) == agent_module.max_attempts()
    # ...and each attempt was a distinct query, so the budget was not wasted on
    # re-running the one that struck out.
    codes = [step["payload"]["code"] for step in analyze]
    assert len(set(codes)) == len(codes)


def test_a_case_with_no_usable_axis_ends_at_a_stated_reason(tmp_path, monkeypatch) -> None:
    """One categorical column: no variant differs, so there is no second try."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client, csv=ONE_COL_CSV, question="What is here?")
        state = _walk(client, case_id)

    assert state["pending"] is None
    end = next(step for step in state["history"] if step["kind"] == "end")
    assert end["note"]
    assert [step["kind"] for step in state["history"] if step["kind"] == "analyze"]


def test_a_closed_loop_proposes_nothing_further(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        _walk(client, case_id)
        # The loop closed; a later propose states that rather than re-opening it.
        after = _propose(client, case_id)
        again = _propose(client, case_id)

    assert after["pending"] is None
    assert again["pending"] is None
    # No `end` row is written for a genuinely closed loop: the workflow already
    # says so, and a second statement of it would be noise.
    assert not [s for s in after["history"] if s["kind"] == "end"]


# ---------------------------------------------------------------------------
# Resumption: the next step is derived, not stored.
# ---------------------------------------------------------------------------


def test_an_interrupted_agent_resumes_where_it_stopped(tmp_path, monkeypatch) -> None:
    """No stored cursor: the artifacts decide the next step on the next call."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        _approve(client, case_id, _propose(client, case_id))  # profile
        # The human walks away mid-case. On return, the agent derives the plan
        # step from the profile's existence - not from anything it remembered.
        state = _propose(client, case_id)

    assert state["pending"]["kind"] == "plan"


def test_an_agent_cannot_be_ahead_of_the_data(tmp_path, monkeypatch) -> None:
    """A step whose artifact already exists is never re-proposed."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        dataset_id = _profiled(client, case_id)
        # The analyst profiled by hand; the agent must not re-propose it.
        state = _propose(client, case_id)

    assert state["pending"]["kind"] != "profile"
    assert client.get(f"/cases/{case_id}/progress").json()["stage"] != "profile"
    del dataset_id  # the profile is observed through the case, not the id


# ---------------------------------------------------------------------------
# The audit trail travels with the case.
# ---------------------------------------------------------------------------


def _run_agent_to_a_finding(client, case_id) -> str:
    """Walk to a validated finding and return the case's exported package."""
    _walk(client, case_id)
    response = client.get(f"/cases/{case_id}/export")
    assert response.status_code == 200, response.text
    return response.json()


def test_export_carries_the_agent_audit_trail(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        package = _run_agent_to_a_finding(client, case_id)

    steps = package["agent_steps"]
    assert [step["kind"] for step in steps] == [
        "profile", "plan", "analyze", "interpret", "accept", "chart", "validate"
    ]
    assert all(step["source"] and step["status"] for step in steps)
    # The payload keeps the ids it cited, so the trail is traceable in-package.
    analyze = next(step for step in steps if step["kind"] == "analyze")
    assert analyze["payload"]["dataset_id"] == package["datasets"][0]["id"]
    assert analyze["payload"]["code"]


def test_the_audit_trail_survives_the_import_round_trip(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        package = _run_agent_to_a_finding(client, case_id)
        imported = client.post("/cases/import", json=package).json()
        state = client.get(f"/cases/{imported['id']}/agent").json()

    kinds = [step["kind"] for step in reversed(state["history"])]
    assert kinds == ["profile", "plan", "analyze", "interpret", "accept", "chart", "validate"]
    # The imported steps cite the imported case's own artifacts, not the
    # original's - a restored package stands on its own.
    imported_datasets = client.get(f"/cases/{imported['id']}/datasets").json()
    analyze = next(step for step in state["history"] if step["kind"] == "analyze")
    assert analyze["payload"]["dataset_id"] == imported_datasets[0]["id"]
    # A restored trail is not a live proposal: nothing is pending on import.
    assert state["pending"] is None


def test_an_older_package_without_agent_steps_still_imports(tmp_path, monkeypatch) -> None:
    """The section is younger than the format; its absence is not an error."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        package = _run_agent_to_a_finding(client, case_id)
        legacy = dict(package)
        del legacy["agent_steps"]

        response = client.post("/cases/import", json=legacy)

    assert response.status_code == 201, response.text
    assert client.get(f"/cases/{response.json()['id']}/agent").json()["history"] == []


def test_delete_removes_the_agent_state_with_the_case(tmp_path, monkeypatch) -> None:
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        _walk(client, case_id)
        response = client.delete(f"/cases/{case_id}")
        assert response.status_code == 204
        # The trail is a child of the case, so it goes with it.
        assert client.get(f"/cases/{case_id}/agent").status_code == 404


def test_duplicate_keeps_the_audit_trail_with_remapped_references(
    tmp_path, monkeypatch,
) -> None:
    """A copy of an agent-run case keeps its approvals, citing its own rows."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        _walk(client, case_id)
        copy_id = client.post(f"/cases/{case_id}/duplicate").json()["id"]
        state = client.get(f"/cases/{copy_id}/agent").json()

    kinds = [step["kind"] for step in reversed(state["history"])]
    assert kinds == ["profile", "plan", "analyze", "interpret", "accept", "chart", "validate"]
    copy_datasets = client.get(f"/cases/{copy_id}/datasets").json()
    analyze = next(step for step in state["history"] if step["kind"] == "analyze")
    # The copy's trail points at the copy's own dataset, not the original's.
    assert analyze["payload"]["dataset_id"] == copy_datasets[0]["id"]
    # Mutating the copy leaves the original's trail alone.
    assert client.get(f"/cases/{case_id}/agent").json()["history"]


def test_the_agent_state_is_one_append_only_table(tmp_path, monkeypatch) -> None:
    """One row per step: a decision settles its own row and never another."""
    _temp_env(tmp_path, monkeypatch)
    with TestClient(app) as client:
        case_id = _case(client)
        _walk(client, case_id)
        with get_connection(tmp_path / "test.db") as connection:
            rows = connection.execute(
                "SELECT kind, status, decided_at FROM agent_steps "
                "WHERE case_id = ? ORDER BY created_at",
                (case_id,),
            ).fetchall()

    # Each row is settled exactly once and a settled row is never revisited:
    # a later decision takes a new row rather than rewriting an old one. A
    # completed loop therefore leaves nothing pending behind it.
    assert all(row["decided_at"] is not None for row in rows)
    assert all(row["status"] == "done" for row in rows)
    assert [row["kind"] for row in rows] == [
        "profile", "plan", "analyze", "interpret", "accept", "chart", "validate"
    ]
