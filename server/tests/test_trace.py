"""The traceability matrix's own contract (P8-TRACE-010, AT-48).

The PRD's section 59 asks for a matrix a release gate can read. A matrix typed
into a document drifts the moment a symbol is renamed, so these tests pin what
makes it a control artifact rather than a claim: every requirement the PRD
states is traced, every cell resolves against the repository as it stands, the
P0/P1 thresholds are computed rather than asserted, and each way a row can
break is caught - a missing file, a renamed symbol, a deleted test, a moved UX
section, a report that went red and a requirement the PRD added but nobody
traced.
"""

from __future__ import annotations

import re
from dataclasses import replace

import pytest

from verification.trace import matrix as matrix_module
from verification.trace import verify_trace as trace
from verification.trace.matrix import (
    Asserted, Case, Code, Gate, Measured, NoUX, Row, UX, Web,
)

PRD_TEXT = matrix_module.PRD_PATH.read_text()
UX_TEXT = matrix_module.UX_PATH.read_text()


@pytest.fixture(scope="module")
def real() -> trace.Report:
    """The matrix resolved against the repository as it actually stands."""
    return trace.run()


def _row(at: str) -> Row:
    return matrix_module.by_id(at)


def _resolver(rows, *, prd=PRD_TEXT, ux=UX_TEXT, sources=None):
    """A resolver over the real files the matrix names, unless overridden."""
    if sources is None:
        sources = {path: (matrix_module.REPO / path).read_text(errors="replace")
                   for path in trace._paths(rows)
                   if (matrix_module.REPO / path).is_file()}
    return trace.Resolver(sources, prd=prd, ux=ux)


# ---------------------------------------------------- the requirement set itself

def test_every_requirement_the_prd_states_is_traced(real) -> None:
    """The matrix's ids are exactly the PRD's: none untraced, none phantom."""
    assert real.requirements is not None
    assert real.requirements.ok, (
        f"untraced: {real.requirements.untraced}; "
        f"phantom: {real.requirements.phantom}")


def test_the_matrix_covers_forty_eight_acceptance_thresholds() -> None:
    assert len(matrix_module.MATRIX) == 48
    assert len(set(matrix_module.ids())) == 48


def test_the_prd_states_the_acceptance_thresholds_in_order() -> None:
    """The PRD's own ids are AT-01..AT-48, so a gap is a red gate."""
    assert trace.prd_at_ids(PRD_TEXT) == [f"AT-{n:02d}" for n in range(1, 49)]


def test_a_requirement_the_prd_adds_is_an_untraced_red_gate() -> None:
    """AT-49 in the PRD and no row for it: the gate must say so."""
    extra = PRD_TEXT + "\n## AT-49 — The Next One\n"
    got = trace.requirement_set(extra, matrix_module.MATRIX)
    assert got.untraced == ["AT-49"]
    assert not got.ok


def test_a_row_the_prd_does_not_state_is_a_phantom_red_gate() -> None:
    """A row tracing a requirement the PRD no longer states is a phantom."""
    rows = (*matrix_module.MATRIX,
            replace(_row("AT-01"), at="AT-99"))
    got = trace.requirement_set(PRD_TEXT, rows)
    assert got.phantom == ["AT-99"]
    assert not got.ok


def test_no_requirement_is_traced_twice() -> None:
    seen = set()
    for row in matrix_module.MATRIX:
        assert row.at not in seen, f"{row.at} has two rows"
        seen.add(row.at)


# ------------------------------------------------------------- the cells resolve

def test_every_rows_prd_header_is_quoted_exactly(real) -> None:
    """The header the row quotes is the PRD's own line, so drift is caught."""
    for one in real.rows:
        assert one.ok, f"{one.row.at}: {one.failures}"


def test_every_implementation_symbol_is_defined(real) -> None:
    """A renamed function or a moved module fails the gate and is named."""
    broken = [one for one in real.rows
              if any(f.cell == "Implementation" for f in one.failures)]
    assert broken == []


def test_every_named_test_exists(real) -> None:
    """A deleted or renamed test fails the gate rather than reading as traced."""
    broken = [one for one in real.rows
              if any(f.cell == "Test" for f in one.failures)]
    assert broken == []


def test_every_cited_report_is_committed_and_green(real) -> None:
    """A measurement the matrix cites is a real report, and it is not red."""
    broken = [one for one in real.rows
              if any(f.cell == "Evidence" for f in one.failures)]
    assert broken == []


def test_every_row_states_a_threshold() -> None:
    """A threshold is the requirement's own claim - an empty one is a label."""
    for row in matrix_module.MATRIX:
        assert row.threshold.strip(), f"{row.at} states no threshold"


def test_every_row_names_its_implementation_and_its_tests() -> None:
    """A row with no implementation or no test traces nothing."""
    for row in matrix_module.MATRIX:
        assert row.implementation, f"{row.at} names no implementation"
        assert row.tests, f"{row.at} names no test"
        assert row.evidence, f"{row.at} names no evidence"


# ----------------------------------------------------- the P0 / P1 classification

def test_the_release_blocking_rows_guard_the_prds_own_categories(real) -> None:
    """Every P0 row names a category the PRD's section 53 lists."""
    assert real.blocking is not None
    assert real.blocking.ok, f"unknown categories: {real.blocking.unknown}"


def test_the_classification_is_a_real_split() -> None:
    p0 = matrix_module.p0_rows()
    p1 = matrix_module.p1_rows()
    assert p0 and p1, "a classification with only one side is not a split"
    assert len(p0) + len(p1) == len(matrix_module.MATRIX)


def test_a_p0_row_guarding_an_invented_category_fails() -> None:
    invented = replace(_row("AT-02"), guards="Widget rot")
    got = trace.release_blocking(PRD_TEXT, (*matrix_module.MATRIX, invented))
    assert got.unknown == ["Widget rot"]
    assert not got.ok


def test_the_p0_threshold_is_one_hundred_percent(real) -> None:
    """AT-48: 100% of P0 requirements traceable. 99% is a red gate."""
    assert real.p0_count == len(matrix_module.p0_rows())
    assert real.p0_rate == pytest.approx(matrix_module.P0_TARGET)


def test_the_p1_threshold_is_at_least_ninety_five_percent(real) -> None:
    assert real.p1_rate >= matrix_module.P1_TARGET


def test_one_broken_p0_row_fails_the_p0_threshold(real) -> None:
    """A single untraced release-blocking requirement is a red gate."""
    untraced = replace(real.rows[0], row=replace(real.rows[0].row, p0=True),
                       failures=[trace.Failure("Test", "the test is gone")])
    report = trace.Report(rows=[untraced, *real.rows[1:]])
    assert report.p0_ok == report.p0_count - 1
    assert report.p0_rate < matrix_module.P0_TARGET
    assert not report.ok


# ------------------------------------------------------------ the ways a row breaks

def test_a_missing_implementation_file_is_caught() -> None:
    row = replace(_row("AT-02"),
                 implementation=(Code("server/app/nope.py", "create_case"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "does not exist" in str(result.failures[0])


def test_a_renamed_symbol_is_caught_and_named() -> None:
    row = replace(_row("AT-02"),
                 implementation=(Code("server/app/main.py", "create_a_case"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "does not define create_a_case" in str(result.failures[0])


def test_a_deleted_test_is_caught_and_named() -> None:
    row = replace(_row("AT-02"),
                 tests=(Case("server/tests/test_cases.py",
                             "test_create_and_reopen_a_case"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "has no test test_create_and_reopen_a_case" in str(result.failures[0])


def test_a_missing_test_file_is_caught() -> None:
    row = replace(_row("AT-02"),
                 tests=(Case("server/tests/test_nope.py", "test_x"),))
    assert not _resolver([row]).resolve(row).ok


def test_a_renumbered_ux_section_is_caught() -> None:
    row = replace(_row("AT-02"), ux=(UX(99, "Home / Case Dashboard"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "no section 99" in str(result.failures[0])


def test_a_renamed_ux_section_is_caught() -> None:
    """The section exists but its title moved: the citation no longer reads."""
    row = replace(_row("AT-02"), ux=(UX(10, "The Case Drawer"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "no longer" in str(result.failures[0])


def test_a_component_that_shipped_under_another_name_is_caught() -> None:
    row = replace(_row("AT-02"), ux=(Web("web/src/CaseList.tsx", "CaseShelf"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "does not define CaseShelf" in str(result.failures[0])


def test_a_component_that_no_longer_ships_is_caught() -> None:
    row = replace(_row("AT-02"), ux=(Web("web/src/Retired.tsx", "CaseList"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "is not a shipped surface" in str(result.failures[0])


def test_a_no_ux_cell_must_state_its_reason() -> None:
    row = replace(_row("AT-36"), ux=(NoUX(""),))
    assert not _resolver([row]).resolve(row).ok


def test_a_cited_report_that_is_not_committed_is_caught() -> None:
    row = replace(_row("AT-04"),
                 evidence=(Measured("verification/refine/verify_refine.py",
                                    "verification/refine/NOPE.md", "AT-04"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "is not committed" in str(result.failures[0])


def test_a_cited_runner_that_no_longer_exists_is_caught() -> None:
    row = replace(_row("AT-04"),
                 evidence=(Measured("verification/refine/nope.py",
                                    "verification/refine/REPORT.md", "AT-04"),))
    result = _resolver([row]).resolve(row)
    assert not result.ok
    assert "runner" in str(result.failures[0])


def test_a_report_that_went_red_is_caught() -> None:
    sources = {path: (matrix_module.REPO / path).read_text(errors="replace")
               for path in trace._paths([_row("AT-04")])
               if (matrix_module.REPO / path).is_file()}
    sources["verification/refine/REPORT.md"] = (
        "# AT-04\n\none threshold did not hold: FAIL\n")
    row = _row("AT-04")
    result = _resolver([row], sources=sources).resolve(row)
    assert not result.ok
    assert "failure marker" in str(result.failures[0])


def test_a_report_that_lost_its_marker_is_caught() -> None:
    sources = {path: (matrix_module.REPO / path).read_text(errors="replace")
               for path in trace._paths([_row("AT-04")])
               if (matrix_module.REPO / path).is_file()}
    sources["verification/refine/REPORT.md"] = "# AT-04\n\nnothing to see\n"
    row = _row("AT-04")
    result = _resolver([row], sources=sources).resolve(row)
    assert not result.ok
    assert "green marker" in str(result.failures[0])


def test_a_report_that_does_not_mention_the_requirement_is_caught() -> None:
    sources = {path: (matrix_module.REPO / path).read_text(errors="replace")
               for path in trace._paths([_row("AT-04")])
               if (matrix_module.REPO / path).is_file()}
    sources["verification/refine/REPORT.md"] = (
        "# something else entirely\n\nPASS\n")
    row = _row("AT-04")
    result = _resolver([row], sources=sources).resolve(row)
    assert not result.ok
    assert "does not mention AT-04" in str(result.failures[0])


def test_an_asserted_suite_that_does_not_exist_is_caught() -> None:
    row = replace(_row("AT-04"), evidence=(Asserted("server/tests/test_nope.py"),))
    assert not _resolver([row]).resolve(row).ok


def test_an_asserted_directory_still_counts() -> None:
    """Citing the suite as a directory resolves while it holds a test."""
    row = replace(_row("AT-02"), evidence=(Asserted("server/tests"),))
    assert _resolver([row]).resolve(row).ok


# ------------------------------------------------------------- the gate and report

def test_the_whole_matrix_gates_green(real) -> None:
    assert real.ok, "\n".join(
        f"{one.row.at}: {one.failures}" for one in real.failures)


def test_one_broken_row_fails_the_gate_and_names_the_requirement() -> None:
    broken = replace(_row("AT-02"),
                     implementation=(Code("server/app/main.py", "create_a_case"),))
    report = trace.run(_resolver([broken, *matrix_module.MATRIX[1:]]),
                       rows=(broken, *matrix_module.MATRIX[1:]))
    assert not report.ok
    assert report.failures[0].row.at == "AT-02"


def test_the_report_names_every_requirement_and_its_verdict(real) -> None:
    text = trace.summarize(real)
    for row in matrix_module.MATRIX:
        assert f"**{row.at}**" in text
    assert "**PASS**" in text


def test_the_report_states_the_two_at48_thresholds(real) -> None:
    text = trace.summarize(real)
    assert "release-blocking (P0)" in text
    assert "target 100%" in text
    assert "target >= 95%" in text


def test_the_report_is_written_and_readable(tmp_path) -> None:
    out = tmp_path / "REPORT.md"
    trace.write_report_file(trace.run(), path=out)
    body = out.read_text()
    assert body.startswith("# Requirement Traceability Matrix")
    assert re.search(r"\| \*\*AT-48\*\*", body)


def test_the_prds_section_53_block_is_found() -> None:
    block = trace._section_53(PRD_TEXT)
    for category in matrix_module.RELEASE_BLOCKING:
        assert category in block


def test_at48s_own_row_traces_to_this_matrix_and_its_tests() -> None:
    """The requirement that demands the matrix is itself traced by it."""
    row = _row("AT-48")
    assert row.implementation[0].path == "verification/trace/matrix.py"
    assert any(isinstance(item, Measured) is False and
               isinstance(item, Asserted) and
               item.where == "server/tests/test_trace.py"
               for item in row.evidence)


def test_the_matrix_module_and_the_runner_agree_on_the_paths() -> None:
    """Every path the runner loads comes from the matrix, never the reverse."""
    paths = trace._paths(matrix_module.MATRIX)
    assert "server/app/main.py" in paths
    assert "docs/Product Requirements Specification (PRD).md" not in paths
