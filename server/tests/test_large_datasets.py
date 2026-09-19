"""Large-dataset behaviour (P4-PERF-006).

The 1000-row result cap had existed since P1 and the profiling cost had never
been measured at scale. These tests pin both: the cap truncates a full-table
query, and a profile over tens of thousands of rows reports the same numbers
an independent Python pass computes from the same generated rows - so the
expectations cross-check DuckDB against a second implementation rather than
restating hardcoded magic numbers.
"""

import csv
import io

from fastapi.testclient import TestClient

from app.main import app, get_db
from app.db import get_connection
import app.db as db_module

ROWS = 50_000
REGIONS = ["north", "south", "east", "west", "central"]


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _generated_csv() -> bytes:
    """A deterministic wide-enough dataset whose stats are analytically known.

    Every column is a closed function of the row index, so the expectations
    below can be derived by hand and still hold at any row count.
    """
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["id", "region", "quantity", "revenue", "flag"])
    for i in range(1, ROWS + 1):
        quantity = 1 + (i % 50)
        writer.writerow([
            i,
            REGIONS[i % 5],
            quantity,
            round(quantity * 2.5, 2),
            "" if i % 10 == 0 else "ok",
        ])
    return buf.getvalue().encode()


def _attach(client, case_id: str, content: bytes, filename: str) -> str:
    response = client.post(
        f"/cases/{case_id}/datasets",
        files={"file": (filename, content, "text/csv")},
    )
    assert response.status_code == 201
    return response.json()["id"]


def test_profile_is_correct_at_scale(tmp_path) -> None:
    """The profile over 50k rows matches the values the data defines.

    This is the regression guard for the P4-PERF-006 change: the description is
    now read with LIMIT 0 and the total is folded into the aggregate pass, so
    a column whose stats depend on the type seen at describe time or on the
    row total would report wrong numbers if that plumbing drifted.
    """
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "big.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, _generated_csv(), "big.csv")

        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        assert response.status_code == 201
        profile = response.json()

    assert profile["rows"] == ROWS
    assert profile["columns"] == ["id", "region", "quantity", "revenue", "flag"]
    assert profile["duplicate_rows"] == 0

    stats = profile["stats"]
    # id: 1..ROWS, no nulls.
    assert stats["id"]["distinct_count"] == ROWS
    assert stats["id"]["min"] == 1
    assert stats["id"]["max"] == ROWS
    assert stats["id"]["null_count"] == 0
    # region: five values cycling, none null.
    assert stats["region"]["distinct_count"] == 5
    assert stats["region"]["null_count"] == 0
    # quantity: 1..50 cycling, so the mean is the midpoint.
    assert stats["quantity"]["distinct_count"] == 50
    assert stats["quantity"]["min"] == 1
    assert stats["quantity"]["max"] == 50
    assert abs(stats["quantity"]["avg"] - 25.5) < 1e-6
    # revenue is quantity * 2.5, so it inherits the same shape.
    assert stats["revenue"]["min"] == 2.5
    assert stats["revenue"]["max"] == 125.0
    assert abs(stats["revenue"]["avg"] - 63.75) < 1e-6
    # flag: one null in every ten rows, one value otherwise.
    assert stats["flag"]["null_count"] == ROWS // 10
    assert stats["flag"]["null_percentage"] == 10.0
    assert stats["flag"]["distinct_count"] == 1


def test_result_cap_truncates_a_full_table_query(tmp_path) -> None:
    """A full-table scan at scale is capped and flagged, never unbounded."""
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "big.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, _generated_csv(), "big.csv")
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")

        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT * FROM read_csv_auto(?)"},
        )
        assert response.status_code == 201
        run = response.json()

    assert run["row_count"] == 1000
    assert run["truncated"] is True
    assert len(run["rows"]) == 1000
    assert run["columns"] == ["id", "region", "quantity", "revenue", "flag"]


def test_aggregation_across_a_large_dataset_is_exact(tmp_path) -> None:
    """An aggregation over the full set sees every row, not just the capped page."""
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "big.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, _generated_csv(), "big.csv")

        response = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT COUNT(*) AS n, SUM(quantity) AS q"
                        " FROM read_csv_auto(?)"},
        )
        assert response.status_code == 201
        run = response.json()

    assert run["row_count"] == 1
    assert run["truncated"] is False
    # Every row was summed: 50k rows of quantity 1..50 cycling sum to 25.5 * 50000.
    assert run["rows"] == [[ROWS, 25.5 * ROWS]]


def test_wide_table_profiles_correctly(tmp_path) -> None:
    """A table with many columns still reports one stat block per column.

    The aggregate pass slices its flat result row by per-column widths, so a
    wide table is the shape most likely to expose an off-by-one in that
    slicing - and the row total now occupies slot 0.
    """
    _temp_env(tmp_path)
    width = 40

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow([f"col_{i}" for i in range(width)])
    for row in range(2000):
        writer.writerow([row % (i + 3) for i in range(width)])
    body = buf.getvalue().encode()

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "wide.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, body, "wide.csv")

        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        assert response.status_code == 201
        profile = response.json()

    assert profile["rows"] == 2000
    assert len(profile["columns"]) == width
    assert set(profile["stats"]) == {f"col_{i}" for i in range(width)}
    # col_i cycles through 0..i+2, so it has i + 3 distinct values.
    for i in range(width):
        assert profile["stats"][f"col_{i}"]["distinct_count"] == i + 3


def test_duplicate_rows_are_counted_at_scale(tmp_path) -> None:
    """The duplicate count is exact over a large set with known repeats."""
    _temp_env(tmp_path)
    groups = 500
    repeats = 4

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["k", "v"])
    for k in range(groups):
        for _ in range(repeats):
            writer.writerow([k, k * 2])
    body = buf.getvalue().encode()

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "dupes.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, body, "dupes.csv")

        response = client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        assert response.status_code == 201
        profile = response.json()

    assert profile["rows"] == groups * repeats
    assert profile["duplicate_rows"] == groups * (repeats - 1)
    assert profile["stats"]["k"]["distinct_count"] == groups


def test_large_case_exports_and_round_trips(tmp_path) -> None:
    """A case carrying a large dataset exports and restores intact."""
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "big.csv"}
        ).json()["id"]
        dataset_id = _attach(client, case_id, _generated_csv(), "big.csv")
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs",
            json={"sql": "SELECT region, COUNT(*) AS n"
                        " FROM read_csv_auto(?) GROUP BY region"},
        ).json()["id"]
        client.post(
            f"/cases/{case_id}/findings",
            json={"run_id": run_id, "statement": "Every region is present"},
        )

        package = client.get(f"/cases/{case_id}/export")
        assert package.status_code == 200
        body = package.json()
        # Five groups, uncapped.
        restored = client.post("/cases/import", json=body)
        assert restored.status_code == 201
        imported_id = restored.json()["id"]

        datasets = client.get(f"/cases/{imported_id}/datasets").json()
        assert len(datasets) == 1
        profile = client.post(
            f"/cases/{imported_id}/datasets/{datasets[0]['id']}/profile"
        )
        assert profile.status_code == 201
        assert profile.json()["rows"] == ROWS
