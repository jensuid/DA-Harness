"""The traceability runner (P8-TRACE-010): AT-48, resolved, not asserted.

The PRD's section 59 asks for a matrix that carries each requirement from the
PRD through the UX surface, the implementation and the test to the threshold
that says it holds. A matrix someone types into a document drifts the moment
a symbol is renamed, so this runner resolves every cell against the repository
as it actually stands:

- the PRD cell      - the row's header line is quoted exactly and must appear
                      in the PRD, so the matrix cannot quietly disagree with
                      the requirement it traces;
- the UX cell       - a shipped component must exist and define the component
                      the row names, or the UX document must still carry the
                      section it cites, or the row must say it has no surface
                      and why;
- the implementation cell - the file must exist and the name must be defined
                      in it (an AST check for Python, a source check for the
                      shell);
- the test cell     - the test file must exist and, when a test is named, the
                      test must be defined in it;
- the evidence cell - a cited runner must exist, and the report it wrote must
                      be committed, mention the acceptance test and carry its
                      own green sentence - a report that went red, or one the
                      matrix cites but nobody committed, fails the gate.

It then checks the requirement set itself: the matrix's ids must be exactly
the PRD's ids, so a requirement the PRD adds is a red gate until a row exists
for it, and a row the PRD no longer states is a red gate too. AT-48's two
thresholds are computed from that: 100% of the release-blocking (P0)
requirements traceable, and >= 95% of the rest.

    server/.venv/bin/python verification/trace/verify_trace.py

The report is written to verification/trace/REPORT.md either way, and the exit
code is 0 only when every cell resolves and both thresholds hold.
"""

from __future__ import annotations

import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping, Sequence

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from verification.trace import matrix as matrix_module
from verification.trace.matrix import (
    Asserted, Case, Code, Gate, Measured, NoUX, Row, UX, Web,
)

REPO = matrix_module.REPO
PRD_PATH = matrix_module.PRD_PATH
UX_PATH = matrix_module.UX_PATH
REPORT_PATH = matrix_module.REPORT_PATH

# The PRD's section 53 header, which frames the release-blocking list the P0
# rows guard.
RELEASE_BLOCKING_HEADER = "# 53. Release Blocking Thresholds"


# ------------------------------------------------------------------ resolution

@dataclass
class Failure:
    """One cell of one row that does not resolve."""

    cell: str
    detail: str

    def __str__(self) -> str:
        return f"{self.cell}: {self.detail}"


@dataclass
class RowResult:
    """A row and every cell of it that did not resolve."""

    row: Row
    failures: list[Failure] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.failures

    @property
    def surfaces(self) -> str:
        """The UX cell, as the report renders it."""
        parts: list[str] = []
        for item in self.row.ux:
            if isinstance(item, Web):
                parts.append(f"{item.path}::{item.name}")
            elif isinstance(item, UX):
                parts.append(f"UX section {item.section}")
            else:
                parts.append(f"no surface ({item.reason.split(' - ')[0]})")
        return "; ".join(parts) or "-"


class Resolver:
    """Checks the matrix's cells against sources as they stand.

    Sources are a map of repository-relative path to text, so a test can
    resolve a deliberately broken row against a fake repository.
    """

    def __init__(self, sources: Mapping[str, str], *, prd: str,
                 ux: str) -> None:
        self.sources: dict[str, str] = dict(sources)
        self.prd = prd
        self.ux = ux
        self._names: dict[str, set[str]] = {}

    @classmethod
    def from_repo(cls, repo: Path = REPO) -> "Resolver":
        """Read the PRD, the UX document and every file the matrix names."""
        prd = (repo / PRD_PATH.relative_to(REPO)).read_text()
        ux = (repo / UX_PATH.relative_to(REPO)).read_text()
        wanted = _paths(matrix_module.MATRIX)
        wanted.add(RELEASE_BLOCKING_HEADER)  # a marker, not a path
        sources: dict[str, str] = {}
        for path in sorted(wanted):
            full = repo / path
            if full.is_file():
                sources[path] = full.read_text(errors="replace")
            elif full.is_dir():
                sources[path] = ""
        return cls(sources, prd=prd, ux=ux)

    # --------------------------------------------------------------- sources

    def _exists(self, path: str) -> bool:
        """A file the matrix names, or a directory with at least one file."""
        if path in self.sources:
            return True
        prefix = path.rstrip("/") + "/"
        return any(other.startswith(prefix) for other in self.sources)

    def _text(self, path: str) -> str | None:
        if path in self.sources:
            return self.sources[path]
        return None

    def _names_in(self, path: str) -> set[str]:
        """Module-level names defined in a Python file (AST, once per file)."""
        if path in self._names:
            return self._names[path]
        names: set[str] = set()
        text = self._text(path)
        if text is not None and path.endswith(".py"):
            try:
                tree = ast.parse(text)
            except SyntaxError:
                tree = None
            if tree is not None:
                for node in tree.body:
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef,
                                         ast.ClassDef)):
                        names.add(node.name)
                    elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                        targets = (node.targets if isinstance(node, ast.Assign)
                                   else [node.target])
                        names.update(t.id for t in targets
                                     if isinstance(t, ast.Name))
        self._names[path] = names
        return names

    def _defined(self, path: str, name: str) -> bool:
        """A name defined in a Python module, or present in a source file."""
        if not name:
            return True
        if path.endswith(".py"):
            return name in self._names_in(path)
        text = self._text(path)
        if text is None:
            return False
        return re.search(rf"(?<![\w$]){re.escape(name)}\b", text) is not None

    # ---------------------------------------------------------------- the row

    def resolve(self, row: Row) -> RowResult:
        result = RowResult(row)
        self._prd(row, result)
        self._ux(row, result)
        self._implementation(row, result)
        self._tests(row, result)
        self._evidence(row, result)
        return result

    def _prd(self, row: Row, result: RowResult) -> None:
        for line in self.prd.splitlines():
            if line.strip() == row.prd_header.strip():
                return
        result.failures.append(Failure(
            "PRD", f"the header the row quotes is not in the PRD "
                   f"({row.prd_header})"))

    def _ux(self, row: Row, result: RowResult) -> None:
        for item in row.ux:
            if isinstance(item, NoUX):
                if not item.reason.strip():
                    result.failures.append(Failure(
                        "UX", "the row claims no surface and gives no reason"))
                continue
            if isinstance(item, Web):
                if self._text(item.path) is None:
                    result.failures.append(Failure(
                        "UX", f"{item.path} is not a shipped surface"))
                elif not self._defined(item.path, item.name):
                    result.failures.append(Failure(
                        "UX", f"{item.path} does not define {item.name}"))
                continue
            if isinstance(item, UX):
                pattern = rf"^# {item.section}\. .*$"
                if not re.search(pattern, self.ux, re.M):
                    result.failures.append(Failure(
                        "UX", f"the UX document has no section {item.section}"))
                elif item.title.lower() not in _section(self.ux, item.section).lower():
                    result.failures.append(Failure(
                        "UX", f"UX section {item.section} is no longer "
                              f"'{item.title}'"))

    def _implementation(self, row: Row, result: RowResult) -> None:
        for item in row.implementation:
            if not self._exists(item.path):
                result.failures.append(Failure(
                    "Implementation", f"{item.path} does not exist"))
            elif not self._defined(item.path, item.name):
                result.failures.append(Failure(
                    "Implementation",
                    f"{item.path} does not define {item.name}"))

    def _tests(self, row: Row, result: RowResult) -> None:
        for item in row.tests:
            if not self._exists(item.path):
                result.failures.append(Failure(
                    "Test", f"{item.path} does not exist"))
            elif item.name and not self._defined(item.path, item.name):
                result.failures.append(Failure(
                    "Test", f"{item.path} has no test {item.name}"))

    def _evidence(self, row: Row, result: RowResult) -> None:
        for item in row.evidence:
            if isinstance(item, Asserted):
                if not self._exists(item.where):
                    result.failures.append(Failure(
                        "Evidence", f"{item.where} does not exist"))
                continue
            if isinstance(item, (Measured, Gate)):
                if not self._exists(item.runner):
                    result.failures.append(Failure(
                        "Evidence", f"the runner {item.runner} does not exist"))
                report = self._text(item.report)
                if report is None:
                    result.failures.append(Failure(
                        "Evidence", f"the report {item.report} the row cites "
                                    f"is not committed"))
                    continue
                if item.bad in report:
                    result.failures.append(Failure(
                        "Evidence", f"{item.report} carries a failure marker"))
                elif item.marker not in report:
                    result.failures.append(Failure(
                        "Evidence", f"{item.report} does not carry its green "
                                    f"marker ('{item.marker}')"))
                if isinstance(item, Measured) and item.at not in report:
                    result.failures.append(Failure(
                        "Evidence", f"{item.report} does not mention "
                                    f"{item.at}"))


def _section(ux_text: str, section: int) -> str:
    """The body of one numbered section of the UX document."""
    match = re.search(rf"^# {section}\. .*$", ux_text, re.M)
    if match is None:
        return ""
    head = match.start()
    body = ux_text[match.end():]
    nxt = re.search(r"^# \d+\. ", body, re.M)
    if nxt is None:
        return ux_text[head:]
    return ux_text[head: match.end() + nxt.start()]


def _paths(rows: Sequence[Row]) -> set[str]:
    """Every path the matrix cites, so one read loads the resolver."""
    found: set[str] = set()
    for row in rows:
        for items in (row.ux, row.implementation, row.tests, row.evidence):
            for item in items:
                if isinstance(item, (Web, Code)):
                    found.add(item.path)
                elif isinstance(item, Case):
                    found.add(item.path)
                elif isinstance(item, Measured):
                    found.update((item.runner, item.report))
                elif isinstance(item, Gate):
                    found.update((item.runner, item.report))
                elif isinstance(item, Asserted):
                    found.add(item.where)
    return found


# ------------------------------------------------------------- the requirement

AT_HEADER = re.compile(r"^#{1,6} (?:\d+\. )?AT-(\d+) — .+$", re.M)


def prd_at_ids(prd_text: str) -> list[str]:
    """Every acceptance threshold the PRD states, in the PRD's own order.

    AT-01 lives under the global-thresholds heading rather than in a numbered
    section of its own, so the level of the heading is not part of the match.
    """
    return [f"AT-{int(match.group(1)):02d}"
            for match in AT_HEADER.finditer(prd_text)]


@dataclass
class RequirementSet:
    """The matrix's ids against the PRD's ids, and what does not agree."""

    traced: list[str]
    untraced: list[str]
    phantom: list[str]

    @property
    def ok(self) -> bool:
        return not self.untraced and not self.phantom


def requirement_set(prd_text: str, rows: Sequence[Row]) -> RequirementSet:
    stated = prd_at_ids(prd_text)
    traced = [row.at for row in rows]
    untraced = [one for one in stated if one not in traced]
    phantom = [one for one in traced if one not in stated]
    return RequirementSet(traced=traced, untraced=untraced, phantom=phantom)


@dataclass
class ReleaseBlocking:
    """The PRD's section 53 categories, and any P0 row guarding one it does not name."""

    categories: tuple[str, ...]
    unknown: list[str]

    @property
    def ok(self) -> bool:
        return not self.unknown


def release_blocking(prd_text: str, rows: Sequence[Row]) -> ReleaseBlocking:
    block = _section_53(prd_text)
    unknown = [row.guards for row in rows if row.p0 and row.guards not in block]
    return ReleaseBlocking(categories=matrix_module.RELEASE_BLOCKING,
                           unknown=unknown)


def _section_53(prd_text: str) -> str:
    start = prd_text.find(RELEASE_BLOCKING_HEADER)
    if start < 0:
        return ""
    rest = prd_text[start:]
    nxt = re.search(r"^# \d+\. ", rest[1:], re.M)
    return rest if nxt is None else rest[: nxt.start() + 1]


# --------------------------------------------------------------------- the gate

@dataclass
class Report:
    """The whole matrix, resolved, and whether it gates."""

    rows: list[RowResult] = field(default_factory=list)
    requirements: RequirementSet | None = None
    blocking: ReleaseBlocking | None = None

    @property
    def failures(self) -> list[RowResult]:
        return [one for one in self.rows if not one.ok]

    @property
    def ok(self) -> bool:
        return (not self.failures and self.requirements is not None
                and self.requirements.ok and self.blocking is not None
                and self.blocking.ok and self._at48_ok)

    @property
    def _at48_ok(self) -> bool:
        return self.p0_rate >= matrix_module.P0_TARGET and \
            self.p1_rate >= matrix_module.P1_TARGET

    @property
    def p0_count(self) -> int:
        return sum(1 for one in self.rows if one.row.p0)

    @property
    def p0_ok(self) -> int:
        return sum(1 for one in self.rows if one.row.p0 and one.ok)

    @property
    def p0_rate(self) -> float:
        return self.p0_ok / self.p0_count if self.p0_count else 0.0

    @property
    def p1_count(self) -> int:
        return sum(1 for one in self.rows if not one.row.p0)

    @property
    def p1_ok(self) -> int:
        return sum(1 for one in self.rows if not one.row.p0 and one.ok)

    @property
    def p1_rate(self) -> float:
        return self.p1_ok / self.p1_count if self.p1_count else 0.0


def run(resolver: Resolver | None = None,
        rows: Sequence[Row] = matrix_module.MATRIX) -> Report:
    """Resolve every row of the matrix and fold the verdicts into one report."""
    if resolver is None:
        resolver = Resolver.from_repo()
    report = Report(rows=[resolver.resolve(row) for row in rows])
    report.requirements = requirement_set(resolver.prd, rows)
    report.blocking = release_blocking(resolver.prd, rows)
    return report


# -------------------------------------------------------------------- the text

def _cells(row: Row) -> list[str]:
    def impl(item: Code) -> str:
        return f"{item.path}::{item.name}" if item.name else item.path

    def test(item: Case) -> str:
        return f"{item.path}::{item.name}" if item.name else item.path

    def evidence(item) -> str:
        if isinstance(item, Measured):
            return f"measured: {item.report}"
        if isinstance(item, Gate):
            return f"gate: {item.report}"
        return f"asserted: {item.where}"

    return [
        " ".join(impl(i) for i in row.implementation),
        " ".join(test(i) for i in row.tests),
        " ".join(evidence(i) for i in row.evidence),
    ]


def summarize(report: Report) -> str:
    """The report body: the PRD's own control-artifact table, then the gaps."""
    lines = [
        "# Requirement Traceability Matrix (P8-TRACE-010)",
        "",
        "The PRD's own control artifact (its section 59): every requirement",
        "traces from the PRD, through the UX surface, the implementation and",
        "the test, to the threshold that says it holds. Every cell is resolved",
        "against the repository as it stands - a renamed symbol, a deleted",
        "test, a renumbered UX section, or a report that went red fails the",
        "gate rather than reading as a claim.",
        "",
        "| Requirement | UX | Implementation | Test | Verification | Threshold | Verdict |",
        "|---|---|---|---|---|---|---|",
    ]
    for one in report.rows:
        row = one.row
        impl_cell, test_cell, ev_cell = _cells(row)
        lines.append(
            f"| **{row.at}** {row.title} | {one.surfaces} "
            f"| {impl_cell} | {test_cell} | {ev_cell} "
            f"| {row.threshold} | {'PASS' if one.ok else 'FAIL'} |"
        )
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## AT-48 - the traceability thresholds")
    lines.append("")
    lines.append(
        f"- release-blocking (P0): {report.p0_ok}/{report.p0_count} traceable "
        f"({report.p0_rate:.0%}), target 100% - "
        f"{'PASS' if report.p0_rate >= matrix_module.P0_TARGET else 'FAIL'}")
    lines.append(
        f"- the rest (P1): {report.p1_ok}/{report.p1_count} traceable "
        f"({report.p1_rate:.0%}), target >= 95% - "
        f"{'PASS' if report.p1_rate >= matrix_module.P1_TARGET else 'FAIL'}")
    lines.append("")
    req = report.requirements
    if req is not None:
        lines.append(
            f"- the requirement set agrees with the PRD: {len(req.traced)} "
            f"requirements traced"
            + (f", {len(req.untraced)} the PRD states but no row traces"
               f" ({', '.join(req.untraced)})" if req.untraced else "")
            + (f", {len(req.phantom)} a row traces but the PRD does not state"
               f" ({', '.join(req.phantom)})" if req.phantom else "")
            + ".")
    blocking = report.blocking
    if blocking is not None and blocking.unknown:
        lines.append(
            f"- {len(blocking.unknown)} P0 row(s) guard a category the PRD's "
            f"section 53 does not name: {', '.join(blocking.unknown)}.")
    lines.append("")
    failures = report.failures
    if failures:
        lines.append("## Rows that do not trace")
        lines.append("")
        for one in failures:
            lines.append(f"- **{one.row.at} {one.row.title}**")
            for failure in one.failures:
                lines.append(f"  - {failure}")
        lines.append("")
    verdict = "PASS" if report.ok else "FAIL"
    lines.append("---")
    lines.append("")
    lines.append(f"**{verdict}** - {len(report.rows) - len(failures)}/"
                 f"{len(report.rows)} rows trace end to end.")
    return "\n".join(lines)


def write_report_file(report: Report, path: Path = REPORT_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(summarize(report) + "\n")


def main() -> int:
    report = run()
    write_report_file(report)
    print(summarize(report))
    print(f"\nreport written to {REPORT_PATH}")
    return 0 if report.ok else 1


if __name__ == "__main__":
    sys.exit(main())
