"""The analytical golden suite, asserted (P8-GOLDEN-005).

verify_golden.py measures two numbers the PRD asks for and nothing previously
computed - AT-40's reference-calculation match rate and AT-01's workflow-
completion rate. A report nobody reads does not guard anything, so this module
asserts both in the suite, where a regression fails a test.

The tests come in two weights. The fixture's own audit - hand-computed
expectation against an independent recomputation from the CSV, and the
coverage of AT-40's ten shapes - is pure data and runs in milliseconds. The
two measurements themselves need the real server the runner starts, and that
is the ~minute the loop costs; it is the only slow test here, and it is the
one that makes the numbers real.

One property worth stating because it is not obvious: a completion rate above
zero is itself proof the run was offline. The runner fails the `plan` stage
unless the planner answers `source: "deterministic"`, so a journey that
reached an LLM would score 0, not 95%.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

# The golden modules live at the repo root, one level above the server package
# this suite runs from - the same path the standalone runner inserts.
REPO = Path(__file__).resolve().parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from verification.golden.reference import (
    AT40_SHAPES,
    CHECKS,
    GoldenCheck,
    check_by_id,
    shapes_covered,
)
from verification.golden.verify_golden import (
    COMPLETION_THRESHOLD,
    MIN_DATASETS,
    MIN_WORKFLOW_RUNS,
    REFERENCE_THRESHOLD,
    rows_match,
    run_golden,
    verify_expectations,
)


def test_all_ten_at40_shapes_are_covered() -> None:
    """Every shape AT-40 names has at least one reference calculation."""
    covered = shapes_covered()
    uncovered = [shape for shape in AT40_SHAPES if covered[shape] == 0]
    assert not uncovered, f"no golden check exercises: {', '.join(uncovered)}"


def test_the_suite_meets_its_own_size_floor() -> None:
    """AT-01 measures a rate over >= 20 runs and >= 3 datasets."""
    datasets = {check.dataset for check in CHECKS}
    assert len(CHECKS) >= MIN_WORKFLOW_RUNS, (
        "the workflow measurement needs >= 20 scripted runs"
    )
    assert len(datasets) >= MIN_DATASETS, (
        "the workflow measurement needs >= 3 datasets"
    )


def test_every_expectation_is_independently_recomputed() -> None:
    """Hand-computed against a second implementation, before the engine runs.

    This is what keeps a golden value from being the engine agreeing with
    itself: neither path here is DuckDB.
    """
    verify_expectations()


def test_the_audit_catches_a_wrong_fixture() -> None:
    """A deliberately wrong expectation fails the audit, proving it can fail.

    A check that cannot fail measures nothing, so the wrong value is real: the
    tickets' average resolution time is 19.83h, and this claims 25.0h.
    """
    right = check_by_id("tickets-validation-average")
    wrong = GoldenCheck(
        check_id="tickets-validation-average-wrong",
        dataset=right.dataset,
        shape=right.shape,
        question=right.question,
        sql=right.sql,
        columns=right.columns,
        expected=[[10, 25.0]],
        tolerance=right.tolerance,
        recompute_key=right.recompute_key,
    )
    with pytest.raises(RuntimeError, match="the fixture is wrong"):
        verify_expectations((wrong,))


def test_a_numeric_mismatch_is_a_mismatch_within_tolerance() -> None:
    """The comparator's tolerance is a tolerance, not a rubber stamp."""
    assert rows_match([[19.83]], [[19.83]], 1e-9)
    assert not rows_match([[19.83]], [[25.0]], 1e-9)
    # A label or a row count compares exactly - order included, because every
    # reference query carries an ORDER BY.
    assert not rows_match([["high", 30.0]], [["high", 30.0], ["low", 50.0]], 0.0)
    assert not rows_match([["high"]], [["low"]], 0.0)


@pytest.mark.slow
def test_the_two_numbers_hold_over_a_real_server() -> None:
    """AT-40 and AT-01, measured against a real server over HTTP.

    Every scripted run walks the whole loop and the query it makes is the
    reference query, so this one call answers both numbers. The report is not
    rewritten here - the standalone runner owns that artefact.
    """
    report = run_golden(write_report=False)

    assert report.reference_rate >= REFERENCE_THRESHOLD, (
        f"AT-40: {report.reference_passed}/{report.reference_total} reference "
        f"calculations matched; every one must"
    )
    assert report.completion_rate >= COMPLETION_THRESHOLD, (
        f"AT-01: {report.workflow_completed}/{report.workflow_total} scripted "
        f"runs completed the full loop"
    )
    assert report.workflow_total >= MIN_WORKFLOW_RUNS
    assert report.datasets >= MIN_DATASETS

    # A failure the rate can hide is still a failure: if any single journey
    # broke, the report names the stage, and the suite hears it.
    broken = [r for r in report.results if not r.workflow_ok]
    assert not broken, (
        "a scripted run broke at "
        f"{broken[0].failed_stage}: {broken[0].detail[:200]}"
    )
    mismatched = [r for r in report.results if not r.reference_ok]
    assert not mismatched, (
        f"{mismatched[0].check_id} did not match its golden value: "
        f"{mismatched[0].detail[:200]}"
    )
