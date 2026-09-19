# Graph Report - DA-Harness  (2026-09-19)

## Corpus Check
- 80 files · ~61,446 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 7 file(s) not represented in the graph (top: (none) 2, .icns 1, .ico 1)

## Summary
- 1010 nodes · 1939 edges · 60 communities (54 shown, 3 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 91 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `e8a727a0`
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
- datetime
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
- test_plans.py
- test_charts_raster.py
- run_python
- exporter.py
- core_server.rs
- load_env_config
- test_eda.py
- build_evidence_graph
- attach_dataset
- run_query
- P2 MVP Milestone Verification
- test_validation.py
- DAH - Global Roadmap Status
- test_dataset_delete.py
- test_workflow.py
- get
- test_case_management.py
- validate_finding
- get_case_history
- Template
- get_connection
- test_supervisor.py
- python_exec.py
- python_worker.py
- get_case_progress
- LLM Configuration
- list_plans
- tauri.conf.json
- scripts
- DAH desktop shell
- default.json
- dah_core_main.py
- build_sidecar.sh
- dah-shell

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 74 edges
2. `get_db()` - 22 edges
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

## Communities (60 total, 3 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.09
Nodes (34): BaseModel, get_evidence_graph(), node(), Every claim in the case and what it rests on (P3-EVIDENCE-006). The graph is…, CaseCreate, CaseFromTemplate, CaseUpdate, ChartCreate (+26 more)

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
Cohesion: 0.24
Nodes (16): _promote(), Case template tests for P3-CASE-007. A template is the skeleton a new case…, A templated case starts clean: question and label only, no data., Deleting a promoted case leaves the template usable., _temp_db(), override(), test_case_from_template_allows_overrides(), test_case_from_template_keeps_skeleton() (+8 more)

### Community 6 - "analysis.py"
Cohesion: 0.10
Nodes (29): _bind_dataset(), _bind_datasets(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), _execute_read_only(), _is_read_only() (+21 more)

### Community 7 - "test_datasets.py"
Cohesion: 0.24
Nodes (19): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+11 more)

### Community 8 - "datetime"
Cohesion: 0.10
Nodes (26): datetime, build_case_history(), add(), _parse(), Any, Case history: a timeline of everything that happened in a case (P3-CASE-007).…, Project a case into its timeline. Raises ValueError when the case does not…, log() (+18 more)

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
Cohesion: 0.42
Nodes (15): _case_with_dataset(), _python(), _temp_env(), test_evidence_chain_works_for_python_run(), test_python_allows_safe_import(), test_python_rejects_blocked_import(), test_python_rejects_dunder_escape(), test_python_rejects_empty_code() (+7 more)

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
Cohesion: 0.15
Nodes (15): create_case(), create_case_from_template(), get_case(), _insert_case(), _like_pattern(), list_cases(), Persist a fresh case row and return it (P3-CASE-007). Shared by direct creation…, Create and persist a new Analysis Case. (+7 more)

### Community 23 - "main.py"
Cohesion: 0.21
Nodes (12): _chart_row_to_summary(), create_chart(), get_chart(), list_charts(), Render a chart from a persisted run result and store it with the case. The…, List the charts rendered from one run, without the image bytes., Retrieve a chart's metadata., _require_chart() (+4 more)

### Community 24 - "test_multi_dataset_runs.py"
Cohesion: 0.34
Nodes (16): _case_with_datasets(), _multi_run(), Multi-dataset run tests for P3-DATA-003. Attaching several datasets per case…, The trust loop closes on a multi-dataset run too., The k-th placeholder binds to the k-th dataset, not to any file that fits., _temp_env(), test_dataset_ids_must_be_unique(), test_duplicate_copies_the_join_run() (+8 more)

### Community 25 - "test_plans.py"
Cohesion: 0.08
Nodes (35): _categorical_columns(), _column_names(), _configured_llm(), create_plan(), LLMPlanner, _null_columns(), _numeric_columns(), plan_analysis() (+27 more)

### Community 26 - "test_charts_raster.py"
Cohesion: 0.06
Nodes (53): ChartModel, _hex_rgb(), _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002). Turns a persisted…, A computed chart: geometry plus the data both renderers need. Everything…, Y-axis tick values from low to high. (+45 more)

### Community 27 - "run_python"
Cohesion: 0.12
Nodes (17): _child_env(), _failure(), _kill_group(), Popen, The macOS sandbox-exec profile for one run. Reads are unrestricted (the…, The minimal environment the worker inherits. The API process may carry…, Kill the worker and anything it spawned (sandbox-exec sits in between)., Execute user Python in a separate, OS-sandboxed process and tabulate it. Raises… (+9 more)

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
Cohesion: 0.44
Nodes (13): _dataset(), _eda(), EDA tests for P3-ANALYSIS-005. Every op compiles to read-only DuckDB and runs…, _temp_env(), test_correlates_two_numeric_columns(), test_distribution_falls_back_to_top_values_for_a_category(), test_distribution_summarises_a_numeric_column(), test_eda_404_for_unknown_dataset() (+5 more)

### Community 32 - "build_evidence_graph"
Cohesion: 0.33
Nodes (6): build_evidence_graph(), _dataset_ids_of(), Any, Case-wide evidence graph and claim-to-source tracing (P3-EVIDENCE-006). The…, Every dataset a run bound, from its recorded list (P3-DATA-003)., Project a case into its evidence graph. Raises ValueError when the case has no…

### Community 33 - "attach_dataset"
Cohesion: 0.11
Nodes (20): FileResponse, attach_dataset(), _chart_media_type(), delete_dataset(), duplicate_case(), _format_for(), get_chart_image(), Path (+12 more)

### Community 34 - "run_query"
Cohesion: 0.21
Nodes (19): Run a read-only SQL query against one attached file. The dataset path is bound…, run_query(), _column_types(), _columns_of(), _correlate(), _distribution(), _is_numeric(), _quote() (+11 more)

### Community 35 - "P2 MVP Milestone Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,, Journey under test, P2 MVP Milestone Verification, Steps

### Community 36 - "test_validation.py"
Cohesion: 0.22
Nodes (17): _full_setup(), _python_setup(), The core guarantee: if the persisted result no longer matches a rerun,…, Case + dataset + profile + Python run + finding., A changed result shape shows up as a column change even when values line up., A script that no longer runs is a verdict, never a 500., Case + dataset + profile + run + finding. Returns case and finding ids., _tamper() (+9 more)

### Community 37 - "DAH - Global Roadmap Status"
Cohesion: 0.29
Nodes (6): Current position detail, DAH - Global Roadmap Status, P3 V1 — entry checklist (next work, nothing started), Phase gate definitions (what "done" means), Phase status, Rules this file enforces

### Community 38 - "test_dataset_delete.py"
Cohesion: 0.23
Nodes (20): delete_case(), delete_template(), Remove a template. Cases created from it are unaffected (P3-CASE-007)., Delete a case and everything attached to it. Children are removed before the…, _case_with_datasets(), _dataset(), _delete(), Single-dataset deletion tests for P3-DATA-009. A case could already be deleted… (+12 more)

### Community 39 - "test_workflow.py"
Cohesion: 0.15
Nodes (19): case_progress(), _counts(), Any, Guided analysis workflow (P3-FLOW-004). The Master Specification's core loop is…, Whether the case has at least one artifact behind this stage., The case's position in the workflow and the action that moves it. `stage` is…, How much of each artifact the case has right now., _stage_state() (+11 more)

### Community 40 - "get"
Cohesion: 0.10
Nodes (27): get, patch, create_finding(), _dataset_ids_of(), export_case_package(), get_evidence_chain(), get_finding(), get_run() (+19 more)

### Community 41 - "test_case_management.py"
Cohesion: 0.28
Nodes (15): _counts(), _first_run(), _full_case(), A case with a dataset, profile, run, finding and chart attached., _temp_env(), override(), test_delete_does_not_touch_other_cases(), test_delete_is_idempotent_for_unknown_case() (+7 more)

### Community 42 - "validate_finding"
Cohesion: 0.22
Nodes (11): Append the reproducibility check and report whether it passed., Rerun the stored SQL and compare it to the persisted rows. A multi-dataset run…, Re-execute the stored script and compare the whole tabulated result. Both…, Reproduce a finding's computation and check its support. The trust loop closes…, _record_repro(), _reproduce_python(), _reproduce_sql(), validate_finding() (+3 more)

### Community 43 - "get_case_history"
Cohesion: 0.50
Nodes (4): get_case_history(), Everything that happened in a case, in order (P3-CASE-007). A read-side…, CaseHistory, Everything that happened in a case, in the order it happened. A read-side…

### Community 44 - "Template"
Cohesion: 0.33
Nodes (6): list_templates(), promote_template(), Promote a case into a reusable template (P3-CASE-007). The template keeps the…, List every saved template, newest first (P3-CASE-007)., A reusable case skeleton: the question and the dataset label. A template…, Template

### Community 45 - "get_connection"
Cohesion: 0.05
Nodes (73): Connection, _ensure_column(), get_connection(), Path, SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Add a column to an older schema; a no-op on current ones., Open a connection, ensuring the schema exists, and commit on success., get_db() (+65 more)

### Community 46 - "test_supervisor.py"
Cohesion: 0.16
Nodes (21): parent_pid(), pid_alive(), Parent-process supervision for the desktop shell. The Tauri shell is the only…, The pid the shell asked this core to outlive, or None if not supervised., Whether ``pid`` is currently a running process., Start a daemon thread that ends this process when the shell is gone. Returns…, start_parent_watchdog(), watch() (+13 more)

### Community 47 - "python_exec.py"
Cohesion: 0.13
Nodes (20): Exception, _alarm_handler(), _dataset_columns(), execute_user_code(), _guarded_import(), _import_restrictions(), _ImportGuard, Restricted Python execution engine for the Analysis Workspace. The Python… (+12 more)

### Community 48 - "python_worker.py"
Cohesion: 0.60
Nodes (4): _emit(), main(), In-sandbox entrypoint for analysis Python runs (P3-SEC-001). This module is…, _run()

### Community 49 - "get_case_progress"
Cohesion: 0.50
Nodes (4): get_case_progress(), Where this case stands in the guided workflow (P3-FLOW-004). The stage is…, CaseProgress, Where a case sits in the guided workflow (P3-FLOW-004). The stage is derived…

### Community 50 - "LLM Configuration"
Cohesion: 0.22
Nodes (8): 1. Create the file, 2. Start the server, 3. Check it took effect, Alternative: set the variables inline, LLM Configuration, Notes, Setup with a `.env` file (recommended), Variables

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

### Community 60 - "default.json"
Cohesion: 0.33
Nodes (5): description, identifier, permissions, $schema, windows

### Community 62 - "dah_core_main.py"
Cohesion: 0.67
Nodes (3): main(), parse_port(), Entrypoint for the `dah-core` sidecar (the packaged Python core). DAH's desktop…

## Knowledge Gaps
- **120 isolated node(s):** `name`, `private`, `version`, `description`, `tauri` (+115 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 399 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `test_validation.py`, `test_case_templates.py`, `test_dataset_delete.py`, `test_datasets.py`, `test_workflow.py`, `test_case_management.py`, `datetime`, `test_case_history.py`, `test_python_runs.py`, `test_evidence_graph.py`, `main.py`, `test_multi_dataset_runs.py`, `test_plans.py`, `test_charts_raster.py`, `test_eda.py`?**
  _High betweenness centrality (0.074) - this node is a cross-community bridge._
- **Why does `profile_csv()` connect `analysis.py` to `post`, `main.py`?**
  _High betweenness centrality (0.016) - this node is a cross-community bridge._
- **Why does `start_parent_watchdog()` connect `test_supervisor.py` to `main.py`?**
  _High betweenness centrality (0.014) - this node is a cross-community bridge._
- **What connects `name`, `private`, `version` to the rest of the system?**
  _120 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `models.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0907563025210084 - nodes in this community are weakly interconnected._
- **Should `web/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05365402405180388 - nodes in this community are weakly interconnected._