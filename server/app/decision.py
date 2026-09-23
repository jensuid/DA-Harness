"""The loop's exit: the decision view (P8-DECISION-008, UX 46).

Until this task, a validated finding was the end of the road. The verdict was
computed, shown and discarded - only the status survived, on the finding - and
nothing in the product closed over what the loop had established. The PRD's own
flow (UX 48) ends at Decision Support -> Export; this module is the decision
support.

What it is *not* is as important as what it is. DAH informs decisions; it does
not make them. So the view contains no score, no ranking, no recommendation and
no weighting: a finding is either one validation stood behind or one it did
not, the uncertainty is the checks that did not pass carried verbatim with
their own sentences (UX 44's rule - structured signals, not confidence), and
the implications are the analyst's own words, written by the analyst. The
module assembles; it never concludes.

Everything here is a pure function of rows already on disk. Nothing is executed
and nothing is derived that the case does not already store, which is what
makes the view safe to render on a read and stable across two reads: reading a
decision changes nothing, and a verdict read an hour later is the verdict
validation computed an hour ago.
"""

from __future__ import annotations

import json
from typing import Any

from app.workflow import case_progress

# A finding the case can act on. `supported` is a clean pass; a
# `partially_supported` finding passed the hard dimensions and carries soft
# concerns, which is exactly the residual uncertainty the decision needs to
# see. Anything else is a claim the loop refused or has not examined, and
# belongs in the open items rather than in the key findings.
ACTIONABLE_STATUSES = ("supported", "partially_supported")

# The implications are the analyst's, and they are bounded the way the context's
# lists are bounded: an unbounded list is an unbounded form, and a book-length
# entry is not a decision aid.
MAX_IMPLICATIONS = 12
IMPLICATION_MAX_LENGTH = 2_000


class ImplicationError(ValueError):
    """A list of implications the store will not accept; the caller answers 400."""


def clean_implications(raw: Any) -> list[str]:
    """Normalise and validate the implications the analyst wrote.

    Raises ImplicationError with a sentence naming the first entry that breaks
    a rule, so a 400 tells the analyst which implication to fix rather than
    that something was wrong. An empty list is allowed: clearing them is a
    decision the analyst is allowed to make, so the refusal is about shape,
    never about whether the analyst decided enough.
    """
    if not isinstance(raw, list):
        raise ImplicationError("implications must be a list of strings")
    cleaned: list[str] = []
    for index, entry in enumerate(raw):
        if not isinstance(entry, str):
            raise ImplicationError(
                f"implication {index + 1} is not a string"
            )
        text = entry.strip()
        if not text:
            raise ImplicationError(
                f"implication {index + 1} is empty"
            )
        if len(text) > IMPLICATION_MAX_LENGTH:
            raise ImplicationError(
                f"implication {index + 1} is longer than "
                f"{IMPLICATION_MAX_LENGTH} characters"
            )
        cleaned.append(text)
    if len(cleaned) > MAX_IMPLICATIONS:
        raise ImplicationError(
            f"a case carries at most {MAX_IMPLICATIONS} implications"
        )
    return cleaned


def _uncertainty(verdict: dict | None) -> list[dict[str, Any]]:
    """The checks a validated finding did not pass, as the view carries them.

    A `supported` finding has none. A `partially_supported` finding has its soft
    concerns, and a finding whose status was set by hand over a stored verdict
    that failed hard still shows the hard failure - the uncertainty is what
    validation found, not what the status implies.
    """
    if verdict is None:
        return []
    try:
        checks = json.loads(verdict["checks_json"] or "[]")
    except (json.JSONDecodeError, TypeError):
        return []
    return [
        {
            "dimension": check.get("dimension") or check.get("name") or "",
            "detail": check.get("detail") or "",
            "hard": bool(check.get("hard")),
        }
        for check in checks
        if isinstance(check, dict) and not check.get("passed")
    ]


def _reasons(row, verdict: dict | None) -> list[str]:
    """Why an open item is still open, as sentences."""
    if row["validation_status"] == "not_evaluated":
        return ["awaiting validation - the loop's last step has not run"]
    failed = [
        check["detail"]
        for check in _uncertainty(verdict)
        if check["hard"] and check["detail"]
    ]
    if failed:
        return failed
    if verdict is None:
        # The status was set without a recorded verdict (the manual override
        # path), so the checks behind it are unknown rather than absent.
        return [
            "the status was set without a recorded verdict, so its checks "
            "are unknown - validate the finding to record them"
        ]
    return ["the verdict left this finding unresolved"]


def build_decision(db, case_id: str) -> dict[str, Any] | None:
    """Assemble a case's decision view, or None if the case does not exist.

    Read-only, deterministic, and executes nothing: every field is a stored row
    or a count of stored rows. The findings read oldest first, the order the
    loop produced them in, so the decision reads as the analysis happened.
    """
    case = db.execute(
        "SELECT id, question FROM cases WHERE id = ?", (case_id,)
    ).fetchone()
    if case is None:
        return None

    purpose = ""
    context_row = db.execute(
        "SELECT purpose FROM contexts WHERE case_id = ?", (case_id,)
    ).fetchone()
    if context_row is not None:
        purpose = context_row["purpose"] or ""

    # The verdict each finding earned, keyed by the finding: the whole verdict,
    # not only the status, is what the view's uncertainty reads.
    verdicts = {
        row["finding_id"]: row
        for row in db.execute(
            "SELECT finding_id, status, checks_json, validated_at "
            "FROM validations WHERE case_id = ?",
            (case_id,),
        ).fetchall()
    }

    findings: list[dict[str, Any]] = []
    open_items: list[dict[str, Any]] = []
    for row in db.execute(
        "SELECT id, statement, interpretation, caveat, validation_status, "
        "created_at FROM findings WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall():
        verdict = verdicts.get(row["id"])
        if row["validation_status"] in ACTIONABLE_STATUSES:
            findings.append(
                {
                    "id": row["id"],
                    "statement": row["statement"],
                    "validation_status": row["validation_status"],
                    "interpretation": row["interpretation"],
                    "caveat": row["caveat"],
                    "uncertainty": _uncertainty(verdict),
                    "validated_at": verdict["validated_at"]
                    if verdict is not None
                    else None,
                }
            )
            continue
        open_items.append(
            {
                "id": row["id"],
                "statement": row["statement"],
                "validation_status": row["validation_status"],
                "reasons": _reasons(row, verdict),
            }
        )

    implications: list[str] = []
    updated_at = None
    decision_row = db.execute(
        "SELECT implications_json, updated_at FROM decisions WHERE case_id = ?",
        (case_id,),
    ).fetchone()
    if decision_row is not None:
        try:
            stored = json.loads(decision_row["implications_json"] or "[]")
        except json.JSONDecodeError:
            stored = []
        implications = [
            str(item) for item in stored if isinstance(item, str) and item.strip()
        ]
        updated_at = decision_row["updated_at"]

    validated = sum(
        1 for row in findings if row["validation_status"] == "supported"
    )
    partial = len(findings) - validated
    # The loop's closure is the core's to declare, not the view's: this reads
    # `workflow.case_progress`, so the decision cannot say the loop is open
    # while the shell's rail says it is closed (or the reverse). One definition,
    # in the one place that derives it from the artifacts.
    progress = case_progress(db, case_id)

    return {
        "case_id": case_id,
        "question": case["question"],
        "purpose": purpose,
        "loop_closed": bool(progress["loop_closed"]),
        "findings": findings,
        "open_items": open_items,
        "implications": implications,
        "updated_at": updated_at,
        "counts": {
            "findings": len(findings) + len(open_items),
            "key_findings": len(findings),
            "supported": validated,
            "partially_supported": partial,
            "open_items": len(open_items),
            "open_checks": sum(len(item["uncertainty"]) for item in findings),
            "implications": len(implications),
        },
    }
