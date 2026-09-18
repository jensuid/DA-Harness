"""DuckDB analytical engine - the seed of the Data & Evidence Engine.

Analytical queries only. This module never writes Analysis Case state; that stays
in db.py on SQLite (DEC-001).
"""

import duckdb

# Only these statements may run. Anything else (INSERT/UPDATE/DELETE, COPY,
# ATTACH, PRAGMA, CALL ...) is rejected before execution.
_ALLOWED_PREFIXES = ("select", "with", "values", "table", "show", "describe")


def _is_read_only(sql: str) -> bool:
    """Reject anything that is not a single read-only statement."""
    stripped = sql.strip().rstrip(";").strip()
    if not stripped:
        return False
    if ";" in stripped:
        return False
    return stripped.lower().startswith(_ALLOWED_PREFIXES)


def profile_csv(path: str) -> dict:
    """Profile a CSV: row count, columns, and per-column null counts.

    The path is bound as a parameter, never interpolated into SQL text.
    Column names are quoted defensively; they come from DuckDB's own header
    parsing, not from user input.
    """
    connection = duckdb.connect()
    try:
        reader = connection.execute("SELECT * FROM read_csv_auto(?)", [path])
        columns = [column[0] for column in (reader.description or [])]
        rows = len(reader.fetchall()) if columns else 0

        stats: dict[str, dict] = {}
        if columns:
            null_exprs = ", ".join(
                'COUNT(*) - COUNT("' + column.replace('"', '""') + '")'
                for column in columns
            )
            null_counts = connection.execute(
                "SELECT " + null_exprs + " FROM read_csv_auto(?)", [path]
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
        reader = connection.execute(sql, [path])
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
