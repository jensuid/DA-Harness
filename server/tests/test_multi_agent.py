"""Multi-agent workflow tests for P7-AGENT-001.

The spec names an *autonomous* multi-agent system as a non-goal and Human
control in its Never-lose list, so these test orchestration rather than
autonomy: two roles over one case, each with its own pending step and its own
audit trail, every write behind the same approval gate, and the reviewer's
whole method being EVALUATE - the audit layer the roadmap gated this work on.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
SQL = "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region"
# A claim the data does not support: 999 appears nowhere in the result, so the
# reviewer's Evidence axis fails it.
BAD_CLAIM = "Revenue is 999 in every region."


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _role(client, case_id, role) -> dict:
    response = client.get(f"/cases/{case_id}/agents/{role}")
    assert response.status_code == 200, response.text
    return response.json()


def _propose(client, case_id, role) -> dict:
    response = client.post(f"/cases/{case_id}/agents/{role}")
    assert response.status_code == 200, response.text
    return response.json()


def _approve(client, case_id, role, step_id) -> dict:
    response = client.post(
        f"/cases/{case_id}/agents/{role}/approve", json={"step_id": step_id}
    )
    assert response.status_code == 200, response.text
    return response.json()


def _case_with_a_finding(client, statement: str = "North leads revenue.") -> str:
    """A case the analyst has walked as far as a recorded finding."""
    case_id = client.post(
        "/cases", json={"question": "Why did revenue decline?", "dataset": "s.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("s.csv", CSV, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
    client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
    ).json()["id"]
    client.post(
        f"/cases/{case_id}/runs/{run_id}/charts",
        json={"kind": "bar", "x": "region", "y": "total"},
    )
    client.post(
        f"/cases/{case_id}/findings",
        json={"run_id": run_id, "statement": statement},
    )
    return case_id


def test_the_legacy_paths_are_the_analyst_role(tmp_path) -> None:
    """The single-agent endpoints keep their meaning: they are the analyst."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        ).json()["id"]

        legacy = client.post(f"/cases/{case_id}/agent").json()
        roleful = _propose(client, case_id, "analyst")

    # A pending step stands, so the legacy POST and the analyst POST answer the
    # same step - not two writes to choose from.
    assert legacy["role"] == "analyst"
    assert roleful["role"] == "analyst"
    assert legacy["pending"]["id"] == roleful["pending"]["id"]
    assert legacy["pending"]["kind"] == "profile"
    assert legacy["pending"]["role"] == "analyst"


def test_two_roles_hold_independent_pending_steps(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        analyst = _propose(client, case_id, "analyst")
        reviewer = _propose(client, case_id, "reviewer")

    # The analyst is still on the loop; the reviewer has a finding to audit.
    assert analyst["pending"] is not None
    assert reviewer["pending"] is not None
    assert reviewer["pending"]["id"] != analyst["pending"]["id"]
    assert reviewer["pending"]["role"] == "reviewer"
    assert reviewer["pending"]["kind"] == "evaluate"
    # Each trail is its own: a reviewer's history is not the analyst's.
    assert reviewer["history"] == [] or all(
        step["role"] == "reviewer" for step in reviewer["history"]
    )
    assert all(step["role"] == "analyst" for step in analyst["history"])


def test_the_reviewer_audits_the_finding_its_own_run_backs(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        reviewer = _propose(client, case_id, "reviewer")
        payload = reviewer["pending"]["payload"]

    runs = client.get(f"/cases/{case_id}/runs").json()
    findings = client.get(f"/cases/{case_id}/findings").json()
    assert payload["run_id"] == runs[0]["id"]
    assert payload["dataset_id"] == runs[0]["dataset_id"]
    # The claim under audit is the finding's own statement, and the code is the
    # run's own query - the reviewer invents neither.
    assert payload["claim"] == findings[0]["statement"]
    assert payload["code"] == runs[0]["sql"]
    assert payload["kind"] == runs[0]["kind"]


def test_approving_the_reviewer_records_an_evaluation(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        step_id = _propose(client, case_id, "reviewer")["pending"]["id"]
        after = _approve(client, case_id, "reviewer", step_id)

        dataset_id = client.get(f"/cases/{case_id}/datasets").json()[0]["id"]
        evaluations = client.get(
            f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
        ).json()

    # The write went through the evaluate endpoint: one audit in the table,
    # whose claim is the finding's statement and whose code is the run's query.
    assert len(evaluations) == 1
    assert evaluations[0]["claim"] == "North leads revenue."
    assert "SELECT region" in evaluations[0]["code"]
    assert evaluations[0]["run_id"] is not None
    # The settled step records what the audit found.
    settled = [s for s in after["history"] if s["id"] == step_id]
    assert settled and settled[0]["status"] == "done"
    assert "audited finding" in settled[0]["note"]
    assert "9 axes" in settled[0]["note"]
    # The pass and concern counts are per axis, not per distinct verdict: a
    # summary that collapses the verdicts to a set cannot count past one.
    expected = {v: sum(a["verdict"] == v for a in evaluations[0]["findings"]) for v in ("pass", "concern", "fail")}
    assert f"{expected['pass']} pass" in settled[0]["note"], settled[0]["note"]
    assert f"{expected['concern']} concern" in settled[0]["note"], settled[0]["note"]
    assert f"{expected['fail']} fail" in settled[0]["note"], settled[0]["note"]
    assert expected["pass"] + expected["concern"] + expected["fail"] == 9
    # A clean artifact passes every axis, so no axis is named as failed.
    assert "0 fail" in settled[0]["note"]
    assert ": " not in settled[0]["note"].split("0 fail")[1]


def test_an_audited_finding_is_not_re_audited(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        _approve(client, case_id, "reviewer", _propose(client, case_id, "reviewer")["pending"]["id"])
        again = _propose(client, case_id, "reviewer")

    # The reviewer's work is done: no pending step, no end row (an end row is
    # written when a role is *waiting*, not when it is finished), and the one
    # audit it ran is settled in its trail.
    assert again["pending"] is None
    assert not [s for s in again["history"] if s["kind"] == "end"]
    audits = [s for s in again["history"] if s["kind"] == "evaluate"]
    assert len(audits) == 1
    assert audits[0]["status"] == "done"


def test_a_case_with_no_findings_states_what_the_reviewer_waits_for(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        )
        reviewer = _propose(client, case_id, "reviewer")

    assert reviewer["pending"] is None
    end = [s for s in reviewer["history"] if s["kind"] == "end"]
    assert end
    assert "no findings yet" in end[-1]["note"]


def test_one_role_approval_cannot_authorise_another(tmp_path) -> None:
    """A 409 names the role's own pending step - one role's write is never
    authorised by another role's approval."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        analyst_id = _propose(client, case_id, "analyst")["pending"]["id"]
        reviewer_id = _propose(client, case_id, "reviewer")["pending"]["id"]

        response = client.post(
            f"/cases/{case_id}/agents/reviewer/approve",
            json={"step_id": analyst_id},
        )
        # The analyst's step is not the reviewer's, so nothing runs.
        assert response.status_code == 409
        detail = response.json()["detail"]
        assert detail["role"] == "reviewer"
        assert detail["expected"] == reviewer_id
        assert detail["given"] == analyst_id

        evaluations = client.get(
            f"/cases/{case_id}/datasets/"
            f"{client.get(f'/cases/{case_id}/datasets').json()[0]['id']}/evaluations"
        ).json()
    assert evaluations == []


def test_an_unknown_role_is_refused_with_the_roles_that_exist(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        for verb in ("get", "post"):
            response = getattr(client, verb)(f"/cases/{case_id}/agents/skeptic")
            assert response.status_code == 400, response.text
            assert "analyst" in response.json()["detail"]
            assert "reviewer" in response.json()["detail"]


def test_a_failing_audit_is_recorded_without_touching_the_finding(tmp_path) -> None:
    """Two honest notions stay distinct: the finding's own validation status is
    about rerun support; the reviewer's verdict is an audit. A failing audit is
    recorded beside the finding, not folded into it."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client, statement=BAD_CLAIM)
        before = client.get(f"/cases/{case_id}/findings").json()[0]
        step_id = _propose(client, case_id, "reviewer")["pending"]["id"]
        after = _approve(client, case_id, "reviewer", step_id)
        findings = client.get(f"/cases/{case_id}/findings").json()

    # The claim quotes a value the result does not contain, so Evidence fails.
    settled = next(s for s in after["history"] if s["id"] == step_id)
    assert "1 fail" in settled["note"]
    assert "evidence: " in settled["note"]
    # A mixed audit still counts every axis: the concern tally is not capped at
    # one by collapsing the verdicts to a set.
    dataset_id = client.get(f"/cases/{case_id}/datasets").json()[0]["id"]
    audit = client.get(
        f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
    ).json()[0]
    counts = {v: sum(a["verdict"] == v for a in audit["findings"]) for v in ("pass", "concern", "fail")}
    assert counts["pass"] + counts["concern"] + counts["fail"] == 9
    assert f"{counts['pass']} pass" in settled["note"], settled["note"]
    assert f"{counts['concern']} concern" in settled["note"], settled["note"]
    assert f"{counts['fail']} fail" in settled["note"], settled["note"]
    # ...and the finding's own status is untouched, for any role.
    assert findings[0]["validation_status"] == before["validation_status"]


def test_the_reviewer_rejects_without_writing(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        step_id = _propose(client, case_id, "reviewer")["pending"]["id"]
        response = client.post(
            f"/cases/{case_id}/agents/reviewer/reject",
            json={"step_id": step_id, "reason": "audit this by hand"},
        )
        assert response.status_code == 200, response.text
        dataset_id = client.get(f"/cases/{case_id}/datasets").json()[0]["id"]
        evaluations = client.get(
            f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
        ).json()
        # The analyst's finding stands; no evaluation was written by a refusal.
        assert evaluations == []
        rejected = next(s for s in response.json()["history"] if s["id"] == step_id)
        assert rejected["status"] == "rejected"
        assert rejected["note"] == "audit this by hand"


def test_the_export_round_trip_carries_the_role(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        _propose(client, case_id, "reviewer")
        package = client.get(f"/cases/{case_id}/export").json()
        imported = client.post("/cases/import", json=package).json()

    steps = [step for step in package["agent_steps"]]
    assert any(step["role"] == "reviewer" for step in steps)
    # The copy keeps the roles its steps belonged to.
    imported_state = _role(client, imported["id"], "reviewer")
    assert imported_state["role"] == "reviewer"


def test_reading_a_role_proposes_nothing(tmp_path) -> None:
    """A GET never proposes, for any role - a page refresh commits nothing."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _case_with_a_finding(client)
        first = _role(client, case_id, "reviewer")
        for _ in range(3):
            again = _role(client, case_id, "reviewer")
        dataset_id = client.get(f"/cases/{case_id}/datasets").json()[0]["id"]
        evaluations = client.get(
            f"/cases/{case_id}/datasets/{dataset_id}/evaluations"
        ).json()

    assert first["pending"] is None
    assert again["pending"] is None
    assert evaluations == []
