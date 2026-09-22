"""Data-quality detection beyond missingness (P8-QUALITY-002, AT-08/AT-09).

The PRD names seven defect classes and requires each detected issue to carry an
analytical impact. These tests pin all seven against fixtures written to carry
exactly one defect each, plus the false-positive guard: a clean dataset raises
nothing, which is how the <= 5% budget in AT-08 is held before the golden
suite that measures it (P8-GOLDEN-005) exists.
"""

from app.quality import (
    ALL_CLASSES,
    CLASS_DATE_GAPS,
    CLASS_DUPLICATE_ROWS,
    CLASS_EXTREME_VALUES,
    CLASS_INCONSISTENT_CATEGORIES,
    CLASS_INSUFFICIENT_COVERAGE,
    CLASS_INVALID_TYPES,
    CLASS_MISSING_VALUES,
    QualityIssue,
    assess_quality,
)
from app.db import get_connection



def _issues(issues: list[dict], kind: str) -> list[dict]:
    return [issue for issue in issues if issue["kind"] == kind]


def test_every_prd_class_has_a_detector() -> None:
    """The seven classes AT-08 names are exactly the detectors shipped."""
    assert len(ALL_CLASSES) == 7
    assert set(ALL_CLASSES) == {
        CLASS_MISSING_VALUES,
        CLASS_DUPLICATE_ROWS,
        CLASS_INVALID_TYPES,
        CLASS_INCONSISTENT_CATEGORIES,
        CLASS_DATE_GAPS,
        CLASS_EXTREME_VALUES,
        CLASS_INSUFFICIENT_COVERAGE,
    }


def test_an_issue_carries_an_observation_and_an_impact() -> None:
    """AT-09: the consequence sentence is always present, never empty."""
    issue = QualityIssue(
        CLASS_MISSING_VALUES,
        "1 of 4 values are missing.",
        "revenue contains 25.0% missing values; totals may be understated.",
        column="revenue",
    )
    as_dict = issue.to_dict()
    assert as_dict["observed"]
    assert as_dict["impact"]
    assert as_dict["kind"] == CLASS_MISSING_VALUES
    assert as_dict["column"] == "revenue"
    # Two issues describing the same thing compare equal - the detectors build
    # plain data, so tests compare data rather than identity.
    assert issue == QualityIssue(
        CLASS_MISSING_VALUES,
        "1 of 4 values are missing.",
        "revenue contains 25.0% missing values; totals may be understated.",
        column="revenue",
    )


# --- the two pre-existing classes, now with impact sentences ------------------


def test_missing_values_reports_the_impact_on_aggregates() -> None:
    issues = assess_quality(
        stats={
            "revenue": {"type": "numeric", "null_count": 3, "distinct_count": 2},
            "region": {"type": "other", "null_count": 1, "distinct_count": 2},
        },
        total_rows=20,
        duplicate_rows=0,
    )
    missing = _issues(issues, CLASS_MISSING_VALUES)
    assert len(missing) == 2
    revenue = next(i for i in missing if i["column"] == "revenue")
    # A measure column's nulls understate aggregates; a dimension's exclude rows.
    assert "understated" in revenue["impact"]
    assert "15.0%" in revenue["impact"]
    assert revenue["severity"] == "medium"
    region = next(i for i in missing if i["column"] == "region")
    assert "silently excluded" in region["impact"]
    # A column that is mostly absent is the severe case.
    severe = assess_quality(
        stats={"revenue": {"type": "numeric", "null_count": 8, "distinct_count": 2}},
        total_rows=20,
        duplicate_rows=0,
    )
    assert _issues(severe, CLASS_MISSING_VALUES)[0]["severity"] == "high"


def test_duplicate_rows_report_the_inflated_denominator() -> None:
    issues = assess_quality(
        stats={}, total_rows=20, duplicate_rows=4, samples={}
    )
    duplicates = _issues(issues, CLASS_DUPLICATE_ROWS)
    assert len(duplicates) == 1
    assert "20.0%" in duplicates[0]["impact"]
    assert "inflated" in duplicates[0]["impact"]


def test_a_clean_dataset_raises_nothing() -> None:
    """The false-positive guard: no nulls, no duplicates, no extremes, no
    spelling collisions and enough rows yields no issues at all."""
    issues = assess_quality(
        stats={
            "id": {"type": "numeric", "null_count": 0, "distinct_count": 100},
            "region": {
                "type": "other",
                "null_count": 0,
                "distinct_count": 5,
            },
            "revenue": {"type": "numeric", "null_count": 0, "distinct_count": 90},
        },
        total_rows=100,
        duplicate_rows=0,
        samples={
            "castability": {"region": (100, 0, 0)},
            "value_counts": {
                "region": {"north": 20, "south": 20, "east": 20, "west": 20, "central": 20}
            },
            "extremes": {
                "id": {"top": [100.0, 99.0, 98.0], "bottom": [1.0, 2.0, 3.0]},
                "revenue": {
                    "top": [125.0, 120.0, 115.0],
                    "bottom": [5.0, 7.5, 10.0],
                },
            },
        },
    )
    assert issues == []


# --- the five new classes -----------------------------------------------------


def test_invalid_types_flags_a_mostly_numeric_column_with_some_junk() -> None:
    """A VARCHAR column that is mostly numbers but holds a few non-numbers is
    the defect that breaks a calculation silently."""
    issues = assess_quality(
        stats={"revenue": {"type": "other", "null_count": 0, "distinct_count": 3}},
        total_rows=10,
        duplicate_rows=0,
        samples={"castability": {"revenue": (10, 8, 0)}},
    )
    typed = _issues(issues, CLASS_INVALID_TYPES)
    assert len(typed) == 1
    assert typed[0]["severity"] == "high"
    assert "misread" in typed[0]["impact"]


def test_invalid_types_leaves_a_column_of_names_alone() -> None:
    """A column that casts to neither type is text, not a mixed-type defect."""
    issues = assess_quality(
        stats={"region": {"type": "other", "null_count": 0, "distinct_count": 3}},
        total_rows=10,
        duplicate_rows=0,
        samples={"castability": {"region": (10, 0, 0)}},
    )
    assert _issues(issues, CLASS_INVALID_TYPES) == []


def test_invalid_types_leaves_a_wholly_castable_column_alone() -> None:
    """A column that is 100% numeric under a VARCHAR type was typed `other` for
    another reason (a recovered read); it is not a defect."""
    issues = assess_quality(
        stats={"revenue": {"type": "other", "null_count": 0, "distinct_count": 3}},
        total_rows=10,
        duplicate_rows=0,
        samples={"castability": {"revenue": (10, 10, 0)}},
    )
    assert _issues(issues, CLASS_INVALID_TYPES) == []


def test_inconsistent_categories_flags_case_variants() -> None:
    """'north' and 'North' are one category to an analyst and two to a GROUP
    BY."""
    issues = assess_quality(
        stats={"region": {"type": "other", "null_count": 0, "distinct_count": 3}},
        total_rows=10,
        duplicate_rows=0,
        samples={
            "value_counts": {"region": {"north": 4, "North": 3, "east": 3}},
        },
    )
    inconsistent = _issues(issues, CLASS_INCONSISTENT_CATEGORIES)
    assert len(inconsistent) == 1
    assert inconsistent[0]["column"] == "region"
    assert "splits one category" in inconsistent[0]["impact"]


def test_inconsistent_categories_leaves_consistent_values_alone() -> None:
    issues = assess_quality(
        stats={"region": {"type": "other", "null_count": 0, "distinct_count": 2}},
        total_rows=10,
        duplicate_rows=0,
        samples={"value_counts": {"region": {"north": 5, "south": 5}}},
    )
    assert _issues(issues, CLASS_INCONSISTENT_CATEGORIES) == []


def test_inconsistent_categories_ignores_free_text() -> None:
    """A high-cardinality column has no consistent spelling to violate."""
    issues = assess_quality(
        stats={"name": {"type": "other", "null_count": 0, "distinct_count": 500}},
        total_rows=500,
        duplicate_rows=0,
        samples={"value_counts": {}},
    )
    assert _issues(issues, CLASS_INCONSISTENT_CATEGORIES) == []


def test_date_gaps_flags_a_hole_in_a_regular_series() -> None:
    """A daily series missing a day compares non-adjacent windows as adjacent."""
    import datetime as dt

    issues = assess_quality(
        stats={"day": {"type": "temporal", "null_count": 0, "distinct_count": 4}},
        total_rows=5,
        duplicate_rows=0,
        samples={
            "distinct_values": {
                "day": [
                    dt.date(2024, 1, 1),
                    dt.date(2024, 1, 2),
                    dt.date(2024, 1, 5),
                    dt.date(2024, 1, 6),
                ]
            }
        },
    )
    gaps = _issues(issues, CLASS_DATE_GAPS)
    assert len(gaps) == 1
    assert "non-adjacent" in gaps[0]["impact"]


def test_date_gaps_leaves_a_contiguous_series_alone() -> None:
    import datetime as dt

    issues = assess_quality(
        stats={"day": {"type": "temporal", "null_count": 0, "distinct_count": 4}},
        total_rows=4,
        duplicate_rows=0,
        samples={
            "distinct_values": {
                "day": [
                    dt.date(2024, 1, 1),
                    dt.date(2024, 1, 2),
                    dt.date(2024, 1, 3),
                    dt.date(2024, 1, 4),
                ]
            }
        },
    )
    assert _issues(issues, CLASS_DATE_GAPS) == []


def test_extreme_values_flags_a_value_dwarfing_its_neighbour() -> None:
    issues = assess_quality(
        stats={"revenue": {"type": "numeric", "null_count": 0, "distinct_count": 4}},
        total_rows=4,
        duplicate_rows=0,
        samples={
            "extremes": {
                "revenue": {"top": [10000.0, 10.0, 9.0], "bottom": [8.0, 9.0, 10.0]}
            }
        },
    )
    extremes = _issues(issues, CLASS_EXTREME_VALUES)
    assert len(extremes) == 1
    assert "median" in extremes[0]["impact"]


def test_extreme_values_ignores_a_run_of_ties_at_the_top() -> None:
    """Repeated maxima are a tied value, not an extreme one."""
    issues = assess_quality(
        stats={"revenue": {"type": "numeric", "null_count": 0, "distinct_count": 2}},
        total_rows=6,
        duplicate_rows=0,
        samples={
            "extremes": {"revenue": {"top": [50.0, 50.0, 50.0], "bottom": [1.0, 2.0]}}
        },
    )
    assert _issues(issues, CLASS_EXTREME_VALUES) == []


def test_extreme_values_ignores_an_ordinary_range() -> None:
    issues = assess_quality(
        stats={"revenue": {"type": "numeric", "null_count": 0, "distinct_count": 5}},
        total_rows=5,
        duplicate_rows=0,
        samples={
            "extremes": {
                "revenue": {"top": [120.0, 110.0, 100.0], "bottom": [10.0, 20.0, 30.0]}
            }
        },
    )
    assert _issues(issues, CLASS_EXTREME_VALUES) == []


def test_insufficient_coverage_flags_a_tiny_dataset() -> None:
    issues = assess_quality(stats={}, total_rows=2, duplicate_rows=0, samples={})
    coverage = _issues(issues, CLASS_INSUFFICIENT_COVERAGE)
    assert len(coverage) == 1
    assert "provisional" in coverage[0]["impact"]


def test_insufficient_coverage_flags_a_dominated_category() -> None:
    """A group-by over a column that is 95% one value is about that value."""
    issues = assess_quality(
        stats={"region": {"type": "other", "null_count": 0, "distinct_count": 3}},
        total_rows=100,
        duplicate_rows=0,
        samples={"value_counts": {"region": {"north": 95, "south": 3, "east": 2}}},
    )
    coverage = _issues(issues, CLASS_INSUFFICIENT_COVERAGE)
    assert len(coverage) == 1
    assert coverage[0]["column"] == "region"
    assert "too small to compare" in coverage[0]["impact"]


def test_insufficient_coverage_leaves_a_balanced_category_alone() -> None:
    issues = assess_quality(
        stats={"region": {"type": "other", "null_count": 0, "distinct_count": 2}},
        total_rows=100,
        duplicate_rows=0,
        samples={"value_counts": {"region": {"north": 55, "south": 45}}},
    )
    assert _issues(issues, CLASS_INSUFFICIENT_COVERAGE) == []


def test_issues_are_ordered_worst_first() -> None:
    """The first thing an analyst reads is the issue most likely to invalidate
    the answer they are about to compute."""
    issues = assess_quality(
        stats={
            "region": {"type": "other", "null_count": 0, "distinct_count": 2},
            "revenue": {"type": "numeric", "null_count": 8, "distinct_count": 2},
        },
        total_rows=10,
        duplicate_rows=1,
        samples={"value_counts": {"region": {"north": 9, "south": 1}}},
    )
    severities = [issue["severity"] for issue in issues]
    assert severities == sorted(severities)
    # Every issue carries both sentences, whatever its place in the order.
    assert all(issue["observed"] and issue["impact"] for issue in issues)


# --- persistence and the schema migration ------------------------------------


def _csv(tmp_path, text: str) -> str:
    path = tmp_path / "quality.csv"
    path.write_text(text, encoding="utf-8")
    return str(path)


def _restored_dataset(client, case_id: str) -> str:
    return client.get(f"/cases/{case_id}/datasets").json()[0]["id"]


def _override_get_db(db_path):
    """The dependency shape the app expects: a connection per request."""
    def override():
        with get_connection(db_path) as connection:
            yield connection

    return override


CLEAN_CSV = (
    "order_id,region,revenue\n"
    "101,north,4200\n"
    "102,south,3100\n"
    "103,east,5000\n"
    "104,west,1200\n"
    "105,north,3300\n"
    "106,south,4100\n"
    "107,east,2200\n"
    "108,west,6100\n"
)

MESSY_CSV = (
    "order_id,region,revenue\n"
    "101,north,4200\n"
    "102,North,3100\n"
    "103,west,\n"
    "104,west,8100\n"
    "105,east,2900\n"
    "106,north,5100\n"
    "107,west,8100\n"
    "108,west,999999\n"
)


def test_profile_csv_detects_every_class_in_one_pass(tmp_path) -> None:
    """A single profiling pass over a deliberately messy file raises the
    classes the fixture plants: a null, a spelling collision and an extreme."""
    from app.analysis import profile_csv

    result = profile_csv(_csv(tmp_path, MESSY_CSV))
    kinds = {issue["kind"] for issue in result["quality"]}
    assert CLASS_MISSING_VALUES in kinds
    assert CLASS_INCONSISTENT_CATEGORIES in kinds
    assert CLASS_EXTREME_VALUES in kinds
    # Every issue carries both sentences, straight out of the profiler.
    assert all(i["observed"] and i["impact"] for i in result["quality"])


def test_profile_csv_finds_no_issues_in_clean_data(tmp_path) -> None:
    """The false-positive guard, end to end through the real profiler."""
    from app.analysis import profile_csv

    result = profile_csv(_csv(tmp_path, CLEAN_CSV))
    assert result["quality"] == []


def test_the_quality_list_persists_across_reopen(tmp_path) -> None:
    """AT-08's threshold is about a dataset the analyst comes back to: the
    warnings must still be there without reprofiling."""
    import json

    from fastapi.testclient import TestClient

    from app.db import get_connection
    import app.db as db_module
    from app.main import app, get_db

    db_module.DATA_DIR = tmp_path / "data"
    db_module.DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "test.db"
    app.dependency_overrides[get_db] = _override_get_db(db_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "quality.csv"}
        ).json()["id"]
        with open(_csv(tmp_path, MESSY_CSV), "rb") as handle:
            dataset_id = client.post(
                f"/cases/{case_id}/datasets",
                files={"file": ("quality.csv", handle, "text/csv")},
            ).json()["id"]
        created = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/profile"
        ).json()["quality"]
        assert created
        # A reopen reads the stored list, and it is the same list.
        reopened = client.get(
            f"/cases/{case_id}/datasets/{dataset_id}/profile"
        ).json()["quality"]
        assert reopened == created
        # The store holds it as JSON, not as a recompute, so a closed case's
        # warnings survive a session boundary.
        with get_connection(db_path) as connection:
            stored = connection.execute(
                "SELECT quality_json FROM profiles WHERE dataset_id = ?",
                (dataset_id,),
            ).fetchone()
        assert json.loads(stored[0]) == created


def test_validation_reads_the_impact_sentence(tmp_path) -> None:
    """The audit and the Data stage must not say two different things about
    the same null (AT-09)."""
    from fastapi.testclient import TestClient

    from app.db import get_connection
    import app.db as db_module
    from app.main import app, get_db

    db_module.DATA_DIR = tmp_path / "data"
    db_module.DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "test.db"
    app.dependency_overrides[get_db] = _override_get_db(db_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "quality.csv"}
        ).json()["id"]
        with open(_csv(tmp_path, MESSY_CSV), "rb") as handle:
            dataset_id = client.post(
                f"/cases/{case_id}/datasets",
                files={"file": ("quality.csv", handle, "text/csv")},
            ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        code = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/generate-code",
            json={"question": "q", "kind": "sql"},
        ).json()["code"]
        run_id = client.post(
            f"/cases/{case_id}/datasets/{dataset_id}/runs", json={"sql": code}
        ).json()["id"]
        draft = client.post(
            f"/cases/{case_id}/runs/{run_id}/draft-finding"
        ).json()
        finding_id = client.post(
            f"/cases/{case_id}/findings", json=draft
        ).json()["id"]
        validation = client.post(
            f"/cases/{case_id}/findings/{finding_id}/validate"
        ).json()
        # The finding's support is still judged on the numbers; only the
        # sentence changed.
        assert validation["status"] == "partially_supported"
        checks = {c["name"]: c for c in validation["checks"]}
        assert checks["calculation"]["passed"] is True
        assert "understated" in checks["data"]["detail"]


def test_the_quality_list_travels_with_an_export(tmp_path) -> None:
    """A restored case carries the warnings the profile found, so an audit's
    data quality survives a package the way its findings do."""
    import json

    from fastapi.testclient import TestClient

    import app.db as db_module
    from app.main import app, get_db

    db_module.DATA_DIR = tmp_path / "data"
    db_module.DATA_DIR.mkdir(parents=True, exist_ok=True)
    db_path = tmp_path / "test.db"
    app.dependency_overrides[get_db] = _override_get_db(db_path)

    with TestClient(app) as client:
        case_id = client.post(
            "/cases", json={"question": "q", "dataset": "quality.csv"}
        ).json()["id"]
        with open(_csv(tmp_path, MESSY_CSV), "rb") as handle:
            dataset_id = client.post(
                f"/cases/{case_id}/datasets",
                files={"file": ("quality.csv", handle, "text/csv")},
            ).json()["id"]
        client.post(f"/cases/{case_id}/datasets/{dataset_id}/profile")
        package = client.get(f"/cases/{case_id}/export").json()
        # The package carries the issues, and they are the ones detected.
        assert package["profiles"][0]["quality"]
        kinds = {i["kind"] for i in package["profiles"][0]["quality"]}
        assert CLASS_MISSING_VALUES in kinds

        restored = client.post("/cases/import", json=package).json()["id"]
        reopened = client.get(
            f"/cases/{restored}/datasets/{_restored_dataset(client, restored)}/profile"
        ).json()["quality"]
        assert {i["kind"] for i in reopened} == kinds


def test_a_v10_store_upgrades_to_v11_and_keeps_its_rows(tmp_path) -> None:
    """A store written by a P8-CONTEXT-001 build opens, upgrades to v11 and
    keeps the profile it already held - an absent quality list reads as empty,
    never as an error."""
    import sqlite3

    import app.db as db_module
    from app.db import get_connection

    store = tmp_path / "v10.db"
    conn = sqlite3.connect(store)
    conn.executescript(
        # The profiles table as a v10 build left it: no quality_json column.
        "CREATE TABLE cases (id TEXT PRIMARY KEY, question TEXT NOT NULL, "
        "dataset TEXT NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL);"
        "CREATE TABLE datasets (id TEXT PRIMARY KEY, case_id TEXT NOT NULL, "
        "filename TEXT NOT NULL, stored_path TEXT NOT NULL, format TEXT NOT NULL, "
        "created_at TEXT NOT NULL);"
        "CREATE TABLE profiles (dataset_id TEXT PRIMARY KEY, rows INTEGER NOT NULL, "
        "columns_json TEXT NOT NULL, stats_json TEXT NOT NULL, "
        "duplicate_rows INTEGER NOT NULL DEFAULT 0, profiled_at TEXT NOT NULL);"
        "CREATE TABLE schema_migrations (version INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "applied_at TEXT NOT NULL);"
        "INSERT INTO cases VALUES ('c1', 'why?', 'd.csv', '2026-01-01', '2026-01-01');"
        "INSERT INTO datasets VALUES ('ds-1', 'c1', 'd.csv', 'p', 'csv', '2026-01-01');"
        "INSERT INTO profiles VALUES ('ds-1', 3, '[\"region\"]', "
        "'{\"region\": {\"null_count\": 0}}', 0, '2026-01-01');"
        "INSERT INTO schema_migrations VALUES (10, 'contexts', '2026-01-01');"
    )
    conn.execute("PRAGMA user_version = 10")
    conn.commit()
    conn.close()

    db_module.DATA_DIR = tmp_path / "data"
    with get_connection(store) as upgraded:
        version = upgraded.execute("PRAGMA user_version").fetchone()[0]
        # The migration is idempotent, so re-running it on an open store is the
        # no-op a resumed upgrade depends on.
        from app.db import _m_profiles_quality_json

        _m_profiles_quality_json(upgraded)
        profile = upgraded.execute(
            "SELECT rows, duplicate_rows, quality_json FROM profiles "
            "WHERE dataset_id = ?",
            ("ds-1",),
        ).fetchone()
        kept = upgraded.execute("SELECT question FROM cases").fetchone()
        applied = upgraded.execute(
            "SELECT version, name FROM schema_migrations WHERE version = 11"
        ).fetchone()

    assert version == 11
    # The row the store already held is intact, and the new column reads as
    # empty rather than missing.
    assert profile[0] == 3
    assert profile[2] == "[]"
    assert kept[0] == "why?"
    # The change is recorded in the audit trail the schema keeps.
    assert applied is not None
    assert applied[1]
