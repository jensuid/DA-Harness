"""Code generator (P3-AI-013, contextual AI slice 3).

Turns a question in plain language into the read-only computation that would
answer it - and stops one step short of running it, exactly as drafting
(P3-AI-012) stops one step short of a finding. The analyst describes what they
want to know; the harness proposes SQL or Python; the analyst decides whether it
runs. Running a proposal is a POST to the runs endpoint that already exists,
which is what keeps "the human decides what executes" structural rather than a
flag.

Two engines sit behind one interface, as in the planner (P2-AI-011), the
interpreter (P3-AI-011) and the drafter (P3-AI-012):

- `generate_code` is deterministic and always available. It reads the profile's
  actual structure - its numeric measure, its widest categorical or temporal
  dimension, its nulls - and writes a GROUP BY aggregation, or a count-by-
  dimension query when the data has no measure to sum.
- `LLMGenerator` calls an OpenAI-compatible endpoint when `DAH_LLM_API_KEY` is
  set. Its output is validated here, and - the part that matters for code - the
  only columns it may read are columns the dataset actually has, and its SQL may
  only be a single read-only statement. An invented column or a DELETE falls
  back to the deterministic proposal.

The read-only gates of the run endpoints remain in force at execution time;
this validation is what keeps a proposal from being *handed to* the analyst with
a column that does not exist.

The LLM is an external engine the harness controls, not the other way round;
swapping provider means implementing `generate(question, profile, kind)`.
"""

import json
import logging
import os
import re
from typing import Any

from app.timeouts import LLM_TIMEOUT_SECONDS

_MAX_LLM_CHARS = 12_000

SOURCE_DETERMINISTIC = "deterministic"
SOURCE_LLM = "llm"
SOURCE_DETERMINISTIC_FALLBACK = "deterministic fallback"
SOURCE_FALLBACK_SENTENCE = (
    "the LLM was unavailable, so a deterministic proposal answered in its place"
)


def source_sentence(source: str) -> str:
    """The sentence a panel renders next to an engine's proposal.

    A fallback is announced rather than labelled, so the analyst knows the
    proposal they are reading is not the LLM's (FIX-TIMEOUT-006).
    """
    if source == SOURCE_DETERMINISTIC_FALLBACK:
        return SOURCE_FALLBACK_SENTENCE
    return f"by {source}"

KINDS = ("sql", "python")

# What a generated SQL proposal may start with. Mirrors the run engine's own
# read-only gate (app.analysis) so a proposal cannot be written that the runner
# would refuse - the proposal is checked before the analyst ever sees it.
_READ_ONLY_PREFIXES = ("select", "with", "values", "table", "show", "describe")

# SQL words that are structure, not column references. Kept lowercase; matched
# case-insensitively. Deliberately small - anything not here and not a column is
# reported as an invented reference.
_SQL_KEYWORDS = {
    "select", "from", "where", "group", "by", "order", "asc", "desc", "limit",
    "offset", "having", "join", "left", "right", "inner", "outer", "full",
    "cross", "on", "using", "as", "and", "or", "not", "in", "is", "null",
    "distinct", "case", "when", "then", "else", "end", "between", "like",
    "union", "all", "with", "over", "partition", "true", "false",
}

_ALIAS_RE = re.compile(r"\bas\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE)
_CALL_RE = re.compile(r"([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_IDENT_RE = re.compile(r"`?([A-Za-z_][A-Za-z0-9_]*)`?")
_INDEX_RE = re.compile(r"""\[\s*['"]([A-Za-z_][A-Za-z0-9_]*)['"]\s*\]""")
_QUERY_RE = re.compile(r"""\b(?:query|execute)\s*\(\s*['"]([^'"]+)['"]""")
_FENCE_RE = re.compile(r"^\s*```[a-zA-Z]*\s*\n?|\n?\s*```\s*$")


def _columns(profile: dict | None) -> list[str]:
    return list((profile or {}).get("columns") or [])


def _stats(profile: dict | None) -> dict:
    return (profile or {}).get("stats") or {}


def _typed_columns(profile: dict | None, family: str) -> list[str]:
    stats = _stats(profile)
    return [name for name in _columns(profile) if stats.get(name, {}).get("type") == family]


def _strip_fence(code: str) -> str:
    """Remove markdown fences an LLM sometimes wraps code in."""
    return _FENCE_RE.sub("", code.strip()).strip()


def _sql_identifiers(sql: str) -> set[str]:
    """Every column a SQL statement could be reading.

    Aliases (`AS total`) and function calls (`SUM(...)`, `read_csv_auto(...)`)
    are structure rather than references, so they are not reported. Single-
    quoted literals are values, not identifiers; double-quoted identifiers are.
    """
    without_literals = re.sub(r"'[^']*'", " ", sql)
    # A qualified reference (`a.region`) reads the column `region`; the qualifier
    # is structure, so it is dropped before the reference is checked.
    without_literals = re.sub(r"\b[A-Za-z_][A-Za-z0-9_]*\.", " ", without_literals)
    # An alias a query introduces (AS total) may be referenced later in ORDER BY
    # or GROUP BY; it is structure, not a column read, so it is allowed here.
    aliases = {name.lower() for name in _ALIAS_RE.findall(without_literals)}
    called = {name.lower() for name in _CALL_RE.findall(without_literals)}
    identifiers = set(_IDENT_RE.findall(without_literals))
    return {
        name
        for name in identifiers
        if name.lower() not in called and name.lower() not in aliases
    }


def _python_read_columns(code: str) -> set[str]:
    """Every column a Python snippet reads.

    Reads happen by index (`row["region"]`) or through the read-only SQL passed
    to `dataset.query(...)`. Output keys of a result dict are writes, not reads,
    so they are unconstrained - an invented *output name* invents nothing,
    whereas an invented *read* silently produces wrong numbers.
    """
    read_columns = set(_INDEX_RE.findall(code))
    for embedded in _QUERY_RE.findall(code):
        read_columns |= _sql_identifiers(embedded)
    return read_columns


def _columns_referenced(code: str, kind: str, profile: dict | None) -> list[str]:
    """The dataset columns a proposal reads, in profile order."""
    known = set(_columns(profile))
    if kind == "python":
        candidates = _python_read_columns(code)
    else:
        candidates = _sql_identifiers(code)
    return [name for name in _columns(profile) if name in candidates]


def _looks_read_only(sql: str) -> bool:
    """A single read-only statement, as the run engine would accept."""
    body = sql.strip().rstrip(";").strip()
    if not body or ";" in body:
        return False
    return body.lower().startswith(_READ_ONLY_PREFIXES)


_ID_NAME_RE = re.compile(r"(?:^|_)(?:id|ids|code|key|index|idx|seq|no|number)$", re.I)


def _looks_like_an_id(name: str) -> bool:
    """A column whose name says it is a key, not a quantity."""
    return bool(_ID_NAME_RE.search(name or ""))


def _is_identifier(profile: dict | None, name: str) -> bool:
    """A column that is a key, not a quantity.

    Two independent signals: the name says so (`order_id`, `customer_code`), or
    the values are the row numbers themselves (distinct in every row, and
    spanning exactly 1..rows). Summing such a column means nothing and grouping
    by it yields a row per record, so it is neither a measure nor a dimension.
    A continuous measure like revenue is distinct in every row but spans
    nothing like 1..rows, so it survives.
    """
    if _looks_like_an_id(name):
        return True
    stats = _stats(profile).get(name) or {}
    total = (profile or {}).get("rows") or 0
    distinct = stats.get("distinct_count")
    low, high = stats.get("min"), stats.get("max")
    if (
        total > 1
        and distinct is not None
        and int(distinct) >= int(total)
        and isinstance(low, (int, float))
        and isinstance(high, (int, float))
        and float(low) == 1
        and float(high) == float(total)
    ):
        return True
    return False


def _pick_axes(
    profile: dict | None, variant: int = 0
) -> tuple[str | None, str | None, str | None]:
    """The profile's measure, categorical dimension and temporal column.

    Prefers columns that actually repeat, because a column unique in every row
    is an identifier: summing it means nothing and grouping by it answers
    nothing. Falls back to the first of each family when nothing repeats, so a
    proposal exists even for awkward data.

    `variant` rotates the choice through the usable columns of each family, so
    a retry (P6-AGENT-002) proposes a *different* query instead of re-running
    the one that just returned nothing. A family with a single usable column
    keeps that column, so a dataset with no alternative axis produces an
    identical proposal - the caller detects that and states the dead end
    rather than spending its budget on a query it has already tried.
    """
    numeric = _typed_columns(profile, "numeric")
    temporal = _typed_columns(profile, "temporal")
    other = _typed_columns(profile, "other")
    measures = [name for name in numeric if not _is_identifier(profile, name)]
    dimensions = [name for name in other if not _is_identifier(profile, name)]
    periods = [name for name in temporal if not _is_identifier(profile, name)]
    # Every numeric column being an identifier means the data has no quantity
    # worth aggregating, so the proposal counts rows instead of summing a key.
    measure = (measures or [None])[0]
    dimension = (dimensions or other or [None])[0]
    period = (periods or temporal or [None])[0]
    if variant:
        if len(measures) > 1:
            measure = measures[variant % len(measures)]
        if len(dimensions) > 1:
            dimension = dimensions[variant % len(dimensions)]
        elif len(periods) > 1:
            period = periods[variant % len(periods)]
    return measure, dimension, period


def _sql_question(question: str, measure, dimension, period) -> str:
    if measure and period:
        return (
            f"SELECT {period} AS period, COUNT(*) AS row_count, "
            f"SUM({measure}) AS total_{measure} FROM read_csv_auto(?) "
            f"GROUP BY 1 ORDER BY 1"
        )
    if measure and dimension:
        return (
            f"SELECT {dimension} AS category, COUNT(*) AS row_count, "
            f"SUM({measure}) AS total_{measure} FROM read_csv_auto(?) "
            f"GROUP BY 1 ORDER BY total_{measure} DESC"
        )
    if dimension:
        return (
            f"SELECT {dimension} AS category, COUNT(*) AS row_count "
            f"FROM read_csv_auto(?) GROUP BY 1 ORDER BY row_count DESC"
        )
    if measure:
        return (
            f"SELECT COUNT(*) AS row_count, SUM({measure}) AS total_{measure}, "
            f"MIN({measure}) AS min_{measure}, MAX({measure}) AS max_{measure} "
            f"FROM read_csv_auto(?)"
        )
    return "SELECT COUNT(*) AS row_count FROM read_csv_auto(?)"


def _python_question(question: str, measure, dimension, period) -> str:
    if measure and dimension:
        return (
            f'totals = {{}}\n'
            f'for row in dataset.rows:\n'
            f'    key = row["{dimension}"]\n'
            f'    value = row["{measure}"]\n'
            f'    if not isinstance(value, (int, float)) or isinstance(value, bool):\n'
            f'        continue\n'
            f'    totals[key] = totals.get(key, 0) + value\n'
            f'result = [\n'
            f'    {{"{dimension}": key, "total_{measure}": total}}\n'
            f'    for key, total in sorted(\n'
            f'        totals.items(), key=lambda item: item[1], reverse=True\n'
            f'    )\n'
            f']\n'
        )
    if measure and period:
        return (
            f'rows = sorted(dataset.rows, key=lambda row: row["{period}"])\n'
            f'totals = {{}}\n'
            f'for row in rows:\n'
            f'    value = row["{measure}"]\n'
            f'    if not isinstance(value, (int, float)) or isinstance(value, bool):\n'
            f'        continue\n'
            f'    totals[row["{period}"]] = totals.get(row["{period}"], 0) + value\n'
            f'result = [\n'
            f'    {{"{period}": key, "total_{measure}": total}}\n'
            f'    for key, total in sorted(totals.items())\n'
            f']\n'
        )
    if dimension:
        return (
            f'counts = {{}}\n'
            f'for row in dataset.rows:\n'
            f'    counts[row["{dimension}"]] = counts.get(row["{dimension}"], 0) + 1\n'
            f'result = [\n'
            f'    {{"{dimension}": key, "row_count": count}}\n'
            f'    for key, count in sorted(\n'
            f'        counts.items(), key=lambda item: item[1], reverse=True\n'
            f'    )\n'
            f']\n'
        )
    if measure:
        return (
            f'values = [\n'
            f'    row["{measure}"]\n'
            f'    for row in dataset.rows\n'
            f'    if isinstance(row["{measure}"], (int, float))\n'
            f'    and not isinstance(row["{measure}"], bool)\n'
            f']\n'
            f'summary = {{"row_count": len(values)}}\n'
            f'if values:\n'
            f'    summary["total_{measure}"] = sum(values)\n'
            f'    summary["min_{measure}"] = min(values)\n'
            f'    summary["max_{measure}"] = max(values)\n'
            f'result = [summary]\n'
        )
    return 'result = [{"row_count": len(dataset.rows)}]\n'


def _explain(question: str, kind: str, measure, dimension, period) -> str:
    """Say what the proposal does and which real columns it reads."""
    target = measure or dimension or period
    if measure and (dimension or period):
        axis = dimension or period
        return (
            f"Aggregates {measure} by {axis} and ranks the groups by their total, "
            f"so the question ({question or 'unstated'}) can be answered by comparing "
            f"a handful of rows instead of the whole dataset."
        )
    if measure:
        return (
            f"Summarises {measure} over the whole dataset - its total, minimum and "
            f"maximum - because no grouping column is available to break it down by. "
            f"This is a first read on {question or 'the question'}, not an answer to it."
        )
    if dimension or period:
        axis = dimension or period
        return (
            f"Counts rows by {axis}; the dataset has no numeric measure to sum, so "
            f"the shape of the data is all a proposal can honestly describe."
        )
    return (
        "Counts the dataset's rows. Nothing else can be proposed until the data "
        "has a column to group by or a number to aggregate."
    )


def generate_code(
    question: str, profile: dict | None, kind: str, variant: int = 0
) -> dict:
    """Propose the read-only computation that would answer a question.

    Deterministic and always available. Every column the proposal names comes
    from the profile, so it cannot reference a column the dataset does not have.
    `variant` rotates the chosen axes so a retry proposes a different query.
    """
    if kind not in KINDS:
        kind = "sql"
    measure, dimension, period = _pick_axes(profile, variant)
    if kind == "python":
        code = _python_question(question, measure, dimension, period)
    else:
        code = _sql_question(question, measure, dimension, period)
    return {
        "kind": kind,
        "code": code,
        "explanation": _explain(question, kind, measure, dimension, period),
        "columns_used": _columns_referenced(code, kind, profile),
    }


def validate_code(payload: Any, profile: dict | None, kind: str) -> list[str]:
    """Problems with an LLM proposal, as a list. Empty means acceptable.

    Beyond shape, the proposal may only read columns the dataset actually has -
    code that reads a column that does not exist produces wrong numbers or a
    confusing failure at run time - and its SQL must be a single read-only
    statement, so nothing is handed to the analyst that the runner would refuse.
    """
    problems: list[str] = []
    if not isinstance(payload, dict):
        return ["the proposal must be a JSON object"]
    if payload.get("kind") != kind:
        problems.append(f"'kind' must be {kind!r}")
    code = payload.get("code")
    if not isinstance(code, str) or not code.strip():
        problems.append("'code' must be a non-empty string")
    explanation = payload.get("explanation")
    if not isinstance(explanation, str) or not explanation.strip():
        problems.append("'explanation' must be a non-empty string")
    if not isinstance(code, str):
        return problems

    code = _strip_fence(code)
    known = set(_columns(profile))
    if not known:
        # A profile with no columns is not something to propose against; the
        # deterministic path would also produce nothing meaningful.
        problems.append("the dataset has no profiled columns to read")
        return problems

    if kind == "sql":
        if not _looks_read_only(code):
            problems.append(
                "the SQL must be a single read-only statement (SELECT/WITH/VALUES)"
            )
    read_columns = _columns_referenced(code, kind, profile)
    invented = {
        name
        for name in (_python_read_columns(code) if kind == "python" else _sql_identifiers(code))
        if name not in known
        and name.lower() not in _SQL_KEYWORDS
    }
    if invented:
        problems.append(
            "the proposal reads columns absent from the dataset: "
            + ", ".join(sorted(invented))
        )
    return problems


class LLMGenerator:
    """OpenAI-compatible generator; dormant without configuration.

    Implemented on httpx so no SDK dependency is added. The response is expected
    to be the proposal object itself; anything else is a validation failure and
    the caller falls back to the deterministic proposal.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def generate(self, question: str, profile: dict | None, kind: str) -> dict:
        import httpx

        stats = _stats(profile)
        described = [
            {
                "name": name,
                "type": stats.get(name, {}).get("type"),
                "null_count": stats.get(name, {}).get("null_count"),
                "distinct_count": stats.get(name, {}).get("distinct_count"),
            }
            for name in _columns(profile)
        ]
        prompt = (
            "You are a data analyst's code generator. Given a question and the "
            "profile of one dataset, write the read-only computation that would "
            "answer it. Return ONLY a JSON object with this exact schema:\n"
            "{\n"
            '  "kind": "' + kind + '",\n'
            '  "code": string,\n'
            '  "explanation": string\n'
            "}\n"
            "`code` is a single read-only SQL statement (the table is "
            "`read_csv_auto(?)`, exactly one `?` placeholder, no other tables) "
            "or a Python snippet whose dataset handle is `dataset` "
            "(`dataset.rows` is a list of dicts, `dataset.query(sql)` runs "
            "read-only SQL) and which leaves its answer in `result` as a list "
            "of dicts or lists. Read ONLY columns listed below. Do not add "
            "fields or commentary.\n\n"
            f"Question: {question or '(none given)'}\n"
            f"Requested kind: {kind}\n\n"
            f"Columns: {json.dumps(described, default=str)[:_MAX_LLM_CHARS]}\n"
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
            timeout=LLM_TIMEOUT_SECONDS,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        payload = json.loads(content)
        payload["code"] = _strip_fence(payload.get("code") or "")
        return payload


def _configured_llm() -> "LLMGenerator | None":
    """The configured generator, or None when no key is present."""
    api_key = os.environ.get("DAH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return LLMGenerator(
        api_key=api_key,
        base_url=os.environ.get("DAH_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("DAH_LLM_MODEL", "gpt-4o-mini"),
    )


def create_code(
    question: str, profile: dict | None, kind: str, variant: int = 0
) -> tuple[dict, str]:
    """Produce a validated proposal and the engine that made it.

    Prefers the LLM when configured; falls back to the deterministic proposal on
    any failure - an unavailable LLM, malformed output, a schema violation, a
    statement that is not read-only, or a column the dataset does not have - so
    a proposal is always returned and the source says which engine spoke.
    """
    if kind not in KINDS:
        kind = "sql"
    deterministic = generate_code(question, profile, kind, variant)
    llm = _configured_llm()
    if llm is None:
        return deterministic, SOURCE_DETERMINISTIC

    # A retry tells the LLM what the last attempt returned nothing for, so its
    # proposal differs from the one that struck out instead of paraphrasing it.
    prompted = question
    if variant:
        prompted = (
            f"{question or '(none given)'} "
            f"(note: {variant} earlier attempt(s) at this returned no rows; "
            f"propose a different approach and different columns)"
        )
    try:
        candidate = llm.generate(prompted, profile, kind)
        problems = validate_code(candidate, profile, kind)
        if problems:
            raise ValueError(
                f"LLM proposal failed validation: {'; '.join(problems[:3])}"
            )
        candidate["kind"] = kind
        candidate["code"] = _strip_fence(candidate["code"])
        candidate["columns_used"] = _columns_referenced(
            candidate["code"], kind, profile
        )
        return candidate, SOURCE_LLM
    except Exception as error:
        # An unavailable or misbehaving LLM degrades to the deterministic
        # proposal rather than producing nothing. The breadth stays - the contract
        # is "any failure falls back" - but the reason is logged, so a fallback
        # caused by a bug in our own code surfaces instead of vanishing into
        # source=deterministic (P4-RELIABILITY-002). The source carries it too:
        # the panel's own label is what tells the analyst the engine they
        # configured did not answer and another one did (FIX-TIMEOUT-006).
        logging.getLogger(__name__).warning(
            "llm proposal failed; falling back to deterministic: %s", error,
        )
        return deterministic, SOURCE_DETERMINISTIC_FALLBACK
