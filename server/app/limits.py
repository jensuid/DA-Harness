"""The supported size envelopes (AT-45, AT-46).

The PRD requires the MVP to *declare* what it supports rather than claim
unlimited scale, and to refuse clearly beyond it instead of hanging: "a 6M-row
CSV is processed or rejected, never silently hung". Two envelopes exist, both
declared by `GET /envelope` so the contract is published and testable rather
than folklore:

    AT-45 - the dataset envelope. CSV and Parquet at most 5,000,000 rows and
            100 columns; Excel at most 500,000 rows (the PRD's own benchmark
            numbers, revisable after measurement).
    AT-46 - the case envelope. 100 runs, 500 results, 200 findings and 1,000
            evidence relationships. Engineering benchmark limits, not
            conceptual ones.

The dataset envelope is enforced at attach, the earliest moment the file is on
disk: a dataset beyond it is a 400 naming the limit it broke and the size it
measured, before a profile or a run ever scans it. The row count comes from a
streaming aggregate, so measuring a file inside the envelope costs one scan and
measuring one far beyond it does not first load it into memory. The limits read
from the environment at import so a deployment can tighten them, and the
rejection path is the same code at any value - which is also what makes the
envelope testable without committing a five-million-row fixture.

The case envelope is a stability benchmark rather than a hard refusal: the PRD
asks that the application remain stable within it, so the measurement layer
builds a case at the boundary and proves it does (P8-MEASURE-009).
"""

from __future__ import annotations

import os
from pathlib import Path

# AT-45. The PRD's recommended initial benchmark; the exact numbers may be
# revised after measurement, and the endpoint publishes whatever these are.
DEFAULT_MAX_ROWS = 5_000_000
DEFAULT_MAX_COLUMNS = 100
DEFAULT_MAX_EXCEL_ROWS = 500_000

# AT-46. Engineering benchmark limits for one Analysis Case.
MAX_RUNS = 100
MAX_RESULTS = 500
MAX_FINDINGS = 200
MAX_EVIDENCE_RELATIONSHIPS = 1_000

EXCEL_FORMAT = "xlsx"


def _limit(name: str, default: int) -> int:
    """A limit read from the environment, refusing a value that is not one.

    An unparsable or non-positive value is ignored rather than applied: a
    typo in `DAH_MAX_CSV_ROWS=1e6` must not silently disable the envelope.
    """
    raw = os.environ.get(name, "").strip()
    if not raw:
        return default
    try:
        parsed = int(raw)
    except ValueError:
        return default
    return parsed if parsed > 0 else default


MAX_ROWS = _limit("DAH_MAX_ROWS", DEFAULT_MAX_ROWS)
MAX_COLUMNS = _limit("DAH_MAX_COLUMNS", DEFAULT_MAX_COLUMNS)
MAX_EXCEL_ROWS = _limit("DAH_MAX_EXCEL_ROWS", DEFAULT_MAX_EXCEL_ROWS)


class EnvelopeExceeded(ValueError):
    """A dataset lies outside the supported envelope (AT-45).

    A `ValueError`, so the API's input-error handling answers it with a 400
    and the analyst's own sentence, never a 500 that blames the harness.
    """


def dataset_limits() -> dict:
    """The declared dataset envelope, as `GET /envelope` publishes it."""
    return {
        "csv": {"max_rows": MAX_ROWS, "max_columns": MAX_COLUMNS},
        "parquet": {"max_rows": MAX_ROWS, "max_columns": MAX_COLUMNS},
        EXCEL_FORMAT: {"max_rows": MAX_EXCEL_ROWS, "max_columns": MAX_COLUMNS},
    }


def case_limits() -> dict:
    """The declared case envelope (AT-46), as `GET /envelope` publishes it."""
    return {
        "max_runs": MAX_RUNS,
        "max_results": MAX_RESULTS,
        "max_findings": MAX_FINDINGS,
        "max_evidence_relationships": MAX_EVIDENCE_RELATIONSHIPS,
    }


def measure_dataset(path: str, fmt: str) -> tuple[int, int]:
    """Count a dataset's rows and columns without materialising it.

    One streaming aggregate answers the row count, so a file far beyond the
    envelope is measured in a bounded pass rather than loaded first. The
    column count comes from the schema description, which needs no rows at
    all. Returns (0, 0) for a file with no readable header.

    DuckDB raises `duckdb.Error` for a file it cannot open; that is an input
    error by the API's taxonomy and the caller lets it answer the 400 it
    already answers for an unreadable upload.
    """
    stored = Path(path)
    if not stored.is_file():
        raise EnvelopeExceeded(f"the uploaded file is not readable at {path}")

    if fmt.lower() == EXCEL_FORMAT:
        return _measure_workbook(stored)

    import duckdb

    reader = "read_parquet(?)" if fmt.lower() == "parquet" else "read_csv_auto(?)"
    connection = duckdb.connect()
    try:
        columns = connection.execute(
            f"SELECT * FROM {reader} LIMIT 0", [str(stored)]
        ).description or []
        count = connection.execute(
            f"SELECT COUNT(*) FROM {reader}", [str(stored)]
        ).fetchone()
    finally:
        connection.close()
    return (int(count[0]) if count else 0), len(columns)


def _measure_workbook(path: Path) -> tuple[int, int]:
    """Count an .xlsx by streaming its rows, without converting it to parquet.

    The conversion is the expensive step a refusal exists to skip, so the
    envelope measures the workbook directly: a read-only scan counts the
    non-empty rows and the header gives the column count.
    """
    import openpyxl

    workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
    try:
        sheet = workbook[workbook.sheetnames[0]]
        rows = sheet.iter_rows(values_only=True)
        header = next(rows, None)
        if header is None:
            return (0, 0)
        columns = sum(1 for cell in header if cell is not None)
        # The sheet's own row count includes trailing empty rows the writer
        # emitted; a row with no values is not a record.
        data_rows = sum(1 for row in rows if any(cell is not None for cell in row))
    finally:
        workbook.close()
    return data_rows, columns


def check_dataset_envelope(path: str, fmt: str) -> tuple[int, int]:
    """Measure a dataset and refuse it if it lies outside the envelope.

    Raises `EnvelopeExceeded` with a sentence naming the limit it broke, the
    size that broke it and the format family, so the 400 the analyst receives
    says what to do. Returns the measured (rows, columns) when the dataset is
    inside the envelope.
    """
    rows, columns = measure_dataset(path, fmt)
    family = EXCEL_FORMAT if fmt.lower() == EXCEL_FORMAT else "CSV/Parquet"
    max_rows = MAX_EXCEL_ROWS if fmt.lower() == EXCEL_FORMAT else MAX_ROWS

    if columns > MAX_COLUMNS:
        raise EnvelopeExceeded(
            f"the dataset has {columns} columns and the supported envelope "
            f"allows {MAX_COLUMNS}; reduce the width or export a subset "
            f"(GET /envelope publishes the limits)"
        )
    if rows > max_rows:
        raise EnvelopeExceeded(
            f"the dataset has {rows:,} rows and the supported {family} envelope "
            f"allows {max_rows:,}; reduce the size or export a subset "
            f"(GET /envelope publishes the limits)"
        )
    return rows, columns
