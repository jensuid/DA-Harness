# Data Analysis Harness

## Product & Engineering Master Specification

**Version:** 1.0  
**Status:** Master Source of Truth  
**Product Type:** Analytical Operating System / Analytical Control Layer  
**Primary Goal:** Turn ambiguous analytical problems into structured, trustworthy, reproducible, decision-ready analysis.

---

# 1. Product Definition

## 1.1 One-line definition

> **Data Analysis Harness (DAH) is a system that guides humans and AI through a structured analytical process—from purpose and question to evidence, validation, insight, and decision support.**

## 1.2 Core idea

Traditional analytical tools focus on **performing analysis**.

DAH focuses on **controlling the analytical process**.

```text
Purpose
  ↓
Question
  ↓
Context
  ↓
Data
  ↓
Quality
  ↓
Analysis
  ↓
Validation
  ↓
Evidence
  ↓
Insight
  ↓
Decision
```

The Harness remains stable while analytical tools can change.

```text
DAH
 │
 ├── SQL
 ├── Python
 ├── Statistics
 ├── ML
 ├── BI
 ├── AI
 └── Data Sources
```

---

# 2. Product Vision

## Vision

> Make high-quality analytical thinking easier, more systematic, inspectable, and reproducible for humans and AI.

## Long-term vision

DAH becomes an **analytical operating system** that can coordinate:

- humans
    
- AI agents
    
- data
    
- analytical engines
    
- evidence
    
- validation
    
- organizational knowledge
    

to produce trustworthy analysis.

---

# 3. Problem

Modern analysts have powerful tools but the analytical process is often fragmented.

```text
Question → Chat
Data → SQL
Analysis → Python
Visualization → BI
Documentation → Slides
Reasoning → Human memory
Validation → Manual
```

This creates problems:

- unclear questions
    
- weak assumptions
    
- poor data understanding
    
- inconsistent methodology
    
- unsupported conclusions
    
- difficult reproduction
    
- fragmented analytical context
    
- AI-generated analysis that may look convincing but is poorly validated
    

DAH addresses the **process gap between tools and trustworthy decisions**.

---

# 4. Target Users

## Primary

### Data Analysts

Need to:

- structure problems
    
- explore data
    
- investigate drivers
    
- validate findings
    
- communicate evidence
    

### AI-assisted Analysts

Need AI to help with:

- planning
    
- SQL/Python generation
    
- exploration
    
- interpretation
    
- documentation
    

without losing analytical control.

## Secondary

- Product analysts
    
- Business analysts
    
- Data scientists
    
- Researchers
    
- Managers performing data-driven investigations
    
- Teams evaluating AI-generated analysis
    

---

# 5. Jobs-to-be-Done

DAH should help users:

### Before analysis

> “Help me understand what I actually need to investigate.”

### During analysis

> “Help me perform the right analysis without losing context.”

### After analysis

> “Show me whether my conclusions are actually supported.”

### For future work

> “Let me reproduce and reuse what we learned.”

---

# 6. Core Product Principle

> **AI proposes. Analytical engines compute. The Harness records. Validation checks. Humans decide.**

This separates probabilistic AI behavior from deterministic analytical operations.

---

# 7. Core Mental Model

DAH is organized around four major layers.

```text
┌─────────────────────────────────────────┐
│            DECISION LAYER               │
│ Insight → Evidence → Uncertainty → Action│
├─────────────────────────────────────────┤
│            ANALYSIS LAYER               │
│ EDA → Statistics → Modeling → Viz       │
├─────────────────────────────────────────┤
│            EVIDENCE LAYER               │
│ Data → Quality → Semantics → Provenance │
├─────────────────────────────────────────┤
│             HARNESS LAYER               │
│ Purpose → Question → Context → Method   │
└─────────────────────────────────────────┘
```

---

# 8. Core Analytical Workflow

## Stage 1 — Purpose

Define:

- Why is this analysis needed?
    
- What decision will it inform?
    
- Who will use it?
    

## Stage 2 — Question

Convert the problem into answerable analytical questions.

## Stage 3 — Context

Capture:

- business/domain meaning
    
- definitions
    
- constraints
    
- timing
    
- relevant prior knowledge
    

## Stage 4 — Data

Identify:

- available datasets
    
- sources
    
- grain
    
- coverage
    
- relevant fields
    
- relationships
    

## Stage 5 — Quality

Check whether the data is trustworthy enough.

## Stage 6 — Analysis

Perform appropriate:

- EDA
    
- comparisons
    
- statistics
    
- segmentation
    
- modeling
    
- visualization
    

## Stage 7 — Validation

Check:

- calculations
    
- assumptions
    
- comparisons
    
- evidence
    
- alternative explanations
    
- limitations
    

## Stage 8 — Insight

Translate validated evidence into meaningful findings.

## Stage 9 — Decision

Explain:

- implications
    
- options
    
- uncertainty
    
- required follow-up
    

DAH informs decisions; **it does not make political, business, or other consequential decisions on behalf of users.**

---

# 9. Fundamental Product Object

## Analysis Case

The central object of DAH is an **Analysis Case**.

An Analysis Case is a persistent representation of one analytical investigation.

```text
Analysis Case
│
├── Purpose
├── Context
├── Questions
├── Hypotheses
├── Data Sources
├── Metric Definitions
├── Data Quality
├── Analysis Plan
├── Analysis Runs
├── Evidence
├── Findings
├── Validation
├── Assumptions
├── Uncertainty
├── Limitations
├── Decision Implications
└── Reproducibility
```

### Fundamental equation

> **Analysis Case = Question + Context + Evidence + Method + Computation + Validation + Findings**

The Analysis Case is more fundamental than a dashboard, notebook, or chat conversation.

---

# 10. Core Product Components

## 10.1 Analysis Planner

Transforms:

> “Revenue declined. Find out why.”

into:

```text
Objective
 ↓
Primary Question
 ↓
Sub-questions
 ↓
Hypotheses
 ↓
Data Requirements
 ↓
Analysis Plan
 ↓
Validation Plan
```

---

## 10.2 Data & Evidence Engine

Understands the available data.

Checks:

- schema
    
- data types
    
- grain
    
- missingness
    
- duplicates
    
- distributions
    
- outliers
    
- freshness
    
- coverage
    
- relationships
    
- join risks
    
- metric definitions
    
- source authority
    

Core question:

> **Can this data answer this question?**

---

## 10.3 Analysis Workspace

Provides controlled access to analytical tools:

- SQL
    
- Python
    
- statistics
    
- tables
    
- charts
    
- ML
    
- AI assistance
    

DAH does not need to replace every analytical tool.

---

## 10.4 Evidence System

Every important finding should have traceability.

```text
Finding
  ↓
Evidence
  ↓
Calculation
  ↓
Query / Code
  ↓
Dataset
```

A user should be able to ask:

> “Where did this conclusion come from?”

and trace it back to the underlying computation and data.

---

## 10.5 Validation Engine

Evaluates analytical claims.

Example:

> “Customers exposed to price increases churned more.”

The system should distinguish:

```text
Observed difference
      ↓
Statistical evidence
      ↓
Association
      ↓
Alternative explanations
      ↓
Causal evidence
```

The system must not automatically turn correlation into causation.

---

## 10.6 Analysis Memory

Stores reusable knowledge:

- metric definitions
    
- data sources
    
- SQL
    
- previous findings
    
- known caveats
    
- business rules
    
- analytical history
    

Future cases can reuse validated context.

---

# 11. Product Modes

## LEARN

Teach the analytical process.

```text
Why
 ↓
What
 ↓
How
 ↓
Validate
```

## ANALYZE

Collaborative human + AI analysis.

```text
Problem
 ↓
Harness
 ↓
AI + Tools
 ↓
Analysis
 ↓
Validation
 ↓
Findings
```

## EVALUATE

Audit existing analytical work.

Inputs can include:

- SQL
    
- Python
    
- notebook
    
- dashboard
    
- spreadsheet
    
- report
    
- AI-generated analysis
    

Evaluate:

```text
Question
Data
Quality
Method
Calculation
Evidence
Claim
Visualization
Limitations
```

---

# 12. MVP Definition

## MVP goal

Prove that DAH can turn a messy analytical question and dataset into a structured, validated Analysis Case.

## MVP core workflow

```text
Question
   +
Dataset
   ↓
Analysis Case
   ↓
Data Profiling
   ↓
AI Analysis Plan
   ↓
User Executes Analysis
   ↓
Evidence
   ↓
Validation
   ↓
Findings
   ↓
Exportable Case
```

## Initial supported data

Start with:

- CSV
    
- Parquet
    
- Excel
    

## Initial analytical capabilities

- data profiling
    
- SQL
    
- basic Python
    
- basic statistics
    
- tables
    
- essential charts
    
- AI planning
    
- evidence tracking
    
- basic validation
    
- case persistence
    
- export
    

---

# 13. Explicit Non-Goals for MVP

Do not initially build:

- enterprise data warehouse platform
    
- full BI replacement
    
- full notebook replacement
    
- autonomous multi-agent system
    
- dozens of database connectors
    
- enterprise collaboration
    
- real-time streaming
    
- complex ML platform
    
- enterprise permission system
    
- cloud-scale infrastructure
    
- complete knowledge graph
    

These belong to later stages.

---

# 14. Product Boundary

## DAH owns

- analytical workflow
    
- analysis state
    
- context
    
- planning
    
- evidence
    
- validation
    
- reproducibility
    
- analytical memory
    

## External engines may own

- data storage
    
- SQL execution
    
- Python execution
    
- ML computation
    
- visualization
    
- LLM inference
    
- enterprise BI
    

This creates a **control-layer architecture** rather than another all-in-one analytics platform.

---

# 15. Technical Architecture

Recommended initial architecture:

```text
┌─────────────────────────────┐
│     React + Vite (web)      │
│                             │
│ Case UI                     │
│ Data UI                     │
│ Analysis Workspace          │
│ Evidence UI                 │
│ Validation UI               │
│ AI Assistant                │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│         Harness Core        │
│                             │
│ Case State                  │
│ Planner                     │
│ Evidence                    │
│ Validation                  │
│ Orchestration               │
└──────────────┬──────────────┘
               ↓
┌─────────────────────────────┐
│        Python Engine        │
│                             │
│ Profiling                   │
│ SQL/Data Processing         │
│ Statistics                  │
│ Analysis                    │
└──────────────┬──────────────┘
               ↓
       ┌───────┴────────┐
       ↓                ↓
    DuckDB           Files
```

AI operates through controlled interfaces with the Harness.

### Delivery strategy — web-first

The MVP runs as a **browser-served web application** (React + Vite) backed by a local
Python API. The desktop shell arrives **after the MVP**, when the same React bundle is
wrapped in Tauri with the Python core as a sidecar. The frontend must therefore never
touch the filesystem or DuckDB directly — only through the API — so the move to Tauri
requires no frontend rewrite.

---

# 16. Technology Principles

## Principle 1 — Local-first execution, web-first delivery

MVP keeps execution local while shipping as a web application:

- local files
    
- DuckDB for analytical queries
    
- SQLite for Analysis Case state
    
- Python (FastAPI) as the local core
    
- Analysis Cases stored on the local machine
    

Benefits:

- simpler architecture
    
- lower infrastructure cost
    
- easier development
    
- better privacy
    
- easier offline workflows
    

## Principle 2 — Modular engines

Data, AI, validation, and visualization should have replaceable interfaces.

## Principle 3 — Deterministic core

Critical calculations and state transitions should not depend on LLM output.

## Principle 4 — Inspectability

Users should be able to inspect:

- data
    
- queries
    
- code
    
- calculations
    
- evidence
    
- assumptions
    

## Principle 5 — Reproducibility

Important findings should be reproducible from recorded inputs and computations.

---

# 17. AI Architecture Principles

AI should have bounded responsibilities.

### AI can:

- clarify questions
    
- generate hypotheses
    
- suggest analyses
    
- generate SQL/Python
    
- explain results
    
- identify possible caveats
    
- draft findings
    
- summarize cases
    

### AI should not silently:

- invent data
    
- change analytical state without traceability
    
- fabricate evidence
    
- treat correlation as causation
    
- hide uncertainty
    
- overwrite validated findings
    
- make consequential decisions autonomously
    

---

# 18. AI Context Strategy

The entire project and entire Analysis Case should not be sent to the LLM every time.

Use task-specific context.

```text
Analysis State
      ↓
Relevant Context Selection
      ↓
AI Task Context
      ↓
LLM
      ↓
Structured Output
      ↓
Harness Validation
      ↓
Persisted State
```

This improves:

- token efficiency
    
- reliability
    
- consistency
    
- debugging
    
- coding-agent compatibility
    

---

# 19. Data Model — Initial Core Entities

```text
AnalysisCase
Question
Hypothesis
Dataset
Metric
QualityFinding
AnalysisPlan
AnalysisRun
Result
Evidence
Finding
Validation
Assumption
DecisionImplication
```

Relationships:

```text
AnalysisCase
 ├── Questions
 ├── Hypotheses
 ├── Datasets
 ├── AnalysisRuns
 │     └── Results
 ├── Evidence
 ├── Findings
 │     └── Validation
 └── DecisionImplications
```

---

# 20. UX Principle

The application should feel like an **analytical workspace**, not a chatbot.

Primary navigation should expose the analytical journey:

```text
Case
Question
Data
Explore
Analyze
Validate
Findings
```

The AI assistant should be contextual to the current stage.

Avoid making:

> “Chat with your data”

the primary product metaphor.

Instead:

> **“Work through an analysis with AI assistance.”**

---

# 21. Quality Model

Every important conclusion should be evaluated across:

```text
Question
   ↓
Data
   ↓
Quality
   ↓
Method
   ↓
Calculation
   ↓
Evidence
   ↓
Claim
   ↓
Validation
   ↓
Uncertainty
```

### Quality statuses

Use simple states:

- **Supported**
    
- **Partially supported**
    
- **Insufficient evidence**
    
- **Contradicted**
    
- **Not evaluated**
    

Avoid presenting AI confidence as equivalent to analytical evidence.

---

# 22. Security & Trust Principles

Production design should include:

- explicit data boundaries
    
- safe code execution
    
- permission controls
    
- secrets management
    
- dependency auditing
    
- input validation
    
- sandboxing where required
    
- audit logs
    
- clear AI/data provenance
    
- protection against prompt injection from data content
    

AI-generated code must be treated as **untrusted input** until validated and executed within appropriate controls.

---

# 23. Reproducibility Model

An Analysis Case should preserve enough information to reproduce important findings.

```text
Case
 ↓
Dataset reference
 ↓
Data snapshot / version
 ↓
Query / Code
 ↓
Execution
 ↓
Result
 ↓
Finding
 ↓
Validation
```

Export should eventually produce an analytical package containing:

- case metadata
    
- data references
    
- SQL
    
- Python
    
- results
    
- charts
    
- findings
    
- validation
    
- assumptions
    
- limitations
    

---

# 24. Product Evolution

```text
LEVEL 1
Analysis Case Builder
        ↓
LEVEL 2
AI Analysis Workbench
        ↓
LEVEL 3
Evidence + Validation System
        ↓
LEVEL 4
Analysis Memory
        ↓
LEVEL 5
Agentic Analysis
        ↓
LEVEL 6
Analytical Operating System
```

Each level should be useful independently.

---

# 25. Development Strategy

Build using **vertical slices**, not large technical layers.

First prove:

```text
Question
 ↓
Dataset
 ↓
Profile
 ↓
Plan
 ↓
Analysis
 ↓
Evidence
 ↓
Validation
 ↓
Finding
```

Then expand capabilities around this working loop.

---

# 26. Coding-Agent Development Principle

The coding agent should never be asked:

> “Build the whole DAH.”

Instead:

```text
Master Specification
        ↓
Implementation Roadmap
        ↓
One Milestone
        ↓
One Task
        ↓
Relevant Context
        ↓
Implementation
        ↓
Tests
        ↓
Verification
        ↓
State Update
```

This minimizes context and token consumption.

---

# 27. Master Development Constraints

The project should follow these rules:

### R1 — Scope before code

No feature should be implemented without a defined purpose.

### R2 — Architecture before complexity

New components require a clear responsibility.

### R3 — Small tasks

Coding-agent tasks should be independently implementable and verifiable.

### R4 — Test continuously

Do not accumulate large untested changes.

### R5 — Preserve interfaces

Avoid unnecessary changes across unrelated modules.

### R6 — Record decisions

Important architectural decisions must be documented.

### R7 — Maintain current state

The repository must always expose what is completed, active, blocked, and next.

### R8 — Human approval for consequential changes

AI may propose; humans approve important product, architecture, and analytical decisions.

---

# 28. Production-Grade Definition

DAH is not production-ready merely because the features work.

Production readiness requires:

```text
Functional
+
Correct
+
Tested
+
Secure
+
Reliable
+
Performant
+
Usable
+
Observable
+
Reproducible
+
Maintainable
```

Specific verification areas:

- functional testing
    
- unit testing
    
- integration testing
    
- data correctness
    
- AI evaluation
    
- security testing
    
- error handling
    
- performance
    
- UX
    
- accessibility
    
- packaging
    
- upgrade/recovery
    
- documentation
    

---

# 29. Success Criteria

The core product succeeds when a user can:

1. Start with a vague analytical problem.
    
2. Define a useful question.
    
3. Understand the available data.
    
4. Detect important data-quality issues.
    
5. Generate a reasonable analysis plan.
    
6. Execute analysis using appropriate tools.
    
7. Connect findings to evidence.
    
8. Validate important claims.
    
9. Clearly communicate uncertainty.
    
10. Reproduce the analysis later.
    

### Core product metric

> **Time and effort required to produce a trustworthy Analysis Case from an ambiguous analytical problem.**

---

# 30. Strategic Differentiation

DAH should not compete primarily on:

- number of charts
    
- number of connectors
    
- LLM chat quality
    
- SQL generation alone
    
- dashboard aesthetics
    

Its differentiation should be:

```text
Structured analytical state
+
Evidence traceability
+
Validation
+
Reproducibility
+
AI inside an explicit analytical process
```

### Positioning

> **DAH is the analytical control layer that makes AI-assisted analysis structured, inspectable, validated, and reusable.**

---

# 31. Product North Star

The entire product can be reduced to:

> **From Question → to Evidence → to Trustworthy Insight.**

And the architectural principle:

> **The Harness owns the process; tools perform the work; AI assists the reasoning; evidence supports the claims.**

---

# 32. Master Scope Boundary

### Build now

```text
Analysis Case
Data ingestion
Profiling
Question planning
SQL/Python analysis
Evidence
Validation
Findings
Persistence
Export
```

### Build later

```text
Advanced AI analyst
Memory
Connectors
Agent orchestration
Collaboration
Cloud
Enterprise
```

### Never lose

```text
Purpose
Question
Context
Evidence
Validation
Reproducibility
Human control
```

These are the permanent foundations of the product.

---

# 33. Relationship to the Remaining Master Artifacts

This specification is the **source of truth**.

```text
00 MASTER SPECIFICATION
        │
        ├──── defines WHAT
        │
        ↓
10 IMPLEMENTATION ROADMAP
        │
        ├──── defines WHEN / ORDER
        │
        ↓
11 CODING-AGENT PRODUCTION SYSTEM
        │
        ├──── defines HOW TO BUILD
        │
        ↓
       CODE
        │
        ↓
12 VERIFICATION & PRODUCTION READINESS
        │
        └──── proves WHETHER IT IS READY
```

Supporting specifications provide the required detail without changing the fundamental product thesis.

---

# 34. Final Product Definition

> **Data Analysis Harness is a local-first, AI-assisted analytical workspace that transforms an ambiguous data problem into a structured Analysis Case containing the question, context, data, analysis, evidence, validation, findings, uncertainty, and reproducibility information needed for trustworthy decision support.**

**Core object:** Analysis Case  
**Core workflow:** Purpose → Question → Context → Data → Quality → Analysis → Validation → Insight → Decision  
**Core differentiator:** Analytical control rather than generic AI analysis  
**Initial platform:** React (web) + FastAPI + Python + DuckDB + SQLite  
**Desktop platform (post-MVP):** Tauri wraps the same React bundle  
**Initial strategy:** Narrow vertical slice → MVP → progressive expansion  
**AI principle:** AI assists; the Harness controls; computation is inspectable; evidence is traceable; humans remain in control.