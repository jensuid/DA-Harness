"""Finding drafter (P3-AI-012, contextual AI slice 2).

Drafts the *candidate* finding a persisted result would support, and stops one
step short of creating it. A finding is the trust artifact - it is what the
evidence chain, validation and export stand on - so the LLM proposes and a
human disposes. This module never writes a row to findings; acceptance is a POST
to the endpoint that already exists, which is what keeps that property
structural rather than a flag.

Two engines sit behind one interface, as in the planner (P2-AI-011) and the
interpreter (P3-AI-011):

- `draft_finding` is deterministic and always available. It looks for the
  result's measure and dimension and states which category leads on the measure
  at what value, computing every figure from the persisted rows.
- `LLMDrafter` calls an OpenAI-compatible endpoint when `DAH_LLM_API_KEY` is
  set. Its output is schema-validated here, and - the part that matters for a
  finding - every number it quotes in its statement or grounds must be a value
  the result actually contains. An invented magnitude is a validation failure
  and the draft falls back to the deterministic one.

The LLM is an external engine the harness controls, not the other way round;
swapping provider means implementing `draft(question, run, profile)`.
"""

import json
import os
import re
from typing import Any

_MAX_GROUNDS = 5
_MAX_LLM_CHARS = 12_000
_MAX_ROWS_IN_PROMPT = 25

SOURCE_DETERMINISTIC = "deterministic"
SOURCE_LLM = "llm"

_NUMBER_RE = re.compile(r"-?\d+(?:\.\d+)?")


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _column_values(columns: list[str], rows: list[list[Any]]) -> dict[str, list[Any]]:
    """Every value a column actually carries, in row order."""
    return {
        name: [row[index] if index < len(row) else None for row in rows]
        for index, name in enumerate(columns)
    }


def _measure_and_dimension(columns: list[str], rows: list[list[Any]]):
    """The result's numeric measure and its widest categorical dimension.

    A finding compares things, so the useful shape is one measure against one
    grouping. The measure is the first numeric column; the dimension is the
    first column that repeats a value (a real grouping, not an identifier).
    """
    by_column = _column_values(columns, rows)
    measure = next(
        (name for name, values in by_column.items() if any(_is_number(v) for v in values)),
        None,
    )
    dimension = next(
        (
            name
            for name, values in by_column.items()
            if name != measure and len(set(v for v in values if v is not None)) < len(
                [v for v in values if v is not None]
            )
        ),
        None,
    )
    return measure, dimension


def _fmt(value: Any) -> str:
    if isinstance(value, float) and value.is_integer():
        return f"{value:.1f}"
    return str(value)


def draft_finding(
    question: str,
    kind: str,
    source_text: str | None,
    columns: list[str],
    rows: list[list[Any]],
    profile: dict | None,
    truncated: bool = False,
) -> dict:
    """Draft a candidate finding from a persisted result, deterministically.

    Every figure the draft quotes is computed from `rows`, so the draft cannot
    invent a magnitude. When the result has no measure to compare, the draft
    says so plainly rather than dressing an observation up as a claim.
    """
    question = (question or "").strip()
    by_column = _column_values(columns, rows)
    row_count = len(rows)
    measure, dimension = _measure_and_dimension(columns, rows)

    if measure is not None and dimension is not None:
        pairs = [
            (row[columns.index(dimension)], row[columns.index(measure)])
            for row in rows
            if _is_number(row[columns.index(measure)])
        ]
        leader, best = max(pairs, key=lambda pair: pair[1])
        lowest = min(value for _, value in pairs)
        n_groups = len(pairs)

        statement = (
            f"{_fmt(leader)} has the highest {measure} at {_fmt(best)}, "
            f"the largest of {n_groups} grouped value(s)"
        )
        interpretation = (
            f"the result's {measure} is greatest for {dimension} "
            f"{_fmt(leader)}; every other group is lower, down to {_fmt(lowest)}"
        )
        grounds = [
            f"{measure} = {_fmt(best)} for {dimension} = {_fmt(leader)}",
            f"{n_groups} group(s) of {measure}, lowest {_fmt(lowest)}",
        ]
        caveat = (
            "a single aggregated view; rerun and validate before this carries weight"
        )
    elif measure is not None:
        values = [v for v in by_column[measure] if _is_number(v)]
        statement = (
            f"{measure} spans {_fmt(min(values))} to {_fmt(max(values))} "
            f"across {row_count} row(s)"
        )
        interpretation = (
            f"the result's {measure} varies between {_fmt(min(values))} and "
            f"{_fmt(max(values))}, but the result names no dimension to "
            "attribute the spread to"
        )
        grounds = [
            f"{measure} ranges {_fmt(min(values))}..{_fmt(max(values))}",
            f"{row_count} row(s) in the result",
        ]
        caveat = (
            "a range is an observation, not a comparison; no grouping is present "
            "to explain it"
        )
    else:
        statement = (
            f"the result carries no numeric measure across {len(columns)} "
            f"column(s) over {row_count} row(s), so it supports no quantitative "
            "claim"
        )
        interpretation = (
            "no column in the result is numeric, so there is nothing to compare "
            "or rank"
        )
        grounds = [f"{len(columns)} column(s), {row_count} row(s)"]
        caveat = "this result cannot ground a quantitative finding as it stands"

    if truncated:
        caveat += "; the result was capped, so these figures describe only the rows kept"

    profile = profile or {}
    null_columns = [
        name
        for name, stat in (profile.get("stats") or {}).items()
        if (stat.get("null_count") or 0) > 0 and name in columns
    ]
    if null_columns:
        caveat += f"; the profiled data has nulls in {', '.join(null_columns[:3])}"

    return {
        "statement": statement,
        "interpretation": interpretation,
        "caveat": caveat,
        "grounds": grounds[:_MAX_GROUNDS],
    }


def _numbers_in(text: str) -> set[float]:
    """Every numeric token a piece of text quotes."""
    return {float(match) for match in _NUMBER_RE.findall(text)}


def _allowed_numbers(
    columns: list[str], rows: list[list[Any]], row_count: int
) -> set[float]:
    """The numbers a draft may legitimately quote: cell values and derived counts.

    This is the honesty budget. Anything a draft states as a magnitude has to be
    reachable from the result itself - a cell, the row count, or how often a
    value repeats - so an invented figure cannot slip into a finding's grounds.
    """
    allowed: set[float] = {float(row_count), float(len(columns))}
    for row in rows:
        for value in row:
            if _is_number(value):
                allowed.add(float(value))
    by_column = _column_values(columns, rows)
    for values in by_column.values():
        counts: dict[Any, int] = {}
        for value in values:
            if value is None:
                continue
            counts[value] = counts.get(value, 0) + 1
        for how_often in counts.values():
            allowed.add(float(how_often))
        allowed.add(float(len(counts)))
    return allowed


def validate_draft(payload: Any, columns: list[str], rows: list[list[Any]]) -> list[str]:
    """Problems with an LLM draft, as a list. Empty means acceptable.

    Beyond shape, every number in the statement and the grounds must be one the
    result actually contains - a draft that invents a magnitude is a draft that
    cannot be trusted as the basis of a finding.
    """
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["the draft must be a JSON object"]
    for field in ("statement", "interpretation", "caveat"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"'{field}' must be a non-empty string")
    grounds = payload.get("grounds")
    if isinstance(grounds, str):
        problems.append("'grounds' must be a list of strings, not a string")
    elif grounds is not None and not isinstance(grounds, list):
        problems.append("'grounds' must be a list of strings")
    elif isinstance(grounds, list) and not all(
        isinstance(item, str) and item.strip() for item in grounds
    ):
        problems.append("every entry in 'grounds' must be a non-empty string")

    row_count = len(rows)
    quoted = set(_numbers_in(payload.get("statement") or ""))
    for item in grounds if isinstance(grounds, list) else []:
        quoted |= _numbers_in(item)
    allowed = _allowed_numbers(columns, rows, row_count)
    invented = {value for value in quoted if value not in allowed}
    if invented:
        problems.append(
            "the draft quotes values absent from the result: "
            + ", ".join(sorted(_fmt(v) for v in invented))
        )
    return problems


class LLMDrafter:
    """OpenAI-compatible drafter; dormant without configuration.

    Implemented on httpx so no SDK dependency is added. The response is expected
    to be the draft object itself; anything else is a validation failure and the
    caller falls back to the deterministic draft.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def draft(
        self,
        question: str,
        kind: str,
        source_text: str | None,
        columns: list[str],
        rows: list[list[Any]],
        profile: dict | None,
    ) -> dict:
        import httpx

        prompt_rows = rows[:_MAX_ROWS_IN_PROMPT]
        prompt = (
            "You are a data analyst's drafter. Given a question, the query or "
            "script that produced a result, and the result itself, draft the "
            "finding the result would support - a claim a human will decide "
            "whether to keep. Return ONLY a JSON object with this exact schema:\n"
            "{\n"
            '  "statement": string,\n'
            '  "interpretation": string,\n'
            '  "caveat": string,\n'
            '  "grounds": [string]\n'
            "}\n"
            "`grounds` lists the specific values from the result that the "
            "statement stands on. Quote no number that does not appear in the "
            "result. Do not add fields or commentary.\n\n"
            f"Question: {question or '(none given)'}\n\n"
            f"Run kind: {kind}\n"
            f"Query or script:\n{source_text or '(none recorded)'}\n\n"
            f"Columns: {json.dumps(columns)}\n"
            f"Rows (truncated to {_MAX_ROWS_IN_PROMPT}): "
            f"{json.dumps(prompt_rows, default=str)[:_MAX_LLM_CHARS]}\n"
        )
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
                "response_format": {"type": "json_object"},
            },
            timeout=30.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        return json.loads(content)


def _configured_llm() -> "LLMDrafter | None":
    """The configured drafter, or None when no key is present."""
    api_key = os.environ.get("DAH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return LLMDrafter(
        api_key=api_key,
        base_url=os.environ.get("DAH_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("DAH_LLM_MODEL", "gpt-4o-mini"),
    )


def create_draft(
    question: str,
    kind: str,
    source_text: str | None,
    columns: list[str],
    rows: list[list[Any]],
    profile: dict | None,
    truncated: bool = False,
) -> tuple[dict, str]:
    """Produce a validated draft and the engine that made it.

    Prefers the LLM when configured; falls back to the deterministic draft on
    any failure - an unavailable LLM, malformed output, a schema violation, or a
    magnitude the result does not contain - so a draft is always returned and
    the source says which engine spoke.
    """
    deterministic = draft_finding(
        question, kind, source_text, columns, rows, profile, truncated=truncated
    )
    llm = _configured_llm()
    if llm is None:
        return deterministic, SOURCE_DETERMINISTIC

    try:
        candidate = llm.draft(question, kind, source_text, columns, rows, profile)
        problems = validate_draft(candidate, columns, rows)
        if problems:
            raise ValueError(
                f"LLM draft failed validation: {'; '.join(problems[:3])}"
            )
        candidate.setdefault("grounds", [])
        return candidate, SOURCE_LLM
    except Exception:
        # An unavailable or misbehaving LLM degrades to the deterministic draft
        # rather than producing nothing.
        return deterministic, SOURCE_DETERMINISTIC
