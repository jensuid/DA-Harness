# Graph Report - DA-Harness  (2026-09-20)

## Corpus Check
- 105 files · ~114,052 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 2, .icns 1, .ico 1)

## Summary
- 1536 nodes · 3391 edges · 81 communities (74 shown, 3 thin omitted)
- Extraction: 85% EXTRACTED · 15% INFERRED · 0% AMBIGUOUS · INFERRED: 503 edges (avg confidence: 0.86)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4dca009c`
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
- datetime
- Implementation Roadmap
- _DatasetHandle
- package.json
- dah-server
- test_case_history.py
- Verification & Production Readiness Plan
- DEC-001: Web-first MVP, Tauri post-MVP
- client
- P1 Vertical Slice - Verification Report
- _require_dataset
- test_evidence_graph.py
- post
- validate_finding
- test_multi_dataset_runs.py
- test_plans.py
- test_charts_raster.py
- test_conversation.py
- test_drafting.py
- core_server.rs
- load_env_config
- _child_env
- generator.py
- get_chart_image
- exporter.py
- P2 MVP Milestone Verification
- test_validation.py
- DAH - Global Roadmap Status
- test_dataset_delete.py
- test_workflow.py
- test_large_datasets.py
- test_case_management.py
- test_code_generation.py
- test_cases.py
- main.py
- test_datasets.py
- test_supervisor.py
- python_exec.py
- test_python_hard_sandbox.py
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
- _require_case
- dah_core_main.py
- build_sidecar.sh
- dah-shell
- test_logging.py
- DAH — Data Analysis Harness
- test_interpretations.py
- test_error_semantics.py
- ValueError
- CaseWorkspace.tsx
- get_evidence_graph
- test_eda.py
- get_connection
- current_log_file
- Observability
- Template
- get
- _kill_group
- handle_unexpected_error

## God Nodes (most connected - your core abstractions)
1. `client()` - 174 edges
2. `get_connection()` - 99 edges
3. `get_db()` - 28 edges
4. `messageOf()` - 23 edges
5. `request()` - 20 edges
6. `Product & Engineering Master Specification` - 20 edges
7. `run_query()` - 19 edges
8. `render_chart()` - 19 edges
9. `compilerOptions` - 17 edges
10. `_temp_env()` - 16 edges

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

## Communities (81 total, 3 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.07
Nodes (43): BaseModel, Run one exploratory operation over an attached dataset (P3-ANALYSIS-005).…, run_exploratory_analysis(), CaseCreate, CaseFromTemplate, CaseHistory, CaseProgress, CaseUpdate (+35 more)

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
Cohesion: 0.28
Nodes (17): _promote(), Case template tests for P3-CASE-007. A template is the skeleton a new case…, A templated case starts clean: question and label only, no data., Deleting a promoted case leaves the template usable., _temp_db(), override(), test_case_from_template_allows_overrides(), test_case_from_template_keeps_skeleton() (+9 more)

### Community 6 - "analysis.py"
Cohesion: 0.10
Nodes (29): _bind_dataset(), _bind_datasets(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), _execute_read_only(), _is_read_only() (+21 more)

### Community 7 - "interpreter.py"
Cohesion: 0.17
Nodes (17): _column_stats(), _configured_llm(), create_interpretation(), _fmt(), interpret_result(), _is_number(), LLMInterpreter, Any (+9 more)

### Community 8 - "datetime"
Cohesion: 0.05
Nodes (45): datetime, build_case_history(), add(), _parse(), Any, Case history: a timeline of everything that happened in a case (P3-CASE-007).…, Project a case into its timeline. Raises ValueError when the case does not…, log() (+37 more)

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

### Community 18 - "client"
Cohesion: 0.46
Nodes (16): client(), _case_with_dataset(), _python(), _temp_env(), test_evidence_chain_works_for_python_run(), test_python_allows_safe_import(), test_python_rejects_blocked_import(), test_python_rejects_dunder_escape() (+8 more)

### Community 19 - "P1 Vertical Slice - Verification Report"
Cohesion: 0.33
Nodes (5): Decision, Evidence, Exit criteria (Coding-Agent Production System section 8), Exit-test sequence (the full user journey), P1 Vertical Slice - Verification Report

### Community 20 - "_require_dataset"
Cohesion: 0.10
Nodes (25): Dataset, GeneratedCode, Profile, attach_dataset(), create_plan(), create_run(), generate_code(), get_plan() (+17 more)

### Community 21 - "test_evidence_graph.py"
Cohesion: 0.37
Nodes (12): _full_case(), _graph(), Evidence graph tests for P3-EVIDENCE-006. The graph is a projection of the…, A claim anchored on nothing shows up as an orphan, not as a trace., _temp_env(), test_edges_describe_derivation(), test_graph_400_when_the_case_is_empty(), test_graph_404_for_unknown_case() (+4 more)

### Community 22 - "post"
Cohesion: 0.12
Nodes (24): Case, patch, post, create_case(), create_case_from_template(), duplicate_case(), get_case(), import_case_package() (+16 more)

### Community 23 - "validate_finding"
Cohesion: 0.13
Nodes (17): create_python_run(), Run user Python against an attached dataset and persist the result. The code…, Append the reproducibility check and report whether it passed., A canonical sort key for one result row. DuckDB does not promise a row order…, Rerun the stored SQL and compare it to the persisted rows. A multi-dataset run…, Re-execute the stored script and compare the whole tabulated result. Both…, Reproduce a finding's computation and check its support. The trust loop closes…, _record_repro() (+9 more)

### Community 24 - "test_multi_dataset_runs.py"
Cohesion: 0.34
Nodes (16): _case_with_datasets(), _multi_run(), Multi-dataset run tests for P3-DATA-003. Attaching several datasets per case…, The trust loop closes on a multi-dataset run too., The k-th placeholder binds to the k-th dataset, not to any file that fits., _temp_env(), test_dataset_ids_must_be_unique(), test_duplicate_copies_the_join_run() (+8 more)

### Community 25 - "test_plans.py"
Cohesion: 0.08
Nodes (35): _categorical_columns(), _column_names(), _configured_llm(), create_plan(), LLMPlanner, _null_columns(), _numeric_columns(), plan_analysis() (+27 more)

### Community 26 - "test_charts_raster.py"
Cohesion: 0.06
Nodes (53): ChartModel, _hex_rgb(), _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002). Turns a persisted…, A computed chart: geometry plus the data both renderers need. Everything…, Y-axis tick values from low to high. (+45 more)

### Community 27 - "test_conversation.py"
Cohesion: 0.07
Nodes (50): answer_question(), _artifact_grounds(), _configured_llm(), _counts(), create_answer(), _first_matching_column(), _fmt_stat(), _has_artifacts() (+42 more)

### Community 28 - "test_drafting.py"
Cohesion: 0.09
Nodes (39): _allowed_numbers(), _column_values(), _configured_llm(), create_draft(), draft_finding(), _fmt(), _is_number(), LLMDrafter (+31 more)

### Community 29 - "core_server.rs"
Cohesion: 0.05
Nodes (52): AppHandle, Box, Child, Command, core_starts_and_answers_health(), dev_core_override_ignores_a_present_sidecar(), dev_resolution_uses_the_project_virtualenv(), HEALTH_INTERVAL (+44 more)

### Community 30 - "load_env_config"
Cohesion: 0.31
Nodes (8): load_env_config(), Load a local .env into the process environment. Returns True when a file was…, Environment configuration loading (LLM key setup follow-up). The server loads…, No file, no change, no error., An exported variable is not clobbered by a value in the file., test_env_file_is_loaded(), test_missing_env_file_is_a_no_op(), test_real_environment_wins_over_file()

### Community 31 - "_child_env"
Cohesion: 0.25
Nodes (8): _child_env(), The macOS sandbox-exec profile for one run. Reads are unrestricted (the…, The minimal environment the worker inherits. The API process may carry…, _seatbelt_profile(), Secrets held by the API process never reach the worker., The profile production emits is enforced by the kernel, not by Python., test_child_env_scrubs_api_secrets(), test_seatbelt_profile_denies_writes_and_network()

### Community 32 - "generator.py"
Cohesion: 0.10
Nodes (35): _columns(), _columns_referenced(), _configured_llm(), create_code(), _explain(), generate_code(), _is_identifier(), LLMGenerator (+27 more)

### Community 33 - "get_chart_image"
Cohesion: 0.12
Nodes (17): FileResponse, RunSummary, _chart_media_type(), _dataset_ids_of(), delete_dataset(), _format_for(), get_chart_image(), list_runs() (+9 more)

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
Cohesion: 0.22
Nodes (8): Current position detail, DAH - Global Roadmap Status, P3 V1 — entry checklist (COMPLETE), P4 Production Candidate — entry checklist (COMPLETE), P5 Production Grade — entry checklist (4 of 5 done), Phase gate definitions (what "done" means), Phase status, Rules this file enforces

### Community 38 - "test_dataset_delete.py"
Cohesion: 0.23
Nodes (20): delete_case(), delete_template(), Remove a template. Cases created from it are unaffected (P3-CASE-007)., Delete a case and everything attached to it. Children are removed before the…, _case_with_datasets(), _dataset(), _delete(), Single-dataset deletion tests for P3-DATA-009. A case could already be deleted… (+12 more)

### Community 39 - "test_workflow.py"
Cohesion: 0.15
Nodes (19): case_progress(), _counts(), Any, Guided analysis workflow (P3-FLOW-004). The Master Specification's core loop is…, Whether the case has at least one artifact behind this stage., The case's position in the workflow and the action that moves it. `stage` is…, How much of each artifact the case has right now., _stage_state() (+11 more)

### Community 40 - "test_large_datasets.py"
Cohesion: 0.20
Nodes (18): _attach(), _generated_csv(), Large-dataset behaviour (P4-PERF-006). The 1000-row result cap had existed…, A full-table scan at scale is capped and flagged, never unbounded., An aggregation over the full set sees every row, not just the capped page., A table with many columns still reports one stat block per column. The…, The duplicate count is exact over a large set with known repeats., A case carrying a large dataset exports and restores intact. (+10 more)

### Community 41 - "test_case_management.py"
Cohesion: 0.28
Nodes (15): _counts(), _first_run(), _full_case(), A case with a dataset, profile, run, finding and chart attached., _temp_env(), override(), test_delete_does_not_touch_other_cases(), test_delete_is_idempotent_for_unknown_case() (+7 more)

### Community 42 - "test_code_generation.py"
Cohesion: 0.16
Nodes (21): _case_with_dataset(), _DeletingGenerator, _FailingGenerator, _GoodGenerator, _InventingGenerator, _MalformedGenerator, Code generation tests for P3-AI-013. Writing the analysis is the part of the…, _temp_env() (+13 more)

### Community 43 - "test_cases.py"
Cohesion: 0.21
Nodes (16): _client(), A `%` or `_` in the term is literal, not a LIKE wildcard., Absent or blank `q` is not a filter., The golden test: a case survives being saved and reopened., `q` matches the question, ignoring case (P3-CASE-007)., Point the app at a fresh on-disk SQLite file for this test., `q` also matches the dataset label., _temp_db() (+8 more)

### Community 44 - "main.py"
Cohesion: 0.11
Nodes (28): DraftFinding, Interpretation, Which failures are the input's fault (P4-RELIABILITY-002). Every engine the API…, _chart_row_to_summary(), create_chart(), create_interpretation(), draft_finding(), get_chart() (+20 more)

### Community 45 - "test_datasets.py"
Cohesion: 0.22
Nodes (20): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+12 more)

### Community 46 - "test_supervisor.py"
Cohesion: 0.16
Nodes (21): parent_pid(), pid_alive(), Parent-process supervision for the desktop shell. The Tauri shell is the only…, The pid the shell asked this core to outlive, or None if not supervised., Whether ``pid`` is currently a running process., Start a daemon thread that ends this process when the shell is gone. Returns…, start_parent_watchdog(), watch() (+13 more)

### Community 47 - "python_exec.py"
Cohesion: 0.10
Nodes (26): _alarm_handler(), _dataset_columns(), execute_user_code(), _failure(), _guarded_import(), _import_restrictions(), _ImportGuard, Exception (+18 more)

### Community 48 - "test_python_hard_sandbox.py"
Cohesion: 0.27
Nodes (11): _case_with_dataset(), _python(), Hard-sandbox tests for P3-SEC-001. The inner guards (import allowlist,…, An unbounded loop ends at the time limit and the API answers 400., A worker that dies on startup surfaces as a 400, never as an API crash., A rejected contract is a 400 with a message, not a dead process., _temp_env(), override() (+3 more)

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

### Community 61 - "_require_case"
Cohesion: 0.12
Nodes (23): ConversationTurn, Finding, chat_about_case(), create_finding(), create_multi_dataset_run(), get_finding(), get_run(), list_chat() (+15 more)

### Community 62 - "dah_core_main.py"
Cohesion: 0.67
Nodes (3): main(), parse_port(), Entrypoint for the `dah-core` sidecar (the packaged Python core). DAH's desktop…

### Community 66 - "test_logging.py"
Cohesion: 0.05
Nodes (53): fixture, _clear_handlers(), configure_logging(), Path, Where the core's output goes when nobody is watching it (P5-OBSERVE-002). The…, The older backups, newest first. Empty when file logging is off., The last ``lines`` records of ``path``, in the order they were written. Reads…, Where the log file belongs. An explicit argument wins (tests use it against a… (+45 more)

### Community 67 - "DAH — Data Analysis Harness"
Cohesion: 0.29
Nodes (6): Building the packaged app, DAH — Data Analysis Harness, Getting a build, Installing the app, Layers, When something goes wrong

### Community 68 - "test_interpretations.py"
Cohesion: 0.21
Nodes (16): _case_with_sql_run(), _FailingInterpreter, _GoodInterpreter, _MalformedInterpreter, Result interpretation tests for P3-AI-011. The loop could run, chart, validate…, _temp_env(), override(), test_404s_for_unknown_and_cross_case_runs() (+8 more)

### Community 69 - "test_error_semantics.py"
Cohesion: 0.14
Nodes (27): parametrize, _Boom, _case_with_dataset(), _case_with_profile(), _client(), Error semantics: an input error answers 400, a server fault answers 500…, A fault inside the harness is a server error, never the input's fault., Any failure still degrades to deterministic - and now leaves a trace. (+19 more)

### Community 70 - "ValueError"
Cohesion: 0.21
Nodes (19): Run a read-only SQL query against one attached file. The dataset path is bound…, run_query(), _column_types(), _columns_of(), _correlate(), _distribution(), _is_numeric(), _quote() (+11 more)

### Community 71 - "CaseWorkspace.tsx"
Cohesion: 0.07
Nodes (63): react, @testing-library/react, @testing-library/user-event, vitest, acceptFinding(), ApiError, attachDataset(), Case (+55 more)

### Community 72 - "get_evidence_graph"
Cohesion: 0.16
Nodes (13): build_evidence_graph(), _dataset_ids_of(), Any, Case-wide evidence graph and claim-to-source tracing (P3-EVIDENCE-006). The…, Every dataset a run bound, from its recorded list (P3-DATA-003)., Project a case into its evidence graph. Raises ValueError when the case has no…, get_evidence_graph(), node() (+5 more)

### Community 73 - "test_eda.py"
Cohesion: 0.39
Nodes (14): _dataset(), _eda(), EDA tests for P3-ANALYSIS-005. Every op compiles to read-only DuckDB and runs…, _temp_env(), override(), test_correlates_two_numeric_columns(), test_distribution_falls_back_to_top_values_for_a_category(), test_distribution_summarises_a_numeric_column() (+6 more)

### Community 74 - "get_connection"
Cohesion: 0.12
Nodes (17): Connection, _ensure_column(), get_connection(), Path, SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Add a column to an older schema; a no-op on current ones., Open a connection, ensuring the schema exists, and commit on success., override() (+9 more)

### Community 75 - "current_log_file"
Cohesion: 0.33
Nodes (6): current_log_file(), The log file `GET /logs` reads, or None when file logging is off., The tail of what the core has been doing. Read-only by construction - GET only,…, recent_logs(), LogView, The tail of the core's own log (P5-OBSERVE-002). Read-only: a support question…

### Community 77 - "Observability"
Cohesion: 0.29
Nodes (6): Finding the failure behind an error, Observability, Reading it, What is in it, What is not in it, Where the log lives

### Community 78 - "Template"
Cohesion: 0.33
Nodes (6): list_templates(), promote_template(), Promote a case into a reusable template (P3-CASE-007). The template keeps the…, List every saved template, newest first (P3-CASE-007)., A reusable case skeleton: the question and the dataset label. A template…, Template

### Community 79 - "get"
Cohesion: 0.12
Nodes (16): CaseProgress, get, export_case_package(), get_case_history(), get_case_progress(), get_evidence_chain(), health(), list_plans() (+8 more)

### Community 80 - "_kill_group"
Cohesion: 0.40
Nodes (5): _kill_group(), Popen, Kill the worker and anything it spawned (sandbox-exec sits in between)., A timeout kills the worker and anything it spawned, not just the shell., test_kill_group_terminates_the_tree()

### Community 81 - "handle_unexpected_error"
Cohesion: 0.22
Nodes (9): exception_handler, JSONResponse, middleware, Request, handle_unexpected_error(), log_request(), Exception, A fault in the harness answers 500 as JSON, with an id (P5-RELIABILITY-003).… (+1 more)

## Knowledge Gaps
- **151 isolated node(s):** `name`, `private`, `version`, `description`, `tauri` (+146 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 604 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `TestClient`, `datetime`, `test_case_history.py`, `client`, `test_evidence_graph.py`, `test_multi_dataset_runs.py`, `test_plans.py`, `test_charts_raster.py`, `test_conversation.py`, `test_drafting.py`, `test_validation.py`, `test_dataset_delete.py`, `test_workflow.py`, `test_large_datasets.py`, `test_case_management.py`, `test_code_generation.py`, `test_cases.py`, `main.py`, `test_datasets.py`, `test_python_hard_sandbox.py`, `test_profiles.py`, `get_db`, `test_export.py`, `test_runs.py`, `test_interpretations.py`, `test_error_semantics.py`, `test_eda.py`?**
  _High betweenness centrality (0.045) - this node is a cross-community bridge._
- **Why does `client()` connect `client` to `TestClient`, `test_case_history.py`, `test_evidence_graph.py`, `test_multi_dataset_runs.py`, `test_plans.py`, `test_charts_raster.py`, `test_conversation.py`, `test_drafting.py`, `test_validation.py`, `test_dataset_delete.py`, `test_workflow.py`, `test_large_datasets.py`, `test_case_management.py`, `test_code_generation.py`, `test_datasets.py`, `test_python_hard_sandbox.py`, `test_profiles.py`, `get_db`, `test_export.py`, `test_runs.py`, `test_logging.py`, `test_interpretations.py`, `test_error_semantics.py`, `test_eda.py`?**
  _High betweenness centrality (0.028) - this node is a cross-community bridge._
- **Why does `render_chart()` connect `test_charts_raster.py` to `main.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **Are the 197 inferred relationships involving `TestClient` (e.g. with `test_events_carry_their_own_artifact_ids_and_details()` and `test_finding_event_carries_validation_status()`) actually correct?**
  _`TestClient` has 197 INFERRED edges - model-reasoned connections that need verification._
- **Are the 171 inferred relationships involving `client()` (e.g. with `test_events_carry_their_own_artifact_ids_and_details()` and `test_finding_event_carries_validation_status()`) actually correct?**
  _`client()` has 171 INFERRED edges - model-reasoned connections that need verification._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _151 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._