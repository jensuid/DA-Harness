"""Result interpreter (P3-AI-011, contextual AI slice 1).

Turns a persisted run result into a plain-language read: what the result shows,
observations grounded in the result's own numbers, and the caveats a reviewer
should weigh. The loop could already run, chart, validate and export a result;
reading one still meant re-deriving it from a table.

Two engines sit behind one interface, exactly as the planner (P2-AI-011) does:

- `interpret_result` is deterministic and always available. It computes from
  the result's own rows - row counts, numeric min/max/mean, the most frequent
  value of a text column - so every observation cites a value that is really
  there.
- `LLMInterpreter` calls an OpenAI-compatible endpoint when `DAH_LLM_API_KEY`
  is set. Its output is schema-validated by this module, and any failure - bad
  JSON, a schema violation, a network error - falls back to the deterministic
  read rather than producing nothing. Critical state never depends on LLM
  output, so the persisted interpretation records which engine spoke.

The LLM is an external engine the harness controls, not the other way round;
swapping provider means implementing `interpret(question, run, profile)`.
"""

import json
import logging
import os
from typing import Any

_MAX_OBSERVATIONS = 4
_MAX_CAVEATS = 3
_MAX_LLM_CHARS = 12_000
_MAX_ROWS_IN_PROMPT = 25

SOURCE_DETERMINISTIC = "deterministic"
SOURCE_LLM = "llm"


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _column_stats(columns: list[str], rows: list[list[Any]]) -> dict[str, dict]:
    """Per-column summary computed from the result's own rows.

    Numbers get min/max/mean; anything else gets its most frequent value. This
    is what keeps an interpretation honest: every figure it quotes is one the
    persisted result actually contains.
    """
    stats: dict[str, dict] = {}
    for index, name in enumerate(columns):
        values = [row[index] if index < len(row) else None for row in rows]
        numbers = [v for v in values if _is_number(v)]
        if numbers:
            stats[name] = {
                "kind": "numeric",
                "min": min(numbers),
                "max": max(numbers),
                "mean": sum(numbers) / len(numbers),
                "count": len(numbers),
            }
            continue
        counts: dict[Any, int] = {}
        for value in values:
            if value is None:
                continue
            counts[value] = counts.get(value, 0) + 1
        if counts:
            top, how_often = max(counts.items(), key=lambda pair: pair[1])
            stats[name] = {
                "kind": "categorical",
                "top": top,
                "count": how_often,
                "distinct": len(counts),
            }
    return stats


def _fmt(value: Any) -> str:
    """Render a value the way it appears in the result."""
    if isinstance(value, float) and value.is_integer():
        return f"{value:.1f}"
    return str(value)


def interpret_result(
    question: str,
    kind: str,
    source_text: str | None,
    columns: list[str],
    rows: list[list[Any]],
    profile: dict | None,
    truncated: bool = False,
) -> dict:
    """Read a persisted result deterministically.

    The same inputs always yield the same interpretation, and every figure it
    quotes is computed from `rows` - so the interpretation can never invent a
    number the result does not contain.
    """
    question = (question or "").strip()
    stats = _column_stats(columns, rows)
    row_count = len(rows)

    summary = (
        f"{row_count} row(s) across {len(columns)} column(s)"
        f"{' (the result was truncated)' if truncated else ''}, produced by a "
        f"{kind} run"
        + (f" for the question: {question}" if question else "")
        + "."
    )

    observations: list[str] = []
    for name, summary_of in stats.items():
        if len(observations) >= _MAX_OBSERVATIONS:
            break
        if summary_of["kind"] == "numeric":
            observations.append(
                f"{name} ranges from {_fmt(summary_of['min'])} to "
                f"{_fmt(summary_of['max'])} (mean "
                f"{_fmt(round(summary_of['mean'], 2))} "
                f"over {summary_of['count']} value(s))"
            )
        else:
            observations.append(
                f"{name} is {_fmt(summary_of['top'])} in "
                f"{summary_of['count']} of {row_count} row(s) "
                f"({summary_of['distinct']} distinct value(s))"
            )
    if not observations and columns:
        observations.append(
            f"the result carries no summarisable values across {len(columns)} column(s)"
        )

    caveats: list[str] = []
    profile = profile or {}
    null_columns = [
        name
        for name, stat in (profile.get("stats") or {}).items()
        if (stat.get("null_count") or 0) > 0 and name in columns
    ]
    if null_columns:
        caveats.append(
            "the profiled data has nulls in " + ", ".join(null_columns[:3])
            + ", so aggregates may undercount"
        )
    if truncated:
        caveats.append("the result was capped, so these figures describe only the rows kept")
    caveats.append(
        "this reads a computed result; it is not itself a validated finding"
    )
    caveats = caveats[:_MAX_CAVEATS]

    return {
        "summary": summary,
        "observations": observations,
        "caveats": caveats,
    }


def validate_interpretation(payload: Any) -> list[str]:
    """Problems with an LLM interpretation, as a list. Empty means acceptable."""
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["the interpretation must be a JSON object"]
    summary = payload.get("summary")
    if not isinstance(summary, str) or not summary.strip():
        problems.append("'summary' must be a non-empty string")
    for field in ("observations", "caveats"):
        value = payload.get(field)
        if isinstance(value, str):
            # The common LLM mistake: prose where a list belongs.
            problems.append(f"'{field}' must be a list of strings, not a string")
        elif isinstance(value, list) and not all(
            isinstance(item, str) and item.strip() for item in value
        ):
            problems.append(f"every entry in '{field}' must be a non-empty string")
        elif value is not None and not isinstance(value, list):
            problems.append(f"'{field}' must be a list of strings")
    return problems


class LLMInterpreter:
    """OpenAI-compatible interpreter; dormant without configuration.

    Implemented on httpx so no SDK dependency is added. The response is expected
    to be the interpretation object itself; anything else is a validation
    failure and the caller falls back to the deterministic read.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def interpret(
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
            "You are a data analyst's reader. Given a question, the query or "
            "script that produced a result, and the result itself, say what the "
            "result shows. Return ONLY a JSON object with this exact schema:\n"
            "{\n"
            '  "summary": string,\n'
            '  "observations": [string],\n'
            '  "caveats": [string]\n'
            "}\n"
            "Every observation must cite a value that appears in the result. Do "
            "not add fields or commentary.\n\n"
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


def _configured_llm() -> LLMInterpreter | None:
    """The configured interpreter, or None when no key is present."""
    api_key = os.environ.get("DAH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return LLMInterpreter(
        api_key=api_key,
        base_url=os.environ.get("DAH_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("DAH_LLM_MODEL", "gpt-4o-mini"),
    )


def create_interpretation(
    question: str,
    kind: str,
    source_text: str | None,
    columns: list[str],
    rows: list[list[Any]],
    profile: dict | None,
    truncated: bool = False,
) -> tuple[dict, str]:
    """Produce a validated interpretation and the engine that made it.

    Prefers the LLM when configured; falls back to the deterministic read on
    any failure, so an interpretation is always returned. The source is
    reported alongside so a reviewer knows how much weight it earns.
    """
    deterministic = interpret_result(
        question, kind, source_text, columns, rows, profile, truncated=truncated
    )
    llm = _configured_llm()
    if llm is None:
        return deterministic, SOURCE_DETERMINISTIC

    try:
        candidate = llm.interpret(question, kind, source_text, columns, rows, profile)
        problems = validate_interpretation(candidate)
        if problems:
            raise ValueError(
                f"LLM interpretation failed validation: {'; '.join(problems[:3])}"
            )
        candidate.setdefault("observations", [])
        candidate.setdefault("caveats", [])
        return candidate, SOURCE_LLM
    except Exception as error:
        # An unavailable or misbehaving LLM degrades to the deterministic
        # read rather than producing nothing. The breadth stays - the contract
        # is "any failure falls back" - but the reason is logged, so a fallback
        # caused by a bug in our own code surfaces instead of vanishing into
        # source=deterministic (P4-RELIABILITY-002).
        logging.getLogger(__name__).warning(
            "llm read failed; falling back to deterministic: %s", error,
        )
        return deterministic, SOURCE_DETERMINISTIC
