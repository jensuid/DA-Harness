"""DuckDB analytical engine - the seed of the Data & Evidence Engine.

Analytical queries only. This module never writes Analysis Case state; that stays
in db.py on SQLite (DEC-001).
"""

import duckdb

_XLSX_CACHE: dict[str, str] = {}

# Only these statements may run. Anything else (INSERT/UPDATE/DELETE, COPY,
# ATTACH, PRAGMA, CALL ...) is rejected before execution.
_ALLOWED_PREFIXES = ("select", "with", "values", "table", "show", "describe")


def _reader_for(path: str) -> tuple[str, str]:
    """Return the DuckDB reader call and the path to bind for a file.

    DuckDB cannot read .xlsx without an extension that is not installable in
    every environment, so xlsx is converted to parquet once and cached. The
    bound path is then the converted file, not the original workbook.
    All downstream reads stay on DuckDB - one engine, one path.
    """
    suffix = path.lower().rsplit(".", 1)[-1]
    if suffix == "parquet":
        return "read_parquet(?)", path
    if suffix != "xlsx":
        return "read_csv_auto(?)", path

    if path not in _XLSX_CACHE:
        import openpyxl

        workbook = openpyxl.load_workbook(path, read_only=True, data_only=True)
        sheet = workbook[workbook.sheetnames[0]]

        rows = sheet.iter_rows(values_only=True)
        header = [str(cell) if cell is not None else "" for cell in next(rows)]
        data = [
            [None if cell is None else cell for cell in row]
            for row in rows
            if any(cell is not None for cell in row)
        ]
        workbook.close()

        import pyarrow as pa
        import pyarrow.parquet as pq

        table = pa.table(
            {name: pa.array([row[i] if i < len(row) else None for row in data])
             for i, name in enumerate(header)}
        )
        converted = path + ".parquet"
        pq.write_table(table, converted)
        _XLSX_CACHE[path] = converted
    return "read_parquet(?)", _XLSX_CACHE[path]


_DATASET_PLACEHOLDERS = ("read_csv_auto(?)", "read_parquet(?)")


def _bind_dataset(sql: str, path: str) -> tuple[str, list]:
    """Swap the dataset placeholder(s) in user SQL for this file's reader.

    Either placeholder is accepted so the natural form works for every format;
    the actual reader is chosen from the file, not from what the user typed.
    Returns the rewritten SQL plus the parameter(s) to bind - one per
    placeholder occurrence, since xlsx reads bind the converted parquet path.
    """
    reader_call, bind_path = _reader_for(path)
    occurrences = sum(sql.count(p) for p in _DATASET_PLACEHOLDERS)
    for placeholder in _DATASET_PLACEHOLDERS:
        sql = sql.replace(placeholder, reader_call)
    return sql, [bind_path] * occurrences


def _is_read_only(sql: str) -> bool:
    """Reject anything that is not a single read-only statement."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        return False
    if ";" in stripped:
        return False
    return stripped.lower().startswith(_ALLOWED_PREFIXES)


def profile_csv(path: str) -> dict:
    """Profile a tabular file: row count, columns, and per-column null counts.

    The path is bound as a parameter, never interpolated into SQL text.
    Column names are quoted defensively; they come from DuckDB's own header
    parsing, not from user input.
    """
    connection = duckdb.connect()
    try:
        reader_call, bind_path = _reader_for(path)
        reader = connection.execute(f"SELECT * FROM {reader_call}", [bind_path])
        columns = [column[0] for column in (reader.description or [])]
        rows = len(reader.fetchall()) if columns else 0

        stats: dict[str, dict] = {}
        if columns:
            null_exprs = ", ".join(
                'COUNT(*) - COUNT("' + column.replace('"', '""') + '")'
                for column in columns
            )
            null_counts = connection.execute(
                f"SELECT {null_exprs} FROM {reader_call}", [bind_path]
            ).fetchone()
            for index, column in enumerate(columns):
                stats[column] = {"null_count": int(null_counts[index])}
    finally:
        connection.close()
    return {"rows": rows, "columns": columns, "stats": stats}


def run_query(path: str, sql: str, limit: int = 1000) -> dict:
    """Run a read-only SQL query against a CSV file.

    The dataset path is bound as a parameter; only the read-only check inspects
    the query text. Results are capped to avoid unbounded memory use.
    """
    if not _is_read_only(sql):
        raise ValueError("only single read-only SELECT queries are supported")

    connection = duckdb.connect()
    try:
        bound_sql, params = _bind_dataset(sql, path)
        reader = connection.execute(bound_sql, params)
        columns = [column[0] for column in (reader.description or [])]
        rows = reader.fetchmany(limit + 1)
    finally:
        connection.close()

    truncated = len(rows) > limit
    if truncated:
        rows = rows[:limit]
    return {
        "columns": columns,
        "rows": [list(row) for row in rows],
        "row_count": len(rows),
        "truncated": truncated,
    }
