# Graph Report - DA-Harness  (2026-09-19)

## Corpus Check
- 47 files · ~29,607 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .css 1, .tsbuildinfo 1)

## Summary
- 505 nodes · 945 edges · 32 communities (28 shown, 1 thin omitted)
- Extraction: 95% EXTRACTED · 5% INFERRED · 0% AMBIGUOUS · INFERRED: 47 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `9d7fc5c7`
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
- Verification & Production Readiness Plan
- DEC-001: Web-first MVP, Tauri post-MVP
- test_python_runs.py
- P1 Vertical Slice - Verification Report
- post
- test_charts.py
- verify_p1.py
- main.py
- test_case_management.py
- planner.py
- get
- test_plans.py
- Plan
- Case
- attach_dataset
- delete_case

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 39 edges
2. `Product & Engineering Master Specification` - 20 edges
3. `compilerOptions` - 17 edges
4. `_temp_env()` - 15 edges
5. `Implementation Roadmap` - 15 edges
6. `Coding-Agent Production System` - 14 edges
7. `profile_csv()` - 13 edges
8. `render_chart()` - 13 edges
9. `_python()` - 13 edges
10. `get_db()` - 12 edges

## Surprising Connections (you probably didn't know these)
- `override()` --calls--> `get_connection()`  [EXTRACTED]
  verification/p1/verify_p1.py → server/app/db.py
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P0 Foundation`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P3 V1`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `P2 MVP` --references--> `Analysis Planner`  [INFERRED]
  docs/Implementation Roadmap.md → docs/Product & Engineering Master Specification.md
- `Locked tech selections (FastAPI/SQLite/DuckDB)` --implements--> `Control-Layer Architecture`  [INFERRED]
  ai/DECISIONS.md → docs/Product & Engineering Master Specification.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **P0 Verification System: gate + state + report** — verification_p0_report, ai_current_state, ai_tasks, ai_handoff [INFERRED 0.90]

## Communities (32 total, 1 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "models.py"
Cohesion: 0.16
Nodes (18): BaseModel, Reproduce a finding's computation and check its support. The trust loop closes…, validate_finding(), CaseCreate, CaseUpdate, ChartCreate, EvidenceChain, FindingCreate (+10 more)

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
Cohesion: 0.07
Nodes (52): Connection, _ensure_column(), get_connection(), Path, SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Add a column to an older schema; a no-op on current ones., Open a connection, ensuring the schema exists, and commit on success., get_db() (+44 more)

### Community 6 - "analysis.py"
Cohesion: 0.12
Nodes (23): _bind_dataset(), _coerce(), _column_stat(), _column_stat_expr(), _duplicate_row_count(), _is_read_only(), profile_csv(), DuckDB analytical engine - the seed of the Data & Evidence Engine. Analytical… (+15 more)

### Community 7 - "test_datasets.py"
Cohesion: 0.24
Nodes (19): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+11 more)

### Community 8 - "verify_p0.py"
Cohesion: 0.36
Nodes (9): Popen, log(), main(), Path, P0 Foundation milestone verification. Runs the P0 exit-test sequence as one…, request(), run_tests(), start_server() (+1 more)

### Community 9 - "Implementation Roadmap"
Cohesion: 0.29
Nodes (15): Milestone Exit Criteria (P0-P5), Implementation Roadmap, Feature Priority Model (M/S/C/L), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate (+7 more)

### Community 10 - "python_exec.py"
Cohesion: 0.08
Nodes (29): Exception, Run a read-only SQL query against a CSV file. The dataset path is bound as a…, run_query(), _alarm_handler(), _dataset_columns(), _DatasetHandle, _DatasetQuery, _guarded_import() (+21 more)

### Community 11 - "package.json"
Cohesion: 0.40
Nodes (3): devDependencies, @testing-library/jest-dom, @testing-library/jest-dom

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
Cohesion: 0.14
Nodes (18): post, create_case(), create_plan(), create_python_run(), create_run(), get_profile(), list_plans(), profile_dataset() (+10 more)

### Community 21 - "test_charts.py"
Cohesion: 0.12
Nodes (26): _label(), _nice_scale(), _numeric(), Deterministic chart renderer (P2-ANALYSIS-009). Turns a persisted run result…, Render a persisted run result to SVG. Raises ValueError for anything the chart…, Coerce a value to float; non-numeric and None are not plottable., Compact, escaped axis label for a category or tick., Split the result into ordered (series name, points) pairs. Without a series… (+18 more)

### Community 22 - "verify_p1.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P1 Vertical Slice milestone verification. Runs the full user journey as one…

### Community 23 - "main.py"
Cohesion: 0.17
Nodes (15): FileResponse, _chart_row_to_summary(), create_chart(), get_chart(), get_chart_image(), list_charts(), List the charts rendered from one run, without the image bytes., Retrieve a chart's metadata. (+7 more)

### Community 24 - "test_case_management.py"
Cohesion: 0.30
Nodes (14): _counts(), _first_run(), _full_case(), A case with a dataset, profile, run, finding and chart attached., _temp_env(), test_delete_does_not_touch_other_cases(), test_delete_is_idempotent_for_unknown_case(), test_delete_removes_case_and_its_data() (+6 more)

### Community 25 - "planner.py"
Cohesion: 0.13
Nodes (20): _categorical_columns(), _column_names(), _configured_llm(), create_plan(), LLMPlanner, _null_columns(), _numeric_columns(), plan_analysis() (+12 more)

### Community 26 - "get"
Cohesion: 0.15
Nodes (18): get, create_finding(), get_evidence_chain(), get_finding(), get_run(), health(), list_findings(), list_runs() (+10 more)

### Community 27 - "test_plans.py"
Cohesion: 0.24
Nodes (14): _case_with_profile(), _FailingLLM, _GoodLLM, _MalformedLLM, _temp_env(), test_list_plans_newest_first(), test_llm_failure_falls_back_to_deterministic(), test_malformed_llm_output_falls_back() (+6 more)

### Community 28 - "Plan"
Cohesion: 0.50
Nodes (4): get_plan(), Retrieve the latest plan for a case's dataset., Plan, A structured analysis plan, persisted against a case and dataset.

### Community 29 - "Case"
Cohesion: 0.17
Nodes (12): patch, duplicate_case(), get_case(), list_cases(), List all persisted Analysis Cases., Rename a case: its question and/or dataset label. Omitted fields are left as…, Deep-copy a case with new IDs throughout. Copies datasets (bytes on disk),…, Set a finding's validation status by explicit decision only. (+4 more)

### Community 30 - "attach_dataset"
Cohesion: 0.25
Nodes (8): attach_dataset(), _format_for(), list_datasets(), Dataset format is the lowercased extension, without the dot., Attach a CSV dataset to an Analysis Case. The file is written to disk by the…, List datasets attached to an Analysis Case., Dataset, UploadFile

### Community 32 - "delete_case"
Cohesion: 0.67
Nodes (3): delete, delete_case(), Delete a case and everything attached to it. Children are removed before the…

## Knowledge Gaps
- **62 isolated node(s):** `@testing-library/jest-dom`, `dah-server`, `name`, `private`, `version` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 195 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `test_datasets.py`, `test_python_runs.py`, `test_charts.py`, `verify_p1.py`, `main.py`, `test_case_management.py`, `test_plans.py`?**
  _High betweenness centrality (0.083) - this node is a cross-community bridge._
- **Why does `profile_csv()` connect `analysis.py` to `post`, `main.py`?**
  _High betweenness centrality (0.023) - this node is a cross-community bridge._
- **Why does `run_python()` connect `python_exec.py` to `post`, `main.py`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **What connects `@testing-library/jest-dom`, `dah-server`, `name` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `web/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05656565656565657 - nodes in this community are weakly interconnected._
- **Should `compilerOptions` be split into smaller, more focused modules?**
  _Cohesion score 0.10526315789473684 - nodes in this community are weakly interconnected._