"""LEARN mode tests for P7-LEARN-001.

The walk is a projection over the artifact counts the workflow already
derives, so these test the ladder itself more than the plumbing: that the
phases cover the workflow exactly once each, that the statuses are the
honest ones, and that the teaching travels with them.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.learn import LEARN_PHASES
from app.main import app, get_db
from app.workflow import STAGES
import app.db as db_module

CSV = b"order_id,revenue,region\n1,125.0,north\n2,80.5,south\n3,200.0,north\n"
SQL = "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _learn(client, case_id) -> dict:
    response = client.get(f"/cases/{case_id}/learn")
    assert response.status_code == 200, response.text
    return response.json()


def _full_case(client) -> str:
    """A case walked through every stage of the loop."""
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
    finding_id = client.post(
        f"/cases/{case_id}/findings",
        json={"run_id": run_id, "statement": "North leads revenue."},
    ).json()["id"]
    client.post(f"/cases/{case_id}/findings/{finding_id}/validate")
    return case_id


def test_the_ladder_covers_every_workflow_stage_exactly_once() -> None:
    """The LEARN phases are the workflow regrouped, not a second sequence."""
    covered = [stage for _, stages in LEARN_PHASES for stage in stages]
    assert sorted(covered) == sorted(STAGES)
    assert len(covered) == len(set(covered))
    # And the phases are the spec's ladder, in its order.
    assert [name for name, _ in LEARN_PHASES] == [
        "why", "what", "how", "validate"
    ]


def test_a_just_created_case_starts_on_why(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why did revenue decline?", "dataset": "s.csv"}
        ).json()["id"]
        walk = _learn(client, case_id)

    assert walk["case_id"] == case_id
    assert walk["question"] == "Why did revenue decline?"
    assert [step["name"] for step in walk["steps"]] == [
        "why", "what", "how", "validate"
    ]
    assert [step["status"] for step in walk["steps"]] == [
        "current", "pending", "pending", "pending"
    ]
    # "question" is always complete - the case row exists - so the learner's
    # first job is the data, and the walk says so rather than gesturing at Why.
    assert walk["current"] == "why"
    assert walk["done"] is False
    why = walk["steps"][0]
    assert [stage["name"] for stage in why["stages"]] == ["question", "data"]
    assert [stage["completed"] for stage in why["stages"]] == [True, False]
    assert walk["next_action"] == "Attach a dataset"
    assert walk["next_endpoint"] == f"POST /cases/{case_id}/datasets"


def test_a_walked_through_case_graduates(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _full_case(client)
        walk = _learn(client, case_id)

    assert [step["status"] for step in walk["steps"]] == [
        "complete", "complete", "complete", "complete"
    ]
    assert walk["current"] is None
    # The loop closed: a finding was validated. That is all `done` may claim -
    # the trust loop ran, not that the answer is right.
    assert walk["done"] is True
    assert walk["next_action"] is None
    assert walk["next_endpoint"] is None


def test_the_phase_boundary_moves_with_the_artifacts(tmp_path) -> None:
    """Profiled and planned: Why is done, What is current because the plan
    still has to be written."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        walk = _learn(client, case_id)

    assert [step["status"] for step in walk["steps"]] == [
        "complete", "current", "pending", "pending"
    ]
    what = walk["steps"][1]
    assert [stage["name"] for stage in what["stages"]] == ["profile", "plan"]
    assert [stage["completed"] for stage in what["stages"]] == [True, False]
    assert walk["next_action"] == "Generate an analysis plan"
    assert walk["current"] == "what"


def test_one_current_phase_at_every_step_of_the_build(tmp_path) -> None:
    """A property of the ladder, not one state of it: at every point in the
    build, the statuses are valid, at most one phase is current, and the
    complete phases precede the current one which precedes the pending ones."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]

        def check() -> dict:
            walk = _learn(client, case_id)
            statuses = [step["status"] for step in walk["steps"]]
            assert set(statuses) <= {"complete", "current", "pending"}
            if walk["done"]:
                assert statuses == ["complete"] * 4
                assert walk["current"] is None
                return walk
            assert statuses.count("current") == 1
            i = statuses.index("current")
            assert statuses[:i] == ["complete"] * i
            assert statuses[i + 1:] == ["pending"] * (3 - i)
            return walk

        check()
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        ).json()["id"]
        check()
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        check()
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
        check()
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        ).json()["id"]
        check()
        client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total"},
        )
        check()
        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "North leads revenue."},
        ).json()["id"]
        check()
        client.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        final = check()

    assert final["done"] is True


def test_deleting_an_artifact_moves_the_walk_back(tmp_path) -> None:
    """The walk is derived, not stored, so losing an artifact reopens a phase
    the case had closed - and restoring the counts closes it again."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = _full_case(client)
        assert _learn(client, case_id)["done"] is True

        # An attached-but-unprofiled dataset breaks the profile stage's
        # "every dataset is profiled" condition, so What reopens mid-walk.
        second = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("other.csv", CSV, "text/csv")},
        ).json()["id"]
        reopened = _learn(client, case_id)

        # Deleting it is what moves the walk back to complete: the projection
        # recomputes from the counts that remain.
        client.delete(f"/cases/{case_id}/datasets/{second}")
        restored = _learn(client, case_id)

    assert reopened["done"] is False
    assert reopened["current"] == "what"
    assert [step["status"] for step in reopened["steps"]] == [
        "complete", "current", "pending", "pending"
    ]
    assert restored["done"] is True
    assert restored["current"] is None


def test_every_phase_carries_the_teaching(tmp_path) -> None:
    """A purpose and a prompt are what make the ladder teaching rather than a
    checklist - and they are sentences, not labels."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        walk = _learn(client, case_id)

    assert len(walk["steps"]) == 4
    for step in walk["steps"]:
        assert step["purpose"], step["name"]
        assert step["purpose"].endswith("."), step["name"]
        assert step["prompt"].endswith("?"), step["name"]
        assert "?" in step["prompt"], step["name"]
        # The stages keep workflow's own actions, so there is one source of
        # truth for what closes a stage.
        assert step["stages"], step["name"]
        for stage in step["stages"]:
            assert stage["action"]
            assert stage["hint"]


def test_unknown_case_answers_404(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        response = client.get("/cases/nope/learn")

    assert response.status_code == 404
    assert response.json()["detail"] == "case not found"


def test_the_walk_reads_only(tmp_path) -> None:
    """Reading the walk must not create an artifact - it is a projection, and
    a learner who looks at the ladder has not done the work."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        for _ in range(3):
            walk = _learn(client, case_id)
        progress = client.get(f"/cases/{case_id}/progress").json()

    assert walk["current"] == "why"
    assert progress["stage"] == "data"
    assert progress["counts"]["datasets"] == 0
