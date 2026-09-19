"""Self-contained Analysis Case packages (P2-CASE-012).

Export assembles everything that makes a case meaningful - metadata, datasets
with their bytes, profiles, runs (SQL and Python), findings with validation
status, chart artifacts, and AI plans - into one JSON document that needs
neither the database nor the data directory to be understood.

Import is the proof that the package is self-contained: it reconstructs the
case with fresh IDs and remapped references, so a package restored elsewhere
stands on its own. Export and import are inverses to the extent the stored
state allows; row results are already capped at the point they were run, and
the cap is part of what is exported, so a restored case reports the same
truncation as the original.

Package layout (version 1):

    case           - question, dataset label, timestamps
    datasets       - metadata plus the raw bytes as data_base64
    profiles       - the deterministic profile per dataset
    runs           - kind, sql/code, columns, rows, truncation
    findings       - statement, interpretation, caveat, validation status
    charts         - rendering parameters plus the SVG itself
    plans          - the structured plan and which engine produced it

Original IDs are carried through so relationships inside the package stay
traceable (a finding points at its run, a chart at its run); import remaps
them to fresh IDs rather than reusing them.
"""

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

PACKAGE_FORMAT = "dah-case-package"
PACKAGE_VERSION = 1

# Guard against a package that is too large to handle in one request.
_MAX_PACKAGE_BYTES = 100 * 1024 * 1024


def _read_bytes(path: str) -> str:
    """File contents as base64, or an empty string if the file is gone."""
    try:
        return base64.b64encode(Path(path).read_bytes()).decode("ascii")
    except OSError:
        return ""


def export_case(db, case_id: str) -> dict | None:
    """Assemble a case into a self-contained package, or None if it is missing."""
    case_row = db.execute(
        "SELECT id, question, dataset, created_at, updated_at FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()
    if case_row is None:
        return None

    datasets = [
        {
            "id": row["id"],
            "filename": row["filename"],
            "format": row["format"],
            "created_at": row["created_at"],
            "data_base64": _read_bytes(row["stored_path"]),
        }
        for row in db.execute(
            "SELECT id, filename, stored_path, format, created_at FROM datasets "
            "WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]

    profiles = [
        {
            "dataset_id": row["dataset_id"],
            "rows": row["rows"],
            "columns": json.loads(row["columns_json"]),
            "stats": json.loads(row["stats_json"]),
            "duplicate_rows": row["duplicate_rows"],
            "profiled_at": row["profiled_at"],
        }
        for row in db.execute(
            "SELECT dataset_id, rows, columns_json, stats_json, duplicate_rows, "
            "profiled_at FROM profiles WHERE dataset_id IN "
            "(SELECT id FROM datasets WHERE case_id = ?)",
            (case_id,),
        ).fetchall()
    ]

    runs = [
        {
            "id": row["id"],
            "dataset_id": row["dataset_id"],
            "kind": row["kind"],
            "sql": row["sql"],
            "code": row["code"],
            "columns": json.loads(row["columns_json"]),
            "rows": json.loads(row["rows_json"]),
            "row_count": row["row_count"],
            "truncated": bool(row["truncated"]),
            "executed_at": row["executed_at"],
        }
        for row in db.execute(
            "SELECT id, dataset_id, kind, sql, code, columns_json, rows_json, "
            "row_count, truncated, executed_at FROM runs WHERE case_id = ? "
            "ORDER BY executed_at",
            (case_id,),
        ).fetchall()
    ]

    findings = [
        {
            "id": row["id"],
            "run_id": row["run_id"],
            "statement": row["statement"],
            "interpretation": row["interpretation"],
            "caveat": row["caveat"],
            "validation_status": row["validation_status"],
            "created_at": row["created_at"],
        }
        for row in db.execute(
            "SELECT id, run_id, statement, interpretation, caveat, "
            "validation_status, created_at FROM findings WHERE case_id = ? "
            "ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]

    charts = [
        {
            "id": row["id"],
            "run_id": row["run_id"],
            "kind": row["kind"],
            "x": row["x"],
            "y": row["y"],
            "series": row["series"],
            "title": row["title"],
            "width": row["width"],
            "height": row["height"],
            "created_at": row["created_at"],
            "svg": Path(row["stored_path"]).read_text(encoding="utf-8")
            if Path(row["stored_path"]).is_file()
            else "",
        }
        for row in db.execute(
            "SELECT id, run_id, kind, x, y, series, title, stored_path, width, "
            "height, created_at FROM charts WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]

    plans = [
        {
            "id": row["id"],
            "dataset_id": row["dataset_id"],
            "question": row["question"],
            "plan": json.loads(row["plan_json"]),
            "source": row["source"],
            "created_at": row["created_at"],
        }
        for row in db.execute(
            "SELECT id, dataset_id, question, plan_json, source, created_at "
            "FROM plans WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]

    return {
        "format": PACKAGE_FORMAT,
        "version": PACKAGE_VERSION,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "case": {
            "id": case_row["id"],
            "question": case_row["question"],
            "dataset": case_row["dataset"],
            "created_at": case_row["created_at"],
            "updated_at": case_row["updated_at"],
        },
        "datasets": datasets,
        "profiles": profiles,
        "runs": runs,
        "findings": findings,
        "charts": charts,
        "plans": plans,
    }


class PackageError(ValueError):
    """A package that cannot be imported; the caller answers 400 with it."""


def _require_keys(package: dict) -> None:
    if not isinstance(package, dict):
        raise PackageError("package must be a JSON object")
    if package.get("format") != PACKAGE_FORMAT:
        raise PackageError(f"unsupported package format (expected {PACKAGE_FORMAT})")
    if int(package.get("version") or 0) != PACKAGE_VERSION:
        raise PackageError(f"unsupported package version (expected {PACKAGE_VERSION})")
    for key in ("case", "datasets", "runs", "findings", "charts", "profiles", "plans"):
        if key not in package:
            raise PackageError(f"package is missing the '{key}' section")


def import_package(db, package: dict, data_dir: Path) -> dict:
    """Reconstruct a case from an exported package.

    Returns the new case. Every entity gets a fresh ID, with references remapped,
    so an imported package never collides with existing IDs.
    """
    _require_keys(package)
    source_case = package["case"]
    if not isinstance(source_case.get("question"), str) or not source_case["question"].strip():
        raise PackageError("package case has no question")

    new_case_id = str(uuid4())
    now = datetime.now(timezone.utc)
    db.execute(
        "INSERT INTO cases (id, question, dataset, created_at, updated_at) "
        "VALUES (?, ?, ?, ?, ?)",
        (
            new_case_id,
            source_case["question"],
            source_case.get("dataset") or "",
            source_case.get("created_at") or now.isoformat(),
            now.isoformat(),
        ),
    )

    case_dir = data_dir / new_case_id
    case_dir.mkdir(parents=True, exist_ok=True)

    dataset_ids: dict[str, str] = {}
    for dataset in package["datasets"]:
        new_dataset_id = str(uuid4())
        dataset_ids[dataset["id"]] = new_dataset_id
        stored_path = case_dir / f"{new_dataset_id}.{dataset.get('format') or 'csv'}"
        payload = dataset.get("data_base64") or ""
        if payload:
            try:
                stored_path.write_bytes(base64.b64decode(payload))
            except (ValueError, OSError) as error:
                raise PackageError(f"dataset '{dataset['filename']}' is not decodable: {error}")
        db.execute(
            "INSERT INTO datasets (id, case_id, filename, stored_path, format, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                new_dataset_id,
                new_case_id,
                dataset.get("filename") or "dataset",
                str(stored_path),
                dataset.get("format") or "csv",
                dataset.get("created_at") or now.isoformat(),
            ),
        )

    for profile in package["profiles"]:
        db.execute(
            "INSERT OR REPLACE INTO profiles (dataset_id, rows, columns_json, stats_json, "
            "duplicate_rows, profiled_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                dataset_ids.get(profile.get("dataset_id")),
                profile.get("rows") or 0,
                json.dumps(profile.get("columns") or []),
                json.dumps(profile.get("stats") or {}),
                profile.get("duplicate_rows") or 0,
                profile.get("profiled_at") or now.isoformat(),
            ),
        )

    run_ids: dict[str, str] = {}
    for run in package["runs"]:
        new_run_id = str(uuid4())
        run_ids[run["id"]] = new_run_id
        db.execute(
            "INSERT INTO runs (id, case_id, dataset_id, kind, sql, code, columns_json, "
            "rows_json, row_count, truncated, executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_run_id,
                new_case_id,
                dataset_ids.get(run.get("dataset_id")),
                run.get("kind") or "sql",
                run.get("sql"),
                run.get("code"),
                json.dumps(run.get("columns") or []),
                json.dumps(run.get("rows") or []),
                run.get("row_count") or 0,
                1 if run.get("truncated") else 0,
                run.get("executed_at") or now.isoformat(),
            ),
        )

    for finding in package["findings"]:
        db.execute(
            "INSERT INTO findings (id, case_id, run_id, statement, interpretation, "
            "caveat, validation_status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                new_case_id,
                run_ids.get(finding.get("run_id")),
                finding.get("statement") or "",
                finding.get("interpretation"),
                finding.get("caveat"),
                finding.get("validation_status") or "not_evaluated",
                finding.get("created_at") or now.isoformat(),
            ),
        )

    for chart in package["charts"]:
        new_chart_id = str(uuid4())
        stored_path = case_dir / f"chart_{new_chart_id}.svg"
        svg = chart.get("svg") or ""
        if svg:
            stored_path.write_text(svg, encoding="utf-8")
        db.execute(
            "INSERT INTO charts (id, case_id, run_id, kind, x, y, series, title, "
            "stored_path, width, height, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_chart_id,
                new_case_id,
                run_ids.get(chart.get("run_id")),
                chart.get("kind") or "bar",
                chart.get("x") or "",
                chart.get("y") or "",
                chart.get("series"),
                chart.get("title") or "",
                str(stored_path),
                chart.get("width") or 800,
                chart.get("height") or 400,
                chart.get("created_at") or now.isoformat(),
            ),
        )

    for plan in package["plans"]:
        db.execute(
            "INSERT INTO plans (id, case_id, dataset_id, question, plan_json, source, "
            "created_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                new_case_id,
                dataset_ids.get(plan.get("dataset_id")),
                plan.get("question") or source_case["question"],
                json.dumps(plan.get("plan") or {}),
                plan.get("source") or "deterministic",
                plan.get("created_at") or now.isoformat(),
            ),
        )

    return {
        "id": new_case_id,
        "question": source_case["question"],
        "dataset": source_case.get("dataset") or "",
        "created_at": source_case.get("created_at") or now.isoformat(),
        "updated_at": now.isoformat(),
    }
