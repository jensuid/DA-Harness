# Graph Report - DA-Harness  (2026-09-19)

## Corpus Check
- 58 files · ~43,047 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .css 1, .tsbuildinfo 1)

## Summary
- 685 nodes · 1312 edges · 44 communities (40 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 67 edges (avg confidence: 0.89)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `f5df5d18`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Product & Engineering Master Specification
- models.py
- web/package.json
- compilerOptions
- Coding-Agent Production System
- get_connection
- analysis.py
- test_datasets.py
- verify_p0.py
- Implementation Roadmap
- python_exec.py
- package.json
- dah-server
- _kill_group
- Verification & Production Readiness Plan
- DEC-001: Web-first MVP, Tauri post-MVP
- test_python_runs.py
- P1 Vertical Slice - Verification Report
- _require_dataset
- test_charts.py
- _require_case
- main.py
- test_multi_dataset_runs.py
- planner.py
- test_charts_raster.py
- test_plans.py
- exporter.py
- get
- attach_dataset
- post
- delete_case
- run_query
- run_python
- P2 MVP Milestone Verification
- ValueError
- DAH - Global Roadmap Status
- _DatasetHandle
- test_workflow.py
- validate_finding
- test_case_management.py
- test_profiles.py
- _ImportGuard

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 55 edges
2. `Product & Engineering Master Specification` - 20 edges
3. `render_chart()` - 19 edges
4. `get_db()` - 17 edges
5. `compilerOptions` - 17 edges
6. `_temp_env()` - 15 edges
7. `Implementation Roadmap` - 15 edges
8. `Coding-Agent Production System` - 14 edges
9. `profile_csv()` - 13 edges
10. `run_query()` - 13 edges

## Surprising Connections (you probably didn't know these)
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P0 Foundation`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P3 V1`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p1/verify_p1.py → server/app/db.py
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p2/verify_p2.py → server/app/db.py
- `P2 MVP` --references--> `Analysis Planner`  [INFERRED]
  docs/Implementation Roadmap.md → docs/Product & Engineering Master Specification.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **P0 Verification System: gate + state + report** — verification_p0_report, ai_current_state, ai_tasks, ai_handoff [INFERRED 0.90]

## Communities (44 total, 2 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.15
Nodes (19): BaseModel, CaseCreate, CaseProgress, CaseUpdate, ChartCreate, FindingCreate, MultiRunCreate, PlanSummary (+11 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (38): jsdom, react, react-dom, @testing-library/react, @types/react, @types/react-dom, typescript, vite (+30 more)

### Community 3 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Coding-Agent Production System"
Cohesion: 0.14
Nodes (12): Coding-Agent Production System, Agent Implementation Protocol, Artifact Authority Hierarchy, Agent Control Loop: PLAN to EXIT-CRITERIA, Development Context Protocol, Development State Model, Hard Stop Conditions, Persistent Project State (/ai documents) (+4 more)

### Community 5 - "get_connection"
Cohesion: 0.05
Nodes (67): Connection, _ensure_column(), get_connection(), Path, SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Add a column to an older schema; a no-op on current ones., Open a connection, ensuring the schema exists, and commit on success., get_db() (+59 more)

### Community 6 - "analysis.py"
Cohesion: 0.12
Nodes (23): _bind_dataset(), _bind_datasets(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), profile_csv(), DuckDB analytical engine - the seed of the Data & Evidence Engine. Analytical… (+15 more)

### Community 7 - "test_datasets.py"
Cohesion: 0.22
Nodes (20): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+12 more)

### Community 8 - "verify_p0.py"
Cohesion: 0.36
Nodes (9): log(), main(), Path, Popen, P0 Foundation milestone verification. Runs the P0 exit-test sequence as one…, request(), run_tests(), start_server() (+1 more)

### Community 9 - "Implementation Roadmap"
Cohesion: 0.29
Nodes (15): Milestone Exit Criteria (P0-P5), Implementation Roadmap, Feature Priority Model (M/S/C/L), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate (+7 more)

### Community 10 - "python_exec.py"
Cohesion: 0.19
Nodes (12): Exception, _alarm_handler(), _dataset_columns(), _guarded_import(), Restricted Python execution engine for the Analysis Workspace. The Python…, Column names of the attached file, without materialising any rows., Raised in the signal handler when a run exceeds its wall clock., Bound wall clock and CPU time, restoring both afterwards. Address space is… (+4 more)

### Community 11 - "package.json"
Cohesion: 0.40
Nodes (3): devDependencies, @testing-library/jest-dom, @testing-library/jest-dom

### Community 13 - "_kill_group"
Cohesion: 0.40
Nodes (5): _kill_group(), Popen, Kill the worker and anything it spawned (sandbox-exec sits in between)., A timeout kills the worker and anything it spawned, not just the shell., test_kill_group_terminates_the_tree()

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

### Community 20 - "_require_dataset"
Cohesion: 0.16
Nodes (14): create_plan(), get_plan(), get_profile(), list_plans(), profile_dataset(), Plan an analysis from the case question and the dataset profile. The plan is…, Retrieve the latest plan for a case's dataset., Every plan recorded for a case's dataset, newest first. (+6 more)

### Community 21 - "test_charts.py"
Cohesion: 0.25
Nodes (15): _case_with_run(), Bars sit on the zero baseline and scale linearly with their values., _temp_env(), override(), test_bar_chart_persists_and_serves(), test_bar_geometry_is_anchored_and_proportional(), test_chart_from_python_run(), test_chart_is_reproducible() (+7 more)

### Community 22 - "_require_case"
Cohesion: 0.19
Nodes (13): patch, create_finding(), get_finding(), list_findings(), Rename a case: its question and/or dataset label. Omitted fields are left as…, Record a finding against a specific analysis run. The finding starts…, List findings recorded against a case., Reopen a single finding. (+5 more)

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
Cohesion: 0.07
Nodes (38): ChartModel, _hex_rgb(), _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002). Turns a persisted…, A computed chart: geometry plus the data both renderers need. Everything…, Y-axis tick values from low to high. (+30 more)

### Community 27 - "test_plans.py"
Cohesion: 0.22
Nodes (15): _case_with_profile(), _FailingLLM, _GoodLLM, _MalformedLLM, _temp_env(), override(), test_list_plans_newest_first(), test_llm_failure_falls_back_to_deterministic() (+7 more)

### Community 28 - "exporter.py"
Cohesion: 0.18
Nodes (17): _chart_format(), _dataset_ids_of(), export_case(), _import_dataset_ids(), import_package(), PackageError, Path, Self-contained Analysis Case packages (P2-CASE-012). Export assembles… (+9 more)

### Community 29 - "get"
Cohesion: 0.15
Nodes (13): get, export_case_package(), get_case_progress(), get_evidence_chain(), health(), list_cases(), Where this case stands in the guided workflow (P3-FLOW-004). The stage is…, List all persisted Analysis Cases. (+5 more)

### Community 30 - "attach_dataset"
Cohesion: 0.15
Nodes (14): FileResponse, attach_dataset(), _chart_media_type(), _format_for(), get_chart_image(), list_datasets(), Path, Serve the persisted chart image itself. (+6 more)

### Community 31 - "post"
Cohesion: 0.20
Nodes (12): post, create_case(), duplicate_case(), get_case(), import_case_package(), Reconstruct a case from an exported package. The inverse of export: entities…, Deep-copy a case with new IDs throughout. Copies datasets (bytes on disk),…, Repoint a duplicated run's dataset list at the copy's own datasets. (+4 more)

### Community 32 - "delete_case"
Cohesion: 0.67
Nodes (3): delete, delete_case(), Delete a case and everything attached to it. Children are removed before the…

### Community 33 - "run_query"
Cohesion: 0.13
Nodes (17): _execute_read_only(), _is_read_only(), Run an already-bound read-only query and cap its result., Run a read-only SQL query against one attached file. The dataset path is bound…, Run a read-only SQL query across several attached files (P3-DATA-003).…, Reject anything that is not a single read-only statement., run_query(), run_query_multi() (+9 more)

### Community 34 - "run_python"
Cohesion: 0.18
Nodes (12): _child_env(), _failure(), The macOS sandbox-exec profile for one run. Reads are unrestricted (the…, The minimal environment the worker inherits. The API process may carry…, Execute user Python in a separate, OS-sandboxed process and tabulate it. Raises…, Turn a sandbox-layer rejection into the ValueError the API answers 400., run_python(), _seatbelt_profile() (+4 more)

### Community 35 - "P2 MVP Milestone Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,, Journey under test, P2 MVP Milestone Verification, Steps

### Community 36 - "ValueError"
Cohesion: 0.24
Nodes (11): execute_user_code(), _import_restrictions(), Install the import guard, refcounting so concurrent runs stay covered., Turn the script's `result` into the columns/rows shape runs persist. A list of…, Run user code in this process under the inner guards. Used by the sandboxed…, _tabulate(), _emit(), main() (+3 more)

### Community 37 - "DAH - Global Roadmap Status"
Cohesion: 0.29
Nodes (6): Current position detail, DAH - Global Roadmap Status, P3 V1 — entry checklist (next work, nothing started), Phase gate definitions (what "done" means), Phase status, Rules this file enforces

### Community 38 - "_DatasetHandle"
Cohesion: 0.15
Nodes (7): _DatasetHandle, _DatasetQuery, Any, A bound, dunder-hardened callable that runs read-only SQL on the file.…, The read-only view of an attached dataset that user code receives., The attached file as a list of row dicts, under the standard row cap., _rows_as_dicts()

### Community 39 - "test_workflow.py"
Cohesion: 0.15
Nodes (19): case_progress(), _counts(), Any, Guided analysis workflow (P3-FLOW-004). The Master Specification's core loop is…, Whether the case has at least one artifact behind this stage., The case's position in the workflow and the action that moves it. `stage` is…, How much of each artifact the case has right now., _stage_state() (+11 more)

### Community 40 - "validate_finding"
Cohesion: 0.25
Nodes (8): _dataset_ids_of(), list_runs(), Reproduce a finding's computation and check its support. The trust loop closes…, The datasets a run touches; None means an unknown (legacy) set. Older runs…, List analysis runs for a case, without the heavy result rows., validate_finding(), RunSummary, ValidationResult

### Community 41 - "test_case_management.py"
Cohesion: 0.28
Nodes (15): _counts(), _first_run(), _full_case(), A case with a dataset, profile, run, finding and chart attached., _temp_env(), override(), test_delete_does_not_touch_other_cases(), test_delete_is_idempotent_for_unknown_case() (+7 more)

### Community 42 - "test_profiles.py"
Cohesion: 0.44
Nodes (9): _attach(), _temp_env(), override(), test_deep_profile_stats(), test_deep_profile_survives_reopen(), test_get_profile_before_profiling_returns_404(), test_header_only_dataset_profiles_cleanly(), test_profile_and_reopen() (+1 more)

## Knowledge Gaps
- **71 isolated node(s):** `@testing-library/jest-dom`, `dah-server`, `name`, `private`, `version` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 263 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `test_datasets.py`, `test_workflow.py`, `test_case_management.py`, `test_profiles.py`, `test_python_runs.py`, `test_charts.py`, `main.py`, `test_multi_dataset_runs.py`, `test_charts_raster.py`, `test_plans.py`?**
  _High betweenness centrality (0.101) - this node is a cross-community bridge._
- **Why does `render_chart()` connect `test_charts_raster.py` to `test_charts.py`, `main.py`?**
  _High betweenness centrality (0.022) - this node is a cross-community bridge._
- **Why does `profile_csv()` connect `analysis.py` to `_require_dataset`, `main.py`?**
  _High betweenness centrality (0.018) - this node is a cross-community bridge._
- **What connects `@testing-library/jest-dom`, `dah-server`, `name` to the rest of the system?**
  _71 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `web/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05656565656565657 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._