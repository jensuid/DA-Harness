# Graph Report - DA-Harness  (2026-09-19)

## Corpus Check
- 79 files · ~58,721 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 2, .icns 1, .ico 1)

## Summary
- 974 nodes · 1845 edges · 66 communities (60 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 90 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `a3424f1e`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Product & Engineering Master Specification
- models.py
- web/package.json
- compilerOptions
- Coding-Agent Production System
- test_case_templates.py
- analysis.py
- test_datasets.py
- verify_p0.py
- Implementation Roadmap
- _DatasetHandle
- package.json
- dah-server
- test_case_history.py
- Verification & Production Readiness Plan
- DEC-001: Web-first MVP, Tauri post-MVP
- test_python_runs.py
- P1 Vertical Slice - Verification Report
- post
- test_evidence_graph.py
- Case
- main.py
- test_multi_dataset_runs.py
- planner.py
- test_charts_raster.py
- test_plans.py
- exporter.py
- core_server.rs
- load_env_config
- test_eda.py
- build_evidence_graph
- attach_dataset
- test_python_hard_sandbox.py
- P2 MVP Milestone Verification
- Template
- DAH - Global Roadmap Status
- delete_case
- test_workflow.py
- get
- test_case_management.py
- test_profiles.py
- datetime
- db.py
- test_cases.py
- test_supervisor.py
- python_exec.py
- python_worker.py
- get_connection
- LLM Configuration
- test_export.py
- test_runs.py
- test_findings.py
- run_query
- list_plans
- tauri.conf.json
- scripts
- DAH desktop shell
- run_query_multi
- default.json
- verify_p2.py
- dah_core_main.py
- build_sidecar.sh
- dah-shell

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 69 edges
2. `get_db()` - 21 edges
3. `Product & Engineering Master Specification` - 20 edges
4. `run_query()` - 19 edges
5. `render_chart()` - 19 edges
6. `compilerOptions` - 17 edges
7. `_temp_env()` - 15 edges
8. `Implementation Roadmap` - 15 edges
9. `Coding-Agent Production System` - 14 edges
10. `profile_csv()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p1/verify_p1.py → server/app/db.py
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p2/verify_p2.py → server/app/db.py
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P0 Foundation`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P3 V1`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `P2 MVP` --references--> `Analysis Planner`  [INFERRED]
  docs/Implementation Roadmap.md → docs/Product & Engineering Master Specification.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **P0 Verification System: gate + state + report** — verification_p0_report, ai_current_state, ai_tasks, ai_handoff [INFERRED 0.90]

## Communities (66 total, 3 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.09
Nodes (36): BaseModel, get_evidence_graph(), node(), Every claim in the case and what it rests on (P3-EVIDENCE-006). The graph is…, CaseCreate, CaseFromTemplate, CaseProgress, CaseUpdate (+28 more)

### Community 2 - "web/package.json"
Cohesion: 0.05
Nodes (40): jsdom, react, react-dom, @testing-library/react, @types/react, @types/react-dom, typescript, vite (+32 more)

### Community 3 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Coding-Agent Production System"
Cohesion: 0.14
Nodes (12): Coding-Agent Production System, Agent Implementation Protocol, Artifact Authority Hierarchy, Agent Control Loop: PLAN to EXIT-CRITERIA, Development Context Protocol, Development State Model, Hard Stop Conditions, Persistent Project State (/ai documents) (+4 more)

### Community 5 - "test_case_templates.py"
Cohesion: 0.27
Nodes (15): _promote(), Case template tests for P3-CASE-007. A template is the skeleton a new case…, A templated case starts clean: question and label only, no data., Deleting a promoted case leaves the template usable., _temp_db(), test_case_from_template_allows_overrides(), test_case_from_template_keeps_skeleton(), test_case_from_unknown_template_is_404() (+7 more)

### Community 6 - "analysis.py"
Cohesion: 0.13
Nodes (21): _bind_dataset(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), profile_csv(), DuckDB analytical engine - the seed of the Data & Evidence Engine. Analytical…, Collapse a DuckDB type name into numeric / temporal / other. (+13 more)

### Community 7 - "test_datasets.py"
Cohesion: 0.22
Nodes (20): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+12 more)

### Community 8 - "verify_p0.py"
Cohesion: 0.36
Nodes (9): log(), main(), Path, Popen, P0 Foundation milestone verification. Runs the P0 exit-test sequence as one…, request(), run_tests(), start_server() (+1 more)

### Community 9 - "Implementation Roadmap"
Cohesion: 0.29
Nodes (15): Milestone Exit Criteria (P0-P5), Implementation Roadmap, Feature Priority Model (M/S/C/L), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate (+7 more)

### Community 10 - "_DatasetHandle"
Cohesion: 0.15
Nodes (7): _DatasetHandle, _DatasetQuery, Any, A bound, dunder-hardened callable that runs read-only SQL on the file.…, The read-only view of an attached dataset that user code receives., The attached file as a list of row dicts, under the standard row cap., _rows_as_dicts()

### Community 11 - "package.json"
Cohesion: 0.40
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

### Community 20 - "post"
Cohesion: 0.11
Nodes (25): post, create_multi_dataset_run(), create_plan(), create_python_run(), create_run(), get_plan(), get_profile(), import_case_package() (+17 more)

### Community 21 - "test_evidence_graph.py"
Cohesion: 0.33
Nodes (13): _full_case(), _graph(), Evidence graph tests for P3-EVIDENCE-006. The graph is a projection of the…, A claim anchored on nothing shows up as an orphan, not as a trace., _temp_env(), override(), test_edges_describe_derivation(), test_graph_400_when_the_case_is_empty() (+5 more)

### Community 22 - "Case"
Cohesion: 0.12
Nodes (18): patch, create_case(), create_case_from_template(), get_case(), _insert_case(), _like_pattern(), list_cases(), Persist a fresh case row and return it (P3-CASE-007). Shared by direct creation… (+10 more)

### Community 23 - "main.py"
Cohesion: 0.21
Nodes (12): _chart_row_to_summary(), create_chart(), get_chart(), list_charts(), Render a chart from a persisted run result and store it with the case. The…, List the charts rendered from one run, without the image bytes., Retrieve a chart's metadata., _require_chart() (+4 more)

### Community 24 - "test_multi_dataset_runs.py"
Cohesion: 0.31
Nodes (17): _case_with_datasets(), _multi_run(), Multi-dataset run tests for P3-DATA-003. Attaching several datasets per case…, The trust loop closes on a multi-dataset run too., The k-th placeholder binds to the k-th dataset, not to any file that fits., _temp_env(), override(), test_dataset_ids_must_be_unique() (+9 more)

### Community 25 - "planner.py"
Cohesion: 0.13
Nodes (20): _categorical_columns(), _column_names(), _configured_llm(), create_plan(), LLMPlanner, _null_columns(), _numeric_columns(), plan_analysis() (+12 more)

### Community 26 - "test_charts_raster.py"
Cohesion: 0.06
Nodes (53): ChartModel, _hex_rgb(), _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002). Turns a persisted…, A computed chart: geometry plus the data both renderers need. Everything…, Y-axis tick values from low to high. (+45 more)

### Community 27 - "test_plans.py"
Cohesion: 0.22
Nodes (15): _case_with_profile(), _FailingLLM, _GoodLLM, _MalformedLLM, _temp_env(), override(), test_list_plans_newest_first(), test_llm_failure_falls_back_to_deterministic() (+7 more)

### Community 28 - "exporter.py"
Cohesion: 0.18
Nodes (17): _chart_format(), _dataset_ids_of(), export_case(), _import_dataset_ids(), import_package(), PackageError, Path, Self-contained Analysis Case packages (P2-CASE-012). Export assembles… (+9 more)

### Community 29 - "core_server.rs"
Cohesion: 0.08
Nodes (37): AppHandle, Box, Child, Command, core_starts_and_answers_health(), dev_core_override_ignores_a_present_sidecar(), dev_resolution_uses_the_project_virtualenv(), HEALTH_INTERVAL (+29 more)

### Community 30 - "load_env_config"
Cohesion: 0.31
Nodes (8): load_env_config(), Load a local .env into the process environment. Returns True when a file was…, Environment configuration loading (LLM key setup follow-up). The server loads…, No file, no change, no error., An exported variable is not clobbered by a value in the file., test_env_file_is_loaded(), test_missing_env_file_is_a_no_op(), test_real_environment_wins_over_file()

### Community 31 - "test_eda.py"
Cohesion: 0.39
Nodes (14): _dataset(), _eda(), EDA tests for P3-ANALYSIS-005. Every op compiles to read-only DuckDB and runs…, _temp_env(), override(), test_correlates_two_numeric_columns(), test_distribution_falls_back_to_top_values_for_a_category(), test_distribution_summarises_a_numeric_column() (+6 more)

### Community 32 - "build_evidence_graph"
Cohesion: 0.33
Nodes (6): build_evidence_graph(), _dataset_ids_of(), Any, Case-wide evidence graph and claim-to-source tracing (P3-EVIDENCE-006). The…, Every dataset a run bound, from its recorded list (P3-DATA-003)., Project a case into its evidence graph. Raises ValueError when the case has no…

### Community 33 - "attach_dataset"
Cohesion: 0.13
Nodes (16): FileResponse, attach_dataset(), _chart_media_type(), duplicate_case(), _format_for(), get_chart_image(), Path, Serve the persisted chart image itself. (+8 more)

### Community 34 - "test_python_hard_sandbox.py"
Cohesion: 0.09
Nodes (28): _child_env(), _failure(), _kill_group(), Popen, The macOS sandbox-exec profile for one run. Reads are unrestricted (the…, The minimal environment the worker inherits. The API process may carry…, Kill the worker and anything it spawned (sandbox-exec sits in between)., Execute user Python in a separate, OS-sandboxed process and tabulate it. Raises… (+20 more)

### Community 35 - "P2 MVP Milestone Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,, Journey under test, P2 MVP Milestone Verification, Steps

### Community 36 - "Template"
Cohesion: 0.33
Nodes (6): list_templates(), promote_template(), Promote a case into a reusable template (P3-CASE-007). The template keeps the…, List every saved template, newest first (P3-CASE-007)., A reusable case skeleton: the question and the dataset label. A template…, Template

### Community 37 - "DAH - Global Roadmap Status"
Cohesion: 0.29
Nodes (6): Current position detail, DAH - Global Roadmap Status, P3 V1 — entry checklist (next work, nothing started), Phase gate definitions (what "done" means), Phase status, Rules this file enforces

### Community 38 - "delete_case"
Cohesion: 0.40
Nodes (5): delete, delete_case(), delete_template(), Remove a template. Cases created from it are unaffected (P3-CASE-007)., Delete a case and everything attached to it. Children are removed before the…

### Community 39 - "test_workflow.py"
Cohesion: 0.15
Nodes (19): case_progress(), _counts(), Any, Guided analysis workflow (P3-FLOW-004). The Master Specification's core loop is…, Whether the case has at least one artifact behind this stage., The case's position in the workflow and the action that moves it. `stage` is…, How much of each artifact the case has right now., _stage_state() (+11 more)

### Community 40 - "get"
Cohesion: 0.09
Nodes (31): get, create_finding(), _dataset_ids_of(), export_case_package(), get_case_progress(), get_evidence_chain(), get_finding(), get_run() (+23 more)

### Community 41 - "test_case_management.py"
Cohesion: 0.28
Nodes (15): _counts(), _first_run(), _full_case(), A case with a dataset, profile, run, finding and chart attached., _temp_env(), override(), test_delete_does_not_touch_other_cases(), test_delete_is_idempotent_for_unknown_case() (+7 more)

### Community 42 - "test_profiles.py"
Cohesion: 0.53
Nodes (8): _attach(), _temp_env(), test_deep_profile_stats(), test_deep_profile_survives_reopen(), test_get_profile_before_profiling_returns_404(), test_header_only_dataset_profiles_cleanly(), test_profile_and_reopen(), test_profile_unknown_dataset_returns_404()

### Community 43 - "datetime"
Cohesion: 0.20
Nodes (11): datetime, build_case_history(), add(), _parse(), Any, Case history: a timeline of everything that happened in a case (P3-CASE-007).…, Project a case into its timeline. Raises ValueError when the case does not…, get_case_history() (+3 more)

### Community 44 - "db.py"
Cohesion: 0.24
Nodes (8): _ensure_column(), SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Add a column to an older schema; a no-op on current ones., log(), main(), override(), record(), P1 Vertical Slice milestone verification. Runs the full user journey as one…

### Community 45 - "test_cases.py"
Cohesion: 0.21
Nodes (16): _client(), A `%` or `_` in the term is literal, not a LIKE wildcard., Absent or blank `q` is not a filter., The golden test: a case survives being saved and reopened., `q` matches the question, ignoring case (P3-CASE-007)., Point the app at a fresh on-disk SQLite file for this test., `q` also matches the dataset label., _temp_db() (+8 more)

### Community 46 - "test_supervisor.py"
Cohesion: 0.16
Nodes (21): parent_pid(), pid_alive(), Parent-process supervision for the desktop shell. The Tauri shell is the only…, The pid the shell asked this core to outlive, or None if not supervised., Whether ``pid`` is currently a running process., Start a daemon thread that ends this process when the shell is gone. Returns…, start_parent_watchdog(), watch() (+13 more)

### Community 47 - "python_exec.py"
Cohesion: 0.13
Nodes (20): Exception, _alarm_handler(), _dataset_columns(), execute_user_code(), _guarded_import(), _import_restrictions(), _ImportGuard, Restricted Python execution engine for the Analysis Workspace. The Python… (+12 more)

### Community 48 - "python_worker.py"
Cohesion: 0.60
Nodes (4): _emit(), main(), In-sandbox entrypoint for analysis Python runs (P3-SEC-001). This module is…, _run()

### Community 49 - "get_connection"
Cohesion: 0.18
Nodes (16): Connection, get_connection(), Path, Open a connection, ensuring the schema exists, and commit on success., get_db(), override(), override(), override() (+8 more)

### Community 50 - "LLM Configuration"
Cohesion: 0.22
Nodes (8): 1. Create the file, 2. Start the server, 3. Check it took effect, Alternative: set the variables inline, LLM Configuration, Notes, Setup with a `.env` file (recommended), Variables

### Community 51 - "test_export.py"
Cohesion: 0.44
Nodes (8): _full_case(), _temp_env(), override(), test_export_contains_every_section(), test_export_unknown_case_returns_404(), test_import_rejects_bad_package(), test_round_trip_relinks_references_and_serves_artifacts(), test_round_trip_restores_the_case()

### Community 52 - "test_runs.py"
Cohesion: 0.47
Nodes (8): _case_with_dataset(), _temp_env(), override(), test_list_runs_excludes_rows(), test_rejects_multi_statement(), test_rejects_write_query(), test_run_aggregation_and_reopen(), test_run_unknown_dataset_returns_404()

### Community 53 - "test_findings.py"
Cohesion: 0.50
Nodes (7): _case_with_run(), _temp_env(), override(), test_create_finding_and_trace_evidence(), test_finding_unknown_run_returns_404(), test_findings_survive_reopen(), test_set_validation_status()

### Community 54 - "run_query"
Cohesion: 0.21
Nodes (19): Run a read-only SQL query against one attached file. The dataset path is bound…, run_query(), _column_types(), _columns_of(), _correlate(), _distribution(), _is_numeric(), _quote() (+11 more)

### Community 55 - "list_plans"
Cohesion: 0.50
Nodes (4): list_plans(), Every plan recorded for a case's dataset, newest first., PlanSummary, Plan metadata without the plan body.

### Community 56 - "tauri.conf.json"
Cohesion: 0.11
Nodes (17): app, security, windows, build, beforeBuildCommand, beforeDevCommand, frontendDist, bundle (+9 more)

### Community 57 - "scripts"
Cohesion: 0.12
Nodes (15): description, devDependencies, @tauri-apps/cli, name, private, scripts, build, dev (+7 more)

### Community 58 - "DAH desktop shell"
Cohesion: 0.25
Nodes (7): DAH desktop shell, How the core is started, Known limits, Layout, Running it, Tests, Why no remote-URL capability

### Community 59 - "run_query_multi"
Cohesion: 0.25
Nodes (8): _bind_datasets(), _execute_read_only(), _is_read_only(), Bind the k-th dataset placeholder in user SQL to the k-th file. The natural…, Run an already-bound read-only query and cap its result., Run a read-only SQL query across several attached files (P3-DATA-003).…, Reject anything that is not a single read-only statement., run_query_multi()

### Community 60 - "default.json"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 61 - "verify_p2.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P2 MVP milestone verification. Runs the full P2 user journey as one atomic…

### Community 62 - "dah_core_main.py"
Cohesion: 0.67
Nodes (3): main(), parse_port(), Entrypoint for the `dah-core` sidecar (the packaged Python core). DAH's desktop…

## Knowledge Gaps
- **120 isolated node(s):** `name`, `private`, `version`, `description`, `tauri` (+115 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 387 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `test_case_templates.py`, `test_datasets.py`, `test_case_history.py`, `test_python_runs.py`, `test_evidence_graph.py`, `main.py`, `test_multi_dataset_runs.py`, `test_charts_raster.py`, `test_plans.py`, `test_eda.py`, `test_python_hard_sandbox.py`, `test_workflow.py`, `test_case_management.py`, `test_profiles.py`, `db.py`, `test_cases.py`, `test_export.py`, `test_runs.py`, `test_findings.py`, `verify_p2.py`?**
  _High betweenness centrality (0.088) - this node is a cross-community bridge._
- **Why does `run_query()` connect `run_query` to `analysis.py`, `get`, `_DatasetHandle`, `python_exec.py`, `post`, `main.py`, `run_query_multi`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `start_parent_watchdog()` connect `test_supervisor.py` to `main.py`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _120 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `models.py` be split into smaller, more focused modules?**
  _Cohesion score 0.08558558558558559 - nodes in this community are weakly interconnected._
- **Should `web/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05365402405180388 - nodes in this community are weakly interconnected._