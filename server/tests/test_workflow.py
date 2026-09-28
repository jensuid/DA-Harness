"""Guided workflow tests for P3-FLOW-004.

The stage is derived from artifacts, not stored, so these walk the whole loop
and check that progress follows the data in both directions - forward as
artifacts arrive, and back when one is removed.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
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


def _progress(client, case_id) -> dict:
    response = client.get(f"/cases/{case_id}/progress")
    assert response.status_code == 200, response.text
    return response.json()


def test_progress_starts_at_data(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why did revenue decline?", "dataset": "s.csv"}
        ).json()["id"]
        progress = _progress(client, case_id)

    assert progress["stage"] == "data"
    assert progress["completed"] == ["question"]
    assert progress["loop_closed"] is False
    assert progress["next_action"] == "Attach a dataset"
    assert progress["next_endpoint"] == f"POST /cases/{case_id}/datasets"
    assert [stage["name"] for stage in progress["stages"]] == list(STAGES)


def test_progress_advances_through_the_loop(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]

        client.post(
            f"/cases/{case_id}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        )
        assert _progress(client, case_id)["stage"] == "profile"

        dataset_id = client.get(f"/cases/{case_id}/datasets").json()[0]["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        assert _progress(client, case_id)["stage"] == "plan"

        client.post(f"/cases/{case_id}/datasets/{dataset_id}/plan")
        assert _progress(client, case_id)["stage"] == "analyze"

        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": SQL}
        ).json()["id"]
        assert _progress(client, case_id)["stage"] == "evidence"

        chart = client.post(
            f"/cases/{case_id}/runs/{run_id}/charts",
            json={"kind": "bar", "x": "region", "y": "total"},
        )
        assert chart.status_code == 201, chart.text
        # A chart alone is not evidence: the loop asks for a finding too.
        assert _progress(client, case_id)["stage"] == "evidence"

        finding = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "North leads revenue."},
        )
        assert finding.status_code == 201, finding.text
        assert _progress(client, case_id)["stage"] == "validate"

        result = client.post(
            f"/cases/{case_id}/findings/{finding.json()['id']}/validate"
        )
        assert result.status_code == 200, result.text

        done = _progress(client, case_id)
        assert done["stage"] == "validated"
        assert done["loop_closed"] is True
        assert done["next_action"] is None
        assert set(done["completed"]) == set(STAGES)


def test_profile_stage_needs_every_dataset(tmp_path) -> None:
    """Two datasets with one profile leaves the case at the profile stage."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        for index in range(2):
            client.post(
                f"/cases/{case_id}/datasets",
                files={"file": (f"s{index}.csv", CSV, "text/csv")},
            )
        datasets = client.get(f"/cases/{case_id}/datasets").json()
        client.post(f"/cases/{case_id}/datasets/{datasets[0]['id']}/profile")

        progress = _progress(client, case_id)

    assert progress["stage"] == "profile"
    assert progress["counts"]["datasets"] == 2
    assert progress["counts"]["profiles"] == 1


def test_progress_is_derived_per_request_and_case_scoped(tmp_path) -> None:
    """No stored stage: every call recomputes from the artifacts, per case."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        advanced = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        dataset_id = client.post(
            f"/cases/{advanced}/datasets",
            files={"file": ("s.csv", CSV, "text/csv")},
        ).json()["id"]
        client.post(f"/cases/{advanced}/datasets/{dataset_id}/profile")
        client.post(f"/cases/{advanced}/datasets/{dataset_id}/plan")
        client.post(
            f"/cases/{advanced}/datasets/{dataset_id}/runs", json={"sql": SQL}
        )

        fresh = client.post(
            "/cases", json={"question": "Other question", "dataset": "s.csv"}
        ).json()["id"]

        advanced_progress = _progress(client, advanced)
        fresh_progress = _progress(client, fresh)

    assert advanced_progress["stage"] == "evidence"
    assert advanced_progress["completed"] == ["question", "data", "profile", "plan", "analyze"]
    # The advanced case's artifacts do not leak into the fresh one's stage.
    assert fresh_progress["stage"] == "data"
    assert fresh_progress["completed"] == ["question"]
    # Recomputed from scratch on the next call, not cached anywhere.
    assert _progress(client, advanced) == advanced_progress


def test_progress_404_for_unknown_case(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        response = client.get("/cases/no-such-case/progress")
    assert response.status_code == 404


def test_the_next_endpoint_names_the_case_when_no_dataset_exists(tmp_path) -> None:
    """W2X-005: a `{dataset_id}` the case cannot fill reads as a bug.

    The walk-test saw `POST /cases/{case_id}/datasets/{dataset_id}/plan` with
    the placeholder unfilled, on the guidance an analyst reads first. When the
    stage is before any dataset the placeholder is dropped rather than shown
    empty - the path still names the case, and the routes that take one are the
    routes this stage is in.
    """
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Why?", "dataset": "s.csv"}
        ).json()["id"]
        progress = _progress(client, case_id)

    assert progress["stage"] == "data"
    assert "{dataset_id}" not in progress["next_endpoint"]
    assert progress["next_endpoint"] == f"POST /cases/{case_id}/datasets"


def test_the_next_endpoint_fills_the_dataset_when_one_exists(tmp_path) -> None:
    """W2X-005: the endpoint the guidance quotes is the endpoint that runs.

    Once a dataset is attached, the placeholder that read as a bug is the id
    the endpoint actually takes, so a developer who opens the disclosure and
    curls the path reaches the route rather than a 404 on a literal.
    """
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
        progress = _progress(client, case_id)

    assert progress["stage"] == "profile"
    assert "{dataset_id}" not in progress["next_endpoint"]
    assert progress["next_endpoint"] == (
        f"POST /cases/{case_id}/datasets/{dataset_id}/profile"
    )
