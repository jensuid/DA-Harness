"""Agentic analysis (P6-AGENT-002).

The loop already existed as endpoints - profile, plan, generate code, run,
interpret, draft, accept, chart, validate - each with its own honesty budget
and each writing through one path. What did not exist was the loop *driver*:
nothing read a result and decided what to try next, so a human walked the
panels one click at a time even when the next click was never in doubt.

This module is that driver, and it is deliberately not an autonomous one. It
proposes a step; a human approves the step by id; the write runs through the
endpoint that already owns it. The agent holds no privilege a hand-written call
lacks: its SQL passes the same read-only gate and row cap, its findings are
created by the same POST, and its drafts and code proposals come from the same
stateless modules with the same validation. What it contributes is the
sequence, the memory of what it already tried, and an audit row for every step.

Design rules this module enforces:

- The next step is DERIVED from the case's artifacts, the way the workflow stage
  is (P3-FLOW-004). Nothing stores "the agent is on step 4", so an interrupted
  agent resumes exactly where it stopped and can never claim a step the data
  does not support.
- A write step needs an approval id. Approving a step that is not this case's
  current pending step is a 409, not a second write.
- Iteration is not re-proposal. A query that returned no rows advances the
  generator's variant so the next proposal reads different columns; a proposal
  identical to one already tried is a dead end the run states, not a retry.
- The budget is bounded. Exhausting it ends the run with a reason, and a
  dataset with no usable axis ends it immediately, so the agent always
  terminates.
- Every step records the `source` of the proposal that made it, so a reviewer
  can see which engine spoke at every point in an agent-run case.
"""

import json
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.drafter import create_draft as create_draft_module
from app.generator import create_code as create_code_module

# The kinds of step the agent takes, in loop order: profile, plan, analyze,
# interpret, accept, chart, validate. `profile` and `plan` are the entry
# conditions the endpoints themselves enforce with a 400; the agent does the
# case the courtesy of naming them instead of failing later. `accept` carries
# the drafter's candidate finding inside its payload - the draft is stateless by
# design (P3-AI-012), so there is no separate draft step to take - and `analyze`
# carries its proposal the same way, since generate-code writes nothing either.
# Every one of them is a write the human must approve first; the stateless
# proposals those writes consume never reach the table on their own.
#
# STEP_END is a terminal record rather than a write: it explains why the agent
# stopped, so an abandoned case states its reason instead of falling silent
# mid-loop.
STEP_END = "end"

# The roles a case can be worked by (P7-AGENT-001). Each shares the one
# approval gate: a role never writes without a human's yes, and a GET never
# proposes. What differs is the objective - the analyst drives the analysis
# loop, the reviewer audits what it produced - so an agent-run case can be
# examined by an agent that did not write it.
ROLE_ANALYST = "analyst"
ROLE_REVIEWER = "reviewer"
ROLES = (ROLE_ANALYST, ROLE_REVIEWER)

# The step kinds are shared, because the write paths are: a reviewer's audit
# runs through the evaluate endpoint, exactly as a human audit would.
STEP_EVALUATE = "evaluate"

STATUS_PENDING = "pending"
STATUS_DONE = "done"
STATUS_REJECTED = "rejected"

# A query that returns nothing is worth retrying with a different axis, but not
# forever: three attempts covers measure, dimension and period rotations, and
# anything still empty is a question the data cannot answer rather than a
# strategy the agent has not found yet.
_MAX_ATTEMPTS = 3

_TABLE = "agent_steps"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _primary_dataset(db, case_id: str) -> dict | None:
    """The dataset the agent works on: the case's named one, else the first.

    The agent is single-dataset by design; planning a join needs the two
    datasets named and is a human's call, not a guess.
    """
    case = db.execute(
        "SELECT dataset FROM cases WHERE id = ?", (case_id,)
    ).fetchone()
    rows = db.execute(
        "SELECT id, filename FROM datasets WHERE case_id = ? ORDER BY created_at",
        (case_id,),
    ).fetchall()
    if not rows:
        return None
    if case and case["dataset"]:
        for row in rows:
            if row["filename"] == case["dataset"]:
                return dict(row)
    return dict(rows[0])


def _unprofiled(db, case_id: str, dataset_id: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM profiles WHERE dataset_id = ?", (dataset_id,)
    ).fetchone()
    return row is None


def _has_plan(db, case_id: str, dataset_id: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM plans WHERE case_id = ? AND dataset_id = ?",
        (case_id, dataset_id),
    ).fetchone()
    return row is not None


def _profile(db, dataset_id: str) -> dict | None:
    row = db.execute(
        "SELECT rows, columns_json, stats_json, duplicate_rows FROM profiles "
        "WHERE dataset_id = ?",
        (dataset_id,),
    ).fetchone()
    if row is None:
        return None
    return {
        "rows": row["rows"],
        "columns": json.loads(row["columns_json"]),
        "stats": json.loads(row["stats_json"]),
        "duplicate_rows": row["duplicate_rows"],
    }


def _latest_run(db, case_id: str) -> dict | None:
    """The case's most recent run, with its columns and rows."""
    row = db.execute(
        "SELECT id, dataset_id, kind, sql, code, columns_json, rows_json, "
        "row_count, truncated, executed_at FROM runs WHERE case_id = ? "
        "ORDER BY executed_at DESC LIMIT 1",
        (case_id,),
    ).fetchone()
    if row is None:
        return None
    return dict(
        row,
        columns=json.loads(row["columns_json"]),
        rows=json.loads(row["rows_json"]),
    )


def _findings_for_run(db, case_id: str, run_id: str) -> list[dict]:
    return [
        dict(row)
        for row in db.execute(
            "SELECT id, validation_status FROM findings WHERE case_id = ? "
            "AND run_id = ? ORDER BY created_at",
            (case_id, run_id),
        ).fetchall()
    ]


def _charts_for_run(db, case_id: str, run_id: str) -> list[dict]:
    return [
        dict(row)
        for row in db.execute(
            "SELECT id FROM charts WHERE case_id = ? AND run_id = ?",
            (case_id, run_id),
        ).fetchall()
    ]


def _interpretation_exists(db, case_id: str, run_id: str) -> bool:
    row = db.execute(
        "SELECT 1 FROM interpretations WHERE case_id = ? AND run_id = ?",
        (case_id, run_id),
    ).fetchone()
    return row is not None


def _pending(db, case_id: str, role: str) -> dict | None:
    """The step awaiting a human, if any. There is at most one.

    An `end` row is settled when it is written - it records a conclusion, not
    work - so it is excluded even though nothing decides it afterwards.
    """
    row = db.execute(
        f"SELECT id, case_id, role, kind, payload_json, source, status, note, "
        f"created_at, decided_at FROM {_TABLE} "
        "WHERE case_id = ? AND role = ? AND status = ? AND kind != ? "
        "ORDER BY created_at DESC LIMIT 1",
        (case_id, role, STATUS_PENDING, STEP_END),
    ).fetchone()
    if row is None:
        return None
    return dict(row, payload=json.loads(row["payload_json"]))


def _history(db, case_id: str, role: str) -> list[dict]:
    """The settled steps, newest first.

    The pending step is reported separately, so it is excluded here - a caller
    reading both fields would otherwise see the live proposal twice.
    """
    return [
        dict(row, payload=json.loads(row["payload_json"]))
        for row in db.execute(
            f"SELECT id, case_id, role, kind, payload_json, source, status, "
            f"note, created_at, decided_at FROM {_TABLE} WHERE case_id = ? "
            f"AND role = ? AND status != ? ORDER BY created_at DESC",
            (case_id, role, STATUS_PENDING),
        ).fetchall()
    ]


def _attempted_codes(db, case_id: str) -> set[str]:
    """Every code the agent has already proposed for this case.

    A retry that reproduces a tried query spends the budget without learning
    anything, so the proposal loop skips these.
    """
    return {
        json.loads(row["payload_json"]).get("code", "")
        for row in db.execute(
            f"SELECT payload_json FROM {_TABLE} WHERE case_id = ? AND kind = 'analyze'",
            (case_id,),
        ).fetchall()
    }


def _attempt_count(db, case_id: str, role: str) -> int:
    return int(
        db.execute(
            f"SELECT COUNT(*) AS n FROM {_TABLE} WHERE case_id = ? "
            f"AND role = ? AND kind = 'analyze'",
            (case_id, role),
        ).fetchone()["n"]
    )


def _record(
    db, case_id: str, role: str, kind: str, payload: dict, source: str, note: str = ""
) -> dict:
    step = {
        "id": str(uuid4()),
        "case_id": case_id,
        "kind": kind,
        "payload": payload,
        "source": source,
        "status": STATUS_PENDING,
        "note": note,
        "created_at": _now(),
        "decided_at": None,
    }
    db.execute(
        f"INSERT INTO {_TABLE} (id, case_id, role, kind, payload_json, source, "
        "status, note, created_at, decided_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            step["id"],
            case_id,
            role,
            kind,
            json.dumps(payload),
            source,
            STATUS_PENDING,
            note,
            step["created_at"],
            None,
        ),
    )
    return step


def _decide(db, step_id: str, status: str, note: str = "") -> None:
    db.execute(
        f"UPDATE {_TABLE} SET status = ?, note = ?, decided_at = ? WHERE id = ?",
        (status, note, _now(), step_id),
    )


def _question(db, case_id: str) -> str:
    row = db.execute("SELECT question FROM cases WHERE id = ?", (case_id,)).fetchone()
    return row["question"] if row else ""


def _empty(run: dict | None) -> bool:
    return run is None or not run["rows"]


def _analyze_proposal(
    db, case_id: str, dataset: dict, question: str, profile: dict
) -> dict | None:
    """Propose the next analysis, rotating axes until the code is untried.

    Returns None when no untried proposal exists within the budget - a dead end
    the caller states rather than retries.
    """
    tried = _attempted_codes(db, case_id)
    attempts = _attempt_count(db, case_id, ROLE_ANALYST)
    for variant in range(attempts, _MAX_ATTEMPTS):
        proposal, source = create_code_module(question, profile, "sql", variant)
        if proposal.get("code") and proposal["code"] not in tried:
            return {
                "kind": "analyze",
                "payload": {
                    "dataset_id": dataset["id"],
                    "filename": dataset["filename"],
                    "variant": variant,
                    **proposal,
                },
                "source": source,
            }
    return None


def _analyst_step(db, case_id: str) -> dict | None:
    """Derive the next step from the case's artifacts, or None if the loop is closed.

    This is the agent's whole decision procedure, and it is a pure projection
    over what the case actually has - the same discipline as the workflow stage,
    so the agent can never be ahead of or behind the data.
    """
    dataset = _primary_dataset(db, case_id)
    if dataset is None:
        return None

    if _unprofiled(db, case_id, dataset["id"]):
        return {
            "kind": "profile",
            "payload": {"dataset_id": dataset["id"], "filename": dataset["filename"]},
            "source": "deterministic",
            "note": "Profiling is what the planner and the generator read.",
        }

    if not _has_plan(db, case_id, dataset["id"]):
        return {
            "kind": "plan",
            "payload": {"dataset_id": dataset["id"], "filename": dataset["filename"]},
            "source": "deterministic",
            "note": "A plan is the input the agent iterates against.",
        }

    question = _question(db, case_id)
    profile = _profile(db, dataset["id"])
    run = _latest_run(db, case_id)

    # An empty result is the agent's one real decision point: try a different
    # query rather than interpreting nothing. A proposal that repeats one already
    # tried (no usable axis left) ends the run honestly instead of looping.
    if _empty(run):
        proposal = _analyze_proposal(db, case_id, dataset, question, profile or {})
        if proposal is None:
            return None
        proposal["note"] = (
            "The previous query returned no rows; this proposal reads "
            "different columns."
            if _attempt_count(db, case_id, ROLE_ANALYST)
            else "The first read of the dataset."
        )
        return proposal

    if not _interpretation_exists(db, case_id, run["id"]):
        return {
            "kind": "interpret",
            "payload": {"run_id": run["id"], "row_count": run["row_count"]},
            "source": "deterministic",
            "note": "A plain-language read of the result the agent just produced.",
        }

    findings = _findings_for_run(db, case_id, run["id"])
    if not findings:
        question = _question(db, case_id)
        draft, source = create_draft_module(
            question=question,
            kind=run["kind"],
            source_text=run["sql"] if run["kind"] == "sql" else run["code"],
            columns=run["columns"],
            rows=run["rows"],
            profile=_profile(db, run["dataset_id"]),
            truncated=bool(run["truncated"]),
        )
        return {
            "kind": "accept",
            "payload": {
                "run_id": run["id"],
                "statement": draft["statement"],
                "interpretation": draft.get("interpretation"),
                "caveat": draft.get("caveat"),
                "grounds": draft.get("grounds", []),
            },
            "source": source,
            "note": "A draft finding. Accepting creates it; nothing else does.",
        }

    if not _charts_for_run(db, case_id, run["id"]):
        x, measure = _chart_axes(run["columns"], run["rows"])
        if measure and x:
            return {
                "kind": "chart",
                "payload": {
                    "run_id": run["id"],
                    "kind": "bar",
                    "x": x,
                    "y": measure,
                },
                "source": "deterministic",
                "note": f"A bar chart of {measure} by {x} from the run.",
            }

    finding = findings[0]
    if finding["validation_status"] == "not_evaluated":
        return {
            "kind": "validate",
            "payload": {"finding_id": finding["id"], "run_id": run["id"]},
            "source": "deterministic",
            "note": "Rerun the stored computation and check its support.",
        }

    return None


def _audited_claims(db, case_id: str) -> set[tuple[str, str]]:
    """The (code, claim) pairs the reviewer has already examined.

    An evaluation records the code it ran and the claim it was offered to
    support, and stores the artifact as a run of its own - so its run_id is the
    audit's own artifact, not the finding's, and cannot be the join key. The
    code and the claim together are: they are exactly what the reviewer
    proposed, so matching them is a projection, and the reviewer cannot audit a
    finding twice without an evaluation existing, nor skip one by forgetting.
    """
    rows = db.execute(
        "SELECT code, claim FROM evaluations WHERE case_id = ?",
        (case_id,),
    ).fetchall()
    return {(row["code"], row["claim"]) for row in rows}


def _reviewer_step(db, case_id: str) -> dict | None:
    """The reviewer's whole decision procedure: audit what the case claims.

    It is deliberately small, and deliberately not the analyst's. The reviewer
    does not discover, does not propose queries and does not draft findings -
    it takes each finding the case has recorded and proposes the EVALUATE audit
    of the run that backs it. That a different agent with a different objective
    examines the analyst's output is the point of the role, and the reason the
    roadmap gated multi-agent work on EVALUATE existing at all.
    """
    audited = _audited_claims(db, case_id)
    rows = db.execute(
        "SELECT f.id AS finding_id, f.statement, f.run_id, f.validation_status, "
        "r.dataset_id, r.kind, r.sql, r.code "
        "FROM findings f JOIN runs r ON r.id = f.run_id "
        "WHERE f.case_id = ? ORDER BY f.created_at",
        (case_id,),
    ).fetchall()
    for row in rows:
        # A finding whose stored code is gone cannot be rerun for audit, so it
        # is skipped with the rest still considered rather than ending the run.
        code = row["sql"] if row["kind"] == "sql" else row["code"]
        if not code:
            continue
        if (code, row["statement"]) in audited:
            continue
        return {
            "kind": STEP_EVALUATE,
            "payload": {
                "dataset_id": row["dataset_id"],
                "run_id": row["run_id"],
                "finding_id": row["finding_id"],
                "kind": row["kind"],
                "code": code,
                "claim": row["statement"],
            },
            "source": "deterministic",
            "note": (
                "An audit of the finding this case recorded: the claim its own "
                "run was offered to support, judged on the nine axes."
            ),
        }
    return None


def next_step(db, case_id: str, role: str = ROLE_ANALYST) -> dict | None:
    """Derive the next step for this role from the case's artifacts.

    The dispatch is the whole of the orchestration: two objectives over one
    case, each reading the artifacts the other wrote. Neither writes anything
    without an approval.
    """
    if role == ROLE_REVIEWER:
        return _reviewer_step(db, case_id)
    return _analyst_step(db, case_id)

def _end_reason(db, case_id: str, role: str = ROLE_ANALYST) -> str | None:
    """Why this role has no next step, or None when its work is genuinely done."""
    if role == ROLE_REVIEWER:
        return _reviewer_end_reason(db, case_id)

    from app.workflow import case_progress

    progress = case_progress(db, case_id)
    if progress["loop_closed"]:
        return None
    dataset = _primary_dataset(db, case_id)
    if dataset is None:
        return "the case has no dataset attached; nothing to analyse"
    run = _latest_run(db, case_id)
    if _empty(run):
        attempts = _attempt_count(db, case_id, ROLE_ANALYST)
        if attempts >= _MAX_ATTEMPTS:
            return (
                f"{attempts} quer{'y' if attempts == 1 else 'ies'} returned no rows "
                "and no untried axis remains; the data may not answer this question"
            )
        return "no proposal could be generated for this dataset"
    return "the loop is open but the agent has no further automated step"


def _reviewer_end_reason(db, case_id: str) -> str | None:
    """The reviewer is done when every finding has been audited.

    A case with no findings is not a finished review - it is a case the
    analyst has not concluded yet, so the reviewer states what it is waiting
    for rather than claiming to be finished.
    """
    findings = db.execute(
        "SELECT COUNT(*) AS n FROM findings WHERE case_id = ?", (case_id,)
    ).fetchone()["n"]
    if findings == 0:
        return "the case has no findings yet; the reviewer audits what the analyst concludes"
    audited = _audited_claims(db, case_id)
    rows = db.execute(
        "SELECT f.statement, r.kind, r.sql, r.code "
        "FROM findings f JOIN runs r ON r.id = f.run_id "
        "WHERE f.case_id = ? ORDER BY f.created_at",
        (case_id,),
    ).fetchall()
    unaudited = [
        row
        for row in rows
        if (row["sql"] if row["kind"] == "sql" else row["code"], row["statement"])
        not in audited
    ]
    if not unaudited:
        return None
    return f"{len(unaudited)} finding{'s' if len(unaudited) == 1 else ''} remain to be audited"


def propose(db, case_id: str, role: str = ROLE_ANALYST) -> dict | None:
    """Record the next pending step, or leave the current one standing.

    Idempotent: a pending step is returned as-is, so calling this twice before
    an approval never produces two writes to choose from. When the loop is open
    but no step can be taken, an `end` row records the reason rather than
    leaving a caller to guess whether the agent is idle or finished.
    """
    pending = _pending(db, case_id, role)
    if pending is not None:
        return pending
    step = next_step(db, case_id, role)
    if step is None:
        reason = _end_reason(db, case_id, role)
        if reason is None:
            return None
        # An end row is a recorded conclusion, not work awaiting a decision, so
        # it is written already settled.
        step = _record(
            db, case_id, role, STEP_END, {"reason": reason}, "deterministic", reason
        )
        _decide(db, step["id"], STATUS_DONE, reason)
        return None
    return _record(
        db, case_id, role, step["kind"], step["payload"], step["source"],
        step.get("note", ""),
    )


def approve(db, case_id: str, step_id: str, role: str = ROLE_ANALYST) -> dict:
    """The human's yes. Refuses anything that is not this role's live step."""
    pending = _pending(db, case_id, role)
    if pending is None:
        raise ValueError("no pending step to approve")
    if pending["id"] != step_id:
        raise PendingStepError(step_id, pending["id"] if pending else None)
    return pending


class PendingStepError(Exception):
    """An approval id that does not match the case's current pending step."""

    def __init__(self, given: str, expected: str | None) -> None:
        self.given = given
        self.expected = expected
        super().__init__(
            f"step {given} is not the pending step "
            f"({expected if expected else 'none is pending'})"
        )


def reject(db, case_id: str, step_id: str, reason: str = "", role: str = ROLE_ANALYST) -> dict:
    """The human's no, recorded with their reason. Never a write."""
    pending = _pending(db, case_id, role)
    if pending is None:
        raise ValueError("no pending step to reject")
    if pending["id"] != step_id:
        raise PendingStepError(step_id, pending["id"])
    _decide(db, step_id, STATUS_REJECTED, reason or "rejected by the analyst")
    return pending


def settle(db, step_id: str, note: str = "") -> None:
    """Mark a write step completed, with whatever the write produced."""
    _decide(db, step_id, STATUS_DONE, note)


def state(db, case_id: str, role: str = ROLE_ANALYST) -> dict[str, Any]:
    """One role's whole position: its pending step and its audit trail."""
    return {
        "case_id": case_id,
        "role": role,
        "pending": _pending(db, case_id, role),
        "history": _history(db, case_id, role),
    }


def _chart_axes(columns: list[str], rows: list[list[Any]]) -> tuple[str | None, str | None]:
    """The x and y a bar chart of this result should use.

    Weaker than the drafter's notion on purpose: the drafter's dimension must
    *repeat* (a finding compares things, so a unique value is an identifier),
    but a chart of two categories is still worth drawing. The measure is the
    numeric column with the widest spread - `SUM(measure)` over `COUNT(*)` when
    both are present, because a bar chart of a constant count says nothing - and
    x is the first column that is not it, preferring a categorical one.
    """
    def is_number(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)

    # A column's position is what the positional rows actually index by, so it
    # is computed once here and reused by both branches below.
    indexes = {name: index for index, name in enumerate(columns)}

    def column_values(name: str) -> list[Any]:
        index = indexes[name]
        return [row[index] for row in rows if index < len(row)]

    numeric = [name for name in columns if any(map(is_number, column_values(name)))]
    if not numeric:
        return None, None

    def spread(name: str) -> float:
        values = [float(value) for value in column_values(name) if is_number(value)]
        return max(values) - min(values) if values else 0.0

    # `SUM(measure)` beats `COUNT(*)` when both are present: a bar chart of a
    # count that is constant across categories says nothing.
    measure = max(numeric, key=spread)
    others = [name for name in columns if name != measure]
    if not others:
        return None, None
    # A categorical x is what a bar chart is for; fall back to any other column.
    categorical = [
        name for name in others if not any(map(is_number, column_values(name)))
    ]
    return (categorical or others)[0], measure


def max_attempts() -> int:
    return _MAX_ATTEMPTS
