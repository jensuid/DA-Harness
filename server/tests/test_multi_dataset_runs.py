"""Multi-dataset run tests for P3-DATA-003.

Attaching several datasets per case already worked; the gap was the query
layer, which bound every placeholder to one file. These cover joining across
attached files of different formats, the error contract, and the evidence
chain (validation, duplicate, export) surviving a join run.
"""

import json

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

SALES = b"order_id,region,revenue\n1,north,100.0\n2,south,60.0\n3,north,80.0\n"
TARGETS = b"region,target\nnorth,150.0\nsouth,150.0\n"


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case_with_datasets(client):
    case_id = client.post(
        "/cases", json={"question": "Did regions hit target?", "dataset": "sales.csv"}
    ).json()["id"]
    sales = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("sales.csv", SALES, "text/csv")},
    ).json()["id"]
    targets = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("targets.csv", TARGETS, "text/csv")},
    ).json()["id"]
    return case_id, sales, targets


def _multi_run(client, case_id, dataset_ids, sql):
    return client.post(
        f"/cases/{case_id}/runs",
        json={"dataset_ids": dataset_ids, "sql": sql},
    )


JOIN_SQL = (
    "SELECT a.region, SUM(a.revenue) AS revenue, b.target "
    "FROM read_csv_auto(?) a JOIN read_csv_auto(?) b ON a.region = b.region "
    "GROUP BY a.region, b.target ORDER BY a.region"
)


def test_join_across_two_datasets(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        response = _multi_run(client, case_id, [sales, targets], JOIN_SQL)

    assert response.status_code == 201, response.text
    run = response.json()
    assert run["kind"] == "sql"
    assert run["dataset_id"] == sales
    assert run["dataset_ids"] == [sales, targets]
    assert run["columns"] == ["region", "revenue", "target"]
    assert run["rows"] == [["north", 180.0, 150.0], ["south", 60.0, 150.0]]


def test_placeholder_order_follows_dataset_ids(tmp_path) -> None:
    """The k-th placeholder binds to the k-th dataset, not to any file that fits."""
    _temp_env(tmp_path)
    # sales has order_id; targets does not. Only one binding order is valid,
    # which is what makes the assignment positional rather than by shape.
    sql = (
        "SELECT a.order_id FROM read_csv_auto(?) a "
        "JOIN read_csv_auto(?) b ON a.region = b.region"
    )
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        forward = _multi_run(client, case_id, [sales, targets], sql)
        reversed_response = _multi_run(client, case_id, [targets, sales], sql)
        both = _multi_run(client, case_id, [targets, targets], sql)

    assert forward.status_code == 201, forward.text
    assert forward.json()["columns"] == ["order_id"]
    assert reversed_response.status_code == 400, reversed_response.text
    assert "order_id" in reversed_response.json()["detail"]
    assert both.status_code == 400, both.text


def test_placeholder_count_must_match(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        response = _multi_run(client, case_id, [sales], JOIN_SQL)

    assert response.status_code == 400, response.text
    assert "placeholder" in response.json()["detail"]


def test_unknown_dataset_is_404(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, _ = _case_with_datasets(client)
        response = _multi_run(
            client, case_id, [sales, "no-such-dataset"], JOIN_SQL
        )

    assert response.status_code == 404, response.text
    assert "no-such-dataset" in response.json()["detail"]


def test_dataset_ids_must_be_unique(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        response = _multi_run(client, case_id, [sales, sales], JOIN_SQL)

    assert response.status_code == 400, response.text


def test_multi_run_is_read_only(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        response = _multi_run(
            client, case_id, [sales, targets], "DELETE FROM read_csv_auto(?)"
        )

    assert response.status_code == 400, response.text


def test_multi_run_reopens_and_lists(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        run_id = _multi_run(client, case_id, [sales, targets], JOIN_SQL).json()["id"]

        reopened = client.get(f"/cases/{case_id}/runs/{run_id}")
        assert reopened.status_code == 200
        assert reopened.json()["dataset_ids"] == [sales, targets]

        listed = client.get(f"/cases/{case_id}/runs").json()
        assert any(run["id"] == run_id for run in listed)
        summary = next(run for run in listed if run["id"] == run_id)
        assert summary["dataset_ids"] == [sales, targets]


def test_finding_on_a_join_run_validates(tmp_path) -> None:
    """The trust loop closes on a multi-dataset run too."""
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        run_id = _multi_run(client, case_id, [sales, targets], JOIN_SQL).json()["id"]
        finding = client.post(
            f"/cases/{case_id}/findings",
            json={
                "run_id": run_id,
                "statement": "North exceeded its revenue target.",
                "interpretation": "north is ahead",
                "caveat": "single period",
            },
        )
        assert finding.status_code == 201, finding.text
        result = client.post(
            f"/cases/{case_id}/findings/{finding.json()['id']}/validate"
        )

    assert result.status_code == 200, result.text
    checks = {check["name"]: check for check in result.json()["checks"]}
    assert checks["reproducibility"]["passed"]


def test_duplicate_copies_the_join_run(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        _multi_run(client, case_id, [sales, targets], JOIN_SQL)

        copied_id = client.post(f"/cases/{case_id}/duplicate").json()["id"]
        restored = client.get(f"/cases/{copied_id}/runs").json()
        copied_datasets = client.get(f"/cases/{copied_id}/datasets").json()

    assert len(restored) == 1
    run = restored[0]
    assert run["kind"] == "sql"
    assert run["dataset_ids"] is not None
    assert len(run["dataset_ids"]) == 2
    # The copy's run points at the copy's own datasets, never the source's.
    assert set(run["dataset_ids"]).isdisjoint({sales, targets})
    assert set(run["dataset_ids"]) <= {dataset["id"] for dataset in copied_datasets}


def test_join_run_exports_and_imports(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, sales, targets = _case_with_datasets(client)
        run_id = _multi_run(client, case_id, [sales, targets], JOIN_SQL).json()["id"]

        package = client.get(f"/cases/{case_id}/export").json()
        assert len(package["runs"][0]["dataset_ids"]) == 2

        imported_id = client.post("/cases/import", json=package).json()["id"]
        restored = client.get(f"/cases/{imported_id}/export").json()
        restored_run = restored["runs"][0]

    assert restored_run["sql"] == JOIN_SQL
    assert restored_run["rows"] == package["runs"][0]["rows"]
    assert len(restored_run["dataset_ids"]) == 2
    assert set(restored_run["dataset_ids"]) == {
        dataset["id"] for dataset in restored["datasets"]
    }
