"""The measurement runner (P8-MEASURE-009): one number per acceptance test.

The PRD's measurement targets existed only as prose until this runner. It folds
the layer's five measurements into a single report, one line per acceptance
test, and exits non-zero when a measured threshold did not hold:

    AT-27  interaction response, p95 <= 200ms          (asserted in the web suite)
    AT-28  case loading, 95% within 2s                 (measured, real server)
    AT-29  profiling, 95% within 5s                    (measured, real server)
    AT-30  long-running operations show their state    (asserted in the web suite)
    AT-32  accessibility, 0 critical violations        (asserted in the web suite)
    AT-37  dependencies, 0 Critical / 0 High           (measured, OSV)
    AT-38  coverage, >= 80% core / >= 90% critical     (measured, the suite itself)
    AT-45  the dataset envelope, declared and enforced (measured)
    AT-46  the case envelope, stable at the boundary   (measured, real server)

Every number is measured against a real core or the real suite, never taken
from the engine being measured. The three browser-side targets (AT-27, AT-30,
AT-32) are asserted inside the web suite rather than measured here, and the
report says so rather than restating them as numbers this runner did not
compute: jsdom is not a browser, and a millisecond there is not a millisecond
in one. The web suite's green is the measurement - the thresholds are pinned
in the tests, so a regression fails a test rather than a report nobody reads.

AT-01, AT-04 and AT-40 have their own runners (verification/golden and
verification/refine) with their own reports; this one points at them rather
than re-running them.

    server/.venv/bin/python verification/measure/verify_measure.py

The report is written to verification/measure/REPORT.md either way, and the
exit code is 0 only when no measured threshold failed. A measurement that
could not run - the dependency scan with no network - is reported as not
completed with the reason, and the gate is red for it, because "could not
check" and "nothing to fix" are different statements and only one is true.
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SERVER = REPO / "server"
WEB = REPO / "web"
REPORT_PATH = REPO / "verification" / "measure" / "REPORT.md"
sys.path.insert(0, str(REPO))

from verification.measure import coverage as coverage_module
from verification.measure import deps as deps_module
from verification.measure import perf as perf_module

WEB_TIMEOUT_SECONDS = 420


@dataclass
class Measurement:
    """One acceptance test's measured number, or why there is not one."""

    at: str
    label: str
    value: str
    threshold: str
    ok: bool
    note: str = ""

    @property
    def verdict(self) -> str:
        return "PASS" if self.ok else "FAIL"


@dataclass
class Report:
    """The whole measurement run, and whether it gates."""

    measurements: list[Measurement] = field(default_factory=list)
    duration_seconds: float = 0.0
    notes: list[str] = field(default_factory=list)

    @property
    def failures(self) -> list[Measurement]:
        return [one for one in self.measurements if not one.ok]

    @property
    def ok(self) -> bool:
        return not self.failures

    def by_at(self, at: str) -> Measurement | None:
        for one in self.measurements:
            if one.at == at:
                return one
        return None


def measure_coverage_at(measurer=None) -> Measurement:
    """AT-38: line coverage of core, critical analytical and evidence paths."""
    if measurer is None:
        measurer = coverage_module.measure_coverage
    report = measurer()
    value = (
        f"core {report.core.percent:.1%} ({report.core.executed}/"
        f"{report.core.executable} lines), analytical {report.analytical.percent:.1%}, "
        f"evidence {report.evidence.percent:.1%}"
    )
    threshold = (
        f">= {coverage_module.CORE_THRESHOLD:.0%} core, "
        f">= {coverage_module.CRITICAL_THRESHOLD:.0%} analytical and evidence"
    )
    return Measurement(
        at="AT-38",
        label="line coverage (the suite run under a line counter)",
        value=value,
        threshold=threshold,
        ok=report.ok,
        note=report.failures_text() if not report.ok else "",
    )


def measure_deps_at(measurer=None) -> Measurement:
    """AT-37: production dependencies scanned, with nothing High or Critical."""
    if measurer is None:
        measurer = deps_module.measure_dependencies
    report = measurer()
    scanned = sum(1 for dep in report.dependencies if dep.scanned)
    value = (
        f"{len(report.critical)} critical, {len(report.high)} high "
        f"({scanned}/{len(report.dependencies)} packages scanned)"
    )
    measurement = Measurement(
        at="AT-37",
        label="dependency security (production inventory against OSV)",
        value=value,
        threshold="0 critical, 0 high without a documented risk acceptance",
        ok=report.ok,
    )
    if not report.ok:
        measurement.note = report.failures_text()
    return measurement


def measure_perf_at(measurer=None) -> list[Measurement]:
    """AT-28, AT-29 and AT-46: timing and the case envelope, over real HTTP."""
    if measurer is None:
        measurer = perf_module.run_perf
    report = measurer()
    made: list[Measurement] = []

    def timed(at: str, label: str, one: perf_module.Timed | None) -> None:
        made.append(
            Measurement(
                at=at,
                label=label,
                value="not measured" if one is None
                else f"p95 {one.p95_ms:.0f}ms over {one.samples} samples",
                threshold="not measured" if one is None
                else f"p95 <= {one.threshold_ms:.0f}ms",
                ok=bool(one and one.ok),
            )
        )

    timed(
        "AT-28",
        "case opening (the case, datasets, runs, findings, decision, history)",
        report.case_loading,
    )
    timed(
        "AT-29",
        f"profiling a {perf_module.BENCHMARK_ROWS:,}-row benchmark dataset",
        report.profiling,
    )
    boundary = report.boundary
    made.append(
        Measurement(
            at="AT-46",
            label="a case built at the envelope's boundary",
            value=(
                "not measured" if boundary is None
                else f"{boundary.runs} runs, {boundary.findings} findings, "
                f"{boundary.edges} evidence edges, "
                f"{sum(1 for read in boundary.reads if read.ok)}/"
                f"{len(boundary.reads)} surfaces answered in budget"
            ),
            threshold=(
                "not measured" if boundary is None
                else f"the envelope "
                f"({perf_module.BOUNDARY_RUNS}/{perf_module.BOUNDARY_FINDINGS}/"
                f"{perf_module.BOUNDARY_EDGES}) holds and every surface answers"
            ),
            ok=bool(boundary and boundary.ok),
            note="" if boundary is None or boundary.ok
            else boundary.failures()[0] if boundary.failures() else "",
        )
    )
    return made


def measure_envelope_at() -> list[Measurement]:
    """AT-45: the envelope is declared with the PRD's numbers and enforced."""
    declaration_failures = perf_module.measure_envelope_declaration()
    declared = Measurement(
        at="AT-45",
        label="the envelope the core declares (GET /envelope)",
        value=(
            "the PRD's numbers: "
            f"{perf_module.limits_module.DEFAULT_MAX_ROWS:,} rows and "
            f"{perf_module.limits_module.DEFAULT_MAX_COLUMNS} columns for "
            "CSV/Parquet, "
            f"{perf_module.limits_module.DEFAULT_MAX_EXCEL_ROWS:,} for Excel"
        ),
        threshold="declared explicitly rather than claiming unlimited scale",
        ok=not declaration_failures,
        note="; ".join(declaration_failures) if declaration_failures else "",
    )
    refusal = perf_module.measure_envelope_refusal()
    enforced = Measurement(
        at="AT-45",
        label="a dataset beyond the envelope is refused, not hung",
        value=(
            f"too wide refused ({refusal.sentence_wide or 'NO'}), "
            f"too tall refused ({refusal.sentence_tall or 'NO'})"
        ),
        threshold="a 400 naming the limit it broke, before any profile runs",
        ok=refusal.ok,
        note="" if refusal.ok
        else "the refusal path let a dataset past the envelope through",
    )
    # A gate reports the stricter of the two halves: a declaration that is not
    # enforced is a claim, and an enforcement of numbers that are not the PRD's
    # is a different envelope than the one it publishes.
    both = Measurement(
        at="AT-45",
        label="the dataset envelope, declared and enforced",
        value=f"declared {'ok' if declared.ok else 'drifted'}, "
        f"enforced {'ok' if enforced.ok else 'not enforced'}",
        threshold="the PRD's numbers, refused beyond",
        ok=declared.ok and enforced.ok,
        note="\n".join(
            line for line in (declared.note, enforced.note) if line
        ),
    )
    return [both, declared, enforced]


def run_web_suite(cwd: Path = WEB, timeout: int = WEB_TIMEOUT_SECONDS) -> tuple[int, str]:
    """Run the web suite and answer its exit code with its summary line.

    The browser-side targets are asserted there, not measured here; the suite's
    own summary is the evidence, and its exit code is the verdict.
    """
    try:
        completed = subprocess.run(
            ["npm", "test"],
            cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
        )
    except (OSError, subprocess.SubprocessError) as err:
        return -1, f"the web suite could not run: {err}"
    # Vitest's own summary is the evidence: the "Tests" and "Test Files" lines
    # it prints last, which carry the counts the report quotes.
    summary_lines = [
        line for line in completed.stdout.splitlines()
        if line.strip().startswith(("Tests", "Test Files"))
    ]
    tail = "\n".join(summary_lines) or "\n".join(
        completed.stdout.strip().splitlines()[-6:]
    )
    if completed.returncode != 0:
        tail = tail + "\n" + "\n".join(
            completed.stderr.strip().splitlines()[-12:]
        )
    return completed.returncode, tail


def measure_web_at(runner=None) -> Measurement:
    """AT-27, AT-30 and AT-32: the shell's own targets, asserted in its suite.

    These are browser targets - a 200ms interaction p95 on benchmark hardware
    - and this runner has no browser. What it can verify is that the suite that
    pins them is green, so the thresholds are enforced by a test rather than by
    prose, and the report says where the number lives instead of inventing one.
    """
    if runner is None:
        runner = run_web_suite
    code, summary = runner()
    first_line = summary.strip().splitlines()[-1] if summary.strip() else ""
    return Measurement(
        at="AT-27 / AT-30 / AT-32",
        label="the web shell's interaction, progress and accessibility targets",
        value=f"the web suite is {'green' if code == 0 else 'red'} ({first_line.strip()})",
        threshold=(
            "p95 <= 200ms, every long-running operation shows its state, "
            "0 critical accessibility violations"
        ),
        ok=code == 0,
        note="" if code == 0 else summary,
    )


def run_all(
    *,
    coverage_measure=None,
    deps_measure=None,
    perf_measure=None,
    web_runner=None,
    run_coverage: bool = True,
    run_deps: bool = True,
    run_perf: bool = True,
    run_web: bool = True,
) -> Report:
    """Fold the five measurements into one report.

    Each measurement is injected so a test can prove a failure fails the gate;
    each can also be skipped, so a partial run names what it did not measure
    rather than silently reporting a smaller report as complete.
    """
    started = time.perf_counter()
    report = Report()
    measurements: list[Measurement] = []

    if run_coverage:
        measurements.append(measure_coverage_at(coverage_measure))
    else:
        report.notes.append("coverage was not run for this pass")
    if run_deps:
        measurements.append(measure_deps_at(deps_measure))
    else:
        report.notes.append("the dependency scan was not run for this pass")
    if run_perf:
        measurements.extend(measure_perf_at(perf_measure))
    else:
        report.notes.append("the performance and envelope measurements were not run")
    measurements.extend(measure_envelope_at())
    if run_web:
        measurements.append(measure_web_at(web_runner))
    else:
        report.notes.append("the web suite was not run for this pass")

    report.measurements = measurements
    report.duration_seconds = time.perf_counter() - started
    return report


def summarize(report: Report) -> str:
    """The report body: one line per acceptance test, then the failures."""
    lines = [
        "# The measurement layer (P8-MEASURE-009)",
        "",
        "One measured number per acceptance test, each against a real core or the",
        "real suite - never the engine's own claim about itself. AT-01, AT-04 and",
        "AT-40 are measured by their own runners: verification/golden/REPORT.md",
        "and verification/refine/REPORT.md.",
        "",
    ]
    width = max(len(one.at) for one in report.measurements)
    for one in report.measurements:
        lines.append(f"## {one.at.ljust(width)}  {one.verdict}")
        lines.append("")
        lines.append(f"- measured: {one.value}")
        lines.append(f"- target: {one.threshold}")
        if one.note:
            for line in one.note.strip().splitlines():
                lines.append(f"- {line}")
        lines.append("")
    if report.notes:
        lines.append("## not run this pass")
        lines.append("")
        for note in report.notes:
            lines.append(f"- {note}")
        lines.append("")
    failures = report.failures
    if failures:
        lines.append("## Thresholds that did not hold")
        lines.append("")
        for one in failures:
            lines.append(f"- **{one.at} - {one.label}**: {one.value}")
        lines.append("")
    verdict = "PASS" if report.ok else "FAIL"
    lines.append("---")
    lines.append("")
    lines.append(f"**{verdict}** - {len(report.measurements) - len(failures)}/"
                 f"{len(report.measurements)} measurements hold; measured in "
                 f"{report.duration_seconds:.0f}s.")
    return "\n".join(lines)


def write_report_file(report: Report, path: Path = REPORT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summarize(report) + "\n")


def main() -> int:
    report = run_all()
    write_report_file(report)
    print(summarize(report))
    print(f"\nreport written to {REPORT_PATH}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
