# DAH - Task Backlog

## P0 Foundation - PASSED

| Task ID | Status | Verification |
|---------|--------|--------------|
| P0-INFRA-001 | DONE | pytest passes; live `GET /health` returns 200 |
| P0-WEB-002 | DONE | Vitest 2/2 pass; build succeeds; `/api` proxy reaches backend |
| P0-DATA-003 | DONE | 5/5 pytest pass; case survives restart; DuckDB profiles CSV |

## P1 Vertical Slice - PASSED

| Task ID | Status | Verification |
|---------|--------|--------------|
| P1-DATA-001 | DONE | CSV attaches, file on disk, survives reopen |
| P1-DATA-002 | DONE | profile (rows/columns/null counts) stored against dataset |
| P1-ANALYSIS-003 | DONE | read-only SQL runs persisted with results |
| P1-EVIDENCE-004 | DONE | evidence chain finding -> run -> dataset |
| P1-VALID-005 | DONE | rerun reproduces or demotes the finding |

## P2 MVP

Goal: turn the vertical slice into a genuinely usable analytical application.
The loop is proven; P2 broadens it. AI joins last, only after the deterministic
surface is complete (roadmap section 5).

```
Parquet/Excel + richer profiling + Python execution + charts
+ case management + AI planning (structured) + export
```

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P2-DATA-006 | Data Layer (breadth) | M | DONE | P1 done | Parquet and Excel attach alongside CSV |
| P2-DATA-007 | Data Layer (depth) | M | DONE | P2-DATA-006 | Profile covers duplicates, types, basic stats |
| P2-ANALYSIS-008 | Analysis Workspace | M | DONE | P2-DATA-006 | Read-only Python executes against a dataset, result persisted |
| P2-ANALYSIS-009 | Analysis Workspace | M | DONE | P2-ANALYSIS-008 | Chart image persisted from a run result |
| P2-CASE-010 | Analysis Case | M | DONE | P1 done | Rename, duplicate, delete cases |
| P2-AI-011 | AI Planning | M | DONE | P2-ANALYSIS-008 | Structured plan (sub-questions, hypotheses) from a question + profile |
| P2-CASE-012 | Export | M | DONE | P2-AI-011 | Case exports as a self-contained JSON package |

## P3 V1

Goal: make the MVP substantially better for repeated real-world use (roadmap
section 6). Entry order follows ai/ROADMAP.md; hardening first because the P3
AI code-generation work multiplies the risk of the P2 soft sandbox.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P3-SEC-001 | Analysis Workspace (hardening) | M | DONE | P2-ANALYSIS-008 | Python runs in a separate process under an OS sandbox; writes outside scratch, network, and runaway CPU are bounded and reported as 400 |
| P3-CHART-002 | Analysis Workspace (raster charts) | M | DONE | P3-SEC-001 | PNG rendering behind the same interface; bar geometry and export round trip verified |
| P3-DATA-003 | Data Layer (multi-dataset) | M | DONE | P2 done | Join runs across attached files; validation, duplicate, export all carry the dataset list |
| P3-FLOW-004 | Analysis workflow (guided) | M | DONE | P3-DATA-003 | Derived stage and single next action from the case's artifacts |
| P3-ANALYSIS-005 | Analysis Workspace (richer EDA) | M | DONE | P3-FLOW-004 | Segment / correlate / distribution compile to read-only SQL |
| P3-EVIDENCE-006 | Evidence (richer lineage) | M | DONE | P3-ANALYSIS-005 | Case-wide evidence graph with claim-to-source tracing |
| P3-CASE-007 | Analysis Case (reuse) | M | DONE | P3-EVIDENCE-006 | Case search, case history timeline, and case templates |

## P4 Production Candidate

Goal: make DAH reliable, secure, usable and observable enough for controlled
external users (roadmap section 7). Entry order follows ai/ROADMAP.md's
checklist; the gate comes first because a phase is done when a gate says so.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P4-VERIFY-001 | Verification (P3 gate) | M | DONE | P3 complete | One journey exercises multi-dataset joins, the hard sandbox and all four assistant slices end to end |
| P4-RELIABILITY-002 | Reliability | M | DONE | P4-VERIFY-001 | Input errors answer 400 with the engine's message; a harness fault answers 500 instead of a 400 that blamed the analyst |
| P4-UX-003 | UX (case workspace + chat) | M | DONE | P4-RELIABILITY-002 | Cases can be searched and opened; the workspace shows the derived stage, datasets and runs, and the case answers questions with visible citations |
| P4-UX-004 | UX (run-scoped assistant surfaces) | M | DONE | P4-UX-003 | The workspace walks the loop one panel per step - attach+profile, generate code, run, interpret, draft, accept, validate - and every write posts to the endpoint that owns it |
| P4-VALID-005 | Validation (rerun determinism) | M | DONE | P4-UX-004 | Reproduction compares SQL rows as a multiset, so an unordered GROUP BY answering in a different order is a match, not a drift |
| P4-PERF-006 | Performance (large datasets) | M | DONE | P4-VALID-005 | Profiling no longer materialises every row to read a description; the result cap and profile correctness are pinned at scale |
| P4-CI-007 | Distribution (CI + signing decision) | M | DONE | P4-PERF-006 | macOS CI runs the server suite and both gates, the web suite and build, the desktop lifecycle tests against a live core, and a sidecar packaging build; signing deferred to P5 by DEC-004 |

## P5 Production Grade

Goal: make DAH tested, hardened, distributable, maintainable, observable and
supportable (roadmap section 8). Entry order follows ai/ROADMAP.md's checklist;
the gate comes first because a phase is done when a gate says so.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P5-VERIFY-001 | Verification (P4 gate) | M | DONE | P4 complete | One journey walks the edges: the error taxonomy, rerun determinism, the result cap, graceful degradation |
| P5-OBSERVE-002 | Observability | M | DONE | P5-VERIFY-001 | The core writes a size-capped rotating log into the user's data dir, `GET /logs` tails it read-only, and nothing the analyst typed ever lands in it |
| P5-RELIABILITY-003 | Error contract | M | DONE | P5-OBSERVE-002 | A 500 answers a JSON envelope with a request id that maps to the traceback in the log, and the id is surfaced to the user |
| P5-CI-004 | CI floor | S | DONE | P5-RELIABILITY-003 | Every job runs on macos-13 (Ventura), the minimum supported macOS, and the packaged-core smoke now asserts file logging lands in the data dir |
| P5-RELEASE-005 | Release automation | M | DONE | P5-CI-004 | A tag matching server/pyproject.toml's version builds, smokes and publishes an unsigned .app as a flagged pre-release with its checksum |
| P5-UX-006 | Shell UX | S | DONE | P5-RELEASE-005 | A Reveal DAH Logs menu item asks the core where its log is and opens the folder in Finder with it selected |

### Carried follow-ups (still open)

- Validation of Python runs still answers a clear 400 "not supported yet". The
  hard sandbox (P3-SEC-001) makes re-execution safe, so the gate is now
  implementable: rerun the stored script in the sandbox and compare the result
  shape, the way SQL validation compares rows. DELIVERED as P3-VALID-010.
- The packaged app is unsigned: macOS gatekeeps the first launch (right-click,
  Open). Signing and notarization are P5.

## P6 Post-Launch Evolution

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P6-MEMORY-001 | Analysis memory (cross-case recall) | DONE | 11 tests in test_memory.py; P2/P3/P4 gates PASS |
| P6-AGENT-002 | Agentic analysis | DONE | 24 tests in test_agent.py; P2/P3/P4 gates PASS |
| P6-TEMPLATE-003 | Case reuse (templates carry the shape) | DONE | +11 tests in test_case_templates.py; P2/P3/P4 gates PASS |
| P6-MIGRATE-004 | Maintainability (versioned migration path) | DONE | 13 tests in test_migrations.py; P2/P3/P4 gates PASS |
| P6-UPDATE-005 | Distribution (update check) | DONE | 21 tests in test_updates.py + 7 Rust tests; P2/P3/P4 gates PASS |

## P7 Product Modes

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P7-EVAL-001 | EVALUATE mode (audit existing work) | DONE | 22 tests in test_evaluator.py; P2/P3/P4 gates PASS |
| P7-SHELL-002 | UX (EVALUATE in the web shell) | DONE | +6 tests in CaseWorkspace.test.tsx; web build PASS |

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
### P7-EVAL-001 contract
```
TASK ID: P7-EVAL-001
MILESTONE: P7 Product Modes
CAPABILITY: EVALUATE mode
GOAL: Audit existing analytical work. A user submits work someone already did -
      a SQL query and the claim it was used to support - and DAH answers the
      nine questions the specification names, each against the data rather than
      against the claim's own confidence.

CONTEXT: the master specification defines three product modes. ANALYZE is the
         one that exists and it is finished through P6. EVALUATE is the second:
         "audit existing analytical work", over inputs that can include SQL,
         Python, a notebook, a dashboard, a spreadsheet, a report or
         AI-generated analysis, judged on Question / Data / Quality / Method /
         Calculation / Evidence / Claim / Visualization / Limitations.
         Most of the machinery already exists and is validated - read-only
         execution with a row cap, deep profiling, rerun determinism, the
         evidence graph, the honesty budgets that bound what a claim may quote.
         What does not exist is the frame: today every one of those primitives
         serves the user's *own* analysis. EVALUATE turns them on work that
         came from elsewhere, and that turn is the whole task.

INPUTS: a case with at least one attached, profiled dataset; a submitted
        artifact - its code (SQL or Python), the kind, and the claim the code
        was offered as evidence for.
RELEVANT FILES: server/app/evaluator.py (NEW), server/app/main.py,
                server/app/models.py, server/app/db.py,
                server/tests/test_evaluator.py (NEW)
REQUIRED CHANGE:
  - server/app/evaluator.py: a pure module, the way evidence.py and workflow.py
    are pure. `evaluate` takes the artifact, the dataset's profile and the
    run it produced, and returns one finding per spec axis. Nothing is computed
    that the data does not contain; nothing is asserted the run does not show.
  - the nine axes, each a named check with a verdict and a sentence:
    * Question - the claim is stated and is answerable from this dataset.
    * Data - every column the code reads exists in the profile, and the
      profile's own caveats (nulls, duplicates) are surfaced as limitations.
    * Quality - the profile's missing-value and duplicate-row counts reach the
      verdict, so a claim over a column that is 40% null is a *finding*, not a
      pass.
    * Method - the code is read-only (the existing gate), bounded by the row
      cap, and deterministic: an artifact whose result depends on unordered
      output is flagged, because a rerun could disagree without anything
      changing.
    * Calculation - the code runs, and it reproduces: the artifact is executed
      twice and the two results must agree, the same standard a finding's
      validation holds (P4-VALID-005).
    * Evidence - the claim's magnitudes all appear in the result the code
      actually produced, checked against the same honesty budget a draft is
      checked against (P3-AI-012): a claim quoting a number the run does not
      contain is the single most common way an analysis lies.
    * Claim - the claim is specific enough to be wrong: it names a magnitude or
      a direction, not only a topic. "Revenue declined in north" is auditable;
      "revenue was analysed" is not, and the verdict says so.
    * Visualization - whether the artifact's result is chartable, and if a
      chart exists, whether its axes match the result's own columns. Not a
      requirement that one exist - an honest "no chart, and none needed" is a
      valid verdict.
    * Limitations - the accumulated caveats, stated as sentences rather than
      as an error code.
  - POST /cases/{id}/datasets/{id}/evaluate accepts the artifact and the claim,
    executes the code through the *existing* run endpoints' engine (never a
    second code path), and returns the evaluation. It writes the artifact as a
    run and the evaluation beside it, so an audit is itself inspectable and
    reproducible - the standard every other artifact in DAH is held to.
  - GET .../evaluations lists them, newest first, the same as runs and plans.
  - the endpoint refuses an artifact whose code is not read-only, exactly as
    the run endpoints do, and refuses a claim that is empty; both are 400s with
    a message, never a 500.
NON-GOALS: evaluating a notebook, a dashboard, a spreadsheet or a report as a
           whole file (this task takes the code and the claim, which is the
           common core of all of them; whole-file ingestion is a later task),
           an LLM judgement of the claim (deterministic by default, as every
           other assistant slice is - the LLM may later rephrase, never
           decide), a score or a grade (a verdict per axis with a sentence is
           the honest output; a number would imply a precision the axes do not
           have), evaluating an artifact against a dataset it never ran
           against, fixing the artifact.
CONSTRAINTS: the code executes under the same read-only gate, row cap and
             (for Python) hard sandbox as any other run - EVALUATE earns no
             privilege, and untrusted code is the *premise* of the mode; the
             honesty budgets from P3-AI-011..014 are reused unchanged; an
             evaluation never mutates the case, the dataset or any run, only
             appends its own row; nothing the analyst submitted is logged (the
             log holds method/path/status/duration, as P5-OBSERVE-002 pins);
             deterministic by default with `source` recorded; no new runtime
             dependency; the suite, the P2/P3/P4 gates, the web and desktop
             suites stay green.
ACCEPTANCE CRITERIA:
- [x] a clean artifact over a clean dataset passes all nine axes
- [x] an artifact reading a column the dataset lacks is flagged on Data, not
      silently passed
- [x] a claim quoting a magnitude absent from the result is flagged on
      Evidence with the value it should have been
- [x] a claim too vague to be wrong ("revenue was analysed") is flagged on
      Claim
- [x] a non-deterministic artifact (unordered output treated as a ranking) is
      flagged on Method
- [x] an artifact over a mostly-null column reports the null share as a
      Quality limitation, not a pass
- [x] an artifact that does not reproduce is flagged on Calculation
- [x] a non-read-only artifact is refused with 400 before anything executes
- [x] an evaluation is persisted, listed and inspectable; it never mutates
      another artifact
- [x] every verdict carries a sentence a reader can act on, not only a code
- [x] the full server suite, the P2/P3/P4 gates, the web suite and the desktop
      tests stay green
TESTS: server/tests/test_evaluator.py - the clean baseline; each axis's failure
       case (unknown column, invented magnitude, vague claim, unordered
       ranking, null-heavy column, non-reproducing artifact, non-read-only
      refusal); the persistence and listing round trip; the no-mutation
       invariant; 404s including a cross-case dataset.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS;
              cd desktop/src-tauri && cargo test PASS.
STATE UPDATE: mark P7-EVAL-001 done on pass; ROADMAP item 1 flips to DONE.
```


```
TASK: P7-EVAL-001 - audit existing analytical work against nine axes
ID: P7-EVAL-001
PRIORITY: high
STATUS: DONE
SUMMARY: EVALUATE mode - the spec's second product mode. Until now every
         primitive DAH has served the analyst's *own* work: read-only
         execution, deep profiling, rerun validation, the evidence graph, the
         honesty budgets. This task turns those primitives on work that came
         from elsewhere. A user submits an artifact - its code (SQL or Python)
         and the claim that code was offered to support - and DAH answers the
         nine questions the specification names, each against the data rather
         than against the claim's own confidence.

Three pieces:

- **`server/app/evaluator.py` (new)** - a pure module, the way evidence.py and
  workflow.py are pure. `evaluate()` returns one finding per axis - question,
  data, quality, method, calculation, evidence, claim, visualization,
  limitations - each a verdict (pass / concern / fail, deliberately not a
  score: a single number would imply a precision nine heterogenous axes do not
  have) and a sentence a reader can act on. The Evidence axis reuses the
  drafter's honesty budget unchanged (`_allowed_numbers`, `_numbers_in`), so a
  claim quoting a magnitude the run does not contain is caught by the same
  standard a draft is judged by.
- **`POST /cases/{id}/datasets/{id}/evaluate`** - executes the artifact through
  the *existing* run engine, never a second code path, so the read-only gate,
  the row cap and the hard sandbox are the ones every other run answers to.
  EVALUATE earns no privilege, and untrusted code is the premise of the mode.
  The artifact is stored as a run and the evaluation beside it, so an audit is
  itself inspectable and reproducible. `GET .../evaluations` lists them newest
  first.
- **`server/app/db.py`** - the `evaluations` table, migration 8, so an audit is
  a first-class artifact rather than a transient response.

Four judgement calls the contract left open, each written into the code:

- **A non-read-only artifact is a 400 before anything executes**, exactly as the
  run endpoints refuse one. A mutation is not an artifact to audit - it is a
  request the store must never honour, and it is refused before the engine is
  asked to do anything. But an artifact that *is* read-only and still fails at
  run time is a **Calculation finding, not a 400**: the work is not the user's
  to fix, it came from elsewhere, and "this does not run" is the answer an
  auditor exists to give.
- **An unknown column is a Data fail, never a silent pass.** The first version
  of the check intersected the code's identifiers with the profile's columns,
  which drops every name the dataset lacks - the axis passed on exactly the
  case it exists to catch. The fix reuses the generator's own notion of a
  column read (`_sql_identifiers`, `_python_read_columns`, `_SQL_KEYWORDS`),
  so an invented name is *reported* rather than filtered away.
- **A chart is not required.** The contract's baseline is that a clean artifact
  passes all nine axes, and "no chart, and none needed" is a valid verdict,
  because a table's numbers are checkable without one. What *is* a fail is a
  chart whose axes are not the result's own columns - a check the previous
  shape (a bare `has_chart` boolean) could not make, because a boolean cannot
  be wrong.
- **A single-row result is deterministic without an ORDER BY**, because one row
  has no row order to disagree about; the Method axis flags only an unordered
  *multi-row* result, whose order a rerun may present differently.

NON-GOALS held: no whole-file ingestion of notebooks, dashboards or
             spreadsheets (this task takes the code and the claim, which is the
             common core of all of them), no LLM judgement of the claim
             (deterministic by default, as every assistant slice is; an LLM may
             later rephrase a sentence, never decide one), no score or grade,
             no evaluating an artifact against a dataset it never ran against,
             no fixing the artifact.
CONSTRAINTS held: the code executes under the same read-only gate, row cap and
             hard sandbox as any other run; the honesty budgets from
             P3-AI-011..014 are reused unchanged; an evaluation appends its own
             row and mutates nothing else (pinned by a test that counts runs,
             findings and evaluations around one); nothing the analyst
             submitted is logged (the log holds method/path/status/duration, as
             P5-OBSERVE-002 pins); deterministic, `source` recorded; no new
             runtime dependency; the suite, the gates and the web and desktop
             suites stayed green.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 22 in server/tests/test_evaluator.py - the clean baseline across all nine
       axes, each axis's failure case (unknown column, invented magnitude, vague
       claim, unordered ranking, null-heavy column, non-reproducing artifact,
       artifact that does not run), the read-only refusal with nothing written,
       the empty-code / empty-claim / bad-kind 400s, both the SQL and the Python
       artifact paths, persistence and newest-first listing, the no-mutation
       invariant, 404s including a cross-case dataset, the unprofiled dataset,
       and the pure module's chart branches - which the endpoint cannot reach,
       because a chart cannot exist for the run the request itself creates.
VERIFICATION: server suite 358 passed (was 336, +22); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 358); web 21 passed; desktop 22
              Rust tests. All green locally; CI will run it on push.
LESSON: three of the eleven criteria were satisfied by code that had not been
        written yet, and the missing half was the interesting half. The Data
        axis "passed" an unknown column because it asked "which of the code's
        names are in the profile?" instead of "which are NOT?"; the
        Visualization axis could never pass at all, because it treated the
        absence of a chart as a defect the contract explicitly calls a valid
        verdict; and the read-only refusal had been softened into a Calculation
        finding, which is kinder but is not what the contract asks. Each was
        found the same way - reading the acceptance criteria as assertions and
        asking what code would make each one true. The general shape: a check
        that filters its inputs before testing them is testing the survivors,
        and a check that cannot fail cannot pass either.
```

### P7-SHELL-002 contract

```
TASK ID: P7-SHELL-002
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A user can hand DAH work that came from elsewhere and read the nine-axis
      audit without a terminal. POST .../evaluate answers nine verdicts and
      nothing in the shell reaches it today; this task puts a surface in front
      of it.

CONTEXT: P7-EVAL-001 shipped the core half of EVALUATE mode. The web shell
         walks the ANALYZE loop one panel per step - data, runs, findings,
         chat - and every one of those panels posts to the endpoint that owns
         its write. The evaluate endpoint is the first endpoint with no panel
         at all, and it is the flagship capability of the phase, so closing
         that one gap is the slice of the web-shell work that pays first. The
         other un-UI'd endpoints (the agent, templates, memory, EDA, the
         evidence graph, case history, case management) are later tasks in the
         same checklist item, not this one.

INPUTS: a case with at least one attached, profiled dataset; the artifact's
        code, its kind (SQL or Python) and the claim it was offered to support,
        typed or pasted.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `AxisFinding` and `Evaluation` interfaces matching the
    core's models, plus `evaluateDataset(caseId, datasetId, code, claim, kind)`
    and `listEvaluations(caseId, datasetId)`. Failures travel as `ApiError`, so
    a 400's `detail` and a 500's `request_id` reach the panel unchanged - the
    existing error contract, not a new one.
  - web/src/CaseWorkspace.tsx: an `EvaluatePanel`, shown once the case has a
    profiled dataset (an unprofiled case has no columns to audit against, and
    the panel says so rather than offering a submission that cannot succeed).
    A kind toggle between SQL and Python, a textarea for the code, an input for
    the claim, and a submit that posts to the evaluate endpoint and nothing
    else. The audit renders as nine rows, one per axis in the spec's order,
    each with its verdict as a badge - pass / concern / fail - and its sentence;
    the verdict is the summary and the sentence is the substance, so neither is
    rendered without the other. Audits already recorded over that dataset are
    listed below, newest first, so an audit is itself inspectable from the
    workspace the way a run is.
  - The panel degrades rather than breaking: a 400 (a non-read-only artifact,
    an empty code or claim, an unknown kind) shows the core's own message
    inline and the panel stays usable, because that message is the actionable
    thing - "only single read-only SELECT queries are supported" tells the
    user what to change. A 500 shows the message with its request id, as every
    other panel does.
  - When the case has several datasets the panel offers a chooser, because the
    axis verdicts are per-dataset - an artifact audited against the wrong file
    would fail every column check for a reason that is not the artifact's.
NON-GOALS: ingesting a whole notebook, dashboard, spreadsheet or report as a
           file (this task takes the code and the claim, the common core, as
           P7-EVAL-001 did), editing or re-running a past audit's artifact (the
           artifact is already stored as a run and appears in the Runs panel),
           a chart or score over the audit (the core deliberately returns no
           score), an LLM phrasing of the verdicts (deterministic, as the core
           is), a mode switcher that reorganises the workspace around ANALYZE /
           EVALUATE / LEARN (the workspace is ANALYZE's loop; EVALUATE is a
           labelled panel beside it, and a mode architecture is a later
           design), the other un-UI'd endpoints (each is its own task).
CONSTRAINTS: every write posts to the evaluate endpoint - the panel proposes
             nothing else and creates no run, finding or chart of its own;
             deterministic; no new dependency; the existing panels and their
             tests are unchanged; `tsc -b` passes (the build is CI's type gate,
             and a type error the jsdom tests cannot see fails it); the desktop
             bundle builds from the same source, so nothing may assume a
             browser-only environment; nothing the analyst typed is logged by
             the core (P5-OBSERVE-002) and the shell adds no logging of its
             own; the server suite and the gates are untouched by this change
             and stay green.
ACCEPTANCE CRITERIA:
- [x] a case with a profiled dataset shows the EVALUATE panel; a case with no
      dataset or no profile does not
- [x] submitting clean work shows all nine axes, each with a pass verdict and
      its sentence, in the spec's order
- [x] a claim quoting a magnitude the run does not contain shows a fail on
      Evidence, with the value and the sentence
- [x] a non-read-only artifact shows the core's 400 message inline; the panel
      stays usable and no audit was recorded
- [x] an audit is recorded and listed afterwards, newest first, with its claim
      and its nine verdicts
- [x] the kind toggle switches the submission between SQL and Python
- [x] a failed request never crashes the workspace: the error is a sentence
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the clean nine-axis baseline, the
       invented magnitude on Evidence, the read-only refusal rendered as a
       sentence, the recorded audit listed newest first, the panel's absence
       without a profiled dataset, and the kind toggle.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS (tsc -b
              runs first, so a type error the jsdom tests cannot see fails
              it). The server suite and the three gates are unchanged.
STATE UPDATE: mark P7-SHELL-002 done on pass; ROADMAP item 2 records EVALUATE's
              surface as delivered.
```


```
TASK: P7-SHELL-002 - EVALUATE mode in the web shell
ID: P7-SHELL-002
PRIORITY: high
STATUS: DONE
SUMMARY: The core half of EVALUATE mode shipped with P7-EVAL-001 and nothing
         in the shell could reach it. The web workspace walks the ANALYZE loop
         one panel per step - data, runs, findings, chat - and the evaluate
         endpoint was the first one with no panel at all, in the phase whose
         flagship capability it is. This task puts a surface in front of it
         without adding a single endpoint, contract or dependency: the panel
         only renders what the core already answers.

Two files of substance:

- **`web/src/api.ts`** - `AxisFinding` and `Evaluation` interfaces matching the
  core's models, and the two functions the panel needs: `evaluateDataset` (the
  submission) and `listEvaluations` (so an audit is inspectable after the fact,
  the way a run is). Failures travel as `ApiError`, so a 400's `detail` and a
  500's `request_id` reach the panel unchanged - the error contract the rest of
  the shell already uses, not a new one.
- **`web/src/CaseWorkspace.tsx`** - an `EvaluatePanel` placed after the loop it
  audits and before the assistant. It appears once a dataset is profiled (an
  unprofiled case has no columns to audit against, so the panel says so rather
  than offering a submission that cannot succeed); offers a kind toggle, a code
  textarea and a claim input; and renders nine rows - one per axis in the
  spec's own order - each a verdict badge and its sentence, because the verdict
  is the summary and the sentence is the substance and neither is rendered
  without the other. Recorded audits list below, newest first. With several
  datasets there is a chooser, because the verdicts are per-dataset and an
  artifact audited against the wrong file fails every column check for a reason
  that is not the artifact's.

The panel holds to the discipline every other panel keeps: the submit posts to
the evaluate endpoint and nothing else. The panel never runs code and never
decides whether work is sound - the endpoint does, under the same read-only
gate, row cap and hard sandbox as any other run. A 400 is part of the contract
rather than a failure: a non-read-only artifact is refused before anything
executes, and its detail ("only single read-only SELECT queries are supported")
is shown as a sentence next to a panel still ready for corrected work.

NON-GOALS held: no whole-file ingestion of notebooks, dashboards or
             spreadsheets (the code and the claim, as P7-EVAL-001 took them),
             no editing or re-running a past audit's artifact (it is already a
             run, in the Runs panel), no chart or score over the audit (the core
             returns neither), no LLM phrasing of verdicts, no mode switcher
             reorganising the workspace around ANALYZE/EVALUATE/LEARN - the
             workspace is ANALYZE's loop and EVALUATE is a labelled panel
             beside it; a mode architecture is a later design, and the other
             un-UI'd endpoints (the agent, templates, memory, EDA, the evidence
             graph, case history, case management) are their own tasks.
CONSTRAINTS held: every write posts to the evaluate endpoint alone; the panel
             creates no run, finding or chart of its own; deterministic; no new
             dependency; the existing panels and their tests are unchanged;
             `tsc -b` passes (the build is CI's type gate, and a type error the
             jsdom tests cannot see fails it); the desktop bundle builds from
             the same source and nothing assumes a browser-only environment;
             the shell adds no logging of its own.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 6 added to web/src/CaseWorkspace.test.tsx (21 -> 27) - the clean
       nine-axis baseline scoped to the audit container, the failing Evidence
       axis with its value, the read-only refusal rendered as a sentence with
       the panel still usable, the recorded-audit listing newest first, the
       kind toggle reaching the endpoint with kind: "python", and the panel's
       absence without a profile.
VERIFICATION: cd web && npm test - 27 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS; the
              server suite is untouched by this change and stays at 358 passed.
LESSON: two of the six tests failed first for the same reason - the query, not
        the component. The nine verdict badges and the workflow's stage list
        both render a checkmark and an axis name ("✓ question"), so a page-wide
        `getByText` found two elements; and userEvent parses `[` and `]` as key
        descriptors, so typing `result = []` was read as a key sequence. The
        fix for the first was to scope the query to the audit's own container
        with `within` - an assertion should name where it is looking, because a
        page is not a component. The second is a reminder that `user.type`
        types *keys*, not text: fixtures that stay clear of `[]{}` are cheaper
        than escaping them.
```

