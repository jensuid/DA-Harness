# Graph Report - DA-Harness  (2026-09-22)

## Corpus Check
- 130 files · ~230,201 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 2, .icns 1, .ico 1)

## Summary
- 2563 nodes · 5572 edges · 177 communities (121 shown, 52 thin omitted)
- Extraction: 86% EXTRACTED · 14% INFERRED · 0% AMBIGUOUS · INFERRED: 756 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `ba56a5ed`
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
- interpreter.py
- test_evaluator.py
- Implementation Roadmap
- _DatasetHandle
- package.json
- dah-server
- test_case_history.py
- Verification & Production Readiness Plan
- DEC-001: Web-first MVP, Tauri post-MVP
- test_python_runs.py
- P1 Vertical Slice - Verification Report
- UX- UI Architecture.md
- test_updates.py
- get
- validate_finding
- test_multi_dataset_runs.py
- test_plans.py
- test_charts_raster.py
- main.py
- test_drafting.py
- core_server.rs
- load_env_config
- test_conversation.py
- generator.py
- test_multi_agent.py
- exporter.py
- P2 MVP Milestone Verification
- test_validation.py
- DAH - Global Roadmap Status
- get_finding
- agent.py
- test_large_datasets.py
- test_case_management.py
- test_code_generation.py
- test_cases.py
- _require_case
- test_agent.py
- test_supervisor.py
- python_exec.py
- post
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
- get_evidence_graph
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
- Interpretation
- request
- planner.py
- Product Requirements Specification (PRD).md
- CaseWorkspace.test.tsx
- DAH - Task Archive
- Server
- 4. Proposed plan — phase P8: *Analytical Contract*
- summarize_case
- test_python_hard_sandbox.py
- evaluator.py
- messageOf
- logs.rs
- test_cors.py
- client
- verify_p3.py
- test_interpretations.py
- main
- Sample Cases — a detailed guide
- LLMGenerator
- ServerCommand
- test_learn.py
- _RecallingAssistant
- datetime
- LLMAssistant
- verify_p1.py
- verify_p2.py
- ContextPanel.tsx
- test_evidence_graph.py
- _evaluate_evidence
- chat_about_case
- _python_read_columns
- attach_dataset
- Evaluation
- GeneratePanel
- put_context
- e2e/REPORT.md
- 55. MVP Definition of Done
- 55. Anti-Patterns
- 57. Measurement Sources
- 54. Design System Principles
- 31. Layout Principles
- 50. MVP UX Scope
- 9. Adaptive Workspace
- 23. AI Interaction Model
- 8. Main Workspace Layout
- runEda
- 5. Global Acceptance Thresholds
- 10. AT-06 — Schema Detection
- 11. AT-07 — Data Profiling
- 12. AT-08 — Data Quality Detection
- 13. AT-09 — Quality Impact
- 14. AT-10 — Analysis Planning
- 15. AT-11 — SQL Execution
- 16. AT-12 — Python Execution
- 17. AT-13 — Result Integrity
- 18. AT-14 — Visualization Integrity
- 19. AT-15 — Evidence Traceability
- 20. AT-16 — Finding Creation
- 21. AT-17 — Validation Coverage
- 22. AT-18 — Unsupported Causality
- 23. AT-19 — AI Execution Honesty
- 24. AT-20 — AI Structured Output
- 25. AT-21 — AI Relevance
- 26. AT-22 — AI Human Control
- 27. AT-23 — Reproducibility
- 28. AT-24 — Case Reopening
- 30. AT-26 — Error Recovery
- 31. AT-27 — UI Responsiveness
- 32. AT-28 — Case Loading
- 34. AT-30 — Long-Running Operations
- 35. AT-31 — Data Loss
- 36. AT-32 — Accessibility
- 37. AT-33 — UX Completion
- 39. AT-35 — Validation Understanding
- 40. AT-36 — Security
- 41. AT-37 — Dependency Security
- 42. AT-38 — Test Coverage
- 43. AT-39 — Regression Suite
- 44. AT-40 — Analytical Golden Dataset
- 45. AT-41 — Finding-to-Evidence Integrity
- 46. AT-42 — Validation-State Integrity
- 47. AT-43 — Export Integrity
- 48. AT-44 — Auditability
- 49. AT-45 — MVP Data Size Envelope
- 52. AT-48 — Requirement Traceability
- 6. AT-02 — Case Persistence
- 7. AT-03 — Question Capture
- 9. AT-05 — Data Import
- Data Analysis Harness
- 30. Visual Design Language
- 3. Primary UX Principle
- 4. Primary Navigation Model
- Data Analysis Harness

## God Nodes (most connected - your core abstractions)
1. `client()` - 260 edges
2. `get_connection()` - 143 edges
3. `messageOf()` - 46 edges
4. `request()` - 44 edges
5. `get_db()` - 35 edges
6. `DAH - Task Archive` - 30 edges
7. `_temp_env()` - 27 edges
8. `_case()` - 24 edges
9. `_require_case()` - 23 edges
10. `_temp_env()` - 22 edges

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

## Communities (177 total, 52 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.05
Nodes (62): BaseModel, Which schema shape the local store is on, and whether it is current. Read-only:…, schema_version(), AxisFinding, CaseCreate, CaseFromTemplate, CaseHistory, CaseProgress (+54 more)

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
Cohesion: 0.08
Nodes (36): _bind_dataset(), _bind_datasets(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), _execute_read_only(), _header_field_count() (+28 more)

### Community 7 - "interpreter.py"
Cohesion: 0.17
Nodes (17): _column_stats(), _configured_llm(), create_interpretation(), _fmt(), interpret_result(), _is_number(), LLMInterpreter, Any (+9 more)

### Community 8 - "test_evaluator.py"
Cohesion: 0.12
Nodes (42): _audit(), _case_with_dataset(), _evaluate(), EVALUATE mode tests for P7-EVAL-001. The user hands DAH work that came from…, A column the dataset lacks is a Data fail, never a silent pass., A claim quoting a number the run does not contain is the commonest lie., A claim that cannot be wrong cannot be audited., A result whose order is not pinned cannot be checked by being redone. (+34 more)

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
Cohesion: 0.26
Nodes (13): _history(), Case history tests for P3-CASE-007. The timeline is derived from each…, Validation has no timestamp of its own, so its status rides along., One case's artifacts never appear in another's timeline., Walking the whole loop leaves one event per artifact, chronologically., _temp_env(), override(), test_events_carry_their_own_artifact_ids_and_details() (+5 more)

### Community 16 - "Verification & Production Readiness Plan"
Cohesion: 0.22
Nodes (9): Verification & Production Readiness Plan, AI Evaluation Dataset, AI Safety Rules, Data Trust Rules (Observed/Calculated/Inferred/...), Golden Datasets and Golden Analytical Tests, Production Readiness Checklist, Release Decision Matrix, Defect Severity Model (P0-P3) (+1 more)

### Community 17 - "DEC-001: Web-first MVP, Tauri post-MVP"
Cohesion: 0.29
Nodes (7): AGENTS.md graphify guidance, API-only frontend contract, DEC-001: Web-first MVP, Tauri post-MVP, Locked tech selections (FastAPI/SQLite/DuckDB), Control-Layer Architecture, Web-First Delivery Strategy (Tauri post-MVP), web/index.html (React entry point)

### Community 18 - "test_python_runs.py"
Cohesion: 0.38
Nodes (16): _case_with_dataset(), _python(), _temp_env(), override(), test_evidence_chain_works_for_python_run(), test_python_allows_safe_import(), test_python_rejects_blocked_import(), test_python_rejects_dunder_escape() (+8 more)

### Community 19 - "P1 Vertical Slice - Verification Report"
Cohesion: 0.33
Nodes (5): Decision, Evidence, Exit criteria (Coding-Agent Production System section 8), Exit-test sequence (the full user journey), P1 Vertical Slice - Verification Report

### Community 20 - "UX- UI Architecture.md"
Cohesion: 0.04
Nodes (49): 10. Home / Case Dashboard, 11. Create Analysis UX, 12. Question Refinement UX, 13. Context UX, 14. Data Workspace, 15. Data Quality UX, 16. Exploration UX, 17. Analysis Workspace (+41 more)

### Community 21 - "test_updates.py"
Cohesion: 0.06
Nodes (55): Protocol, check_for_update(), current_version(), _HttpClient, httpx_client(), fetch(), is_update_available(), parse_feed_answer() (+47 more)

### Community 22 - "get"
Cohesion: 0.07
Nodes (36): Case, get, LearnWalk, _case_of(), create_case(), create_case_from_template(), duplicate_case(), export_case_package() (+28 more)

### Community 23 - "validate_finding"
Cohesion: 0.11
Nodes (20): RunSummary, _dataset_ids_of(), get_run(), list_runs(), The datasets a run touches; None means an unknown (legacy) set. Older runs…, List analysis runs for a case, without the heavy result rows., Reopen a persisted analysis run, including its result rows., Append the reproducibility check and report whether it passed. (+12 more)

### Community 24 - "test_multi_dataset_runs.py"
Cohesion: 0.31
Nodes (17): _case_with_datasets(), _multi_run(), Multi-dataset run tests for P3-DATA-003. Attaching several datasets per case…, The trust loop closes on a multi-dataset run too., The k-th placeholder binds to the k-th dataset, not to any file that fits., _temp_env(), override(), test_dataset_ids_must_be_unique() (+9 more)

### Community 25 - "test_plans.py"
Cohesion: 0.16
Nodes (21): Any, Check a plan (from any engine) against the contract before persisting. Returns…, validate_plan(), _case_with_profile(), _FailingLLM, _GoodLLM, _MalformedLLM, The basis is part of the plan contract, so a malformed one is a problem rather… (+13 more)

### Community 26 - "test_charts_raster.py"
Cohesion: 0.06
Nodes (53): ChartModel, _hex_rgb(), _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002). Turns a persisted…, A computed chart: geometry plus the data both renderers need. Everything…, Y-axis tick values from low to high. (+45 more)

### Community 27 - "main.py"
Cohesion: 0.07
Nodes (34): AgentStep, GeneratedCode, Which failures are the input's fault (P4-RELIABILITY-002). Every engine the API…, _agent_step_of(), _chart_row_to_summary(), generate_code(), get_chart(), list_charts() (+26 more)

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
Cohesion: 0.16
Nodes (27): _ask(), _CapturingAssistant, _case_with_data(), _FailingAssistant, _InventingAssistant, _MalformedAssistant, Conversational memory tests for P3-AI-014. The last assistant slice: the case…, The names a ground may cite, read from the same rows the API served. (+19 more)

### Community 32 - "generator.py"
Cohesion: 0.12
Nodes (27): _columns(), _columns_referenced(), create_code(), _explain(), generate_code(), _is_identifier(), _looks_like_an_id(), _looks_read_only() (+19 more)

### Community 33 - "test_multi_agent.py"
Cohesion: 0.20
Nodes (24): _approve(), _case_with_a_finding(), _propose(), Multi-agent workflow tests for P7-AGENT-001. The spec names an *autonomous*…, A 409 names the role's own pending step - one role's write is never authorised…, Two honest notions stay distinct: the finding's own validation status is about…, A GET never proposes, for any role - a page refresh commits nothing., A case the analyst has walked as far as a recorded finding. (+16 more)

### Community 34 - "exporter.py"
Cohesion: 0.19
Nodes (16): _chart_format(), _dataset_ids_of(), export_case(), _import_dataset_ids(), import_package(), PackageError, Path, A package that cannot be imported; the caller answers 400 with it. (+8 more)

### Community 35 - "P2 MVP Milestone Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,, Journey under test, P2 MVP Milestone Verification, Steps

### Community 36 - "test_validation.py"
Cohesion: 0.19
Nodes (20): _full_setup(), _python_setup(), The core guarantee: if the persisted result no longer matches a rerun,…, A GROUP BY without ORDER BY must not fail reproduction for getting its rows…, The same unordered query, validated repeatedly, must always agree. This is the…, Case + dataset + profile + Python run + finding., A changed result shape shows up as a column change even when values line up., A script that no longer runs is a verdict, never a 500. (+12 more)

### Community 37 - "DAH - Global Roadmap Status"
Cohesion: 0.18
Nodes (10): Current position detail, DAH - Global Roadmap Status, P3 V1 — entry checklist (COMPLETE), P4 Production Candidate — entry checklist (COMPLETE), P5 Production Grade — entry checklist (COMPLETE; signing retired by DEC-006), P6 Post-Launch Evolution — entry checklist (COMPLETE, 5 of 5), P7 Product Modes — entry checklist (1 of 4 done), Phase gate definitions (what "done" means) (+2 more)

### Community 38 - "get_finding"
Cohesion: 0.18
Nodes (13): Finding, patch, get_evidence_chain(), get_finding(), list_findings(), List findings recorded against a case., Reopen a single finding., Trace a finding back to its computation and dataset. Walks finding -> run ->… (+5 more)

### Community 39 - "agent.py"
Cohesion: 0.06
Nodes (57): _analyst_step(), _analyze_proposal(), approve(), _attempt_count(), _attempted_codes(), _audited_claims(), _chart_axes(), column_values() (+49 more)

### Community 40 - "test_large_datasets.py"
Cohesion: 0.22
Nodes (17): _attach(), _generated_csv(), Large-dataset behaviour (P4-PERF-006). The 1000-row result cap had existed…, A full-table scan at scale is capped and flagged, never unbounded., An aggregation over the full set sees every row, not just the capped page., A table with many columns still reports one stat block per column. The…, The duplicate count is exact over a large set with known repeats., A case carrying a large dataset exports and restores intact. (+9 more)

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
Cohesion: 0.10
Nodes (32): AgentState, CaseProgress, _agent_state(), approve_agent_step(), approve_role_agent_step(), create_multi_dataset_run(), get_agent_state(), get_case_progress() (+24 more)

### Community 45 - "test_agent.py"
Cohesion: 0.10
Nodes (53): _approve(), _case(), _counts(), _profiled(), _propose(), Agentic analysis tests for P6-AGENT-002. The loop already existed as endpoints;…, A proposal is recorded, not performed; the case gains no artifact., profile -> plan -> analyze -> interpret -> accept -> chart -> validate. (+45 more)

### Community 46 - "test_supervisor.py"
Cohesion: 0.16
Nodes (21): parent_pid(), pid_alive(), Parent-process supervision for the desktop shell. The Tauri shell is the only…, The pid the shell asked this core to outlive, or None if not supervised., Whether ``pid`` is currently a running process., Start a daemon thread that ends this process when the shell is gone. Returns…, start_parent_watchdog(), watch() (+13 more)

### Community 47 - "python_exec.py"
Cohesion: 0.10
Nodes (26): _alarm_handler(), _dataset_columns(), execute_user_code(), _failure(), _guarded_import(), _import_restrictions(), _ImportGuard, Exception (+18 more)

### Community 48 - "post"
Cohesion: 0.07
Nodes (45): DraftFinding, EdaResult, Evaluation, post, Profile, _apply_agent_step(), create_chart(), create_finding() (+37 more)

### Community 49 - "P4 Production Candidate Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P4 gate: error semantics, determinism, scale,, Journey under test, P4 Production Candidate Verification, Steps

### Community 50 - "LLM Configuration"
Cohesion: 0.22
Nodes (8): 1. Create the file, 2. Start the server, 3. Check it took effect, Alternative: set the variables inline, LLM Configuration, Notes, Setup with a `.env` file (recommended), Variables

### Community 51 - "test_profiles.py"
Cohesion: 0.42
Nodes (10): _attach(), _temp_env(), override(), test_deep_profile_stats(), test_deep_profile_survives_reopen(), test_get_profile_before_profiling_returns_404(), test_header_only_dataset_profiles_cleanly(), test_profile_and_reopen() (+2 more)

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
Cohesion: 0.10
Nodes (25): react, @testing-library/react, @testing-library/user-event, vitest, ApiError, Case, createCase(), deleteCase() (+17 more)

### Community 62 - "dah_core_main.py"
Cohesion: 0.67
Nodes (3): main(), parse_port(), Entrypoint for the `dah-core` sidecar (the packaged Python core). DAH's desktop…

### Community 66 - "test_logging.py"
Cohesion: 0.05
Nodes (55): fixture, _clear_handlers(), configure_logging(), current_log_file(), Path, Where the core's output goes when nobody is watching it (P5-OBSERVE-002). The…, The log file `GET /logs` reads, or None when file logging is off., The older backups, newest first. Empty when file logging is off. (+47 more)

### Community 67 - "DAH — Data Analysis Harness"
Cohesion: 0.25
Nodes (7): Building the packaged app, Checking for updates, DAH — Data Analysis Harness, Getting a build, Installing the app, Layers, When something goes wrong

### Community 68 - "db.py"
Cohesion: 0.15
Nodes (24): Connection, _ensure_column(), _m_agent_steps_role(), _m_cases_template_id(), _m_contexts_table(), _m_datasets_format(), _m_evaluations_table(), _m_profiles_duplicate_rows() (+16 more)

### Community 69 - "test_error_semantics.py"
Cohesion: 0.15
Nodes (28): parametrize, _Boom, _case_with_dataset(), _case_with_profile(), _client(), Error semantics: an input error answers 400, a server fault answers 500…, A fault inside the harness is a server error, never the input's fault., Any failure still degrades to deterministic - and now leaves a trace. (+20 more)

### Community 70 - "ValueError"
Cohesion: 0.21
Nodes (19): Run a read-only SQL query against one attached file. The dataset path is bound…, run_query(), _column_types(), _columns_of(), _correlate(), _distribution(), _is_numeric(), _quote() (+11 more)

### Community 71 - "CaseWorkspace.tsx"
Cohesion: 0.05
Nodes (51): AgentRole, AgentState, AgentStep, approveAgentStep(), approveRoleAgentStep(), AxisFinding, CaseHistory, CaseProgress (+43 more)

### Community 72 - "get_evidence_graph"
Cohesion: 0.18
Nodes (12): EvidenceGraph, build_evidence_graph(), _dataset_ids_of(), Any, Case-wide evidence graph and claim-to-source tracing (P3-EVIDENCE-006). The…, Every dataset a run bound, from its recorded list (P3-DATA-003)., Project a case into its evidence graph. Raises ValueError when the case has no…, get_evidence_graph() (+4 more)

### Community 73 - "test_eda.py"
Cohesion: 0.39
Nodes (14): _dataset(), _eda(), EDA tests for P3-ANALYSIS-005. Every op compiles to read-only DuckDB and runs…, _temp_env(), override(), test_correlates_two_numeric_columns(), test_distribution_falls_back_to_top_values_for_a_category(), test_distribution_summarises_a_numeric_column() (+6 more)

### Community 74 - "get_connection"
Cohesion: 0.10
Nodes (39): get_connection(), Path, Open a connection, ensuring the schema exists and is current. FastAPI runs sync…, override(), override(), override(), A store written at schema 9 opens, gains the contexts table, and loses nothing…, test_a_pre_v10_store_upgrades_and_keeps_its_rows() (+31 more)

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
Cohesion: 0.20
Nodes (11): exception_handler, JSONResponse, middleware, Request, cors(), handle_unexpected_error(), log_request(), Exception (+3 more)

### Community 82 - "test_datasets.py"
Cohesion: 0.22
Nodes (20): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+12 more)

### Community 83 - "Interpretation"
Cohesion: 0.32
Nodes (8): Interpretation, get_interpretation(), _interpretation_of(), list_interpretations(), The latest reading of this run's result., Every reading of this run's result, newest first., Interpretation, A plain-language read of a persisted run result (P3-AI-011). An artifact of the…

### Community 84 - "request"
Cohesion: 0.27
Nodes (19): attachDataset(), getAgentState(), getCase(), getCaseHistory(), getEvidenceGraph(), getLearnWalk(), getProgress(), getRoleAgentState() (+11 more)

### Community 85 - "planner.py"
Cohesion: 0.12
Nodes (23): _basis_for(), _categorical_columns(), _column_names(), _configured_llm(), create_plan(), LLMPlanner, _null_columns(), _numeric_columns() (+15 more)

### Community 86 - "Product Requirements Specification (PRD).md"
Cohesion: 0.10
Nodes (19): 1. Purpose, 29. AT-25 — Application Stability, 2. Product Definition, 33. AT-29 — Data Profiling Performance, 38. AT-34 — Evidence Understanding, 3. Product Goal, 4. Core Acceptance Philosophy, 50. AT-46 — Analysis Case Size Envelope (+11 more)

### Community 87 - "CaseWorkspace.test.tsx"
Cohesion: 0.16
Nodes (12): agentIdle(), caseHistory, cleanFindings(), dataset, emptyContext(), evaluation(), evidenceGraph, finding() (+4 more)

### Community 88 - "DAH - Task Archive"
Cohesion: 0.06
Nodes (30): DAH - Task Archive, P2-DATA-006 contract, P2-DATA-007 contract, P3-ANALYSIS-005 contract, P3-CASE-007 contract, P3-CHART-002 contract, P3-DATA-003 contract, P3-EVIDENCE-006 contract (+22 more)

### Community 89 - "Server"
Cohesion: 0.19
Nodes (10): log(), main(), note(), End-to-end verification against a REAL server. The P2/P3/P4 gates drive the app…, A case the analyst agent drives itself, one approved write at a time. This is…, A real uvicorn server on a free port, isolated to a temp data dir., run_agent_case(), run_journey() (+2 more)

### Community 90 - "4. Proposed plan — phase P8: *Analytical Contract*"
Cohesion: 0.11
Nodes (17): 1. Verdict, 2. Where DAH already satisfies the contract, 3. The gaps, in the PRD's own priority order, 4. Proposed plan — phase P8: *Analytical Contract*, DAH — PRD & UX/UI Conformance Evaluation, Entry checklist, Level 0 — Safety / Trust (0 tolerance): **MET**, Level 1 — Correctness (≈100%): **MOSTLY MET** (+9 more)

### Community 91 - "summarize_case"
Cohesion: 0.21
Nodes (11): _profile_of(), Everything an answer about this case may draw on. Read from the case's own…, summarize_case(), _case_findings(), _content_words(), Any, Cross-case recall: let an answer cite what a previous case found…, The meaning-bearing lowercase tokens of a string, stopwords out. (+3 more)

### Community 92 - "test_python_hard_sandbox.py"
Cohesion: 0.11
Nodes (24): _child_env(), _kill_group(), Popen, The macOS sandbox-exec profile for one run. Reads are unrestricted (the…, The minimal environment the worker inherits. The API process may carry…, Kill the worker and anything it spawned (sandbox-exec sits in between)., _seatbelt_profile(), _case_with_dataset() (+16 more)

### Community 93 - "evaluator.py"
Cohesion: 0.16
Nodes (22): AxisFinding, evaluate(), _evaluate_calculation(), _evaluate_data(), _evaluate_limitations(), _evaluate_method(), _evaluate_quality(), _evaluate_question() (+14 more)

### Community 94 - "messageOf"
Cohesion: 0.11
Nodes (33): acceptFinding(), createCaseFromTemplate(), deleteTemplate(), draftFinding, evaluateDataset(), interpretRun(), listTemplates(), postChat() (+25 more)

### Community 95 - "logs.rs"
Cohesion: 0.18
Nodes (13): log_location(), LogLocation, logs_url(), parse_log_location(), REQUEST_TIMEOUT, reveal_core_logs(), reveal_in_finder(), RevealOutcome (+5 more)

### Community 96 - "test_cors.py"
Cohesion: 0.20
Nodes (9): CORS for the desktop shell. The packaged app's frontend is served from the…, The shell's origin is named back, so the browser releases the body., OPTIONS has no endpoint, so the middleware answers it or the real request is…, A webpage on an origin of its own cannot read the analyst's cases. The response…, The list stays auditable: every entry is a real shell origin., test_a_preflight_is_answered_not_routed(), test_an_allowed_origin_is_echoed(), test_an_unknown_origin_gets_no_cors_header() (+1 more)

### Community 97 - "client"
Cohesion: 0.34
Nodes (16): _case(), P8-CONTEXT-001: a case carries the analyst's stated intent. The primary…, _temp_env(), override(), test_an_older_package_without_context_degrades_to_empty(), test_context_defaults_to_empty_without_a_404(), test_context_is_rejected_for_an_unknown_case(), test_context_persists_and_reopens() (+8 more)

### Community 98 - "verify_p3.py"
Cohesion: 0.33
Nodes (8): build_parquet(), log(), main(), override(), record(), Path, P3 V1 milestone verification. Runs the full P3 user journey as one atomic gate,…, Write the targets table as Parquet, so the join mixes formats.

### Community 99 - "test_interpretations.py"
Cohesion: 0.06
Nodes (40): RuntimeError, plan(), leaking(), _case_with_sql_run(), _FailingInterpreter, _GoodInterpreter, _MalformedInterpreter, Result interpretation tests for P3-AI-011. The loop could run, chart, validate… (+32 more)

### Community 100 - "main"
Cohesion: 0.24
Nodes (10): AppHandle, Box, CHECK_UPDATES_ID, current_exe_dir(), main(), REVEAL_LOGS_ID, PathBuf, Result (+2 more)

### Community 101 - "Sample Cases — a detailed guide"
Cohesion: 0.15
Nodes (12): Case 1 — "Why did western region revenue dip in Q3?", Case 2 — "Does marketing spend drive signups?", Case 3 — "Which support category is slowest to resolve?", Drive it, step by step, If something looks wrong, Sample Cases — a detailed guide, The loop, in one breath, The trap this case is here for (+4 more)

### Community 102 - "LLMGenerator"
Cohesion: 0.40
Nodes (4): _configured_llm(), LLMGenerator, OpenAI-compatible generator; dormant without configuration. Implemented on…, The configured generator, or None when no key is present.

### Community 103 - "ServerCommand"
Cohesion: 0.25
Nodes (7): health_url(), PathBuf, String, ServerCommand, the_live_core_reports_a_log_we_can_reveal(), Option, Vec

### Community 104 - "test_learn.py"
Cohesion: 0.07
Nodes (45): build_learn_walk(), Any, LEARN mode: the analytical process as a guided walk (P7-LEARN-001). The Master…, Project a case onto the LEARN ladder. Raises ValueError when the case does not…, case_progress(), _counts(), Any, Guided analysis workflow (P3-FLOW-004). The Master Specification's core loop is… (+37 more)

### Community 106 - "datetime"
Cohesion: 0.22
Nodes (10): CaseHistory, datetime, build_case_history(), add(), _parse(), Any, Case history: a timeline of everything that happened in a case (P3-CASE-007).…, Project a case into its timeline. Raises ValueError when the case does not… (+2 more)

### Community 107 - "LLMAssistant"
Cohesion: 0.33
Nodes (4): _configured_llm(), LLMAssistant, OpenAI-compatible assistant; dormant without configuration. Implemented on…, The configured assistant, or None when no key is present.

### Community 108 - "verify_p1.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P1 Vertical Slice milestone verification. Runs the full user journey as one…

### Community 109 - "verify_p2.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P2 MVP milestone verification. Runs the full P2 user journey as one atomic…

### Community 110 - "ContextPanel.tsx"
Cohesion: 0.24
Nodes (9): CaseContext, getContext(), putContext(), ContextPanel(), load(), save(), empty(), FIELDS (+1 more)

### Community 111 - "test_evidence_graph.py"
Cohesion: 0.33
Nodes (13): _full_case(), _graph(), Evidence graph tests for P3-EVIDENCE-006. The graph is a projection of the…, A claim anchored on nothing shows up as an orphan, not as a trace., _temp_env(), override(), test_edges_describe_derivation(), test_graph_400_when_the_case_is_empty() (+5 more)

### Community 112 - "_evaluate_evidence"
Cohesion: 0.24
Nodes (11): _allowed_numbers(), _evaluate_claim(), _evaluate_evidence(), _fmt(), _is_number(), _numbers_in(), Any, Every numeric token a claim quotes - the same notion a draft is judged by. (+3 more)

### Community 113 - "chat_about_case"
Cohesion: 0.33
Nodes (7): ConversationTurn, chat_about_case(), list_chat(), Answer a question about the case, and remember the exchange. The case's own…, The case's conversation, oldest first, so a reopened case resumes., ConversationTurn, One question and its answer, grounded in the case's artifacts (P3-AI-014). A…

### Community 114 - "_python_read_columns"
Cohesion: 0.40
Nodes (6): _candidate_reads(), The columns an artifact plausibly reads, as candidate names. Aliases (`AS…, _python_read_columns(), Every column a Python snippet reads. Reads happen by index (`row["region"]`) or…, Every column a SQL statement could be reading. Aliases (`AS total`) and…, _sql_identifiers()

### Community 115 - "attach_dataset"
Cohesion: 0.12
Nodes (19): Dataset, FileResponse, attach_dataset(), _chart_media_type(), delete_dataset(), _format_for(), get_chart_image(), list_datasets() (+11 more)

### Community 117 - "GeneratePanel"
Cohesion: 0.60
Nodes (5): generateCode(), runSql(), GeneratePanel(), propose(), run()

### Community 118 - "put_context"
Cohesion: 0.24
Nodes (10): CaseContext, put, _context_of(), get_context(), put_context(), The case's context, or an empty one - never a 404. A case without a context row…, The case's stated intent: purpose, sub-questions, hypotheses, constraints.…, Replace the case's context wholesale. Whole-object rather than partial, so a… (+2 more)

### Community 120 - "55. MVP Definition of Done"
Cohesion: 0.20
Nodes (10): 55. MVP Definition of Done, AI, Analytical, Evidence, Functional, Reliability, Reproducibility, Security (+2 more)

### Community 121 - "55. Anti-Patterns"
Cohesion: 0.29
Nodes (7): 55. Anti-Patterns, AI Black Box, Generic Chatbot, Notebook Clone, Old BI Dashboard, Spreadsheet Clone, Wizard

### Community 122 - "57. Measurement Sources"
Cohesion: 0.33
Nodes (6): 57. Measurement Sources, AI Evaluation Suite, Automated Tests, Golden Datasets, Performance Benchmarks, Usability Tests

### Community 123 - "54. Design System Principles"
Cohesion: 0.33
Nodes (6): 54. Design System Principles, Consistency, Density, Depth, Motion, Surface

### Community 124 - "31. Layout Principles"
Cohesion: 0.40
Nodes (5): 1. Strong hierarchy, 2. Generous spacing, 31. Layout Principles, 3. Visual grouping, 4. Stable orientation

### Community 125 - "50. MVP UX Scope"
Cohesion: 0.40
Nodes (5): 50. MVP UX Scope, P0, P1, P2, P3

### Community 126 - "9. Adaptive Workspace"
Cohesion: 0.40
Nodes (5): 9. Adaptive Workspace, Coding, Exploration, Finding creation, Validation

### Community 127 - "23. AI Interaction Model"
Cohesion: 0.50
Nodes (4): 23. AI Interaction Model, Level 1 — Suggestions, Level 2 — Assisted execution, Level 3 — Advanced agentic assistance

### Community 128 - "8. Main Workspace Layout"
Cohesion: 0.50
Nodes (4): 8. Main Workspace Layout, Center, Left, Right

### Community 129 - "runEda"
Cohesion: 0.67
Nodes (4): runEda(), EdaPanel(), submit(), typeOf()

### Community 130 - "5. Global Acceptance Thresholds"
Cohesion: 0.67
Nodes (3): 5. Global Acceptance Thresholds, AT-01 — Core Workflow Completion, Threshold

## Knowledge Gaps
- **381 isolated node(s):** `name`, `private`, `version`, `description`, `tauri` (+376 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 1075 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **52 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `TestClient`, `test_evaluator.py`, `test_case_history.py`, `test_python_runs.py`, `test_multi_dataset_runs.py`, `test_plans.py`, `test_charts_raster.py`, `main.py`, `test_drafting.py`, `test_conversation.py`, `test_multi_agent.py`, `test_validation.py`, `test_large_datasets.py`, `test_case_management.py`, `test_code_generation.py`, `test_cases.py`, `test_agent.py`, `test_profiles.py`, `get_db`, `test_export.py`, `test_runs.py`, `db.py`, `test_error_semantics.py`, `test_eda.py`, `test_memory.py`, `test_dataset_delete.py`, `test_datasets.py`, `test_python_hard_sandbox.py`, `client`, `verify_p3.py`, `test_interpretations.py`, `test_learn.py`, `verify_p1.py`, `verify_p2.py`, `test_evidence_graph.py`?**
  _High betweenness centrality (0.047) - this node is a cross-community bridge._
- **Why does `client()` connect `client` to `TestClient`, `test_evaluator.py`, `test_case_history.py`, `test_python_runs.py`, `test_multi_dataset_runs.py`, `test_plans.py`, `test_charts_raster.py`, `test_drafting.py`, `test_conversation.py`, `test_multi_agent.py`, `test_validation.py`, `test_large_datasets.py`, `test_case_management.py`, `test_code_generation.py`, `test_agent.py`, `test_profiles.py`, `get_db`, `test_export.py`, `test_runs.py`, `test_logging.py`, `test_error_semantics.py`, `test_eda.py`, `test_dataset_delete.py`, `test_datasets.py`, `test_python_hard_sandbox.py`, `test_interpretations.py`, `test_learn.py`, `test_evidence_graph.py`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Why does `evaluate()` connect `evaluator.py` to `_evaluate_evidence`, `test_evaluator.py`, `main.py`, `Evaluation`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **Are the 305 inferred relationships involving `TestClient` (e.g. with `test_a_case_with_no_usable_axis_ends_at_a_stated_reason()` and `test_a_closed_loop_proposes_nothing_further()`) actually correct?**
  _`TestClient` has 305 INFERRED edges - model-reasoned connections that need verification._
- **Are the 257 inferred relationships involving `client()` (e.g. with `test_a_case_with_no_usable_axis_ends_at_a_stated_reason()` and `test_a_closed_loop_proposes_nothing_further()`) actually correct?**
  _`client()` has 257 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _381 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._