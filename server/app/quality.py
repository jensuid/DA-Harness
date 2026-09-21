"""Data-quality detection beyond missingness (P8-QUALITY-002, AT-08/AT-09).

The profiler already counts nulls and duplicate rows. The PRD names seven
defect classes; this module gives all seven a detector and gives every issue
an *impact* sentence (AT-09) - not "1 null value(s)" but "revenue contains
12.5% missing values; averages and totals over it may be understated."

Everything is a pure function of numbers the profile already holds plus
bounded, targeted queries the profiler makes once (see analysis.py's
_quality_samples). No detector guesses what the data *should* look like: an
issue is raised only on measured evidence, which is how the false-positive
budget (AT-08: <= 5%) is held. Nothing here is an LLM; impact sentences are
templated from the observed numbers (DEC-001), so a dataset always yields the
same warnings.

The five new classes and the evidence each needs:

  invalid_types        one scan counting how many values cast to the type the
                       column mostly holds
  inconsistent_categories  a low-cardinality column's value counts
  date_gaps            a temporal column's distinct values
  extreme_values       the few largest and smallest values (top-k, not a scan)
  insufficient_coverage    row count, plus a categorical column's value counts
"""

from __future__ import annotations

import datetime as _dt
from typing import Any

# The PRD's seven defect classes (AT-08). The first two existed as counts
# before this task; the rest are new. These names are the contract the shell
# and the validation layer key on, and the golden suite (P8-GOLDEN-005) will
# measure them.
CLASS_MISSING_VALUES = "missing_values"
CLASS_DUPLICATE_ROWS = "duplicate_rows"
CLASS_INVALID_TYPES = "invalid_types"
CLASS_INCONSISTENT_CATEGORIES = "inconsistent_categories"
CLASS_DATE_GAPS = "date_gaps"
CLASS_EXTREME_VALUES = "extreme_values"
CLASS_INSUFFICIENT_COVERAGE = "insufficient_coverage"

ALL_CLASSES = (
    CLASS_MISSING_VALUES,
    CLASS_DUPLICATE_ROWS,
    CLASS_INVALID_TYPES,
    CLASS_INCONSISTENT_CATEGORIES,
    CLASS_DATE_GAPS,
    CLASS_EXTREME_VALUES,
    CLASS_INSUFFICIENT_COVERAGE,
)

# A category column with more distinct values than this is a name or an id, not
# a dimension - consistency and dominance checks on free text are noise.
CATEGORY_MAX_DISTINCT = 20

# A temporal series needs at least this many distinct points before a gap in
# it means anything; three is the smallest series that can have a hole.
MIN_TEMPORAL_POINTS = 3

# The largest value must exceed the runner-up by this multiple to be an
# extreme. Comparing against the *next* value rather than a mean is the point:
# an outlier inflates the very statistics a z-score would use, so the mean is
# the wrong yardstick for the value that moved it.
EXTREME_MULTIPLE = 10.0

# Below this many rows a comparison rests on very little. Deliberately small:
# this catches "the calculation runs and the answer means nothing", not "small
# data is bad".
MIN_ROWS_FOR_COMPARISON = 5

# When one category covers this share of a categorical column, a group-by is
# really about that one group.
DOMINANT_CATEGORY_SHARE = 0.9

# How many of the largest / smallest values to fetch for the extreme check.
_EXTREME_K = 5

class QualityIssue:
    """One detected defect, with the sentence that says what it costs.

    `observed` is the measured fact; `impact` is what it does to an analysis
    built on this column. AT-09 is the second sentence and it is the one an
    analyst acts on, so it is never empty.
    """

    def __init__(
        self,
        kind: str,
        observed: str,
        impact: str,
        column: str | None = None,
        severity: str = "medium",
    ) -> None:
        self.kind = kind
        self.column = column
        self.severity = severity
        self.observed = observed
        self.impact = impact

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "column": self.column,
            "severity": self.severity,
            "observed": self.observed,
            "impact": self.impact,
        }

    def __eq__(self, other: object) -> bool:
        return isinstance(other, QualityIssue) and self.to_dict() == other.to_dict()

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"QualityIssue({self.kind!r}, column={self.column!r}, {self.severity!r})"


def _percent(count: int, total: int) -> float:
    """A percentage rounded to one place, or 0.0 when there is nothing to divide."""
    if total <= 0:
        return 0.0
    return round(count / total * 100.0, 1)


def _fmt(value: Any) -> str:
    """Format a measured value for a sentence, trimming float noise."""
    if isinstance(value, float) and value.is_integer():
        return f"{value:.1f}"
    return f"{value}"


# --- the two pre-existing classes, now with impacts --------------------------


def missing_value_issues(stats: dict[str, dict], total_rows: int) -> list[QualityIssue]:
    """Nulls, per column, and what they cost an aggregate over that column.

    The count existed before; the impact is the new part. A null in a measure
    column understates every SUM and AVG the generator proposes, while a null
    in a dimension silently shrinks the groups a GROUP BY produces - different
    consequences, so different sentences.
    """
    issues: list[QualityIssue] = []
    if total_rows <= 0:
        return issues
    for name, stat in stats.items():
        null_count = int(stat.get("null_count", 0) or 0)
        if null_count <= 0:
            continue
        pct = _percent(null_count, total_rows)
        if stat.get("type") == "numeric":
            impact = (
                f"{name} contains {pct}% missing values; averages and totals "
                f"over it may be understated."
            )
        else:
            impact = (
                f"{name} contains {pct}% missing values; rows may be silently "
                f"excluded from comparisons grouped by it."
            )
        issues.append(
            QualityIssue(
                CLASS_MISSING_VALUES,
                f"{null_count} of {total_rows} values are missing.",
                impact,
                column=name,
                severity="high" if pct >= 20 else "medium",
            )
        )
    return issues


def duplicate_row_issues(duplicate_rows: int, total_rows: int) -> list[QualityIssue]:
    """Exact duplicate rows, and what they do to a denominator.

    The count existed before; the impact is the new part. A duplicate inflates
    the denominator of every rate and every average, so a comparison of totals
    compares more than the analyst thinks.
    """
    if duplicate_rows <= 0 or total_rows <= 0:
        return []
    pct = _percent(duplicate_rows, total_rows)
    return [
        QualityIssue(
            CLASS_DUPLICATE_ROWS,
            f"{duplicate_rows} of {total_rows} rows are exact duplicates of an "
            f"earlier row.",
            f"Counts and rates over the full dataset may be inflated by up to "
            f"{pct}%; count distinct rows when a total matters.",
            severity="high" if pct >= 10 else "medium",
        )
    ]


# --- the five new classes ----------------------------------------------------


def invalid_type_issues(
    stats: dict[str, dict], castability: dict[str, tuple[int, int, int]]
) -> list[QualityIssue]:
    """A column typed `other` that is mostly numeric or temporal, but not entirely.

    This is the defect that breaks a calculation *silently*: DuckDB types the
    column VARCHAR, the SQL still runs, and a SUM yields NULL or a comparison
    drops the row instead of erroring. `castability` holds, per column, the
    counts `(non_null, numeric_casts, datetime_casts)` from one scan, so this
    detector costs no query of its own.

    A column that is entirely numbers would have been typed numeric by DuckDB,
    so a VARCHAR column that is mostly-castable is the mixed-type case - and a
    column of names casts to neither, so it is correctly left alone.
    """
    issues: list[QualityIssue] = []
    for name, stat in stats.items():
        if stat.get("type") != "other":
            continue
        counts = castability.get(name)
        if not counts:
            continue
        non_null, numeric_ok, datetime_ok = counts
        if non_null <= 0:
            continue
        castable = max(numeric_ok, datetime_ok)
        share = castable / non_null
        # Mostly-castable but not wholly so: the mixed-type case. A column
        # that is 100% castable was typed `other` for another reason (a
        # recovered read, say) and is not a defect.
        if share < 0.5 or castable >= non_null:
            continue
        bad = non_null - castable
        issues.append(
            QualityIssue(
                CLASS_INVALID_TYPES,
                f"{bad} of {non_null} non-null values in {name} do not read as "
                f"the type the other {castable} values hold "
                f"({_percent(castable, non_null)}% consistent).",
                f"{name} does not behave as one type in SQL: aggregates and "
                f"comparisons over it may silently exclude or misread those "
                f"rows.",
                column=name,
                severity="high",
            )
        )
    return issues


def inconsistent_category_issues(
    stats: dict[str, dict], value_counts: dict[str, dict[str, int]]
) -> list[QualityIssue]:
    """Category values that differ only by case or whitespace.

    "north" and "North" are one region to an analyst and two to a GROUP BY, so
    a comparison by region splits a group without any error. Detected from the
    column's value counts: normalise each value and look for two distinct
    spellings that collide. Only low-cardinality columns are candidates - a
    free-text field has no consistent spelling to violate.
    """
    issues: list[QualityIssue] = []
    for name, stat in stats.items():
        if stat.get("type") != "other":
            continue
        distinct = int(stat.get("distinct_count", 0) or 0)
        if distinct < 2 or distinct > CATEGORY_MAX_DISTINCT:
            continue
        counts = value_counts.get(name)
        if not counts:
            continue
        normalised: dict[str, set[str]] = {}
        for value in counts:
            key = str(value).strip().casefold()
            normalised.setdefault(key, set()).add(str(value))
        collisions = {
            key: spellings
            for key, spellings in normalised.items()
            if len(spellings) > 1
        }
        if not collisions:
            continue
        spellings = sorted(next(iter(collisions.values())))
        issues.append(
            QualityIssue(
                CLASS_INCONSISTENT_CATEGORIES,
                f"{name} has {len(collisions)} categor{'y' if len(collisions) == 1 else 'ies'} "
                f"with inconsistent spelling; for example {spellings[0]!r} and "
                f"{spellings[1]!r} are the same value.",
                f"Grouping by {name} splits one category across several groups, "
                f"understating each; normalise the values before comparing.",
                column=name,
                severity="medium",
            )
        )
    return issues


def date_gap_issues(
    stats: dict[str, dict], distinct_values: dict[str, list[Any]]
) -> list[QualityIssue]:
    """A temporal column with a gap in an otherwise regular series.

    The defect that makes a period-over-period comparison compare different
    windows without erroring: each period looks present, and only the sequence
    shows the hole. Detected by asking whether the gaps between consecutive
    distinct values are all the same size - a daily series that jumps a week
    has a gap, a series of irregular-but-fine events does not, and the mode of
    the steps is what tells them apart.
    """
    issues: list[QualityIssue] = []
    for name, stat in stats.items():
        if stat.get("type") != "temporal":
            continue
        raw = distinct_values.get(name, [])
        if len(raw) < MIN_TEMPORAL_POINTS:
            continue
        parsed = sorted(
            {_as_datetime(v) for v in raw if _as_datetime(v) is not None}
        )
        if len(parsed) < MIN_TEMPORAL_POINTS:
            continue
        steps = [
            (parsed[i + 1] - parsed[i]).total_seconds()
            for i in range(len(parsed) - 1)
        ]
        if not steps or min(steps) <= 0:
            continue
        # The usual step is the mode. A gap is a step more than twice it - not
        # merely a different step, which is how an irregular series is left
        # alone.
        usual = max(set(steps), key=steps.count)
        gaps = [s for s in steps if s > usual * 2]
        if not gaps:
            continue
        largest = max(gaps)
        unit, amount = _human_interval(largest)
        issues.append(
            QualityIssue(
                CLASS_DATE_GAPS,
                f"{name} has {len(gaps)} interval(s) at least twice the usual "
                f"step; the largest is {amount:.1f} {unit}.",
                f"A period-over-period comparison over {name} may treat "
                f"non-adjacent windows as consecutive.",
                column=name,
                severity="medium",
            )
        )
    return issues


def extreme_value_issues(
    stats: dict[str, dict], extremes: dict[str, dict[str, list[float]]]
) -> list[QualityIssue]:
    """A numeric column whose largest or smallest value dwarfs the rest.

    The average is the first thing the generator reaches for, and one extreme
    value moves it enough to change the story. Detected from the few largest
    and smallest values rather than a scan: the end value is compared against
    the next-distinct value in the same direction, because an outlier inflates
    the very mean and deviation a z-score would measure it with.
    """
    issues: list[QualityIssue] = []
    for name, stat in stats.items():
        if stat.get("type") != "numeric":
            continue
        ends = extremes.get(name)
        if not ends:
            continue
        # `top` is descending from the largest, `bottom` ascending from the
        # smallest; in both the first element is the candidate extreme.
        found = _extreme_at_end(ends.get("top", [])) or _extreme_at_end(
            ends.get("bottom", [])
        )
        if not found:
            continue
        value, multiple, is_max = found
        direction = "largest" if is_max else "smallest"
        issues.append(
            QualityIssue(
                CLASS_EXTREME_VALUES,
                f"The {direction} value in {name} ({_fmt(value)}) is "
                f"{multiple:.1f}x the next-{direction} value.",
                f"Averages over {name} are pulled by this extreme value; a "
                f"median may describe the typical value better.",
                column=name,
                severity="medium",
            )
        )
    return issues


def _extreme_at_end(ordered: list[float]) -> tuple[float, float, bool] | None:
    """The first element of an end-ordered list dwarfs its neighbour.

    `ordered` runs from the candidate extreme inward - descending for a
    maximum, ascending for a minimum - so the candidate is element 0 and its
    neighbour is the first *different* value: a run of ties is a repeated
    value, not an extreme one. Returns None when the end is not extreme, or
    when the comparison is undefined (nothing to compare against, or a
    neighbour of zero).
    """
    cleaned = [float(v) for v in ordered if v is not None]
    if len(cleaned) < 2:
        return None
    end = cleaned[0]
    neighbour = next((v for v in cleaned[1:] if v != end), None)
    if neighbour is None:
        return None
    # A magnitude comparison, so both arms - a towering maximum and a depthless
    # minimum - reduce to one test on absolute values.
    if neighbour == 0:
        return None
    if abs(end) < abs(neighbour) * EXTREME_MULTIPLE:
        return None
    return end, abs(end) / abs(neighbour), end > neighbour


def insufficient_coverage_issues(
    stats: dict[str, dict],
    total_rows: int,
    value_counts: dict[str, dict[str, int]],
) -> list[QualityIssue]:
    """The data cannot support the comparison the question implies.

    Two shapes: too few rows for any comparison to mean anything, and a
    categorical column so dominated by one value that a group-by is really
    about that one group. Both are defects of *coverage* rather than of values
    - the calculation runs, and the answer is still not trustworthy.
    """
    issues: list[QualityIssue] = []
    if 0 < total_rows < MIN_ROWS_FOR_COMPARISON:
        issues.append(
            QualityIssue(
                CLASS_INSUFFICIENT_COVERAGE,
                f"The dataset holds {total_rows} row(s).",
                f"Comparisons and trends over so few rows rest on very little "
                f"evidence; treat results as provisional.",
                severity="medium",
            )
        )
    for name, stat in stats.items():
        if stat.get("type") != "other":
            continue
        distinct = int(stat.get("distinct_count", 0) or 0)
        if distinct < 2 or distinct > CATEGORY_MAX_DISTINCT:
            continue
        counts = value_counts.get(name)
        if not counts:
            continue
        total = sum(counts.values())
        if total <= 0:
            continue
        dominant_value, dominant_count = max(counts.items(), key=lambda kv: kv[1])
        if dominant_count / total < DOMINANT_CATEGORY_SHARE:
            continue
        issues.append(
            QualityIssue(
                CLASS_INSUFFICIENT_COVERAGE,
                f"{_percent(dominant_count, total)}% of {name} values are "
                f"{dominant_value!r}; the other {distinct - 1} categories "
                f"account for {total - dominant_count} row(s).",
                f"A comparison grouped by {name} mostly describes "
                f"{dominant_value!r}; the other groups are too small to "
                f"compare.",
                column=name,
                severity="medium",
            )
        )
    return issues


# --- interval formatting -----------------------------------------------------


def _as_datetime(value: Any) -> _dt.datetime | None:
    """Coerce a profiled value to a datetime, or None when it is not one.

    DuckDB returns real date/datetime objects for a typed temporal column; the
    string branch covers a VARCHAR column holding dates, which is this
    detector's actual subject - and the reason the parser set is tried, not
    assumed.
    """
    if isinstance(value, _dt.datetime):
        return value
    if isinstance(value, _dt.date):
        return _dt.datetime(value.year, value.month, value.day)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        for parser in (
            _dt.datetime.fromisoformat,
            lambda s: _dt.datetime.strptime(s, "%Y-%m-%d"),
            lambda s: _dt.datetime.strptime(s, "%m/%d/%Y"),
            lambda s: _dt.datetime.strptime(s, "%d/%m/%Y"),
        ):
            try:
                return parser(text)
            except ValueError:
                continue
    return None


def _human_interval(seconds: float) -> tuple[str, float]:
    """Describe an interval in the largest unit that makes it readable."""
    if seconds >= 86400:
        return "days", seconds / 86400.0
    if seconds >= 3600:
        return "hours", seconds / 3600.0
    if seconds >= 60:
        return "minutes", seconds / 60.0
    return "seconds", seconds


def assess_quality(
    stats: dict[str, dict],
    total_rows: int,
    duplicate_rows: int,
    samples: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Run every detector and return the issues, worst first.

    `samples` collects the bounded query results the new classes need:
    `castability`, `value_counts`, `distinct_values` and `extremes`. The two
    pre-existing classes need none of them. Severity orders the list, so the
    first thing an analyst reads is the issue most likely to invalidate the
    answer they are about to compute.
    """
    samples = samples or {}
    castability = samples.get("castability", {})
    value_counts = samples.get("value_counts", {})
    distinct_values = samples.get("distinct_values", {})
    extremes = samples.get("extremes", {})

    issues: list[QualityIssue] = []
    issues += missing_value_issues(stats, total_rows)
    issues += duplicate_row_issues(duplicate_rows, total_rows)
    issues += invalid_type_issues(stats, castability)
    issues += inconsistent_category_issues(stats, value_counts)
    issues += date_gap_issues(stats, distinct_values)
    issues += extreme_value_issues(stats, extremes)
    issues += insufficient_coverage_issues(stats, total_rows, value_counts)

    rank = {"high": 0, "medium": 1, "low": 2}
    issues.sort(
        key=lambda issue: (rank.get(issue.severity, 3), issue.kind, issue.column or "")
    )
    return [issue.to_dict() for issue in issues]
