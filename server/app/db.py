"""SQLite persistence for Analysis Cases.

Owns case STATE only. Analytical queries belong in analysis.py against DuckDB -
the two stores stay separate by design (DEC-001).
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("DAH_DB_PATH", Path(__file__).resolve().parent.parent / "dah.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
"""


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Open a connection, ensuring the schema exists, and commit on success."""
    # FastAPI runs sync endpoints in a threadpool, so connections must be
    # usable across threads. Each request gets its own connection and commits
    # before closing, so sharing one connection across threads is safe here.
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        conn.execute(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()
