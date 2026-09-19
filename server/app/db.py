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
    format TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS profiles (
    dataset_id TEXT PRIMARY KEY,
    rows INTEGER NOT NULL,
    columns_json TEXT NOT NULL,
    stats_json TEXT NOT NULL,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    profiled_at TEXT NOT NULL,
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);

CREATE TABLE IF NOT EXISTS findings (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    statement TEXT NOT NULL,
    interpretation TEXT,
    caveat TEXT,
    validation_status TEXT NOT NULL DEFAULT 'not_evaluated',
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS runs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    kind TEXT NOT NULL DEFAULT 'sql',
    sql TEXT,
    code TEXT,
    dataset_ids_json TEXT,
    columns_json TEXT NOT NULL,
    rows_json TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    truncated INTEGER NOT NULL,
    executed_at TEXT NOT NULL,
        FOREIGN KEY (case_id) REFERENCES cases(id),
        FOREIGN KEY (dataset_id) REFERENCES datasets(id)
    );

CREATE TABLE IF NOT EXISTS charts (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    x TEXT NOT NULL,
    y TEXT NOT NULL,
    series TEXT,
    title TEXT NOT NULL DEFAULT '',
    stored_path TEXT NOT NULL,
    width INTEGER NOT NULL,
    height INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS plans (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    question TEXT NOT NULL,
    plan_json TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id)
);
"""


def _ensure_column(conn, table: str, column: str, definition: str) -> None:
    """Add a column to an older schema; a no-op on current ones."""
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})")
    }
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


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
        # Databases created before the format column existed need it added.
        # Guarded so it is a no-op on current schemas.
        _ensure_column(conn, "datasets", "format", "TEXT")
        _ensure_column(conn, "profiles", "duplicate_rows", "INTEGER DEFAULT 0")
        # Runs created before P2-ANALYSIS-008 were SQL-only.
        _ensure_column(conn, "runs", "kind", "TEXT NOT NULL DEFAULT 'sql'")
        _ensure_column(conn, "runs", "code", "TEXT")
        # Runs created before P3-DATA-003 touch a single dataset; the JSON list
        # is the full set, dataset_id kept as the primary for old code paths.
        _ensure_column(conn, "runs", "dataset_ids_json", "TEXT")
        yield conn
        conn.commit()
    finally:
        conn.close()
