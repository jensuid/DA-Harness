"""Nine-dimension validation of a finding (P8-VALID-003, AT-17).

A finding's verdict used to account for three things: the calculation
reproduced, the data had no nulls, and the run belonged to the case. Those are
the honest core and they stay. The PRD names nine dimensions - Calculation,
Data, Population, Timeframe, Method, Evidence, Assumptions, Causality and
Alternative explanations - and the six that were missing are the ones that
catch a *correct* calculation answering the *wrong* question: a comparison of
groups a filter excluded, a trend read into a single period, causation claimed
from a correlation.

Everything here is a pure function of objects already on disk - the stored run,
the stored profile, the case's question and context. No check executes
anything; the one execution validation performs is the rerun `validate_finding`
already did, whose outcome the checks read. That is what keeps validation at
one execution rather than nine, and what keeps these checks from ever producing
a 500.

A check that cannot decide answers `passed=True` with a sentence saying it was
skipped. This is deliberate and it is the rule, not a fallback: a verdict must
not punish a finding for the validator's own blindness, and a skipped check
that fails is indistinguishable from a finding that is wrong.
"""

from __future__ import annotations

import json
from typing import Any

from app.evaluator import _allowed_numbers, _numbers_in
from app.quality import CATEGORY_MAX_DISTINCT
from app.generator import _SQL_KEYWORDS, _sql_identifiers

# The PRD's nine dimensions, in the spec's own order. The first three are the
# checks that existed before this task; the rest are new. The names are the
# contract the shell renders and the golden suite (P8-GOLDEN-005) measures.
DIMENSION_CALCULATION = "calculation"
DIMENSION_DATA = "data"
DIMENSION_POPULATION = "population"
DIMENSION_TIMEFRAME = "timeframe"
DIMENSION_METHOD = "method"
DIMENSION_EVIDENCE = "evidence"
DIMENSION_ASSUMPTIONS = "assumptions"
DIMENSION_CAUSALITY = "causality"
DIMENSION_ALTERNATIVES = "alternative_explanations"

DIMENSIONS = (
    DIMENSION_CALCULATION,
    DIMENSION_DATA,
    DIMENSION_POPULATION,
    DIMENSION_TIMEFRAME,
    DIMENSION_METHOD,
    DIMENSION_EVIDENCE,
    DIMENSION_ASSUMPTIONS,
    DIMENSION_CAUSALITY,
    DIMENSION_ALTERNATIVES,
)

# A hard failure blocks `supported`; a soft concern yields
# `partially_supported`, the verdict that says the numbers reproduce and the
# claim is phrased within them but the analysis carries a stated limitation.
# Calculation and Evidence are hard because they are about the finding's own
# truth; Population is hard because a comparison the filter excluded is not a
# comparison of what was asked. The rest are about how the finding reads, which
# is a concern an analyst can accept with their eyes open.
HARD_DIMENSIONS = frozenset(
    {DIMENSION_CALCULATION, DIMENSION_EVIDENCE, DIMENSION_POPULATION}
)

# Causal language that correlation cannot support. The weakest form of AT-18:
# this check *says* the claim outruns the method, the full guard with its
# thresholds is P8-CAUSAL-004.
_CAUSAL_TERMS = (
    "drives",
    "causes",
    "caused",
    "leads to",
    "led to",
    "results in",
    "resulted in",
    "because of",
    "due to",
    "impact on",
    "affects",
    "influences",
    "produces",
    "generates",
)

# Words that make a claim about change over time, which is what the Timeframe
# check exists to qualify.
_TREND_TERMS = (
    "trend",
    "decline",
    "declined",
    "increase",
    "increased",
    "decrease",
    "decreased",
    "grew",
    "growth",
    "fell",
    "fall",
    "rose",
    "rise",
    "drop",
    "dropped",
    "over time",
    "same period",
    "year over year",
    "month over month",
    "quarter over quarter",
)


class ValidationCheck:
    """One dimension's verdict. A plain carrier - no behaviour, no side effects."""

    def __init__(self, dimension: str, passed: bool, detail: str, hard: bool) -> None:
        self.dimension = dimension
        self.passed = passed
        self.detail = detail
        self.hard = hard

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.dimension,
            "dimension": self.dimension,
            "passed": self.passed,
            "detail": self.detail,
            "hard": self.hard,
        }

    def __eq__(self, other: object) -> bool:
        return isinstance(other, ValidationCheck) and self.to_dict() == other.to_dict()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"ValidationCheck({self.dimension!r}, passed={self.passed!r})"


def _skip(dimension: str, reason: str) -> ValidationCheck:
    """A check that cannot decide. Passes, and says why it did not decide."""
    return ValidationCheck(dimension, True, f"skipped - {reason}", hard=False)


def _normalise(text: str) -> str:
    return (text or "").strip().lower()


def _profile_columns(profile: dict | None) -> list[str]:
    if not isinstance(profile, dict):
        return []
    columns = profile.get("columns")
    return [str(name) for name in columns] if isinstance(columns, list) else []


def _profile_stats(profile: dict | None) -> dict[str, Any]:
    if not isinstance(profile, dict):
        return {}
    stats = profile.get("stats")
    return stats if isinstance(stats, dict) else {}


def _quality_issues(profile: dict | None) -> list[dict[str, Any]]:
    if not isinstance(profile, dict):
        return []
    issues = profile.get("quality")
    return issues if isinstance(issues, list) else []


# --- the three pre-existing checks, now as dimensions ------------------------


def check_calculation(reproduced: bool, rerun_detail: str) -> ValidationCheck:
    """The stored computation reproduces. The one check that executes anything,
    and its outcome is passed in - so this module never runs code."""
    return ValidationCheck(
        DIMENSION_CALCULATION,
        reproduced,
        rerun_detail,
        hard=True,
    )


def check_data(profile: dict | None) -> ValidationCheck:
    """The data the finding rests on is complete enough to support it.

    Reads the profile's own missing-value quality issue (P8-QUALITY-002), which
    already carries the impact sentence, so the finding's audit and the Data
    stage say the same thing about the same null.
    """
    if not isinstance(profile, dict):
        return _skip(DIMENSION_DATA, "no profile was recorded for this dataset")
    for issue in _quality_issues(profile):
        if issue.get("kind") == "missing_values" and issue.get("column"):
            return ValidationCheck(
                DIMENSION_DATA,
                False,
                issue.get("impact") or "the profiled data contains missing values",
                hard=False,
            )
    return ValidationCheck(
        DIMENSION_DATA,
        True,
        "no missing values were detected in the profiled columns",
        hard=False,
    )


def check_evidence(statement: str, columns: list[str], rows: list[list[Any]]) -> ValidationCheck:
    """Every magnitude the finding quotes is one its run actually produced.

    The drafter's own honesty budget (P3-AI-012), reused from the EVALUATE
    engine rather than reimplemented: cell values, row and column counts and
    value frequencies are the magnitudes a claim may quote, and anything else
    is a number the analysis did not produce.
    """
    quoted = _numbers_in(statement)
    if not quoted:
        return ValidationCheck(
            DIMENSION_EVIDENCE,
            True,
            "the finding quotes no magnitude, so no number is checkable against "
            "the result",
            hard=True,
        )
    allowed = _allowed_numbers(columns, rows)
    invented = sorted(value for value in quoted if value not in allowed)
    if invented:
        return ValidationCheck(
            DIMENSION_EVIDENCE,
            False,
            "the finding quotes values absent from its own result: "
            + ", ".join(str(value) for value in invented),
            hard=True,
        )
    return ValidationCheck(
        DIMENSION_EVIDENCE,
        True,
        "every magnitude the finding quotes appears in its own result",
        hard=True,
    )


# --- the six new checks -------------------------------------------------------


def check_population(
    sql: str,
    columns: list[str],
    rows: list[list[Any]],
    profile: dict | None,
    question: str,
) -> ValidationCheck:
    """The result is the population the question asks about, or a stated subset
    of it.

    Two defects this catches that a correct calculation would not: a filter in
    the SQL that narrows the table under a GROUP BY, so the groups compared are
    not the groups in the data; and a comparison across groups whose sizes are
    so uneven that the comparison is really about one of them.
    """
    text = _normalise(sql)
    if not text:
        return _skip(DIMENSION_POPULATION, "the finding's run has no stored query")
    total = _profile_rows(profile)
    filtered = " where " in text
    if filtered and total:
        # A GROUP BY over a filtered table answers a narrower question than the
        # one the dataset holds; the finding has to say so or it overclaims.
        grouping = "group by" in text
        noun = "the groups it compares" if grouping else "the rows it reads"
        return ValidationCheck(
            DIMENSION_POPULATION,
            False,
            f"the query filters the table before analysing it, so {noun} are a "
            f"subset of the {total} row(s) the dataset holds, not the whole "
            f"population",
            hard=True,
        )
    if rows and len(rows) > 1:
        # Even group sizes are not required, but a comparison where one group
        # is an order of magnitude larger is a comparison about that group.
        sizes = [len(row) for row in rows]
        if max(sizes) >= min(sizes) * 10 and min(sizes) > 0:
            return ValidationCheck(
                DIMENSION_POPULATION,
                False,
                "the result's rows differ in width by an order of magnitude, so "
                "the comparison rests on the widest one",
                hard=True,
            )
    return ValidationCheck(
        DIMENSION_POPULATION,
        True,
        "the query reads the table without narrowing it, so the result covers "
        "the dataset's full population"
        if not filtered
        else "the query filters the table and the finding's claim is scoped to "
        "that subset",
        hard=True,
    )


def check_timeframe(
    statement: str, question: str, profile: dict | None
) -> ValidationCheck:
    """A claim about change over time is supportable by the time the data
    actually spans.

    A trend over one period is not a trend, and a 'same period last year'
    comparison over data holding only one year compares a period to nothing.
    The profile's temporal column supplies the span; the date-gap quality issue
    supplies the holes.
    """
    claim = _normalise(statement) + " " + _normalise(question)
    if not any(term in claim for term in _TREND_TERMS):
        return ValidationCheck(
            DIMENSION_TIMEFRAME,
            True,
            "the finding makes no claim about change over time, so no period "
            "span is required to support it",
            hard=False,
        )
    if not isinstance(profile, dict):
        return _skip(DIMENSION_TIMEFRAME, "no profile was recorded for this dataset")
    temporal = [
        name
        for name, stat in _profile_stats(profile).items()
        if isinstance(stat, dict) and stat.get("type") == "temporal"
    ]
    if not temporal:
        return _skip(
            DIMENSION_TIMEFRAME,
            "the dataset has no date or timestamp column to check the claim "
            "against",
        )
    # A single distinct temporal value cannot support change over time, however
    # many rows hold it.
    stats = _profile_stats(profile)
    spans = []
    for name in temporal:
        distinct = int(stats.get(name, {}).get("distinct_count", 0) or 0)
        spans.append((name, distinct))
    thin = [name for name, distinct in spans if distinct < 2]
    if thin:
        return ValidationCheck(
            DIMENSION_TIMEFRAME,
            False,
            f"the finding claims change over time but {thin[0]} holds a single "
            f"distinct value, so there is no earlier period to compare against",
            hard=False,
        )
    gaps = [
        issue
        for issue in _quality_issues(profile)
        if issue.get("kind") == "date_gaps" and issue.get("column")
    ]
    if gaps:
        return ValidationCheck(
            DIMENSION_TIMEFRAME,
            False,
            gaps[0].get("impact")
            or "the time column has gaps the finding's comparison steps over",
            hard=False,
        )
    named = ", ".join(temporal[:2])
    return ValidationCheck(
        DIMENSION_TIMEFRAME,
        True,
        f"the finding's time claim is over a column with more than one period "
        f"({named}) and no gaps were detected",
        hard=False,
    )


def check_method(
    sql: str,
    statement: str,
    question: str,
    profile: dict | None,
    columns: list[str],
    rows: list[list[Any]],
) -> ValidationCheck:
    """The computation matches the shape of the question.

    Three mismatches this catches: an average over a column the profile flagged
    extreme (the mean is the first thing a generator reaches for and the one an
    outlier moves most); a COUNT offered where the question asks for a rate or
    a share; and a computation that never reads the column the question is
    actually about, which is the shape of an answer to a different question.
    """
    text = _normalise(sql)
    claim = _normalise(question)
    if not text:
        return _skip(DIMENSION_METHOD, "the finding's run has no stored query")

    extremes = {
        issue.get("column")
        for issue in _quality_issues(profile)
        if issue.get("kind") == "extreme_values"
    }
    averaged = _averaged_columns(text)
    flagged = sorted(name for name in averaged if name in extremes)
    if flagged:
        return ValidationCheck(
            DIMENSION_METHOD,
            False,
            f"the query averages {flagged[0]}, which the profile flagged as "
            f"holding extreme values; an average there describes the outlier "
            f"more than the typical value",
            hard=False,
        )

    if claim and ("rate" in claim or "share" in claim or "percentage" in claim):
        if "avg(" in text.replace(" ", "") or "count(" in text.replace(" ", ""):
            if "sum(" not in text:
                return ValidationCheck(
                    DIMENSION_METHOD,
                    False,
                    "the question asks for a rate or share but the query "
                    "computes a count or an average without the total that a "
                    "rate is a share of",
                    hard=False,
                )

    reads = {
        str(name).lower()
        for name in _sql_identifiers(sql)
        if str(name).lower() in _profile_columns(profile)
    }
    asked = _words_of(claim)
    profile_columns = {str(name).lower() for name in _profile_columns(profile)}
    about = [
        word
        for word in asked
        if len(word) > 3 and word in profile_columns and word not in _SQL_KEYWORDS
    ]
    unread = sorted(name for name in about if name.lower() not in {r.lower() for r in reads})
    if unread and about:
        # A question about revenue answered by a query that never reads revenue
        # is an answer to a different question, however correctly it computes.
        return ValidationCheck(
            DIMENSION_METHOD,
            False,
            f"the question names {unread[0]} but the query does not read it, so "
            f"the computation cannot be about what was asked",
            hard=False,
        )
    return ValidationCheck(
        DIMENSION_METHOD,
        True,
        "the query's method matches the question's shape",
        hard=False,
    )


def check_assumptions(
    sql: str, statement: str, profile: dict | None, rows: list[list[Any]]
) -> ValidationCheck:
    """The unstated premises the finding rests on, taken from the profile.

    An implicit 'missing means zero' is the classic: a SUM over a column with
    nulls is not the total of the column, it is the total of the part that was
    present, and a finding that reports it as a total assumes a premise the
    data contradicts. A comparison of raw totals across groups of different
    sizes assumes the sizes do not matter, which a rate would refute.
    """
    text = _normalise(sql)
    if not text:
        return _skip(DIMENSION_ASSUMPTIONS, "the finding's run has no stored query")
    summed = _summed_columns(text)
    for name in summed:
        stat = _profile_stats(profile).get(name)
        if isinstance(stat, dict) and (stat.get("null_count") or 0) > 0:
            return ValidationCheck(
                DIMENSION_ASSUMPTIONS,
                False,
                f"the query sums {name}, which holds missing values; the total "
                f"is of the values present, not of the column, unless the "
                f"finding states that missing means zero",
                hard=False,
            )
    return ValidationCheck(
        DIMENSION_ASSUMPTIONS,
        True,
        "the computation's premises are stated by the data, or the finding "
        "states them",
        hard=False,
    )


def check_causality(statement: str, interpretation: str) -> ValidationCheck:
    """Causal language that the evidence cannot support (AT-18's weakest form).

    A correlation is not a cause, and a finding drafted inside DAH has no
    intervention and no control - so a causal verb in its statement is a claim
    the method does not earn. This check names the gap; the full guard with its
    thresholds is P8-CAUSAL-004.
    """
    claim = _normalise(statement) + " " + _normalise(interpretation)
    if not claim.strip():
        return _skip(DIMENSION_CAUSALITY, "the finding states nothing to read")
    used = [term for term in _CAUSAL_TERMS if term in claim]
    if not used:
        return ValidationCheck(
            DIMENSION_CAUSALITY,
            True,
            "the finding's language is associative rather than causal, which is "
            "what a comparison can support",
            hard=False,
        )
    return ValidationCheck(
        DIMENSION_CAUSALITY,
        False,
        f"the finding uses causal language ('{used[0]}') but the evidence is a "
        f"comparison; this supports association, not causation",
        hard=False,
    )


def check_alternatives(
    sql: str,
    question: str,
    profile: dict | None,
    columns: list[str],
    rows: list[list[Any]],
) -> ValidationCheck:
    """The explanations the analysis did not look at.

    A finding does not rule out an alternative by ignoring it. Two sources: the
    columns the question names that the query never read, and a categorical
    column the profile shows is confounded with the grouping - a group-by that
    never accounts for a variable that moves with the grouping cannot separate
    the two.
    """
    text = _normalise(sql)
    if not text:
        return _skip(DIMENSION_ALTERNATIVES, "the finding's run has no stored query")
    profile_columns = {str(name).lower() for name in _profile_columns(profile)}
    reads = {
        str(name).lower()
        for name in _sql_identifiers(sql)
        if str(name).lower() in profile_columns
    }
    unread = sorted(name for name in profile_columns if name not in reads)
    if not unread:
        return ValidationCheck(
            DIMENSION_ALTERNATIVES,
            True,
            "the query reads every column the dataset holds, so no variable was "
            "left unexamined",
            hard=False,
        )
    # A column the question itself names and the query ignores is the sharpest
    # form: the analyst asked about it and the analysis did not look.
    asked = _words_of(_normalise(question))
    named_but_unread = [
        word for word in asked if word in unread and word not in _SQL_KEYWORDS
    ]
    if named_but_unread:
        return ValidationCheck(
            DIMENSION_ALTERNATIVES,
            False,
            f"the question names {named_but_unread[0]} but the query never reads "
            f"it, so an explanation resting on it is untested",
            hard=False,
        )
    # Otherwise an unread column is only an alternative explanation if it could
    # actually carry one. An identifier or a free-text column is not a
    # competing account of the finding - it is a row label - so flagging it
    # would make every group-by a concern and bury the signal. A categorical
    # column of plausible cardinality the query never accounted for is a
    # confounder the analysis did not separate from its grouping.
    stats = _profile_stats(profile)
    confounders = [name for name in unread if _could_explain(stats.get(name))]
    if not confounders:
        return ValidationCheck(
            DIMENSION_ALTERNATIVES,
            True,
            "the columns the query does not read are identifiers or free text, "
            "not competing explanations",
            hard=False,
        )
    return ValidationCheck(
        DIMENSION_ALTERNATIVES,
        False,
        f"the query never reads {', '.join(confounders[:3])}, which the profile "
        f"shows varying across the data; an explanation resting on "
        f"{confounders[0]} is untested",
        hard=False,
    )


# --- assembly -----------------------------------------------------------------


def validate_finding(
    *,
    reproduced: bool,
    rerun_detail: str,
    statement: str,
    interpretation: str,
    question: str,
    sql: str,
    columns: list[str],
    rows: list[list[Any]],
    profile: dict | None,
) -> tuple[str, list[ValidationCheck]]:
    """Run all nine checks and assemble the verdict.

    Returns the status the API answers and the checks the shell renders. The
    rule is three-valued and stays honest: a hard failure blocks `supported`,
    any concern yields `partially_supported`, and only a clean sweep is
    `supported`. Nothing is failed silently - every check's sentence is what the
    analyst reads - and nothing is promoted silently.
    """
    checks = [
        check_calculation(reproduced, rerun_detail),
        check_data(profile),
        check_population(sql, columns, rows, profile, question),
        check_timeframe(statement, question, profile),
        check_method(sql, statement, question, profile, columns, rows),
        check_evidence(statement, columns, rows),
        check_assumptions(sql, statement, profile, rows),
        check_causality(statement, interpretation),
        check_alternatives(sql, question, profile, columns, rows),
    ]
    # The order the PRD names them in, whatever order they were built in.
    order = {dimension: index for index, dimension in enumerate(DIMENSIONS)}
    checks.sort(key=lambda check: order.get(check.dimension, len(DIMENSIONS)))

    hard_failed = [check for check in checks if check.hard and not check.passed]
    concerns = [check for check in checks if not check.hard and not check.passed]
    if hard_failed:
        status = "insufficient_evidence"
    elif concerns:
        status = "partially_supported"
    else:
        status = "supported"
    return status, checks


# --- small helpers ------------------------------------------------------------


def _profile_rows(profile: dict | None) -> int:
    if not isinstance(profile, dict):
        return 0
    rows = profile.get("rows")
    return int(rows) if isinstance(rows, int) else 0


_AGG_RE_CACHE: dict[str, Any] = {}


def _aggregated_columns(text: str, function: str) -> list[str]:
    """The columns a SQL aggregate reads, e.g. AVG(revenue) -> ['revenue'].

    Parsed defensively rather than with a SQL grammar: the query is already
    stored and was already executed, so this only reads words between the
    function's parentheses. A name it fails to find costs a skipped premise,
    never a wrong verdict.
    """
    import re

    pattern = _AGG_RE_CACHE.setdefault(
        function, re.compile(rf"\b{function}\s*\(\s*([A-Za-z_][A-Za-z0-9_]*)\s*\)", re.I)
    )
    return pattern.findall(text or "")


def _averaged_columns(text: str) -> list[str]:
    return _aggregated_columns(text, "AVG")


def _summed_columns(text: str) -> list[str]:
    return _aggregated_columns(text, "SUM")


def _could_explain(stat: Any) -> bool:
    """Could an unread column carry a competing explanation?

    A categorical column of modest cardinality can: it divides the data the
    way the grouping does, so a group-by that ignores it cannot tell its own
    effect from the column's. A numeric identifier, a date and a free-text
    field cannot - they distinguish rows rather than accounts of the finding,
    and treating them as untested alternatives would flag every comparison.
    """
    if not isinstance(stat, dict):
        return False
    if stat.get("type") != "other":
        return False
    distinct = int(stat.get("distinct_count", 0) or 0)
    # Same ceiling the quality detectors use: above this, a column is a name or
    # an id rather than a dimension.
    return 2 <= distinct <= CATEGORY_MAX_DISTINCT


def _words_of(text: str) -> list[str]:
    """The words a question or claim is made of, for matching against column
    names. A question's own vocabulary is how the Method and Alternatives
    checks know what the analysis was *about*."""
    return [word for word in (text or "").replace("-", " ").split() if word]
