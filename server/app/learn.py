"""LEARN mode: the analytical process as a guided walk (P7-LEARN-001).

The Master Specification names three product modes. ANALYZE is the one that
exists - the workspace walks question -> data -> profile -> plan -> analyze ->
evidence -> validate, and `case_progress` (P3-FLOW-004) derives where the case
stands and names the single action that advances. LEARN is that same loop,
regrouped into the spec's four phases and explained:

    Why       why ask this at all, and why this data can answer it
      |       (question, data)
      v
    What      what the data actually contains, before you query it
      |       (profile, plan)
      v
    How       how a computation tests the question
      |       (analyze, evidence)
      v
    Validate  whether the answer survives being checked
              (validate)

This module is the mapping and the teaching. It is a read-side projection, like
evidence.py and history.py: it recomputes the walk from the artifact counts
workflow.py already derives, so it cannot drift from the case, and a learner
who deletes a dataset moves back as honestly as one who attached it. Nothing is
stored, and nothing is executed - LEARN sequences work the learner does through
the endpoints that already own it.

What the workflow does not say, and this does, is *why* each phase exists and
*what a learner should be able to answer* before leaving it. "Attach a dataset"
is an instruction; "know why this dataset can bear on your question" is the
education, and a prompt is what tests it.
"""

from typing import Any

from app.workflow import STAGES, _STAGE_ACTIONS, _counts, _stage_state

# The ladder: each LEARN phase over the ANALYZE stages it covers. The stages
# appear in the workflow's own order and each in exactly one phase, so the walk
# is the workflow regrouped rather than a second sequence the case could
# disagree with. The property is asserted by the test suite, not just intended.
LEARN_PHASES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("why", ("question", "data")),
    ("what", ("profile", "plan")),
    ("how", ("analyze", "evidence")),
    ("validate", ("validate",)),
)

# The teaching. The purpose is what the phase is for - the thing the workflow's
# "next action" never says. The prompt is the question a learner should be able
# to answer before moving on; answering it is what closes the phase, and the
# artifacts are what the answer rests on.
_PHASE_CONTENT: dict[str, dict[str, str]] = {
    "why": {
        "purpose": (
            "An analysis starts with a question worth answering, and a reason "
            "this data can answer it. Without both, the rest is motion without "
            "direction - so say what you want to know and how you would "
            "recognise the answer."
        ),
        "prompt": "What do you want to know, and why would this dataset know it?",
    },
    "what": {
        "purpose": (
            "Before querying, read what the data actually is: which columns "
            "carry which types, how many rows and duplicates there are, and "
            "what the shape of a question has to be for this data to hold it. "
            "A profile is what makes the plan honest."
        ),
        "prompt": "What is in this dataset - and what can it not tell you?",
    },
    "how": {
        "purpose": (
            "A question is tested by a computation: run the read-only query or "
            "script that would have to be true for the answer, then record the "
            "finding the result actually supports, with the evidence attached "
            "and a chart rendered from the same numbers a reader will check."
        ),
        "prompt": "What calculation would the data have to agree with?",
    },
    "validate": {
        "purpose": (
            "An answer is not finished when it is written. Rerun the stored "
            "computation and check the finding's support, so the claim is "
            "reproducible by someone who was not there when you made it."
        ),
        "prompt": "Does the finding still hold when the computation reruns?",
    },
}


def build_learn_walk(db, case_id: str) -> dict[str, Any]:
    """Project a case onto the LEARN ladder.

    Raises ValueError when the case does not exist, so the caller answers 404.
    """
    case = db.execute(
        "SELECT id, question FROM cases WHERE id = ?", (case_id,)
    ).fetchone()
    if case is None:
        raise ValueError("case not found")

    # The walk is derived, not stored: the same counts the workflow derives its
    # stage from, so the ladder can never claim a phase the artifacts do not
    # support.
    counts = _counts(db, case_id)
    completed = {stage for stage in STAGES if _stage_state(stage, counts)}

    steps: list[dict[str, Any]] = []
    for phase, stage_names in LEARN_PHASES:
        phase_complete = all(stage in completed for stage in stage_names)
        content = _PHASE_CONTENT[phase]
        steps.append(
            {
                "name": phase,
                "purpose": content["purpose"],
                "prompt": content["prompt"],
                "stages": [
                    {
                        "name": stage,
                        "completed": stage in completed,
                        "action": _STAGE_ACTIONS[stage]["action"],
                        "hint": _STAGE_ACTIONS[stage]["hint"],
                    }
                    for stage in stage_names
                ],
                "status": "pending",
                "complete": phase_complete,
            }
        )

    # The current phase is the first that is not finished; the phases after it
    # are pending, the ones before it complete. At most one phase is current -
    # a learner always has one thing to do next, never two.
    current_index = next(
        (i for i, step in enumerate(steps) if not step["complete"]), None
    )
    if current_index is None:
        for step in steps:
            step["status"] = "complete"
        current = None
        done = True
        next_action = None
        next_hint = None
        next_endpoint = None
    else:
        for i, step in enumerate(steps):
            step["status"] = (
                "complete" if i < current_index else
                "current" if i == current_index else "pending"
            )
        current = steps[current_index]["name"]
        # The action that advances is the workflow's own: the first incomplete
        # stage of the current phase, looked up in the same table the progress
        # endpoint reads, so there is one source of truth and no second copy.
        focus = next(
            stage
            for stage in steps[current_index]["stages"]
            if not stage["completed"]
        )
        action = _STAGE_ACTIONS[focus["name"]]
        next_action = action["action"]
        next_hint = action["hint"]
        next_endpoint = action["endpoint"].replace("{case_id}", case_id)
        done = False

    for step in steps:
        del step["complete"]

    return {
        "case_id": case_id,
        "question": case["question"],
        "steps": steps,
        "current": current,
        "next_action": next_action,
        "next_hint": next_hint,
        "next_endpoint": next_endpoint,
        "done": done,
    }
