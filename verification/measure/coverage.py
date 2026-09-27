"""Zero-dependency line-coverage measurement (AT-38).

The PRD asks for >= 80% line coverage of core domain logic and >= 90% of
critical analytical, validation and evidence paths - and nothing in the
project computed a number. `coverage.py` or `pytest-cov` would be the
conventional tools, but the phase carries a no-new-dependency constraint
(DEC-001), so the measurement is built on what the interpreter itself gives:
`sys.monitoring` (3.12+) registers a callback for line events, and the test
suite is the driver - its calls are what coverage means, and no fixture is
asked to represent "the suite".

Two details make it fast enough to run at all. Line events are enabled
*locally*, per code object, only for `app/`: globally enabled line events fire
for every line of pytest, anyio and the stdlib, and the per-line callback cost
then dominates the run. Enabling locally means non-application code pays
nothing, and application code pays one callback per executed line - the
irreducible cost of counting it. The code objects to enable are discovered by
importing every `app` module and walking `co_consts` recursively, so nested
functions, comprehensions and lambdas defined inside a function are included
rather than only its first line.

Executable lines are derived by re-compiling each module's source and walking
the same code-object tree, so the denominator is what the interpreter would
run, not a line count that includes comments and blanks. The measurement is
therefore a ratio over the same notion of "line" on both sides.

One module is excluded and the report says why: `app.python_worker` is
executed as a separate process by the sandbox (`python_exec.run_python`), so
an in-process line counter cannot observe it by construction - its lines run
in a child the measurement does not instrument. Its absence is a limit of the
method, not a claim that it is untested; the sandbox suite exercises it in
that other process.

    server/.venv/bin/python -m verification.measure.coverage

prints the per-module report; `verify_measure.py` folds it into the AT-38
measurement and asserts the thresholds.
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
SERVER = REPO / "server"
APP_DIR = SERVER / "app"

# The PRD's targets (AT-38).
CORE_THRESHOLD = 0.80
CRITICAL_THRESHOLD = 0.90

# Critical analytical and validation logic: the engines that produce, check or
# refuse a claim. >= 90% is required of these.
CRITICAL_ANALYTICAL = (
    "analysis.py",
    "assistant.py",
    "agent.py",
    "causality.py",
    "decision.py",
    "drafter.py",
    "eda.py",
    "evaluator.py",
    "generator.py",
    "interpreter.py",
    "learn.py",
    "memory.py",
    "planner.py",
    "quality.py",
    "refine.py",
    "supervisor.py",
    "validation.py",
    "workflow.py",
)

# Critical evidence and reproducibility paths: what makes a finding traceable
# to its source and a case portable. >= 90% is required of these too.
CRITICAL_EVIDENCE = (
    "charts.py",
    "evidence.py",
    "exporter.py",
    "history.py",
    "python_exec.py",
)

# Runs only as a separate process under the sandbox (see module docstring); an
# in-process measurement cannot observe it, and pretending otherwise would
# understate real coverage by counting lines that never run in this process.
EXCLUDED_MODULES = ("python_worker.py",)


@dataclass
class FileCoverage:
    """One module's measured coverage."""

    name: str
    executed: int
    executable: int

    @property
    def percent(self) -> float:
        return self.executed / self.executable if self.executable else 1.0


@dataclass
class GroupCoverage:
    """A named group of modules measured against one AT-38 threshold."""

    label: str
    threshold: float
    files: list[FileCoverage] = field(default_factory=list)

    @property
    def executed(self) -> int:
        return sum(one.executed for one in self.files)

    @property
    def executable(self) -> int:
        return sum(one.executable for one in self.files)

    @property
    def percent(self) -> float:
        return self.executed / self.executable if self.executable else 1.0

    @property
    def ok(self) -> bool:
        # A group with no executable lines is vacuously clean; a real group
        # that measured nothing is a measurement failure, not a pass.
        return self.executable > 0 and self.percent >= self.threshold


@dataclass
class CoverageReport:
    """The AT-38 measurement: three ratios, one per PRD target."""

    core: GroupCoverage
    analytical: GroupCoverage
    evidence: GroupCoverage
    excluded: list[str] = field(default_factory=list)
    duration_seconds: float = 0.0
    failures: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return (
            self.core.ok
            and self.analytical.ok
            and self.evidence.ok
            and not self.failures
        )

    @property
    def threshold_failures(self) -> list[str]:
        """Only the group thresholds - the notes are advisory, not a gate.

        A single module below three quarters is worth naming in the report,
        but it does not fail the PRD's group-level targets on its own; the
        targets are ratios over a group, and that is what they gate.
        """
        lines = list(self.failures)
        for group in (self.core, self.analytical, self.evidence):
            if group.executable == 0:
                lines.append(f"{group.label}: measured nothing")
            elif group.percent < group.threshold:
                lines.append(
                    f"{group.label}: {group.percent:.1%} below the "
                    f"{group.threshold:.0%} target"
                )
        return lines

    def failures_text(self) -> str:
        return "\n".join(self.threshold_failures)


def app_source_files() -> list[Path]:
    """Every measured module under app/, excluding the subprocess entrypoint."""
    return sorted(
        path
        for path in APP_DIR.glob("*.py")
        if path.name != "__init__.py" and path.name not in EXCLUDED_MODULES
    )


def _signature_lines(source: str) -> set[int]:
    """The continuation lines of a function signature, which never fire.

    A `def` spread across lines puts its parameters on lines of their own, and
    the compiler attributes those lines to the function's own code object - so
    a re-compile counts them as executable. The interpreter does not: a
    signature's prologue does not report a line event, so a line that can only
    ever be a parameter line is unreachable by measurement even when the
    function is called. Counting it makes the denominator larger than what the
    interpreter would ever report, and coverage then reads lower than it is.

    Class bases, call arguments, collection literals and multi-line conditions
    are *not* like this - their continuation lines do fire, measured - so only
    function signatures are excluded, and only the lines between the `def` and
    its first statement. A decorator is on its own line before the `def` and
    does fire, so it stays.
    """
    import ast

    excluded: set[int] = set()
    tree = ast.parse(source)
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        if not node.body:
            continue
        body_starts = min(child.lineno for child in node.body)
        for line in range(node.lineno + 1, body_starts):
            excluded.add(line)
    return excluded


def executable_lines(source: str) -> set[int]:
    """The lines the interpreter would actually report, from a re-compile.

    Walking `co_consts` finds nested code objects - comprehensions, lambdas and
    nested functions - whose lines belong to the module too. Blank lines,
    comments and docstrings carry no line numbers here, so the denominator is
    executable lines rather than file lines. Function-signature continuation
    lines are removed: the compiler attributes them to the function's code
    object but the interpreter never reports them, so counting them would make
    the denominator bigger than anything the numerator could reach.
    """
    code = compile(source, "<measured>", "exec")
    found: set[int] = set()

    def walk(node) -> None:
        for _start, _end, line in node.co_lines():
            # 0 is what a synthetic code object reports (a comprehension's
            # implicit wrapper among them), and it is not a line in the file.
            if line:
                found.add(line)
        for const in node.co_consts:
            if hasattr(const, "co_lines"):
                walk(const)

    walk(code)
    return found - _signature_lines(source)


# The code objects the import window discovered: populated by
# _collect_code_objects while line events run globally, then enabled locally
# for the suite's run.
_collected: list[object] = []


def _collect_code_objects() -> list[object]:
    """Import every app module and gather its code objects, nested ones too."""
    import types

    import app  # noqa: F401  -- imported to walk its package

    found: list[object] = []

    def keep(code) -> None:
        found.append(code)
        for const in code.co_consts:
            if hasattr(const, "co_lines"):
                keep(const)

    def record(value) -> None:
        if isinstance(value, types.FunctionType):
            keep(value.__code__)
        elif isinstance(value, (staticmethod, classmethod)):
            inner = value.__func__
            if isinstance(inner, types.FunctionType):
                keep(inner.__code__)
        elif isinstance(value, property):
            for f in (value.fget, value.fset, value.fdel):
                if isinstance(f, types.FunctionType):
                    keep(f.__code__)
        elif isinstance(value, type):
            for attr in vars(value).values():
                record(attr)

    for module_info in pkgutil.iter_modules(app.__path__, "app."):
        if module_info.name.split(".")[-1] + ".py" in EXCLUDED_MODULES:
            continue
        try:
            module = importlib.import_module(module_info.name)
        except ImportError as error:  # pragma: no cover - defensive
            print(f"[coverage] could not import {module_info.name}: {error}")
            continue
        for value in vars(module).values():
            record(value)
    _collected[:] = found
    return found


class LineCounter:
    """Counts executed lines in app/ only, with line events enabled locally.

    Process-wide rather than thread-local: the API serves requests through
    anyio's thread portal, so a `sys.settrace` hook would silently miss every
    endpoint body. Monitoring sees all threads.
    """

    def __init__(self) -> None:
        self.hits: dict[str, set[int]] = {}
        monitoring = sys.monitoring
        self._monitoring = monitoring
        self._tool = monitoring.COVERAGE_ID

    def _on_line(self, code, lineno: int) -> None:
        filename = code.co_filename
        if filename.startswith(str(APP_DIR)):
            self.hits.setdefault(filename, set()).add(lineno)

    def __enter__(self) -> "LineCounter":
        monitoring = self._monitoring
        monitoring.use_tool_id(self._tool, "dah-coverage")
        monitoring.register_callback(self._tool, monitoring.events.LINE, self._on_line)

        # Module bodies run once, at their import, and the code object the
        # import system executes is not the one a re-compile of the source
        # yields - local events key on the object, not the path - so enabling
        # them in advance cannot work. Instead, line events run *globally* for
        # exactly the import window: the app modules' bodies then register, and
        # everything they pull in is filtered by filename in the callback. The
        # window is a few seconds once; leaving it on for the suite is what
        # costs, and that is what the per-object pass below replaces.
        monitoring.set_events(self._tool, monitoring.events.LINE)
        try:
            _collect_code_objects()
        finally:
            monitoring.set_events(self._tool, 0)

        # From here the suite runs with global events off and local events on
        # for the app code objects the import left behind, so pytest, anyio and
        # the stdlib pay nothing.
        for code in _collected:
            monitoring.set_local_events(self._tool, code, monitoring.events.LINE)
        return self

    def __exit__(self, *exc) -> None:
        monitoring = self._monitoring
        monitoring.set_events(self._tool, 0)
        monitoring.register_callback(self._tool, monitoring.events.LINE, None)
        monitoring.free_tool_id(self._tool)
        return False


def build_report(
    hits: dict[str, set[int]],
    duration_seconds: float,
    failures: list[str] | None = None,
) -> CoverageReport:
    """Assemble the three AT-38 groups from the counted lines."""
    failures = list(failures or [])

    def group(label: str, threshold: float, names: tuple[str, ...]) -> GroupCoverage:
        files = []
        for name in names:
            path = APP_DIR / name
            if not path.is_file():
                failures.append(f"{name}: module not found")
                continue
            executable = executable_lines(path.read_text())
            executed = len(hits.get(str(path), set()) & executable)
            files.append(
                FileCoverage(
                    name=name, executed=executed, executable=len(executable)
                )
            )
        return GroupCoverage(label=label, threshold=threshold, files=files)

    measured = [path.name for path in app_source_files()]
    core = group("core domain logic (>= 80%)", CORE_THRESHOLD, tuple(measured))
    analytical = group(
        "critical analytical / validation (>= 90%)", CRITICAL_THRESHOLD, CRITICAL_ANALYTICAL
    )
    evidence = group(
        "critical evidence / reproducibility (>= 90%)", CRITICAL_THRESHOLD, CRITICAL_EVIDENCE
    )
    return CoverageReport(
        core=core,
        analytical=analytical,
        evidence=evidence,
        excluded=list(EXCLUDED_MODULES),
        duration_seconds=duration_seconds,
        failures=failures,
    )


def measure_coverage(
    test_args: list[str] | None = None,
    report_progress=None,
) -> CoverageReport:
    """Run the suite under the counter and answer the AT-38 ratios.

    The suite is the driver: coverage of app/ is the share of its executable
    lines the tests reached, and the runner prints each module's number so a
    shortfall names the file rather than a percentage alone.
    """
    if test_args is None:
        test_args = ["-q", "-p", "no:cacheprovider", "--no-header", "-m", "not slow"]

    failures: list[str] = []
    started = time.perf_counter()
    # pytest must be imported before the counter enters: `LineCounter.__enter__`
    # imports every app module, and `app.main` calls `configure_logging()` at
    # import time. That call installs a file handler only when pytest is absent
    # from `sys.modules` (the suite repoints the data dir after import, so an
    # import-time handler would write into the repository), and the tests that
    # assert the suite installs no file handler would fail under the runner that
    # is here to measure them. Importing first is one line and it is the seam
    # the logging contract already keys on.
    import pytest

    with LineCounter() as counter:
        if report_progress:
            report_progress("running the suite under the line counter")
        exit_code = pytest.main(list(test_args))
    duration = time.perf_counter() - started
    if exit_code != 0:
        failures.append(f"the suite exited {exit_code}, so the counts are partial")

    report = build_report(counter.hits, duration, failures)
    _annotate(report)
    return report


def _annotate(report: CoverageReport) -> None:
    """Name any critical module far below its group's target, advisably.

    These are notes rather than failures: the PRD's targets are group ratios,
    and one module that needs live network to exercise should not be able to
    fail them alone. It should be visible in the report, which it now is.
    """
    for group in (report.analytical, report.evidence):
        for one in group.files:
            if one.executable and one.percent < 0.75:
                report.notes.append(
                    f"{one.name}: {one.percent:.1%} of its executable lines "
                    f"were not reached"
                )


def format_report(report: CoverageReport) -> str:
    """A plain-text table, one line per module, for the report and the log."""
    lines = [
        "AT-38 line coverage (measured by running the suite under a line counter)",
        "",
    ]

    def row(group: GroupCoverage) -> None:
        lines.append(f"## {group.label}")
        lines.append("")
        lines.append(
            f"{group.percent:6.1%}  {group.executed}/{group.executable} lines  "
            f"(target {group.threshold:.0%})  {'PASS' if group.ok else 'FAIL'}"
        )
        for one in sorted(group.files, key=lambda f: f.percent):
            lines.append(f"        {one.percent:6.1%}  {one.name}")
        lines.append("")

    row(report.analytical)
    row(report.evidence)
    row(report.core)
    if report.excluded:
        lines.append(
            "excluded: "
            + ", ".join(report.excluded)
            + " - a subprocess entrypoint an in-process counter cannot observe"
        )
    if report.notes:
        lines.append("")
        lines.append("advisories (named, not gating):")
        for note in report.notes:
            lines.append(f"  - {note}")
    gate = report.threshold_failures
    if gate:
        lines.append("")
        lines.append("threshold failures:")
        for failure in gate:
            lines.append(f"  - {failure}")
    lines.append(f"\nmeasured in {report.duration_seconds:.0f}s")
    return "\n".join(lines)


if __name__ == "__main__":
    print(format_report(measure_coverage()))
