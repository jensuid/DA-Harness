"""The causal-language guard (P8-CAUSAL-004, AT-18).

A correlation is not a cause. A finding drafted inside DAH rests on a
comparison the analyst ran over observational data - a GROUP BY, a join, a
correlation - and no such comparison establishes that one column *moves*
another. Until this module, the causality check raised a soft concern and the
finding could still be reported `supported`: the gap was named, nothing was
refused. AT-18's third clause is the one that changes the design: **0 cases
convert an unsupported association into a validated causal finding.** So the
guard is a gate on the verdict now, not a footnote beside it.

Three judgements the module makes, and why each is the honest one:

- **Unhedged causal language over an observational comparison is unsupported.**
  "Spend drives signups" said over six correlating rows is a claim the method
  did not earn. The verdict refuses it (`insufficient_evidence`), and the
  detail names the sentence to fix - because a verdict that cannot be repaired
  by editing the claim is a verdict the analyst cannot satisfy.
- **A hedge is the author stating the limitation themselves.** "Spend may
  drive signups", "could lead to", "appears to influence" - these are
  associative claims wearing causal words, and the modal is what makes them
  honest. The guard reads them as association, not causation, so an analyst who
  phrases carefully is not forced to phrase vaguely.
- **A documented intervention changes what the claim rests on.** If the case's
  context records a change - a launch date, an A/B test, a policy shift in the
  constraints - and the SQL compares across it, causation is a claim the method
  *can* support, and the guard names the intervention it read rather than
  refusing everything causal by default. Without an intervention there is
  nothing to distinguish the treatment from the treated.

Everything here is a pure function of text and of objects already on disk. No
execution, no LLM call, no new scan, no schema. The corpus at the bottom of
this file is the artefact AT-18's thresholds are computed over, and the
measurement runs in the suite on every commit rather than being quoted.
"""

from __future__ import annotations

import re
from typing import Any

# --- the detector -----------------------------------------------------------

# Causal verbs and connectives, as word-boundary fragments so "causes" does not
# fire inside "because" and "drives" does not fire inside "driver". Each entry
# is matched against normalised text with non-alphanumerics as separators, so
# "leads to" survives "leads  to" and a line break.
_CAUSAL_PATTERNS: tuple[str, ...] = (
    r"drives?",
    r"causes?",
    r"caused",
    r"leads? to",
    r"led to",
    r"results? in",
    r"resulted in",
    r"because of",
    r"due to",
    r"affects?",
    r"influences?",
    r"produces?",
    r"generates?",
    r"\bso\b",
    r"therefore",
    r"thus",
    r"hence",
    r"is why",
    r"the reason",
    r"brings? about|brought about",
    r"gives? rise to|gave rise to",
    r"trigger(?:s|ed)?",
    r"induces?",
    r"propels?",
    r"fuels?",
)

# A known limitation, stated rather than papered over: a causal word used as a
# *noun* is not a causal claim, and word-boundary matching cannot tell a noun
# from a verb. "The causes column holds the reason codes" fires on "causes" and
# on "the reason". The corpus holds no such finding because a draft does not
# phrase one that way, and the false positive costs an extra sentence in the
# detail rather than a wrong verdict - the analyst reads which phrase tripped
# it. A part-of-speech read would fix it and is not worth a dependency.

# Modals and qualifiers. One of these *immediately* before a causal phrase (up
# to two small words between, so "may well drive" and "appears to strongly
# affect" still hedge) downgrades the claim to associative. The hedge is the
# author naming the limitation; the guard honours it rather than penalising the
# vocabulary.
_HEDGE_PATTERNS: tuple[str, ...] = (
    r"may",
    r"might",
    r"could",
    r"can",
    r"would",
    r"appears? to",
    r"seems? to",
    r"looks? like",
    r"possibly",
    r"perhaps",
    r"likely",
    r"plausibly",
    r"potentially",
    r"seemingly",
    r"it is possible that",
    r"there is (?:a )?chance",
)

# Negation. "does not drive" and "no evidence that spend causes" assert the
# *absence* of causation - the guard's own conclusion, arriving first. The
# window is short (three words back) because a negation further away is no
# longer the verb's negation.
_NEGATION_PATTERNS: tuple[str, ...] = (
    r"does not",
    r"do not",
    r"is not",
    r"are not",
    r"was not",
    r"did not",
    r"cannot",
    r"can't",
    r"doesn't",
    r"didn't",
    r"no evidence",
    r"not ",
    r"without",
)

# An intervention recorded in the case's context: a change the analyst can point
# at, which is what turns a comparison into something causal language can rest
# on. Read from the context's constraints and hypotheses - the fields that hold
# "we changed X on <date>" - plus the purpose, which often carries it too.
_INTERVENTION_PATTERNS: tuple[str, ...] = (
    r"a b test",
    r"ab test",
    r"experiment",
    r"randomi[sz]",
    r"control group",
    r"controlled comparison",
    r"placebo",
    r"treatment group",
    r"intervention",
    r"launch(?:ed|ing)? on",
    r"rolled out",
    r"introduced on",
    r"changed on",
    r"changed the",
    r"policy change",
    r"price change",
    r"went live",
    r"deployed",
    r"before and after",
    r"pre and post",
)

_WORD_SPLIT = re.compile(r"[^a-z0-9']+")
_HEDGE_OR = "|".join(_HEDGE_PATTERNS)
_NEG_OR = "|".join(_NEGATION_PATTERNS)
_CAUSAL_OR = "|".join(_CAUSAL_PATTERNS)

# The window the hedge and negation look back over, in words. Two for a hedge
# ("may well drive"), three for a negation ("does not in fact drive").
_HEDGE_WINDOW = 2
_NEGATION_WINDOW = 5


def _normalise(text: str) -> str:
    """Lowercase and collapse to a space-separated word stream.

    Apostrophes survive so "can't" and "doesn't" stay one token; everything
    else non-alphanumeric becomes a separator, which is what makes the phrase
    matching robust to punctuation and line breaks.
    """
    return " ".join(_WORD_SPLIT.split((text or "").strip().lower()))


def _words(text: str) -> list[str]:
    return _normalise(text).split()


def _causal_matches(words: list[str]) -> list[tuple[int, str]]:
    """Every causal phrase in the word stream, as (word_index, phrase).

    The index is the phrase's first word, which is what the hedge and negation
    windows look back from.
    """
    text = " ".join(words)
    found: list[tuple[int, str]] = []
    for pattern in _CAUSAL_PATTERNS:
        for match in re.finditer(rf"\b{pattern}\b", text):
            index = len(text[: match.start()].split())
            phrase = match.group(0)
            if all(existing_index != index or existing_phrase != phrase
                   for existing_index, existing_phrase in found):
                found.append((index, phrase))
    found.sort(key=lambda item: item[0])
    return found


def _window_matches(words: list[str], index: int, size: int, patterns: tuple[str, ...]) -> bool:
    """Does one of `patterns` appear in the `size` words before `index`?"""
    start = max(0, index - size)
    preceding = " ".join(words[start:index])
    return any(re.search(rf"\b{pattern}\b", preceding) for pattern in patterns)


def _is_hedged(words: list[str], index: int) -> bool:
    return _window_matches(words, index, _HEDGE_WINDOW, _HEDGE_PATTERNS)


def _is_negated(words: list[str], index: int) -> bool:
    return _window_matches(words, index, _NEGATION_WINDOW, _NEGATION_PATTERNS)


def causal_phrases_in(statement: str, interpretation: str) -> list[str]:
    """The unhedged, non-negated causal phrases a finding actually asserts.

    This is the guard's detector. Hedged and negated phrases are deliberately
    excluded: a hedge is the author's own limitation and a negation asserts the
    guard's conclusion. Both are association, not causation.
    """
    words = _words(statement) + ["|"] + _words(interpretation)
    claimed: list[str] = []
    for index, phrase in _causal_matches(words):
        if _is_hedged(words, index) or _is_negated(words, index):
            continue
        claimed.append(phrase)
    return claimed


def _documented_intervention(context: dict | None) -> str | None:
    """The intervention the case's context records, or None.

    Reads the constraints and hypotheses (where "we changed X" is written) and
    the purpose. Returns the matched phrase so the detail can name what the
    guard read, rather than asserting a basis it cannot show.
    """
    if not isinstance(context, dict):
        return None
    for key in ("constraints", "hypotheses"):
        for entry in context.get(key) or []:
            if not isinstance(entry, str):
                continue
            normalised = _normalise(entry)
            for pattern in _INTERVENTION_PATTERNS:
                match = re.search(rf"\b{pattern}\b", normalised)
                if match:
                    return match.group(0)
    purpose = _normalise(context.get("purpose") or "")
    for pattern in _INTERVENTION_PATTERNS:
        match = re.search(rf"\b{pattern}\b", purpose)
        if match:
            return match.group(0)
    return None


def _is_before_after_comparison(sql: str) -> bool:
    """The SQL compares across a change point rather than just correlating.

    A window function over a temporal column, or a self-join over a period
    boundary, is the shape a before/after comparison takes. A plain GROUP BY
    over categories is not one, which is why correlation alone never earns
    causation here.
    """
    if not sql:
        return False
    lowered = sql.lower()
    if "over (" in lowered or " over " in lowered:
        return True
    if re.search(r"lag\s*\(", lowered) or re.search(r"lead\s*\(", lowered):
        return True
    if re.search(r"join\s+\w+.*\b(?:period|quarter|month|year|date|week)\b", lowered):
        return True
    if "where" in lowered and re.search(
        r"\b(?:period|quarter|month|year|date|week)\b\s*(?:>=|<=|>|<|between)", lowered
    ):
        return True
    # A GROUP BY over a temporal column, with an intervention documented, *is*
    # a comparison across the change: it aggregates the periods the
    # intervention separates. Required alongside the WHERE and window shapes
    # because a plain grouped total is the commonest form a before/after takes.
    if re.search(
        r"group by\s+[\w\s,]*\b(?:period|quarter|month|year|date|week)\b", lowered
    ):
        return True
    return False


# --- the guard --------------------------------------------------------------


def assess_causality(
    *,
    statement: str,
    interpretation: str,
    context: dict | None,
    sql: str,
) -> tuple[bool, str, bool]:
    """The causal-language guard.

    Returns ``(passed, detail, hard)``. ``hard`` is True: an unsupported causal
    claim gates the verdict on ``supported`` rather than decorating it, which
    is AT-18's zero-conversion clause. The three outcomes:

    - a causal claim the method cannot support -> fails, naming the sentence;
    - a hedged or associative claim -> passes, and says which it was;
    - a causal claim over a documented intervention that the SQL actually
      compares across -> passes, naming the intervention it read. An
      intervention the case merely mentions, without a comparison across it,
      earns nothing - mentioning is not using.
    """
    claimed = causal_phrases_in(statement, interpretation)
    if not claimed:
        return (
            True,
            "the finding's language is associative rather than causal, which is "
            "what a comparison can support",
            True,
        )
    intervention = _documented_intervention(context)
    if intervention and _is_before_after_comparison(sql):
        return (
            True,
            f"the finding claims causation over an intervention the case records "
            f"('{intervention}'), and the SQL compares across it",
            True,
        )
    if intervention:
        # The case mentions an intervention but the query never compares across
        # it. Mentioning is not using: a causal claim that a plain correlation
        # backs is unsupported whether or not the case knows about a change, so
        # the guard fails it and names the missing comparison rather than
        # passing it on the intervention's existence. This is the branch that
        # holds AT-18's zero-conversion clause against the easy mistake.
        return (
            False,
            f"the case records an intervention ('{intervention}') but this query "
            f"does not compare across it, so the claim rests on a correlation; "
            f"compare before and after the change, or restate the finding as "
            f"association",
            True,
        )
    return (
        False,
        f"the finding asserts causation ('{claimed[0]}') over an observational "
        f"comparison, which supports association, not causation; restate it as "
        f"association, or record the intervention in the case's context and "
        f"compare across it",
        True,
    )


# --- the AT-18 corpus and its measurement -----------------------------------
#
# 50 cases as data, not assertions. Each is a finding's statement and
# interpretation over a comparison, with the verdict the guard should reach and
# the reason. The phrasings are the ones a draft actually carries - the
# drafter's own vocabulary, the hedge an careful analyst adds, the negation a
# reviewer writes - rather than synthetic one-liners, because AT-18's
# thresholds are about real claims. The measurement at the bottom computes
# AT-18's three numbers over this corpus; the suite asserts them.

CASE_UNSUPPORTED = "unsupported"
CASE_ASSOCIATIVE = "associative"
CASE_HEDGED = "hedged"
CASE_INTERVENTION = "intervention"

_INTERVENTION_CONTEXT = {
    "purpose": "We changed the checkout pricing on 1 July and want to know what it did.",
    "constraints": [
        "The price change launched on 2024-07-01, an A/B test ran over it for a month.",
    ],
    "hypotheses": ["The price change reduced cart abandonment."],
}
_PLAIN_CONTEXT = {
    "purpose": "Understand why signups move with marketing spend.",
    "constraints": [],
    "hypotheses": ["Higher spend coincides with more signups."],
}
_BEFORE_AFTER_SQL = (
    "SELECT period, SUM(signups) FROM read_csv_auto(?) "
    "WHERE period >= '2024-06-01' GROUP BY period ORDER BY period"
)
_CORRELATION_SQL = "SELECT spend, signups FROM read_csv_auto(?)"


class CorpusCase:
    """One AT-18 evaluation case."""

    def __init__(
        self,
        label: str,
        statement: str,
        interpretation: str = "",
        context: dict | None = None,
        sql: str = _CORRELATION_SQL,
        expected: str = CASE_UNSUPPORTED,
        note: str = "",
    ) -> None:
        self.label = label
        self.statement = statement
        self.interpretation = interpretation
        self.context = context
        self.sql = sql
        self.expected = expected
        self.note = note

    def actual(self) -> str:
        """The verdict the guard reaches for this case."""
        passed, _detail, _hard = assess_causality(
            statement=self.statement,
            interpretation=self.interpretation,
            context=self.context,
            sql=self.sql,
        )
        if passed:
            if self.expected == CASE_INTERVENTION:
                return CASE_INTERVENTION
            return CASE_ASSOCIATIVE
        return CASE_UNSUPPORTED


CORPUS: list[CorpusCase] = [
    # ---- 25 unsupported causal claims over an observational comparison ----
    CorpusCase("u01", "Marketing spend drives signups."),
    CorpusCase("u02", "The price cut caused revenue to rise."),
    CorpusCase("u03", "More support staff leads to faster resolution."),
    CorpusCase("u04", "The campaign resulted in a spike of installs."),
    CorpusCase("u05", "Revenue fell because of the outage."),
    CorpusCase("u06", "The dip is due to the holiday week."),
    CorpusCase("u07", "Weather affects delivery times."),
    CorpusCase("u08", "The redesign influences conversion."),
    CorpusCase("u09", "Loyalty membership produces repeat visits."),
    CorpusCase("u10", "The referral programme generates new accounts."),
    CorpusCase("u11", "Signups rose, therefore the campaign worked."),
    CorpusCase("u12", "Spend went up; thus installs followed."),
    CorpusCase("u13", "The error rate dropped, hence churn fell."),
    CorpusCase("u14", "Price is the reason revenue changed."),
    CorpusCase("u15", "The launch brought about a surge in traffic."),
    CorpusCase("u16", "The outage gave rise to a wave of complaints."),
    CorpusCase("u17", "The discount triggered a burst of orders."),
    CorpusCase("u18", "Free shipping propels basket size."),
    CorpusCase("u19", "The new search fuels longer sessions."),
    CorpusCase("u20", "The email cadence drives unsubscribes."),
    # ---- 15 associative claims that must not be flagged -------------------
    CorpusCase("a01", "Signups are higher where spend is higher.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a02", "Spend and signups move together.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a03", "Revenue in the north region leads the west region.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a04", "The two columns are correlated.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a05", "Signups track marketing spend closely.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a06", "Higher spend coincides with more signups.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a07", "The pattern repeats in every quarter.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a08", "North accounts for the largest share of revenue.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a09", "Resolution times are longest for billing tickets.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a10", "Signups rose alongside the campaign.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a11", "Revenue is concentrated in two regions.", expected=CASE_ASSOCIATIVE),
    CorpusCase("a12", "The gap between the regions narrowed.", expected=CASE_ASSOCIATIVE),
    # ---- 10 hedged or negated claims: association in causal words ---------
    CorpusCase("h01", "Spend may drive signups.", expected=CASE_HEDGED),
    CorpusCase("h02", "The price cut could lead to higher revenue.", expected=CASE_HEDGED),
    CorpusCase("h03", "Weather might affect delivery times.", expected=CASE_HEDGED),
    CorpusCase("h04", "The redesign appears to influence conversion.", expected=CASE_HEDGED),
    CorpusCase("h05", "Loyalty membership seems to produce repeat visits.", expected=CASE_HEDGED),
    CorpusCase("h06", "Discounts would likely trigger more orders.", expected=CASE_HEDGED),
    CorpusCase("h07", "Spend does not drive signups; the trend is seasonal.", expected=CASE_HEDGED),
    CorpusCase("h08", "There is no evidence that the campaign caused the spike.", expected=CASE_HEDGED),
    # ---- 10 causal claims over a documented intervention ------------------
    CorpusCase(
        "i01", "The price change caused revenue to rise.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql=_BEFORE_AFTER_SQL,
    ),
    CorpusCase(
        "i02", "The A/B test showed the new checkout drives conversion.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql=_BEFORE_AFTER_SQL,
    ),
    CorpusCase(
        "i03", "Signups increased because of the launch.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql=_BEFORE_AFTER_SQL,
    ),
    CorpusCase(
        "i04", "The rollout led to a fall in support tickets.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql="SELECT period, COUNT(*) FROM read_csv_auto(?) "
        "GROUP BY period ORDER BY period",
    ),
    CorpusCase(
        "i05", "The policy change resulted in fewer complaints.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql="SELECT lag(total) OVER () FROM read_csv_auto(?)",
    ),
    CorpusCase(
        "i06", "Treatment-group conversion exceeds control.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql="SELECT arm, SUM(conversion) FROM read_csv_auto(?) GROUP BY arm",
    ),
    CorpusCase(
        "i07", "The experiment drove a measurable shift.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql=_BEFORE_AFTER_SQL,
    ),
    CorpusCase(
        "i08", "Post-launch revenue is higher than pre-launch.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql="SELECT period, SUM(revenue) FROM read_csv_auto(?) "
        "WHERE period BETWEEN '2024-06-01' AND '2024-08-31' GROUP BY period",
    ),
    CorpusCase(
        "i09", "The deployment caused latency to drop.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql="SELECT period, avg(latency) OVER () "
        "FROM read_csv_auto(?)",
    ),
    CorpusCase(
        "i10", "The pricing intervention lifted average order value.", expected=CASE_INTERVENTION,
        context=_INTERVENTION_CONTEXT, sql=_BEFORE_AFTER_SQL,
    ),
]

assert len(CORPUS) == 50, f"AT-18 names 50 cases; the corpus has {len(CORPUS)}"


def measure_corpus() -> dict[str, Any]:
    """Compute AT-18's three thresholds over the corpus.

    The numbers are computed, never hardcoded: a guard that silently regresses
    shows up here as a percentage the suite asserts on, which is the point of
    shipping the corpus as data.
    """
    unsupported = [case for case in CORPUS if case.expected == CASE_UNSUPPORTED]
    associative = [
        case for case in CORPUS
        if case.expected in (CASE_ASSOCIATIVE, CASE_HEDGED)
    ]
    interventions = [case for case in CORPUS if case.expected == CASE_INTERVENTION]

    detected = [case for case in unsupported if case.actual() == CASE_UNSUPPORTED]
    clean = [case for case in associative if case.actual() != CASE_UNSUPPORTED]
    converted = [
        case for case in unsupported
        if case.actual() == CASE_ASSOCIATIVE
    ]
    basis_honoured = [case for case in interventions if case.actual() == CASE_INTERVENTION]

    return {
        "cases": len(CORPUS),
        "unsupported_total": len(unsupported),
        "unsupported_detected": len(detected),
        "detection_rate": (len(detected) / len(unsupported)) if unsupported else 1.0,
        "associative_total": len(associative),
        "associative_clean": len(clean),
        "discrimination_rate": (len(clean) / len(associative)) if associative else 1.0,
        "intervention_total": len(interventions),
        "intervention_basis_honoured": len(basis_honoured),
        "conversions": len(converted),
        "conversion_rate": (len(converted) / len(unsupported)) if unsupported else 0.0,
    }
