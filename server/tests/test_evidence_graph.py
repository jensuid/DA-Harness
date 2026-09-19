"""Evidence graph tests for P3-EVIDENCE-006.

The graph is a projection of the persisted rows, so these build a real case and
check that every relationship the graph claims is one the data supports - and
that an unsupported claim shows up as an orphan rather than being hidden.
"""

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

SALES = b"order_id,region,revenue\n1,north,100.0\n2,south,60.0\n3,north,80.0\n"
TARGETS = b"region,target\nnorth,150.0\nsouth,150.0\n"
SQL = "SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _graph(client, case_id):
    response = client.get(f"/cases/{case_id}/evidence-graph")
    assert response.status_code == 200, response.text
    return response.json()


def _full_case(client):
    case_id = client.post(
        "/cases", json={"question": "Why did revenue differ?", "dataset": "sales.csv"}
    ).json()["id"]
    sales = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", SALES, "text/csv")},
    ).json()["id"]
    targets = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("targets.csv", TARGETS, "text/csv")},
    ).json()["id"]
    client.post(f"/cases/{case_id}/datasets/{sales}/profile")
    client.post(f"/cases/{case_id}/datasets/{sales}/plan")
    run_id = client.post(
        f"/cases/{case_id}/datasets/{sales}/runs", json={"sql": SQL}
    ).json()["id"]
    client.post(
        f"/cases/{case_id}/runs/{run_id}/charts",
        json={"kind": "bar", "x": "region", "y": "total"},
    )
    finding_id = client.post(
        f"/cases/{case_id}/findings",
        json={"run_id": run_id, "statement": "North leads revenue."},
    ).json()["id"]
    return case_id, sales, targets, run_id, finding_id


def test_graph_covers_every_artifact(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets, run_id, finding_id = _full_case(client)
        graph = _graph(client, case_id)

    kinds = {node["kind"] for node in graph["nodes"]}
    assert kinds == {"dataset", "run", "chart", "plan", "finding"}
    ids = {node["id"] for node in graph["nodes"]}
    assert {sales, targets, run_id, finding_id} <= ids
    assert graph["counts"]["datasets"] == 2
    assert graph["counts"]["findings"] == 1


def test_edges_describe_derivation(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _targets, run_id, finding_id = _full_case(client)
        graph = _graph(client, case_id)

    by_relation = {}
    for edge in graph["edges"]:
        by_relation.setdefault(edge["relation"], []).append((edge["source"], edge["target"]))

    # finding -> run -> dataset
    assert (finding_id, run_id) in by_relation["anchored_on"]
    assert (run_id, sales) in by_relation["queries"]
    # chart -> run, plan -> dataset
    chart_ids = [node["id"] for node in graph["nodes"] if node["kind"] == "chart"]
    assert any((chart_id, run_id) in by_relation["rendered_from"] for chart_id in chart_ids)
    plan_ids = [node["id"] for node in graph["nodes"] if node["kind"] == "plan"]
    assert any((plan_id, sales) in by_relation["planned_from"] for plan_id in plan_ids)
    # Every edge connects nodes that exist.
    ids = {node["id"] for node in graph["nodes"]}
    assert all(edge["source"] in ids and edge["target"] in ids for edge in graph["edges"])


def test_trace_walks_a_claim_to_its_source(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _t, _r, finding_id = _full_case(client)
        graph = _graph(client, case_id)

    trace = next(t for t in graph["traces"] if t["finding_id"] == finding_id)
    assert trace["reaches_source"] is True
    assert trace["hops"][0]["kind"] == "finding"
    assert trace["hops"][0]["label"] == "North leads revenue."
    assert trace["hops"][1]["kind"] == "run"
    assert trace["hops"][-1]["kind"] == "dataset"
    assert trace["hops"][-1]["label"] == "sales.csv"


def test_trace_covers_every_dataset_of_a_join_run(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets, _r, _f = _full_case(client)
        join = client.post(
            f"/cases/{case_id}/runs",
            json={
                "dataset_ids": [sales, targets],
                "sql": (
                    "SELECT a.region, SUM(a.revenue) AS total, b.target "
                    "FROM read_csv_auto(?) a JOIN read_csv_auto(?) b "
                    "ON a.region = b.region GROUP BY a.region, b.target"
                ),
            },
        )
        assert join.status_code == 201, join.text
        finding = client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": join.json()["id"], "statement": "North beat target."},
        )
        graph = _graph(client, case_id)

    trace = next(t for t in graph["traces"] if t["finding_id"] == finding.json()["id"])
    datasets = [hop["label"] for hop in trace["hops"] if hop["kind"] == "dataset"]
    assert set(datasets) == {"sales.csv", "targets.csv"}


def test_orphan_finding_is_reported_not_hidden(tmp_path) -> None:
    """A claim anchored on nothing shows up as an orphan, not as a trace."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _t, _r, _f = _full_case(client)
        # A finding whose run does not exist cannot be created through the API,
        # so insert one directly to model a dangling claim, in the case's own
        # database (not a throwaway file the app never reads).
        import sqlite3

        connection = sqlite3.connect(tmp_path / "test.db")
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            "INSERT INTO findings (id, case_id, run_id, statement, "
            "validation_status, created_at) VALUES (?, ?, ?, ?, ?, ?)",
            ("orphan-1", case_id, "run-that-was-deleted", "A bare claim.",
             "not_evaluated", "2026-01-01T00:00:00+00:00"),
        )
        connection.commit()
        connection.close()

        graph = _graph(client, case_id)

    assert "orphan-1" in graph["orphan_findings"]
    orphan = next(t for t in graph["traces"] if t["finding_id"] == "orphan-1")
    assert orphan["reaches_source"] is False
    assert len(orphan["hops"]) == 1


def test_graph_400_when_the_case_is_empty(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "Nothing here yet", "dataset": "s.csv"}
        ).json()["id"]
        response = client.get(f"/cases/{case_id}/evidence-graph")

    assert response.status_code == 400, response.text
    assert "no artifacts" in response.json()["detail"]


def test_graph_404_for_unknown_case(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        response = client.get("/cases/no-such-case/evidence-graph")
    assert response.status_code == 404
