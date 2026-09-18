# Graph Report - DA-Harness  (2026-09-19)

## Corpus Check
- 40 files · ~18,690 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .css 1, .tsbuildinfo 1)

## Summary
- 306 nodes · 525 edges · 20 communities (16 shown, 1 thin omitted)
- Extraction: 93% EXTRACTED · 7% INFERRED · 0% AMBIGUOUS · INFERRED: 37 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `10bff137`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Product & Engineering Master Specification
- main.py
- web/package.json
- compilerOptions
- Coding-Agent Production System
- get_connection
- analysis.py
- test_datasets.py
- verify_p0.py
- Implementation Roadmap
- verify_p1.py
- package.json
- dah-server
- Verification & Production Readiness Plan
- DEC-001: Web-first MVP, Tauri post-MVP
- test_findings.py
- P1 Vertical Slice - Verification Report

## God Nodes (most connected - your core abstractions)
1. `get_connection()` - 26 edges
2. `Product & Engineering Master Specification` - 20 edges
3. `compilerOptions` - 17 edges
4. `Implementation Roadmap` - 15 edges
5. `Coding-Agent Production System` - 14 edges
6. `_temp_env()` - 12 edges
7. `Verification & Production Readiness Plan` - 12 edges
8. `profile_csv()` - 8 edges
9. `get_db()` - 8 edges
10. `_require_case()` - 8 edges

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

## Communities (20 total, 1 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.13
Nodes (17): Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy, Analysis Case, Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts) (+9 more)

### Community 1 - "main.py"
Cohesion: 0.07
Nodes (59): BaseModel, get, patch, post, attach_dataset(), create_case(), create_finding(), create_run() (+51 more)

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
Cohesion: 0.10
Nodes (36): Connection, get_connection(), Path, SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Open a connection, ensuring the schema exists, and commit on success., get_db(), The golden test: a case survives being saved and reopened., Point the app at a fresh on-disk SQLite file for this test. (+28 more)

### Community 6 - "analysis.py"
Cohesion: 0.20
Nodes (13): _bind_dataset(), _is_read_only(), profile_csv(), DuckDB analytical engine - the seed of the Data & Evidence Engine. Analytical…, Run a read-only SQL query against a CSV file. The dataset path is bound as a…, Return the DuckDB reader call and the path to bind for a file. DuckDB cannot…, Swap the dataset placeholder(s) in user SQL for this file's reader. Either…, Reject anything that is not a single read-only statement. (+5 more)

### Community 7 - "test_datasets.py"
Cohesion: 0.24
Nodes (19): _attach(), _golden_parquet(), _golden_xlsx(), _make_case(), _profile(), The same SQL runs against csv, parquet, and xlsx datasets., Writing the natural read_parquet(?) placeholder works on a parquet file., Build a two-row parquet file from the golden CSV content. (+11 more)

### Community 8 - "verify_p0.py"
Cohesion: 0.36
Nodes (9): Popen, log(), main(), Path, P0 Foundation milestone verification. Runs the P0 exit-test sequence as one…, request(), run_tests(), start_server() (+1 more)

### Community 9 - "Implementation Roadmap"
Cohesion: 0.29
Nodes (15): Milestone Exit Criteria (P0-P5), Implementation Roadmap, Feature Priority Model (M/S/C/L), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate (+7 more)

### Community 10 - "verify_p1.py"
Cohesion: 0.47
Nodes (5): log(), main(), override(), record(), P1 Vertical Slice milestone verification. Runs the full user journey as one…

### Community 11 - "package.json"
Cohesion: 0.40
Nodes (3): devDependencies, @testing-library/jest-dom, @testing-library/jest-dom

### Community 16 - "Verification & Production Readiness Plan"
Cohesion: 0.22
Nodes (9): Verification & Production Readiness Plan, AI Evaluation Dataset, AI Safety Rules, Data Trust Rules (Observed/Calculated/Inferred/...), Golden Datasets and Golden Analytical Tests, Production Readiness Checklist, Release Decision Matrix, Defect Severity Model (P0-P3) (+1 more)

### Community 17 - "DEC-001: Web-first MVP, Tauri post-MVP"
Cohesion: 0.29
Nodes (7): AGENTS.md graphify guidance, API-only frontend contract, DEC-001: Web-first MVP, Tauri post-MVP, Locked tech selections (FastAPI/SQLite/DuckDB), Control-Layer Architecture, Web-First Delivery Strategy (Tauri post-MVP), web/index.html (React entry point)

### Community 18 - "test_findings.py"
Cohesion: 0.50
Nodes (7): _case_with_run(), _temp_env(), override(), test_create_finding_and_trace_evidence(), test_finding_unknown_run_returns_404(), test_findings_survive_reopen(), test_set_validation_status()

### Community 19 - "P1 Vertical Slice - Verification Report"
Cohesion: 0.33
Nodes (5): Decision, Evidence, Exit criteria (Coding-Agent Production System section 8), Exit-test sequence (the full user journey), P1 Vertical Slice - Verification Report

## Knowledge Gaps
- **62 isolated node(s):** `@testing-library/jest-dom`, `dah-server`, `name`, `private`, `version` (+57 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 130 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `get_connection()` connect `get_connection` to `main.py`, `test_findings.py`, `verify_p1.py`, `test_datasets.py`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Product & Engineering Master Specification` connect `Product & Engineering Master Specification` to `Verification & Production Readiness Plan`, `Implementation Roadmap`, `Coding-Agent Production System`, `DEC-001: Web-first MVP, Tauri post-MVP`?**
  _High betweenness centrality (0.021) - this node is a cross-community bridge._
- **Why does `Coding-Agent Production System` connect `Coding-Agent Production System` to `Product & Engineering Master Specification`, `Implementation Roadmap`, `Verification & Production Readiness Plan`?**
  _High betweenness centrality (0.015) - this node is a cross-community bridge._
- **What connects `@testing-library/jest-dom`, `dah-server`, `name` to the rest of the system?**
  _62 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.1323529411764706 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.06912442396313365 - nodes in this community are weakly interconnected._
- **Should `web/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.05656565656565657 - nodes in this community are weakly interconnected._