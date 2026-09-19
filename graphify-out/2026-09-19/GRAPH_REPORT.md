# Graph Report - DA-Harness  (2026-09-19)

## Corpus Check
- 60 files · ~44,795 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .css 1, .tsbuildinfo 1)

## Summary
- 722 nodes · 1414 edges · 54 communities (50 shown, 2 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 73 edges (avg confidence: 0.88)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `967544bc`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Product & Engineering Master Specification
- models.py
- web/package.json
- compilerOptions
- Coding-Agent Production System
- get_db
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
- post
- test_charts.py
- Case
- main.py
- test_multi_dataset_runs.py
- planner.py
- test_charts_raster.py
- test_plans.py
- exporter.py
- get
- get_chart_image
- test_eda.py
- delete_case
- db.py
- run_python
- P2 MVP Milestone Verification
- execute_user_code
- DAH - Global Roadmap Status
- _DatasetQuery
- test_workflow.py
- validate_finding
- test_case_management.py
- test_profiles.py
- _ImportGuard
- get_connection
- test_export.py
- test_runs.py
- test_validation.py
- test_cases.py
- test_findings.py
- _DatasetHandle
- verify_p2.py
- create_finding
- list_plans

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 58 edges
2. `Product & Engineering Master Specification` - 20 edges
3. `run_query()` - 19 edges
4. `render_chart()` - 19 edges
5. `get_db()` - 18 edges
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

## Communities (54 total, 2 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.14
Nodes (21): BaseModel, Run one exploratory operation over an attached dataset (P3-ANALYSIS-005).…, run_exploratory_analysis(), CaseCreate, CaseProgress, CaseUpdate, EdaCreate, EdaResult (+13 more)

### Community 2 - "web/package.json"
Cohesion: 0.06
Nodes (38): jsdom, react, react-dom, @testing-library/react, @types/react, @types/react-dom, typescript, vite (+30 more)

### Community 3 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Coding-Agent Production System"
Cohesion: 0.14
Nodes (12): Coding-Agent Production System, Agent Implementation Protocol, Artifact Authority Hierarchy, Agent Control Loop: PLAN to EXIT-CRITERIA, Development Context Protocol, Development State Model, Hard Stop Conditions, Persistent Project State (/ai documents) (+4 more)

### Community 5 - "get_db"
Cohesion: 0.24
Nodes (12): get_db(), _case_with_dataset(), _python(), Hard-sandbox tests for P3-SEC-001. The inner guards (import allowlist,…, An unbounded loop ends at the time limit and the API answers 400., A worker that dies on startup surfaces as a 400, never as an API crash., A rejected contract is a 400 with a message, not a dead process., _temp_env() (+4 more)

### Community 6 - "analysis.py"
Cohesion: 0.07
Nodes (48): _bind_dataset(), _bind_datasets(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), _execute_read_only(), _is_read_only() (+40 more)

### Community 7 - "test_datasets.py"
Cohesion: 0.24
Nodes (19): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+11 more)

### Community 8 - "verify_p0.py"
Cohesion: 0.36
Nodes (9): log(), main(), Path, Popen, P0 Foundation milestone verification. Runs the P0 exit-test sequence as one…, request(), run_tests(), start_server() (+1 more)

### Community 9 - "Implementation Roadmap"
Cohesion: 0.29
Nodes (15): Milestone Exit Criteria (P0-P5), Implementation Roadmap, Feature Priority Model (M/S/C/L), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate (+7 more)

### Community 10 - "python_exec.py"
Cohesion: 0.24
Nodes (10): Exception, _alarm_handler(), _guarded_import(), Restricted Python execution engine for the Analysis Workspace. The Python…, Raised in the signal handler when a run exceeds its wall clock., Bound wall clock and CPU time, restoring both afterwards. Address space is…, The builtins namespace user code sees., _resource_limits() (+2 more)

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
Cohesion: 0.42
Nodes (15): _case_with_dataset(), _python(), _temp_env(), test_evidence_chain_works_for_python_run(), test_python_allows_safe_import(), test_python_rejects_blocked_import(), test_python_rejects_dunder_escape(), test_python_rejects_empty_code() (+7 more)

### Community 19 - "P1 Vertical Slice - Verification Report"
Cohesion: 0.33
Nodes (5): Decision, Evidence, Exit criteria (Coding-Agent Production System section 8), Exit-test sequence (the full user journey), P1 Vertical Slice - Verification Report

### Community 20 - "post"
Cohesion: 0.12
Nodes (22): post, create_multi_dataset_run(), create_plan(), create_python_run(), create_run(), get_plan(), get_profile(), import_case_package() (+14 more)

### Community 21 - "test_charts.py"
Cohesion: 0.28
Nodes (14): _case_with_run(), Bars sit on the zero baseline and scale linearly with their values., _temp_env(), override(), test_bar_chart_persists_and_serves(), test_bar_geometry_is_anchored_and_proportional(), test_chart_from_python_run(), test_chart_is_reproducible() (+6 more)

### Community 22 - "Case"
Cohesion: 0.17
Nodes (12): patch, create_case(), get_case(), list_cases(), Set a finding's validation status by explicit decision only., List all persisted Analysis Cases., Rename a case: its question and/or dataset label. Omitted fields are left as…, Create and persist a new Analysis Case. (+4 more)

### Community 23 - "main.py"
Cohesion: 0.20
Nodes (13): _chart_row_to_summary(), create_chart(), get_chart(), list_charts(), Render a chart from a persisted run result and store it with the case. The…, List the charts rendered from one run, without the image bytes., Retrieve a chart's metadata., _require_chart() (+5 more)

### Community 24 - "test_multi_dataset_runs.py"
Cohesion: 0.34
Nodes (16): _case_with_datasets(), _multi_run(), Multi-dataset run tests for P3-DATA-003. Attaching several datasets per case…, The trust loop closes on a multi-dataset run too., The k-th placeholder binds to the k-th dataset, not to any file that fits., _temp_env(), test_dataset_ids_must_be_unique(), test_duplicate_copies_the_join_run() (+8 more)

### Community 25 - "planner.py"
Cohesion: 0.13
Nodes (20): _categorical_columns(), _column_names(), _configured_llm(), create_plan(), LLMPlanner, _null_columns(), _numeric_columns(), plan_analysis() (+12 more)

### Community 26 - "test_charts_raster.py"
Cohesion: 0.07
Nodes (39): ChartModel, _hex_rgb(), _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009, P3-CHART-002). Turns a persisted…, A computed chart: geometry plus the data both renderers need. Everything…, Y-axis tick values from low to high. (+31 more)

### Community 27 - "test_plans.py"
Cohesion: 0.24
Nodes (14): _case_with_profile(), _FailingLLM, _GoodLLM, _MalformedLLM, _temp_env(), test_list_plans_newest_first(), test_llm_failure_falls_back_to_deterministic(), test_malformed_llm_output_falls_back() (+6 more)

### Community 28 - "exporter.py"
Cohesion: 0.18
Nodes (17): _chart_format(), _dataset_ids_of(), export_case(), _import_dataset_ids(), import_package(), PackageError, Path, Self-contained Analysis Case packages (P2-CASE-012). Export assembles… (+9 more)

### Community 29 - "get"
Cohesion: 0.12
Nodes (21): get, attach_dataset(), _dataset_ids_of(), export_case_package(), get_case_progress(), get_run(), health(), list_datasets() (+13 more)

### Community 30 - "get_chart_image"
Cohesion: 0.18
Nodes (12): FileResponse, _chart_media_type(), duplicate_case(), _format_for(), get_chart_image(), Path, Serve the persisted chart image itself., The artifact's content type, sniffed from its stored bytes. Charts created… (+4 more)

### Community 31 - "test_eda.py"
Cohesion: 0.44
Nodes (13): _dataset(), _eda(), EDA tests for P3-ANALYSIS-005. Every op compiles to read-only DuckDB and runs…, _temp_env(), test_correlates_two_numeric_columns(), test_distribution_falls_back_to_top_values_for_a_category(), test_distribution_summarises_a_numeric_column(), test_eda_404_for_unknown_dataset() (+5 more)

### Community 32 - "delete_case"
Cohesion: 0.67
Nodes (3): delete, delete_case(), Delete a case and everything attached to it. Children are removed before the…

### Community 33 - "db.py"
Cohesion: 0.24
Nodes (8): _ensure_column(), SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Add a column to an older schema; a no-op on current ones., log(), main(), override(), record(), P1 Vertical Slice milestone verification. Runs the full user journey as one…

### Community 34 - "run_python"
Cohesion: 0.18
Nodes (12): _child_env(), _failure(), The macOS sandbox-exec profile for one run. Reads are unrestricted (the…, The minimal environment the worker inherits. The API process may carry…, Execute user Python in a separate, OS-sandboxed process and tabulate it. Raises…, Turn a sandbox-layer rejection into the ValueError the API answers 400., run_python(), _seatbelt_profile() (+4 more)

### Community 35 - "P2 MVP Milestone Verification"
Cohesion: 0.33
Nodes (5): Decision, Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,, Journey under test, P2 MVP Milestone Verification, Steps

### Community 36 - "execute_user_code"
Cohesion: 0.24
Nodes (10): _dataset_columns(), execute_user_code(), _import_restrictions(), Column names of the attached file, without materialising any rows., Install the import guard, refcounting so concurrent runs stay covered., Run user code in this process under the inner guards. Used by the sandboxed…, _emit(), main() (+2 more)

### Community 37 - "DAH - Global Roadmap Status"
Cohesion: 0.29
Nodes (6): Current position detail, DAH - Global Roadmap Status, P3 V1 — entry checklist (next work, nothing started), Phase gate definitions (what "done" means), Phase status, Rules this file enforces

### Community 38 - "_DatasetQuery"
Cohesion: 0.22
Nodes (5): _DatasetQuery, Any, A bound, dunder-hardened callable that runs read-only SQL on the file.…, Turn the script's `result` into the columns/rows shape runs persist. A list of…, _tabulate()

### Community 39 - "test_workflow.py"
Cohesion: 0.15
Nodes (19): case_progress(), _counts(), Any, Guided analysis workflow (P3-FLOW-004). The Master Specification's core loop is…, Whether the case has at least one artifact behind this stage., The case's position in the workflow and the action that moves it. `stage` is…, How much of each artifact the case has right now., _stage_state() (+11 more)

### Community 40 - "validate_finding"
Cohesion: 0.22
Nodes (9): get_evidence_chain(), get_finding(), Reproduce a finding's computation and check its support. The trust loop closes…, Reopen a single finding., Trace a finding back to its computation and dataset. Walks finding -> run ->…, validate_finding(), EvidenceChain, The trust chain a reviewer walks to verify a finding. (+1 more)

### Community 41 - "test_case_management.py"
Cohesion: 0.28
Nodes (15): _counts(), _first_run(), _full_case(), A case with a dataset, profile, run, finding and chart attached., _temp_env(), override(), test_delete_does_not_touch_other_cases(), test_delete_is_idempotent_for_unknown_case() (+7 more)

### Community 42 - "test_profiles.py"
Cohesion: 0.44
Nodes (9): _attach(), _temp_env(), override(), test_deep_profile_stats(), test_deep_profile_survives_reopen(), test_get_profile_before_profiling_returns_404(), test_header_only_dataset_profiles_cleanly(), test_profile_and_reopen() (+1 more)

### Community 44 - "get_connection"
Cohesion: 0.22
Nodes (9): Connection, get_connection(), Path, Open a connection, ensuring the schema exists, and commit on success., override(), override(), override(), override() (+1 more)

### Community 45 - "test_export.py"
Cohesion: 0.44
Nodes (8): _full_case(), _temp_env(), override(), test_export_contains_every_section(), test_export_unknown_case_returns_404(), test_import_rejects_bad_package(), test_round_trip_relinks_references_and_serves_artifacts(), test_round_trip_restores_the_case()

### Community 46 - "test_runs.py"
Cohesion: 0.47
Nodes (8): _case_with_dataset(), _temp_env(), override(), test_list_runs_excludes_rows(), test_rejects_multi_statement(), test_rejects_write_query(), test_run_aggregation_and_reopen(), test_run_unknown_dataset_returns_404()

### Community 47 - "test_validation.py"
Cohesion: 0.36
Nodes (8): _full_setup(), The core guarantee: if the persisted result no longer matches a rerun,…, Case + dataset + profile + run + finding. Returns case and finding ids., _temp_env(), override(), test_validate_fails_when_result_drifts(), test_validate_partially_supported_when_nulls_exist(), test_validate_supported()

### Community 48 - "test_cases.py"
Cohesion: 0.36
Nodes (7): The golden test: a case survives being saved and reopened., Point the app at a fresh on-disk SQLite file for this test., _temp_db(), override(), test_create_and_reopen_case(), test_get_unknown_case_returns_404(), test_list_cases()

### Community 49 - "test_findings.py"
Cohesion: 0.50
Nodes (7): _case_with_run(), _temp_env(), override(), test_create_finding_and_trace_evidence(), test_finding_unknown_run_returns_404(), test_findings_survive_reopen(), test_set_validation_status()

### Community 50 - "_DatasetHandle"
Cohesion: 0.29
Nodes (4): _DatasetHandle, The read-only view of an attached dataset that user code receives., The attached file as a list of row dicts, under the standard row cap., _rows_as_dicts()

### Community 51 - "verify_p2.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P2 MVP milestone verification. Runs the full P2 user journey as one atomic…

### Community 52 - "create_finding"
Cohesion: 0.40
Nodes (5): create_finding(), list_findings(), Record a finding against a specific analysis run. The finding starts…, List findings recorded against a case., Finding

### Community 53 - "list_plans"
Cohesion: 0.50
Nodes (4): list_plans(), Every plan recorded for a case's dataset, newest first., PlanSummary, Plan metadata without the plan body.

## Knowledge Gaps
- **71 isolated node(s):** `@testing-library/jest-dom`, `dah-server`, `name`, `private`, `version` (+66 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 273 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **2 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `get_db`, `test_datasets.py`, `test_python_runs.py`, `test_charts.py`, `main.py`, `test_multi_dataset_runs.py`, `test_charts_raster.py`, `test_plans.py`, `test_eda.py`, `db.py`, `test_workflow.py`, `test_case_management.py`, `test_profiles.py`, `test_export.py`, `test_runs.py`, `test_validation.py`, `test_cases.py`, `test_findings.py`, `verify_p2.py`?**
  _High betweenness centrality (0.103) - this node is a cross-community bridge._
- **Why does `run_query()` connect `analysis.py` to `execute_user_code`, `_DatasetQuery`, `validate_finding`, `python_exec.py`, `_DatasetHandle`, `post`, `main.py`?**
  _High betweenness centrality (0.024) - this node is a cross-community bridge._
- **Why does `render_chart()` connect `test_charts_raster.py` to `test_charts.py`, `main.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `@testing-library/jest-dom`, `dah-server`, `name` to the rest of the system?**
  _71 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `models.py` be split into smaller, more focused modules?**
  _Cohesion score 0.13852813852813853 - nodes in this community are weakly interconnected._
- **Should `web/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05656565656565657 - nodes in this community are weakly interconnected._