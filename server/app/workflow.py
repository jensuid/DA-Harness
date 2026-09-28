"""Guided analysis workflow (P3-FLOW-004).

The Master Specification's core loop is a sequence, not a menu:

    question -> data -> profile -> plan -> analyze -> evidence -> validate

Rather than storing a stage column that can fall out of sync with reality, the
stage is *derived* from the artifacts a case actually has. `case_progress`
counts datasets, profiles, plans, runs, charts and findings and reports the
first stage with nothing behind it, plus the deterministic next action.

That makes the workflow honest by construction: an endpoint cannot report a
stage the data does not support, and deleting an artifact moves the case back.
"""

from typing import Any

STAGES = (
    "question",
    "data",
    "profile",
    "plan",
    "analyze",
    "evidence",
    "validate",
)

# The action that closes each stage, and the endpoint that performs it. The
# dependency is what the UI surfaces as "do this next"; the endpoints that
# enforce it (plan needs a profile) already answer 400 without it.
_STAGE_ACTIONS: dict[str, dict[str, str]] = {
    "question": {
        "action": "Refine the analytical question",
        "hint": "State what you want to know and how you would know it.",
        "endpoint": "PATCH /cases/{case_id}",
    },
    "data": {
        "action": "Attach a dataset",
        "hint": "CSV, Parquet or Excel - the engine reads all three.",
        "endpoint": "POST /cases/{case_id}/datasets",
    },
    "profile": {
        "action": "Profile every attached dataset",
        "hint": "Profiling is what the planner and the missing-data check read.",
        "endpoint": "POST /cases/{case_id}/datasets/{dataset_id}/profile",
    },
    "plan": {
        "action": "Generate an analysis plan",
        "hint": "Sub-questions and hypotheses derived from the profile.",
        "endpoint": "POST /cases/{case_id}/datasets/{dataset_id}/plan",
    },
    "analyze": {
        "action": "Run an analysis",
        "hint": "SQL or Python, single- or multi-dataset.",
        "endpoint": "POST /cases/{case_id}/datasets/{dataset_id}/runs",
    },
    "evidence": {
        "action": "Attach evidence to a finding",
        "hint": "Record a finding against a run, and render a chart from it.",
        "endpoint": "POST /cases/{case_id}/findings",
    },
    "validate": {
        "action": "Validate a finding",
        "hint": "Rerun the stored computation and check its support.",
        "endpoint": "POST /cases/{case_id}/findings/{finding_id}/validate",
    },
}


def _counts(db, case_id: str) -> dict[str, int]:
    """How much of each artifact the case has right now."""
    datasets = db.execute(
        "SELECT COUNT(*) AS n FROM datasets WHERE case_id = ?", (case_id,)
    ).fetchone()["n"]
    profiles = db.execute(
        "SELECT COUNT(*) AS n FROM profiles WHERE dataset_id IN "
        "(SELECT id FROM datasets WHERE case_id = ?)",
        (case_id,),
    ).fetchone()["n"]
    plans = db.execute(
        "SELECT COUNT(*) AS n FROM plans WHERE case_id = ?", (case_id,)
    ).fetchone()["n"]
    runs = db.execute(
        "SELECT COUNT(*) AS n FROM runs WHERE case_id = ?", (case_id,)
    ).fetchone()["n"]
    findings = db.execute(
        "SELECT COUNT(*) AS n FROM findings WHERE case_id = ?", (case_id,)
    ).fetchone()["n"]
    charts = db.execute(
        "SELECT COUNT(*) AS n FROM charts WHERE case_id = ?", (case_id,)
    ).fetchone()["n"]
    validated = db.execute(
        "SELECT COUNT(*) AS n FROM findings WHERE case_id = ? "
        "AND validation_status != 'not_evaluated'",
        (case_id,),
    ).fetchone()["n"]
    supported = db.execute(
        "SELECT COUNT(*) AS n FROM findings WHERE case_id = ? "
        "AND validation_status IN ('supported', 'partially_supported')",
        (case_id,),
    ).fetchone()["n"]
    return {
        "datasets": datasets,
        "profiles": profiles,
        "plans": plans,
        "runs": runs,
        "findings": findings,
        "charts": charts,
        "validated_findings": validated,
        "supported_findings": supported,
    }


def _stage_state(stage: str, counts: dict[str, int]) -> bool:
    """Whether the case has at least one artifact behind this stage."""
    if stage == "question":
        return True  # a case row exists with a question
    if stage == "data":
        return counts["datasets"] > 0
    if stage == "profile":
        return counts["datasets"] > 0 and counts["profiles"] == counts["datasets"]
    if stage == "plan":
        return counts["plans"] > 0
    if stage == "analyze":
        return counts["runs"] > 0
    if stage == "evidence":
        return counts["findings"] > 0 and counts["charts"] > 0
    if stage == "validate":
        return counts["validated_findings"] > 0
    return False


def case_progress(db, case_id: str) -> dict[str, Any]:
    """The case's position in the workflow and the action that moves it.

    `stage` is the first stage without an artifact - the current focus. Every
    stage before it is listed in `completed`. The loop is closed when a finding
    has been validated; `loop_closed` says so without claiming the analysis is
    right, only that the trust loop ran.
    """
    counts = _counts(db, case_id)
    completed = [stage for stage in STAGES if _stage_state(stage, counts)]
    current = next(
        (stage for stage in STAGES if stage not in completed),
        None,
    )

    if current is None:
        return {
            "stage": "validated",
            "completed": list(STAGES),
            "next_action": None,
            "next_hint": None,
            "next_endpoint": None,
            "loop_closed": True,
            "counts": counts,
        }

    action = _STAGE_ACTIONS[current]
    # W2X-005: a `{dataset_id}` the case cannot fill read as a bug, so the
    # first attached dataset is substituted where the endpoint needs one. When
    # the stage is before any dataset exists the placeholder is dropped rather
    # than shown unfilled - the developer reading it still gets the path's
    # shape from the routes that take only the case.
    first_dataset = next(
        (
            row["id"]
            for row in db.execute(
                "SELECT id FROM datasets WHERE case_id = ? ORDER BY created_at LIMIT 1",
                (case_id,),
            ).fetchall()
        ),
        None,
    )
    endpoint = action["endpoint"].replace("{case_id}", case_id)
    if "{dataset_id}" in endpoint:
        endpoint = (
            endpoint.replace("{dataset_id}", first_dataset)
            if first_dataset
            else endpoint.replace("/{dataset_id}", "")
        )
    return {
        "stage": current,
        "completed": completed,
        "next_action": action["action"],
        "next_hint": action["hint"],
        "next_endpoint": endpoint,
        "loop_closed": False,
        "counts": counts,
    }
