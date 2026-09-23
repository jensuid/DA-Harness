"""Case history tests for P3-CASE-007.

The timeline is derived from each artifact's own timestamp, so these walk the
loop and check that the events follow the data - one per artifact, in order,
and nothing invented.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
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


def _history(client, case_id) -> dict:
    response = client.get(f"/cases/{case_id}/history")
    assert response.status_code == 200, response.text
    return response.json()


def test_fresh_case_has_single_creation_event(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why did revenue decline?", "dataset": "s.csv"}
        ).json()["id"]
        history = _history(client, case_id)

    assert history["case_id"] == case_id
    assert history["question"] == "Why did revenue decline?"
    assert [event["kind"] for event in history["events"]] == ["case_created"]
    assert history["events"][0]["label"] == "Why did revenue decline?"
    assert history["events"][0]["detail"] == "dataset: s.csv"
    assert history["counts"] == {
        "datasets": 0, "profiles": 0, "plans": 0, "runs": 0, "charts": 0,
        "findings": 0, "refinements": 0, "validations": 0, "decisions": 0,
    }


def test_history_covers_every_artifact_in_order(tmp_path) -> None:
    """Walking the whole loop leaves one event per artifact, chronologically."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        )
        dataset_id = client.get(f"/cases/{case_id}/datasets").json()[0]["id"]
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

        history = _history(client, case_id)

    kinds = [event["kind"] for event in history["events"]]
    assert kinds == [
        "case_created",
        "dataset_attached",
        "dataset_profiled",
        "plan_created",
        "run_executed",
        "chart_rendered",
        "finding_recorded",
        # Validation now has a timestamp of its own (P8-DECISION-008), so the
        # act of validating is an event rather than a detail on the finding's.
        "finding_validated",
    ]
    # Chronological: every timestamp is >= the one before it.
    timestamps = [event["timestamp"] for event in history["events"]]
    assert timestamps == sorted(timestamps)
    # Counts come from the artifacts, not the event list.
    assert history["counts"] == {
        "datasets": 1, "profiles": 1, "plans": 1, "runs": 1, "charts": 1,
        "findings": 1, "refinements": 0, "validations": 1, "decisions": 0,
    }


def test_events_carry_their_own_artifact_ids_and_details(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("sales.csv", CSV, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        ).json()["id"]
        history = _history(client, case_id)

    by_kind = {event["kind"]: event for event in history["events"]}
    assert by_kind["dataset_attached"]["artifact_id"] == dataset_id
    assert by_kind["dataset_attached"]["label"] == "sales.csv"
    assert by_kind["dataset_attached"]["detail"] == "format: csv"
    assert by_kind["dataset_profiled"]["label"] == "sales.csv"
    assert "3 rows" in by_kind["dataset_profiled"]["detail"]
    assert by_kind["run_executed"]["artifact_id"] == run_id
    # The run's label is the first line of its query.
    assert by_kind["run_executed"]["label"].startswith("SELECT region")
    assert by_kind["run_executed"]["detail"] == "sql, 2 row(s) returned"


def test_finding_event_carries_validation_status(tmp_path) -> None:
    """Validation has no timestamp of its own, so its status rides along."""
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
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        ).json()["id"]
        finding_id = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "North leads."},
        ).json()["id"]
        before = _history(client, case_id)
        client.post(f"/cases/{case_id}/findings/{finding_id}/validate")
        after = _history(client, case_id)

    finding_before = next(e for e in before["events"] if e["kind"] == "finding_recorded")
    finding_after = next(e for e in after["events"] if e["kind"] == "finding_recorded")
    assert finding_before["detail"] == "validation: not_evaluated"
    # The event keeps its own timestamp; only the status moved.
    assert finding_after["detail"].startswith("validation: ")
    assert finding_after["detail"] != "validation: not_evaluated"
    assert finding_after["timestamp"] == finding_before["timestamp"]


def test_history_is_case_scoped(tmp_path) -> None:
    """One case's artifacts never appear in another's timeline."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        busy = client.post(
            "/cases", json={"question": "busy", "dataset": "s.csv"}
        ).json()["id"]
        client.post(
            f"/cases/{busy}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        )
        quiet = client.post(
            "/cases", json={"question": "quiet", "dataset": "s.csv"}
        ).json()["id"]

        busy_history = _history(client, busy)
        quiet_history = _history(client, quiet)

    assert len(busy_history["events"]) == 2
    assert [event["kind"] for event in quiet_history["events"]] == ["case_created"]
    assert quiet_history["counts"]["datasets"] == 0


def test_history_404_for_unknown_case(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        response = client.get("/cases/no-such-case/history")
    assert response.status_code == 404
