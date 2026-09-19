"""EDA tests for P3-ANALYSIS-005.

Every op compiles to read-only DuckDB and runs under the same gate and row cap
as a hand-written query, so these check both the numbers and the contract.
"""

import math

from fastapi.testclient import TestClient

from app.db import get_connection
from app.main import app, get_db
import app.db as db_module

CSV = (
    b"region,quarter,revenue,units\n"
    b"north,Q1,100.0,10\nnorth,Q2,150.0,15\nnorth,Q3,120.0,12\n"
    b"south,Q1,60.0,6\nsouth,Q2,90.0,9\nsouth,Q3,80.0,8\n"
)


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _dataset(client) -> tuple[str, str]:
    case_id = client.post(
        "/cases", json={"question": "Where is revenue moving?", "dataset": "s.csv"}
    ).json()["id"]
    dataset_id = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": ("s.csv", CSV, "text/csv")},
    ).json()["id"]
    return case_id, dataset_id


def _eda(client, case_id, dataset_id, **params):
    return client.post(
        f"/cases/{case_id}/datasets/{dataset_id}/eda", json=params
    )


def test_segment_groups_the_measure(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(
            client, case_id, dataset_id, op="segment", by="region", measure="revenue"
        )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["op"] == "segment"
    assert result["columns"] == [
        "segment", "rows", "mean", "median", "min", "max", "stddev"
    ]
    by_region = {row[0]: row for row in result["rows"]}
    assert by_region["north"][1] == 3
    assert by_region["north"][2] == 370.0 / 3
    assert by_region["south"][4] == 60.0
    assert by_region["north"][5] == 150.0


def test_correlates_two_numeric_columns(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(
            client, case_id, dataset_id, op="correlate", x="revenue", y="units"
        )

    assert response.status_code == 200, response.text
    row = response.json()["rows"][0]
    # Revenue is exactly 10x units in the fixture, so r is +1 up to float error.
    assert math.isclose(row[0], 1.0, abs_tol=1e-9)
    assert row[1] == 6


def test_distribution_summarises_a_numeric_column(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(
            client, case_id, dataset_id, op="distribution", column="revenue"
        )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["columns"] == [
        "rows", "min", "max", "mean", "median", "q1", "q3", "stddev"
    ]
    row = dict(zip(result["columns"], result["rows"][0]))
    assert row["rows"] == 6
    assert row["min"] == 60.0
    assert row["max"] == 150.0
    assert row["q1"] <= row["median"] <= row["q3"]


def test_distribution_falls_back_to_top_values_for_a_category(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(
            client, case_id, dataset_id, op="distribution", column="region"
        )

    assert response.status_code == 200, response.text
    result = response.json()
    assert result["columns"] == ["value", "rows"]
    values = {row[0]: row[1] for row in result["rows"]}
    assert values == {"north": 3, "south": 3}


def test_unknown_op_is_rejected(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(client, case_id, dataset_id, op="cluster", column="revenue")

    assert response.status_code == 400, response.text
    assert "cluster" in response.json()["detail"]


def test_unknown_column_is_rejected(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(
            client, case_id, dataset_id, op="segment", by="nope", measure="revenue"
        )

    assert response.status_code == 400, response.text
    assert "nope" in response.json()["detail"]


def test_missing_parameter_is_rejected(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(client, case_id, dataset_id, op="segment", by="region")

    assert response.status_code == 400, response.text
    assert "measure" in response.json()["detail"]


def test_edu_is_read_only(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, dataset_id = _dataset(client)
        response = _eda(
            client, case_id, dataset_id, op="distribution", column="revenue'; DROP TABLE x"
        )

    assert response.status_code == 400, response.text


def test_eda_404_for_unknown_dataset(tmp_path) -> None:
    _temp_env(tmp_path)
    with TestClient(app) as client:
        case_id, _ = _dataset(client)
        response = _eda(
            client, case_id, "no-such-dataset", op="distribution", column="revenue"
        )

    assert response.status_code == 404
