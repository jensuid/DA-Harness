"""The requirement-traceability matrix (AT-48).

The PRD's own control artifact (its section 59) is a table with a row per
requirement and a column for each layer the requirement passes through:

    Requirement -> UX -> Implementation -> Test -> Threshold -> Status

This module is that table, as data, so `verify_trace.py` can resolve every cell
against the repository as it actually stands. A renamed symbol, a deleted test,
a renumbered UX section or a report that went red fails the gate, which is what
makes the matrix an engineering control rather than a document someone keeps up
to date by hand.

Each row carries:

- `at` and `title`  - the PRD's own acceptance-threshold id and its title;
- `prd_header`      - the PRD's header line, quoted exactly, so a drift in the
                      PRD is caught rather than silently mirrored;
- `p0` and `guards` - whether the requirement is release-blocking, and, when it
                      is, which of the PRD's section-53 categories it guards;
- `ux`              - the surface the requirement shows through: a shipped
                      component, a section of the UX architecture document, or
                      an explicit "no surface, and here is why";
- `implementation`  - the code that delivers it: a file and a name defined in it;
- `tests`           - the tests that assert it, by file and test name;
- `threshold`       - the PRD's own threshold, in the PRD's own words;
- `evidence`        - where the measured number lives: a committed report a
                      runner wrote, a phase gate, or the suite itself.

The requirement set is complete by construction - `verify_trace.py` checks the
matrix's ids against the PRD's own headers, so a requirement the PRD adds is a
red gate until a row exists for it.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
PRD_PATH = REPO / "docs" / "Product Requirements Specification (PRD).md"
UX_PATH = REPO / "docs" / "UX- UI Architecture.md"
REPORT_PATH = REPO / "verification" / "trace" / "REPORT.md"

# The PRD's section 53: a defect in any of these blocks the release, so a
# requirement that guards one of them is a P0 row. The runner verifies each
# string appears in the PRD's own section 53 block.
RELEASE_BLOCKING = (
    "Data loss",
    "Fabricated evidence",
    "Fabricated execution",
    "Incorrect validated finding",
    "Broken evidence chain",
    "Critical security vulnerability",
    "Critical analytical calculation error",
    "Application cannot recover from normal critical failures",
)

# AT-48's own thresholds, quoted from the PRD's section 52.
P0_TARGET = 1.0
P1_TARGET = 0.95


# ------------------------------------------------------------- the cell values

@dataclass(frozen=True)
class Web:
    """A shipped UX surface: a file and the component defined in it."""

    path: str
    name: str


@dataclass(frozen=True)
class UX:
    """A section of the UX architecture document."""

    section: int
    title: str


@dataclass(frozen=True)
class NoUX:
    """A requirement with no UX surface, and the reason it has none."""

    reason: str


@dataclass(frozen=True)
class Code:
    """The implementation: a file, and a name defined in it."""

    path: str
    name: str = ""


@dataclass(frozen=True)
class Case:
    """A test: a file and the test defined in it (empty name: the file)."""

    path: str
    name: str = ""


@dataclass(frozen=True)
class Measured:
    """A runner measured this one and wrote a report; the report is cited.

    `at` must appear in the report, so the citation can be followed; `marker`
    is the report's own green sentence and `bad` the red one.
    """

    runner: str
    report: str
    at: str
    marker: str = "PASS"
    bad: str = "FAIL"


@dataclass(frozen=True)
class Gate:
    """A phase gate whose green report is the evidence for the row."""

    runner: str
    report: str
    marker: str = "PASS"
    bad: str = "FAIL"


@dataclass(frozen=True)
class Asserted:
    """Asserted by the test suite in the file (or directory) named."""

    where: str


# --------------------------------------------------------------------- the row

@dataclass(frozen=True)
class Row:
    """One requirement's path through the product, every layer named."""

    at: str
    title: str
    prd_header: str
    p0: bool
    guards: str
    ux: tuple
    implementation: tuple
    tests: tuple
    threshold: str
    evidence: tuple


def _r(at, title, header, p0, guards, ux, impl, tests, threshold, evidence):
    return Row(at, title, header, p0, guards, tuple(ux), tuple(impl),
               tuple(tests), threshold, tuple(evidence))


# The runners and reports the matrix cites, named once so a citation and its
# target cannot drift apart.
GOLDEN_RUNNER = "verification/golden/verify_golden.py"
GOLDEN_REPORT = "verification/golden/REPORT.md"
REFINE_RUNNER = "verification/refine/verify_refine.py"
REFINE_REPORT = "verification/refine/REPORT.md"
MEASURE_RUNNER = "verification/measure/verify_measure.py"
MEASURE_REPORT = "verification/measure/REPORT.md"
E2E_RUNNER = "verification/e2e/verify_e2e.py"
E2E_REPORT = "verification/e2e/REPORT.md"
P2_RUNNER = "verification/p2/verify_p2.py"
P2_REPORT = "verification/p2/REPORT.md"
P3_RUNNER = "verification/p3/verify_p3.py"
P3_REPORT = "verification/p3/REPORT.md"

# The golden report states its verdict in its own words.
GOLDEN_GREEN = "No failures."

# The shell's own tests, cited as evidence for the browser-side thresholds.
WEB_SUITE = "web/src/CaseWorkspace.test.tsx"
MEASURE_SUITE = "web/src/measure.test.tsx"
A11Y_SUITE = "web/src/accessibility.test.tsx"

NO_SURFACE_ENGINE = (
    "an engineering control, not a user surface - it is measured, not shown"
)
NO_SURFACE_TRUST = (
    "a trust guarantee enforced under the product, not rendered in it"
)


MATRIX = (
    _r(
        "AT-01", "Core Workflow Completion", "## AT-01 — Core Workflow Completion",
        False, "",
        (UX(48, "Modern UX Flow"), Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("server/app/workflow.py", "case_progress"),
         Code("server/app/agent.py", "next_step")),
        (Code("server/tests/test_agent.py",
              "test_the_full_loop_reaches_a_validated_finding"),),
        ">= 95% core workflow completion",
        (Measured(GOLDEN_RUNNER, GOLDEN_REPORT, "AT-01", GOLDEN_GREEN),
         Asserted("server/tests/test_agent.py")),
    ),
    _r(
        "AT-02", "Case Persistence", "# 6. AT-02 — Case Persistence",
        True, "Data loss",
        (UX(10, "Home / Case Dashboard"), Web("web/src/CaseList.tsx", "CaseList")),
        (Code("server/app/db.py", "get_connection"),
         Code("server/app/main.py", "create_case")),
        (Code("server/tests/test_cases.py", "test_create_and_reopen_case"),
         Code("server/tests/test_case_management.py",
              "test_delete_removes_case_and_its_data")),
        "0 data-loss defects in release-blocking tests",
        (Asserted("server/tests/test_cases.py"),
         Gate("verification/p1/verify_p1.py", "verification/p1/REPORT.md")),
    ),
    _r(
        "AT-03", "Question Capture", "# 7. AT-03 — Question Capture",
        False, "",
        (UX(11, "Create Analysis UX"), UX(13, "Context UX"),
         Web("web/src/CaseCreation.tsx", "CaseCreation"),
         Web("web/src/ContextPanel.tsx", "ContextPanel")),
        (Code("server/app/main.py", "create_case"),
         Code("server/app/main.py", "put_context")),
        (Code("server/tests/test_context.py", "test_context_persists_and_reopens"),
         Code("server/tests/test_context.py",
              "test_editing_replaces_wholesale_and_persists")),
        "100% of cases: entered text persists, edited text persists, "
        "reopening restores the latest version",
        (Asserted("server/tests/test_context.py"),),
    ),
    _r(
        "AT-04", "AI Question Refinement", "# 8. AT-04 — AI Question Refinement",
        False, "",
        (UX(12, "Question Refinement UX"),
         Web("web/src/RefinePanel.tsx", "RefinePanel")),
        (Code("server/app/refine.py", "refine_question"),
         Code("server/app/refine.py", "validate_refinement")),
        (Code("server/tests/test_refine.py",
              "test_at04s_four_thresholds_hold_over_a_real_server"),),
        "50 cases: >= 95% preserve the original, >= 90% relevant, "
        "0 silent overwrites, 0 fabricated data references",
        (Measured(REFINE_RUNNER, REFINE_REPORT, "AT-04", "PASS"),
         Asserted("server/tests/test_refine.py")),
    ),
    _r(
        "AT-05", "Data Import", "# 9. AT-05 — Data Import",
        False, "",
        (UX(14, "Data Workspace"), Web("web/src/CaseWorkspace.tsx", "DataPanel")),
        (Code("server/app/main.py", "attach_dataset"),
         Code("server/app/analysis.py", "_sniffed_reader_for")),
        (Code("server/tests/test_datasets.py", "test_attach_and_reopen_dataset"),
         Code("server/tests/test_datasets.py", "test_attach_rejects_non_csv"),
         Code("server/tests/test_analysis.py",
              "test_sniffed_reader_recovers_a_stray_trailing_comma")),
        ">= 99% successful import of valid files, 100% rejection of malformed "
        "files with a user-readable reason",
        (Asserted("server/tests/test_datasets.py"), Gate(P2_RUNNER, P2_REPORT)),
    ),
    _r(
        "AT-06", "Schema Detection", "# 10. AT-06 — Schema Detection",
        False, "",
        (UX(14, "Data Workspace"), Web("web/src/CaseWorkspace.tsx", "DataPanel")),
        (Code("server/app/analysis.py", "_type_family"),
         Code("server/app/analysis.py", "profile_csv")),
        (Code("server/tests/test_profiles.py", "test_deep_profile_stats"),
         Code("server/tests/test_analysis.py",
              "test_a_numeric_stays_a_numeric_and_a_null_stays_a_null")),
        ">= 99% column-name and row-count accuracy, >= 95% type-detection "
        "accuracy on the golden suite",
        (Asserted("server/tests/test_profiles.py"),),
    ),
    _r(
        "AT-07", "Data Profiling", "# 11. AT-07 — Data Profiling",
        True, "Critical analytical calculation error",
        (UX(14, "Data Workspace"), Web("web/src/CaseWorkspace.tsx", "DataPanel")),
        (Code("server/app/analysis.py", "profile_csv"),
         Code("server/app/main.py", "profile_dataset")),
        (Code("server/tests/test_golden.py",
              "test_every_expectation_is_independently_recomputed"),
         Code("server/tests/test_profiles.py", "test_profile_and_reopen")),
        "100% of expected profiling calculations match the reference values "
        "within the defined tolerance",
        (Measured(GOLDEN_RUNNER, GOLDEN_REPORT, "AT-40", GOLDEN_GREEN),
         Asserted("server/tests/test_profiles.py")),
    ),
    _r(
        "AT-08", "Data Quality Detection", "# 12. AT-08 — Data Quality Detection",
        False, "",
        (UX(15, "Data Quality UX"), Web("web/src/CaseWorkspace.tsx", "DataPanel")),
        (Code("server/app/quality.py", "assess_quality"),
         Code("server/app/quality.py", "ALL_CLASSES")),
        (Code("server/tests/test_quality.py",
              "test_every_prd_class_has_a_detector"),
         Code("server/tests/test_quality.py",
              "test_a_clean_dataset_raises_nothing")),
        ">= 95% detection rate and <= 5% false-positive rate on the injected-"
        "defect suite",
        (Asserted("server/tests/test_quality.py"),),
    ),
    _r(
        "AT-09", "Quality Impact", "# 13. AT-09 — Quality Impact",
        False, "",
        (UX(15, "Data Quality UX"), Web("web/src/CaseWorkspace.tsx", "DataPanel")),
        (Code("server/app/quality.py", "QualityIssue"),
         Code("server/app/validation.py", "_quality_issues")),
        (Code("server/tests/test_quality.py",
              "test_an_issue_carries_an_observation_and_an_impact"),
         Code("server/tests/test_quality.py",
              "test_validation_reads_the_impact_sentence")),
        ">= 90% of known material issues produce a visible analytical-impact "
        "warning",
        (Asserted("server/tests/test_quality.py"),),
    ),
    _r(
        "AT-10", "Analysis Planning", "# 14. AT-10 — Analysis Planning",
        False, "",
        (UX(17, "Analysis Workspace"), Web("web/src/CaseWorkspace.tsx", "PlanPanel")),
        (Code("server/app/planner.py", "plan_analysis"),
         Code("server/app/planner.py", "validate_plan")),
        (Code("server/tests/test_plans.py", "test_plan_references_real_columns"),
         Code("server/tests/test_plans.py",
              "test_validate_plan_rejects_malformed_shapes"),
         Code("server/tests/test_analysis.py",
              "test_plan_records_which_context_fields_it_read")),
        "20 scenarios: >= 95% carry every structural field, >= 90% name a "
        "relevant method and a relevant column",
        (Asserted("server/tests/test_plans.py"),),
    ),
    _r(
        "AT-11", "SQL Execution", "# 15. AT-11 — SQL Execution",
        True, "Critical analytical calculation error",
        (UX(25, "SQL / Python UX"), Web("web/src/CaseWorkspace.tsx", "RunsPanel")),
        (Code("server/app/analysis.py", "run_query"),
         Code("server/app/analysis.py", "_is_read_only")),
        (Code("server/tests/test_runs.py", "test_run_aggregation_and_reopen"),
         Code("server/tests/test_runs.py", "test_rejects_write_query"),
         Code("server/tests/test_golden.py",
              "test_a_numeric_mismatch_is_a_mismatch_within_tolerance")),
        "100% of reference queries produce the expected result within the "
        "defined tolerance",
        (Measured(GOLDEN_RUNNER, GOLDEN_REPORT, "AT-40", GOLDEN_GREEN),
         Asserted("server/tests/test_runs.py")),
    ),
    _r(
        "AT-12", "Python Execution", "# 16. AT-12 — Python Execution",
        False, "",
        (UX(25, "SQL / Python UX"), Web("web/src/CaseWorkspace.tsx", "RunsPanel")),
        (Code("server/app/python_exec.py", "run_python"),
         Code("server/app/python_exec.py", "execute_user_code")),
        (Code("server/tests/test_python_runs.py",
              "test_python_run_persists_and_reopens"),
         Code("server/tests/test_python_hard_sandbox.py",
              "test_runaway_loop_is_bounded_and_reported")),
        ">= 95% successful execution, 100% with execution metadata, 100% of "
        "invalid programs rejected",
        (Asserted("server/tests/test_python_runs.py"), Gate(P3_RUNNER, P3_REPORT)),
    ),
    _r(
        "AT-13", "Result Integrity", "# 17. AT-13 — Result Integrity",
        True, "Broken evidence chain",
        (UX(26, "Result Object UX"), Web("web/src/CaseWorkspace.tsx", "RunsPanel")),
        (Code("server/app/main.py", "create_run"),
         Code("server/app/main.py", "get_run")),
        (Code("server/tests/test_runs.py", "test_list_runs_excludes_rows"),
         Code("server/tests/test_evidence_graph.py",
              "test_orphan_finding_is_reported_not_hidden")),
        "100% of successful executions have a traceable Result object; no "
        "orphaned result in the golden integration tests",
        (Asserted("server/tests/test_runs.py"),),
    ),
    _r(
        "AT-14", "Visualization Integrity", "# 18. AT-14 — Visualization Integrity",
        False, "",
        (UX(34, "Charts"), Web("web/src/CaseWorkspace.tsx", "RunsPanel")),
        (Code("server/app/charts.py", "render_chart"),
         Code("server/app/charts.py", "ChartModel")),
        (Code("server/tests/test_charts.py",
              "test_bar_geometry_is_anchored_and_proportional"),
         Code("server/tests/test_charts.py", "test_chart_is_reproducible"),
         Code("server/tests/test_charts_raster.py",
              "test_png_bar_is_drawn_and_anchored_at_zero")),
        "100% of reference charts match the expected underlying values, not "
        "only the visual output",
        (Asserted("server/tests/test_charts.py"), Gate(P2_RUNNER, P2_REPORT)),
    ),
    _r(
        "AT-15", "Evidence Traceability", "# 19. AT-15 — Evidence Traceability",
        True, "Broken evidence chain",
        (UX(19, "Evidence UX"), Web("web/src/CaseWorkspace.tsx", "EvidencePanel")),
        (Code("server/app/evidence.py", "build_evidence_graph"),
         Code("server/app/main.py", "get_evidence_chain")),
        (Code("server/tests/test_findings.py",
              "test_create_finding_and_trace_evidence"),
         Code("server/tests/test_evidence_graph.py",
              "test_trace_walks_a_claim_to_its_source")),
        "100% of findings have a valid evidence chain; a fabricated or broken "
        "chain is a P0 defect",
        (Asserted("server/tests/test_findings.py"), Gate(P2_RUNNER, P2_REPORT)),
    ),
    _r(
        "AT-16", "Finding Creation", "# 20. AT-16 — Finding Creation",
        False, "",
        (UX(20, "Finding UX"), Web("web/src/CaseWorkspace.tsx", "FindingsPanel")),
        (Code("server/app/main.py", "create_finding"),
         Code("server/app/models.py", "Finding")),
        (Code("server/tests/test_findings.py", "test_findings_survive_reopen"),
         Code("server/tests/test_findings.py", "test_set_validation_status")),
        "100% of scenarios: the claim persists, evidence attaches, the link "
        "survives restart, limitations record, the status persists",
        (Asserted("server/tests/test_findings.py"),),
    ),
    _r(
        "AT-17", "Validation Coverage", "# 21. AT-17 — Validation Coverage",
        False, "",
        (UX(21, "Validation UX"), Web("web/src/CaseWorkspace.tsx", "FindingsPanel")),
        (Code("server/app/validation.py", "validate_finding"),
         Code("server/app/validation.py", "DIMENSIONS")),
        (Code("server/tests/test_validation.py", "test_every_dimension_is_answered"),
         Code("server/tests/test_validation.py",
              "test_validate_fails_when_result_drifts")),
        "100% of findings expose a validation status; >= 95% of injected "
        "analytical problems are detected",
        (Asserted("server/tests/test_validation.py"),),
    ),
    _r(
        "AT-18", "Unsupported Causality", "# 22. AT-18 — Unsupported Causality",
        False, "",
        (UX(43, "Trust UX"), Web("web/src/CaseWorkspace.tsx", "FindingsPanel")),
        (Code("server/app/causality.py", "assess_causality"),
         Code("server/app/validation.py", "check_causality")),
        (Code("server/tests/test_causality.py",
              "test_at18_detection_rate_meets_95_percent"),
         Code("server/tests/test_causality.py",
              "test_at18_discrimination_rate_meets_95_percent"),
         Code("server/tests/test_causality.py",
              "test_at18_zero_conversions_is_held")),
        "50 cases: >= 95% flag unsupported causal claims, >= 95% distinguish "
        "association from causation, 0 conversions",
        (Asserted("server/tests/test_causality.py"),),
    ),
    _r(
        "AT-19", "AI Execution Honesty", "# 23. AT-19 — AI Execution Honesty",
        True, "Fabricated execution",
        (UX(24, "AI Actions"), Web("web/src/CaseWorkspace.tsx", "AgentPanel")),
        (Code("server/app/generator.py", "validate_code"),
         Code("server/app/drafter.py", "validate_draft"),
         Code("server/app/assistant.py", "validate_answer")),
        (Code("server/tests/test_code_generation.py", "test_generation_writes_no_state"),
         Code("server/tests/test_drafting.py",
              "test_drafting_writes_nothing_to_the_findings_table"),
         Code("server/tests/test_agent.py",
              "test_each_approval_performs_exactly_one_write")),
        "100 scenarios: 100% distinguish proposed from executed, 100% identify "
        "an unavailable result, 0 fabricated results",
        (Asserted("server/tests/test_agent.py"),),
    ),
    _r(
        "AT-20", "AI Structured Output", "# 24. AT-20 — AI Structured Output",
        False, "",
        (UX(23, "AI Interaction Model"),
         Web("web/src/CaseWorkspace.tsx", "AgentPanel")),
        (Code("server/app/planner.py", "validate_plan"),
         Code("server/app/refine.py", "validate_refinement")),
        (Code("server/tests/test_plans.py", "test_malformed_llm_output_falls_back"),
         Code("server/tests/test_code_generation.py",
              "test_malformed_llm_output_falls_back"),
         Code("server/tests/test_refine.py",
              "test_a_non_object_proposal_is_rejected")),
        ">= 98% valid structured output on the first response, >= 99.5% after "
        "automated repair",
        (Asserted("server/tests/test_llm_adapters.py"),),
    ),
    _r(
        "AT-21", "AI Relevance", "# 25. AT-21 — AI Relevance",
        False, "",
        (UX(22, "AI Assistant UX"), Web("web/src/CaseWorkspace.tsx", "AgentPanel")),
        (Code("server/app/assistant.py", "answer_question"),
         Code("server/app/assistant.py", "validate_answer")),
        (Code("server/tests/test_conversation.py",
              "test_every_ground_cites_an_artifact_the_case_has"),
         Code("server/tests/test_conversation.py",
              "test_an_llm_answer_that_invents_a_citation_falls_back")),
        ">= 90% of 50 representative cases rated relevant, against a "
        "predefined rubric",
        (Asserted("server/tests/test_conversation.py"),),
    ),
    _r(
        "AT-22", "AI Human Control", "# 26. AT-22 — AI Human Control",
        False, "",
        (UX(24, "AI Actions"), Web("web/src/CaseWorkspace.tsx", "AgentPanel")),
        (Code("server/app/agent.py", "approve"),
         Code("server/app/agent.py", "reject"),
         Code("server/app/main.py", "_apply_agent_step")),
        (Code("server/tests/test_agent.py",
              "test_each_approval_performs_exactly_one_write"),
         Code("server/tests/test_agent.py",
              "test_an_approval_id_must_name_the_current_pending_step"),
         Code("server/tests/test_multi_agent.py",
              "test_one_role_approval_cannot_authorise_another")),
        "100% of state-changing AI actions pass through the authorisation "
        "mechanism; no silent state change",
        (Asserted("server/tests/test_agent.py"),),
    ),
    _r(
        "AT-23", "Reproducibility", "# 27. AT-23 — Reproducibility",
        True, "Critical analytical calculation error",
        (UX(26, "Result Object UX"), Web("web/src/CaseWorkspace.tsx", "RunsPanel")),
        (Code("server/app/main.py", "_reproduce_sql"),
         Code("server/app/main.py", "_results_agree")),
        (Code("server/tests/test_validation.py",
              "test_validate_unordered_groupby_is_stable_across_reruns"),
         Code("server/tests/test_validation.py",
              "test_validate_accepts_reordered_unordered_result")),
        "100% of deterministic golden analyses reproduce the same result "
        "within the defined tolerance",
        (Asserted("server/tests/test_validation.py"), Gate(P2_RUNNER, P2_REPORT)),
    ),
    _r(
        "AT-24", "Case Reopening", "# 28. AT-24 — Case Reopening",
        False, "",
        (UX(45, "Case Overview"), Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("server/app/exporter.py", "import_package"),
         Code("server/app/main.py", "get_case")),
        (Code("server/tests/test_export.py", "test_round_trip_restores_the_case"),
         Code("server/tests/test_decision.py",
              "test_the_round_trip_restores_the_verdicts_and_the_decision")),
        "50 save-close-reopen cycles: 100% recovery, 0 missing findings, "
        "0 broken evidence, 0 lost validation states",
        (Asserted("server/tests/test_export.py"), Gate(E2E_RUNNER, E2E_REPORT)),
    ),
    _r(
        "AT-25", "Application Stability", "# 29. AT-25 — Application Stability",
        True, "Application cannot recover from normal critical failures",
        (UX(42, "UX State Model"), Web("web/src/App.tsx", "App")),
        (Code("server/app/main.py", "handle_unexpected_error"),
         Code("server/app/main.py", "app")),
        (Code("server/tests/test_health.py", "test_health_returns_ok"),
         Code("server/tests/test_error_semantics.py",
              "test_harness_fault_answers_500")),
        "0 P0 crash defects and >= 99.5% successful completion of the "
        "normal-use operations in the release regression suite",
        (Asserted("server/tests/test_health.py"), Gate(E2E_RUNNER, E2E_REPORT)),
    ),
    _r(
        "AT-26", "Error Recovery", "# 30. AT-26 — Error Recovery",
        True, "Application cannot recover from normal critical failures",
        (UX(38, "Error UX"), Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("server/app/errors.py", "INPUT_ERROR_TYPES"),
         Code("server/app/main.py", "handle_unexpected_error")),
        (Code("server/tests/test_error_semantics.py",
              "test_sql_syntax_error_answers_400"),
         Code("server/tests/test_error_semantics.py",
              "test_a_faults_id_finds_its_traceback_in_the_log"),
         Code("server/tests/test_envelope.py",
              "test_a_missing_file_is_refused_not_crashed")),
        "100% of defined failure scenarios leave the application in a "
        "recoverable state, and the case survives",
        (Asserted("server/tests/test_error_semantics.py"),),
    ),
    _r(
        "AT-27", "UI Responsiveness", "# 31. AT-27 — UI Responsiveness",
        False, "",
        (UX(27, "Modern Interaction Patterns"),
         Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("web/src/measure.ts", "p95"),
         Code("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Case(MEASURE_SUITE),),
        "95th percentile interaction response <= 200 ms on the defined "
        "benchmark hardware",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-27", "PASS"),
         Asserted(MEASURE_SUITE)),
    ),
    _r(
        "AT-28", "Case Loading", "# 32. AT-28 — Case Loading",
        False, "",
        (UX(45, "Case Overview"), Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("server/app/main.py", "get_case"),
         Code("server/app/decision.py", "build_decision")),
        (Case("server/tests/test_measure.py",
              "test_a_green_run_passes_the_gate"),),
        "95% of case openings complete within 2 seconds inside the supported "
        "envelope",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-28", "PASS"),
         Asserted("server/tests/test_measure.py")),
    ),
    _r(
        "AT-29", "Data Profiling Performance", "# 33. AT-29 — Data Profiling Performance",
        False, "",
        (UX(37, "Loading and Long-Running Operations"),
         Web("web/src/CaseWorkspace.tsx", "DataPanel")),
        (Code("server/app/analysis.py", "profile_csv"),
         Code("server/app/analysis.py", "_materialise")),
        (Case("server/tests/test_large_datasets.py",
              "test_profile_is_correct_at_scale"),),
        "95% of standard profiling operations complete within 5 seconds on "
        "the reference machine",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-29", "PASS"),
         Asserted("server/tests/test_large_datasets.py")),
    ),
    _r(
        "AT-30", "Long-Running Operations", "# 34. AT-30 — Long-Running Operations",
        False, "",
        (UX(37, "Loading and Long-Running Operations"),
         Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("web/src/CaseWorkspace.tsx", "RunRow"),
         Code("web/src/CaseWorkspace.tsx", "FindingRow"),
         Code("web/src/CaseWorkspace.tsx", "GeneratePanel")),
        (Case(MEASURE_SUITE),),
        "100% of benchmarked long-running operations provide a visible "
        "execution state",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-30", "PASS"),
         Asserted(MEASURE_SUITE)),
    ),
    _r(
        "AT-31", "Data Loss", "# 35. AT-31 — Data Loss",
        True, "Data loss",
        (UX(43, "Trust UX"), Web("web/src/CaseList.tsx", "CaseList")),
        (Code("server/app/exporter.py", "export_case"),
         Code("server/app/main.py", "delete_case")),
        (Code("server/tests/test_case_management.py",
              "test_delete_removes_case_and_its_data"),
         Code("server/tests/test_large_datasets.py",
              "test_large_case_exports_and_round_trips")),
        "0 known P0 data-loss defects at release; any reproducible loss of "
        "state, finding, evidence, validation or history is release-blocking",
        (Asserted("server/tests/test_case_management.py"),
         Gate(E2E_RUNNER, E2E_REPORT)),
    ),
    _r(
        "AT-32", "Accessibility", "# 36. AT-32 — Accessibility",
        False, "",
        (UX(41, "Accessibility"), Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("web/src/accessibility.ts", "auditAll"),
         Code("web/src/accessibility.ts", "focusIsGuaranteed")),
        (Case(A11Y_SUITE),),
        "100% of critical user flows keyboard-accessible, 0 critical "
        "accessibility violations",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-32", "PASS"),
         Asserted(A11Y_SUITE)),
    ),
    _r(
        "AT-33", "UX Completion", "# 37. AT-33 — UX Completion",
        False, "",
        (UX(45, "Case Overview"), Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("server/app/workflow.py", "case_progress"),
         Code("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Case(WEB_SUITE),),
        "10 users: >= 8/10 complete the core workflow without facilitator "
        "intervention and identify the current stage",
        (Asserted(WEB_SUITE), Gate(E2E_RUNNER, E2E_REPORT)),
    ),
    _r(
        "AT-34", "Evidence Understanding", "# 38. AT-34 — Evidence Understanding",
        False, "",
        (UX(19, "Evidence UX"), Web("web/src/CaseWorkspace.tsx", "EvidencePanel")),
        (Code("server/app/evidence.py", "build_evidence_graph"),
         Code("web/src/CaseWorkspace.tsx", "EvidencePanel")),
        (Case(WEB_SUITE),),
        ">= 8/10 representative users trace a displayed finding back to its "
        "supporting result, unaided",
        (Asserted(WEB_SUITE),),
    ),
    _r(
        "AT-35", "Validation Understanding", "# 39. AT-35 — Validation Understanding",
        False, "",
        (UX(21, "Validation UX"), Web("web/src/CaseWorkspace.tsx", "FindingsPanel")),
        (Code("server/app/validation.py", "validate_finding"),
         Code("web/src/CaseWorkspace.tsx", "FindingsPanel")),
        (Case(WEB_SUITE),),
        ">= 90% task accuracy distinguishing a result, a finding and a "
        "validated finding",
        (Asserted(WEB_SUITE),),
    ),
    _r(
        "AT-36", "Security", "# 40. AT-36 — Security",
        True, "Critical security vulnerability",
        (NoUX(NO_SURFACE_TRUST),),
        (Code("server/app/python_exec.py", "_seatbelt_profile"),
         Code("server/app/python_exec.py", "run_python")),
        (Code("server/tests/test_python_hard_sandbox.py",
              "test_seatbelt_profile_denies_writes_and_network"),
         Code("server/tests/test_python_guards.py",
              "test_the_import_guard_refuses_unsafe_modules")),
        "0 known critical security vulnerabilities at production release",
        (Asserted("server/tests/test_python_hard_sandbox.py"),),
    ),
    _r(
        "AT-37", "Dependency Security", "# 41. AT-37 — Dependency Security",
        True, "Critical security vulnerability",
        (NoUX(NO_SURFACE_TRUST),),
        (Code("verification/measure/deps.py", "measure_dependencies"),
         Code("verification/measure/deps.py", "classify_severity")),
        (Code("server/tests/test_measure.py",
              "test_an_unreachable_database_is_unknown_never_clean"),
         Code("server/tests/test_measure.py",
              "test_a_critical_advisory_is_counted_and_fails_the_gate")),
        "0 known Critical and 0 known High vulnerabilities without a "
        "documented risk acceptance",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-37", "PASS"),
         Asserted("server/tests/test_measure.py")),
    ),
    _r(
        "AT-38", "Test Coverage", "# 42. AT-38 — Test Coverage",
        False, "",
        (NoUX(NO_SURFACE_ENGINE),),
        (Code("verification/measure/coverage.py", "measure_coverage"),
         Code("verification/measure/coverage.py", "CORE_THRESHOLD")),
        (Code("server/tests/test_measure.py",
              "test_a_group_below_its_threshold_is_named"),),
        ">= 80% line coverage of core domain logic, >= 90% of the critical "
        "analytical, validation, evidence and reproducibility paths",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-38", "PASS"),
         Asserted("server/tests/test_measure.py")),
    ),
    _r(
        "AT-39", "Regression Suite", "# 43. AT-39 — Regression Suite",
        False, "",
        (NoUX(NO_SURFACE_ENGINE),),
        (Code(MEASURE_RUNNER, "run_all"),
         Code(GOLDEN_RUNNER, "run_golden")),
        (Case("server/tests/test_health.py", "test_health_returns_ok"),),
        "100% of release-blocking tests pass; no unresolved P0 or "
        "release-blocking P1 defect",
        (Gate(MEASURE_RUNNER, MEASURE_REPORT),
         Gate(GOLDEN_RUNNER, GOLDEN_REPORT, GOLDEN_GREEN),
         Gate(REFINE_RUNNER, REFINE_REPORT),
         Gate(E2E_RUNNER, E2E_REPORT)),
    ),
    _r(
        "AT-40", "Analytical Golden Dataset", "# 44. AT-40 — Analytical Golden Dataset",
        True, "Critical analytical calculation error",
        (NoUX(NO_SURFACE_ENGINE),),
        (Code("verification/golden/reference.py", "recompute"),
         Code("verification/golden/reference.py", "DATASETS")),
        (Code("server/tests/test_golden.py",
              "test_all_ten_at40_shapes_are_covered"),
         Code("server/tests/test_golden.py",
              "test_the_audit_catches_a_wrong_fixture")),
        "100% of deterministic reference calculations match the expected "
        "results within the defined tolerance",
        (Measured(GOLDEN_RUNNER, GOLDEN_REPORT, "AT-40", GOLDEN_GREEN),
         Asserted("server/tests/test_golden.py")),
    ),
    _r(
        "AT-41", "Finding-to-Evidence Integrity", "# 45. AT-41 — Finding-to-Evidence Integrity",
        True, "Incorrect validated finding",
        (UX(21, "Validation UX"), Web("web/src/CaseWorkspace.tsx", "FindingsPanel")),
        (Code("server/app/main.py", "set_validation_status"),
         Code("server/app/main.py", "create_finding")),
        (Code("server/tests/test_findings.py", "test_set_validation_status"),
         Code("server/tests/test_validation.py",
              "test_a_finding_quoting_an_invented_magnitude_fails_evidence")),
        "100% of validation-state transitions enforce the evidence "
        "requirement; a finding without mandatory evidence cannot validate",
        (Asserted("server/tests/test_findings.py"), Gate(P2_RUNNER, P2_REPORT)),
    ),
    _r(
        "AT-42", "Validation-State Integrity", "# 46. AT-42 — Validation-State Integrity",
        True, "Incorrect validated finding",
        (UX(21, "Validation UX"), Web("web/src/CaseWorkspace.tsx", "FindingsPanel")),
        (Code("server/app/main.py", "set_validation_status"),
         Code("server/app/validation.py", "HARD_DIMENSIONS")),
        (Code("server/tests/test_findings.py", "test_set_validation_status"),
         Code("server/tests/test_decision.py",
              "test_a_refused_finding_is_an_open_item_naming_what_failed")),
        "100% of invalid transition attempts are rejected",
        (Asserted("server/tests/test_findings.py"),),
    ),
    _r(
        "AT-43", "Export Integrity", "# 47. AT-43 — Export Integrity",
        False, "",
        (UX(47, "Case Export UX"), Web("web/src/DecisionPanel.tsx", "DecisionPanel")),
        (Code("server/app/exporter.py", "export_case"),
         Code("server/app/exporter.py", "import_package")),
        (Code("server/tests/test_export.py", "test_export_contains_every_section"),
         Code("server/tests/test_decision.py",
              "test_export_carries_the_verdicts_and_the_decision"),
         Code("server/tests/test_decision.py",
              "test_every_validated_finding_survives_the_round_trip")),
        "100%: required sections present, findings included, validation "
        "states preserved, evidence references preserved",
        (Asserted("server/tests/test_export.py"), Gate(E2E_RUNNER, E2E_REPORT)),
    ),
    _r(
        "AT-44", "Auditability", "# 48. AT-44 — Auditability",
        False, "",
        (UX(42, "UX State Model"),
         Web("web/src/CaseWorkspace.tsx", "HistoryPanel")),
        (Code("server/app/history.py", "build_case_history"),
         Code("server/app/history.py", "EVENT_FINDING_VALIDATED")),
        (Code("server/tests/test_case_history.py",
              "test_history_covers_every_artifact_in_order"),
         Code("server/tests/test_agent.py",
              "test_the_audit_trail_survives_the_import_round_trip")),
        ">= 99.9% of defined auditable events recorded correctly in the "
        "integration tests",
        (Asserted("server/tests/test_case_history.py"),),
    ),
    _r(
        "AT-45", "MVP Data Size Envelope", "# 49. AT-45 — MVP Data Size Envelope",
        False, "",
        (UX(14, "Data Workspace"), Web("web/src/CaseWorkspace.tsx", "DataPanel")),
        (Code("server/app/limits.py", "check_dataset_envelope"),
         Code("server/app/limits.py", "DEFAULT_MAX_ROWS"),
         Code("server/app/main.py", "envelope")),
        (Code("server/tests/test_envelope.py",
              "test_envelope_publishes_the_prd_targets"),
         Code("server/tests/test_envelope.py",
              "test_too_many_columns_is_refused_at_attach")),
        "the envelope is declared explicitly and enforced at each limit; a "
        "dataset beyond it is rejected, never silently failed",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-45", "PASS"),
         Asserted("server/tests/test_envelope.py")),
    ),
    _r(
        "AT-46", "Analysis Case Size Envelope", "# 50. AT-46 — Analysis Case Size Envelope",
        False, "",
        (UX(45, "Case Overview"), Web("web/src/CaseWorkspace.tsx", "CaseWorkspace")),
        (Code("server/app/limits.py", "case_limits"),
         Code("server/app/limits.py", "MAX_RUNS")),
        (Code("server/tests/test_measure.py",
              "test_the_boundary_counts_are_the_prds_envelope"),
         Code("server/tests/test_envelope.py",
              "test_the_case_envelope_constants_are_the_prd_benchmark")),
        "the application remains stable within the supported case envelope "
        "(runs, results, findings, evidence relationships)",
        (Measured(MEASURE_RUNNER, MEASURE_REPORT, "AT-46", "PASS"),
         Asserted("server/tests/test_envelope.py")),
    ),
    _r(
        "AT-47", "Export/Reopen Round Trip", "# 51. AT-47 — Export/Reopen Round Trip",
        False, "",
        (UX(47, "Case Export UX"),
         Web("web/src/DecisionPanel.tsx", "DecisionPanel")),
        (Code("server/app/exporter.py", "export_case"),
         Code("server/app/exporter.py", "import_package")),
        (Code("server/tests/test_export.py", "test_round_trip_restores_the_case"),
         Code("server/tests/test_export.py",
              "test_round_trip_relinks_references_and_serves_artifacts")),
        "100% preservation of the required analytical objects in the "
        "round-trip test suite",
        (Asserted("server/tests/test_export.py"), Gate(E2E_RUNNER, E2E_REPORT)),
    ),
    _r(
        "AT-48", "Requirement Traceability", "# 52. AT-48 — Requirement Traceability",
        False, "",
        (NoUX(NO_SURFACE_ENGINE),),
        (Code("verification/trace/matrix.py", "MATRIX"),
         Code("verification/trace/verify_trace.py", "run")),
        (Case("server/tests/test_trace.py",
              "test_every_requirement_the_prd_states_is_traced"),),
        "100% of P0 requirements traceable and >= 95% of P1 requirements "
        "traceable before the release gate",
        (Asserted("server/tests/test_trace.py"),),
    ),
)


# ------------------------------------------------------------------ views over

def by_id(at: str) -> Row:
    for row in MATRIX:
        if row.at == at:
            return row
    raise KeyError(at)


def ids() -> list[str]:
    return [row.at for row in MATRIX]


def p0_rows() -> list[Row]:
    return [row for row in MATRIX if row.p0]


def p1_rows() -> list[Row]:
    return [row for row in MATRIX if not row.p0]
