"""SQLite persistence for Analysis Cases, datasets, and profiles.

Owns case STATE only. Analytical queries belong in analysis.py against DuckDB -
the two stores stay separate by design (DEC-001).
"""

import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

DB_PATH = Path(os.environ.get("DAH_DB_PATH", Path(__file__).resolve().parent.parent / "dah.db"))

# Datasets are stored as files on disk; only their metadata lives in SQLite.
DATA_DIR = Path(os.environ.get("DAH_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS profiles (
    dataset_id TEXT PRIMARY KEY,
    rows INTEGER NOT NULL,
    columns_json TEXT NOT NULL,
    stats_json TEXT NOT NULL,
    profiled_at TEXT NOT NULL,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
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
        conn.executescript(SCHEMA)
        yield conn
        conn.commit()
    finally:
        conn.close()
