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
| P7-SHELL-003 | UX (the agent in the web shell) | DONE | +7 tests; web build PASS |

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

### P7-SHELL-003 contract

```
TASK ID: P7-SHELL-003
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A plan that executes itself one approved write at a time is observable
      only through the API today. This task gives it a surface: the workspace
      shows what the agent proposes, and the human's yes or no is a button
      rather than a curl.

CONTEXT: P6-AGENT-002 shipped the driver. It proposes a step; the human
         approves it by id; the write runs through the endpoint that already
         owns it. Four endpoints serve it - a read-only GET, an idempotent
         proposing POST, /approve and /reject - and not one of them has a
         panel. This is the highest-value of the un-UI'd endpoints, because the
         agent is the capability that most changes what the workspace is for:
         every other panel is a step, and this one is the loop.

INPUTS: a case with artifacts (or none - the agent's first step is to profile,
        if a dataset is attached but unprofiled).
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `AgentStep` and `AgentState` interfaces matching the core's
    models, and the four functions - `getAgentState` (read-only),
    `proposeAgentStep` (idempotent), `approveAgentStep(stepId)` and
    `rejectAgentStep(stepId, reason?)`.
  - api.ts also fixes a real gap the 409 exposes: the agent's approve/reject
    answer 409 with an OBJECT as the detail (`{detail, expected, given}`), not
    a string. The existing client copies `body.detail` straight into the
    message, so a stale approval would render as "[object Object]". The client
    now unwraps a nested `detail` when the body sends one, so the sentence the
    core wrote reaches the user - the same standard every other failure path
    already meets.
  - web/src/CaseWorkspace.tsx: an `AgentPanel`, placed beside the workflow it
    drives. It loads the read-only state, a button proposes the next step
    (idempotent, so a second click is a no-op rather than a second write), and
    a pending step renders what it WILL do - one sentence per kind, built from
    the step's own payload, so the human approves something concrete rather
    than a promise, together with Approve and Reject buttons and an optional
    rejection reason that is recorded on the step. The history lists every
    step with its status and the note the write produced, so an agent-run case
    states what it did at every point. When nothing is pending and the trail
    ends in `end`, the panel shows why the agent stopped, because an abandoned
    case should say so rather than fall silent.
  - A stale approval is a 409, never a second write: the panel shows the
    sentence and reloads, because the pending step it was looking at is no
    longer the case's pending step.
NON-GOALS: autonomy (the write never happens without the button; that is
           P6-AGENT-002's contract and this task does not relax it), editing a
           proposal before approving it (the payload is settled at proposal
           time by design - rejecting and re-proposing is the path), running
           the agent in the background or on a timer, an agent over multiple
           cases, the other un-UI'd endpoints (templates, memory, EDA, the
           evidence graph, case history, case management - each its own task).
CONSTRAINTS: the panel writes only through the four agent endpoints, and each
             write those endpoints perform still goes through the endpoint
             that owns it - the panel introduces no new write path, so the
             read-only gate, the row cap and the single finding-creation path
             are all still in force; the GET never proposes, so a page refresh
             commits nothing; deterministic; no new dependency; `tsc -b`
             passes; the existing panels and tests are unchanged; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] the panel shows the agent's state: a pending proposal, or the absence of
      one, with the history behind it
- [x] proposing is idempotent: a second call returns the same pending step and
      creates no second write
- [x] a pending step states what it will do, in a sentence built from its own
      payload, before the human decides
- [x] approving runs the step and the next proposal appears without a second
      click, with the step's note in the history
- [x] rejecting records the reason and writes nothing: no run, no finding
- [x] a stale approval is shown as a sentence, not "[object Object]", and the
      panel reloads rather than writing twice
- [x] a case the agent finished shows why it stopped
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the state rendering, the idempotent
       proposal, the payload sentence, the approve round trip, the reject with
       a reason, the 409 degradation, and the end reason.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS. The server
              suite and the three gates are untouched by this change and stay
              green.
STATE UPDATE: mark P7-SHELL-003 done on pass; ROADMAP item 2 records the agent
              surface as delivered.
```


```
TASK: P7-SHELL-003 - the agent as a surface in the web shell
ID: P7-SHELL-003
PRIORITY: high
STATUS: DONE
SUMMARY: A plan that executes itself one approved write at a time was
         observable only through the API. P6-AGENT-002 shipped the driver and
         four endpoints serve it - a read-only GET, an idempotent proposing
         POST, /approve and /reject - and not one had a panel. The workspace
         now carries an Agent panel beside the workflow it drives: it shows the
         pending proposal as a sentence built from the step's own payload, and
         the human's yes or no is a button.

Every other panel in the workspace is a step; this one is the sequence. It
keeps the agent's contract exactly - the write never happens without the
button, and the write then runs through the endpoint that owns it, so the
read-only gate, the row cap and the single finding-creation path are all still
in force for an agent-run case. The GET never proposes, so a page refresh
commits nothing; the proposing POST is idempotent, so an impatient second
click is a no-op rather than a second write; and approving a step that is no
longer the case's pending one is a 409 the panel shows as a sentence before
resyncing - never a second write.

One real gap the panel exposed in the client itself: the agent's 409 answers
with an OBJECT as the detail (`{detail, expected, given}`), and the typed
client copied `body.detail` straight into the message, so a stale approval
would have rendered as "[object Object]". The client now unwraps a nested
detail, so the sentence the core wrote reaches the user - the same standard
every other failure path already met.

NON-GOALS held: no autonomy (the write still waits for the button; that is
             P6-AGENT-002's contract and this task does not relax it), no
             editing a proposal before approving it (the payload is settled at
             proposal time by design - reject and re-derive is the path), no
             background or timer-driven running, no agent across cases, no new
             endpoints for the other un-UI'd capabilities.
CONSTRAINTS held: writes only through the four agent endpoints, each of which
             still writes through the endpoint that owns it; no new write path;
             deterministic; no new dependency; `tsc -b` passes; the existing
             panels and tests unchanged; the desktop bundle builds from the
             same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 7 added (web suite 27 -> 34) - six in CaseWorkspace.test.tsx: the state
       rendering, the idempotent proposal, the payload sentence, the approve
       round trip with the next proposal arriving in the same response, the
       reject with a reason writing nothing, the 409 shown as a sentence and
       never as "[object Object]", and the end reason; one in api.test.ts for
       the nested-detail unwrap.
VERIFICATION: cd web && npm test - 34 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched and stay green.
LESSON: the suite had no spy-reset between tests, so the module-level mocks
        accumulated call history across the file; the first negative assertion
        ("approve was not called") therefore answered for every test that had
        run before it. A beforeEach with vi.clearAllMocks is what makes "not
        called" mean "not called in this test". The same class of bug hid
        inside the component too: the panel's refresh() cleared the error
        before resyncing, so a 409 message was set and then erased a tick
        later - an error handler that runs after the thing it prepared for.
        Both are the same shape: state that outlives the action that produced
        it, read as though it were fresh.
```
