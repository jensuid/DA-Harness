# Data Analysis Harness

## Coding-Agent Production System

**Version:** 1.0  
**Purpose:** Define how an AI coding agent builds DAH safely, incrementally, and efficiently from P0 → Production Grade.

---

# 1. System Purpose

The Coding-Agent Production System converts:

```text
Master Specification
        +
Implementation Roadmap
        ↓
Executable Tasks
        ↓
AI Coding Agent
        ↓
Verified Product
```

It prevents the agent from:

- implementing too much at once
    
- inventing architecture
    
- modifying unrelated code
    
- skipping tests
    
- declaring unfinished work complete
    
- losing project context
    
- consuming excessive tokens
    
- accumulating undocumented technical debt
    

---

# 2. Governing Principle

> **The agent implements tasks; the milestone criteria determine completion.**

The agent does **not** determine whether a milestone is complete based on its own judgment.

The control loop is:

```text
PLAN
 ↓
TASK
 ↓
IMPLEMENT
 ↓
TEST
 ↓
VERIFY
 ↓
EXIT-CRITERIA CHECK
 ↓
PASS ─────────→ NEXT MILESTONE
 ↓
FAIL
 ↓
FIX / REWORK
```

---

# 3. Three Control Artifacts

The agent must operate from three authoritative documents:

```text
00 Master Specification
        │
        │ WHAT
        ↓
10 Implementation Roadmap
        │
        │ WHEN
        ↓
11 Coding-Agent Production System
        │
        │ HOW
        ↓
Coding Agent
```

### Authority hierarchy

When documents conflict:

```text
00 Master Specification
        ↓
10 Implementation Roadmap
        ↓
11 Coding-Agent System
        ↓
Task Specification
        ↓
Agent Implementation
```

The agent must not silently override higher-level decisions.

---

# 4. Development Context Protocol

Every task receives a **minimum sufficient context package**.

```text
A. Product Context
B. Current Architecture
C. Current State
D. Task Contract
E. Relevant Files
F. Constraints
G. Acceptance Criteria
H. Verification Instructions
```

Do not provide the entire project history unless required.

### Context principle

> **Give the agent enough context to make the correct change, but not enough irrelevant context to waste tokens or create ambiguity.**

---

# 5. Persistent Project State

Maintain:

```text
/ai
├── CURRENT_STATE.md
├── DECISIONS.md
├── TASKS.md
└── HANDOFF.md
```

### CURRENT_STATE.md

Contains:

- current phase
    
- current milestone
    
- completed capabilities
    
- active task
    
- known issues
    
- test status
    
- architecture status
    
- next task
    
- blockers
    

### DECISIONS.md

Records important architectural decisions:

```text
Decision
Date
Reason
Alternatives
Consequences
```

### TASKS.md

Tracks:

```text
Task ID
Milestone
Status
Priority
Dependencies
Verification
```

### HANDOFF.md

Used when stopping work or changing agents.

Contains:

- what was completed
    
- what changed
    
- tests performed
    
- unresolved problems
    
- next action
    
- important context
    

---

# 6. Milestone Control System

Each milestone must have explicit:

```text
Goal
Scope
Dependencies
Capabilities
Tasks
Exit Criteria
Verification
Known Risks
```

### Milestone status

Use:

```text
🔴 BLOCKED
🟡 IN PROGRESS
🟢 PASSED
⚪ NOT STARTED
```

Only `PASSED` permits progression.

---

# 7. Milestone Exit Criteria

## P0 — Foundation

### Exit criteria

All must pass:

- application launches
    
- web frontend builds and serves
    
- React UI renders
    
- Python backend starts
    
- frontend ↔ backend communication works
    
- basic state can persist
    
- test suite runs
    
- repository structure is established
    
- development documentation exists
    

### Exit test

```text
Start App
 → Execute Backend Operation
 → Persist State
 → Restart App
 → Recover State
 → Run Tests
```

**Exit:** PASS only if the complete sequence succeeds.

---

# 8. P1 — Vertical Slice

### Exit criteria

A user can:

```text
Create Case
 → Enter Question
 → Load CSV
 → Profile Data
 → Generate Plan
 → Execute Analysis
 → Create Finding
 → Attach Evidence
 → Validate Finding
 → Save Case
 → Reopen Case
```

### Analytical criteria

The resulting case must preserve:

- question
    
- dataset
    
- profile
    
- analysis plan
    
- computation
    
- result
    
- evidence
    
- finding
    
- validation
    

### Exit

> **One complete analytical investigation works end-to-end.**

No expansion to broad MVP features until this gate passes.

---

# 9. P2 — MVP

### Exit criteria

The system supports:

- persistent Analysis Cases
    
- CSV / Parquet / Excel
    
- profiling
    
- basic data-quality checks
    
- SQL
    
- Python
    
- essential charts
    
- result persistence
    
- AI planning
    
- evidence tracking
    
- finding management
    
- validation
    
- export
    

### Trust criteria

A finding must be traceable:

```text
Finding
 ↓
Evidence
 ↓
Result
 ↓
SQL / Python
 ↓
Dataset
```

### Reproducibility criteria

Another user can:

1. open the case
    
2. understand the question
    
3. inspect the evidence
    
4. inspect computation
    
5. reproduce the result
    

### MVP Exit

> **A real analytical question can be answered and packaged as an inspectable Analysis Case.**

---

# 10. P3 — V1

### Exit criteria

The application supports repeated analytical work with:

- multiple datasets
    
- joins
    
- richer EDA
    
- segmentation
    
- statistical analysis
    
- reusable analysis components
    
- contextual AI
    
- richer evidence lineage
    
- case history
    
- templates
    

### Usage test

Complete multiple different analytical cases without requiring architectural changes or manual developer intervention.

### V1 Exit

> **DAH is useful as a recurring analytical workbench, not merely a demonstration application.**

---

# 11. P4 — Production Candidate

### Exit criteria

No known critical defects in:

```text
Functionality
Data correctness
Persistence
Execution
Recovery
Security
AI safeguards
Performance
UX
```

Required testing includes:

- malformed files
    
- missing columns
    
- invalid SQL
    
- failed Python execution
    
- interrupted execution
    
- corrupted state
    
- large inputs
    
- long AI responses
    
- unexpected application shutdown
    

### Exit

> **Controlled external users can use the application safely and reliably.**

---

# 12. P5 — Production Grade

### Exit criteria

All production systems are operational:

```text
CI/CD
Testing
Regression protection
Versioning
Migrations
Error reporting
Security controls
AI evaluation
Packaging
Code signing
Notarization
Updates
Documentation
Release process
```

### Final Exit

The product satisfies predefined acceptance thresholds for:

```text
Correctness
Reliability
Security
Performance
UX
AI quality
Evidence traceability
Reproducibility
Maintainability
Distribution
```

Only then is P5 considered complete.

---

# 13. Task Decomposition

Never assign:

> “Build the MVP.”

Instead:

```text
Milestone
 ↓
Capability
 ↓
Task
```

Example:

```text
P2
 ↓
Data Layer
 ↓
CSV Profiling
 ↓
Implement schema inference
```

Then:

```text
Implementation
 ↓
Unit Tests
 ↓
Integration Test
 ↓
Verification
```

---

# 14. Task Contract

Every coding task must contain:

```text
TASK ID
MILESTONE
CAPABILITY
GOAL

CONTEXT
CURRENT STATE

INPUTS
RELEVANT FILES

REQUIRED CHANGE

NON-GOALS
CONSTRAINTS

ACCEPTANCE CRITERIA

TEST REQUIREMENTS

VERIFICATION STEPS

EXPECTED OUTPUT

STATE UPDATE
```

This becomes the standard interface between human and coding agent.

---

# 15. Task Size Rule

Prefer tasks that can be completed in one focused agent session.

### Good

> Add CSV schema inference to the existing profiler and create tests for numeric, categorical, date, and missing columns.

### Bad

> Build the entire data layer.

### Rule

> **One task should produce one coherent, testable change.**

If the task requires multiple unrelated architectural decisions, split it.

---

# 16. Agent Implementation Protocol

For every task:

### Step 1 — Inspect

Agent examines only relevant files.

### Step 2 — Plan

Agent briefly states:

- intended change
    
- affected files
    
- dependencies
    
- risks
    

### Step 3 — Implement

Make the smallest correct change.

### Step 4 — Test

Run relevant tests.

### Step 5 — Inspect

Check:

- regression
    
- architecture consistency
    
- error handling
    
- state changes
    

### Step 6 — Verify

Compare implementation against acceptance criteria.

### Step 7 — Report

Return:

```text
Completed
Changed
Tests
Verification
Known Issues
Next Task
```

### Step 8 — Update State

Update:

```text
CURRENT_STATE.md
TASKS.md
HANDOFF.md
```

where applicable.

---

# 17. Repository Rules

The coding agent must:

1. inspect before modifying
    
2. follow existing architecture
    
3. avoid unrelated changes
    
4. avoid duplicate abstractions
    
5. preserve public interfaces unless explicitly changing them
    
6. add tests for meaningful behavior
    
7. avoid speculative infrastructure
    
8. document architectural decisions
    
9. never delete working functionality without authorization
    
10. never silently change product scope
    

### Important rule

> **Existing code is not permission to redesign the architecture.**

Architecture changes require an explicit task or decision.

---

# 18. AI Development Rules

AI is treated as an engineering assistant, not the source of truth.

### AI may

- propose implementation
    
- generate code
    
- explain errors
    
- generate tests
    
- suggest refactoring
    
- identify potential issues
    

### AI may not independently decide

- product scope
    
- architectural direction
    
- security policy
    
- milestone completion
    
- analytical correctness
    
- production readiness
    

---

# 19. Deterministic Core Principle

DAH separates deterministic computation from probabilistic AI.

### Deterministic

```text
Data loading
Schema inference
Profiling
SQL execution
Statistics
Persistence
Evidence links
Validation rules
Exports
```

### AI-assisted

```text
Question refinement
Hypotheses
Planning
Code suggestions
Interpretation
Finding drafting
```

Core principle:

> **AI proposes. The analytical engine executes. The Harness records. The validator checks.**

---

# 20. Verification Protocol

Every completed task should pass the smallest relevant verification set.

### Level 1 — Unit

Does the changed component work?

### Level 2 — Integration

Does it work with neighboring components?

### Level 3 — Regression

Did existing behavior remain intact?

### Level 4 — Acceptance

Does it satisfy the task contract?

### Level 5 — Milestone

Does the entire milestone satisfy its exit criteria?

```text
Task PASS
 ≠
Milestone PASS
```

This distinction is critical.

---

# 21. Failure Protocol

When implementation fails:

```text
Failure
 ↓
Classify
 ↓
Local Fix
 ↓
Retest
 ↓
Verify
```

Classify failures as:

```text
Code defect
Test defect
Architecture issue
Requirement ambiguity
Environment issue
Dependency issue
Data issue
AI-output issue
```

If the failure exposes a higher-level architectural problem:

> Stop implementation and escalate the architectural decision.

Do not patch repeatedly around a broken design.

---

# 22. Scope-Control Protocol

When the agent discovers a useful additional feature:

```text
Useful idea
    ↓
Does current task require it?
    │
 ┌──┴──┐
YES    NO
 │      │
Build   Record as future task
```

Never allow:

```text
Task
 ↓
Feature creep
 ↓
Refactor
 ↓
New abstraction
 ↓
New dependency
 ↓
Architecture change
```

without explicit authorization.

---

# 23. Token-Efficiency Protocol

Optimize for **context efficiency**, not maximum output.

### Before each task

Provide only:

```text
Relevant rules
+
Relevant architecture
+
Current state
+
Task
+
Relevant files
+
Acceptance criteria
```

### Agent should avoid

- repeating entire source files
    
- explaining obvious code
    
- rewriting unaffected modules
    
- generating unused abstractions
    
- exploring unrelated architecture
    

### Preferred behavior

> Inspect → change minimally → test → report.

---

# 24. Context Compression

Maintain compact project summaries.

Example:

```text
DAH CURRENT STATE

Phase: P2
Milestone: Data Layer
Completed:
- Case persistence
- CSV loader
- schema inference

Current:
- profiling

Next:
- missingness analysis

Known issues:
- Excel date inference

Tests:
- 42 passing
- 1 failing
```

This allows a new agent session to recover context quickly.

---

# 25. Handoff Protocol

When ending a session:

```text
HANDOFF

Current Phase:
Current Milestone:
Current Task:

Completed:
- ...

Changed Files:
- ...

Tests:
- ...

Verification:
- ...

Known Issues:
- ...

Architectural Decisions:
- ...

Next Task:
- ...

Do Not:
- ...
```

The next agent should be able to continue without reconstructing the entire project history.

---

# 26. Definition of Done

A coding task is **DONE** only when:

```text
Implementation
    +
Tests
    +
Acceptance Criteria
    +
Verification
    +
Documentation / State Update
```

A milestone is **DONE** only when:

```text
All required tasks
      +
All required tests
      +
Milestone verification
      +
Explicit exit criteria
```

A phase is **DONE** only when:

```text
Milestone PASS
      +
No blocking defects
      +
Phase exit criteria PASS
```

---

# 27. Master Coding-Agent Prompt

Use this as the persistent base instruction for the coding agent:

> You are the implementation agent for the Data Analysis Harness.
> 
> Treat the Master Specification as the product source of truth and the Implementation Roadmap as the development sequence.
> 
> Your job is to implement the current task only.
> 
> Before changing code:
> 
> 1. inspect the relevant architecture and files;
>     
> 2. identify dependencies and constraints;
>     
> 3. make the smallest correct implementation plan.
>     
> 
> During implementation:
> 
> - do not expand scope;
>     
> - do not redesign unrelated architecture;
>     
> - preserve existing behavior;
>     
> - prefer simple maintainable solutions;
>     
> - add appropriate tests;
>     
> - keep deterministic computation separate from AI behavior.
>     
> 
> After implementation:
> 
> 1. run relevant tests;
>     
> 2. verify acceptance criteria;
>     
> 3. check for regression;
>     
> 4. report exactly what changed;
>     
> 5. identify known issues;
>     
> 6. update project state where required.
>     
> 
> Never declare a milestone complete merely because implementation is finished.
> 
> A milestone is complete only when its explicit exit criteria pass.
> 
> If requirements conflict with architecture or higher-level specifications, stop and report the conflict rather than silently choosing a new direction.
> 
> If the task reveals a fundamental architectural problem, escalate it before continuing.
> 
> Optimize for correctness, traceability, maintainability, and token-efficient execution.

---

# 28. Task Template

```text
TASK ID:
MILESTONE:
PRIORITY:

GOAL:
[One sentence]

CURRENT STATE:
[Relevant existing capability]

CONTEXT:
[Only information necessary]

RELEVANT FILES:
[List]

REQUIRED CHANGE:
[Exact implementation]

NON-GOALS:
[Explicitly excluded work]

CONSTRAINTS:
[Architecture / technology / scope constraints]

ACCEPTANCE CRITERIA:
- [ ]
- [ ]
- [ ]

TESTS:
- [ ]

VERIFICATION:
1.
2.
3.

EXPECTED OUTPUT:
[Code / tests / docs / state]

STATE UPDATE:
[What must be recorded]
```

---

# 29. Example Task

```text
TASK ID: P2-DATA-003
MILESTONE: P2 MVP
PRIORITY: M

GOAL:
Add missing-value profiling to the existing dataset profiler.

CURRENT STATE:
CSV loading and schema inference already work.

RELEVANT FILES:
data/profiler.py
tests/test_profiler.py

REQUIRED CHANGE:
For every column calculate:
- null count
- null percentage
- non-null count

NON-GOALS:
- no visualization
- no AI interpretation
- no UI redesign
- no new database layer

ACCEPTANCE CRITERIA:
- [ ] Every column receives missingness statistics
- [ ] Percentages are correct
- [ ] Empty datasets are handled safely
- [ ] Existing profiling still works

TESTS:
- all-null column
- no-null column
- mixed-null column
- empty dataset

VERIFICATION:
Run profiler tests and full regression suite.

EXPECTED OUTPUT:
Updated profiler + tests.

STATE UPDATE:
Mark P2-DATA-003 complete if verification passes.
```

---

# 30. Milestone Operating Rhythm

For every milestone:

```text
1. Read milestone definition
2. Confirm dependencies
3. Decompose capabilities
4. Create task backlog
5. Execute highest-priority task
6. Verify
7. Update state
8. Repeat
9. Run milestone verification
10. Evaluate exit criteria
11. PASS → next milestone
```

---

# 31. Priority Rules

When deciding what the agent should work on next:

```text
P0 blockers
   ↓
Milestone-critical functionality
   ↓
Correctness
   ↓
Tests
   ↓
Integration
   ↓
UX improvements
   ↓
Performance
   ↓
Nice-to-have features
```

Never prioritize cosmetic improvements over a broken analytical foundation.

---

# 32. Hard Stop Conditions

The agent must stop and request a decision when:

- requirements conflict
    
- architecture must materially change
    
- security implications are unclear
    
- data correctness cannot be established
    
- a destructive migration is required
    
- a dependency introduces major risk
    
- task scope has expanded substantially
    
- acceptance criteria are impossible with the current architecture
    

The agent should **not guess**.

---

# 33. Development State Model

Use:

```text
NOT_STARTED
    ↓
READY
    ↓
IN_PROGRESS
    ↓
IMPLEMENTED
    ↓
TESTED
    ↓
VERIFIED
    ↓
DONE
```

Milestone state:

```text
NOT_STARTED
    ↓
IN_PROGRESS
    ↓
VERIFICATION
    ↓
PASSED
```

There is no shortcut from `IMPLEMENTED` to `DONE`.

---

# 34. Relationship to Roadmap

Artifact 10 answers:

> **What should we build next?**

Artifact 11 answers:

> **How should the coding agent build it?**

Artifact 00 answers:

> **What exactly is DAH?**

Together:

```text
00 MASTER SPEC
      │
      │ WHAT
      ↓
10 ROADMAP
      │
      │ WHEN
      ↓
11 CODING-AGENT SYSTEM
      │
      │ HOW
      ↓
TASK
      ↓
CODE
      ↓
TEST
      ↓
VERIFY
      ↓
EXIT CRITERIA
      ↓
NEXT MILESTONE
```

---

# 35. Core Operating Principle

The entire development system can be reduced to:

```text
SMALL TASKS
     +
SMALL CONTEXT
     +
EXPLICIT ACCEPTANCE
     +
AUTOMATED TESTS
     +
MILESTONE EXIT CRITERIA
     +
PERSISTENT STATE
     ↓
CONTROLLED AI DEVELOPMENT
```

The Coding-Agent Production System therefore transforms AI coding from:

> **“Ask the agent to build the app.”**

into:

> **“Give the agent one controlled task inside a verified development system.”**

That distinction is essential for building DAH reliably under context and token constraints.