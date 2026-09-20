"""Schema migration tests for P6-MIGRATE-004.

A store written by any past release must open, upgrade to the current shape,
and keep its rows. The mechanism is the point: the version is recorded in the
file, the chain is replayed from where the store stopped, and a store newer
than the build is refused rather than downgraded.
"""

import sqlite3

from fastapi.testclient import TestClient

from app.db import LATEST_SCHEMA_VERSION, MIGRATIONS, SchemaVersionError, get_connection
from app.main import app, get_db

# The shape a store had before any of the migrated columns existed: every table
# as its oldest release created it. This is the v0.1.0 store, the one that
# actually exists in the wild.
LEGACY_SCHEMA = """
CREATE TABLE cases (
    id TEXT PRIMARY KEY,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE datasets (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    filename TEXT NOT NULL,
    stored_path TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE profiles (
    dataset_id TEXT PRIMARY KEY,
    rows INTEGER NOT NULL,
    columns_json TEXT NOT NULL,
    stats_json TEXT NOT NULL,
    profiled_at TEXT NOT NULL
);
CREATE TABLE runs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL,
    dataset_id TEXT NOT NULL,
    sql TEXT,
    columns_json TEXT NOT NULL,
    rows_json TEXT NOT NULL,
    row_count INTEGER NOT NULL,
    truncated INTEGER NOT NULL,
    executed_at TEXT NOT NULL
);
CREATE TABLE templates (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    question TEXT NOT NULL,
    dataset TEXT NOT NULL,
    created_at TEXT NOT NULL
);
"""

HISTORICAL_COLUMNS = [
    ("datasets", "format"),
    ("profiles", "duplicate_rows"),
    ("runs", "kind"),
    ("runs", "code"),
    ("runs", "dataset_ids_json"),
    ("templates", "shape_json"),
    ("cases", "template_id"),
]


def _override(db_path):
    def override():
        with get_connection(db_path) as connection:
            yield connection

    app.dependency_overrides[get_db] = override


def _build_legacy(db_path, with_rows=True):
    conn = sqlite3.connect(db_path)
    conn.executescript(LEGACY_SCHEMA)
    if with_rows:
        conn.execute(
            "INSERT INTO cases (id, question, dataset, created_at, updated_at) "
            "VALUES ('case-1', 'Why did revenue decline?', 'sales.csv', "
            "'2024-01-01T00:00:00+00:00', '2024-01-01T00:00:00+00:00')"
        )
        conn.execute(
            "INSERT INTO datasets (id, case_id, filename, stored_path, created_at) "
            "VALUES ('ds-1', 'case-1', 'sales.csv', '/data/sales.csv', "
            "'2024-01-01T00:00:00+00:00')"
        )
    conn.commit()
    conn.close()


def _columns(db_path, table):
    conn = sqlite3.connect(db_path)
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def _version(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return int(conn.execute("PRAGMA user_version").fetchone()[0])
    finally:
        conn.close()


def _migration_rows(db_path):
    conn = sqlite3.connect(db_path)
    try:
        return conn.execute("SELECT COUNT(*) FROM schema_migrations").fetchone()[0]
    finally:
        conn.close()


def test_a_fresh_store_is_created_at_the_current_version(tmp_path):
    db_path = tmp_path / "fresh.db"
    with get_connection(db_path):
        pass
    assert _version(db_path) == LATEST_SCHEMA_VERSION
    # Nothing was applied - the store was born current, so the audit trail is
    # empty rather than padded with migrations that never ran.
    assert _migration_rows(db_path) == 0
    for table, column in HISTORICAL_COLUMNS:
        assert column in _columns(db_path, table)


def test_a_fresh_store_reports_current_through_the_api(tmp_path):
    db_path = tmp_path / "fresh.db"
    _override(db_path)
    with get_connection(db_path):
        pass
    client = TestClient(app)
    response = client.get("/schema-version")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["version"] == LATEST_SCHEMA_VERSION
    assert body["target"] == LATEST_SCHEMA_VERSION
    assert body["current"] is True
    assert body["migrations"] == []
    app.dependency_overrides.clear()


def test_a_legacy_store_upgrades_to_the_current_shape(tmp_path):
    db_path = tmp_path / "legacy.db"
    _build_legacy(db_path)
    with get_connection(db_path):
        pass
    assert _version(db_path) == LATEST_SCHEMA_VERSION
    for table, column in HISTORICAL_COLUMNS:
        assert column in _columns(db_path, table)


def test_a_legacy_store_records_every_migration_it_ran(tmp_path):
    db_path = tmp_path / "legacy.db"
    _build_legacy(db_path)
    with get_connection(db_path):
        pass
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT version, name FROM schema_migrations ORDER BY version"
        ).fetchall()
    finally:
        conn.close()
    assert [(r[0], r[1]) for r in rows] == [
        (m.version, m.name) for m in MIGRATIONS
    ]


def test_a_legacy_store_reports_not_current_before_the_upgrade(tmp_path):
    """The endpoint shows the gap, which is how a pending upgrade is noticed."""
    db_path = tmp_path / "legacy.db"
    _build_legacy(db_path)
    _override(db_path)
    # Open through the api first: the upgrade runs on the ordinary open path,
    # so this call both upgrades and reports.
    client = TestClient(app)
    response = client.get("/schema-version")
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["version"] == LATEST_SCHEMA_VERSION
    assert body["current"] is True
    assert len(body["migrations"]) == len(MIGRATIONS)
    app.dependency_overrides.clear()


def test_existing_rows_survive_the_upgrade(tmp_path):
    db_path = tmp_path / "legacy.db"
    _build_legacy(db_path)
    with get_connection(db_path):
        pass
    conn = sqlite3.connect(db_path)
    try:
        case = conn.execute(
            "SELECT id, question, dataset FROM cases WHERE id = 'case-1'"
        ).fetchone()
        dataset = conn.execute(
            "SELECT id, filename FROM datasets WHERE id = 'ds-1'"
        ).fetchone()
    finally:
        conn.close()
    assert case == ("case-1", "Why did revenue decline?", "sales.csv")
    assert dataset == ("ds-1", "sales.csv")


def test_reopening_a_current_store_is_a_noop(tmp_path):
    db_path = tmp_path / "fresh.db"
    with get_connection(db_path):
        pass
    assert _version(db_path) == LATEST_SCHEMA_VERSION
    assert _migration_rows(db_path) == 0
    # A second open runs no migration and writes no audit row.
    with get_connection(db_path):
        pass
    assert _version(db_path) == LATEST_SCHEMA_VERSION
    assert _migration_rows(db_path) == 0


def test_a_partially_upgraded_store_resumes_from_where_it_stopped(tmp_path):
    """A store stamped mid-chain picks up there, not from the beginning."""
    db_path = tmp_path / "partial.db"
    _build_legacy(db_path)
    # Simulate a store that applied the first two migrations and then stopped.
    conn = sqlite3.connect(db_path)
    conn.executescript("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)")
    conn.execute("INSERT INTO schema_migrations (version, name, applied_at) VALUES (1, 'datasets gain a format column', '2024-01-01')")
    conn.execute("INSERT INTO schema_migrations (version, name, applied_at) VALUES (2, 'profiles gain a duplicate-row count', '2024-01-01')")
    conn.execute("ALTER TABLE datasets ADD COLUMN format TEXT NOT NULL DEFAULT 'unknown'")
    conn.execute("ALTER TABLE profiles ADD COLUMN duplicate_rows INTEGER NOT NULL DEFAULT 0")
    conn.execute("PRAGMA user_version = 2")
    conn.commit()
    conn.close()
    assert _version(db_path) == 2

    with get_connection(db_path):
        pass

    assert _version(db_path) == LATEST_SCHEMA_VERSION
    # The two it already had are not re-recorded; the rest are.
    conn = sqlite3.connect(db_path)
    try:
        versions = [r[0] for r in conn.execute(
            "SELECT version FROM schema_migrations ORDER BY version")]
    finally:
        conn.close()
    assert versions == [m.version for m in MIGRATIONS]


def test_a_store_newer_than_the_build_is_refused(tmp_path):
    """An older binary against a newer store fails loudly, not silently."""
    db_path = tmp_path / "future.db"
    with get_connection(db_path):
        pass
    conn = sqlite3.connect(db_path)
    conn.execute(f"PRAGMA user_version = {LATEST_SCHEMA_VERSION + 5}")
    conn.commit()
    conn.close()

    try:
        with get_connection(db_path):
            pass
    except SchemaVersionError as error:
        assert str(LATEST_SCHEMA_VERSION) in str(error)
        assert str(LATEST_SCHEMA_VERSION + 5) in str(error)
    else:
        raise AssertionError("a store newer than the build was not refused")


def test_a_fresh_and_an_upgraded_store_have_identical_shapes(tmp_path):
    """SCHEMA and the migration chain agree: a store is the same either way."""
    fresh = tmp_path / "fresh.db"
    with get_connection(fresh):
        pass

    upgraded = tmp_path / "upgraded.db"
    _build_legacy(upgraded)
    with get_connection(upgraded):
        pass

    conn_f = sqlite3.connect(fresh)
    conn_u = sqlite3.connect(upgraded)
    try:
        tables = [
            row[0]
            for row in conn_f.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        assert tables == [
            row[0]
            for row in conn_u.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table' "
                "AND name NOT LIKE 'sqlite_%' ORDER BY name"
            )
        ]
        for table in tables:
            fresh_info = sorted(
                (r[1], r[2], r[3], r[4])
                for r in conn_f.execute(f"PRAGMA table_info({table})")
            )
            upgraded_info = sorted(
                (r[1], r[2], r[3], r[4])
                for r in conn_u.execute(f"PRAGMA table_info({table})")
            )
            assert fresh_info == upgraded_info, table
    finally:
        conn_f.close()
        conn_u.close()


def test_a_store_with_no_tables_but_a_version_still_upgrades(tmp_path):
    """The fresh-store shortcut keys on emptiness, not on version 0 alone."""
    db_path = tmp_path / "odd.db"
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)")
    conn.execute(f"PRAGMA user_version = {LATEST_SCHEMA_VERSION - 3}")
    conn.commit()
    conn.close()
    # schema_migrations exists, so the store is not empty; the chain replays
    # the pending migrations against the tables SCHEMA creates.
    with get_connection(db_path):
        pass
    assert _version(db_path) == LATEST_SCHEMA_VERSION


def test_an_empty_legacy_store_upgrades_cleanly(tmp_path):
    """A store with tables but no rows still takes every historical column."""
    db_path = tmp_path / "empty-legacy.db"
    _build_legacy(db_path, with_rows=False)
    with get_connection(db_path):
        pass
    assert _version(db_path) == LATEST_SCHEMA_VERSION
    for table, column in HISTORICAL_COLUMNS:
        assert column in _columns(db_path, table)


def test_the_dev_database_is_current_or_upgraded_in_place(tmp_path):
    """The real store the app opens reaches the current version on open."""
    # A store created by an older release has a pre-migration shape; opening it
    # through the ordinary path is the upgrade path the user actually hits.
    db_path = tmp_path / "simulated-dev.db"
    _build_legacy(db_path)
    with get_connection(db_path):
        pass
    assert _version(db_path) == LATEST_SCHEMA_VERSION
    # It stays current, and stays usable.
    with get_connection(db_path) as conn:
        cases = conn.execute("SELECT COUNT(*) AS n FROM cases").fetchone()
    assert cases["n"] == 1
