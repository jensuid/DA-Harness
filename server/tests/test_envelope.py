"""The supported size envelopes, declared and enforced (AT-45, AT-46).

The PRD requires the MVP to state what it supports instead of claiming
unlimited scale, and to refuse beyond it rather than hang. These tests pin
both halves: the declaration is published at `GET /envelope` with the PRD's
own benchmark numbers, and a dataset past any limit is a 400 naming the limit
it broke and the size it measured - never a hang, and never a silent success.

The row limits are the PRD's millions, and committing a five-million-row
fixture to prove the refusal would be absurd, so the tests tighten the limit
on the module the enforcement function reads it from. The code path is
identical at any value: the same comparison, the same sentence, the same
cleanup. One test then asserts the default really is the PRD's number, so the
declared envelope cannot drift unnoticed.
"""

import io

import pytest

from fastapi.testclient import TestClient

from app import limits as limits_module
from app.db import get_connection
from app.main import app, get_db
import app.db as db_module


def _temp_env(tmp_path):
    db_module.DATA_DIR = tmp_path / "data"
    db_path = tmp_path / "test.db"
    app.dependency_overrides.clear()

    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _case(client) -> str:
    return client.post(
        "/cases", json={"question": "q", "dataset": "data.csv"}
    ).json()["id"]


def _attach(client, case_id: str, filename: str, content: bytes):
    return client.post(
        f"/cases/{case_id}/datasets",
        files={"file": (filename, content, "text/csv")},
    )


def _wide_csv(columns: int, rows: int = 3) -> bytes:
    buf = io.StringIO()
    buf.write(",".join(f"c{i}" for i in range(columns)) + "\n")
    for r in range(rows):
        buf.write(",".join(str(r) for _ in range(columns)) + "\n")
    return buf.getvalue().encode()


def test_envelope_publishes_the_prd_targets() -> None:
    """AT-45 and AT-46's numbers are declared, not assumed."""
    response = TestClient(app).get("/envelope")
    assert response.status_code == 200
    published = response.json()

    formats = published["datasets"]["formats"]
    assert formats["csv"] == {"max_rows": 5_000_000, "max_columns": 100}
    assert formats["parquet"] == formats["csv"]
    assert formats["xlsx"] == {"max_rows": 500_000, "max_columns": 100}
    assert published["cases"] == {
        "max_runs": 100,
        "max_results": 500,
        "max_findings": 200,
        "max_evidence_relationships": 1_000,
    }


def test_the_envelope_is_read_only_and_needs_nothing() -> None:
    """A GET with no body, no path parameter and no store writes nothing."""
    before = limits_module.MAX_ROWS
    response = TestClient(app).get("/envelope")
    assert response.status_code == 200
    assert limits_module.MAX_ROWS == before


@pytest.mark.parametrize(
    "constant, default",
    [
        ("MAX_ROWS", 5_000_000),
        ("DEFAULT_MAX_ROWS", 5_000_000),
        ("MAX_COLUMNS", 100),
        ("MAX_EXCEL_ROWS", 500_000),
    ],
)
def test_the_declared_limits_are_the_prd_defaults(constant: str, default: int) -> None:
    """The shipped envelope is the PRD's benchmark, whatever it was configured from.

    Reloaded deliberately not used: `importlib.reload` rebinds the module's
    classes, and `attach_dataset`'s `except EnvelopeExceeded` still names the
    class it imported, so a reload mid-suite turns a clean 400 into a 500.
    """
    assert getattr(limits_module, constant) == default


def test_an_unparseable_limit_is_ignored_not_applied(monkeypatch) -> None:
    """A typo in the env var must not silently disable the envelope."""
    monkeypatch.setenv("DAH_LIMIT_PROBE", "not-a-number")
    assert limits_module._limit("DAH_LIMIT_PROBE", 5) == 5
    monkeypatch.setenv("DAH_LIMIT_PROBE", "0")
    assert limits_module._limit("DAH_LIMIT_PROBE", 100) == 100
    monkeypatch.setenv("DAH_LIMIT_PROBE", "7")
    assert limits_module._limit("DAH_LIMIT_PROBE", 100) == 7
    monkeypatch.delenv("DAH_LIMIT_PROBE")
    assert limits_module._limit("DAH_LIMIT_PROBE", 100) == 100


def test_too_many_columns_is_refused_at_attach(tmp_path, monkeypatch) -> None:
    """AT-45: a too-wide file answers a 400 naming the limit and the width."""
    monkeypatch.setattr(limits_module, "MAX_COLUMNS", 10)
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client)
        response = _attach(client, case_id, "wide.csv", _wide_csv(11))

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "11 columns" in detail
    assert "10" in detail
    # The refused file leaves nothing behind.
    assert not list((tmp_path / "data").rglob("wide.csv"))


def test_too_many_rows_is_refused_at_attach(tmp_path, monkeypatch) -> None:
    """AT-45: a too-tall file answers a 400 naming the limit and the row count.

    The limit is tightened here; the path is the one a six-million-row CSV
    takes, and the sentence carries the numbers the analyst needs.
    """
    monkeypatch.setattr(limits_module, "MAX_ROWS", 5)
    _temp_env(tmp_path)

    buf = io.StringIO()
    buf.write("id,value\n")
    for i in range(6):
        buf.write(f"{i},{i}\n")

    with TestClient(app) as client:
        case_id = _case(client)
        response = _attach(client, case_id, "tall.csv", buf.getvalue().encode())

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "6 rows" in detail
    assert "5" in detail
    assert "CSV/Parquet" in detail


def test_a_refused_dataset_leaves_no_row_behind(tmp_path, monkeypatch) -> None:
    """The refusal is clean: no dataset row, no file, no stage movement."""
    monkeypatch.setattr(limits_module, "MAX_ROWS", 5)
    _temp_env(tmp_path)

    with TestClient(app) as client:
        case_id = _case(client)
        buf = io.StringIO()
        buf.write("id,value\n")
        for i in range(6):
            buf.write(f"{i},{i}\n")
        refused = _attach(client, case_id, "tall.csv", buf.getvalue().encode())

        assert refused.status_code == 400
        assert client.get(f"/cases/{case_id}/datasets").json() == []

        # The refusal is not sticky: a file inside the envelope attaches on the
        # next attempt, so the analyst is not locked out of the case.
        again = _attach(client, case_id, "small.csv", b"id,value\n1,10\n")
        assert again.status_code == 201


def test_a_dataset_just_inside_the_envelope_is_accepted(tmp_path, monkeypatch) -> None:
    """The boundary is inclusive: the declared maximum is supported, not 1 less."""
    monkeypatch.setattr(limits_module, "MAX_ROWS", 5)
    monkeypatch.setattr(limits_module, "MAX_COLUMNS", 3)
    _temp_env(tmp_path)

    buf = io.StringIO()
    buf.write("id,value,region\n")
    for i in range(5):
        buf.write(f"{i},{i},north\n")

    with TestClient(app) as client:
        case_id = _case(client)
        response = _attach(client, case_id, "envelope.csv", buf.getvalue().encode())

    assert response.status_code == 201
    assert response.json()["format"] == "csv"


def test_an_excel_workbook_past_its_limit_is_refused(tmp_path, monkeypatch) -> None:
    """Excel's envelope is separate and smaller, and is enforced the same way."""
    monkeypatch.setattr(limits_module, "MAX_EXCEL_ROWS", 5)
    _temp_env(tmp_path)

    import openpyxl

    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["id", "value"])
    for i in range(6):
        sheet.append([i, i])
    buffer = io.BytesIO()
    workbook.save(buffer)

    with TestClient(app) as client:
        case_id = _case(client)
        response = client.post(
            f"/cases/{case_id}/datasets",
            files={
                "file": (
                    "book.xlsx",
                    buffer.getvalue(),
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
            },
        )

    assert response.status_code == 400
    detail = response.json()["detail"]
    assert "6 rows" in detail
    assert "xlsx" in detail


def test_an_excel_workbook_inside_the_envelope_is_measured(tmp_path) -> None:
    """The workbook measurement counts records and skips trailing empties."""
    import openpyxl

    path = tmp_path / "book.xlsx"
    workbook = openpyxl.Workbook()
    sheet = workbook.active
    sheet.append(["id", "value", "region"])
    for i in range(4):
        sheet.append([i, i, "north"])
    # Trailing rows the writer emitted with no values are not records.
    sheet.append([])
    sheet.append([None, None, None])
    workbook.save(path)

    rows, columns = limits_module.measure_dataset(str(path), "xlsx")
    assert rows == 4
    assert columns == 3


def test_measure_counts_csv_and_parquet(tmp_path) -> None:
    """The measurement is the same for both tabular formats."""
    import pyarrow as pa
    import pyarrow.parquet as pq

    csv_path = tmp_path / "data.csv"
    csv_path.write_text("id,value\n1,10\n2,20\n3,30\n")

    table = pa.table({"id": [1, 2, 3], "value": [10, 20, 30]})
    parquet_path = tmp_path / "data.parquet"
    pq.write_table(table, parquet_path)

    assert limits_module.measure_dataset(str(csv_path), "csv") == (3, 2)
    assert limits_module.measure_dataset(str(parquet_path), "parquet") == (3, 2)


def test_a_missing_file_is_refused_not_crashed(tmp_path) -> None:
    """An unreadable path answers the envelope's own sentence, not a 500."""
    with pytest.raises(limits_module.EnvelopeExceeded):
        limits_module.check_dataset_envelope(str(tmp_path / "gone.csv"), "csv")


def test_the_case_envelope_constants_are_the_prd_benchmark() -> None:
    """AT-46's engineering limits, stated once where the suite can see them."""
    assert limits_module.MAX_RUNS == 100
    assert limits_module.MAX_RESULTS == 500
    assert limits_module.MAX_FINDINGS == 200
    assert limits_module.MAX_EVIDENCE_RELATIONSHIPS == 1_000
