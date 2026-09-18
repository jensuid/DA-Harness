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


# DuckDB type families that support the basic stats below.
_NUMERIC_TYPES = (
    "TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT",
    "UTINYINT", "USMALLINT", "UINTEGER", "UBIGINT",
    "FLOAT", "DOUBLE", "REAL", "DECIMAL",
)
_TEMPORAL_TYPES = ("DATE", "TIME", "TIMESTAMP", "TIMESTAMP_MS", "TIMESTAMP_NS")


def _type_family(type_name: str) -> str:
    """Collapse a DuckDB type name into numeric / temporal / other."""
    upper = type_name.upper()
    for family, members in (
        ("numeric", _NUMERIC_TYPES),
        ("temporal", _TEMPORAL_TYPES),
    ):
        if any(upper.startswith(m) for m in members):
            return family
    return "other"


def profile_csv(path: str) -> dict:
    """Profile a tabular file: shape, per-column type and null stats, duplicates.

    Numeric and temporal columns also get min/max; numeric columns get an
    average. The profile is deterministic and is the input the AI planner will
    reason over, so it describes the data rather than just counting rows.

    The path is bound as a parameter, never interpolated into SQL text.
    Column names are quoted defensively; they come from DuckDB's own header
    parsing, not from user input.
    """
    connection = duckdb.connect()
    try:
        reader_call, bind_path = _reader_for(path)
        reader = connection.execute(f"SELECT * FROM {reader_call}", [bind_path])
        description = reader.description or []
        columns = [column[0] for column in description]
        # DuckDB reports logical types per column; they drive which stats apply.
        families = {name: _type_family(str(column[1])) for name, column in
                    zip(columns, description)}
        reader.fetchall()

        stats: dict[str, dict] = {}
        total_rows = 0
        duplicate_rows = 0
        if columns:
            # Each column contributes 2 base aggregates, plus min/max for
            # temporal/numeric and avg for numeric - so the flat result row is
            # sliced per column by how many aggregates that column produced.
            exprs = [_column_stat_expr(name, families[name]) for name in columns]
            widths = [_stat_width(families[name]) for name in columns]
            row = connection.execute(
                f"SELECT {', '.join(exprs)} FROM {reader_call}", [bind_path]
            ).fetchone()

            total_rows = connection.execute(
                f"SELECT COUNT(*) FROM {reader_call}", [bind_path]
            ).fetchone()[0]

            offset = 0
            for name, width in zip(columns, widths):
                stats[name] = _column_stat(
                    name, families[name], row[offset:offset + width], total_rows
                )
                offset += width
            duplicate_rows = _duplicate_row_count(connection, path)
    finally:
        connection.close()

    return {
        "rows": total_rows if columns else 0,
        "columns": columns,
        "stats": stats,
        "duplicate_rows": duplicate_rows,
    }


def _column_stat_expr(name: str, family: str) -> str:
    """Build the per-column aggregate expression for a profiling pass."""
    quoted = '"' + name.replace('"', '""') + '"'
    expr = (
        f"COUNT(*) - COUNT({quoted}) AS nulls,"
        f"COUNT(DISTINCT {quoted}) AS distinct_values"
    )
    if family in ("numeric", "temporal"):
        expr += f",MIN({quoted}) AS min_value,MAX({quoted}) AS max_value"
    if family == "numeric":
        expr += f",AVG({quoted}) AS avg_value"
    return expr


def _stat_width(family: str) -> int:
    """Aggregates _column_stat_expr emits for a column of this family."""
    if family == "numeric":
        return 5
    if family == "temporal":
        return 4
    return 2


def _coerce(value) -> object:
    """Make a DuckDB scalar JSON-safe (dates and decimals are not)."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def _column_stat(name: str, family: str, values, total_rows: int) -> dict:
    """Assemble one column's stat dict from its aggregate row."""
    null_count = int(values[0])
    stat = {
        "type": family,
        "null_count": null_count,
        "null_percentage": round(null_count / total_rows * 100, 2)
        if total_rows else 0.0,
        "distinct_count": int(values[1]),
    }
    if family in ("numeric", "temporal"):
        stat["min"] = _coerce(values[2])
        stat["max"] = _coerce(values[3])
    if family == "numeric":
        stat["avg"] = _coerce(values[4])
    return stat


def _duplicate_row_count(connection, path: str) -> int:
    """Count rows that are exact duplicates of an earlier row.

    Total rows minus distinct rows: a row appearing three times contributes two
    duplicates. Computed on the full row, not per column.
    """
    reader_call, bind_path = _reader_for(path)
    row = connection.execute(
        f"SELECT COUNT(*) FROM {reader_call}", [bind_path]
    ).fetchone()
    total = int(row[0])
    distinct = int(connection.execute(
        f"SELECT COUNT(*) FROM (SELECT DISTINCT * FROM {reader_call})",
        [bind_path],
    ).fetchone()[0])
    return total - distinct


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
