# Graph Report - DA-Harness  (2026-09-21)

## Corpus Check
- 120 files · ~187,622 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 2, .icns 1, .ico 1)

## Summary
- 2148 nodes · 4909 edges · 114 communities (105 shown, 5 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 687 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `33c27c63`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Product & Engineering Master Specification
- models.py
- web/package.json
- compilerOptions
- Coding-Agent Production System
- TestClient
- analysis.py
- test_interpretations.py
- test_evaluator.py
- Implementation Roadmap
- _DatasetHandle
- package.json
- dah-server
- test_case_history.py
- Verification & Production Readiness Plan
- DEC-001: Web-first MVP, Tauri post-MVP
- client
- P1 Vertical Slice - Verification Report
- Templates.tsx
- test_updates.py
- get
- validate_finding
- test_multi_dataset_runs.py
- test_plans.py
- test_charts_raster.py
- test_workflow.py
- test_drafting.py
- core_server.rs
- load_env_config
- test_conversation.py
- generator.py
- list_runs
- exporter.py
- P2 MVP Milestone Verification
- test_validation.py
- DAH - Global Roadmap Status
- Plan
- agent.py
- test_large_datasets.py
- test_case_management.py
- test_code_generation.py
- test_cases.py
- _require_case
- test_agent.py
- test_supervisor.py
- python_exec.py
- attach_dataset
- P4 Production Candidate Verification
- LLM Configuration
- test_profiles.py
- get_db
- test_export.py
- test_runs.py
- tauri.conf.json
- scripts
- DAH desktop shell
- P3 V1 Milestone Verification
- default.json
- CaseList.tsx
- dah_core_main.py
- build_sidecar.sh
- dah-shell
- test_logging.py
- DAH — Data Analysis Harness
- db.py
- test_error_semantics.py
- ValueError
- CaseWorkspace.tsx
- build_evidence_graph
- test_eda.py
- get_connection
- test_memory.py
- assistant.py
- Observability
- _capture_shape
- updates.rs
- test_dataset_delete.py
- handle_unexpected_error
- test_datasets.py
- post
- request
- _child_env
- main.py
- CaseWorkspace.test.tsx
- DAH - Task Archive
- list_plans
- Interpretation
- summarize_case
- evaluate
- messageOf
- logs.rs
- postChat
- RunRow
- GeneratePanel
- main
- ServerCommand
- test_learn.py
- verify_p3.py
- datetime
- verify_p1.py
- verify_p2.py
- LLMAssistant
- test_evidence_graph.py
- evaluator.py
- validate_code
- updates.py
- Evaluation
- verify_p4.py
- _RecallingAssistant
- _BrokenLLM

## God Nodes (most connected - your core abstractions)
1. `client()` - 234 edges
2. `get_connection()` - 135 edges
3. `messageOf()` - 42 edges
4. `request()` - 37 edges
5. `get_db()` - 33 edges
6. `_temp_env()` - 27 edges
7. `_case()` - 24 edges
8. `_temp_env()` - 22 edges
9. `DAH - Task Archive` - 22 edges
10. `run_query()` - 20 edges

## Surprising Connections (you probably didn't know these)
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p1/verify_p1.py → server/app/db.py
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p2/verify_p2.py → server/app/db.py
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p3/verify_p3.py → server/app/db.py
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p4/verify_p4.py → server/app/db.py
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P0 Foundation`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **P0 Verification System: gate + state + report** — verification_p0_report, ai_current_state, ai_tasks, ai_handoff [INFERRED 0.90]

## Communities (114 total, 5 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.05
Nodes (64): BaseModel, EvidenceGraph, get_evidence_graph(), node(), Every claim in the case and what it rests on (P3-EVIDENCE-006). The graph is…, Which schema shape the local store is on, and whether it is current. Read-only:…, schema_version(), AgentApproval (+56 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (33): jsdom, react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies (+25 more)

### Community 3 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Coding-Agent Production System"
Cohesion: 0.14
Nodes (12): Coding-Agent Production System, Agent Implementation Protocol, Artifact Authority Hierarchy, Agent Control Loop: PLAN to EXIT-CRITERIA, Development Context Protocol, Development State Model, Hard Stop Conditions, Persistent Project State (/ai documents) (+4 more)

### Community 5 - "TestClient"
Cohesion: 0.13
Nodes (40): _env(), _finished_case(), _finished_template(), _promote(), Case template tests for P3-CASE-007. A template is the skeleton a new case…, A templated case starts clean: question and label only, no data., Deleting a promoted case leaves the template usable., A case with a plan, a run and a validated finding - a shape to carry. (+32 more)

### Community 6 - "analysis.py"
Cohesion: 0.10
Nodes (29): _bind_dataset(), _bind_datasets(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), _execute_read_only(), _is_read_only() (+21 more)

### Community 7 - "test_interpretations.py"
Cohesion: 0.10
Nodes (33): _column_stats(), _configured_llm(), create_interpretation(), _fmt(), interpret_result(), _is_number(), LLMInterpreter, Any (+25 more)

### Community 8 - "test_evaluator.py"
Cohesion: 0.15
Nodes (37): _case_with_dataset(), _evaluate(), EVALUATE mode tests for P7-EVAL-001. The user hands DAH work that came from…, A column the dataset lacks is a Data fail, never a silent pass., A claim quoting a number the run does not contain is the commonest lie., A claim that cannot be wrong cannot be audited., A result whose order is not pinned cannot be checked by being redone., One row has no row order to disagree about, so no ORDER BY is required. (+29 more)

### Community 9 - "Implementation Roadmap"
Cohesion: 0.29
Nodes (15): Milestone Exit Criteria (P0-P5), Implementation Roadmap, Feature Priority Model (M/S/C/L), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate (+7 more)

### Community 10 - "_DatasetHandle"
Cohesion: 0.15
Nodes (7): _DatasetHandle, _DatasetQuery, Any, A bound, dunder-hardened callable that runs read-only SQL on the file.…, The read-only view of an attached dataset that user code receives., The attached file as a list of row dicts, under the standard row cap., _rows_as_dicts()

### Community 11 - "package.json"
Cohesion: 0.50
Nodes (3): devDependencies, @testing-library/jest-dom, @testing-library/jest-dom

### Community 13 - "test_case_history.py"
Cohesion: 0.29
Nodes (12): _history(), Case history tests for P3-CASE-007. The timeline is derived from each…, Validation has no timestamp of its own, so its status rides along., One case's artifacts never appear in another's timeline., Walking the whole loop leaves one event per artifact, chronologically., _temp_env(), test_events_carry_their_own_artifact_ids_and_details(), test_finding_event_carries_validation_status() (+4 more)

### Community 16 - "Verification & Production Readiness Plan"
Cohesion: 0.22
Nodes (9): Verification & Production Readiness Plan, AI Evaluation Dataset, AI Safety Rules, Data Trust Rules (Observed/Calculated/Inferred/...), Golden Datasets and Golden Analytical Tests, Production Readiness Checklist, Release Decision Matrix, Defect Severity Model (P0-P3) (+1 more)

### Community 17 - "DEC-001: Web-first MVP, Tauri post-MVP"
Cohesion: 0.29
Nodes (7): AGENTS.md graphify guidance, API-only frontend contract, DEC-001: Web-first MVP, Tauri post-MVP, Locked tech selections (FastAPI/SQLite/DuckDB), Control-Layer Architecture, Web-First Delivery Strategy (Tauri post-MVP), web/index.html (React entry point)

### Community 18 - "client"
Cohesion: 0.34
Nodes (19): client(), An unbounded loop ends at the time limit and the API answers 400., test_runaway_loop_is_bounded_and_reported(), _case_with_dataset(), _python(), _temp_env(), override(), test_evidence_chain_works_for_python_run() (+11 more)

### Community 19 - "P1 Vertical Slice - Verification Report"
Cohesion: 0.33
Nodes (5): Decision, Evidence, Exit criteria (Coding-Agent Production System section 8), Exit-test sequence (the full user journey), P1 Vertical Slice - Verification Report

### Community 20 - "Templates.tsx"
Cohesion: 0.21
Nodes (13): createCaseFromTemplate(), deleteTemplate(), listTemplates(), promoteCaseToTemplate(), Template, TemplateShape, PromoteTemplate(), save() (+5 more)

### Community 21 - "test_updates.py"
Cohesion: 0.07
Nodes (40): _kill_group(), Popen, Kill the worker and anything it spawned (sandbox-exec sits in between)., _case_with_dataset(), _python(), Hard-sandbox tests for P3-SEC-001. The inner guards (import allowlist,…, A timeout kills the worker and anything it spawned, not just the shell., A worker that dies on startup surfaces as a 400, never as an API crash. (+32 more)

### Community 22 - "get"
Cohesion: 0.08
Nodes (33): Case, CaseHistory, get, patch, _case_of(), create_case(), create_case_from_template(), duplicate_case() (+25 more)

### Community 23 - "validate_finding"
Cohesion: 0.18
Nodes (13): Append the reproducibility check and report whether it passed., A canonical sort key for one result row. DuckDB does not promise a row order…, Rerun the stored SQL and compare it to the persisted rows. A multi-dataset run…, Re-execute the stored script and compare the whole tabulated result. Both…, Reproduce a finding's computation and check its support. The trust loop closes…, _record_repro(), _reproduce_python(), _reproduce_sql() (+5 more)

### Community 24 - "test_multi_dataset_runs.py"
Cohesion: 0.31
Nodes (17): _case_with_datasets(), _multi_run(), Multi-dataset run tests for P3-DATA-003. Attaching several datasets per case…, The trust loop closes on a multi-dataset run too., The k-th placeholder binds to the k-th dataset, not to any file that fits., _temp_env(), override(), test_dataset_ids_must_be_unique() (+9 more)

### Community 25 - "test_plans.py"
Cohesion: 0.08
Nodes (35): _categorical_columns(), _column_names(), _configured_llm(), create_plan(), LLMPlanner, _null_columns(), _numeric_columns(), plan_analysis() (+27 more)

### Community 26 - "test_charts_raster.py"
Cohesion: 0.06
Nodes (53): ChartModel, _hex_rgb(), _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002). Turns a persisted…, A computed chart: geometry plus the data both renderers need. Everything…, Y-axis tick values from low to high. (+45 more)

### Community 27 - "test_workflow.py"
Cohesion: 0.30
Nodes (11): _progress(), Guided workflow tests for P3-FLOW-004. The stage is derived from artifacts, not…, Two datasets with one profile leaves the case at the profile stage., No stored stage: every call recomputes from the artifacts, per case., _temp_env(), override(), test_profile_stage_needs_every_dataset(), test_progress_404_for_unknown_case() (+3 more)

### Community 28 - "test_drafting.py"
Cohesion: 0.09
Nodes (40): _allowed_numbers(), _column_values(), _configured_llm(), create_draft(), draft_finding(), _fmt(), _is_number(), LLMDrafter (+32 more)

### Community 29 - "core_server.rs"
Cohesion: 0.13
Nodes (23): Child, Command, core_starts_and_answers_health(), dev_core_override_ignores_a_present_sidecar(), dev_resolution_uses_the_project_virtualenv(), HEALTH_INTERVAL, HEALTH_REQUEST_TIMEOUT, HEALTH_TIMEOUT (+15 more)

### Community 30 - "load_env_config"
Cohesion: 0.31
Nodes (8): load_env_config(), Load a local .env into the process environment. Returns True when a file was…, Environment configuration loading (LLM key setup follow-up). The server loads…, No file, no change, no error., An exported variable is not clobbered by a value in the file., test_env_file_is_loaded(), test_missing_env_file_is_a_no_op(), test_real_environment_wins_over_file()

### Community 31 - "test_conversation.py"
Cohesion: 0.17
Nodes (24): _ask(), _CapturingAssistant, _case_with_data(), _FailingAssistant, _InventingAssistant, _MalformedAssistant, Conversational memory tests for P3-AI-014. The last assistant slice: the case…, The names a ground may cite, read from the same rows the API served. (+16 more)

### Community 32 - "generator.py"
Cohesion: 0.12
Nodes (26): _columns(), _columns_referenced(), _configured_llm(), create_code(), _explain(), generate_code(), _is_identifier(), LLMGenerator (+18 more)

### Community 33 - "list_runs"
Cohesion: 0.18
Nodes (11): RunSummary, _dataset_ids_of(), delete_dataset(), get_run(), list_runs(), List analysis runs for a case, without the heavy result rows., Reopen a persisted analysis run, including its result rows., Remove one dataset from a case, leaving the case itself standing. The dataset… (+3 more)

### Community 34 - "exporter.py"
Cohesion: 0.18
Nodes (17): _chart_format(), _dataset_ids_of(), export_case(), _import_dataset_ids(), import_package(), PackageError, Path, Self-contained Analysis Case packages (P2-CASE-012). Export assembles… (+9 more)

### Community 35 - "P2 MVP Milestone Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,, Journey under test, P2 MVP Milestone Verification, Steps

### Community 36 - "test_validation.py"
Cohesion: 0.19
Nodes (20): _full_setup(), _python_setup(), The core guarantee: if the persisted result no longer matches a rerun,…, A GROUP BY without ORDER BY must not fail reproduction for getting its rows…, The same unordered query, validated repeatedly, must always agree. This is the…, Case + dataset + profile + Python run + finding., A changed result shape shows up as a column change even when values line up., A script that no longer runs is a verdict, never a 500. (+12 more)

### Community 37 - "DAH - Global Roadmap Status"
Cohesion: 0.18
Nodes (10): Current position detail, DAH - Global Roadmap Status, P3 V1 — entry checklist (COMPLETE), P4 Production Candidate — entry checklist (COMPLETE), P5 Production Grade — entry checklist (COMPLETE; signing retired by DEC-006), P6 Post-Launch Evolution — entry checklist (COMPLETE, 5 of 5), P7 Product Modes — entry checklist (1 of 4 done), Phase gate definitions (what "done" means) (+2 more)

### Community 38 - "Plan"
Cohesion: 0.50
Nodes (4): get_plan(), Retrieve the latest plan for a case's dataset., Plan, A structured analysis plan, persisted against a case and dataset.

### Community 39 - "agent.py"
Cohesion: 0.07
Nodes (49): _analyze_proposal(), approve(), _attempt_count(), _attempted_codes(), _chart_axes(), column_values(), is_number(), spread() (+41 more)

### Community 40 - "test_large_datasets.py"
Cohesion: 0.20
Nodes (18): _attach(), _generated_csv(), Large-dataset behaviour (P4-PERF-006). The 1000-row result cap had existed…, A full-table scan at scale is capped and flagged, never unbounded., An aggregation over the full set sees every row, not just the capped page., A table with many columns still reports one stat block per column. The…, The duplicate count is exact over a large set with known repeats., A case carrying a large dataset exports and restores intact. (+10 more)

### Community 41 - "test_case_management.py"
Cohesion: 0.28
Nodes (15): _counts(), _first_run(), _full_case(), A case with a dataset, profile, run, finding and chart attached., _temp_env(), override(), test_delete_does_not_touch_other_cases(), test_delete_is_idempotent_for_unknown_case() (+7 more)

### Community 42 - "test_code_generation.py"
Cohesion: 0.16
Nodes (22): _case_with_dataset(), _DeletingGenerator, _FailingGenerator, _GoodGenerator, _InventingGenerator, _MalformedGenerator, Code generation tests for P3-AI-013. Writing the analysis is the part of the…, _temp_env() (+14 more)

### Community 43 - "test_cases.py"
Cohesion: 0.21
Nodes (16): _client(), A `%` or `_` in the term is literal, not a LIKE wildcard., Absent or blank `q` is not a filter., The golden test: a case survives being saved and reopened., `q` matches the question, ignoring case (P3-CASE-007)., Point the app at a fresh on-disk SQLite file for this test., `q` also matches the dataset label., _temp_db() (+8 more)

### Community 44 - "_require_case"
Cohesion: 0.09
Nodes (31): AgentState, AgentStep, CaseProgress, ConversationTurn, Finding, _agent_state(), _agent_step_of(), chat_about_case() (+23 more)

### Community 45 - "test_agent.py"
Cohesion: 0.10
Nodes (53): _approve(), _case(), _counts(), _profiled(), _propose(), Agentic analysis tests for P6-AGENT-002. The loop already existed as endpoints;…, A proposal is recorded, not performed; the case gains no artifact., profile -> plan -> analyze -> interpret -> accept -> chart -> validate. (+45 more)

### Community 46 - "test_supervisor.py"
Cohesion: 0.16
Nodes (21): parent_pid(), pid_alive(), Parent-process supervision for the desktop shell. The Tauri shell is the only…, The pid the shell asked this core to outlive, or None if not supervised., Whether ``pid`` is currently a running process., Start a daemon thread that ends this process when the shell is gone. Returns…, start_parent_watchdog(), watch() (+13 more)

### Community 47 - "python_exec.py"
Cohesion: 0.10
Nodes (26): _alarm_handler(), _dataset_columns(), execute_user_code(), _failure(), _guarded_import(), _import_restrictions(), _ImportGuard, Exception (+18 more)

### Community 48 - "attach_dataset"
Cohesion: 0.12
Nodes (19): Dataset, FileResponse, attach_dataset(), _chart_media_type(), _format_for(), get_chart(), get_chart_image(), list_datasets() (+11 more)

### Community 49 - "P4 Production Candidate Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P4 gate: error semantics, determinism, scale,, Journey under test, P4 Production Candidate Verification, Steps

### Community 50 - "LLM Configuration"
Cohesion: 0.22
Nodes (8): 1. Create the file, 2. Start the server, 3. Check it took effect, Alternative: set the variables inline, LLM Configuration, Notes, Setup with a `.env` file (recommended), Variables

### Community 51 - "test_profiles.py"
Cohesion: 0.44
Nodes (9): _attach(), _temp_env(), override(), test_deep_profile_stats(), test_deep_profile_survives_reopen(), test_get_profile_before_profiling_returns_404(), test_header_only_dataset_profiles_cleanly(), test_profile_and_reopen() (+1 more)

### Community 52 - "get_db"
Cohesion: 0.42
Nodes (8): get_db(), _case_with_run(), _temp_env(), override(), test_create_finding_and_trace_evidence(), test_finding_unknown_run_returns_404(), test_findings_survive_reopen(), test_set_validation_status()

### Community 53 - "test_export.py"
Cohesion: 0.44
Nodes (8): _full_case(), _temp_env(), override(), test_export_contains_every_section(), test_export_unknown_case_returns_404(), test_import_rejects_bad_package(), test_round_trip_relinks_references_and_serves_artifacts(), test_round_trip_restores_the_case()

### Community 54 - "test_runs.py"
Cohesion: 0.47
Nodes (8): _case_with_dataset(), _temp_env(), override(), test_list_runs_excludes_rows(), test_rejects_multi_statement(), test_rejects_write_query(), test_run_aggregation_and_reopen(), test_run_unknown_dataset_returns_404()

### Community 56 - "tauri.conf.json"
Cohesion: 0.11
Nodes (17): app, security, windows, build, beforeBuildCommand, beforeDevCommand, frontendDist, bundle (+9 more)

### Community 57 - "scripts"
Cohesion: 0.12
Nodes (15): description, devDependencies, @tauri-apps/cli, name, private, scripts, build, dev (+7 more)

### Community 58 - "DAH desktop shell"
Cohesion: 0.25
Nodes (7): DAH desktop shell, How the core is started, Known limits, Layout, Running it, Tests, Why no remote-URL capability

### Community 59 - "P3 V1 Milestone Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P3 gate: multi-dataset joins, hard sandbox, the four, Journey under test, P3 V1 Milestone Verification, Steps

### Community 60 - "default.json"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 61 - "CaseList.tsx"
Cohesion: 0.12
Nodes (19): react, ApiError, Case, createCase(), deleteCase(), duplicateCase(), getHealth(), listCases() (+11 more)

### Community 62 - "dah_core_main.py"
Cohesion: 0.67
Nodes (3): main(), parse_port(), Entrypoint for the `dah-core` sidecar (the packaged Python core). DAH's desktop…

### Community 66 - "test_logging.py"
Cohesion: 0.06
Nodes (51): fixture, _clear_handlers(), configure_logging(), Path, Where the core's output goes when nobody is watching it (P5-OBSERVE-002). The…, The older backups, newest first. Empty when file logging is off., The last ``lines`` records of ``path``, in the order they were written. Reads…, Where the log file belongs. An explicit argument wins (tests use it against a… (+43 more)

### Community 67 - "DAH — Data Analysis Harness"
Cohesion: 0.25
Nodes (7): Building the packaged app, Checking for updates, DAH — Data Analysis Harness, Getting a build, Installing the app, Layers, When something goes wrong

### Community 68 - "db.py"
Cohesion: 0.16
Nodes (22): Connection, _ensure_column(), _m_cases_template_id(), _m_datasets_format(), _m_evaluations_table(), _m_profiles_duplicate_rows(), _m_runs_code(), _m_runs_dataset_ids_json() (+14 more)

### Community 69 - "test_error_semantics.py"
Cohesion: 0.08
Nodes (43): parametrize, RuntimeError, _Boom, _case_with_dataset(), _case_with_profile(), _client(), Error semantics: an input error answers 400, a server fault answers 500…, A fault inside the harness is a server error, never the input's fault. (+35 more)

### Community 70 - "ValueError"
Cohesion: 0.21
Nodes (19): Run a read-only SQL query against one attached file. The dataset path is bound…, run_query(), _column_types(), _columns_of(), _correlate(), _distribution(), _is_numeric(), _quote() (+11 more)

### Community 71 - "CaseWorkspace.tsx"
Cohesion: 0.06
Nodes (37): AgentState, AgentStep, AxisFinding, CaseHistory, CaseProgress, ClaimTrace, ConversationTurn, Dataset (+29 more)

### Community 72 - "build_evidence_graph"
Cohesion: 0.33
Nodes (6): build_evidence_graph(), _dataset_ids_of(), Any, Case-wide evidence graph and claim-to-source tracing (P3-EVIDENCE-006). The…, Every dataset a run bound, from its recorded list (P3-DATA-003)., Project a case into its evidence graph. Raises ValueError when the case has no…

### Community 73 - "test_eda.py"
Cohesion: 0.39
Nodes (14): _dataset(), _eda(), EDA tests for P3-ANALYSIS-005. Every op compiles to read-only DuckDB and runs…, _temp_env(), override(), test_correlates_two_numeric_columns(), test_distribution_falls_back_to_top_values_for_a_category(), test_distribution_summarises_a_numeric_column() (+6 more)

### Community 74 - "get_connection"
Cohesion: 0.11
Nodes (36): get_connection(), Path, Open a connection, ensuring the schema exists and is current. FastAPI runs sync…, override(), override(), override(), override(), override() (+28 more)

### Community 75 - "test_memory.py"
Cohesion: 0.13
Nodes (29): _case_with_finding(), _empty_case(), _finding_id(), Cross-case recall tests for P6-MEMORY-001. A case could already cite its own…, The headline behaviour: a question a prior case answered is answered from it., A cross-case ground must resolve to a case and finding that exist., `case:does-not-exist` fails validation, exactly as an invented column does., A finding id that does not exist cannot be cited as memory either. (+21 more)

### Community 76 - "assistant.py"
Cohesion: 0.14
Nodes (22): answer_question(), _artifact_grounds(), _counts(), create_answer(), _first_matching_column(), _fmt_stat(), _has_artifacts(), _memory_sentence() (+14 more)

### Community 77 - "Observability"
Cohesion: 0.29
Nodes (6): Finding the failure behind an error, Observability, Reading it, What is in it, What is not in it, Where the log lives

### Community 78 - "_capture_shape"
Cohesion: 0.12
Nodes (20): _capture_shape(), list_templates(), _profile_of(), promote_template(), A stored profile, or None when the dataset was never profiled., The analytical shape of a case, as a projection over what it has. Nothing is…, Promote a case into a reusable template (P3-CASE-007, P6-TEMPLATE-003). The…, List every saved template, newest first (P3-CASE-007). (+12 more)

### Community 79 - "updates.rs"
Cohesion: 0.18
Nodes (19): a_body_that_is_not_json_is_unknown(), a_missing_current_version_reads_as_unknown_rather_than_panicking(), a_newer_build_carries_its_page(), a_newer_build_without_a_page_is_unknown_not_a_guess(), a_private_repository_is_unknown_with_a_reason(), an_empty_body_is_unknown(), an_equal_build_is_current(), an_unknown_status_without_a_reason_still_has_one() (+11 more)

### Community 80 - "test_dataset_delete.py"
Cohesion: 0.21
Nodes (21): delete_case(), delete_template(), Remove a template. Cases created from it are unaffected (P3-CASE-007)., Delete a case and everything attached to it. Children are removed before the…, _case_with_datasets(), _dataset(), _delete(), Single-dataset deletion tests for P3-DATA-009. A case could already be deleted… (+13 more)

### Community 81 - "handle_unexpected_error"
Cohesion: 0.22
Nodes (9): exception_handler, JSONResponse, middleware, Request, handle_unexpected_error(), log_request(), Exception, A fault in the harness answers 500 as JSON, with an id (P5-RELIABILITY-003).… (+1 more)

### Community 82 - "test_datasets.py"
Cohesion: 0.22
Nodes (20): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+12 more)

### Community 83 - "post"
Cohesion: 0.07
Nodes (47): DraftFinding, EdaResult, Evaluation, post, Profile, _apply_agent_step(), approve_agent_step(), create_chart() (+39 more)

### Community 84 - "request"
Cohesion: 0.29
Nodes (17): attachDataset(), getAgentState(), getCase(), getCaseHistory(), getEvidenceGraph(), getProgress(), listChat(), listDatasets() (+9 more)

### Community 85 - "_child_env"
Cohesion: 0.25
Nodes (8): _child_env(), The macOS sandbox-exec profile for one run. Reads are unrestricted (the…, The minimal environment the worker inherits. The API process may carry…, _seatbelt_profile(), Secrets held by the API process never reach the worker., The profile production emits is enforced by the kernel, not by Python., test_child_env_scrubs_api_secrets(), test_seatbelt_profile_denies_writes_and_network()

### Community 86 - "main.py"
Cohesion: 0.06
Nodes (36): GeneratedCode, Which failures are the input's fault (P4-RELIABILITY-002). Every engine the API…, current_log_file(), The log file `GET /logs` reads, or None when file logging is off., _chart_row_to_summary(), generate_code(), get_case_learn_walk(), get_evidence_chain() (+28 more)

### Community 87 - "CaseWorkspace.test.tsx"
Cohesion: 0.12
Nodes (16): @testing-library/react, @testing-library/user-event, vitest, cases, agentIdle(), caseHistory, cleanFindings(), dataset (+8 more)

### Community 88 - "DAH - Task Archive"
Cohesion: 0.09
Nodes (22): DAH - Task Archive, P2-DATA-006 contract, P2-DATA-007 contract, P3-ANALYSIS-005 contract, P3-CASE-007 contract, P3-CHART-002 contract, P3-DATA-003 contract, P3-EVIDENCE-006 contract (+14 more)

### Community 89 - "list_plans"
Cohesion: 0.50
Nodes (4): list_plans(), Every plan recorded for a case's dataset, newest first., PlanSummary, Plan metadata without the plan body.

### Community 90 - "Interpretation"
Cohesion: 0.32
Nodes (8): Interpretation, get_interpretation(), _interpretation_of(), list_interpretations(), The latest reading of this run's result., Every reading of this run's result, newest first., Interpretation, A plain-language read of a persisted run result (P3-AI-011). An artifact of the…

### Community 91 - "summarize_case"
Cohesion: 0.21
Nodes (11): _profile_of(), Everything an answer about this case may draw on. Read from the case's own…, summarize_case(), _case_findings(), _content_words(), Any, Cross-case recall: let an answer cite what a previous case found…, The meaning-bearing lowercase tokens of a string, stopwords out. (+3 more)

### Community 93 - "evaluate"
Cohesion: 0.16
Nodes (17): AxisFinding, evaluate(), _evaluate_calculation(), _evaluate_data(), _evaluate_limitations(), _evaluate_method(), _evaluate_question(), _evaluate_visualization() (+9 more)

### Community 94 - "messageOf"
Cohesion: 0.17
Nodes (21): acceptFinding(), approveAgentStep(), evaluateDataset(), proposeAgentStep(), rejectAgentStep(), runEda(), validateFinding(), messageOf() (+13 more)

### Community 95 - "logs.rs"
Cohesion: 0.18
Nodes (13): log_location(), LogLocation, logs_url(), parse_log_location(), REQUEST_TIMEOUT, reveal_core_logs(), reveal_in_finder(), RevealOutcome (+5 more)

### Community 97 - "postChat"
Cohesion: 1.00
Nodes (3): postChat(), Chat(), send()

### Community 98 - "RunRow"
Cohesion: 0.60
Nodes (5): draftFinding, interpretRun(), RunRow(), draftIt(), read()

### Community 99 - "GeneratePanel"
Cohesion: 0.60
Nodes (5): generateCode(), runSql(), GeneratePanel(), propose(), run()

### Community 100 - "main"
Cohesion: 0.24
Nodes (10): AppHandle, Box, CHECK_UPDATES_ID, current_exe_dir(), main(), REVEAL_LOGS_ID, PathBuf, Result (+2 more)

### Community 103 - "ServerCommand"
Cohesion: 0.25
Nodes (7): health_url(), PathBuf, String, ServerCommand, the_live_core_reports_a_log_we_can_reveal(), Option, Vec

### Community 104 - "test_learn.py"
Cohesion: 0.09
Nodes (34): build_learn_walk(), Any, LEARN mode: the analytical process as a guided walk (P7-LEARN-001). The Master…, Project a case onto the LEARN ladder. Raises ValueError when the case does not…, case_progress(), _counts(), Any, Guided analysis workflow (P3-FLOW-004). The Master Specification's core loop is… (+26 more)

### Community 105 - "verify_p3.py"
Cohesion: 0.33
Nodes (8): build_parquet(), log(), main(), override(), record(), Path, P3 V1 milestone verification. Runs the full P3 user journey as one atomic gate,…, Write the targets table as Parquet, so the join mixes formats.

### Community 106 - "datetime"
Cohesion: 0.32
Nodes (7): datetime, build_case_history(), add(), _parse(), Any, Case history: a timeline of everything that happened in a case (P3-CASE-007).…, Project a case into its timeline. Raises ValueError when the case does not…

### Community 108 - "verify_p1.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P1 Vertical Slice milestone verification. Runs the full user journey as one…

### Community 109 - "verify_p2.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P2 MVP milestone verification. Runs the full P2 user journey as one atomic…

### Community 110 - "LLMAssistant"
Cohesion: 0.33
Nodes (4): _configured_llm(), LLMAssistant, OpenAI-compatible assistant; dormant without configuration. Implemented on…, The configured assistant, or None when no key is present.

### Community 111 - "test_evidence_graph.py"
Cohesion: 0.33
Nodes (13): _full_case(), _graph(), Evidence graph tests for P3-EVIDENCE-006. The graph is a projection of the…, A claim anchored on nothing shows up as an orphan, not as a trace., _temp_env(), override(), test_edges_describe_derivation(), test_graph_400_when_the_case_is_empty() (+5 more)

### Community 112 - "evaluator.py"
Cohesion: 0.21
Nodes (16): _allowed_numbers(), _evaluate_claim(), _evaluate_evidence(), _evaluate_quality(), _fmt(), _is_number(), _null_share(), _numbers_in() (+8 more)

### Community 114 - "validate_code"
Cohesion: 0.22
Nodes (11): _candidate_reads(), The columns an artifact plausibly reads, as candidate names. Aliases (`AS…, _looks_read_only(), Any, _python_read_columns(), Every column a Python snippet reads. Reads happen by index (`row["region"]`) or…, A single read-only statement, as the run engine would accept., Problems with an LLM proposal, as a list. Empty means acceptable. Beyond shape,… (+3 more)

### Community 115 - "updates.py"
Cohesion: 0.09
Nodes (31): Protocol, Whether a newer published build of DAH exists. Read-only, and deliberately…, updates_latest(), check_for_update(), current_version(), _HttpClient, httpx_client(), fetch() (+23 more)

### Community 116 - "Evaluation"
Cohesion: 0.29
Nodes (6): Evaluation, The nine-axis audit of one submitted artifact., _audit(), test_pure_module_matches_and_mismatches_a_chart(), test_pure_module_reports_an_execution_error_on_calculation(), test_pure_module_returns_an_evaluation_of_nine_findings()

### Community 117 - "verify_p4.py"
Cohesion: 0.25
Nodes (9): _Boom, _large_csv(), log(), main(), override(), record(), P4 Production Candidate verification. P3 proved the loop is *useful*. P4 proves…, A harness-side fault: not the input's fault, so never a 400. (+1 more)

## Knowledge Gaps
- **189 isolated node(s):** `name`, `private`, `version`, `description`, `tauri` (+184 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 835 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **5 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `TestClient`, `test_interpretations.py`, `test_evaluator.py`, `test_case_history.py`, `client`, `test_updates.py`, `test_multi_dataset_runs.py`, `test_plans.py`, `test_charts_raster.py`, `test_workflow.py`, `test_drafting.py`, `test_conversation.py`, `test_validation.py`, `test_large_datasets.py`, `test_case_management.py`, `test_code_generation.py`, `test_cases.py`, `test_agent.py`, `test_profiles.py`, `get_db`, `test_export.py`, `test_runs.py`, `db.py`, `test_error_semantics.py`, `test_eda.py`, `test_memory.py`, `test_dataset_delete.py`, `test_datasets.py`, `main.py`, `test_learn.py`, `verify_p3.py`, `verify_p1.py`, `verify_p2.py`, `test_evidence_graph.py`, `verify_p4.py`?**
  _High betweenness centrality (0.055) - this node is a cross-community bridge._
- **Why does `client()` connect `client` to `TestClient`, `test_interpretations.py`, `test_evaluator.py`, `test_case_history.py`, `test_updates.py`, `test_multi_dataset_runs.py`, `test_plans.py`, `test_charts_raster.py`, `test_workflow.py`, `test_drafting.py`, `test_conversation.py`, `test_validation.py`, `test_large_datasets.py`, `test_case_management.py`, `test_code_generation.py`, `test_agent.py`, `test_profiles.py`, `get_db`, `test_export.py`, `test_runs.py`, `test_logging.py`, `test_error_semantics.py`, `test_eda.py`, `test_dataset_delete.py`, `test_datasets.py`, `test_learn.py`, `test_evidence_graph.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `start_parent_watchdog()` connect `test_supervisor.py` to `main.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Are the 275 inferred relationships involving `TestClient` (e.g. with `test_a_case_with_no_usable_axis_ends_at_a_stated_reason()` and `test_a_closed_loop_proposes_nothing_further()`) actually correct?**
  _`TestClient` has 275 INFERRED edges - model-reasoned connections that need verification._
- **Are the 231 inferred relationships involving `client()` (e.g. with `test_a_case_with_no_usable_axis_ends_at_a_stated_reason()` and `test_a_closed_loop_proposes_nothing_further()`) actually correct?**
  _`client()` has 231 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _189 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._