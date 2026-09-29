"""Analysis Planner (P2-AI-011).

Turns a case question plus a dataset profile into a structured analysis plan:
an objective, a primary question, sub-questions, hypotheses, data requirements,
and concrete analysis steps. The plan is persisted state against the case, and
is what the rest of the loop (runs, findings, validation) is organised around.

Two engines sit behind one interface:

- `plan_analysis` is deterministic and always available. It derives the plan
  from the profile's actual structure - nulls, types, spreads, duplicates - so
  it bootstraps a real analysis loop without any external dependency.
- `LLMPlanner` calls an OpenAI-compatible endpoint when `DAH_LLM_API_KEY` is
  set. Its output is schema-validated by this module, and any failure - bad
  JSON, a schema violation, a network error - falls back to the deterministic
  plan rather than producing nothing. Per the Master Spec, critical state never
  depends on LLM output, so the persisted plan records which engine made it.

The LLM is an external engine the harness controls, not the other way round;
swapping it for another provider means implementing `plan(question, profile)`.
"""

import json
import logging
import os
from typing import Any

from app.timeouts import LLM_TIMEOUT_SECONDS

_MAX_SUB_QUESTIONS = 6
_MAX_HYPOTHESES = 5
_MAX_STEPS = 6
_MAX_LLM_CHARS = 12_000

SOURCE_DETERMINISTIC = "deterministic"
SOURCE_LLM = "llm"
SOURCE_DETERMINISTIC_FALLBACK = "deterministic fallback"
SOURCE_FALLBACK_SENTENCE = (
    "the LLM was unavailable, so a deterministic plan answered in its place"
)


def source_sentence(source: str) -> str:
    """The sentence a panel renders next to an engine's plan.

    A fallback is announced rather than labelled, so the analyst knows the plan
    they are reading is not the LLM's (FIX-TIMEOUT-006).
    """
    if source == SOURCE_DETERMINISTIC_FALLBACK:
        return SOURCE_FALLBACK_SENTENCE
    return f"by {source}"


def _column_names(profile: dict) -> list[str]:
    return list(profile.get("columns") or [])


def _stats(profile: dict) -> dict:
    return profile.get("stats") or {}


def _numeric_columns(profile: dict) -> list[str]:
    return [name for name in _column_names(profile) if _stats(profile).get(name, {}).get("type") == "numeric"]


def _temporal_columns(profile: dict) -> list[str]:
    return [name for name in _column_names(profile) if _stats(profile).get(name, {}).get("type") == "temporal"]


def _categorical_columns(profile: dict) -> list[str]:
    return [
        name
        for name in _column_names(profile)
        if _stats(profile).get(name, {}).get("type") == "other"
    ]


def _null_columns(profile: dict) -> list[tuple[str, float]]:
    """Columns with any nulls, most-null first."""
    return sorted(
        (
            (name, float(stat.get("null_percentage") or 0))
            for name, stat in _stats(profile).items()
            if (stat.get("null_count") or 0) > 0
        ),
        key=lambda pair: pair[1],
        reverse=True,
    )


# The analyst's stated intent outranks the derivation when both are available:
# their sub-questions and hypotheses are prepended to the ones the profile
# suggests, and their purpose stands in for a thin objective. `context_basis`
# is recorded so a reader can tell a plan built from intent from one built from
# a profile alone (P8-CONTEXT-001).
_CONTEXT_SUB_QUESTIONS = 3
_CONTEXT_HYPOTHESES = 2


def plan_analysis(question: str, profile: dict, context: dict | None = None) -> dict:
    """Derive a structured plan from a question and a dataset profile.

    Deterministic and dependency-free: the same inputs always yield the same
    plan. Every item references real columns from the profile, so the plan is
    immediately actionable rather than generic advice.

    `context` is the case's stated intent - purpose, sub-questions, hypotheses -
    and is optional: a case without it is planned from the profile alone, which
    is every plan that existed before the context object did.
    """
    question = (question or "").strip()
    basis: list[str] = []
    context = context or {}
    purpose = (context.get("purpose") or "").strip()
    context_subs = [
        item.strip() for item in (context.get("sub_questions") or []) if isinstance(item, str) and item.strip()
    ]
    context_hyps = [
        item.strip() for item in (context.get("hypotheses") or []) if isinstance(item, str) and item.strip()
    ]
    stats = _stats(profile)
    numeric = _numeric_columns(profile)
    temporal = _temporal_columns(profile)
    categorical = _categorical_columns(profile)
    nulls = _null_columns(profile)
    rows = int(profile.get("rows") or 0)
    duplicates = int(profile.get("duplicate_rows") or 0)

    sub_questions: list[str] = []
    hypotheses: list[dict] = []
    steps: list[dict] = []

    def add_sub_question(text: str) -> None:
        if len(sub_questions) < _MAX_SUB_QUESTIONS and text not in sub_questions:
            sub_questions.append(text)

    def add_hypothesis(statement: str, rationale: str, check: str) -> None:
        if len(hypotheses) < _MAX_HYPOTHESES:
            hypotheses.append(
                {"statement": statement, "rationale": rationale, "check": check}
            )

    def add_step(action: str, detail: str) -> None:
        if len(steps) < _MAX_STEPS:
            steps.append({"action": action, "detail": detail})

    # Missingness: the most common reason an analysis of this data would lie.
    for column, percentage in nulls[:2]:
        add_sub_question(
            f"How does missingness in {column} affect the answer, and is it random?"
        )
        add_hypothesis(
            f"Missing values in {column} are concentrated in particular rows rather "
            f"than spread evenly ({percentage}% null)",
            f"{column} is {percentage}% null; non-random missingness biases any "
            "aggregate that ignores it",
            f"Compare the distribution of other columns between rows where {column} "
            "is null and rows where it is not",
        )

    # Numeric columns: spread and outliers drive aggregates.
    for column in numeric[:2]:
        stat = stats.get(column) or {}
        add_sub_question(f"What is the distribution of {column}, and does it contain outliers?")
        add_hypothesis(
            f"A small number of extreme values in {column} dominate its aggregate",
            f"{column} spans {stat.get('min')} to {stat.get('max')} with an average of "
            f"{stat.get('avg')}",
            f"Rank rows by {column} and report the share of the total held by the "
            "top few rows",
        )
        add_step("distribution", f"Profile {column}: histogram, percentiles, top contributors")

    # A categorical split is the natural dimension for a "why did X change" question.
    if categorical:
        column = categorical[0]
        distinct = (stats.get(column) or {}).get("distinct_count") or 0
        add_sub_question(f"How does the answer differ across {column}?")
        add_hypothesis(
            f"The effect behind the question is not uniform across {column}",
            f"{column} has {distinct} distinct value(s) and rows totalling {rows}",
            f"Group the rows by {column} and compare the measure of interest per group",
        )
        add_step("grouped comparison", f"Aggregate the measure per {column} and rank the groups")

    # A date column makes a trend the strongest first hypothesis.
    if temporal:
        column = temporal[0]
        add_sub_question(f"How does the measure move over time by {column}?")
        add_hypothesis(
            f"The change behind the question is a trend in {column} rather than a "
            "one-off shift",
            f"{column} is a temporal column spanning {(stats.get(column) or {}).get('min')}"
            f" to {(stats.get(column) or {}).get('max')}",
            f"Sort by {column} and plot the measure per period",
        )
        add_step("trend", f"Sort by {column} and compare the measure across periods")

    if len(numeric) >= 2:
        first, second = numeric[0], numeric[1]
        add_sub_question(f"How are {first} and {second} related?")
        add_hypothesis(
            f"{first} and {second} move together, but the link may be confounded",
            "Both are numeric; correlation is cheap to compute and easy to over-read",
            f"Compute the correlation of {first} and {second}, then check whether a "
            "third column explains it",
        )

    if duplicates:
        add_hypothesis(
            f"{duplicates} duplicate row(s) inflate the totals",
            f"{duplicates} of {rows} row(s) are exact duplicates of an earlier row",
            "Deduplicate on all columns and recompute the headline aggregate",
        )
        add_step("deduplicate", f"Recompute the headline aggregate on distinct rows only")

    # The plan always proposes the direct measurement of the question itself.
    add_step(
        "answer the primary question",
        "Compute the headline measure directly, then decompose it by the "
        "dimension that varies most",
    )

    data_requirements = [
        {"requirement": "columns", "detail": ", ".join(_column_names(profile)) or "none profiled"},
        {"requirement": "rows", "detail": f"{rows} row(s), {duplicates} duplicate row(s)"},
    ]
    for column, percentage in nulls[:3]:
        data_requirements.append(
            {"requirement": "completeness", "detail": f"{column}: {percentage}% null"}
        )

    objective = question or "Analyse the attached dataset"
    primary_question = question or "What does this dataset say?"
    if not question and purpose:
        # A case whose question is thin but whose purpose is stated is planned
        # for what the analyst said they were after.
        objective = purpose
        basis.append("purpose")
    elif purpose:
        basis.append("purpose")

    # The analyst's own sub-questions and hypotheses come first, ahead of the
    # ones the profile suggests - intent outranks inference.
    if context_subs:
        basis.append(f"sub_questions:{len(context_subs)}")
    if context_hyps:
        basis.append(f"hypotheses:{len(context_hyps)}")

    return {
        "objective": objective,
        "primary_question": primary_question,
        "sub_questions": (
            context_subs[:_CONTEXT_SUB_QUESTIONS]
            + [item for item in sub_questions if item not in context_subs[:_CONTEXT_SUB_QUESTIONS]]
        ) or ["What does the profiled data contain, and what is its overall shape?"],
        "hypotheses": (
            [
                {"statement": text, "rationale": "the analyst's own hypothesis",
                 "check": "Test it directly against the profiled data"}
                for text in context_hyps[:_CONTEXT_HYPOTHESES]
            ]
            + hypotheses
        ) or [
            {
                "statement": "The answer is concentrated in a small subset of the data",
                "rationale": "No specific structure surfaced in the profile to anchor a "
                "stronger hypothesis",
                "check": "Rank rows by the measure of interest and report the share held "
                "by the top few",
            }
        ],
        "data_requirements": data_requirements,
        "analysis_steps": steps,
        "context_basis": basis,
    }


def validate_plan(plan: Any) -> list[str]:
    """Check a plan (from any engine) against the contract before persisting.

    Returns the list of problems; empty means the plan is fit to persist. This
    is the harness-validation step in the AI context strategy - an LLM that
    returns malformed output never reaches the database.
    """
    problems: list[str] = []
    if not isinstance(plan, dict):
        return ["plan must be a JSON object"]

    for field in ("objective", "primary_question"):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            problems.append(f"'{field}' must be a non-empty string")

    for field in ("sub_questions", "hypotheses", "data_requirements", "analysis_steps"):
        value = plan.get(field)
        if not isinstance(value, list):
            problems.append(f"'{field}' must be a list")
            continue
        if field == "sub_questions":
            for item in value:
                if not isinstance(item, str) or not item.strip():
                    problems.append("every sub-question must be a non-empty string")
        else:
            for item in value:
                if not isinstance(item, dict):
                    problems.append(f"every entry in '{field}' must be an object")

    for hypothesis in plan.get("hypotheses") or []:
        if isinstance(hypothesis, dict):
            for field in ("statement", "rationale", "check"):
                if not isinstance(hypothesis.get(field), str) or not hypothesis[field].strip():
                    problems.append(f"every hypothesis must have a non-empty '{field}'")

    for step in plan.get("analysis_steps") or []:
        if isinstance(step, dict):
            for field in ("action", "detail"):
                if not isinstance(step.get(field), str) or not step[field].strip():
                    problems.append(f"every analysis step must have a non-empty '{field}'")

    # The record of which context fields the plan was built from (P8-CONTEXT-001).
    # Optional - a plan made before the context object existed has none - but a
    # malformed one is a problem rather than something to silently drop.
    basis = plan.get("context_basis")
    if basis is not None:
        if not isinstance(basis, list):
            problems.append("'context_basis' must be a list")
        else:
            for item in basis:
                if not isinstance(item, str) or not item.strip():
                    problems.append("every entry in 'context_basis' must be a non-empty string")

    return problems


class LLMPlanner:
    """OpenAI-compatible planner; dormant without configuration.

    Implemented on httpx so no SDK dependency is added. The response is expected
    to be the plan object itself; anything else is a validation failure and the
    caller falls back to the deterministic plan.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def plan(self, question: str, profile: dict, context: dict | None = None) -> dict:
        import httpx

        prompt = self.prompt(question, profile, context)
        response = httpx.post(
            f"{self._base_url}/chat/completions",
            headers={
                "authorization": f"Bearer {self._api_key}",
                "content-type": "application/json",
            },
            json={
                "model": self._model,
                "messages": [
                    {"role": "system", "content": "Return valid JSON only, no prose."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)

    def prompt(self, question: str, profile: dict, context: dict | None = None) -> str:
        """The prompt `plan` posts, on its own so a measurement can time it.

        W3X-003-PROMPT: the prompt's requested output is the cost (the provider
        generates at ~13 completion tokens per second, so 1785 tokens is ~137s
        against a 120s timeout), so the prompt is what a measurement holds and
        a test pins. The caps below are a *request*, not the validator's
        ceilings: the deterministic planner and `validate_plan` still accept
        up to `_MAX_SUB_QUESTIONS / _MAX_HYPOTHESES / _MAX_STEPS`, so asking
        the LLM for less shrinks the wait without shrinking what is accepted.
        """
        return (
            "You are an analysis planner. Given a question and a dataset profile, "
            "return ONLY a JSON object with this exact schema:\n"
            "{\n"
            '  "objective": string,\n'
            '  "primary_question": string,\n'
            '  "sub_questions": [string],\n'
            '  "hypotheses": [{"statement": string, "rationale": string, "check": string}],\n'
            '  "data_requirements": [{"requirement": string, "detail": string}],\n'
            '  "analysis_steps": [{"action": string, "detail": string}]\n'
            "}\n"
            "Reference real column names from the profile. Do not add fields or "
            "commentary.\n"
            "Keep it short: at most 4 sub_questions, 3 hypotheses, 4 analysis_steps "
            "and 3 data_requirements, and every string one short clause - a "
            "sentence at most, never a paragraph.\n\n"
            f"Question: {question}\n\n"
            f"Profile (truncated): {json.dumps(profile)[:_MAX_LLM_CHARS]}\n"
            + (f"Stated intent: {json.dumps(context)}\n" if context else "")
        )


def _configured_llm() -> LLMPlanner | None:
    """The configured planner, or None when no key is present."""
    api_key = os.environ.get("DAH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return LLMPlanner(
        api_key=api_key,
        base_url=os.environ.get("DAH_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("DAH_LLM_MODEL", "gpt-4o-mini"),
    )


def _basis_for(context: dict | None) -> list[str]:
    """Which fields of stated intent a plan was built from.

    Named the same way the deterministic planner names them, so a reader cannot
    tell from the field which engine spoke - only from `source`.
    """
    context = context or {}
    basis: list[str] = []
    if (context.get("purpose") or "").strip():
        basis.append("purpose")
    subs = [s for s in (context.get("sub_questions") or []) if isinstance(s, str) and s.strip()]
    if subs:
        basis.append(f"sub_questions:{len(subs)}")
    hyps = [h for h in (context.get("hypotheses") or []) if isinstance(h, str) and h.strip()]
    if hyps:
        basis.append(f"hypotheses:{len(hyps)}")
    return basis


def create_plan(question: str, profile: dict, context: dict | None = None) -> tuple[dict, str]:
    """Produce a validated plan and the engine that made it.

    Prefers the LLM when configured; falls back to the deterministic planner on
    any failure, so a plan is always returned. The source is reported alongside
    so callers and reviewers know how much trust the plan earns. `context` is
    the case's stated intent, passed to the deterministic planner; the LLM
    prompt carries it too so an engine that can use intent is not asked to
    guess at it. Whichever engine answers, the basis records what intent the
    caller supplied - it describes the question asked, not the engine asked.
    """
    deterministic = plan_analysis(question, profile, context)
    llm = _configured_llm()
    if llm is None:
        return deterministic, SOURCE_DETERMINISTIC

    try:
        candidate = llm.plan(question, profile, context)
        # An engine that used the intent should say so on the same field the
        # deterministic one uses; one that ignored it records nothing, which is
        # also true.
        if isinstance(candidate, dict):
            supplied = _basis_for(context)
            if supplied and not candidate.get("context_basis"):
                candidate["context_basis"] = supplied
        problems = validate_plan(candidate)
        if problems:
            raise ValueError(f"LLM plan failed validation: {'; '.join(problems[:3])}")
        return candidate, SOURCE_LLM
    except Exception as error:
        # An unavailable or misbehaving LLM degrades to the deterministic
        # plan rather than producing nothing. The breadth stays - the contract
        # is "any failure falls back" - but the reason is logged, so a fallback
        # caused by a bug in our own code surfaces instead of vanishing into
        # source=deterministic (P4-RELIABILITY-002). The source carries it too:
        # the panel's own label is what tells the analyst the engine they
        # configured did not answer and another one did (FIX-TIMEOUT-006).
        logging.getLogger(__name__).warning(
            "llm plan failed; falling back to deterministic: %s", error,
        )
        return deterministic, SOURCE_DETERMINISTIC_FALLBACK
