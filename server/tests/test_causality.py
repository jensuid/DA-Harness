"""The causal-language guard, measured (P8-CAUSAL-004, AT-18).

AT-18 is a measurement contract, not a behaviour: across 50 cases, >= 95% of
unsupported causal claims are flagged, >= 95% distinguish association from
causation, and **0** convert an unsupported association into a validated causal
finding. The corpus lives in `app.causality` as data; these tests compute the
three numbers over it and assert them, so a regression shows up as a number
that fails rather than a threshold that was quietly missed.
"""

from app import causality
from app import validation


# --- the AT-18 measurement over the 50-case corpus -------------------------


def test_the_corpus_has_the_fifty_cases_at18_names() -> None:
    assert len(causality.CORPUS) == 50, (
        f"AT-18 names 50 cases; the corpus holds {len(causality.CORPUS)}. Adding "
        "or removing a case changes the denominators of every threshold below."
    )


def test_at18_detection_rate_meets_95_percent() -> None:
    measured = causality.measure_corpus()
    assert measured["detection_rate"] >= 0.95, (
        f"AT-18 requires >= 95% of unsupported causal claims flagged; the corpus "
        f"measures {measured['detection_rate']:.0%} "
        f"({measured['unsupported_detected']} of {measured['unsupported_total']})."
    )


def test_at18_discrimination_rate_meets_95_percent() -> None:
    measured = causality.measure_corpus()
    assert measured["discrimination_rate"] >= 0.95, (
        f"AT-18 requires >= 95% discrimination between association and causation; "
        f"the corpus measures {measured['discrimination_rate']:.0%} "
        f"({measured['associative_clean']} of {measured['associative_total']})."
    )


def test_at18_zero_conversions_is_held() -> None:
    """The clause the guard exists for: no unsupported claim becomes a pass."""
    measured = causality.measure_corpus()
    assert measured["conversions"] == 0, (
        f"AT-18 allows 0 conversions of an unsupported association into a "
        f"validated causal finding; the corpus reports {measured['conversions']}."
    )


def test_every_corpus_case_reaches_its_expected_verdict() -> None:
    """The guard's verdict per case, so a single regression names its case."""
    failures = []
    for case in causality.CORPUS:
        actual = case.actual()
        if case.expected == causality.CASE_UNSUPPORTED:
            ok = actual == causality.CASE_UNSUPPORTED
        else:
            ok = actual != causality.CASE_UNSUPPORTED
        if not ok:
            failures.append(f"{case.label} ({case.expected} -> {actual}): {case.statement!r}")
    assert not failures, "\n".join(failures)


def test_the_measurement_is_computed_not_hardcoded() -> None:
    """A guard that quotes its threshold without computing it cannot regress."""
    measured = causality.measure_corpus()
    # Recompute one number independently of the module's own arithmetic.
    unsupported = [c for c in causality.CORPUS if c.expected == causality.CASE_UNSUPPORTED]
    detected = [c for c in unsupported if c.actual() == causality.CASE_UNSUPPORTED]
    independent = len(detected) / len(unsupported)
    assert measured["detection_rate"] == independent


# --- the detector's judgements, one path at a time -------------------------


def test_an_unhedged_causal_claim_over_a_comparison_is_refused() -> None:
    passed, detail, hard = causality.assess_causality(
        statement="Marketing spend drives signups.",
        interpretation="",
        context=None,
        sql="SELECT spend, signups FROM read_csv_auto(?)",
    )
    assert passed is False
    assert hard is True
    assert "association" in detail
    assert "drives" in detail


def test_a_hedge_is_the_authors_own_limitation_and_passes() -> None:
    for statement in (
        "Spend may drive signups.",
        "The price cut could lead to higher revenue.",
        "Weather might affect delivery times.",
        "The redesign appears to influence conversion.",
    ):
        passed, _detail, _hard = causality.assess_causality(
            statement=statement,
            interpretation="",
            context=None,
            sql="SELECT a, b FROM read_csv_auto(?)",
        )
        assert passed is True, f"a hedged claim is associative: {statement!r}"


def test_a_negation_asserts_the_guards_own_conclusion_and_passes() -> None:
    for statement in (
        "Spend does not drive signups; the trend is seasonal.",
        "There is no evidence that the campaign caused the spike.",
        "The outage was not the reason revenue fell.",
        "Churn cannot be attributed to onboarding alone.",
    ):
        passed, _detail, _hard = causality.assess_causality(
            statement=statement,
            interpretation="",
            context=None,
            sql="SELECT a, b FROM read_csv_auto(?)",
        )
        assert passed is True, f"a negated claim asserts no causation: {statement!r}"


def test_an_intervention_the_sql_compares_across_supports_causation() -> None:
    passed, detail, hard = causality.assess_causality(
        statement="The price change caused revenue to rise.",
        interpretation="",
        context={
            "purpose": "",
            "constraints": ["The price change launched on 2024-07-01."],
            "hypotheses": [],
        },
        sql="SELECT period, SUM(revenue) FROM read_csv_auto(?) "
            "WHERE period >= '2024-06-01' GROUP BY period",
    )
    assert passed is True
    assert hard is True
    assert "launched on" in detail


def test_an_intervention_the_sql_ignores_still_refuses_the_claim() -> None:
    """Mentioning a change is not using it - the branch AT-18 turns on."""
    passed, detail, _hard = causality.assess_causality(
        statement="The price change caused revenue to rise.",
        interpretation="",
        context={
            "purpose": "",
            "constraints": ["The price change launched on 2024-07-01."],
            "hypotheses": [],
        },
        sql="SELECT region, SUM(revenue) FROM read_csv_auto(?) GROUP BY region",
    )
    assert passed is False
    assert "does not compare across it" in detail


def test_causal_words_inside_larger_words_do_not_fire() -> None:
    """A word-boundary match: 'driver' is not 'drives', 'because' is not 'causes'."""
    for statement in (
        "The driver of revenue is the north region.",
        "Resolution times track first-response cadence.",
        "The producer region is the north.",
    ):
        phrases = causality.causal_phrases_in(statement, "")
        assert phrases == [], f"a non-causal use must not fire: {statement!r} -> {phrases}"


def test_an_intervention_in_the_purpose_is_read() -> None:
    passed, detail, _hard = causality.assess_causality(
        statement="The rollout led to a fall in support tickets.",
        interpretation="",
        context={
            "purpose": "We ran an A/B test on the help centre and want its effect.",
            "constraints": ["The A/B test ran over the help-centre change."],
            "hypotheses": [],
        },
        sql="SELECT period, COUNT(*) FROM read_csv_auto(?) GROUP BY period",
    )
    assert passed is True
    assert "a b test" in detail


def test_an_associative_statement_reports_association() -> None:
    passed, detail, _hard = causality.assess_causality(
        statement="Signups are higher where spend is higher.",
        interpretation="",
        context=None,
        sql="SELECT spend, signups FROM read_csv_auto(?)",
    )
    assert passed is True
    assert "associative" in detail


# --- the guard as a validation dimension ------------------------------------


def test_the_guard_gates_the_verdict_through_validate_finding() -> None:
    """A causal claim the method cannot support reaches insufficient_evidence."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="Spend drives signups.",
        interpretation="",
        question="Do signups follow spend?",
        sql="SELECT spend, signups FROM read_csv_auto(?)",
        columns=["spend", "signups"],
        rows=[[100.0, 40.0], [200.0, 85.0]],
        profile={
            "rows": 2,
            "columns": ["spend", "signups"],
            "stats": {
                "spend": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "signups": {"type": "numeric", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
        context=None,
    )
    causality_check = [c for c in checks if c.dimension == validation.DIMENSION_CAUSALITY][0]
    assert causality_check.passed is False
    assert causality_check.hard is True
    assert status == "insufficient_evidence"


def test_a_hedged_finding_can_still_be_supported() -> None:
    """The guard does not force careful phrasing into a refusal."""
    status, checks = validation.validate_finding(
        reproduced=True,
        rerun_detail="rerun matches stored result",
        statement="Spend may drive signups, and they certainly move together.",
        interpretation="",
        question="Do signups follow spend?",
        sql="SELECT spend, signups FROM read_csv_auto(?)",
        columns=["spend", "signups"],
        rows=[[100.0, 40.0], [200.0, 85.0]],
        profile={
            "rows": 2,
            "columns": ["spend", "signups"],
            "stats": {
                "spend": {"type": "numeric", "null_count": 0, "distinct_count": 2},
                "signups": {"type": "numeric", "null_count": 0, "distinct_count": 2},
            },
            "quality": [],
        },
        context=None,
    )
    causality_check = [c for c in checks if c.dimension == validation.DIMENSION_CAUSALITY][0]
    assert causality_check.passed is True
    assert status == "supported"
