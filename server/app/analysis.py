"""DuckDB analytical engine - the seed of the Data & Evidence Engine.

Analytical queries only. This module never writes Analysis Case state; that stays
in db.py on SQLite (DEC-001).
"""

import duckdb


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
