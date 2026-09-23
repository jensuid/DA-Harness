"""Question refinement (P8-REFINE-007, AT-04).

A vague question is the first thing that makes an analysis lie: "why are sales
down?" cannot be answered until it says which column is the measure, what the
split is, and - the part almost always missing - what "down" is measured
against. This module proposes that sharpening. It proposes and never writes:
the case's question moves only when the analyst accepts, edits or keeps the
original through the endpoints that own the case row.

Two engines sit behind one interface, as in the planner, the assistant, the
drafter and the generator:

- `refine_question` is deterministic and always available. It reads the
  profile's own measurements - real columns, measured min/max, measured
  cardinality - and appends the grounding the question lacks. It declines
  rather than invents: no profile, nothing numeric or temporal to sharpen
  with, no subject terms to preserve, or a question that already names its
  measure, its dimension and its time axis is left alone, and the decline is
  recorded rather than answered as a proposal.
- `LLMRefiner` calls an OpenAI-compatible endpoint when `DAH_LLM_API_KEY` is
  set. Its output is gated by `validate_refinement` before it is ever stored:
  the original must be echoed verbatim, every data reference must be a column
  the profile has, every number must be one the profile measured, and the
  subject terms must survive so the refinement answers the question asked
  rather than a neighbouring one. Any failure falls back to the deterministic
  proposal, which may itself be a decline.

AT-04's four thresholds are measured by verification/refine/verify_refine.py
over 50 cases, and the same four numbers are asserted in test_refine.py. The
deterministic engine makes three of them structural - the refined question
carries the original as its prefix, so it is preserved by construction and
semantically relevant by construction - but the suite measures them anyway,
because a claim that is structural today is one renamed variable away from
being a regression.

The LLM is an external engine the harness controls, not the other way round;
swapping provider means implementing `refine(question, profile, context)`.
"""

import json
import logging
import os
import re
from typing import Any

_MAX_QUESTION_CHARS = 500
_MAX_LLM_CHARS = 8_000

SOURCE_DETERMINISTIC = "deterministic"
SOURCE_LLM = "llm"

# Words that express a direction the question wants explained but not the
# reference frame it would be measured against - "down" says what, not "than
# what", which is exactly the gap a refinement should close.
_DIRECTION_WORDS = {
    "down", "up", "decline", "declined", "declining", "drop", "dropped",
    "decrease", "decreased", "increase", "increased", "grow", "grew", "growing",
    "rose", "fall", "fell", "falling", "rise", "rising", "shrink", "shrunk",
    "slump", "slumped", "surge", "surged", "improve", "improved", "worsen",
    "worse", "better", "change", "changed", "changing", "shift", "shifted",
    "move", "moved", "trend", "trending", "vary", "varies", "varied",
    "fluctuate", "fluctuating", "dip", "dipped", "spike", "spiked", "slide",
    "slid", "weak", "weakness", "strong", "strength", "slow", "slowed",
    "accelerate", "accelerated", "lag", "lagged", "lagging", "underperform",
    "outperform", "gain", "gained", "loss", "lost", "lose", "recover",
    "recovered", "rebound", "rebounded", "contract", "contracted", "expand",
    "expanded", "volatile", "volatility", " Momentum".strip().lower(),
}

# A reference frame: these do ground a comparison, so a question carrying one
# does not get a comparison clause appended.
_FRAME_WORDS = {
    "vs", "versus", "compared", "compare", "comparison", "than", "prior",
    "previous", "earlier", "last", "next", "baseline", "difference",
    "before", "after", "yesterday", "today", "now", "historical",
}

# Time references short of a column name: a question naming a month, a quarter
# or a year has already chosen its window.
_TIME_WORDS = {
    "january", "february", "march", "april", "may", "june", "july", "august",
    "september", "october", "november", "december", "jan", "feb", "mar",
    "apr", "jun", "jul", "aug", "sep", "sept", "oct", "nov", "dec",
    "month", "monthly", "week", "weekly", "day", "daily", "quarter",
    "quarterly", "year", "yearly", "annual", "annually", "decade", "period",
    "periods", "recent", "latest", "current", "historically", "lately",
    "nowadays", "timeframe", "timespan", "season", "seasonal", "ytd", "qtd",
    "mtd", "fiscal", "calendar", "q1", "q2", "q3", "q4",
}


# Words that carry no topic - a question made only of these is not a question
# about anything, so a refinement of it would have to invent a subject. Better
# to decline and let the analyst say what they mean.
_GENERIC_WORDS = {
    "data", "help", "info", "question", "test", "stuff", "things", "thing",
    "overview", "summary", "report", "analysis", "dashboard", "table", "file",
    "csv", "dataset", "sheet", "spreadsheet", "numbers", "metrics", "stats",
    "kpi", "kpis", "insights", "general", "everything", "anything", "something",
    "show", "give", "tell", "get", "see", "look", "make", "find", "list",
    "display", "print", "pull", "fetch", "want", "need", "please", "me",
}

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "of", "in", "on", "at", "to", "for",
    "with", "by", "is", "are", "was", "were", "be", "been", "being", "do",
    "does", "did", "what", "which", "who", "whom", "whose", "why", "how",
    "when", "where", "there", "their", "they", "them", "this", "that",
    "these", "those", "from", "as", "into", "about", "have", "has", "had",
    "not", "no", "so", "if", "it", "its", "our", "we", "you", "your", "my",
    "me", "i", "can", "could", "would", "should", "will", "may", "might",
    "any", "all", "some", "more", "most", "less", "least", "than", "then",
    "over", "under", "between", "across", "per", "each", "one", "two",
    "three", "very", "much", "many", "such", "also", "just", "only", "even",
}

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
# Numbers, with optional thousands separators and decimals, and date-like runs
# (a date's own digits are allowed because the profile measured them).
_NUMBER_RE = re.compile(r"\d[\d,]*(?:\.\d+)?")


def _columns(profile: dict | None) -> list[str]:
    return list((profile or {}).get("columns") or [])


def _stats(profile: dict | None) -> dict[str, dict]:
    return (profile or {}).get("stats") or {}


def _typed(profile: dict | None, family: str) -> list[str]:
    stats = _stats(profile)
    return [name for name in _columns(profile) if (stats.get(name) or {}).get("type") == family]


def _numeric(profile: dict | None) -> list[str]:
    return _typed(profile, "numeric")


def _temporal(profile: dict | None) -> list[str]:
    return _typed(profile, "temporal")


def _categorical(profile: dict | None) -> list[str]:
    return _typed(profile, "other")


def _words(text: str) -> list[str]:
    return [word.lower() for word in _WORD_RE.findall(text or "")]


def _subject_terms(question: str) -> list[str]:
    """The words that carry the question's topic.

    Used as the relevance guard: a refinement that loses them is answering a
    different question, however well written. Stopwords and short fragments are
    dropped, so "why are sales down?" keeps `sales` (and `down`, which is a
    direction word worth preserving in the refined question).
    """
    return [
        word
        for word in _words(question)
        if len(word) > 2 and word not in _STOPWORDS
    ]


def _names_column(question: str, candidates: list[str]) -> bool:
    """Does the question already reference one of these columns?

    Column names are matched on whole tokens so `region` does not match
    "regional" as a column reference - that is a word, not the column - but a
    multi-word column matches on its full name appearing in the question.
    """
    text = (question or "").lower()
    tokens = set(_words(question))
    for name in candidates:
        name = (name or "").strip().lower()
        if not name:
            continue
        if " " in name or "_" in name:
            if name in text:
                return True
        elif name in tokens:
            return True
    return False


def _measure_choice(question: str, numeric: list[str], stats: dict) -> str | None:
    """The numeric column the refinement should name as the measure.

    Prefers a column the question already gestures at; otherwise the one with
    the widest measured spread, which is the aggregate a "why did X change"
    question is usually about.
    """
    if not numeric:
        return None
    tokens = set(_subject_terms(question))
    for name in numeric:
        if (name or "").strip().lower() in tokens:
            return name
    best, best_spread = numeric[0], None
    for name in numeric:
        stat = stats.get(name) or {}
        try:
            spread = float(stat.get("max") or 0) - float(stat.get("min") or 0)
        except (TypeError, ValueError):
            spread = 0.0
        if best_spread is None or spread > best_spread:
            best, best_spread = name, spread
    return best


def _dimension_choice(question: str, categorical: list[str], stats: dict) -> str | None:
    """The categorical column the refinement should split by.

    Prefers a column the question names; otherwise the lowest-cardinality split
    available, because a two- or three-value split is the comparison the
    question can actually act on. Very high-cardinality columns (an id, a free
    text field) are not a usable split and are skipped rather than offered.
    """
    usable = [
        name for name in categorical
        if 2 <= int((stats.get(name) or {}).get("distinct_count") or 0) <= 50
    ]
    if not usable:
        return None
    tokens = set(_subject_terms(question))
    for name in usable:
        if (name or "").strip().lower() in tokens:
            return name
    return min(
        usable,
        key=lambda name: int((stats.get(name) or {}).get("distinct_count") or 0),
    )


def _time_choice(question: str, temporal: list[str]) -> str | None:
    """The temporal column the refinement should name as the axis."""
    if not temporal:
        return None
    tokens = set(_subject_terms(question))
    for name in temporal:
        if (name or "").strip().lower() in tokens:
            return name
    return temporal[0]


def _format_number(value: Any) -> str:
    """A measured value as it appears in the refined question.

    Integers get thousands separators for readability; everything else is
    stringified as the profiler measured it, so the value in the question is
    the value in the profile and the fabrication check sees the same digits.
    """
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, int):
        return f"{value:,}"
    if isinstance(value, float):
        if value == int(value) and abs(value) < 1e15:
            return f"{int(value):,}"
        return repr(value)
    return str(value)


def refine_question(question: str, profile: dict | None,
                    context: dict | None = None) -> dict | None:
    """Propose a sharpening of a question from the profile's measurements.

    Deterministic and dependency-free. Returns the proposal - the original
    verbatim, the refined question, the reason, and the grounds each added
    element came from - or `None` when the honest answer is that the question
    needs nothing this data can add. The refined question is the original with
    grounding appended, never a replacement: it cannot quietly drop what the
    analyst asked, which is AT-04's preserve-and-relevant thresholds made
    structural rather than hoped for.
    """
    question = (question or "").strip()
    if not question or len(question) > _MAX_QUESTION_CHARS:
        return None

    numeric = _numeric(profile)
    temporal = _temporal(profile)
    if not numeric and not temporal:
        # Nothing here could make the question measurable.
        return None

    terms = _subject_terms(question)
    if not terms or all(term in _GENERIC_WORDS for term in terms):
        # A question with no topic ("why?", "data", "help") has nothing to
        # preserve, so a refinement of it would be a new question rather than a
        # sharpening - and a new question is exactly the overwrite AT-04
        # forbids, even when the engine is the one making it.
        return None

    stats = _stats(profile)
    categorical = _categorical(profile)
    words = set(_words(question))

    has_measure = _names_column(question, numeric)
    has_dimension = _names_column(question, categorical)
    has_time = _names_column(question, temporal) or bool(words & _TIME_WORDS)
    wants_comparison = bool(words & _DIRECTION_WORDS)
    has_comparison = bool(words & _FRAME_WORDS)

    measure = None if has_measure else _measure_choice(question, numeric, stats)
    dimension = None if has_dimension else _dimension_choice(question, categorical, stats)
    time = None if has_time else _time_choice(question, temporal)
    comparison = None if (has_comparison or not wants_comparison) else time

    if not any([measure, dimension, time, comparison]):
        # The question already names its measure, its dimension and its window
        # and says what it compares against: it is already answerable as
        # written, and a refinement that reworded it would be noise.
        return None

    clauses: list[str] = []
    grounds: list[dict] = []
    changes: list[str] = []

    if measure:
        stat = stats.get(measure) or {}
        low = _format_number(stat.get("min"))
        high = _format_number(stat.get("max"))
        clauses.append(f"measured as {measure} ({low} to {high})")
        grounds.append({
            "kind": "column", "name": measure,
            "detail": f"numeric column, spanning {low} to {high}",
        })
        changes.append(
            f"names the measure {measure}, which the question left implied "
            f"(it spans {low} to {high})"
        )
    if dimension:
        count = int((stats.get(dimension) or {}).get("distinct_count") or 0)
        clauses.append(f"split by {dimension} ({count} values)")
        grounds.append({
            "kind": "column", "name": dimension,
            "detail": f"categorical column with {count} distinct values",
        })
        changes.append(
            f"splits the answer by {dimension}, which has {count} distinct "
            "values, so the comparison is between groups rather than one total"
        )
    if time:
        stat = stats.get(time) or {}
        low = _format_number(stat.get("min"))
        high = _format_number(stat.get("max"))
        clauses.append(f"over {time} ({low} to {high})")
        grounds.append({
            "kind": "column", "name": time,
            "detail": f"temporal column, {low} to {high}",
        })
        changes.append(
            f"fixes the window to {time}, which runs {low} to {high}, so the "
            "question is about a period rather than the whole table"
        )
    if comparison:
        clauses.append("comparing each period with the one before it")
        grounds.append({
            "kind": "column", "name": comparison,
            "detail": "the comparison is a period-over-period change on this "
                      "temporal column",
        })
        changes.append(
            "says what the change is measured against - the prior period - "
            "which a direction word like \"down\" leaves unstated"
        )

    # The clauses are an apposition of the original question, which keeps its
    # wording and its sentence type: a question stays a question and ends with
    # the grounding that makes it answerable.
    body = question.rstrip()
    terminal = body[-1] if body and body[-1] in "?.!" else ""
    body = body[:-1].rstrip() if terminal else body
    joiner = terminal if terminal else " -"
    refined = f"{body}{joiner} {', '.join(clauses)}{terminal}"

    purpose = ((context or {}).get("purpose") or "").strip()
    rationale = (
        "The question is sharpened, not replaced: each addition is a "
        "measurement the profile already made, so nothing in the refined "
        "version is estimated. "
        + " ".join(change[:1].upper() + change[1:] for change in changes)
        + "."
    )
    if purpose:
        rationale += (
            f" The stated purpose - {purpose[:200]} - is unchanged; only the "
            "question is sharpened."
        )

    return {
        "original": question,
        "refined": refined,
        "rationale": rationale.strip(),
        "grounds": grounds,
        "changes": changes,
    }


def _spellings(value) -> set[str]:
    """Every way a measured value may legitimately appear in a question.

    The formatter renders an integral float as an integer (52.0 -> "52"),
    separates thousands (9600 -> "9,600"), and prints a date as the profiler
    recorded it. The gate judges provenance, not formatting, so a measured
    value is allowed in any spelling the formatter or the analyst might use -
    and a value the profile never measured, in no spelling at all.
    """
    text = str(value)
    out = {text, text.replace(",", "")}
    for run in _NUMBER_RE.findall(text):
        out.add(run.replace(",", ""))
    try:
        number = float(value)
    except (TypeError, ValueError):
        return out
    out.add(f"{number:g}")
    if number == int(number):
        out.add(str(int(number)))
        out.add(f"{int(number):,}")
    return out


def _profile_numbers(profile: dict | None) -> set[str]:
    """Every number the profile measured, in any spelling it may be printed in.

    A refined question may quote any of these. A number that is none of them
    and none of the original's is a fabrication.
    """
    allowed: set[str] = set()
    profile = profile or {}
    allowed |= _spellings(int(profile.get("rows") or 0))
    allowed |= _spellings(int(profile.get("duplicate_rows") or 0))
    for name, stat in (profile.get("stats") or {}).items():
        for key in ("min", "max", "avg", "null_count", "null_percentage",
                    "distinct_count"):
            if key in stat and stat[key] is not None:
                allowed |= _spellings(stat[key])
    return allowed


def _numbers_in(text: str) -> set[str]:
    return {run.replace(",", "") for run in _NUMBER_RE.findall(text or "")}


def validate_refinement(proposal: Any, question: str,
                        profile: dict | None) -> list[str]:
    """Gate a proposal from any engine before it is persisted.

    Returns the problems; empty means the proposal is fit to show. This is the
    harness-validation step in the AI context strategy - an LLM that invents a
    column, invents a figure, or quietly rewrites the question never reaches
    the analyst, and the caller falls back to the deterministic proposal.
    """
    problems: list[str] = []
    if not isinstance(proposal, dict):
        return ["refinement must be a JSON object"]

    original = proposal.get("original")
    refined = proposal.get("refined")
    rationale = proposal.get("rationale")

    # AT-04's Level 0 requirement: the original is preserved, and the engine
    # must echo it so the harness can check rather than trust.
    if not isinstance(original, str) or original.strip() != (question or "").strip():
        problems.append("the original question must be echoed verbatim")

    if not isinstance(refined, str) or not refined.strip():
        problems.append("the refined question must be a non-empty string")
    elif refined.strip() == (question or "").strip():
        problems.append("the refined question must differ from the original")
    else:
        terms = _subject_terms(question)
        missing = [term for term in terms if term not in refined.lower()]
        if missing:
            problems.append(
                "the refined question loses the original's subject terms: "
                + ", ".join(missing[:5])
            )

    if not isinstance(rationale, str) or not rationale.strip():
        problems.append("a rationale is required, so a proposal is never bare")

    columns = set((c or "").lower() for c in _columns(profile))

    grounds = proposal.get("grounds")
    if grounds is None:
        grounds = []
    if not isinstance(grounds, list):
        problems.append("'grounds' must be a list")
        grounds = []
    else:
        for ground in grounds:
            if not isinstance(ground, dict):
                problems.append("every ground must be an object")
                continue
            name = ground.get("name")
            if not isinstance(name, str) or not name.strip():
                problems.append("every ground must name what it cites")
            elif columns and name.strip().lower() not in columns:
                # A citation of a column the profile never saw is the
                # fabrication AT-04 forbids, and it is caught here rather than
                # after the analyst has read it.
                problems.append(
                    f"ground cites '{name}', which is not a column in the "
                    "profiled data"
                )

    if isinstance(refined, str) and refined.strip():
        # Any token that exactly matches a column name must be a real one; a
        # column-shaped reference the profile does not have is invented.
        quoted = sorted(
            {match.strip().lower() for match in _QUOTED_RE.findall(refined)}
        )
        invented = [name for name in quoted if name not in columns]
        if invented:
            problems.append(
                "the refined question names columns the data does not have: "
                + ", ".join(invented[:5])
            )
        # A figure the profile never measured and the question never stated.
        allowed = _numbers_in(question) | _profile_numbers(profile)
        fabricated = sorted(
            number for number in _numbers_in(refined) if number not in allowed
        )
        if fabricated:
            problems.append(
                "the refined question quotes figures the profile did not "
                "measure: " + ", ".join(fabricated[:5])
            )

    return problems


# A column an engine quotes by name - in backticks or quotes, the way a
# schema-aware assistant writes one - must exist in the profile. Free-text
# words are left alone: "sales" in a question about a sales table is a word,
# not a citation, and treating it as one is how a guard stops being trusted.
_QUOTED_RE = re.compile(r'["\x60]([^"\x60]+)["\x60]')


class LLMRefiner:
    """OpenAI-compatible refiner; dormant without configuration.

    Implemented on httpx so no SDK dependency is added (DEC-001). The response
    is expected to be the proposal object itself; anything else fails
    validation and the caller falls back to the deterministic proposal.
    """

    def __init__(self, api_key: str, base_url: str, model: str) -> None:
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._model = model

    def refine(self, question: str, profile: dict | None,
               context: dict | None = None) -> dict:
        import httpx

        prompt = (
            "You refine an analyst's question into one the data can actually "
            "answer. Reference ONLY columns and figures that appear in the "
            "profile below - an invented column or an invented number is a "
            "failure. Keep the original question's meaning: the refined "
            "question must still be about what they asked.\n\n"
            "Return ONLY a JSON object with this exact schema:\n"
            "{\n"
            '  "original": string,  // the question verbatim, unchanged\n'
            '  "refined": string,   // the sharpened question\n'
            '  "rationale": string, // one or two sentences on what was added and why\n'
            '  "grounds": [{"kind": "column", "name": string, "detail": string}]\n'
            "}\n"
            "Do not add fields or commentary. If the question is already "
            "specific, return the same question as `refined`.\n\n"
            f"Question: {question}\n\n"
            f"Profile: {json.dumps(profile)[:_MAX_LLM_CHARS]}\n"
            + (f"Stated intent: {json.dumps(context)}\n" if context else "")
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
                "temperature": 0.2,
                "response_format": {"type": "json_object"},
            },
            timeout=60.0,
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"]
        proposal = json.loads(content)
        if isinstance(proposal, dict) and not proposal.get("original"):
            proposal["original"] = question
        return proposal


def _configured_llm() -> LLMRefiner | None:
    """The configured refiner, or none when no key is present."""
    api_key = os.environ.get("DAH_LLM_API_KEY") or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    return LLMRefiner(
        api_key=api_key,
        base_url=os.environ.get("DAH_LLM_BASE_URL", "https://api.openai.com/v1"),
        model=os.environ.get("DAH_LLM_MODEL", "gpt-4o-mini"),
    )


def create_refinement(question: str, profile: dict | None,
                      context: dict | None = None) -> tuple[dict | None, str]:
    """Produce a validated proposal and the engine that made it.

    Prefers the LLM when configured; falls back to the deterministic refiner on
    any failure, so a proposal is either honest or absent - never half-made.
    The source is reported alongside, so the shell can say which engine spoke
    and the analyst can weight the proposal accordingly.

    A failure of the LLM's own making - a bad schema, an invented column, a
    rewritten question - is logged with the reason rather than vanishing into
    `source=deterministic`, the discipline P4-RELIABILITY-002 set.
    """
    deterministic = refine_question(question, profile, context)
    llm = _configured_llm()
    if llm is None:
        return deterministic, SOURCE_DETERMINISTIC

    try:
        candidate = llm.refine(question, profile, context)
        problems = validate_refinement(candidate, question, profile)
        if problems:
            raise ValueError(
                f"LLM refinement failed validation: {'; '.join(problems[:3])}"
            )
        return candidate, SOURCE_LLM
    except Exception as error:
        logging.getLogger(__name__).warning(
            "llm refinement failed; falling back to deterministic: %s", error,
        )
        return deterministic, SOURCE_DETERMINISTIC
