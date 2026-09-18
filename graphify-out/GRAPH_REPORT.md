# Graph Report - DA-Harness  (2026-09-18)

## Corpus Check
- Corpus is ~9,442 words - fits in a single context window. You may not need a graph.

## Summary
- 56 nodes · 100 edges · 8 communities (7 shown, 1 thin omitted)
- Extraction: 65% EXTRACTED · 35% INFERRED · 0% AMBIGUOUS · INFERRED: 35 edges (avg confidence: 0.92)
- Token cost: 14,500 input · 5,200 output

## Community Hubs (Navigation)
- Product Architecture & AI Principles
- Milestones & Trust Chain
- Roadmap Strategy & Phases
- Verification & Quality Gates
- Agent Build Protocol
- Constraints & Guardrails
- Task Definition
- Context Budgeting

## God Nodes (most connected - your core abstractions)
1. `Product & Engineering Master Specification` - 19 edges
2. `Implementation Roadmap` - 17 edges
3. `Coding-Agent Production System` - 16 edges
4. `Verification & Production Readiness Plan` - 12 edges
5. `Verification Hierarchy (Unit to Release Gate)` - 11 edges
6. `Milestone Exit Criteria (P0-P5)` - 9 edges
7. `P2 MVP` - 7 edges
8. `P1 Vertical Slice` - 6 edges
9. `P5 Production Grade` - 6 edges
10. `P3 V1` - 5 edges

## Surprising Connections (you probably didn't know these)
- `Milestone Exit Criteria (P0-P5)` --semantically_similar_to--> `Verification Gates A-H`  [INFERRED] [semantically similar]
  docs/Coding-Agent Production System.md → docs/Implementation Roadmap.md
- `P2 MVP` --references--> `Analysis Planner`  [INFERRED]
  docs/Implementation Roadmap.md → docs/Product & Engineering Master Specification.md
- `Reproducibility Model` --conceptually_related_to--> `Verification Hierarchy (Unit to Release Gate)`  [INFERRED]
  docs/Product & Engineering Master Specification.md → docs/Verification & Production Readiness Plan.md
- `Agent Control Loop: PLAN to EXIT-CRITERIA` --conceptually_related_to--> `Verification Hierarchy (Unit to Release Gate)`  [INFERRED]
  docs/Coding-Agent Production System.md → docs/Verification & Production Readiness Plan.md
- `Milestone Exit Criteria (P0-P5)` --references--> `Release Decision Matrix`  [INFERRED]
  docs/Coding-Agent Production System.md → docs/Verification & Production Readiness Plan.md

## Hyperedges (group relationships)
- **Four-Artifact Development Control System** — docs_product___engineering_master_specification, docs_implementation_roadmap, docs_coding_agent_production_system, docs_verification___production_readiness_plan [INFERRED 0.95]
- **Analytical Trust Chain: Case -> Evidence -> Validation** — docs_product___engineering_master_specification_analysis_case, docs_product___engineering_master_specification_evidence_system, docs_product___engineering_master_specification_validation_engine [INFERRED 0.90]
- **Milestone Gate System** — docs_implementation_roadmap_verification_gates, docs_coding_agent_production_system_milestone_exit_criteria, docs_verification___production_readiness_plan_verification_hierarchy [INFERRED 0.90]

## Communities (8 total, 1 thin omitted)

### Community 0 - "Product Architecture & AI Principles"
Cohesion: 0.22
Nodes (11): Product & Engineering Master Specification, AI Architecture Principles (bounded AI responsibility), Analysis Memory, Analysis Planner, Analysis Workspace (SQL/Python/stats/charts), Control-Layer Architecture, Data & Evidence Engine, Deterministic Core Principle (+3 more)

### Community 1 - "Milestones & Trust Chain"
Cohesion: 0.44
Nodes (10): Milestone Exit Criteria (P0-P5), P0 Foundation, P1 Vertical Slice, P2 MVP, P3 V1, P4 Production Candidate, Analysis Case, Evidence System (claim-to-source traceability) (+2 more)

### Community 2 - "Roadmap Strategy & Phases"
Cohesion: 0.24
Nodes (10): Implementation Roadmap, Core Analytical Loop: Question to Finding, Feature Priority Model (M/S/C/L), P5 Production Grade, P6 Post-Launch Evolution, Token-Budget Strategy, Verification Gates A-H, Vertical-Slice Strategy (+2 more)

### Community 3 - "Verification & Quality Gates"
Cohesion: 0.22
Nodes (9): AI Context Strategy, Quality Model and Finding Statuses, Verification & Production Readiness Plan, AI Evaluation Dataset, Data Trust Rules (Observed/Calculated/Inferred/...), Golden Datasets and Golden Analytical Tests, Release Decision Matrix, Defect Severity Model (P0-P3) (+1 more)

### Community 4 - "Agent Build Protocol"
Cohesion: 0.25
Nodes (8): Coding-Agent Production System, Agent Implementation Protocol, Artifact Authority Hierarchy, Agent Control Loop: PLAN to EXIT-CRITERIA, Development State Model, Task Priority Rules, Task Size Rule, Three Control Artifacts (00/10/11)

### Community 5 - "Constraints & Guardrails"
Cohesion: 0.67
Nodes (3): Hard Stop Conditions, Persistent Project State (/ai documents), Master Development Constraints R1-R8

### Community 6 - "Task Definition"
Cohesion: 0.67
Nodes (3): Task Contract, Task Decomposition: Milestone to Capability to Task, Milestone Definition

## Knowledge Gaps
- **5 isolated node(s):** `Data & Evidence Engine`, `Analysis Memory`, `Feature Priority Model (M/S/C/L)`, `Golden Datasets and Golden Analytical Tests`, `Test Pyramid`
  These have ≤1 connection - possible missing edges or undocumented components. (Counts symbols only; 14 node(s) total have ≤1 connection when file, concept and rationale nodes are included.)
- **1 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `Product & Engineering Master Specification` connect `Product Architecture & AI Principles` to `Milestones & Trust Chain`, `Roadmap Strategy & Phases`, `Verification & Quality Gates`, `Agent Build Protocol`, `Constraints & Guardrails`?**
  _High betweenness centrality (0.423) - this node is a cross-community bridge._
- **Why does `Coding-Agent Production System` connect `Agent Build Protocol` to `Product Architecture & AI Principles`, `Milestones & Trust Chain`, `Roadmap Strategy & Phases`, `Verification & Quality Gates`, `Constraints & Guardrails`, `Task Definition`, `Context Budgeting`?**
  _High betweenness centrality (0.366) - this node is a cross-community bridge._
- **Why does `Implementation Roadmap` connect `Roadmap Strategy & Phases` to `Product Architecture & AI Principles`, `Milestones & Trust Chain`, `Verification & Quality Gates`, `Agent Build Protocol`, `Task Definition`, `Context Budgeting`?**
  _High betweenness centrality (0.320) - this node is a cross-community bridge._
- **Are the 10 inferred relationships involving `Verification Hierarchy (Unit to Release Gate)` (e.g. with `Agent Control Loop: PLAN to EXIT-CRITERIA` and `Evidence System (claim-to-source traceability)`) actually correct?**
  _`Verification Hierarchy (Unit to Release Gate)` has 10 INFERRED edges - model-reasoned connections that need verification._
- **What connects `Data & Evidence Engine`, `Analysis Memory`, `Feature Priority Model (M/S/C/L)` to the rest of the system?**
  _5 weakly-connected nodes found - possible documentation gaps or missing edges._