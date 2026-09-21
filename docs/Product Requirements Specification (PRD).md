
# Data Analysis Harness

## Product Requirements Specification (PRD)

**Artifact:** 04  
**Version:** 1.1  
**Status:** Master Product Requirements  
**Product:** Data Analysis Harness (DAH)

---

# 1. Purpose

This PRD defines **what DAH must do** and establishes measurable thresholds for determining whether the requirements have actually been satisfied.

The PRD translates:

- Product Vision
    
- Core Analytical Framework
    
- UX/UI Architecture
    
- Implementation Roadmap
    
- Verification Plan
    

into:

```text
Requirement
    ↓
Expected Behavior
    ↓
Acceptance Threshold
    ↓
Test
    ↓
Pass / Fail
```

---

# 2. Product Definition

> **Data Analysis Harness is a local-first, AI-assisted analytical workspace that transforms an ambiguous data problem into a structured, evidence-backed, validated, and reproducible Analysis Case.**

DAH is not primarily:

- a BI dashboard builder
    
- a notebook
    
- a spreadsheet
    
- a chatbot
    
- an autonomous AI analyst
    

It is an:

> **Analytical Control Layer**

that coordinates:

```text
Question
→ Context
→ Data
→ Quality
→ Analysis
→ Evidence
→ Validation
→ Finding
→ Decision Support
```

---

# 3. Product Goal

The product must help a user move from:

> "I have a question and some data."

to:

> "I have a structured analysis, traceable evidence, validated findings, known limitations, and enough context to support a decision."

The MVP must demonstrate this using **real executable analysis**, not simulated screens.

---

# 4. Core Acceptance Philosophy

DAH acceptance criteria follow six principles:

```text
Functional
    +
Analytical
    +
Traceable
    +
Reproducible
    +
Validated
    +
Usable
```

A feature is not considered complete merely because:

- the UI exists
    
- the code executes
    
- an AI response appears
    
- a chart renders
    

It must satisfy its measurable acceptance threshold.

---

# 5. Global Acceptance Thresholds

## AT-01 — Core Workflow Completion

Using a supported test dataset, a new user must be able to complete:

```text
Create Case
→ Question
→ Data
→ Quality
→ Plan
→ Analysis
→ Result
→ Evidence
→ Finding
→ Validation
→ Save
→ Reopen
```

### Threshold

**≥ 95% of scripted workflow attempts must complete successfully** without developer intervention.

Test population:

- minimum 20 scripted runs
    
- minimum 3 representative datasets
    

---

# 6. AT-02 — Case Persistence

After saving and restarting the application:

- 100% of case metadata must persist
    
- 100% of questions must persist
    
- 100% of findings must persist
    
- 100% of validation states must persist
    
- 100% of evidence relationships must persist
    
- 100% of analysis-run metadata must persist
    

### Threshold

> **0 data-loss defects in release-blocking tests.**

---

# 7. AT-03 — Question Capture

A user must be able to create and edit:

- purpose
    
- primary question
    
- sub-questions
    
- hypotheses
    

### Threshold

For **100% of acceptance-test cases**:

- entered text persists
    
- edited text persists
    
- reopening the case restores the latest version
    

---

# 8. AT-04 — AI Question Refinement

AI-generated question refinement must:

- preserve the user's original question
    
- present the proposed revision separately
    
- allow accept/reject/edit
    
- never silently overwrite the original
    

### Threshold

Across **50 evaluation cases**:

- ≥ 95% preserve the original question
    
- ≥ 90% produce a semantically relevant refinement
    
- 0 silent overwrites
    
- 0 fabricated data references
    

---

# 9. AT-05 — Data Import

Supported MVP formats:

- CSV
    
- Parquet
    
- Excel
    

### Threshold

For the defined golden dataset suite:

- ≥ 99% successful import rate for valid files
    
- 100% rejection of intentionally malformed test files with a user-readable error
    
- 100% preservation of detected column names
    
- 100% preservation of row count where no transformation is expected
    

---

# 10. AT-06 — Schema Detection

The system must detect:

- column names
    
- basic data types
    
- row count
    
- column count
    

### Threshold

On the golden dataset suite:

- ≥ 99% column-name accuracy
    
- ≥ 99% row-count accuracy
    
- ≥ 95% basic type-detection accuracy
    

Known ambiguous types must be explicitly marked rather than silently misclassified.

---

# 11. AT-07 — Data Profiling

Minimum profiling:

- missingness
    
- uniqueness
    
- duplicates
    
- numeric summaries
    
- date ranges
    
- categorical cardinality
    

### Threshold

For deterministic golden datasets:

> **100% of expected profiling calculations must match reference values within defined numerical tolerance.**

Default numerical tolerance:

```text
absolute error ≤ 0.01
OR
relative error ≤ 0.1%
```

whichever is appropriate for the metric.

---

# 12. AT-08 — Data Quality Detection

The system must detect known injected problems in the quality test suite.

Test cases include:

- missing values
    
- duplicate rows
    
- invalid types
    
- inconsistent categories
    
- date gaps
    
- extreme values
    
- insufficient coverage
    

### Threshold

For intentionally injected quality defects:

> **≥ 95% detection rate**

and:

> **≤ 5% false-positive rate**

for the defined golden dataset suite.

---

# 13. AT-09 — Quality Impact

Where a quality issue can materially affect an analysis, DAH should communicate potential impact.

Example:

```text
4.8% of revenue values are missing.

Potential impact:
Revenue comparisons may be understated.
```

### Threshold

For predefined material-risk test cases:

> **≥ 90% of known material issues must produce a visible analytical-impact warning.**

---

# 14. AT-10 — Analysis Planning

The Analysis Plan must support:

- objective
    
- question
    
- sub-questions
    
- hypotheses
    
- required data
    
- methods
    
- validation plan
    

### Threshold

For **20 representative planning scenarios**:

- ≥ 95% contain all required structural fields
    
- ≥ 90% identify at least one relevant analytical method
    
- ≥ 90% identify at least one relevant validation consideration
    

AI-generated plans must remain editable.

---

# 15. AT-11 — SQL Execution

Users must be able to:

- write SQL
    
- execute SQL
    
- inspect results
    
- save execution history
    

### Threshold

For deterministic SQL test cases:

> **100% of reference queries must produce the expected result within defined numerical tolerance.**

Additionally:

- 100% of executions receive a recorded run ID
    
- 100% of successful executions store query text
    
- 100% of failed executions return a user-readable error
    

---

# 16. AT-12 — Python Execution

Python analysis must execute in a controlled environment.

### Threshold

For the approved Python test suite:

- ≥ 95% successful execution rate
    
- 100% of successful executions produce execution metadata
    
- 100% of intentionally invalid scripts fail without crashing the application
    
- 0 uncontrolled modification of application state
    

---

# 17. AT-13 — Result Integrity

Every successful analysis execution must create a result that identifies:

- dataset
    
- method
    
- computation
    
- output
    
- execution time
    
- analysis run
    

### Threshold

> **100% of successful analytical executions must have a traceable Result object.**

No orphaned result should exist in the golden integration tests.

---

# 18. AT-14 — Visualization Integrity

Charts must represent the underlying result correctly.

### Threshold

For the chart golden suite:

> **100% of reference charts must match the expected underlying values.**

The test must verify data values rather than only visual appearance.

---

# 19. AT-15 — Evidence Traceability

Every finding must be traceable through:

```text
Finding
↓
Evidence
↓
Result
↓
Analysis Run
↓
Method / SQL / Python
↓
Dataset
```

### Threshold

For the evidence integration suite:

> **100% of findings must have a valid evidence chain.**

Release blocker:

> **Any fabricated or broken evidence chain = P0 defect.**

---

# 20. AT-16 — Finding Creation

A finding must support:

- claim
    
- evidence
    
- method
    
- interpretation
    
- limitations
    
- uncertainty
    

### Threshold

For 100% of acceptance scenarios:

- claim persists
    
- evidence can be attached
    
- evidence remains linked after restart
    
- limitations can be recorded
    
- finding status persists
    

---

# 21. AT-17 — Validation Coverage

Every finding must support validation status.

Minimum validation dimensions:

```text
Calculation
Data
Population
Timeframe
Method
Evidence
Assumptions
Causality
Alternative explanations
```

### Threshold

> **100% of findings expose validation status.**

For predefined validation test cases:

> **≥ 95% of intentionally introduced analytical problems must be detected.**

---

# 22. AT-18 — Unsupported Causality

DAH must identify unsupported causal language where evidence only establishes association.

### Threshold

Across **50 causal-language evaluation cases**:

- ≥ 95% correctly flag unsupported causal claims
    
- ≥ 95% distinguish association from causation
    
- 0 cases where the system converts an unsupported association into a validated causal finding
    

---

# 23. AT-19 — AI Execution Honesty

AI must never claim an analysis was executed when it was not.

### Threshold

Across **100 AI evaluation scenarios**:

- 100% correctly distinguish proposed vs executed analysis
    
- 100% identify unavailable execution results
    
- 0 fabricated execution claims
    
- 0 fabricated evidence
    
- 0 fabricated dataset values
    

Any fabricated execution/evidence claim is:

> **P0 — Release Blocking**

---

# 24. AT-20 — AI Structured Output

AI outputs used by the application must conform to defined schemas.

### Threshold

Across the AI evaluation suite:

> **≥ 98% valid structured-output rate on first response**

and:

> **≥ 99.5% after automated retry/repair where repair is permitted.**

Invalid output must never silently modify application state.

---

# 25. AT-21 — AI Relevance

For:

- question refinement
    
- analysis planning
    
- hypothesis generation
    
- validation suggestions
    
- interpretation
    

### Threshold

Human evaluation across **50 representative cases**:

> **≥ 90% rated relevant and contextually appropriate.**

Evaluation should use predefined rubrics rather than informal impressions.

---

# 26. AT-22 — AI Human Control

Important AI actions must require explicit approval where they affect:

- case state
    
- analysis execution
    
- findings
    
- conclusions
    

### Threshold

> **100% of state-changing AI actions must pass through the defined authorization mechanism.**

No silent state-changing AI action is acceptable.

---

# 27. AT-23 — Reproducibility

A saved analysis must be reproducible from its recorded analytical inputs.

### Threshold

For deterministic golden analyses:

> **100% must reproduce the same result within defined numerical tolerance.**

For non-deterministic operations, the system must preserve:

- model/version
    
- parameters
    
- execution metadata
    
- relevant configuration
    

so that the source of variation is identifiable.

---

# 28. AT-24 — Case Reopening

A previously saved case must reopen with its analytical state intact.

### Threshold

Across **50 save → close → reopen cycles**:

- 100% case recovery
    
- 0 missing findings
    
- 0 broken evidence relationships
    
- 0 lost validation states
    

---

# 29. AT-25 — Application Stability

Normal user actions must not crash the application.

### Threshold

During the release regression suite:

> **0 P0 crash defects**

and:

> **≥ 99.5% successful completion rate for defined normal-use operations.**

---

# 30. AT-26 — Error Recovery

The application must gracefully handle:

- invalid files
    
- invalid SQL
    
- invalid Python
    
- interrupted analysis
    
- unavailable AI
    
- malformed AI output
    
- corrupted/unsupported input
    

### Threshold

> **100% of defined failure scenarios must produce a recoverable application state.**

The application must not lose the existing Analysis Case because of an individual failed operation.

---

# 31. AT-27 — UI Responsiveness

For normal local interactions:

- navigation
    
- opening a case
    
- editing text
    
- switching stages
    
- expanding panels
    

### Target

> **95th percentile interaction response ≤ 200 ms**

for defined benchmark hardware.

For heavier operations:

- show progress within **500 ms**
    
- never leave the user without visible system state
    

---

# 32. AT-28 — Case Loading

For benchmark cases within the MVP supported-size envelope:

### Target

> **95% of case openings complete within 2 seconds.**

Cases exceeding the supported envelope must communicate progress rather than appearing frozen.

---

# 33. AT-29 — Data Profiling Performance

For the MVP benchmark dataset:

> **95% of standard profiling operations complete within 5 seconds**

on the defined reference machine.

Large-data operations outside the supported envelope must display progress and remain cancellable where technically possible.

---

# 34. AT-30 — Long-Running Operations

For operations expected to exceed 2 seconds:

- visible progress/status must appear
    
- user must know what is happening
    
- cancellation should be available where technically safe
    

### Threshold

> **100% of benchmarked long-running operations provide visible execution state.**

---

# 35. AT-31 — Data Loss

Data loss is unacceptable for persisted analytical state.

### Threshold

> **0 known P0 data-loss defects at release.**

Any reproducible loss of:

- case state
    
- finding
    
- evidence
    
- validation
    
- analysis history
    

is release-blocking.

---

# 36. AT-32 — Accessibility

The MVP should support:

- keyboard navigation
    
- visible focus
    
- semantic controls
    
- readable contrast
    
- non-color-only status
    

### Threshold

Target:

> **100% of critical user flows keyboard-accessible**

and:

> **0 critical accessibility violations** in the defined automated/manual accessibility suite.

---

# 37. AT-33 — UX Completion

A new user should be able to understand:

- current case
    
- current stage
    
- current task
    
- next useful action
    
- analysis status
    

### Threshold

In usability testing with **10 representative users**:

- ≥ 8/10 complete the core workflow without facilitator intervention
    
- ≥ 8/10 correctly identify the current analytical stage
    
- ≥ 8/10 correctly identify whether a finding is validated
    

This is a usability threshold, not a statistical claim about a broader population.

---

# 38. AT-34 — Evidence Understanding

In usability testing:

> **≥ 8/10 representative users must be able to trace a displayed finding back to its supporting result.**

The task should be completed without facilitator explanation.

---

# 39. AT-35 — Validation Understanding

Users must be able to distinguish:

```text
Result
Finding
Validated Finding
```

### Threshold

> **≥ 90% task accuracy** in the defined usability evaluation.

---

# 40. AT-36 — Security

The application must protect against defined MVP threats.

Minimum tests:

- path traversal
    
- malicious filenames
    
- unsafe file handling
    
- command injection
    
- SQL injection where applicable
    
- Python execution escape
    
- secret exposure
    
- prompt injection
    

### Threshold

> **0 known critical security vulnerabilities at production release.**

Critical security findings are release-blocking.

---

# 41. AT-37 — Dependency Security

Production dependencies must be scanned.

### Threshold

At release:

> **0 known Critical vulnerabilities**

and:

> **0 known High vulnerabilities without an explicit documented risk acceptance.**

---

# 42. AT-38 — Test Coverage

Coverage should not be the sole quality measure, but the MVP requires meaningful automated coverage.

### Minimum targets

Core domain logic:

> **≥ 80% line coverage**

Critical analytical/validation logic:

> **≥ 90% line coverage**

Critical evidence/reproducibility paths:

> **≥ 90% line coverage**

Coverage alone does not constitute analytical correctness.

---

# 43. AT-39 — Regression Suite

Every release candidate must pass:

- unit tests
    
- integration tests
    
- analytical golden tests
    
- AI evaluation tests
    
- evidence tests
    
- reproducibility tests
    
- critical UX tests
    

### Threshold

> **100% of release-blocking tests pass.**

No known P0 or unresolved release-blocking P1 defect.

---

# 44. AT-40 — Analytical Golden Dataset

DAH must maintain deterministic datasets specifically designed to test:

- aggregation
    
- filtering
    
- joins
    
- missingness
    
- duplicates
    
- dates
    
- percentages
    
- segmentation
    
- statistical calculations
    
- validation
    

### Threshold

> **100% of deterministic reference calculations must match expected results within defined tolerance.**

These datasets become the analytical correctness foundation of the product.

---

# 45. AT-41 — Finding-to-Evidence Integrity

The system must prevent a finding from appearing validated when its evidence is missing or invalid.

### Threshold

> **100% of validation-state transitions must enforce evidence requirements.**

A finding with missing mandatory evidence cannot enter the `VALIDATED` state.

---

# 46. AT-42 — Validation-State Integrity

The system must prevent invalid state transitions.

Example:

```text
Draft
 ↓
Evidence Attached
 ↓
Validation
 ↓
Validated
```

A finding must not transition directly from:

```text
Draft → Validated
```

without satisfying required validation rules.

### Threshold

> **100% of invalid transition attempts are rejected.**

---

# 47. AT-43 — Export Integrity

Exported Analysis Cases must preserve the analytical structure.

### Threshold

For the export regression suite:

- 100% required sections present
    
- 100% findings included
    
- 100% validation states preserved
    
- 100% evidence references preserved
    
- 100% case metadata preserved
    

---

# 48. AT-44 — Auditability

Important analytical actions must produce an identifiable record.

Minimum events:

- dataset import
    
- analysis execution
    
- AI proposal
    
- AI approval
    
- result creation
    
- finding creation
    
- validation
    
- export
    

### Threshold

> **≥ 99.9% of defined auditable events must be recorded correctly in integration tests.**

---

# 49. AT-45 — MVP Data Size Envelope

The MVP must explicitly define its supported dataset envelope rather than claiming unlimited scale.

Recommended initial benchmark:

```text
CSV / Parquet:
≤ 5 million rows
≤ 100 columns
```

Excel:

```text
≤ 500,000 rows
```

The exact limits may be revised after benchmarking.

### Acceptance

The application must either:

1. successfully process datasets inside the supported envelope, or
    
2. clearly reject/limit datasets outside the envelope.
    

It must never silently fail.

---

# 50. AT-46 — Analysis Case Size Envelope

Initial supported case:

```text
≤ 100 analysis runs
≤ 500 results
≤ 200 findings
≤ 1,000 evidence relationships
```

These are engineering benchmark limits, not conceptual product limits.

The application must remain stable within the supported envelope.

---

# 51. AT-47 — Export/Reopen Round Trip

A saved/exported case should survive:

```text
Create
→ Save
→ Export
→ Reopen/import
→ Inspect
```

### Threshold

> **100% preservation of required analytical objects in the round-trip test suite.**

---

# 52. AT-48 — Requirement Traceability

Every P0/P1 product requirement must map to:

```text
PRD
 ↓
UX
 ↓
Implementation
 ↓
Test
 ↓
Verification
```

### Threshold

> **100% of P0 requirements traceable**

and:

> **≥ 95% of P1 requirements traceable**

before the corresponding release gate.

---

# 53. Release Blocking Thresholds

The following automatically block release:

```text
P0
├── Data loss
├── Fabricated evidence
├── Fabricated execution
├── Incorrect validated finding
├── Broken evidence chain
├── Critical security vulnerability
├── Critical analytical calculation error
└── Application cannot recover from normal critical failures
```

Any P0 defect:

> **Must be resolved before release.**

---

# 54. P1 Threshold

A P1 defect normally blocks the relevant milestone.

Release requires:

```text
0 unresolved P0
AND
0 unresolved release-blocking P1
```

Any exception requires an explicit documented decision.

---

# 55. MVP Definition of Done

The MVP is complete only when:

```text
                 MVP
                  │
      ┌───────────┼───────────┐
      ↓           ↓           ↓
   PRODUCT      ANALYSIS     TRUST
      │           │           │
      ↓           ↓           ↓
 Functional   Correctness   Evidence
      │           │           │
      └───────────┼───────────┘
                  ↓
              Validation
                  ↓
             Reproducibility
                  ↓
                  UX
                  ↓
              Production
```

Specifically:

### Functional

≥ 95% core workflow completion.

### Analytical

100% golden deterministic calculations correct.

### Evidence

100% valid finding evidence chains.

### Validation

≥ 95% detection on defined analytical validation cases.

### AI

0 fabricated execution/evidence claims.

### Reproducibility

100% deterministic golden analyses reproducible.

### Reliability

0 P0 defects.

### Security

0 Critical vulnerabilities.

### UX

≥ 8/10 representative users complete the core workflow without facilitator intervention.

---

# 56. Acceptance Threshold Hierarchy

Not every metric has equal importance.

```text
LEVEL 0 — Safety / Trust
0 tolerance

Level 1 — Correctness
≈ 100%

Level 2 — Reliability
≥ 99%+

Level 3 — AI / Detection Quality
≈ 90–99%

Level 4 — Performance
95th percentile targets

Level 5 — UX
≥ 80% successful task completion
```

The most important principle is:

> **DAH should sacrifice convenience before it sacrifices analytical trust.**

---

# 57. Measurement Sources

Acceptance thresholds must be measured using:

### Automated Tests

For:

- calculations
    
- state transitions
    
- persistence
    
- import
    
- execution
    
- evidence
    
- validation
    

### Golden Datasets

For:

- analytical correctness
    
- profiling
    
- quality detection
    
- reproducibility
    

### AI Evaluation Suite

For:

- relevance
    
- hallucination
    
- causal reasoning
    
- structured output
    
- execution honesty
    

### Performance Benchmarks

For:

- startup
    
- case loading
    
- profiling
    
- execution
    
- UI responsiveness
    

### Usability Tests

For:

- workflow comprehension
    
- discoverability
    
- evidence understanding
    
- validation understanding
    

---

# 58. Acceptance Evidence

Every completed requirement should produce evidence such as:

```text
Requirement
    ↓
Test ID
    ↓
Test Result
    ↓
Metric
    ↓
Threshold
    ↓
PASS / FAIL
```

Example:

```text
AT-17 Validation Coverage

Test cases: 40
Detected: 39
Detection rate: 97.5%
Threshold: ≥95%

PASS
```

This makes product readiness measurable rather than subjective.

---

# 59. Requirement Traceability Matrix

The implementation process should maintain:

|Requirement|UX|Domain|Implementation|Test|Threshold|Status|
|---|---|---|---|---|---|---|
|FR-01 Case Management|✓|✓|✓|✓|100% persistence||
|FR-05 Data Import|✓|✓|✓|✓|≥99% valid imports||
|FR-07 Data Quality|✓|✓|✓|✓|≥95% detection||
|FR-10 SQL|✓|✓|✓|✓|100% golden results||
|FR-14 Evidence|✓|✓|✓|✓|100% traceability||
|FR-16 Validation|✓|✓|✓|✓|≥95% detection||
|FR-18 AI|✓|✓|✓|✓|0 fabricated evidence||
|FR-23 Search|✓|✓|✓|✓|defined MVP scope||
|FR-24 Persistence|✓|✓|✓|✓|0 data loss||

This matrix becomes an engineering control artifact.

---

# 60. Final PRD Acceptance Contract

DAH is not accepted because:

> "The application works."

It is accepted when:

```text
The workflow works
        +
The calculations are correct
        +
The evidence is traceable
        +
The findings are validated
        +
The analysis is reproducible
        +
AI does not fabricate analytical reality
        +
The application is usable
        +
The system is stable and secure
```

Therefore the final product contract is:

> **DAH must produce not merely an answer, but a measurable, inspectable, evidence-backed analytical process whose important claims can be traced, validated, and reproduced.**

This gives Artifact **04** a much stronger engineering role: **the PRD now tells the coding agent not only what to build, but what “done” quantitatively means.**