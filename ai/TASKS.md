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
| P7-SHELL-004 | UX (rename, duplicate, delete a case) | DONE | +5 tests; web build PASS |
| P7-SHELL-005 | UX (templates in the web shell) | DONE | +11 tests; web build PASS |
| P7-SHELL-006 | UX (cross-case memory actionable in the shell) | DONE | +4 tests; web build PASS |
| P7-SHELL-007 | UX (EDA in the web shell) | DONE | +6 tests; web build PASS |

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
### P7-SHELL-007 contract

```
TASK ID: P7-SHELL-007
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: The "what should I look at first" steps are reachable. Segment a measure
      by a category, correlate two columns, or read a column's spread - each
      one click from the profile - instead of a hand-written query the analyst
      only wrote because there was no button.

CONTEXT: P3-ANALYSIS-005 shipped `POST /cases/{id}/datasets/{id}/eda` with
         three ops (segment, correlate, distribution), each compiling to
         read-only SQL under the same gate and row cap as a hand-written query,
         and each deliberately *not persisted* - EDA is exploration, and a
         finding must anchor on a query the analyst wrote. Nothing in the shell
         reaches it, so the profile that names every column is shown one screen
         away from the question those columns pose.

INPUTS: a profiled dataset's columns and per-column types; the op and its
        column choices.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx, web/src/index.css,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `EdaOp`, an `EdaRequest` for the three ops' inputs, an
    `EdaResult` matching the core's, and `runEda(caseId, datasetId, request)`.
  - web/src/CaseWorkspace.tsx: an **EDA panel** between the data and runs
    panels - exploration sits between profiling and a hand-written query, which
    is where the core's own module puts it. It needs a profile (the columns are
    the inputs and the types decide which summary a distribution yields), and
    it says so rather than offering a submission that cannot succeed, the way
    the EVALUATE panel does. Where several datasets are profiled there is a
    chooser, because the ops are per-dataset.
    The op is a chooser and each op renders only its own column pickers:
    segment asks *by* and *measure*, correlate asks *x* and *y*, distribution
    asks one *column*. The profile's per-column type steers the defaults - a
    measure or a correlation axis defaults to a numeric column - but every
    column stays selectable, because the core's 400 is the honest answer to a
    wrong choice and the sentence is what teaches it.
    The result is a table of the columns the core returned, with the row count
    and a truncated marker. Nothing is kept: the panel says plainly that an EDA
    result is not a finding, and making it one is a query the analyst writes -
    the same discipline the runs and findings panels keep.
  - Every write is the one POST to the eda endpoint; a failure degrades to the
    core's own sentence and the panel stays usable for a corrected attempt.
NON-GOALS: persisting an EDA result (the core's contract is that exploration
           is not evidence; persistence would make a snapshot look like a
           finding), charts from EDA results (the chart endpoint belongs to a
           persisted run), generating the "equivalent query" from an op (the
           core does not return one, and inventing SQL the analyst did not
           write is exactly what EDA is not), new ops (their own task in the
           core), the evidence graph and case history (their own tasks).
CONSTRAINTS: the panel calls only the eda endpoint and reads only the profile;
             `tsc -b` passes; no new dependency; the existing workspace tests
             stay green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a profiled dataset offers the three ops with column pickers
- [x] each op shows only the inputs it takes
- [x] a segment returns a table grouped by the chosen category
- [x] a correlation returns the coefficient and the paired row count
- [x] a distribution adapts to a numeric or a categorical column
- [x] an unprofiled dataset explains itself rather than offering a run
- [x] a 400 shows the core's sentence and leaves the panel usable
- [x] the panel states that an EDA result is not a finding
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the three ops' round trips, the op
       chooser swapping pickers, the unprofiled message, and a refusal as a
       sentence.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-007 done on pass; ROADMAP item 2 records EDA as
              delivered.
```


```
TASK: P7-SHELL-007 - EDA in the web shell
ID: P7-SHELL-007
PRIORITY: medium
STATUS: DONE
SUMMARY: The "what should I look at first" steps were reachable only by
         writing a query. P3-ANALYSIS-005 shipped three ops - segment a measure
         by a category, correlate two columns, describe a column's distribution
         - each compiling to read-only SQL under the same gate and row cap as a
         hand-written query, and nothing in the shell could ask for one. The
         profile that names every column was shown one panel away from the
         question those columns pose.

A new **EDA panel** sits between the data and runs panels, which is where the
core's own module puts exploration: between profiling and a hand-written query.
The op is a chooser, and each op renders only its own pickers - segment asks
*by* and *measure*, correlate asks *x* and *y*, distribution asks one *column* -
so a question is asked with the shape of its answer, not a free-form form.

Four behaviours that had to be right rather than present:

- **The profile steers, but does not forbid.** A measure or a correlation axis
  defaults to a numeric column, read off the profile's per-column type family;
  every column stays selectable, because the core's 400 is the honest answer to
  a wrong choice and its sentence is what teaches the correction. A dataset with
  no numeric columns offers all of them and lets the core say why not.
- **A stale pick can never be submitted.** The pickers hold advisory state; the
  request is built from values resolved against the *current* dataset's columns,
  so a choice left over from another dataset or another op is replaced rather
  than sent.
- **The table is what the core returned.** A numeric distribution has seven
  columns and a categorical one has two, and the panel assumes neither - it
  renders the columns the answer carries. Numbers are rounded to four decimals
  for reading; the stored value is untouched.
- **Nothing is kept.** The panel says plainly that an EDA result is exploration,
  not evidence, and that making a finding of it is a query the analyst writes -
  the discipline the runs and findings panels keep. Switching ops drops an
  earlier result, because a distribution's answer is not an answer to a
  correlation's question.

NON-GOALS held: no persistence of an EDA result (the core's contract is that
             exploration is not evidence; persistence would make a snapshot
             look like a finding), no charts from EDA results (the chart
             endpoint belongs to a persisted run), no generated "equivalent
             query" (the core does not return one, and inventing SQL the analyst
             did not write is exactly what EDA is not), no new ops.
CONSTRAINTS held: the panel calls only the eda endpoint and reads only the
             profile; no new endpoint and no new dependency; `tsc -b` passes;
             the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA: all 9 - see the checked boxes above.
TESTS: 6 added to web/src/CaseWorkspace.test.tsx (web suite 54 -> 60) - the
       three ops' round trips, the op chooser swapping pickers, an earlier
       result dropping on an op change, the unprofiled message, and a 400 as a
       sentence with the op still runnable.
VERIFICATION: cd web && npm test - 60 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: four of the ten new and existing tests failed on the first run, and all
        four were the same failure - the workspace is one page, and a sentence
        or a button name that was unique when its panel was alone is not unique
        beside another panel. "Run this" matched "Run this op"; "Attach and
        profile a dataset first" matched the EVALUATE panel's version; a cell
        value of 100 appeared twice in one table. Each is fixed by saying
        exactly which thing the test means, and each fix is also the accessible
        thing - a button that two panels answer to is a button a screen reader
        cannot aim. The one type error the suite could not see was the same
        lesson at the compiler's level: `runEda`'s parameter was named
        `request`, shadowing the module's own request helper, and the tests
        never ran that code because the module was mocked.
```

### P7-SHELL-006 contract

```
TASK ID: P7-SHELL-006
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A citation of a previous case is something the analyst can follow. The
      core's cross-case recall already answers "what did I find before about
      revenue?" with the prior case's question and its strongest finding, but
      the shell renders that citation as an inert chip carrying a uuid - the
      one thing recall exists for, going to look at what was concluded last
      time, is not reachable.

CONTEXT: P6-MEMORY-001 made memory a derived, read-only projection over the
         cases and findings on disk, and P3-AI-014 made the chat answer carry
         each claim's source in `grounds` as `kind:name`. A recall answer cites
         `case:<id>` and the prior finding's `finding:<id>`. The shell's Chat
         panel renders those grounds as plain text chips, so a prior case is
         named in the sentence and unreachable below it. Memory has no
         endpoint of its own and needs none: the chat turn is the contract.

INPUTS: a conversation turn's grounds; a click on a cited case.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx, web/src/App.tsx,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/CaseWorkspace.tsx: the Chat panel's grounds chips are replaced by
    a small resolver. A `case:<id>` ground is looked up once per cited case
    (read-only GET, and only for case grounds - the other kinds are not
    case-scoped) and rendered as a button that opens that prior case in the
    workspace, labelled with the case's own question because that is how the
    analyst recognises it. Any other ground keeps rendering as the chip it
    always was. A lookup that fails - a deleted case, an unreachable core - is
    not an error: the chip falls back to the id and the answer stays readable,
    because a citation that cannot be resolved is still a citation.
  - web/src/App.tsx: the workspace gains an `onOpenCase` handler so a prior
    case opens as its own workspace rather than dumping the analyst back on
    the list.
NON-GOALS: a memory endpoint (memory is derived per question and already
           answers through the chat; a GET would be a second copy of a
           projection that cannot drift), editing or pinning memory (it is
           computed, not stored - pinning would be a store to keep consistent),
           resolving a cross-case `finding:<id>` to its statement (it needs a
           case-scoped read the shell does not have, and the answer sentence
           already quotes it), EDA, the evidence graph and case history (their
           own tasks).
CONSTRAINTS: no new endpoint; the lookup is a GET and writes nothing; a click
             only navigates - it creates no case state; `tsc -b` passes; no new
             dependency; the existing workspace tests stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a chat answer citing a previous case shows that case's question as a
      button
- [x] clicking it opens the cited case's workspace
- [x] a cited case that cannot be resolved degrades to a chip, not an error
- [x] grounds of other kinds still render as they did
- [x] a case cited by more than one turn is looked up once
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the cited case as a button that opens,
       the unresolved citation degrading to a chip, and other grounds
       unaffected.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-006 done on pass; ROADMAP item 2 records
              cross-case memory as delivered.
```


```
TASK: P7-SHELL-006 - cross-case memory, actionable in the shell
ID: P7-SHELL-006
PRIORITY: medium
STATUS: DONE
SUMMARY: P6-MEMORY-001 let an answer cite what a previous case found, and the
         shell rendered that citation as an inert chip carrying a uuid. The
         one thing recall exists for - going to read what was concluded last
         time - was a click that did nothing.

The Chat panel now resolves each `case:<id>` ground to the prior case's own
question and renders it as a button that opens that case as its own workspace,
so a citation is something the analyst can follow. The question is the label
because that is how the case is recognised; a uuid would not be.

Three behaviours that had to be right rather than present:

- **One lookup per cited case.** The panel collects the case ids across every
  turn's grounds, fetches each once, and shares the result. A case cited by
  five turns costs one call.
- **A failed lookup is not an error.** A citation outlives the case it names -
  the case may have been deleted while the conversation stayed. A 404 records
  the id as absent and the chip says "a previous case that is no longer
  available", so the answer stays readable and the missing case is not
  refetched on every render. The state update returns the same object when
  nothing was learned, because a fresh object on an all-failed batch would
  re-run the effect forever.
- **Only `case:` grounds change.** Columns, datasets, runs and findings keep
  rendering as the chips they always were.

NON-GOALS held: no memory endpoint (memory is derived per question and already
             answers through the chat; a GET would be a second copy of a
             projection that cannot drift), no pinning or editing memory
             (computed, not stored), no resolution of a cross-case
             `finding:<id>` to its statement (it needs a case-scoped read the
             shell does not have, and the answer sentence already quotes it).
CONSTRAINTS held: no new endpoint and no new dependency; the lookup is a GET
             that writes nothing, and a click only navigates; `tsc -b` passes;
             the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA: all 6 - see the checked boxes above.
TESTS: 4 added to web/src/CaseWorkspace.test.tsx (web suite 50 -> 54) - the
       cited case as a button that opens it, the single lookup across two
       citations, the deleted case degrading to a chip with the answer intact,
       and the other ground kinds unchanged.
VERIFICATION: cd web && npm test - 54 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: two of the four tests failed on the first run for the same reason -
        the fixture described a component in isolation, but the workspace
        loads its own case on mount. A rejection mocked for every id took the
        whole workspace to its error screen before the chat could render, and
        the spy counted the workspace's own lookup alongside the citation's.
        The workspace is the thing under test, and it has its own life in the
        fixture's mocks.
```

