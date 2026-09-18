# Graph Report - DA-Harness  (2026-09-18)

## Corpus Check
- Corpus is ~13,121 words - fits in a single context window. You may not need a graph.

## Summary
- 186 nodes · 251 edges · 16 communities (12 shown, 1 thin omitted)
- Extraction: 89% EXTRACTED · 11% INFERRED · 0% AMBIGUOUS · INFERRED: 27 edges (avg confidence: 0.9)
- Token cost: 9,000 input · 3,800 output

## Community Hubs (Navigation)
- Product Spec & Decisions
- FastAPI Core Endpoints
- Web Toolchain & Dependencies
- TypeScript Config
- Agent Build Protocol & State
- SQLite Persistence Layer
- Roadmap & Milestones
- React UI & API Client
- P0 Verification Harness
- Verification & Quality Gates
- Web Dev Dependencies
- Test Setup
- Server Package

## God Nodes (most connected - your core abstractions)
1. `Product & Engineering Master Specification` - 20 edges
2. `compilerOptions` - 17 edges
3. `Implementation Roadmap` - 15 edges
4. `Coding-Agent Production System` - 14 edges
5. `Verification & Production Readiness Plan` - 12 edges
6. `get_connection()` - 9 edges
7. `_temp_db()` - 7 edges
8. `Verification Hierarchy (Unit to Release Gate)` - 7 edges
9. `P1 Vertical Slice` - 7 edges
10. `P2 MVP` - 7 edges

## Surprising Connections (you probably didn't know these)
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P0 Foundation`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `DEC-001: Web-first MVP, Tauri post-MVP` --references--> `P3 V1`  [INFERRED]
  ai/DECISIONS.md → docs/Implementation Roadmap.md
- `P2 MVP` --references--> `Analysis Planner`  [INFERRED]
  docs/Implementation Roadmap.md → docs/Product & Engineering Master Specification.md
- `web/index.html (React entry point)` --references--> `Web-First Delivery Strategy (Tauri post-MVP)`  [INFERRED]
  web/index.html → docs/Product & Engineering Master Specification.md
- `Locked tech selections (FastAPI/SQLite/DuckDB)` --implements--> `Control-Layer Architecture`  [INFERRED]
  ai/DECISIONS.md → docs/Product & Engineering Master Specification.md

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **P0 Verification System: gate + state + report** — verification_p0_report, ai_current_state, ai_tasks, ai_handoff [INFERRED 0.90]

## Communities (16 total, 1 thin omitted)

### Community 0 - "Product Spec & Decisions"
Cohesion: 0.09
Nodes (24): AGENTS.md graphify guidance, API-only frontend contract, DEC-001: Web-first MVP, Tauri post-MVP, Locked tech selections (FastAPI/SQLite/DuckDB), Core Analytical Loop: Question to Finding, Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), AI Context Strategy (+16 more)

### Community 1 - "FastAPI Core Endpoints"
Cohesion: 0.13
Nodes (18): BaseModel, get, post, profile_csv(), DuckDB analytical engine - the seed of the Data & Evidence Engine. Analytical…, Profile a CSV: row count and column names. The path is bound as a parameter,…, create_case(), get_case() (+10 more)

### Community 2 - "Web Toolchain & Dependencies"
Cohesion: 0.10
Nodes (19): jsdom, react-dom, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react, dependencies (+11 more)

### Community 3 - "TypeScript Config"
Cohesion: 0.11
Nodes (18): compilerOptions, allowImportingTsExtensions, isolatedModules, jsx, lib, module, moduleDetection, moduleResolution (+10 more)

### Community 4 - "Agent Build Protocol & State"
Cohesion: 0.14
Nodes (12): Coding-Agent Production System, Agent Implementation Protocol, Artifact Authority Hierarchy, Agent Control Loop: PLAN to EXIT-CRITERIA, Development Context Protocol, Development State Model, Hard Stop Conditions, Persistent Project State (/ai documents) (+4 more)

### Community 5 - "SQLite Persistence Layer"
Cohesion: 0.20
Nodes (13): Connection, get_connection(), Path, SQLite persistence for Analysis Cases. Owns case STATE only. Analytical queries…, Open a connection, ensuring the schema exists, and commit on success., get_db(), The golden test: a case survives being saved and reopened., Point the app at a fresh on-disk SQLite file for this test. (+5 more)

### Community 6 - "Roadmap & Milestones"
Cohesion: 0.29
Nodes (15): Milestone Exit Criteria (P0-P5), Implementation Roadmap, Feature Priority Model (M/S/C/L), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate (+7 more)

### Community 7 - "React UI & API Client"
Cohesion: 0.22
Nodes (10): react, @testing-library/react, vitest, createCase(), getHealth(), Health, NewCase, App() (+2 more)

### Community 8 - "P0 Verification Harness"
Cohesion: 0.36
Nodes (9): Popen, log(), main(), Path, P0 Foundation milestone verification. Runs the P0 exit-test sequence as one…, request(), run_tests(), start_server() (+1 more)

### Community 9 - "Verification & Quality Gates"
Cohesion: 0.22
Nodes (9): Verification & Production Readiness Plan, AI Evaluation Dataset, AI Safety Rules, Data Trust Rules (Observed/Calculated/Inferred/...), Golden Datasets and Golden Analytical Tests, Production Readiness Checklist, Release Decision Matrix, Defect Severity Model (P0-P3) (+1 more)

### Community 10 - "Web Dev Dependencies"
Cohesion: 0.22
Nodes (9): devDependencies, jsdom, @testing-library/react, @types/react, @types/react-dom, typescript, vite, @vitejs/plugin-react (+1 more)

### Community 11 - "Test Setup"
Cohesion: 0.40
Nodes (3): devDependencies, @testing-library/jest-dom, @testing-library/jest-dom

## Knowledge Gaps
- **58 isolated node(s):** `@testing-library/jest-dom`, `dah-server`, `name`, `private`, `version` (+53 more)
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 96 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Product & Engineering Master Specification` connect `Product Spec & Decisions` to `Verification & Quality Gates`, `Agent Build Protocol & State`, `Roadmap & Milestones`?**
  _High betweenness centrality (0.058) - this node is a cross-community bridge._
- **Why does `Coding-Agent Production System` connect `Agent Build Protocol & State` to `Product Spec & Decisions`, `Verification & Quality Gates`, `Roadmap & Milestones`?**
  _High betweenness centrality (0.041) - this node is a cross-community bridge._
- **Why does `Implementation Roadmap` connect `Roadmap & Milestones` to `Product Spec & Decisions`, `Verification & Quality Gates`, `Agent Build Protocol & State`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **What connects `@testing-library/jest-dom`, `dah-server`, `name` to the rest of the system?**
  _58 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Product Spec & Decisions` be split into smaller, more focused modules?**
  _Cohesion score 0.09333333333333334 - nodes in this community are weakly interconnected._
- **Should `FastAPI Core Endpoints` be split into smaller, more focused modules?**
  _Cohesion score 0.12681159420289856 - nodes in this community are weakly interconnected._
- **Should `Web Toolchain & Dependencies` be split into smaller, more focused modules?**
  _Cohesion score 0.1 - nodes in this community are weakly interconnected._