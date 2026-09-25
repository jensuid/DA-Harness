"""EVALUATE mode: audit existing analytical work (P7-EVAL-001).

The master specification defines three product modes. ANALYZE is the one that
exists, and P6 finished it. EVALUATE is the second: audit work that came from
somewhere else - a query, a script, a notebook cell, an AI-generated answer -
against the nine axes the specification names.

```
Question  Data  Quality  Method  Calculation
Evidence  Claim  Visualization  Limitations
```

The design principle is the same one that governs every other module: **nothing
is asserted the data does not contain**. Each axis is a check with a verdict
and a sentence a reader can act on, and every verdict is derived from the
profile, the code, or the run the code actually produced - never from the
claim's own confidence. An evaluation does not grade; a single number would
imply a precision nine heterogenous axes do not have.

Most of the machinery already existed and is reused rather than duplicated:
the read-only gate and row cap, deep profiling, rerun determinism, and the
honesty budget that bounds what a claim may quote (P3-AI-012). What did not
exist was the frame - those primitives all served the user's *own* analysis.
EVALUATE turns them on work from elsewhere, and that turn is the whole module.

Deterministic by default. No LLM decides a verdict; one may later rephrase a
sentence, never judge one.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# The generator's notion of what a piece of code reads (P3-AI-013). Reused
# rather than reimplemented: a second parser would only be a second opinion
# about what the code touches, and the generator's is the opinion the rest
# of DAH already applies to generated code.
from app.generator import _python_read_columns, _sql_identifiers, _SQL_KEYWORDS

# The verdict vocabulary. Three states, not a score: a pass is a claim the data
# supports, a concern is something a reader should weigh, a fail is a claim the
# data contradicts or the artifact cannot support.
PASS = "pass"
CONCERN = "concern"
FAIL = "fail"

# The nine axes the specification names, in the spec's own order. The order is
# the order a reader asks them in: what was asked, over what, how, whether it
# worked, and what is still unaccounted for.
AXES = (
    "question",
    "data",
    "quality",
    "method",
    "calculation",
    "evidence",
    "claim",
    "visualization",
    "limitations",
)

# Claims this short cannot be wrong, and a claim that cannot be wrong cannot be
# audited. "revenue was analysed" is a topic, not a finding.
_MIN_CLAIM_WORDS = 6


@dataclass(frozen=True)
class AxisFinding:
    """One axis, one verdict, one sentence a reader can act on."""

    axis: str
    verdict: str
    detail: str


@dataclass
class Evaluation:
    """The nine-axis audit of one submitted artifact."""

    artifact_kind: str
    claim: str
    findings: list[AxisFinding] = field(default_factory=list)

    @property
    def verdicts(self) -> dict[str, str]:
        return {finding.axis: finding.verdict for finding in self.findings}


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


def _candidate_reads(code: str, kind: str) -> set[str]:
    """The columns an artifact plausibly reads, as candidate names.

    Aliases (`AS total`), function calls (`SUM(...)`, `read_csv_auto(...)`) and
    single-quoted literals are structure rather than references, so they are
    excluded - which is what makes a candidate a *read* rather than a mention.

    Candidates are not verdicts. A name the profile does not contain may still
    be a SQL keyword, so the caller filters with the generator's keyword set
    before it calls a name invented. Filtering here instead would hide the one
    case the axis exists to catch.
    """
    if not code:
        return set()
    if kind == "python":
        return _python_read_columns(code)
    return _sql_identifiers(code)


def _null_share(column: str, stats: dict[str, Any]) -> float | None:
    column_stats = stats.get(column)
    if not isinstance(column_stats, dict):
        return None
    share = column_stats.get("null_percentage")
    return float(share) if isinstance(share, (int, float)) else None


def _is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


# The notion of magnitude a statement quotes. Digits are only a magnitude when
# they are a token, not a fragment of a longer one: a period (`2026-07`), an id
# (`ORD-100331`) or a code (`SKU-4001`) is not a number the claim states, and
# counting it split the token into two invented numbers a correct finding was
# then refused for quoting (W-015). A minus is only a sign when it starts a
# token, which is the exact confusion that turned `2026-07` into `-7`.
#
# The regex finds the run; the edges decide. A digit, a letter or a hyphen
# against either side of the run means the run is part of something larger, so
# it is not a magnitude the claim quotes.
_NUMBER_TOKEN_RE = re.compile(r"-?[0-9]+(?:[0-9]{0,2},[0-9]{3})*(?:\.[0-9]+)?")
_NUMBER_EDGE = frozenset("0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-")


def _numbers_in(text: str) -> set[float]:
    """Every numeric token a claim quotes - the same notion a draft is judged by."""
    source = text or ""
    quoted: set[float] = set()
    for match in _NUMBER_TOKEN_RE.finditer(source):
        start, end = match.start(), match.end()
        before = source[start - 1] if start > 0 else ""
        after = source[end] if end < len(source) else ""
        # A run that touches a digit, a letter or a hyphen is a fragment of a
        # longer token, and the minus is only a sign when it starts the run.
        if before in _NUMBER_EDGE or after in _NUMBER_EDGE:
            continue
        digits = match.group(0).replace(",", "")
        if digits.lstrip("-").replace(".", "", 1).isdigit():
            quoted.add(float(digits))
    return quoted


def _allowed_numbers(columns: list[str], rows: list[list[Any]]) -> set[float]:
    """The magnitudes a claim may legitimately quote.

    Reused from the drafter's honesty budget (P3-AI-012): cell values, the row
    and column counts, and how often a value repeats. A claim quoting anything
    else is quoting a number the analysis did not produce.

    A statement may also name its own result's shape - the number of groups a
    column has, or how many rows it reads - which the deterministic drafter
    writes as "N grouped value(s)" and which is true of the result, so both are
    part of the budget.
    """
    allowed = {float(len(rows)), float(len(columns))}
    for row in rows:
        for value in row:
            if _is_number(value):
                allowed.add(float(value))
    by_column = {
        column: [row[index] for row in rows if index < len(row)]
        for index, column in enumerate(columns)
    }
    for values in by_column.values():
        counts: dict[Any, int] = {}
        for value in values:
            if value is None:
                continue
            counts[value] = counts.get(value, 0) + 1
        for how_often in counts.values():
            allowed.add(float(how_often))
        allowed.add(float(len(counts)))
        allowed.add(float(len(values)))
    return allowed


def _fmt(value: float) -> str:
    return str(int(value)) if value == int(value) else str(value)


def _evaluate_question(claim: str, profile_columns: list[str]) -> AxisFinding:
    """Is a claim stated, and is it answerable from this dataset?"""
    if not claim or not claim.strip():
        return AxisFinding(
            "question", FAIL, "no claim was submitted, so there is nothing to audit"
        )
    words = [word for word in claim.split() if word]
    if len(words) < _MIN_CLAIM_WORDS:
        return AxisFinding(
            "question",
            CONCERN,
            f"the claim is only {len(words)} words - it names a topic rather than a "
            "question, and a topic cannot be wrong",
        )
    return AxisFinding(
        "question",
        PASS,
        f"the claim states a position over {len(profile_columns)} profiled column(s)",
    )


def _evaluate_data(
    code: str, kind: str, profile: dict | None
) -> tuple[AxisFinding, list[str]]:
    """Does the artifact read columns this dataset actually has?"""
    columns = _profile_columns(profile)
    if not columns:
        return (
            AxisFinding(
                "data", FAIL,
                "the dataset has no profile, so its columns are unknown",
            ),
            [],
        )
    lowered = {name.lower(): name for name in columns}
    candidates = _candidate_reads(code, kind)
    read = sorted(
        lowered[name.lower()] for name in candidates if name.lower() in lowered
    )
    # A name the code reads that the dataset does not have. SQL keywords were
    # never columns, so they are excluded; everything else is a name the
    # artifact rests on that the data cannot give it, and that is a fail -
    # the single most preventable way an analysis produces wrong numbers.
    invented = sorted(
        name
        for name in candidates
        if name.lower() not in lowered and name.lower() not in _SQL_KEYWORDS
    )
    if invented:
        return (
            AxisFinding(
                "data",
                FAIL,
                "the artifact reads column(s) the dataset does not have: "
                + ", ".join(invented),
            ),
            read,
        )
    if not read:
        return (
            AxisFinding(
                "data",
                CONCERN,
                "the artifact names no column from this dataset - it may be "
                "generic code, or it may read from a source that is not this one",
            ),
            [],
        )
    return (
        AxisFinding(
            "data",
            PASS,
            f"the artifact reads {len(read)} column(s) present in the profile: "
            + ", ".join(read),
        ),
        read,
    )


def _evaluate_quality(
    profile: dict | None, read_columns: list[str]
) -> AxisFinding:
    """Do the profile's own caveats reach the verdict?"""
    stats = _profile_stats(profile)
    total_rows = profile.get("rows") if isinstance(profile, dict) else None
    if not isinstance(total_rows, int) or total_rows <= 0 or not read_columns:
        return AxisFinding(
            "quality", CONCERN, "no profiled rows to judge data quality against"
        )
    heavy = []
    for column in read_columns:
        share = _null_share(column, stats)
        # A column this empty turns a claim over it into a claim over mostly
        # nothing. Surfaced as a limitation first, and a concern when it is
        # material - 30% is the threshold the profile's own stat reporting
        # treats as notable.
        if share is not None and share >= 30.0:
            heavy.append(f"{column} is {share:g}% null")
    duplicates = profile.get("duplicate_rows") if isinstance(profile, dict) else None
    dup_share = (
        round(float(duplicates) / total_rows * 100, 1)
        if isinstance(duplicates, int) and total_rows
        else 0.0
    )
    sentences = []
    verdict = PASS
    if heavy:
        verdict = CONCERN
        sentences.append("; ".join(heavy))
    if dup_share >= 10.0:
        verdict = CONCERN
        sentences.append(
            f"{dup_share:g}% of the dataset's rows are exact duplicates of an earlier row"
        )
    if not sentences:
        return AxisFinding(
            "quality",
            PASS,
            f"the profiled columns the artifact reads carry no material null or duplicate load",
        )
    return AxisFinding("quality", verdict, "; ".join(sentences))


def _evaluate_method(
    run: dict, code: str, deterministic: bool
) -> AxisFinding:
    """Read-only, bounded, and reproducible-by-construction?"""
    problems = []
    if not deterministic:
        # The artifact's result depends on engine-internal ordering. A rerun
        # could disagree without anything in the data changing, so a reader
        # cannot check the work by doing it again.
        problems.append(
            "the result is unordered, so its row order is not a property of the data "
            "and a rerun may present it differently"
        )
    truncated = run.get("truncated")
    if truncated:
        problems.append(
            "the result is truncated at the row cap, so any total it implies is a "
            "partial one"
        )
    if not problems:
        return AxisFinding(
            "method",
            PASS,
            "the artifact is read-only, bounded, and its result is reproducible",
        )
    return AxisFinding(
        "method",
        CONCERN,
        "; ".join(problems),
    )


def _evaluate_calculation(reproduced: bool, error: str | None) -> AxisFinding:
    """Did the code run, and does it run the same way twice?"""
    if error:
        return AxisFinding(
            "calculation",
            FAIL,
            f"the artifact does not run: {error}",
        )
    if not reproduced:
        return AxisFinding(
            "calculation",
            FAIL,
            "the artifact was executed twice and the two results disagree - the "
            "work does not reproduce, so no claim resting on it can be checked",
        )
    return AxisFinding(
        "calculation",
        PASS,
        "the artifact executes and a second execution produced the same result",
    )


def _evaluate_evidence(
    claim: str, columns: list[str], rows: list[list[Any]]
) -> AxisFinding:
    """Is every magnitude the claim quotes one the run actually produced?"""
    quoted = _numbers_in(claim)
    if not quoted:
        return AxisFinding(
            "evidence",
            CONCERN,
            "the claim quotes no magnitude, so there is no number to check against "
            "the result",
        )
    allowed = _allowed_numbers(columns, rows)
    invented = sorted(value for value in quoted if value not in allowed)
    if not invented:
        return AxisFinding(
            "evidence",
            PASS,
            f"every magnitude the claim quotes appears in the result "
            f"({_fmt(len(allowed))} value(s) the run provides)",
        )
    return AxisFinding(
        "evidence",
        FAIL,
        "the claim quotes values absent from the result: "
        + ", ".join(_fmt(value) for value in invented),
    )


def _evaluate_claim(claim: str, rows: list[list[Any]]) -> AxisFinding:
    """Is the claim specific enough to be wrong?"""
    if not claim or not claim.strip():
        return AxisFinding("claim", FAIL, "there is no claim to evaluate")
    lowered = claim.lower()
    directional = any(
        word in lowered
        for word in (
            "declin", "increas", "decreas", "grew", "fell", "rose", "drop",
            "higher", "lower", "more", "less", "most", "fewer", "doubled",
            "halved", "fell", "rose", "shrank",
        )
    )
    has_magnitude = bool(_numbers_in(claim))
    if directional or has_magnitude:
        what = "a direction" if directional else "a magnitude"
        return AxisFinding(
            "claim",
            PASS,
            f"the claim is specific enough to be wrong - it states {what}, so the "
            "data can disagree with it",
        )
    if len([word for word in claim.split() if word]) < _MIN_CLAIM_WORDS:
        return AxisFinding(
            "claim",
            CONCERN,
            "the claim is too short to commit to anything, so nothing the data "
            "shows could contradict it",
        )
    return AxisFinding(
        "claim",
        CONCERN,
        "the claim asserts no direction and quotes no magnitude - it reports a "
        "topic rather than a result, so it cannot be falsified by the data",
    )


def _evaluate_visualization(
    columns: list[str], rows: list[list[Any]], chart_axes: list[str] | None
) -> AxisFinding:
    """Is the result chartable, and does a chart match it?

    A chart is not required. An honest "no chart, and none needed" is a valid
    verdict, because the numbers in a table are checkable without one - what
    would be dishonest is claiming a chart supports a result it does not
    describe, which is what the axis-matching check exists to catch.
    """
    if not columns or not rows:
        return AxisFinding(
            "visualization",
            CONCERN,
            "the result has nothing to plot",
        )
    if not chart_axes:
        return AxisFinding(
            "visualization",
            PASS,
            "no chart exists for this result and none is required - the numbers "
            "are checkable from the table",
        )
    unknown = sorted(axis for axis in chart_axes if axis not in columns)
    if unknown:
        return AxisFinding(
            "visualization",
            FAIL,
            "a chart exists whose axes are not this result's columns: "
            + ", ".join(unknown),
        )
    return AxisFinding(
        "visualization",
        PASS,
        "a chart exists over this run's own columns: " + ", ".join(chart_axes),
    )


def _evaluate_limitations(findings: list[AxisFinding]) -> AxisFinding:
    """Every caveat, stated as sentences rather than as an error code."""
    caveats = [
        finding.detail
        for finding in findings
        if finding.axis != "limitations" and finding.verdict != PASS
    ]
    if not caveats:
        return AxisFinding(
            "limitations",
            PASS,
            "no material limitations: every axis passed",
        )
    return AxisFinding(
        "limitations",
        CONCERN,
        f"{len(caveats)} limitation(s): " + " | ".join(caveats),
    )


def evaluate(
    *,
    artifact_kind: str,
    code: str,
    claim: str,
    profile: dict | None,
    run: dict,
    reproduced: bool,
    run_error: str | None = None,
    deterministic: bool = True,
    chart_axes: list[str] | None = None,
) -> Evaluation:
    """Audit one artifact against the nine axes.

    Pure: takes the profile and the run the caller already produced, returns
    findings, writes nothing. The caller executes the artifact through the
    existing run engine - never a second code path - so the read-only gate, the
    row cap and the hard sandbox are the same ones every other run answers to.

    `chart_axes` are the axes of a chart rendered from this run (x, y and
    series), or None when no chart exists - the caller's record of what a
    chart actually plots, so the axis check compares against the result
    rather than trusting that a chart exists at all.
    `deterministic` is the caller's judgement of whether the result's row order
    is a property of the data (an ORDER BY is present, or the result is a
    single-row aggregate). `reproduced` is whether a second execution agreed.
    """
    findings: list[AxisFinding] = []
    findings.append(_evaluate_question(claim, _profile_columns(profile)))

    data_finding, read_columns = _evaluate_data(code, artifact_kind, profile)
    findings.append(data_finding)
    findings.append(_evaluate_quality(profile, read_columns))
    findings.append(_evaluate_method(run, code, deterministic))
    findings.append(_evaluate_calculation(reproduced, run_error))

    columns = run.get("columns") if isinstance(run, dict) else None
    rows = run.get("rows") if isinstance(run, dict) else None
    columns = [str(name) for name in columns] if isinstance(columns, list) else []
    rows = [list(row) for row in rows] if isinstance(rows, list) else []

    findings.append(_evaluate_evidence(claim, columns, rows))
    findings.append(_evaluate_claim(claim, rows))
    findings.append(_evaluate_visualization(columns, rows, chart_axes))
    findings.append(_evaluate_limitations(findings))

    return Evaluation(
        artifact_kind=artifact_kind,
        claim=claim,
        findings=findings,
    )
