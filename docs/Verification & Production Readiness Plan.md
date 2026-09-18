# Data Analysis Harness

## Verification & Production Readiness Plan

**Version:** 1.0  
**Purpose:** Define how DAH is tested, validated, hardened, and approved from the first vertical slice through production release.

---

# 1. Purpose

Artifact 12 answers:

> **How do we know DAH is actually ready?**

It prevents:

```text
Feature implemented
      ≠
Feature correct
      ≠
Milestone complete
      ≠
Production ready
```

The verification system is:

```text
BUILD
 ↓
TEST
 ↓
VERIFY
 ↓
VALIDATE
 ↓
GATE
 ↓
RELEASE
```

---

# 2. Quality Model

DAH quality has eight dimensions:

```text
1. Functional
2. Analytical
3. Data Integrity
4. Evidence & Reproducibility
5. AI Quality
6. UX
7. Engineering
8. Production
```

A serious DAH release must satisfy all applicable dimensions.

---

# 3. Verification Hierarchy

Use five levels:

```text
Level 1 — Unit
      ↓
Level 2 — Integration
      ↓
Level 3 — System
      ↓
Level 4 — Acceptance
      ↓
Level 5 — Milestone / Release Gate
```

### Important rule

> Passing unit tests does not prove the analytical workflow is correct.

---

# 4. Gate A — Functional Correctness

Question:

> **Does the software perform the intended operation?**

Test:

- UI actions
    
- API calls
    
- file loading
    
- state changes
    
- persistence
    
- SQL execution
    
- Python execution
    
- chart creation
    
- exports
    

Example:

```text
Import CSV
 ↓
Dataset appears
 ↓
Schema detected
 ↓
Profile generated
```

### Pass criteria

All critical user workflows succeed under expected conditions.

---

# 5. Gate B — Analytical Correctness

Question:

> **Are the analytical results actually correct?**

This is a critical DAH-specific gate.

Test calculations against known expected values.

Example:

```text
Known dataset
      ↓
DAH calculation
      ↓
Expected result
```

Compare:

- counts
    
- sums
    
- averages
    
- percentages
    
- rates
    
- aggregations
    
- filters
    
- joins
    
- statistical calculations
    

### Golden datasets

Maintain small datasets with known answers.

Example:

```text
tests/
└── fixtures/
    ├── simple_sales.csv
    ├── missing_values.csv
    ├── duplicates.csv
    └── join_test.csv
```

### Pass criteria

No unexplained discrepancy in critical calculations.

---

# 6. Gate C — Data Integrity

Question:

> **Does DAH preserve the meaning and integrity of the user's data?**

Test:

- row counts
    
- column types
    
- null handling
    
- duplicate handling
    
- encoding
    
- date parsing
    
- numeric conversion
    
- joins
    
- filtering
    
- aggregation
    

Special attention:

```text
Raw Data
   ↓
Transformation
   ↓
Analysis
   ↓
Result
```

Each transformation should be explainable.

---

# 7. Gate D — Evidence Traceability

Question:

> **Can every important finding be traced to evidence?**

Required chain:

```text
Finding
 ↓
Evidence
 ↓
Result
 ↓
Analysis Run
 ↓
SQL / Python
 ↓
Dataset
```

Test:

- evidence IDs exist
    
- source result exists
    
- query/code is preserved
    
- dataset reference exists
    
- finding is not detached from evidence
    

### Pass criteria

A reviewer can trace an important claim back to its computational source.

---

# 8. Gate E — Reproducibility

Question:

> **Can the analysis be repeated?**

Test:

1. save Analysis Case
    
2. close application
    
3. reopen case
    
4. inspect analysis
    
5. rerun computation
    
6. compare result
    

Record:

- data source
    
- query/code
    
- parameters
    
- method
    
- relevant configuration
    
- execution metadata
    

### Pass criteria

Critical analytical results can be reproduced or differences are explicitly explained.

---

# 9. Gate F — Validation Quality

Validation should examine both computation and reasoning.

Initial checks:

```text
Calculation
Denominator
Population
Missing data
Duplicates
Comparisons
Assumptions
Contradictions
Causal claims
```

Example:

> Revenue increased 20%.

Validator should be able to establish:

```text
20% relative to what?
Which period?
Which population?
Which metric definition?
What data was excluded?
```

### Pass criteria

Important findings cannot silently bypass required validation.

---

# 10. Gate G — AI Quality

AI is evaluated separately from deterministic computation.

Test categories:

```text
Question refinement
Hypothesis generation
Analysis planning
Code generation
Result interpretation
Finding drafting
Validation suggestions
```

Evaluate:

- correctness
    
- relevance
    
- grounding
    
- structured-output validity
    
- hallucination
    
- unsupported claims
    
- instruction following
    
- consistency
    

---

# 11. AI Safety Rules

AI must not silently:

- modify analytical results
    
- fabricate evidence
    
- invent data
    
- claim an analysis was executed when it was not
    
- convert correlation into causation
    
- bypass validation
    
- alter case state without authorization
    

Use:

```text
AI Proposal
 ↓
Schema Validation
 ↓
Human / Harness Approval
 ↓
Execution
 ↓
Recorded Result
```

---

# 12. AI Evaluation Dataset

Create a fixed evaluation set:

```text
tests/
└── ai/
    ├── question_refinement/
    ├── planning/
    ├── code_generation/
    ├── interpretation/
    └── validation/
```

Each case contains:

```text
Input
Expected properties
Known failure modes
Evaluation criteria
```

Do not require identical wording from the model.

Evaluate whether the output satisfies the required properties.

---

# 13. Gate H — UX Verification

Question:

> **Can users actually understand and complete the workflow?**

Test the core journey:

```text
Create Case
 ↓
Question
 ↓
Import Data
 ↓
Understand Data
 ↓
Plan
 ↓
Analyze
 ↓
Evidence
 ↓
Finding
 ↓
Validate
 ↓
Export
```

Check:

- discoverability
    
- feedback
    
- loading states
    
- error messages
    
- navigation
    
- terminology
    
- accessibility
    
- recovery
    

### Pass criteria

A representative user can complete the core workflow without developer assistance.

---

# 14. Gate I — Error & Recovery

Every important operation must handle failure.

Test:

```text
Invalid file
Invalid schema
Invalid SQL
Python failure
AI failure
Large input
Cancelled operation
Interrupted execution
Corrupted state
Unexpected shutdown
```

Expected pattern:

```text
Failure
 ↓
Clear error
 ↓
Safe state
 ↓
Recovery path
```

Never allow a failed operation to silently corrupt the Analysis Case.

---

# 15. Gate J — Performance

Create representative datasets:

```text
Small
Medium
Large
Stress
```

Measure:

- application startup
    
- file import
    
- profiling
    
- SQL execution
    
- Python execution
    
- chart rendering
    
- case loading
    
- case saving
    
- AI interaction
    

Do not optimize based on intuition.

> **Measure → identify bottleneck → optimize → remeasure.**

---

# 16. Gate K — Security

Perform security verification for:

### Files

- unsafe paths
    
- malformed files
    
- oversized files
    

### SQL

- injection risks
    
- unauthorized operations
    
- resource abuse
    

### Python

- unrestricted filesystem access
    
- process execution
    
- network access
    
- resource exhaustion
    

### AI

- prompt injection
    
- malicious instructions in data
    
- unsafe generated code
    
- secret exposure
    

### Application

- secrets
    
- local storage
    
- dependencies
    
- update mechanism
    

---

# 17. Data Trust Rules

DAH must distinguish:

```text
Observed
Calculated
Inferred
Suggested
Assumed
Unknown
```

For example:

```text
Observed:
Revenue = $1.2M

Calculated:
Revenue increased 18%

Inferred:
Possible seasonal effect

Suggested:
Investigate regional mix

Unknown:
Causal reason for increase
```

This prevents AI-generated interpretation from being mistaken for measured fact.

---

# 18. Test Pyramid

Prefer:

```text
             E2E
            /   \
       Integration
          /     \
       Unit Tests
```

Most tests should be fast unit tests.

Use integration tests for:

- database
    
- backend/frontend communication
    
- execution pipeline
    
- persistence
    

Use E2E tests for critical user journeys.

---

# 19. Golden Analytical Tests

Maintain stable reference cases.

Example:

```text
Case:
Sales Analysis

Known:
Rows = 1000
Revenue = 125000
Average Order = 125
Missing Customer IDs = 30
```

DAH must reproduce expected results.

These tests protect against analytical regressions.

---

# 20. Regression Testing

Every significant change should run:

```text
Relevant Unit Tests
        ↓
Relevant Integration Tests
        ↓
Full Regression Suite
```

Never assume a small code change cannot affect analytical correctness.

---

# 21. Milestone Verification Gates

## P0 Gate

```text
App launches
+
Frontend works
+
Backend works
+
Communication works
+
Persistence works
+
Tests run
```

→ **P0 PASS**

---

## P1 Gate

```text
Case
+
Question
+
CSV
+
Profile
+
Plan
+
Analysis
+
Evidence
+
Finding
+
Validation
+
Persistence
```

→ **P1 PASS**

---

## P2 Gate

```text
Real analytical problem
+
Supported data
+
SQL/Python
+
Visualization
+
AI assistance
+
Evidence
+
Validation
+
Export
+
Reproducibility
```

→ **MVP PASS**

---

## P3 Gate

```text
Multiple real cases
+
Multiple datasets
+
Advanced analysis
+
Contextual AI
+
Reusable workflow
```

→ **V1 PASS**

---

## P4 Gate

```text
Reliability
+
Security
+
Performance
+
Recovery
+
AI safeguards
+
UX
```

→ **Production Candidate PASS**

---

## P5 Gate

```text
Testing
+
CI/CD
+
Security
+
AI evaluation
+
Packaging
+
Signing
+
Updates
+
Documentation
+
Operational readiness
```

→ **Production PASS**

---

# 22. Severity Model

Classify defects:

### P0 — Critical

- data corruption
    
- security vulnerability
    
- incorrect critical analytical result
    
- unrecoverable case loss
    

**Blocks release.**

### P1 — High

- major workflow failure
    
- incorrect calculation
    
- broken evidence chain
    
- serious AI safety issue
    

**Normally blocks milestone.**

### P2 — Medium

- limited functionality
    
- significant UX issue
    
- non-critical performance issue
    

**May be deferred with explicit decision.**

### P3 — Low

- cosmetic issue
    
- minor usability improvement
    

**Does not normally block release.**

---

# 23. Release Decision Matrix

```text
Critical defect?
   │
  YES → NO RELEASE
   │
  NO
   ↓
Analytical correctness PASS?
   │
  NO → NO RELEASE
   │
  YES
   ↓
Security PASS?
   │
  NO → NO RELEASE
   │
  YES
   ↓
Core workflow PASS?
   │
  NO → NO RELEASE
   │
  YES
   ↓
Production criteria PASS?
   │
  NO → FIX / DEFER WITH DECISION
   │
  YES
   ↓
RELEASE
```

---

# 24. Verification Evidence

Every gate should produce evidence.

Examples:

```text
Test results
Screenshots
Benchmark results
AI evaluation results
Security findings
Regression results
User-test results
```

Store references in the project.

Suggested structure:

```text
verification/
├── p0/
├── p1/
├── p2/
├── p3/
├── p4/
└── p5/
```

---

# 25. Verification Report

Each milestone should produce:

```text
Milestone:
Date:
Version:

Exit Criteria:
- PASS
- PASS
- PASS
- PASS

Tests:
X passed
Y failed

Critical Issues:
None

Known Issues:
...

Evidence:
...

Decision:
PASS / FAIL

Approved Next Step:
...
```

---

# 26. Production Readiness Checklist

Before production:

### Product

-  Core workflows complete
    
-  User onboarding works
    
-  Errors understandable
    
-  Export works
    

### Analytical

-  Calculations verified
    
-  Statistical methods verified
    
-  Golden datasets pass
    
-  Analytical regressions absent
    

### Evidence

-  Findings trace to evidence
    
-  Evidence traces to computation
    
-  Data sources are identifiable
    
-  Reproduction works
    

### AI

-  Structured outputs validated
    
-  Hallucination tests performed
    
-  Prompt injection tested
    
-  Generated code controlled
    
-  AI failures handled
    

### Engineering

-  Automated tests
    
-  CI
    
-  Error handling
    
-  Recovery
    
-  Migration strategy
    
-  Dependency management
    

### Security

-  Threat model
    
-  Dependency scanning
    
-  Secret handling
    
-  File security
    
-  Code execution controls
    
-  Update security
    

### Performance

-  Representative benchmarks
    
-  Known limits documented
    
-  Stress tests completed
    

### Distribution

-  macOS package
    
-  Code signing
    
-  Notarization
    
-  Installer
    
-  Update mechanism
    

---

# 27. Definition of Production Ready

DAH is production-ready only when:

> **A real user can perform meaningful analysis, obtain correct results, trace findings to evidence, reproduce important computations, recover from expected failures, and use the application safely and reliably.**

Not:

> “All planned features are implemented.”

---

# 28. Continuous Verification Loop

Verification does not end at release.

```text
Build
 ↓
Test
 ↓
Release
 ↓
Observe
 ↓
Detect
 ↓
Investigate
 ↓
Fix
 ↓
Regression Test
 ↓
Release Again
```

Every production defect should become a future regression test where appropriate.

---

# 29. Relationship to the Three Master Artifacts

```text
00 MASTER SPECIFICATION
        │
        │ Product truth
        ↓
10 IMPLEMENTATION ROADMAP
        │
        │ Milestones
        ↓
11 CODING-AGENT SYSTEM
        │
        │ Build process
        ↓
APPLICATION
        │
        ↓
12 VERIFICATION & READINESS
        │
        │ Prove correctness
        ↓
MILESTONE PASS
        │
        ↓
NEXT MILESTONE
```

Artifact 12 therefore closes the development loop.

---

# 30. Complete DAH Development Control System

The four key artifacts now form:

```text
┌──────────────────────────────┐
│ 00 MASTER SPECIFICATION      │
│ WHAT                         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 10 IMPLEMENTATION ROADMAP    │
│ WHEN                         │
└──────────────┬───────────────┘
               ↓
┌──────────────────────────────┐
│ 11 CODING-AGENT SYSTEM       │
│ HOW                          │
└──────────────┬───────────────┘
               ↓
             TASK
               ↓
             CODE
               ↓
             TEST
               ↓
┌──────────────────────────────┐
│ 12 VERIFICATION SYSTEM       │
│ IS IT CORRECT / READY?       │
└──────────────┬───────────────┘
               ↓
          EXIT CRITERIA
               ↓
          PASS / FAIL
               ↓
        NEXT MILESTONE
```

---

# 31. Master Quality Principle

The DAH development system follows one fundamental rule:

> **Never confuse implementation with proof.**

The coding agent creates the capability.

Tests establish behavior.

Analytical verification establishes correctness.

Evidence verification establishes trust.

Production verification establishes readiness.

Only the combined result earns a milestone or release.

---

# 32. Final Gate Philosophy

The development sequence is therefore:

```text
BUILD
  ↓
PROVE
  ↓
HARDEN
  ↓
VERIFY
  ↓
RELEASE
```

And the product itself follows the same philosophy:

```text
Data
 ↓
Analysis
 ↓
Evidence
 ↓
Validation
 ↓
Trustworthy Finding
```

**DAH should apply the same discipline to its own construction that it expects users to apply to their analysis.**