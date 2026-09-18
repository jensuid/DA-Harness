# Data Analysis Harness

## Implementation Roadmap

**Version:** 1.0  
**Purpose:** Convert the Master Specification into a concrete, staged path from MVP to production-grade application.

---

# 1. Roadmap Strategy

Build the product through **vertical slices**, not by attempting the complete platform at once.

The core loop must work first:

```text
Question
   ↓
Data
   ↓
Profile
   ↓
Plan
   ↓
Analyze
   ↓
Evidence
   ↓
Validate
   ↓
Finding
```

Then progressively increase:

```text
Capability
 → Reliability
 → AI assistance
 → Memory
 → Integrations
 → Automation
 → Production scale
```

---

# 2. Development Phases

```text
P0 Foundation
      ↓
P1 Vertical Slice
      ↓
P2 MVP
      ↓
P3 V1
      ↓
P4 Production Candidate
      ↓
P5 Production Grade
      ↓
P6 Post-Launch Evolution
```

---

# 3. P0 — Foundation

## Goal

Create a stable development foundation before implementing analytical features.

### Build

```text
Repository
React (web) + Vite
Python backend (FastAPI)
Project structure
Application shell
State architecture
Basic persistence
Testing infrastructure
AI development protocol
```

### Outputs

- runnable web application
    
- frontend/backend communication
    
- repository conventions
    
- basic test framework
    
- initial domain model
    
- development documentation
    

### Gate

The application can:

> **Start → communicate across layers → persist basic state → run tests.**

---

# 4. P1 — Core Vertical Slice

## Goal

Prove the fundamental DAH concept with the smallest useful workflow.

### User journey

```text
Create Analysis Case
       ↓
Enter Question
       ↓
Load CSV
       ↓
Profile Data
       ↓
Generate Analysis Plan
       ↓
Run Simple Analysis
       ↓
Create Finding
       ↓
Attach Evidence
       ↓
Validate Finding
       ↓
Save Case
```

### Build only enough functionality to demonstrate this loop.

### Example

Input:

> “Why did revenue decline?”

Dataset:

```text
sales.csv
```

Output:

```text
Analysis Case
├── Question
├── Dataset
├── Data Profile
├── Analysis Plan
├── Result
├── Evidence
├── Finding
└── Validation
```

### Gate

A real user can complete one complete analytical case from beginning to end.

---

# 5. P2 — MVP

## Goal

Turn the vertical slice into a genuinely usable analytical application.

### 5.1 Analysis Case

Support:

- create
    
- open
    
- save
    
- rename
    
- duplicate
    
- delete
    
- export
    

---

### 5.2 Data Layer

Initial support:

- CSV
    
- Parquet
    
- Excel
    

Add:

- schema detection
    
- profiling
    
- missingness
    
- duplicates
    
- data types
    
- distributions
    
- basic statistics
    
- data-quality findings
    

---

### 5.3 Analysis Workspace

Support:

- SQL
    
- Python
    
- result tables
    
- essential charts
    
- execution history
    

Use DuckDB as the initial analytical engine where appropriate.

---

### 5.4 AI Planning

AI assists with:

- question refinement
    
- sub-question generation
    
- hypotheses
    
- analysis suggestions
    
- validation suggestions
    

AI output should be structured rather than uncontrolled prose.

---

### 5.5 Evidence

Every important result should connect:

```text
Finding
 ↓
Result
 ↓
Query / Code
 ↓
Dataset
```

---

### 5.6 Validation

Initial validation should check:

- calculation reproducibility
    
- denominator
    
- comparison population
    
- missing data
    
- obvious contradictions
    
- unsupported causal claims
    
- important assumptions
    

---

### 5.7 Findings

Allow users to record:

- finding
    
- supporting evidence
    
- interpretation
    
- caveat
    
- validation status
    

---

### MVP Gate

A user can answer a real analytical question and produce a **structured Analysis Case that another person can inspect and reproduce**.

---

# 6. P3 — V1

## Goal

Make the MVP substantially better for repeated real-world use.

### Add

#### Analysis workflow

- guided workflow
    
- stage completion
    
- recommendations
    
- dependencies
    
- analysis history
    

#### Data

- multiple datasets
    
- joins
    
- relationships
    
- data-source metadata
    
- better quality diagnostics
    

#### Analysis

- richer EDA
    
- segmentation
    
- statistical tests
    
- reusable analysis components
    
- better visualization
    

#### AI

- contextual AI assistant
    
- code generation
    
- result interpretation
    
- next-analysis suggestions
    
- finding drafting
    

#### Evidence

- richer lineage
    
- evidence graph
    
- claim-to-source tracing
    

#### Case management

- templates
    
- search
    
- case history
    
- reusable components
    

### V1 Gate

A regular analyst can use DAH for **multiple analytical investigations**, not merely a demo.

---

# 7. P4 — Production Candidate

## Goal

Move from “working application” to “serious software.”

### Reliability

Implement:

- robust error handling
    
- recovery
    
- cancellation
    
- long-running task handling
    
- corrupted-case protection
    
- safe application shutdown
    

### Security

Implement:

- safe file handling
    
- sandboxed code execution where appropriate
    
- dependency auditing
    
- secret protection
    
- input validation
    
- AI-generated-code safeguards
    
- prompt-injection defenses
    

### Performance

Test:

- large datasets
    
- large Analysis Cases
    
- repeated queries
    
- multiple charts
    
- long AI interactions
    

Identify acceptable limits.

### UX

Improve:

- onboarding
    
- empty states
    
- errors
    
- progress indicators
    
- discoverability
    
- accessibility
    
- keyboard workflows
    

### Observability

Track application health without unnecessarily collecting user data.

### Gate

The application is stable enough for controlled external users.

---

# 8. P5 — Production Grade

## Goal

Create a maintainable, distributable, secure product.

### Product

- polished onboarding
    
- settings
    
- project management
    
- import/export
    
- recovery
    
- documentation
    
- help system
    

### Engineering

- automated CI
    
- release pipeline
    
- versioning
    
- migrations
    
- crash/error reporting
    
- dependency management
    
- automated regression tests
    

### Security

- threat model
    
- security review
    
- dependency scanning
    
- secure update mechanism
    
- sensitive-data handling
    
- permission model where needed
    

### AI

- model abstraction
    
- provider configuration
    
- prompt/version management
    
- AI evaluation suite
    
- hallucination tests
    
- structured-output validation
    
- cost/token monitoring
    

### Data

- larger dataset handling
    
- robust execution
    
- schema evolution
    
- connector architecture
    

### Distribution

- macOS packaging
    
- code signing
    
- notarization
    
- installer/update flow
    
- release channels
    

### Gate

The application satisfies predefined production-readiness criteria across:

```text
Functionality
Correctness
Reliability
Security
Performance
UX
AI Quality
Reproducibility
Maintainability
Distribution
```

---

# 9. P6 — Post-Launch Evolution

Only after the core product is proven.

Potential capabilities:

```text
Cloud
 ↓
Team Collaboration
 ↓
Warehouse Connectors
 ↓
Analysis Memory
 ↓
Agentic Analysis
 ↓
Multi-Agent Workflows
 ↓
Enterprise Governance
```

Possible integrations:

- PostgreSQL
    
- Snowflake
    
- BigQuery
    
- Databricks
    
- APIs
    
- BI platforms
    

The architecture should allow these without making them MVP dependencies.

---

# 10. Feature Priority Model

Use four categories.

### M — Must

Required for the current milestone.

### S — Should

Important but can follow the core path.

### C — Could

Useful enhancement.

### L — Later

Explicitly deferred.

Example:

|Capability|MVP|V1|Production|
|---|--:|--:|--:|
|Analysis Case|M|M|M|
|CSV|M|M|M|
|Parquet|M|M|M|
|Excel|M|M|M|
|DuckDB|M|M|M|
|Profiling|M|M|M|
|SQL|M|M|M|
|Python|M|M|M|
|Basic charts|M|M|M|
|AI planning|M|M|M|
|Evidence|M|M|M|
|Validation|M|M|M|
|Multiple datasets|—|M|M|
|Advanced EDA|—|M|M|
|AI analyst|—|M|M|
|Memory|—|—|S|
|Warehouse connectors|—|—|S|
|Multi-agent system|—|—|L|
|Enterprise collaboration|—|—|L|

---

# 11. Vertical-Slice Strategy

Each major milestone should produce something usable.

### Slice 1

```text
Case
+
Question
+
CSV
+
Profile
```

### Slice 2

```text
Case
+
Question
+
CSV
+
Profile
+
SQL
+
Result
```

### Slice 3

```text
+
AI Plan
+
Hypotheses
```

### Slice 4

```text
+
Evidence
+
Finding
+
Validation
```

### Slice 5

```text
+
Python
+
Charts
+
Export
```

### Slice 6

```text
+
Multiple datasets
+
Advanced analysis
+
AI assistance
```

This keeps every development stage demonstrable.

---

# 12. Verification Gates

Never move to the next major phase only because features are implemented.

Use gates.

## Gate A — Functional

> Does it work?

## Gate B — Analytical

> Are calculations and analytical workflows correct?

## Gate C — AI

> Does AI produce useful, structured, bounded assistance?

## Gate D — Evidence

> Can findings be traced to actual computation and data?

## Gate E — Reproducibility

> Can the analysis be repeated?

## Gate F — UX

> Can a real user understand and operate it?

## Gate G — Engineering

> Is it reliable, maintainable, and testable?

## Gate H — Production

> Is it secure, distributable, observable, and supportable?

---

# 13. Development Rule

A phase is complete only when:

```text
Feature
 +
Tests
 +
Verification
 +
Documentation
 +
State Update
```

All five are required.

---

# 14. Coding-Agent Task Hierarchy

The roadmap should translate into:

```text
Phase
 ↓
Milestone
 ↓
Capability
 ↓
Task
 ↓
Implementation
 ↓
Test
 ↓
Verification
```

Example:

```text
P2 MVP
 ↓
Data Layer
 ↓
CSV Profiling
 ↓
Implement missing-value profiler
 ↓
Write tests
 ↓
Verify against sample datasets
 ↓
Update state
```

Never give the agent the entire phase as one coding task.

---

# 15. Token-Budget Strategy

Reserve development budget approximately as:

```text
Planning / architecture       10%
Core implementation            50%
Testing / debugging            20%
Integration / refactoring      10%
Unexpected issues              10%
```

The exact percentages can change.

The key rule is:

> **Never budget 100% of tokens for feature implementation.**

Integration and debugging are inevitable.

---

# 16. Context-Budget Strategy

Each coding-agent task receives only:

```text
1. Relevant master rules
2. Current architecture
3. Current state
4. Task specification
5. Relevant files
6. Acceptance criteria
7. Verification instructions
```

Not:

> the entire repository + every historical conversation.

---

# 17. Milestone Definition

Every milestone should contain:

```text
Goal
Scope
Dependencies
Tasks
Expected outputs
Tests
Verification gate
Known risks
Next milestone
```

This makes the roadmap directly executable by the Coding-Agent Production System.

---

# 18. Recommended Build Order

The final recommended sequence is:

```text
0. Product & Engineering Master Specification
             ↓
P0. Foundation
             ↓
P1. Vertical Slice
             ↓
P2. MVP
             ↓
P3. V1
             ↓
P4. Production Candidate
             ↓
P5. Production Grade
             ↓
P6. Evolution
```

---

# 19. Definition of “Done”

## MVP Done

> One complete analytical case can be created, analyzed, validated, saved, and inspected.

## V1 Done

> Analysts can repeatedly perform meaningful real-world analyses using multiple datasets and AI assistance.

## Production Candidate Done

> The application is stable, secure, usable, and reliable enough for controlled users.

## Production Grade Done

> The product is tested, hardened, distributable, maintainable, observable, and supportable.

---

# 20. North-Star Development Principle

Do not optimize for:

> **“How many features have we built?”**

Optimize for:

> **“How much trustworthy analytical work can a user complete successfully?”**

The product should evolve like this:

```text
        PROVE THE LOOP
             ↓
        MAKE IT USEFUL
             ↓
        MAKE IT REPEATABLE
             ↓
        MAKE IT RELIABLE
             ↓
        MAKE IT PRODUCTION-GRADE
             ↓
        MAKE IT INTELLIGENT
             ↓
        MAKE IT SCALE
```

---

# 21. Final Roadmap

```text
                    DAH
                     │
             MASTER SPECIFICATION
                     │
                     ↓
              ┌──────────────┐
              │ P0 FOUNDATION│
              └──────┬───────┘
                     ↓
             ┌───────────────┐
             │ P1 VERTICAL   │
             │ SLICE         │
             └──────┬────────┘
                    ↓
             ┌───────────────┐
             │ P2 MVP        │
             └──────┬────────┘
                    ↓
             ┌───────────────┐
             │ P3 V1         │
             └──────┬────────┘
                    ↓
             ┌───────────────┐
             │ P4 PRODUCTION │
             │ CANDIDATE     │
             └──────┬────────┘
                    ↓
             ┌───────────────┐
             │ P5 PRODUCTION │
             │ GRADE         │
             └──────┬────────┘
                    ↓
             ┌───────────────┐
             │ P6 EVOLUTION  │
             └───────────────┘
```

### Roadmap principle

> **Build the smallest complete analytical loop first. Validate it. Then expand capability without breaking the core Harness.**

This roadmap is now the **“WHEN / WHAT NEXT” control artifact**. It should be used together with Artifact 00, while Artifact 11 will define exactly **how a coding agent executes each milestone and task**.