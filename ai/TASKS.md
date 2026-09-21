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
| P7-SHELL-008 | UX (the evidence graph in the web shell) | DONE | +4 tests; web build PASS |
| P7-SHELL-009 | UX (case history in the web shell) | DONE | +3 tests; web build PASS |


Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
### P7-SHELL-009 contract

```
TASK ID: P7-SHELL-009
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A reviewer reopening a case can ask "what did I do here, and when?" and
      read the answer. The timeline exists in the core as a projection over the
      persisted rows; nothing in the shell shows it, so the shape of a case -
      how it grew, and in what order - is only reconstructable by opening every
      panel and comparing timestamps yourself.

CONTEXT: P3-CASE-007 ships `GET /cases/{id}/history` -> `CaseHistory`: one event
         per artifact (case created, dataset attached and profiled, plan
         created, run executed, chart rendered, finding recorded), each carrying
         the artifact's own timestamp, a label and a detail; plus counts. It is
         a read-side projection like the evidence graph, so it cannot drift from
         the rows. A just-created case answers one event, not an error. The only
         failure is 404 for an unknown case - and the workspace loads its own
         case on mount, so that answer means the workspace is already on its
         error screen.

INPUTS: the case's persisted artifacts, read read-only.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `HistoryEvent` and `CaseHistory` matching the core's models,
    and `getCaseHistory(caseId)` for the GET.
  - web/src/CaseWorkspace.tsx: a **History panel** at the end of the workspace,
    after the evidence panel, because it is the other read-only review surface -
    where the evidence graph says what backs each claim, this says what
    happened in the case at all. It loads with the workspace, read-only. Each
    event is one line in chronological order: the timestamp, the kind as a
    phrase a reader does not have to decode ("dataset attached", not
    "dataset_attached"), the artifact's own label, and its detail - the same
    fields the core returns, shown rather than transformed. The counts are one
    summary sentence so a reader can see the case's shape at a glance.
  - A 404 degrades to muted guidance, not an alert: the workspace loads its own
    case on mount, so a 404 here means the case is already unreachable and the
    header already says so - a second alert would report the same failure twice.
    Any other failure is the sentence in an alert, the way every other panel
    reports one.
NON-GOALS: filtering or collapsing events (a case has as many events as it has
           artifacts, and the whole timeline is the point), editing history (it
           is a projection; the only way to change it is to change the case
           through the endpoints that own it), per-artifact timestamps of their
           own for validation (the finding keeps its status, not when it was
           set, so the status rides along as the event's detail - the core's
           decision, kept rather than re-derived).
CONSTRAINTS: the panel calls only the read-only GET and writes nothing; `tsc -b`
             passes; no new dependency; the existing workspace tests stay
             green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case with artifacts shows every event in chronological order
- [x] each event's kind is readable, and its label and detail are shown
- [x] a young case's single event is shown, not reported as emptiness
- [x] the counts appear as one summary sentence
- [x] an unknown case degrades to guidance rather than a duplicate alert
- [x] the panel writes nothing and reloads with the workspace
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the events of a worked case in order
       with their kinds, labels and details; the single event of a just-created
       case; the counts summary; and the 404 rendered as guidance.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-009 done on pass; ROADMAP item 2 records the
              web-shell gap as closed.

```

TASK: P7-SHELL-009 - case history, as a review surface
ID: P7-SHELL-009
PRIORITY: medium
STATUS: DONE
SUMMARY: P3-CASE-007 shipped `GET /cases/{id}/history` - one event per
         artifact, chronological, each carrying its own timestamp, a label and
         a detail - and nothing in the shell showed it, so the shape of a case,
         how it grew and in what order, was reconstructible only by opening
         every panel and comparing timestamps yourself.

A **Case history panel** now sits at the end of the workspace, after the
evidence panel, because the two are the read-only review surfaces: the graph
says what backs each claim, the timeline says what happened in the case at all.
It loads with the workspace and writes nothing. Each event is one line in the
order the core sends them: the timestamp, the kind as a phrase a reader does
not have to decode ("dataset attached", not "dataset_attached"), the artifact's
own label, and its detail beneath - the same fields the core returns, shown
rather than transformed. The counts are one summary sentence naming only the
kinds the case actually has, so a young case is not described by a row of
zeroes it would have to explain away.

Two behaviours that had to be right rather than present:

- **A 404 is guidance, not a second alert.** The only failure the endpoint
  answers is an unknown case, and the workspace loads its own case on mount, so
  that answer already reaches the user at the top of the page. The panel says
  the sentence once, muted, rather than raising an alert for a failure the
  header already reported. Every other failure is the sentence in an alert, the
  way every other panel reports one.
- **A young case is its beginning, not an empty list.** A just-created case
  answers one event, and the panel renders it - the timeline of a case that has
  only started is the start of a story, not a placeholder.

NON-GOALS held: no filtering or collapsing (a case has as many events as it has
             artifacts, and the whole timeline is the point), no editing (it is
             a projection; the only way to change it is to change the case
             through the endpoints that own the artifacts), no invented
             per-artifact timestamps for validation (the finding keeps its
             status, not when it was set, so the status rides along as the
             event's detail - the core's decision, kept).
CONSTRAINTS held: the panel calls only the read-only GET and writes nothing; no
             new endpoint and no new dependency; `tsc -b` passes; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 3 added to web/src/CaseWorkspace.test.tsx (web suite 64 -> 67) - a
       worked case's events in order with their kinds, labels, details and the
       counts summary, a young case's single event shown rather than reported
       as emptiness, and a 404 rendered as guidance with no alert.
VERIFICATION: cd web && npm test - 67 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: the timeline's first event is the case's creation, whose label is the
        case's own question - so the question now appears twice on the page,
        once as its title and once as the timeline's first line, and five
        existing assertions that meant the title broke on the duplication. Each
        now asks for the heading by role, which is the accessible thing anyway:
        an assertion that says which of two identical texts it means is the
        same judgement a screen reader user needs. The second collision was
        subtler and cost more guessing than it should have: a label inside a
        <strong> is invisible to getByText, because the matcher reads an
        element's own text nodes, not its descendants' - so a line whose label
        is emphasised cannot be matched by the phrase it renders. The event
        line is plain text now, and the lesson is to keep a line's asserted
        content in its own text nodes.


### P7-SHELL-008 contract

```
TASK ID: P7-SHELL-008
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A reviewer can ask of a case "what backs each claim, and does every one
      of them reach the data?" and get an answer. The graph exists in the core
      as a projection over persisted rows; nothing in the shell shows it, so
      the case's own evidence is only inspectable one finding at a time, and a
      claim with no source is invisible.

CONTEXT: P3-EVIDENCE-006 shipped `GET /cases/{id}/evidence-graph`, answering
         nodes (datasets, runs, charts, plans, findings), edges that say how
         one was derived from another (anchored_on, queries, rendered_from,
         planned_from), one trace per finding walking it out to the datasets it
         stands on, the findings that reach no source as `orphan_findings`, and
         counts. It is derived, never stored, so it cannot drift from the rows.
         The endpoint answers 400 with a sentence when the case has no
         artifacts to graph - that is the normal state of a young case rather
         than a failure, and the shell has to say so as guidance rather than as
         an error.

INPUTS: the case's persisted artifacts, read read-only.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx, web/src/index.css,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `EvidenceNode`, `EvidenceEdge`, `ClaimTrace` and
    `EvidenceGraph` matching the core's models, and `getEvidenceGraph(caseId)`
    for the GET.
  - web/src/CaseWorkspace.tsx: an **Evidence panel** after the findings panel,
    because the evidence graph is what reviews them. It loads with the
    workspace, read-only. Two parts:
      - **Claims and what they rest on** - one block per trace: the finding's
        statement with its validation badge, and its path rendered as nodes
        joined by arrows (finding -> run -> dataset), so a reviewer reads the
        chain without leaving the case. A trace that does not reach a source
        says so plainly and is marked, because a claim with no source is what
        the graph exists to surface.
      - **How each artifact was derived** - every edge as a sentence
        ("chart 'Revenue by region' is rendered from the sql run"), so the
        graph's structure is visible as text rather than as a diagram only a
        library could draw. No node is left out: a node with no edges still
        appears under its kind.
  - The 400 of an artifact-free case is shown as muted guidance, not as an
    alert: the core's own sentence names what would build a graph, and a young
    case is not a failed review. Any other failure is the sentence in an alert,
    the way every other panel reports one.
NON-GOALS: a drawn graph (an SVG layout is a library's job and DEC-001 keeps
           the bundle dependency-free; the edges-as-sentences list carries the
           same information a reader can act on), editing the graph (it is a
           projection; there is nothing to edit, only artifacts to add or
           remove through the endpoints that own them), the single-finding
           chain (`GET .../findings/{id}/evidence`, its own surface one day),
           case history (its own task).
CONSTRAINTS: the panel calls only the read-only GET and writes nothing; `tsc
             -b` passes; no new dependency; the existing workspace tests stay
             green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case with artifacts shows its claims and the path each one rests on
- [x] a finding's validation status is shown with its statement
- [x] a claim that reaches no source is marked and does not pass silently
- [x] every edge is visible as a sentence, and a node without one appears
- [x] an artifact-free case shows the core's guidance rather than an error
- [x] the panel writes nothing and reloads with the workspace
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - a case with a trace and its path, an
       orphan flagged, the edge list, and the empty-case guidance.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-008 done on pass; ROADMAP item 2 records the
              evidence graph as delivered.
```



```
TASK: P7-SHELL-008 - the evidence graph, as a review surface
ID: P7-SHELL-008
PRIORITY: medium
STATUS: DONE
SUMMARY: P3-EVIDENCE-006 could answer "what backs each claim in this case, and
         does every one of them reach the data?" - and nothing in the shell
         showed it, so a case's own evidence was only inspectable one finding at
         a time and a claim with no source was invisible.

An **Evidence panel** now sits after the findings panel, because the graph is
what reviews them. It loads read-only with the workspace. Two parts, both
textual - an SVG layout is a library's job and DEC-001 keeps the bundle
dependency-free, and a sentence carries the same information a reader can act
on:

- **Claims and what they rest on** - one block per trace: the finding's
  statement with its validation status, and its path rendered as a chain of
  chips (finding -> run -> dataset), the same shape the chat uses for a citation
  so a reviewer reads it the same way.
- **How each artifact was derived** - every edge as a sentence
  ("chart 'Revenue by region' is rendered from the sql run"), so the graph's
  structure is visible without a diagram. A node with no edge is still listed
  under its kind - an attached dataset nothing has queried yet, a plan nothing
  has run - because leaving it out would make the graph say the case has less
  than it does.

Three behaviours that had to be right rather than present:

- **A claim with no source is marked, not smoothed over.** A finding whose run
  is gone is the thing the graph exists to surface; it renders with "a claim
  with no source: its run is gone" so a reviewer cannot read it as supported.
- **A broken edge says so.** Such a finding still has its edge to a run the case
  no longer has, so an edge whose target is missing renders as "an artifact no
  longer in the case" rather than as a uuid.
- **The 400 of an artifact-free case is guidance, not an error.** The endpoint
  answers 400 with a sentence naming what would build a graph, and a young case
  is not a failed review - so it is a muted paragraph, and only other failures
  become an alert.

NON-GOALS held: no drawn graph (DEC-001 keeps the bundle dependency-free; the
             edge sentences carry the same information), no editing the graph
             (it is a projection; there is nothing to edit, only artifacts to
             add through the endpoints that own them), no single-finding chain
             surface (`GET .../findings/{id}/evidence`, its own task one day).
CONSTRAINTS held: the panel calls only the read-only GET and writes nothing; no
             new endpoint and no new dependency; `tsc -b` passes; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 4 added to web/src/CaseWorkspace.test.tsx (web suite 60 -> 64) - a claim
       with its path, an orphan flagged, the derivations and the unused
       artifacts, and the empty case's guidance rendered without an alert.
VERIFICATION: cd web && npm test - 64 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: the patch script failed three times before a line of it landed, and the
        cause was the script, not the file - an earlier replacement had moved
        the anchor a later assertion looked for, so the whole script died at
        an assert and nothing was written. Writing the file after each
        replacement instead of once at the end turned a silent all-or-nothing
        failure into a resumable one, and the same idempotency check
        ("already applied") is what made the retry safe. The same discipline
        that keeps a task atomic applies to the tool that edits it.
```
