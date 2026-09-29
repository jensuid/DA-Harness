"""SQLite persistence for Analysis Cases, datasets, and profiles.

Owns case STATE only. Analytical queries belong in analysis.py against DuckDB -
the two stores stay separate by design (DEC-001).

Schema evolution: opening a store upgrades it to the current shape through a
recorded, forward-only chain (see MIGRATIONS and _migrate). The version lives in
SQLite's `user_version` pragma, which is stored in the file header and so
survives without a table; the `schema_migrations` rows are the audit trail of
what actually ran and when.
"""

import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Iterator

DB_PATH = Path(os.environ.get("DAH_DB_PATH", Path(__file__).resolve().parent.parent / "dah.db"))

# Datasets are stored as files on disk; only their metadata lives in SQLite.
DATA_DIR = Path(os.environ.get("DAH_DATA_DIR", Path(__file__).resolve().parent.parent / "data"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    template_id TEXT,
    duplicate_of TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS datasets (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    format TEXT NOT NULL DEFAULT 'unknown',
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS profiles (
    dataset_id TEXT PRIMARY KEY,
    rows INTEGER NOT NULL,
    columns_json TEXT NOT NULL,
    stats_json TEXT NOT NULL,
    duplicate_rows INTEGER NOT NULL DEFAULT 0,
    quality_json TEXT NOT NULL DEFAULT '[]',
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
    shape_json TEXT,
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

CREATE TABLE IF NOT EXISTS interpretations (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    case_id TEXT NOT NULL,
    summary TEXT NOT NULL,
    observations_json TEXT NOT NULL,
    caveats_json TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);

CREATE TABLE IF NOT EXISTS agent_steps (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    kind TEXT NOT NULL,
    payload_json TEXT NOT NULL,
    source TEXT NOT NULL,
    status TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'analyst',
    note TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL,
    decided_at TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS conversations (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    message TEXT NOT NULL,
    answer TEXT NOT NULL,
    grounds_json TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS contexts (
    case_id TEXT PRIMARY KEY,
    purpose TEXT NOT NULL DEFAULT '',
    sub_questions_json TEXT NOT NULL DEFAULT '[]',
    hypotheses_json TEXT NOT NULL DEFAULT '[]',
    constraints_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS refinements (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    original_question TEXT NOT NULL,
    refined_question TEXT NOT NULL DEFAULT '',
    rationale TEXT NOT NULL DEFAULT '',
    grounds_json TEXT NOT NULL DEFAULT '[]',
    source TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'pending',
    edited_question TEXT,
    created_at TEXT NOT NULL,
    decided_at TEXT,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS validations (
    finding_id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    run_id TEXT NOT NULL,
    status TEXT NOT NULL,
    checks_json TEXT NOT NULL,
    validated_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (finding_id) REFERENCES findings(id)
);

CREATE TABLE IF NOT EXISTS decisions (
    case_id TEXT PRIMARY KEY,
    implications_json TEXT NOT NULL DEFAULT '[]',
    updated_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id)
);

CREATE TABLE IF NOT EXISTS schema_migrations (
    version INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS evaluations (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    run_id TEXT,
    artifact_kind TEXT NOT NULL,
    code TEXT NOT NULL,
    claim TEXT NOT NULL,
    findings_json TEXT NOT NULL,
    source TEXT NOT NULL,
    created_at TEXT NOT NULL,
    FOREIGN KEY (case_id) REFERENCES cases(id),
    FOREIGN KEY (dataset_id) REFERENCES datasets(id),
    FOREIGN KEY (run_id) REFERENCES runs(id)
);
"""


def _ensure_column(conn, table: str, column: str, definition: str) -> None:
    """Add a column to an older schema; a no-op on current ones.

    Guarded by PRAGMA table_info rather than assuming: a store may have arrived
    at a partial state through any earlier release, and a re-run after a
    crashed upgrade must not error on the column it already added.
    """
    existing = {
        row["name"]
        for row in conn.execute(f"PRAGMA table_info({table})")
    }
    if column not in existing:
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")


# The current shape of the store. Opening a store below this upgrades it;
# opening one above it is refused (see _check_version) rather than silently
# treated as current, because a downgrade against an unknown schema is how a
# store is corrupted quietly.
LATEST_SCHEMA_VERSION = 14


class Migration:
    """One forward-only schema change.

    A migration is a version number, a name a reader can understand, and a
    call that makes the change. Every historical migration is guarded, so it
    is a no-op on a store that already has its result - which is what makes an
    upgrade resumable: after a crash, the next open re-runs the pending
    migration without erroring on the part it already finished.
    """

    def __init__(self, version: int, name: str, apply: Callable[[sqlite3.Connection], None]):
        self.version = version
        self.name = name
        self.apply = apply


def _m_datasets_format(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "datasets", "format", "TEXT NOT NULL DEFAULT 'unknown'")


def _m_profiles_duplicate_rows(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "profiles", "duplicate_rows", "INTEGER NOT NULL DEFAULT 0")


def _m_runs_kind(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "runs", "kind", "TEXT NOT NULL DEFAULT 'sql'")


def _m_runs_code(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "runs", "code", "TEXT")


def _m_runs_dataset_ids_json(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "runs", "dataset_ids_json", "TEXT")


def _m_templates_shape_json(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "templates", "shape_json", "TEXT")


def _m_cases_template_id(conn: sqlite3.Connection) -> None:
    _ensure_column(conn, "cases", "template_id", "TEXT")


def _m_cases_duplicate_of(conn: sqlite3.Connection) -> None:
    # A case created with another's exact question+dataset records which one it
    # repeats (W2X-010). Advisory like template_id: it is read to warn, never
    # to enforce, so a store that predates it answers "not a duplicate".
    _ensure_column(conn, "cases", "duplicate_of", "TEXT")


def _m_evaluations_table(conn: sqlite3.Connection) -> None:
    # EVALUATE mode's own store (P7-EVAL-001). Created here rather than relying
    # on SCHEMA alone so a store upgraded from an older release gets it too -
    # the same standard every other new table is held to.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS evaluations ("
        "id TEXT PRIMARY KEY, "
        "case_id TEXT NOT NULL, "
        "dataset_id TEXT NOT NULL, "
        "run_id TEXT, "
        "artifact_kind TEXT NOT NULL, "
        "code TEXT NOT NULL, "
        "claim TEXT NOT NULL, "
        "findings_json TEXT NOT NULL, "
        "source TEXT NOT NULL, "
        "created_at TEXT NOT NULL, "
        "FOREIGN KEY (case_id) REFERENCES cases(id), "
        "FOREIGN KEY (dataset_id) REFERENCES datasets(id), "
        "FOREIGN KEY (run_id) REFERENCES runs(id))"
    )



def _m_profiles_quality_json(conn: sqlite3.Connection) -> None:
    # A profile states what the data cannot support (P8-QUALITY-002): the
    # seven defect classes, each with an impact sentence. JSON in one column,
    # like every other list the store holds, because the issues are read whole
    # and never queried individually.
    _ensure_column(
        conn, "profiles", "quality_json", "TEXT NOT NULL DEFAULT '[]'"
    )


def _m_contexts_table(conn: sqlite3.Connection) -> None:
    # A case carries the analyst's intent, not just a question string
    # (P8-CONTEXT-001): purpose, sub-questions, hypotheses, known constraints.
    # One row per case, so the primary key is the case rather than a surrogate -
    # a context without a case is meaningless, and a second write is an edit.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS contexts ("
        "case_id TEXT PRIMARY KEY, "
        "purpose TEXT NOT NULL DEFAULT '', "
        "sub_questions_json TEXT NOT NULL DEFAULT '[]', "
        "hypotheses_json TEXT NOT NULL DEFAULT '[]', "
        "constraints_json TEXT NOT NULL DEFAULT '[]', "
        "updated_at TEXT NOT NULL, "
        "FOREIGN KEY (case_id) REFERENCES cases(id))"
    )


def _m_refinements_table(conn: sqlite3.Connection) -> None:
    # A proposed sharpening of the case's question and what the analyst did
    # with it (P8-REFINE-007, AT-04). The original is carried on the row, so it
    # survives an accept that replaced it on the case: recoverability is a
    # property of the store, not of the client that happened to be looking.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS refinements ("
        "id TEXT PRIMARY KEY, "
        "case_id TEXT NOT NULL, "
        "original_question TEXT NOT NULL, "
        "refined_question TEXT NOT NULL DEFAULT '', "
        "rationale TEXT NOT NULL DEFAULT '', "
        "grounds_json TEXT NOT NULL DEFAULT '[]', "
        "source TEXT NOT NULL, "
        "status TEXT NOT NULL DEFAULT 'pending', "
        "edited_question TEXT, "
        "created_at TEXT NOT NULL, "
        "decided_at TEXT, "
        "FOREIGN KEY (case_id) REFERENCES cases(id))"
    )


def _m_decisions_table(conn: sqlite3.Connection) -> None:
    # The loop's exit keeps what it concluded (P8-DECISION-008, UX 46). Two
    # tables, because two different things are being kept. `validations` stores
    # the verdict validation computed - all nine checks, not only the status
    # that used to be all that survived - so a decision can be read without
    # re-running a single query, and a reopened case still shows what
    # validation found. `decisions` stores the implications the analyst wrote,
    # which are the only thing in the view a human authors.
    conn.execute(
        "CREATE TABLE IF NOT EXISTS validations ("
        "finding_id TEXT PRIMARY KEY, "
        "case_id TEXT NOT NULL, "
        "run_id TEXT NOT NULL, "
        "status TEXT NOT NULL, "
        "checks_json TEXT NOT NULL, "
        "validated_at TEXT NOT NULL, "
        "FOREIGN KEY (case_id) REFERENCES cases(id), "
        "FOREIGN KEY (finding_id) REFERENCES findings(id))"
    )
    conn.execute(
        "CREATE TABLE IF NOT EXISTS decisions ("
        "case_id TEXT PRIMARY KEY, "
        "implications_json TEXT NOT NULL DEFAULT '[]', "
        "updated_at TEXT NOT NULL, "
        "FOREIGN KEY (case_id) REFERENCES cases(id))"
    )


def _m_agent_steps_role(conn: sqlite3.Connection) -> None:
    # Multi-agent workflows: a step belongs to a role (P7-AGENT-001). Every
    # step recorded before the column existed is the analyst role - the one
    # driver the store had - so the default is the meaning those rows already
    # had rather than a new one invented by an upgrade.
    _ensure_column(conn, "agent_steps", "role", "TEXT NOT NULL DEFAULT 'analyst'")

# The history of the store, oldest first. Each entry corresponds to a change
# that once shipped as an ad-hoc `_ensure_column` call; the chain is the same
# set of changes, now named, ordered and recorded. Append here - never edit an
# entry, never renumber - when a future task changes the shape.
MIGRATIONS: tuple[Migration, ...] = (
    Migration(1, "datasets gain a format column", _m_datasets_format),
    Migration(2, "profiles gain a duplicate-row count", _m_profiles_duplicate_rows),
    Migration(3, "runs gain a kind (sql or python)", _m_runs_kind),
    Migration(4, "runs gain the python code they executed", _m_runs_code),
    Migration(5, "runs gain the full dataset list of a join", _m_runs_dataset_ids_json),
    Migration(6, "templates gain the analytical shape they carry", _m_templates_shape_json),
    Migration(7, "cases gain the template they came from", _m_cases_template_id),
    Migration(8, "evaluations: EVALUATE mode stores its audits", _m_evaluations_table),
    Migration(9, "agent_steps gain the role they belong to", _m_agent_steps_role),
    Migration(10, "contexts: a case carries purpose, sub-questions, hypotheses", _m_contexts_table),
    Migration(11, "profiles gain the quality issues they detected", _m_profiles_quality_json),
    Migration(12, "refinements: a proposed question sharpening and its decision", _m_refinements_table),
    Migration(13, "decisions: the verdicts validation computed and the implications the analyst wrote", _m_decisions_table),
    Migration(14, "cases gain the case they repeat", _m_cases_duplicate_of),
)


class SchemaVersionError(RuntimeError):
    """The store's schema is newer than this build understands."""


def _recorded_version(conn: sqlite3.Connection) -> int:
    """The version stamped into the store's header, 0 for a pre-migration one.

    `user_version` lives in the file header rather than a table, so it is
    readable before the schema exists and survives a crash that leaves the
    tables half-made.
    """
    return int(conn.execute("PRAGMA user_version").fetchone()[0])


def _store_is_fresh(conn: sqlite3.Connection) -> bool:
    """No table has ever been created in this file.

    A store that predates the migration chain has tables but no recorded
    version; a store created now has neither. The distinction decides whether
    the historical migrations are replayed or simply stamped as already-had.
    """
    row = conn.execute(
        "SELECT COUNT(*) AS n FROM sqlite_master "
        "WHERE type = 'table' AND name NOT LIKE 'sqlite_%'"
    ).fetchone()
    return int(row["n"]) == 0


def _migrate(conn: sqlite3.Connection, fresh: bool) -> int:
    """Bring the store to the current shape, and return the version reached.

    `fresh` means the file had no table in it at all before this connection
    created them, and is decided by the caller - before SCHEMA runs, since
    SCHEMA itself creates the migration table and would make a newborn store
    look old.

    Idempotent: a store already at the current version runs no migration and
    writes nothing but the pragma read. A store below it applies each pending
    migration in its own transaction, stamping the version after each, so a
    failure mid-chain leaves a consistent store at the last good version and
    the next open resumes from there.
    """
    current = _recorded_version(conn)
    if current > LATEST_SCHEMA_VERSION:
        raise SchemaVersionError(
            f"the case store is at schema version {current}, but this build "
            f"only understands up to {LATEST_SCHEMA_VERSION}. A newer DAH "
            "wrote this store; use that version or later rather than letting "
            "this one guess at a schema it does not know."
        )
    if current == LATEST_SCHEMA_VERSION:
        return current

    if fresh:
        # The schema created the store whole at the current shape, so there is
        # nothing to replay. The migration table stays empty, which is the
        # truth: nothing was applied, the store was born current.
        conn.execute(f"PRAGMA user_version = {LATEST_SCHEMA_VERSION}")
        return LATEST_SCHEMA_VERSION

    for migration in MIGRATIONS:
        if migration.version <= current:
            continue
        now = datetime.now(timezone.utc).isoformat()
        # One transaction per migration: the change, its audit row and its
        # version stamp land together, or none of them do.
        with conn:  # commits on exit, rolls back on any exception
            migration.apply(conn)
            conn.execute(
                "INSERT INTO schema_migrations (version, name, applied_at) "
                "VALUES (?, ?, ?)",
                (migration.version, migration.name, now),
            )
            conn.execute(f"PRAGMA user_version = {migration.version}")
    return LATEST_SCHEMA_VERSION


@contextmanager
def get_connection(db_path: Path = DB_PATH) -> Iterator[sqlite3.Connection]:
    """Open a connection, ensuring the schema exists and is current.

    FastAPI runs sync endpoints in a threadpool, so connections must be usable
    across threads. Each request gets its own connection and commits before
    closing, so sharing one connection across threads is safe here.
    """
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    try:
        # The schema creates the tables at the current shape; the migration
        # chain then brings a store written by any older release up to it. The
        # two agree by construction: every column SCHEMA declares is either
        # created by it or added by a migration below, and nothing else.
        # Emptiness is decided before SCHEMA creates anything, otherwise a
        # newborn store would look like an old one that needs the chain.
        fresh = _store_is_fresh(conn)
        conn.executescript(SCHEMA)
        _migrate(conn, fresh)
        yield conn
        conn.commit()
    finally:
        conn.close()
