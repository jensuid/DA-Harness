"""Case history: a timeline of everything that happened in a case (P3-CASE-007).

The evidence graph answers "what backs each claim". This answers the simpler
question an analyst asks on reopening a case: what did I do here, and when?

It is a read-side projection, like evidence.py: it reads the persisted rows and
derives the timeline from each artifact's own timestamp. Nothing is stored, so
the timeline cannot drift from what is on disk - attach a dataset and an event
appears; delete the case and it is gone.

Validation's verdict is persisted with its own timestamp (P8-DECISION-008), so
the act of validating is an event in its own right; the finding's own event
still carries the status as its detail, which is what a reader scanning the
timeline for the claim's standing wants.
"""

import json
from datetime import datetime, timezone
from typing import Any

# One per artifact kind, in the order the loop usually produces them. Ties in
# timestamps keep this order, so a fast session still reads top to bottom.
EVENT_CASE_CREATED = "case_created"
EVENT_DATASET_ATTACHED = "dataset_attached"
EVENT_DATASET_PROFILED = "dataset_profiled"
EVENT_PLAN_CREATED = "plan_created"
EVENT_RUN_EXECUTED = "run_executed"
EVENT_CHART_RENDERED = "chart_rendered"
EVENT_FINDING_RECORDED = "finding_recorded"
# A proposed sharpening of the question, and the decision the analyst made
# about it (P8-REFINE-007). Two events from one row: the proposal at
# created_at, the decision at decided_at - the same shape as the loop's own
# propose-then-approve rhythm.
EVENT_QUESTION_REFINED = "question_refined"
EVENT_REFINE_DECISION = "refine_decision"
# The verdict validation computed, now that it has a timestamp of its own
# (P8-DECISION-008). AT-44 names validation among the minimum auditable events;
# before this it rode as the detail of the finding's own event, which said
# *what* the status was without saying the act of validating happened.
EVENT_FINDING_VALIDATED = "finding_validated"
# The implications the analyst wrote - the loop's exit, and the one event in
# the timeline a human authors rather than a tool (P8-DECISION-008).
EVENT_DECISION_WRITTEN = "decision_written"


def _parse(timestamp: str | None) -> datetime | None:
    if not timestamp:
        return None
    try:
        # fromisoformat handles the +00:00 offset this project writes.
        parsed = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def build_case_history(db, case_id: str) -> dict[str, Any]:
    """Project a case into its timeline.

    Raises ValueError when the case does not exist, so the caller answers 404.
    """
    case = db.execute(
        "SELECT id, question, dataset, created_at FROM cases WHERE id = ?",
        (case_id,),
    ).fetchone()
    if case is None:
        raise ValueError("case not found")

    events: list[tuple[datetime, int, dict[str, Any]]] = []
    order = 0

    def add(timestamp: str | None, kind: str, artifact_id: str | None,
            label: str, detail: str | None) -> None:
        nonlocal order
        when = _parse(timestamp)
        if when is None:
            # An artifact without a usable timestamp is not silently dropped:
            # it lands at the case's start so the timeline stays complete.
            when = _parse(case["created_at"]) or datetime.now()
        order += 1
        events.append((when, order, {
            "timestamp": when.isoformat(),
            "kind": kind,
            "artifact_id": artifact_id,
            "label": label,
            "detail": detail,
        }))

    add(case["created_at"], EVENT_CASE_CREATED, case["id"],
        case["question"], f"dataset: {case['dataset']}")

    datasets = db.execute(
        "SELECT id, filename, format, created_at FROM datasets "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()
    dataset_names = {row["id"]: row["filename"] for row in datasets}
    for row in datasets:
        add(row["created_at"], EVENT_DATASET_ATTACHED, row["id"],
            row["filename"], f"format: {row['format']}")

    for row in db.execute(
        "SELECT dataset_id, rows, duplicate_rows, profiled_at FROM profiles "
        "WHERE dataset_id IN (SELECT id FROM datasets WHERE case_id = ?) "
        "ORDER BY profiled_at",
        (case_id,),
    ).fetchall():
        add(row["profiled_at"], EVENT_DATASET_PROFILED, row["dataset_id"],
            dataset_names.get(row["dataset_id"], row["dataset_id"]),
            f"{row['rows']} rows, {row['duplicate_rows']} duplicate")

    for row in db.execute(
        "SELECT id, dataset_id, question, source, created_at FROM plans "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        add(row["created_at"], EVENT_PLAN_CREATED, row["id"],
            row["question"], f"source: {row['source']}")

    for row in db.execute(
        "SELECT id, kind, sql, code, row_count, executed_at FROM runs "
        "WHERE case_id = ? ORDER BY executed_at",
        (case_id,),
    ).fetchall():
        source = (row["sql"] or row["code"] or "").strip().splitlines()
        label = source[0][:120] if source else f"{row['kind']} run"
        add(row["executed_at"], EVENT_RUN_EXECUTED, row["id"], label,
            f"{row['kind']}, {row['row_count']} row(s) returned")

    for row in db.execute(
        "SELECT id, run_id, kind, x, y, title, created_at FROM charts "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        label = row["title"] or f"{row['kind']} of {row['y']} by {row['x']}"
        add(row["created_at"], EVENT_CHART_RENDERED, row["id"], label,
            f"from run {row['run_id']}")

    for row in db.execute(
        "SELECT id, statement, validation_status, created_at FROM findings "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        add(row["created_at"], EVENT_FINDING_RECORDED, row["id"],
            row["statement"], f"validation: {row['validation_status']}")

    for row in db.execute(
        "SELECT id, original_question, refined_question, source, status, "
        "edited_question, created_at, decided_at FROM refinements "
        "WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        if (row["status"] or "pending") == "declined":
            add(row["created_at"], EVENT_QUESTION_REFINED, row["id"],
                row["original_question"],
                "no refinement proposed; the question was already specific "
                f"(source: {row['source']})")
            continue
        add(row["created_at"], EVENT_QUESTION_REFINED, row["id"],
            row["refined_question"] or row["original_question"],
            f"proposed a sharpening of the question (source: {row['source']})")
        if row["decided_at"] and row["status"] != "pending":
            if row["status"] == "accepted":
                label = row["refined_question"] or row["original_question"]
                detail = "accepted; the case's question is now the refined one"
            elif row["status"] == "edited":
                label = row["edited_question"] or row["original_question"]
                detail = ("edited; the analyst's own wording replaced both the "
                          "original and the proposal")
            else:
                label = row["original_question"]
                detail = "kept the original question"
            add(row["decided_at"], EVENT_REFINE_DECISION, row["id"], label,
                detail)

    # The verdicts validation computed (P8-DECISION-008). One event per
    # validated finding, at the moment the validation ran - the timeline's
    # record that the loop's last step happened, which the finding's own event
    # (recorded when the claim was drafted, carrying the status as its detail)
    # cannot say on its own.
    finding_statements = {
        row["id"]: row["statement"]
        for row in db.execute(
            "SELECT id, statement FROM findings WHERE case_id = ?",
            (case_id,),
        ).fetchall()
    }
    for row in db.execute(
        "SELECT finding_id, status, validated_at FROM validations "
        "WHERE case_id = ? ORDER BY validated_at",
        (case_id,),
    ).fetchall():
        add(
            row["validated_at"],
            EVENT_FINDING_VALIDATED,
            row["finding_id"],
            finding_statements.get(row["finding_id"], row["finding_id"]),
            f"validation: {row['status']}",
        )

    # The implications the analyst wrote (P8-DECISION-008). A decision the case
    # remembers, at the moment it was written - the loop's exit, and the one
    # event that records a judgement rather than a computation.
    decision_row = db.execute(
        "SELECT implications_json, updated_at FROM decisions WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    if decision_row is not None and decision_row["updated_at"]:
        try:
            written = json.loads(decision_row["implications_json"] or "[]")
        except json.JSONDecodeError:
            written = []
        add(
            decision_row["updated_at"],
            EVENT_DECISION_WRITTEN,
            case_id,
            case["question"],
            f"{len(written)} implication(s) written",
        )

    events.sort(key=lambda item: (item[0], item[1]))

    counts = {
        "datasets": len(datasets),
        "profiles": sum(1 for e in events if e[2]["kind"] == EVENT_DATASET_PROFILED),
        "plans": sum(1 for e in events if e[2]["kind"] == EVENT_PLAN_CREATED),
        "runs": sum(1 for e in events if e[2]["kind"] == EVENT_RUN_EXECUTED),
        "charts": sum(1 for e in events if e[2]["kind"] == EVENT_CHART_RENDERED),
        "findings": sum(1 for e in events if e[2]["kind"] == EVENT_FINDING_RECORDED),
        "refinements": sum(
            1 for e in events if e[2]["kind"] == EVENT_QUESTION_REFINED
        ),
        "validations": sum(
            1 for e in events if e[2]["kind"] == EVENT_FINDING_VALIDATED
        ),
        "decisions": sum(
            1 for e in events if e[2]["kind"] == EVENT_DECISION_WRITTEN
        ),
    }
    return {
        "case_id": case_id,
        "question": case["question"],
        "events": [event for _, _, event in events],
        "counts": counts,
    }
