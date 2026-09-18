"""DuckDB analytical engine - the seed of the Data & Evidence Engine.

Analytical queries only. This module never writes Analysis Case state; that stays
in db.py on SQLite (DEC-001).
"""

import duckdb


def profile_csv(path: str) -> dict:
    """Profile a CSV: row count and column names.

    The path is bound as a parameter, never interpolated into SQL text.
    """
    connection = duckdb.connect()
    try:
        result = connection.execute("SELECT * FROM read_csv_auto(?)", [path])
        columns = [column[0] for column in (result.description or [])]
        rows = connection.execute(
            "SELECT COUNT(*) FROM read_csv_auto(?)", [path]
        ).fetchone()[0]
    finally:
        connection.close()
    return {"rows": rows, "columns": columns}
