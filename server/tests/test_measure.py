"""The measurement layer's own numbers, asserted in the suite (P8-MEASURE-009).

A report nobody reads is how a measured threshold quietly stops being measured,
so every number verify_measure.py prints is pinned here: the percentiles, the
envelope's counts, the dependency classifier's counts, the coverage groups'
ratios, and the fold that turns a failing measurement into a red gate. Each has
a deliberately-wrong expectation proving the measurement can fail, the
discipline the golden and refinement suites established.
"""

from __future__ import annotations

import urllib.error

import pytest

from verification.measure import coverage as coverage_module
from verification.measure import deps as deps_module
from verification.measure import perf as perf_module
from verification.measure import verify_measure


# ------------------------------------------------------------------ percentiles

@pytest.mark.parametrize(
    "samples, want",
    [
        ([10, 10, 10, 10, 10], 10.0),
        ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 9.55),
        ([100, 1, 2], 90.2),
        ([5], 5.0),
    ],
)
def test_p95_is_the_interpolated_95th_percentile(samples, want) -> None:
    """The same computation the web suite's AT-27 helper makes."""
    assert perf_module.p95(samples) == pytest.approx(want)


def test_p95_of_nothing_answers_zero_rather_than_dividing() -> None:
    assert perf_module.p95([]) == 0.0


def test_a_percentile_over_the_budget_is_a_failure() -> None:
    """The measurement can fail: a slow sample makes the timing not ok."""
    inside = perf_module.Timed("opening", 150.0, 2000.0, 20)
    outside = perf_module.Timed("opening", 2500.0, 2000.0, 20)
    assert inside.ok
    assert not outside.ok
    # A timing with no samples measured nothing, and measuring nothing is not
    # a pass.
    assert not perf_module.Timed("opening", 0.0, 2000.0, 0).ok


# --------------------------------------------------------------- the AT-46 case

def test_the_boundary_counts_are_the_prds_envelope() -> None:
    """The case the runner builds sits at the envelope the PRD names."""
    assert perf_module.BOUNDARY_RUNS == 100
    assert perf_module.BOUNDARY_FINDINGS == 200
    assert perf_module.BOUNDARY_EDGES == 1000
    # 100 runs crossing 10 datasets each is the thousand edges, so the shape
    # itself has to be the PRD's rather than a convenient near-miss.
    assert perf_module.BOUNDARY_RUNS * perf_module.BOUNDARY_DATASETS >= 1000


def test_a_boundary_case_below_the_envelope_is_a_failure() -> None:
    """Reaching nearly the envelope is not reaching it."""
    short = perf_module.BoundaryCase(runs=90, findings=200, edges=1200)
    assert not short.counts_ok
    assert "runs: 90 of the 100" in short.failures()[0]


def test_a_boundary_case_that_does_not_answer_is_a_failure() -> None:
    """Stability is the reads at the boundary, not the counts alone."""
    built = perf_module.BoundaryCase(runs=100, findings=200, edges=1200)
    assert built.ok
    hung = perf_module.BoundaryCase(
        runs=100, findings=200, edges=1200,
        reads=[perf_module.BoundaryRead("GET /cases/{id}", 500, 30.0)],
    )
    assert not hung.ok
    assert "GET /cases/{id}: status 500 in 30.00s" in hung.failures()[0]


def test_the_import_round_trip_answers_201_and_that_is_a_pass() -> None:
    """The envelope's portability read creates a case, so 201 is its success."""
    assert perf_module.BoundaryRead("POST /cases/import", 201, 0.1, expect=201).ok
    refused = perf_module.BoundaryRead("POST /cases/import", 400, 0.1, expect=201)
    assert not refused.ok
    # A refused round trip is named in the case's failures, with its status.
    hung = perf_module.BoundaryCase(
        runs=100, findings=200, edges=1200, reads=[refused]
    )
    assert not hung.ok
    assert any("POST /cases/import: status 400" in line for line in hung.failures())


# ---------------------------------------------------------------- AT-45's two halves

def test_the_envelope_the_core_declares_is_the_prds() -> None:
    """AT-45: the declaration is the specification's numbers, not near them."""
    assert perf_module.measure_envelope_declaration() == []


def test_an_envelope_that_drifts_from_the_prd_is_caught(monkeypatch) -> None:
    """The measurement can fail: a drifted limit is named, not tolerated."""
    monkeypatch.setattr(perf_module.limits_module, "MAX_FINDINGS", 199)
    failures = perf_module.measure_envelope_declaration()
    assert len(failures) == 1
    assert "max_findings" in failures[0]


def test_a_dataset_past_the_envelope_is_refused_with_a_sentence() -> None:
    """AT-45's enforcement half: the path the attach endpoint refuses on."""
    refusal = perf_module.measure_envelope_refusal()
    assert refusal.ok
    assert "columns" in refusal.sentence_wide
    assert "rows" in refusal.sentence_tall


def test_a_refusal_that_lets_a_dataset_through_is_caught(monkeypatch) -> None:
    """The measurement can fail: a check that stops refusing reports as not ok."""

    def permissive(path: str, fmt: str):
        return (0, 0)

    monkeypatch.setattr(perf_module.limits_module, "check_dataset_envelope", permissive)
    refusal = perf_module.measure_envelope_refusal()
    assert not refusal.ok
    assert refusal.sentence_wide == "" and refusal.sentence_tall == ""


# ------------------------------------------------------------------- AT-37 deps

def _advisory(vector: str) -> dict:
    return {"id": "GHSA-test", "severity": [{"type": "CVSS_V3", "score": vector}]}


def test_a_scanned_inventory_with_nothing_high_is_ok() -> None:
    report = deps_module.measure_dependencies(
        inventory={"safe": ("PyPI", "1.0")},
        querier=lambda name, version, ecosystem: [],
    )
    assert report.ok
    assert report.scan_status == "scanned"


def test_a_critical_advisory_is_counted_and_fails_the_gate() -> None:
    """The classifier reads the vector and counts what it rates."""
    report = deps_module.measure_dependencies(
        inventory={"danger": ("PyPI", "1.0")},
        querier=lambda name, version, ecosystem: [_advisory(_CVSS_CRITICAL)],
    )
    assert not report.ok
    assert len(report.critical) == 1
    assert "CRITICAL PyPI:danger@1.0" in report.failures_text()


def test_an_unreachable_database_is_unknown_never_clean() -> None:
    """`could not check` and `nothing to fix` are different statements."""

    def unreachable(name, version, ecosystem):
        raise urllib.error.URLError("network unavailable")

    report = deps_module.measure_dependencies(
        inventory={"offline": ("PyPI", "1.0")}, querier=unreachable
    )
    assert not report.ok
    assert report.scan_status == "unknown"
    assert "network unavailable" in report.scan_reason


_CVSS_CRITICAL = (
    "CVSS:3.1/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"  # 9.8, critical
)


# ------------------------------------------------------------------ AT-38 groups

def test_a_group_above_its_threshold_passes() -> None:
    """The ratios are computed from counted lines, and the group gates."""
    report = coverage_module.build_report(_fake_hits(), 1.0)
    assert report.analytical.ok
    assert report.evidence.ok
    assert report.core.ok


def test_a_group_below_its_threshold_is_named() -> None:
    """The measurement can fail: a shortfall names the group and its ratio."""
    hits = _fake_hits()
    # Empty every analytical module's hits and the group falls under 90%.
    for name in coverage_module.CRITICAL_ANALYTICAL:
        hits[str(coverage_module.APP_DIR / name)] = set()
    report = coverage_module.build_report(hits, 1.0)
    assert not report.analytical.ok
    analytical = [
        line for line in report.threshold_failures
        if "critical analytical / validation" in line
    ]
    assert analytical
    assert "below the 90% target" in analytical[0]


def test_a_group_measured_below_its_target_is_named() -> None:
    """Nothing counted at all is zero percent, and zero is below 80%."""
    report = coverage_module.build_report({}, 1.0)
    assert not report.core.ok
    assert "core domain logic" in report.threshold_failures[0]
    assert "below the 80% target" in report.threshold_failures[0]


def test_a_group_with_no_executable_lines_is_a_measurement_failure() -> None:
    """A vacuous group does not pass by accident of having nothing to cover."""
    empty = coverage_module.GroupCoverage(label="nothing", threshold=0.80, files=[])
    assert not empty.ok
    assert empty.percent == 1.0  # no lines, so the ratio is vacuously whole
    assert "nothing: measured nothing" in coverage_module.CoverageReport(
        core=empty, analytical=empty, evidence=empty
    ).threshold_failures


def _fake_hits() -> dict:
    """Every app module fully covered, so the groups are about the ratios.

    The core group is the whole package, so a green fold covers all of it; the
    analytical and evidence groups are subsets of the same files.
    """
    return {
        str(path): set(coverage_module.executable_lines(path.read_text()))
        for path in coverage_module.app_source_files()
    }


# -------------------------------------------------------------- the fold into a gate

def test_a_green_run_passes_the_gate() -> None:
    report = verify_measure.run_all(
        coverage_measure=lambda: coverage_module.build_report(_fake_hits(), 1.0),
        deps_measure=lambda: _clean_deps(),
        perf_measure=_green_perf,
        web_runner=lambda: (0, "138 passed"),
    )
    assert report.ok
    assert not report.failures


def test_one_failing_measurement_fails_the_gate_and_is_named() -> None:
    """The measurement can fail: a red measurement makes the report red."""
    slow = _green_perf()
    slow.case_loading.p95_ms = slow.case_loading.threshold_ms * 3
    report = verify_measure.run_all(
        coverage_measure=lambda: coverage_module.build_report(_fake_hits(), 1.0),
        deps_measure=lambda: _clean_deps(),
        perf_measure=lambda: slow,
        web_runner=lambda: (0, "138 passed"),
    )
    assert not report.ok
    failure = report.by_at("AT-28")
    assert failure is not None and not failure.ok
    assert "p95 6000ms" in failure.value
    assert "## AT-28" in verify_measure.summarize(report)


def test_a_dependency_scan_that_did_not_complete_fails_the_gate() -> None:
    """An offline scan is red with its reason, never a silent green."""
    unscanned = deps_module.DepsReport()
    unscanned.scan_status = "unknown"
    unscanned.scan_reason = "network unavailable"
    report = verify_measure.run_all(
        coverage_measure=lambda: coverage_module.build_report(_fake_hits(), 1.0),
        deps_measure=lambda: unscanned,
        perf_measure=_green_perf,
        web_runner=lambda: (0, "138 passed"),
    )
    assert not report.ok
    assert "network unavailable" in report.by_at("AT-37").note


def test_a_red_web_suite_fails_the_shell_targets() -> None:
    report = verify_measure.run_all(
        coverage_measure=lambda: coverage_module.build_report(_fake_hits(), 1.0),
        deps_measure=lambda: _clean_deps(),
        perf_measure=_green_perf,
        web_runner=lambda: (1, "2 failed"),
    )
    target = report.by_at("AT-27 / AT-30 / AT-32")
    assert target is not None and not target.ok
    assert "the web suite is red" in target.value


def test_a_skipped_measurement_is_named_not_silent() -> None:
    report = verify_measure.run_all(
        coverage_measure=lambda: coverage_module.build_report(_fake_hits(), 1.0),
        deps_measure=lambda: _clean_deps(),
        perf_measure=_green_perf,
        run_web=False,
    )
    assert "the web suite was not run for this pass" in report.notes
    assert report.by_at("AT-27 / AT-30 / AT-32") is None


def _clean_deps() -> deps_module.DepsReport:
    """A scan that ran over a non-empty inventory and found nothing."""
    return deps_module.measure_dependencies(
        inventory={"safe": ("PyPI", "1.0")},
        querier=lambda name, version, ecosystem: [],
    )


def _green_perf() -> perf_module.PerfReport:
    """A boundary case that held, measured well inside every budget."""
    boundary = perf_module.BoundaryCase(
        runs=perf_module.BOUNDARY_RUNS,
        findings=perf_module.BOUNDARY_FINDINGS,
        edges=perf_module.BOUNDARY_RUNS * perf_module.BOUNDARY_DATASETS,
        reads=[
            perf_module.BoundaryRead("GET /cases/{id}", 200, 0.01),
            perf_module.BoundaryRead("POST /cases/import", 201, 0.01, expect=201),
        ],
    )
    return perf_module.PerfReport(
        case_loading=perf_module.Timed("opening", 187.0, 2000.0, 20),
        profiling=perf_module.Timed("profiling", 900.0, 5000.0, 10),
        boundary=boundary,
    )
