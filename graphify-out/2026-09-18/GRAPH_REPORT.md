# Graph Report - DA-Harness  (2026-09-18)

## Corpus Check
- 36 files · ~15,116 words
- Verdict: corpus is large enough that graph structure adds value.
- Unclassified: 3 file(s) not represented in the graph (top: (none) 1, .css 1, .tsbuildinfo 1)

## Summary
- 238 nodes · 377 edges · 15 communities (11 shown, 1 thin omitted)
- Extraction: 92% EXTRACTED · 8% INFERRED · 0% AMBIGUOUS · INFERRED: 31 edges (avg confidence: 0.9)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `4d26ab0d`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Product & Engineering Master Specification
- main.py
- web/package.json
- compilerOptions
- Coding-Agent Production System
- get_connection
- profile_csv
- test_runs.py
- verify_p0.py
- devDependencies
- package.json
- dah-server

## God Nodes (most connected - your core abstractions)
1. `Product & Engineering Master Specification` - 20 edges
2. `get_connection()` - 18 edges
3. `compilerOptions` - 17 edges
4. `Implementation Roadmap` - 15 edges
5. `Coding-Agent Production System` - 14 edges
6. `Verification & Production Readiness Plan` - 12 edges
7. `_temp_env()` - 8 edges
8. `_temp_env()` - 8 edges
9. `profile_csv()` - 7 edges
10. `create_run()` - 7 edges

## Surprising Connections (you probably didn't know these)
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P0 Foundation`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P3 V1`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `Locked tech selections (FastAPI/SQLite/DuckDB)` --implements--> `Control-Layer Architecture`  [INFERRED]
  ai/DECISIONS.md → docs/Product & Engineering Master Specification.md
- `AGENTS.md graphify guidance` --references--> `web/index.html (React entry point)`  [INFERRED]
  AGENTS.md → web/index.html
- `web/index.html (React entry point)` --references--> `Web-First Delivery Strategy (Tauri post-MVP)`  [INFERRED]
  web/index.html → docs/Product & Engineering Master Specification.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **P0 Verification System: gate + state + report** — verification_p0_report, ai_current_state, ai_tasks, ai_handoff [INFERRED 0.90]

## Communities (15 total, 1 thin omitted)

### Community 0 - "Product & Engineering Master Specification"
Cohesion: 0.08
Nodes (39): AGENTS.md graphify guidance, API-only frontend contract, DEC-001: Web-first MVP, Tauri post-MVP, Locked tech selections (FastAPI/SQLite/DuckDB), Milestone Exit Criteria (P0-P5), Implementation Roadmap, Core Analytical Loop: Question to Finding, Feature Priority Model (M/S/C/L) (+31 more)

### Community 1 - "main.py"
Cohesion: 0.10
Nodes (38): BaseModel, get, post, Run a read-only SQL query against a CSV file. The dataset path is bound as a…, run_query(), attach_dataset(), create_case(), create_run() (+30 more)

### Community 2 - "web/package.json"
Cohesion: 0.07
Nodes (29): jsdom, react, react-dom, @testing-library/react, @types/react, @types/react-dom, typescript, vite (+21 more)

### Community 3 - "compilerOptions"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Coding-Agent Production System"
Cohesion: 0.09
Nodes (21): Coding-Agent Production System, Agent Implementation Protocol, Artifact Authority Hierarchy, Agent Control Loop: PLAN to EXIT-CRITERIA, Development Context Protocol, Development State Model, Hard Stop Conditions, Persistent Project State (/ai documents) (+13 more)

### Community 5 - "get_connection"
Cohesion: 0.12
Nodes (28): Connection, get_connection(), Path, SQLite persistence for Analysis Cases, datasets, and profiles. Owns case STATE…, Open a connection, ensuring the schema exists, and commit on success., get_db(), The golden test: a case survives being saved and reopened., Point the app at a fresh on-disk SQLite file for this test. (+20 more)

### Community 6 - "profile_csv"
Cohesion: 0.31
Nodes (7): _is_read_only(), profile_csv(), DuckDB analytical engine - the seed of the Data & Evidence Engine. Analytical…, Reject anything that is not a single read-only statement., Profile a CSV: row count, columns, and per-column null counts. The path is…, test_profile_csv(), test_profile_csv_missing_values()

### Community 7 - "test_runs.py"
Cohesion: 0.57
Nodes (7): _case_with_dataset(), _temp_env(), test_list_runs_excludes_rows(), test_rejects_multi_statement(), test_rejects_write_query(), test_run_aggregation_and_reopen(), test_run_unknown_dataset_returns_404()

### Community 8 - "verify_p0.py"
Cohesion: 0.36
Nodes (9): Popen, log(), main(), Path, P0 Foundation milestone verification. Runs the P0 exit-test sequence as one…, request(), run_tests(), start_server() (+1 more)

### Community 10 - "devDependencies"
Cohesion: 0.22
Nodes (9): devDependencies, jsdom, @testing-library/react, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react (+1 more)

### Community 11 - "package.json"
Cohesion: 0.40
Nodes (3): devDependencies, @testing-library/jest-dom, @testing-library/jest-dom

## Knowledge Gaps
- **58 isolated node(s):** `@testing-library/jest-dom`, `dah-server`, `name`, `private`, `version` (+53 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 106 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Product & Engineering Master Specification` connect `Product & Engineering Master Specification` to `Coding-Agent Production System`?**
  _High betweenness centrality (0.035) - this node is a cross-community bridge._
- **Why does `get_connection()` connect `get_connection` to `main.py`, `test_runs.py`?**
  _High betweenness centrality (0.034) - this node is a cross-community bridge._
- **Why does `Coding-Agent Production System` connect `Coding-Agent Production System` to `Product & Engineering Master Specification`?**
  _High betweenness centrality (0.025) - this node is a cross-community bridge._
- **What connects `@testing-library/jest-dom`, `dah-server`, `name` to the rest of the system?**
  _58 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product & Engineering Master Specification` be split into smaller, more focused modules?**
  _Cohesion score 0.08333333333333333 - nodes in this community are weakly interconnected._
- **Should `main.py` be split into smaller, more focused modules?**
  _Cohesion score 0.0975609756097561 - nodes in this community are weakly interconnected._
- **Should `web/package.json` be split into smaller, more focused modules?**
  _Cohesion score 0.0746031746031746 - nodes in this community are weakly interconnected._