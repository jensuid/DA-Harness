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

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
### P7-SHELL-005 contract

```
TASK ID: P7-SHELL-005
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A finished investigation becomes a reusable template and a template
      becomes a new case, both from the shell. Today the four template
      endpoints answer only through the API, so the shape of a case that was
      worked out once is never offered to the next one.

CONTEXT: P6-TEMPLATE-003 made a template carry the analytical shape of the case
         it came from - its plan and which engine produced it, the proposals it
         offered, and its findings' statements with the verdicts validation gave
         them - and made a case started from a template offer that shape as
         proposals a human accepts. Four endpoints serve it and all are tested
         in the core; none has a surface. Templates are not case children and
         outlive the case they came from, so they do not belong inside a case
         workspace - they belong on the front door beside the case list.

INPUTS: the case list screen (where templates are listed and started); a case
        workspace (where one is promoted); an optional name for a promotion.
RELEVANT FILES: web/src/api.ts, web/src/Templates.tsx (NEW), web/src/CaseList.tsx,
                web/src/CaseWorkspace.tsx, web/src/index.css,
                web/src/Templates.test.tsx (NEW), web/src/CaseWorkspace.test.tsx,
                web/src/api.test.ts
REQUIRED CHANGE:
  - web/src/api.ts: `Template`, `TemplateShape`, `TemplateProposal` and
    `TemplateFindingSummary` types matching the core's models, and four
    functions - `promoteCaseToTemplate(caseId, name?)` for the POST, a GET
    `listTemplates`, `createCaseFromTemplate(templateId, {question?, dataset?})`
    for the POST that seeds a case, and `deleteTemplate(templateId)` for the
    DELETE. A DELETE answers 204 and an empty body, so the shared request
    helper returns nothing for an empty body rather than trying to parse one -
    without that, every DELETE the shell makes fails at the parse after
    succeeding at the write.
  - web/src/Templates.tsx (NEW): a section for the front door. Each template
    row shows its name, the question and the dataset label it seeds, and a
    shape summary - how many proposals it carries and how many findings, with
    each finding's validation verdict - so a template says what kind of
    investigation it is, not only what it asked. A template with no shape says
    so instead of showing zeroes that imply an empty case. Each row has two
    actions: **Start a case from this**, which posts to the from-template
    endpoint and opens the seeded case, and **Retire**, which removes the
    template. A template carries no data of its own - no datasets, runs or
    findings travel with it - and the core's contract is that cases already
    created from a template are unaffected when it goes, degrading to normal
    derivation, so retiring needs no second confirmation the way deleting a
    case does.
  - web/src/CaseList.tsx: the templates section renders below the case list on
    the same screen, because templates are the other thing a user comes to the
    front door for.
  - web/src/CaseWorkspace.tsx: a **Save as a template** panel. The name is
    optional - the core defaults it to the case's question, because the common
    gesture needs no second prompt - and a promotion reports success as a
    sentence and leaves the workspace usable on failure.
  - Every write posts to its endpoint and nothing else; the list reloads after
    a write rather than mutating its own copy; a failure degrades to the
    core's own sentence.
NON-GOALS: editing a template (a template is a snapshot; changing one would
           make it disagree with the case it was captured from - the honest
           edit is to fix the case and promote again), a template gallery or
           sharing (single user, local-first), promoting from the case list
           (promotion belongs to the workspace that shows what would be
           captured), cross-case memory, EDA, the evidence graph and case
           history (read-only views, their own tasks).
CONSTRAINTS: each action calls its endpoint and nothing else; `tsc -b` passes;
             no new dependency; the existing list, workspace and client tests
             stay green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case can be saved as a template from its workspace, with an optional name
- [x] a promotion without a name is named for the case's question
- [x] the template list shows a template's name, question, dataset and shape
- [x] a shapeless template is shown as such, not as an empty case
- [x] a case started from a template is created and opened
- [x] a template can be retired, and cases created from it are unaffected
- [x] a failed write shows the core's message and leaves the screen usable
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/Templates.test.tsx - the list and its shape summary, the
       shapeless template, starting a case, retiring, and a failure rendered as
       a sentence; web/src/CaseWorkspace.test.tsx - the promotion, named and
       unnamed; web/src/api.test.ts - an empty 204 body parses to nothing.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-005 done on pass; ROADMAP item 2 records templates
              as delivered.
```


```
TASK: P7-SHELL-005 - templates in the web shell
ID: P7-SHELL-005
PRIORITY: medium
STATUS: DONE
SUMMARY: The four template endpoints answered only through the API, so the
         shape of an investigation worked out once was never offered to the
         next one from the shell. A finished case becomes a template from its
         workspace, and a template becomes a new case from the front door.

Two surfaces:

- **web/src/Templates.tsx (NEW)** sits on the case-list screen, because
  templates are not case children and outlive the case they came from - they
  are the other thing a user comes to the front door for. Each row shows the
  name, the question and the dataset label it seeds, and a **shape summary**:
  how many proposals it carries and how many findings, with each finding's
  validation verdict counted. A name alone cannot say whether a template is a
  finished method or a question-only skeleton, so a shapeless template *says
  so* - "A question-only skeleton - no shape was captured" - rather than
  showing zeroes that would imply an empty investigation. Each row has
  **Start a case from this**, which posts to the from-template endpoint and
  opens the seeded case, and **Retire**. Retiring is one click, deliberately:
  a template carries no data of its own, and the core's contract is that cases
  created from it are unaffected when it goes - `_template_of` answers None and
  the case degrades to normal derivation - so unlike deleting a case, nothing
  is lost.
- **CaseWorkspace** gains a **Save as a template** panel. The name is optional
  - the core defaults it to the case's question, because the common gesture
  needs no second prompt - and a promotion reports the saved name as a
  sentence, so a user learns where to find it.

One real bug surfaced while wiring the DELETE, and it was not in this task's
endpoints: the shared `request` helper parsed every successful body as JSON,
and the core answers 204 with an empty body for all three of the shell's
DELETEs (a case, a dataset, now a template). The write had already landed when
the response arrived, so the client threw "Unexpected end of JSON input" and
the row reported a success as "The action failed". The helper now returns
nothing for an empty body. The case-delete that P7-SHELL-004 shipped was
broken in exactly this way - its tests mocked the client, so the path never
ran for real - and it is fixed by the same two lines.

NON-GOALS held: no editing a template (a template is a snapshot; changing one
             would make it disagree with the case it was captured from, and
             the honest edit is to fix the case and promote again), no gallery
             or sharing (single user, local-first), no promoting from the list
             (promotion belongs to the workspace that shows what would be
             captured), and the remaining shell surfaces (cross-case memory,
             EDA, the evidence graph, case history) stay unowned.
CONSTRAINTS held: every write posts to its endpoint and nothing else, and the
             template list reloads after a write rather than mutating its own
             copy; `tsc -b` passes; no new dependency; the desktop bundle
             builds from the same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 11 added (web suite 39 -> 50) - 7 in the new web/src/Templates.test.tsx
       (the shape summary, the shapeless template, the empty list, starting a
       case, retiring, a failed start rendered as a sentence, a failed load),
       3 in web/src/CaseWorkspace.test.tsx (the unnamed promotion naming it for
       the question, a chosen name, a failed promotion leaving the panel
       usable), and 1 in web/src/api.test.ts (an empty 204 body parses to
       nothing).
VERIFICATION: cd web && npm test - 50 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: three of the eleven tests failed on the first run for reasons that
        were the fixtures' fault, and each taught the same thing - a test
        suite is only as honest as the DOM it asserts against. The template
        row renders the question and the dataset label as one sentence, so an
        exact `getByText('sales.csv')` could not find it; the list screen now
        loads templates beside the cases, so a test that mocked only the case
        calls saw a second alert from an unresolved spy; and the WHATWG
        Response constructor refuses a body with a 204, so the client's own
        fixture had to build one without. Each was the test describing a DOM
        the component did not produce, and the component was right.
```

### P7-SHELL-004 contract

```
TASK ID: P7-SHELL-004
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A case can be renamed, duplicated and deleted from the shell. These are
      the everyday operations on the front door, and today all three answer
      only through the API.

CONTEXT: the three endpoints have existed since P2-CASE-010 and are tested in
         the core, but the case list renders a row per case whose only
         affordance is opening it. A user who mistyped a question cannot fix
         it; a finished investigation cannot be copied as a starting point for
         a variant; and a case that has served its purpose cannot be removed,
         so the list only ever grows. This is the cheapest slice of the
         web-shell gap, and it is the one a user meets first.

INPUTS: the case list; for a rename, the edited question and the dataset label.
RELEVANT FILES: web/src/api.ts, web/src/CaseList.tsx, web/src/CaseList.test.tsx,
                web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `updateCase(caseId, {question?, dataset?})` for the PATCH,
    `duplicateCase(caseId)` for the POST, `deleteCase(caseId)` for the DELETE.
    The core's `Case` also carries `template_id`, which the shell's type now
    admits as optional so a templated case round-trips without the type
    disagreeing with the payload.
  - web/src/CaseList.tsx: each row keeps opening the case as its primary
    affordance and gains three actions - Rename, Duplicate, Delete. Rename is
    an inline edit of the question and the dataset label with Save and Cancel,
    so a correction never needs a second screen. Duplicate creates the copy and
    the list reloads with it. Delete is irreversible - the core removes the
    case row, every child and the case's on-disk directory - so it asks twice:
    a first click arms the row and a second, labelled with what will be lost,
    is the one that removes it. Nothing is deleted by a single click, and the
    armed state is per row, so confirming one case never endangers another.
  - Every action reports a failure as the core's own sentence and leaves the
    list usable, the way the list already does for a failed load.
NON-GOALS: bulk operations (a single-user tool with a handful of cases does not
           need selection machinery), undo for a delete (the core's contract is
           that deletion is final and its data dir goes with it; an undo would
           be a second store to keep consistent), renaming a dataset label that
           renames the file on disk (the label is a case property, not a
           filename), templates (their own task), case history and the evidence
           graph (read-only views, their own task).
CONSTRAINTS: each action calls its endpoint and nothing else; the list reloads
             after a write rather than mutating its own copy, so what it shows
             is what the core has; `tsc -b` passes; no new dependency; the
             existing list tests and the workspace stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case can be renamed inline, and the list shows the corrected question
- [x] a duplicate appears in the list after the action
- [x] a delete needs two clicks, and the second names what it removes
- [x] an armed delete is per row: confirming one case deletes no other
- [x] a failed action shows the core's message and leaves the list usable
- [x] opening a case is still the row's primary affordance
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseList.test.tsx - the rename round trip, the duplicate
       appearing, the two-click delete, the per-row isolation, and a failure
       rendered as a sentence.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS. The server
              suite and the three gates are untouched by this change and stay
              green.
STATE UPDATE: mark P7-SHELL-004 done on pass; ROADMAP item 2 records case
              management as delivered.
```


```
TASK: P7-SHELL-004 - rename, duplicate and delete a case from the shell
ID: P7-SHELL-004
PRIORITY: medium
STATUS: DONE
SUMMARY: The three everyday operations on the front door answered only through
         the API. The case list rendered a row per case whose only affordance
         was opening it: a mistyped question could not be fixed, a finished
         investigation could not be copied as the start of a variant, and a
         case that had served its purpose could not be removed, so the list
         only ever grew. All three are buttons now.

Each row keeps opening the case as its primary affordance and gains Rename,
Duplicate and Delete:

- **Rename** is inline - the question and the dataset label become inputs on
  the row itself, with Save and Cancel, so a correction never needs a second
  screen and a cancelled edit restores what was there.
- **Duplicate** creates the copy and the list reloads with it.
- **Delete** asks twice, because the core's deletion is final and takes the
  case's on-disk directory with it. A first click arms the row; the second is
  labelled with the case's own question ("Delete "Why did revenue decline?" for
  good"), because the question is the thing a user would be sorry to lose. The
  armed state is per row - confirming one case never endangers another, and an
  armed row offers "Keep it" as an escape.

Every action reports a failure as the core's own sentence and leaves the list
usable, the way a failed load already did.

NON-GOALS held: no bulk operations (a single-user tool with a handful of cases
             does not need selection machinery), no undo for a delete (the
             core's contract is that deletion is final; an undo would be a
             second store to keep consistent), no file rename behind a dataset
             label (the label is a case property), no templates, history or
             evidence-graph surfaces (their own tasks).
CONSTRAINTS held: each action calls its endpoint and nothing else, and the list
             reloads after a write rather than mutating its own copy, so what
             it shows is what the core has; `tsc -b` passes; no new dependency;
             the existing list and workspace tests stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 5 added to web/src/CaseList.test.tsx (web suite 34 -> 39) - the rename
       round trip, the duplicate appearing, the two-click delete whose second
       click names the case, the per-row isolation of an armed delete, and a
       failed delete rendered as a sentence with the case still present.
VERIFICATION: cd web && npm test - 39 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched and stay green.
LESSON: the two-click delete and the aria-labels solved each other. The first
        draft named the buttons "Rename"/"Duplicate"/"Delete" and the tests
        could not address one case among two; per-row aria-labels naming the
        question fixed the tests AND are the accessible thing to do - an action
        button that does not say which case it acts on is ambiguous to a screen
        reader for exactly the reason it was ambiguous to a test. The same
        spy-accumulation bug CaseWorkspace hit recurred here, and for the same
        reason: this file's module-level mocks had no reset between tests.
```
