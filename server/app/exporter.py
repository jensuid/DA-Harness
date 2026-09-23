_CONTEXT_TEXT_MAX = 2_000
_CONTEXT_LIST_MAX = 12

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
    agent_steps    - the agent's audit trail: each proposal, its role, its
                     source, the human's decision, and what the write produced
                     (P6-AGENT-002, P7-AGENT-001)

Original IDs are carried through so relationships inside the package stay
traceable (a finding points at its run, a chart at its run); import remaps
them to fresh IDs rather than reusing them.
"""

import base64
import json
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from app.models import REFINEMENT_STATUSES

PACKAGE_FORMAT = "dah-case-package"
PACKAGE_VERSION = 1

# Guard against a package that is too large to handle in one request.
_MAX_PACKAGE_BYTES = 100 * 1024 * 1024

# The implications a restored decision may carry, bounded as the write endpoint
# bounds them (app/decision.py), so an imported package cannot smuggle an
# unbounded list past the only path that accepts one.
_DECISION_MAX = 12


def _read_bytes(path: str) -> str:
    """File contents as base64, or an empty string if the file is gone."""
    try:
        return base64.b64encode(Path(path).read_bytes()).decode("ascii")
    except OSError:
        return ""


def _dataset_ids_of(row) -> list[str] | None:
    """The datasets a run touches, as recorded (None for older packages)."""
    raw = row["dataset_ids_json"] if "dataset_ids_json" in row.keys() else None
    if not raw:
        return None
    try:
        ids = json.loads(raw)
    except json.JSONDecodeError:
        return None
    return [str(item) for item in ids] if ids else None


def _import_dataset_ids(run: dict, dataset_ids: dict[str, str]) -> str:
    """Re-map a package run's dataset list to the imported case's own ids."""
    listed = run.get("dataset_ids")
    if not listed:
        # Older packages name one dataset; the column keeps the remapped id.
        return json.dumps([dataset_ids.get(run.get("dataset_id"))])
    return json.dumps([dataset_ids.get(dataset_id) for dataset_id in listed])


def _chart_format(path: Path) -> str:
    """The artifact format, sniffed from its bytes (PNG magic, else SVG)."""
    try:
        with path.open("rb") as handle:
            head = handle.read(8)
    except OSError:
        return "svg"
    return "png" if head.startswith(b"\x89PNG\r\n\x1a\n") else "svg"


def export_case(db, case_id: str) -> dict | None:
    """Assemble a case into a self-contained package, or None if it is missing."""
    case_row = db.execute(
        "SELECT id, question, dataset, template_id, created_at, updated_at "
        "FROM cases WHERE id = ?",
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
            "quality": json.loads(row["quality_json"] or "[]"),
            "profiled_at": row["profiled_at"],
        }
        for row in db.execute(
            "SELECT dataset_id, rows, columns_json, stats_json, duplicate_rows, "
            "quality_json, profiled_at FROM profiles WHERE dataset_id IN "
            "(SELECT id FROM datasets WHERE case_id = ?)",
            (case_id,),
        ).fetchall()
    ]

    runs = [
        {
            "id": row["id"],
            "dataset_id": row["dataset_id"],
            "dataset_ids": _dataset_ids_of(row),
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
            "SELECT id, dataset_id, dataset_ids_json, kind, sql, code, "
            "columns_json, rows_json, row_count, truncated, executed_at "
            "FROM runs WHERE case_id = ? "
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
            "format": _chart_format(Path(row["stored_path"])),
            "image_b64": base64.b64encode(
                Path(row["stored_path"]).read_bytes()
            ).decode("ascii")
            if Path(row["stored_path"]).is_file()
            else "",
            # Legacy text field: older consumers read SVG from "svg". Kept for
            # charts rendered as SVG (an empty string for PNG ones).
            "svg": Path(row["stored_path"]).read_text(encoding="utf-8")
            if _chart_format(Path(row["stored_path"])) == "svg"
            and Path(row["stored_path"]).is_file()
            else "",
        }
        for row in db.execute(
            "SELECT id, run_id, kind, x, y, series, title, stored_path, width, "
            "height, created_at FROM charts WHERE case_id = ? ORDER BY created_at",
            (case_id,),
        ).fetchall()
    ]

    # The analyst's stated intent (P8-CONTEXT-001). A restored case without it
    # keeps every finding and loses what the analyst was trying to establish,
    # so it travels with the package rather than being re-derived.
    context_row = db.execute(
        "SELECT purpose, sub_questions_json, hypotheses_json, constraints_json "
        "FROM contexts WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    context = (
        {
            "purpose": context_row["purpose"] or "",
            "sub_questions": json.loads(context_row["sub_questions_json"] or "[]"),
            "hypotheses": json.loads(context_row["hypotheses_json"] or "[]"),
            "constraints": json.loads(context_row["constraints_json"] or "[]"),
        }
        if context_row is not None
        else {"purpose": "", "sub_questions": [], "hypotheses": [], "constraints": []}
    )

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

    agent_steps = [
        {
            "id": row["id"],
            "role": row["role"],
            "kind": row["kind"],
            "payload": json.loads(row["payload_json"]),
            "source": row["source"],
            "status": row["status"],
            "note": row["note"] or "",
            "created_at": row["created_at"],
            "decided_at": row["decided_at"],
        }
        for row in db.execute(
            "SELECT id, role, kind, payload_json, source, status, note, "
            "created_at, decided_at FROM agent_steps "
            "WHERE case_id = ? ORDER BY created_at",
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
            # Advisory: the template is a separate entity that may not exist in
            # the store this package is restored into, so import treats a
            # dangling reference as no lineage rather than an error.
            "template_id": case_row["template_id"]
            if "template_id" in case_row.keys()
            else None,
            "created_at": case_row["created_at"],
            "updated_at": case_row["updated_at"],
        },
        "datasets": datasets,
        "profiles": profiles,
        "runs": runs,
        "findings": findings,
        "charts": charts,
        "plans": plans,
        "context": context,
        "agent_steps": agent_steps,
        # The verdicts validation computed, in full (P8-DECISION-008). A
        # package used to carry a finding's status and nothing else, so a case
        # restored elsewhere lost the nine checks behind it - the residual
        # uncertainty its decision was made on. AT-43's "validation states
        # preserved" is a property of the package now, not a claim about it.
        "validations": [
            {
                "finding_id": row["finding_id"],
                "run_id": row["run_id"],
                "status": row["status"],
                "checks": json.loads(row["checks_json"] or "[]"),
                "validated_at": row["validated_at"],
            }
            for row in db.execute(
                "SELECT finding_id, run_id, status, checks_json, validated_at "
                "FROM validations WHERE case_id = ? ORDER BY validated_at",
                (case_id,),
            ).fetchall()
        ],
        # The decision the analyst wrote (P8-DECISION-008): the loop's exit,
        # which is the point of carrying a case anywhere else. Absent from
        # packages written before this task, which is no decision rather than
        # an error - the round trip degrades, it does not fail.
        "decision": _decision_section(db, case_id),
        # The proposed sharpenings and what the analyst did with them
        # (P8-REFINE-007). An accepted refinement replaced the question on the
        # case row; the original lives here, so the round trip keeps it
        # recoverable - AT-04's threshold holds across an export, not only
        # within one store.
        "refinements": [
            {
                "original_question": row["original_question"],
                "refined_question": row["refined_question"] or "",
                "rationale": row["rationale"] or "",
                "grounds": json.loads(row["grounds_json"] or "[]"),
                "source": row["source"],
                "status": row["status"],
                "edited_question": row["edited_question"],
                "created_at": row["created_at"],
                "decided_at": row["decided_at"],
            }
            for row in db.execute(
                "SELECT original_question, refined_question, rationale, "
                "grounds_json, source, status, edited_question, created_at, "
                "decided_at FROM refinements WHERE case_id = ? "
                "ORDER BY created_at",
                (case_id,),
            ).fetchall()
        ],
    }


def _decision_section(db, case_id: str) -> dict | None:
    """The case's decision, or None if the analyst wrote no implications."""
    row = db.execute(
        "SELECT implications_json, updated_at FROM decisions WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    if row is None:
        return None
    try:
        implications = json.loads(row["implications_json"] or "[]")
    except json.JSONDecodeError:
        implications = []
    return {
        "implications": [
            str(item) for item in implications if isinstance(item, str) and item.strip()
        ],
        "updated_at": row["updated_at"],
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
    # agent_steps is younger than the package format (P6-AGENT-002), so its
    # absence means an older package, not a corrupt one.


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
        "INSERT INTO cases (id, question, dataset, template_id, created_at, "
        "updated_at) VALUES (?, ?, ?, ?, ?, ?)",
        (
            new_case_id,
            source_case["question"],
            source_case.get("dataset") or "",
            source_case.get("template_id"),
            source_case.get("created_at") or now.isoformat(),
            now.isoformat(),
        ),
    )

    # The stated intent, if the package carries one (P8-CONTEXT-001). A package
    # exported before the context object existed has no section, which is an
    # empty context rather than an error - the round trip degrades, it does not
    # fail.
    context_payload = package.get("context") or {}
    purpose = str(context_payload.get("purpose") or "").strip()[:_CONTEXT_TEXT_MAX]
    context_lists = {}
    for field in ("sub_questions", "hypotheses", "constraints"):
        items = [
            str(item).strip()[:_CONTEXT_TEXT_MAX]
            for item in (context_payload.get(field) or [])
            if isinstance(item, (str, int, float)) and str(item).strip()
        ][:_CONTEXT_LIST_MAX]
        context_lists[field] = items
    if purpose or any(context_lists.values()):
        db.execute(
            "INSERT INTO contexts (case_id, purpose, sub_questions_json, "
            "hypotheses_json, constraints_json, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (
                new_case_id,
                purpose,
                json.dumps(context_lists["sub_questions"]),
                json.dumps(context_lists["hypotheses"]),
                json.dumps(context_lists["constraints"]),
                now.isoformat(),
            ),
        )

    # The question's refinement history, if the package carries it. A package
    # from before the feature has no section, which is no history rather than
    # an error - the round trip degrades, it does not fail.
    for refinement in (package.get("refinements") or []):
        if not isinstance(refinement, dict):
            continue
        original = str(refinement.get("original_question") or "").strip()
        if not original:
            continue
        status = refinement.get("status")
        if status not in REFINEMENT_STATUSES:
            status = "declined"
        db.execute(
            "INSERT INTO refinements (id, case_id, original_question, "
            "refined_question, rationale, grounds_json, source, status, "
            "edited_question, created_at, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                new_case_id,
                original,
                str(refinement.get("refined_question") or "")[:_CONTEXT_TEXT_MAX],
                str(refinement.get("rationale") or "")[:_CONTEXT_TEXT_MAX * 4],
                json.dumps(refinement.get("grounds") or []),
                str(refinement.get("source") or "deterministic"),
                status,
                str(refinement.get("edited_question") or "").strip()[:_CONTEXT_TEXT_MAX] or None,
                refinement.get("created_at") or now.isoformat(),
                refinement.get("decided_at"),
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
            "duplicate_rows, quality_json, profiled_at) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                dataset_ids.get(profile.get("dataset_id")),
                profile.get("rows") or 0,
                json.dumps(profile.get("columns") or []),
                json.dumps(profile.get("stats") or {}),
                profile.get("duplicate_rows") or 0,
                # A package from before quality detection has no list; an empty
                # one is the honest read of "nothing was recorded", and a
                # reprofile repopulates it.
                json.dumps(profile.get("quality") or []),
                profile.get("profiled_at") or now.isoformat(),
            ),
        )

    run_ids: dict[str, str] = {}
    for run in package["runs"]:
        new_run_id = str(uuid4())
        run_ids[run["id"]] = new_run_id
        db.execute(
            "INSERT INTO runs (id, case_id, dataset_id, kind, sql, code, "
            "dataset_ids_json, columns_json, rows_json, row_count, truncated, "
            "executed_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_run_id,
                new_case_id,
                dataset_ids.get(run.get("dataset_id")),
                run.get("kind") or "sql",
                run.get("sql"),
                run.get("code"),
                _import_dataset_ids(run, dataset_ids),
                json.dumps(run.get("columns") or []),
                json.dumps(run.get("rows") or []),
                run.get("row_count") or 0,
                1 if run.get("truncated") else 0,
                run.get("executed_at") or now.isoformat(),
            ),
        )

    finding_ids: dict[str, str] = {}
    for finding in package["findings"]:
        new_finding_id = str(uuid4())
        finding_ids[finding["id"]] = new_finding_id
        db.execute(
            "INSERT INTO findings (id, case_id, run_id, statement, interpretation, "
            "caveat, validation_status, created_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                new_finding_id,
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
        # Newer packages carry the artifact as base64 with an explicit format;
        # older ones carry the SVG as text under "svg".
        encoded = chart.get("image_b64") or ""
        legacy_svg = chart.get("svg") or ""
        fmt = chart.get("format") or ("svg" if legacy_svg else "svg")
        stored_path = case_dir / f"chart_{new_chart_id}.{fmt}"
        if encoded:
            stored_path.write_bytes(base64.b64decode(encoded))
        elif legacy_svg:
            stored_path.write_text(legacy_svg, encoding="utf-8")
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

    # The verdicts the package carried (P8-DECISION-008). Finding ids are
    # remapped exactly as the findings above were, so a restored verdict points
    # at the restored finding. Absent from older packages, which is the same
    # degradation every other young section accepts.
    for verdict in (package.get("validations") or []):
        if not isinstance(verdict, dict):
            continue
        new_finding_id = finding_ids.get(verdict.get("finding_id"))
        if new_finding_id is None:
            continue
        db.execute(
            "INSERT OR REPLACE INTO validations (finding_id, case_id, run_id, "
            "status, checks_json, validated_at) VALUES (?, ?, ?, ?, ?, ?)",
            (
                new_finding_id,
                new_case_id,
                run_ids.get(verdict.get("run_id")),
                str(verdict.get("status") or "not_evaluated"),
                json.dumps(verdict.get("checks") or []),
                verdict.get("validated_at") or now.isoformat(),
            ),
        )

    # The decision the analyst wrote (P8-DECISION-008).
    decision_payload = package.get("decision")
    if isinstance(decision_payload, dict):
        implications = [
            str(item).strip()[:_CONTEXT_TEXT_MAX]
            for item in (decision_payload.get("implications") or [])
            if isinstance(item, (str, int, float)) and str(item).strip()
        ][:_DECISION_MAX]
        if implications:
            db.execute(
                "INSERT OR REPLACE INTO decisions (case_id, implications_json, "
                "updated_at) VALUES (?, ?, ?)",
                (
                    new_case_id,
                    json.dumps(implications),
                    decision_payload.get("updated_at") or now.isoformat(),
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

    # The agent's audit trail. A step's payload names the artifacts it proposed
    # to touch, so the ids are remapped exactly as the rows above are; a step
    # that was never decided keeps its pending status, since importing is not a
    # decision. Absent entirely from packages written before P6-AGENT-002.
    for step in package.get("agent_steps") or []:
        payload = step.get("payload") or {}
        remapped = dict(payload)
        for key, mapping in (
            ("dataset_id", dataset_ids),
            ("run_id", run_ids),
            ("finding_id", finding_ids),
        ):
            if isinstance(remapped.get(key), str):
                remapped[key] = mapping.get(remapped[key], remapped[key])
        db.execute(
            "INSERT INTO agent_steps (id, case_id, role, kind, payload_json, "
            "source, status, note, created_at, decided_at) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                str(uuid4()),
                new_case_id,
                step.get("role") or "analyst",
                step.get("kind") or "end",
                json.dumps(remapped),
                step.get("source") or "deterministic",
                step.get("status") or "done",
                step.get("note") or "",
                step.get("created_at") or now.isoformat(),
                step.get("decided_at"),
            ),
        )

    return {
        "id": new_case_id,
        "question": source_case["question"],
        "dataset": source_case.get("dataset") or "",
        # Advisory: the template may not exist in this store, so a case that
        # keeps the reference still answers every question without it.
        "template_id": source_case.get("template_id"),
        "created_at": source_case.get("created_at") or now.isoformat(),
        "updated_at": now.isoformat(),
    }
