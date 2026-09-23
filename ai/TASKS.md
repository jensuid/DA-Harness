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
| P7-LEARN-001 | LEARN mode (the guided walk, core) | DONE | +9 tests; P2/P3/P4 gates PASS |
| P7-SHELL-010 | UX (LEARN mode in the web shell) | DONE | +6 tests; web build PASS |
| P7-AGENT-001 | Multi-agent workflows (roles, core) | DONE | +13 tests; P2/P3/P4 gates PASS |
| P7-SHELL-011 | UX (the multi-agent surface) | DONE | +5 web tests; web build PASS |
| P7-E2E-001 | Verification (real-server e2e) | DONE | 25 steps over real HTTP; 3 runs green |
| P7-WALK-001 | Verification (manual shell walkthrough) | DONE | walked the shipped shell by hand; 1 bug fixed, 380 tests + e2e green |
| P7-CORS-001 | Reliability (the packaged app's webview) | DONE | CORS for the shell's origins; 4 tests, +4 (384), e2e green |
| P7-CSV-002 | Data Layer (a stray trailing comma) | DONE | 4 tests, +4 (388), e2e green |


## P8 Analytical Contract

Goal: close the PRD's Level 1 breadth gaps and make "done" measurable. DAH
implements its trust model narrowly (validation 3 of 9 dimensions, quality
detection 2 of 7 defect classes, question capture one text field) and measures
nothing; this phase widens the trust machinery first - the PRD's own rule is
that convenience is sacrificed before analytical trust - and then measures it.
See `docs/PRD & UX Conformance Evaluation.md` for the gap analysis this phase
answers.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P8-RELEASE | Distribution (the v0.2.0 release) | DONE | tag v0.2.0; 409 server tests green; artifacts built locally and published as pre-release |
| P8-CONTEXT-001 | Data Layer (the case's context object) | DONE | 21 tests added (409 server, 82 web); schema v10; e2e green |
| P8-QUALITY-002 | Data Layer (quality beyond missingness) | DONE | 26 tests added (435 server, 84 web); schema v11; e2e green |
| P8-VALID-003 | Validation (3 checks to 9 dimensions) | DONE | 16 tests added (451 server, 85 web); e2e green; schema v11 |
| P8-CAUSAL-004 | Validation (the causal-language guard) | DONE | 16 tests added (468 server, 86 web); 50-case corpus measures 100% on AT-18's three thresholds; e2e green; schema v11 |
| P8-GOLDEN-005 | Verification (the analytical golden suite) | DONE | 21 reference calculations match at 100% (AT-40); 21/21 scripted runs complete the loop at 100% over 3 datasets (AT-01); 477 server, 86 web; e2e green |
| P8-SHELL-006 | UX (the orientation spine) | DONE | 13 tests added (477 server, 99 web); AT-33's seven questions answerable from the rendered workspace; e2e green |
| P8-REFINE-007 | AI (question refinement) | DONE | 41 tests added (518 server, 106 web); schema v12; AT-04's four thresholds measured over 50 cases at 100%/100%/0/0; e2e green |
| P8-DECISION-008 | UX (the decision view) | OPEN | UX 46 |
| P8-MEASURE-009 | Verification (coverage, perf, a11y, deps) | OPEN | AT-27..30/32/37/38/45/46 |
| P8-TRACE-010 | Verification (the traceability matrix) | OPEN | AT-48 |

### P8-REFINE-007 contract

```
TASK ID: P8-REFINE-007
MILESTONE: P8 Analytical Contract
CAPABILITY: AI (question refinement)
GOAL: AT-04 requires that an AI refinement preserves the user's original
      question, presents the revision separately, allows accept / reject /
      edit, and never silently overwrites - and measures it over 50 cases:
      >= 95% preserve the original, >= 90% semantically relevant, 0 silent
      overwrites, 0 fabricated data references. Before this task nothing
      proposed a sharpening at all: a vague question ("why are sales down?")
      was carried verbatim into every plan, every generated query and every
      finding, so the analysis inherited its vagueness and the product had no
      surface where the gap was even visible.
CONTEXT: the six tasks before it built the objects a refinement reads and the
         surfaces it sits beside - the context object (P8-CONTEXT-001), the
         profile's own measurements with their quality defects
         (P8-QUALITY-002), and the orientation spine that places the question
         at the top of the case (P8-SHELL-006). The refinement grounds itself
         in the profiler's measured columns and ranges, so it proposes from
         the same data every other assistant reads.
INPUTS: the case's question, the most recently profiled dataset's profile
        (columns, per-column stats, measured min/max and cardinality), and the
        context's purpose / sub-questions / hypotheses when the case stated
        intent.
RELEVANT FILES: server/app/refine.py (new - the deterministic engine, the
                validation gate, the LLM refiner behind the same interface),
                server/app/main.py (the five refine endpoints and the
                duplicate/delete wiring), server/app/db.py (schema v12, the
                refinements table and its migration), server/app/models.py
                (Refinement, RefinementGround, RefinementEdit,
                REFINEMENT_STATUSES), server/app/history.py (the two new event
                kinds), server/app/exporter.py (the round trip),
                verification/refine/{cases.py,verify_refine.py} (new - the
                50-case corpus and the measurement runner),
                server/tests/test_refine.py (new, 41 tests),
                web/src/RefinePanel.tsx (new), web/src/CaseWorkspace.tsx,
                web/src/api.ts, web/src/CaseWorkspace.test.tsx (+7 tests),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - One interface, two engines, as in the planner / assistant / drafter /
    generator: `refine_question` is deterministic and always available;
    `LLMRefiner` calls an OpenAI-compatible endpoint when DAH_LLM_API_KEY is
    set and its output is gated by `validate_refinement` before it is stored.
    A failure of the LLM falls back to the deterministic proposal, which may
    itself be a decline.
  - The deterministic engine appends grounding rather than rewording: the
    refined question is the original with clauses added - the measure, the
    split, the time window, the comparison a direction word leaves unstated -
    each one a column and a range the profile measured. So the original is
    preserved by construction and the refinement is relevant by construction,
    and the suite measures both anyway because a structural guarantee is one
    renamed variable away from a regression. It declines rather than invents:
    no profile, nothing numeric or temporal, no subject terms to preserve, or
    a question already naming its measure, split and window is left alone, and
    the decline is recorded rather than answered as an empty proposal.
  - The gate: the original must be echoed verbatim, the subject terms must
    survive, every cited column must be one the profile has, every quoted
    column name must exist, every figure must be one the profile measured (in
    any spelling the formatter or the analyst might use), and a rationale is
    required - a bare proposal never reaches the analyst.
  - Five endpoints, and only two of them write: POST /refine proposes
    (idempotent while pending and the question unmoved); GET /refine and GET
    /refinements are read-only; accept and edit are the only paths that move
    the case's question, and reject keeps the original and writes nothing but
    the decision. A decided proposal is a 409, not a second decision; an edit
    that restores the original is refused with "use keep original instead".
  - The original is carried on the proposal row, so recoverability is a
    property of the store, not of the client that happened to be looking: it
    survives the accept that replaced it on the case row, travels with the
    export and the duplicate, and is readable from the case's refinement
    history and its timeline (two new event kinds - the proposal, then the
    decision).
  - The measurement: verification/refine/verify_refine.py drives 50 cases over
    6 datasets against a real server over HTTP with the LLM vars scrubbed,
    walking accept / edit / keep / pending at volume, and reports the four
    numbers to verification/refine/REPORT.md. Relevance is measured
    mechanically, not judged: the refined question keeps the original's subject
    terms and names at least one real column. The same four numbers are
    asserted in the test suite.
  - The shell panel (UX 12) shows the transformation explicitly - "Your
    question" above "Refined question", the arrow between them, the engine that
    spoke, the rationale and the grounds behind a disclosure - and accept /
    edit / keep original are the only three buttons. It sits in the orientation
    zone, where the question is described.
NON-GOALS: the decision view (P8-DECISION-008); measurement of coverage /
           perf / a11y (P8-MEASURE-009); refining the context's sub-questions
           and hypotheses rather than the primary question; an LLM judgement of
           relevance - the measurement is mechanical by design, and the
           deterministic engine makes three of the four thresholds structural.
CONSTRAINTS: green only. No new dependency (DEC-001 - the LLM client is
             httpx, already required). Schema moves to v12 with a migration
             that upgrades an existing store in place. Deterministic and
             offline by default: the runner fails unless the deterministic
             engine answered, so a passing suite is itself proof no LLM was
             called. Zero silent overwrites is a Level 0 requirement.
ACCEPTANCE CRITERIA:
- [x] the original question is preserved verbatim beside the proposal, and is
      recoverable after accept, after edit, and after keep-original
- [x] accept / edit / keep-original are the only three paths, and there is no
      fourth that moves the question
- [x] 0 silent overwrites: the case's question moves only through the accept
      and edit endpoints, and the original stays on the row
- [x] 0 fabricated data references: the gate rejects a cited or quoted column
      the profile does not have and a figure it did not measure, before the
      analyst sees the proposal
- [x] AT-04 measured over 50 cases: preserve 100% (>= 95%), relevant 100%
      (>= 90%), 0 silent overwrites, 0 fabrications
- [x] the four numbers are asserted in the test suite, so a regression fails a
      test rather than a report nobody reads
- [x] a deliberately-wrong expectation is caught, proving the measurement can
      fail
- [x] the round trip through export keeps the refinement history, and the
      original with it
- [x] the suite is deterministic and offline, no LLM call
TESTS: test_refine.py (41) - the engine's additions and its four decline
       paths, its determinism, the gate's nine rejection paths and its
       allowance of a measured figure in any spelling, the five endpoints
       (proposes nothing, a read never proposes, idempotency, the decline
       answer, accept / keep / edit and their error contracts: 409 on a second
       decision, 404 on another case's proposal, 400 on an edit that restores
       the original or is empty), the history's two events, the export round
       trip including a decline, the duplicate carrying the history, the delete
       removing the proposals, the schema upgrade recording the migration, and
       the measurement over a real server. CaseWorkspace.test.tsx (+7) - the
       transformation shown with both halves, accept moving the question while
       the original stays visible, keep original writing nothing, the edit
       pre-filled from the proposal, a failed decision reported, the decline
       said rather than shown as an empty panel, and the panel in the
       orientation zone.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (518);
              `server/.venv/bin/python verification/refine/verify_refine.py`
              green (50 cases, four thresholds);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (25/25); `cd web && npm test && npm run build` green (106, build
              ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; schema v11 -> v12.
```

TASK: P8-REFINE-007 - question refinement
ID: P8-REFINE-007
PRIORITY: high
STATUS: DONE
SUMMARY: AT-04's four numbers now exist, and the question is the one place in
         the loop a vague ask was carried verbatim into every artifact after
         it. Two engines sit behind one interface, as in every other assistant:
         a deterministic refiner that appends grounding the profile measured
         (the measure, the split, the window, and the comparison a direction
         word like "down" leaves unstated) and an LLM refiner whose output is
         gated before the analyst sees it - the original echoed verbatim, the
         subject terms surviving, every cited and quoted column real, every
         figure measured, a rationale present. The refined question is the
         original with clauses added, never a replacement, so preserve and
         relevant are structural; the suite measures them anyway. The engine
         declines rather than invents - no profile, nothing numeric or
         temporal, nothing to preserve, or an already-answerable question - and
         the decline is recorded, not answered as an empty proposal.
         Measured over 50 cases and 6 datasets against a real server:
         preserve 100%, relevant 100%, 0 silent overwrites, 0 fabrications.
         The three paths are the only three: accept and edit are the sole
         writes to the case's question, and keep-original writes nothing but
         the no. Recoverability is a property of the store, not the client -
         the original rides on the proposal row, so it survives the accept
         that replaced it, the export round trip and the duplicate, and it is
         readable in the case's timeline as two events. Schema v12, one
         migration, upgrading in place. Two bugs the work surfaced, both fixed
         with their own tests: the new suite's schema test caught that a fresh
         store records no migration rows at all (it is born current, which is
         the truth - the assertion now builds the legacy store the upgrade
         path is actually about), and the web test caught that the api spies
         are module-level, so a "not called" assertion in a top-level describe
         answers for every test before it (its own beforeEach clear, the same
         discipline the CaseWorkspace describe already had).

### P8-SHELL-006 contract

```
TASK ID: P8-SHELL-006
MILESTONE: P8 Analytical Contract
CAPABILITY: UX (the orientation spine)
GOAL: AT-33 asks whether a user can understand "current case, current stage,
      current task, next useful action, analysis status" - and until this task
      the shell answered those with one text sentence and thirteen panels in a
      fixed vertical column. The UX document's own orientation machinery was
      absent: no persistent rail with per-stage status (UX 7), no three-zone
      workspace (UX 8), no case overview (UX 45). This task is the only one in
      the phase that restructures a working surface, and it is deliberately a
      rearrangement: every panel it places already existed and already had a
      contract, so the layout changes and the assertions do not have to.
CONTEXT: the five tasks before it built the objects the spine presents -
         context, quality defects, nine validation dimensions, the causal
         guard, and the golden suite that measures them. Rendering them is now
         possible and is now the gap: the walkthrough (P7-WALK-001) recorded
         that a run's result rows, the plan's contents and the per-column null
         counts were all computed by the core and never shown back, and that
         the chat and generate-code inputs were adjacent near-identical boxes.
INPUTS: the case, the derived progress (stage, completed stages, next action,
        artifact counts), the profiles with their quality issues and per-column
        stats, the findings with their validation statuses, the context's
        purpose, and the plan and run rows the endpoints already served. No new
        endpoint and no new schema: every number on the new surfaces is an
        artifact count or a stored row the core already computed.
RELEVANT FILES: web/src/CaseWorkspace.tsx (the rail, the overview, the plan
                panel, the run's rows, the per-column nulls, the zones),
                web/src/api.ts (getRun and getPlan, over endpoints that
                already existed), web/src/index.css (the three-zone grid, the
                sticky rail, the marks), web/src/App.tsx (the wide main),
                web/src/CaseWorkspace.test.tsx (+13 tests), ai/HANDOFF.md,
                ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The persistent workflow rail (UX 5/7) with the document's four marks:
    `✓` complete, `⚠` requires attention, `●` the current stage, `○` not
    started. The marks are derived the way the core derives the stage itself -
    from `progress.completed` and `progress.stage` - so the rail cannot
    disagree with the core. The one judgement is the warning, and it is
    measured: the data stage's `⚠` is the profiler's own quality issue
    (P8-QUALITY-002), never a guess. The rail is sticky, so the workflow
    indicator stays visible while the work zone scrolls.
  - The three-zone layout (UX 8): left = orientation (the rail, the case
    overview, the LEARN walk, the history, the template action), center = work
    (data, the plan, EDA, runs, findings, EVALUATE, the evidence graph),
    right = intelligence (the context, the analyst agent, the reviewer, the
    chat). The zones are real landmarks - `<section>` with an aria-label each -
    so "where am I / what am I doing / what can help me" is the DOM as well as
    the design. On a narrow screen the grid collapses to one column and the
    rail stops being sticky.
  - The case overview (UX 45, AT-33): objective, question, status as "N / M
    stages complete", key findings, open issues (the profiler's defects plus
    findings still awaiting validation), data sources, and the validation
    counts. The objective reads the context's purpose and falls back to the
    question, so a case that never stated intent is still described.
  - The three render gaps: a run's result rows and the query that produced
    them, reopened on demand over the endpoint that already served them; the
    plan's own contents - objective, sub-questions, hypotheses with their
    rationale and check, steps, data requirements, and the basis it was
    planned from; and each column's measured null count at the Data stage.
  - The two adjacent input boxes are separated by the zones themselves:
    generate-code sits in the work zone, ask-this-case in the intelligence
    zone.
NON-GOALS: the decision view (P8-DECISION-008 - this is orientation, not the
           loop's exit); question refinement (P8-REFINE-007); measurement
           (P8-MEASURE-009 - AT-33's own 8/10 threshold is a usability study,
           not something a unit suite asserts; what this task delivers is the
           surface the study would be run against, and the suite asserts the
           seven questions are answerable from it); any new core capability -
           every endpoint the new surfaces read already existed, and a failure
           in one of them is a finding about an existing contract.
CONSTRAINTS: green only. No new endpoint, no schema change, no new dependency
             (DEC-001). Deterministic: nothing new is executed and no LLM is
             involved. The rearrangement must not weaken an existing panel's
             contract - each panel keeps its own heading and its own asserted
             content, and the tests that pinned them were not edited to fit
             the new layout.
ACCEPTANCE CRITERIA:
- [x] the rail renders the four marks and its current stage agrees with the
      core's derived stage, asserted against the progress the core answers
- [x] a measured data-quality defect marks the data stage `⚠`, and a clean
      stage beside it stays `✓`
- [x] AT-33's seven questions are answerable from the rendered workspace
      alone - case, stage, task, next action and analysis status all assert on
      rendered text
- [x] the three zones are distinguishable landmarks, and the assistants live
      only in the intelligence zone
- [x] a run's result rows and its query render on demand, including the
      truncation notice when the stored result was capped
- [x] the plan's contents render, and a case without a plan is guidance
      rather than an error
- [x] every column's measured null count renders at the Data stage
- [x] the layout is responsive: narrow screens collapse to one column and the
      rail stops being sticky
TESTS: CaseWorkspace.test.tsx - the seven AT-33 questions asserted from the
       rendered workspace, the purpose-as-objective path, the open-issue count
       over quality defects plus pending validation, the three zones as
       landmarks with the assistants on one side and the work on another, the
       four marks over completed/current/attention stages, the per-column null
       counts, the plan's full body, the no-plan-yet degradation, the run's
       rows with its query, the hide path, the truncation notice, and a failed
       read reported rather than hidden.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (477);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (25/25); `cd web && npm test && npm run build` green (99, build
              ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11 and
              the server suite is unchanged - this task touched only the
              shell.
```

TASK: P8-SHELL-006 - the orientation spine
ID: P8-SHELL-006
PRIORITY: high
STATUS: DONE
SUMMARY: the shell now answers "where am I, what am I doing, what can help me"
         as a layout rather than as a sentence. The persistent rail carries the
         UX document's four marks - `✓` complete, `⚠` requires attention, `●`
         the current stage, `○` not started - derived the same way the core
         derives the stage, from `progress.completed` and `progress.stage`, so
         the rail cannot disagree with the core. The one judgement is the
         warning, and it is measured: the data stage's `⚠` is the profiler's
         own quality defect from P8-QUALITY-002, never a guess. Beside it sits
         the case overview (UX 45) - objective, question, status as "N / M
         stages complete", key findings, open issues, data sources, validation
         counts - every one of them an artifact count the core already
         computed, and the objective reading the context's purpose with the
         question as the fallback. The workspace splits into three landmark
         zones (orientation / work / intelligence), which is a rearrangement of
         panels that already existed: no panel was rewritten and the tests that
         pinned them were not edited to fit the new layout - only the one that
         asserted a stage the loop is on was "pending" now reads "current", the
         rail's own sharper vocabulary. The three render gaps the walkthrough
         found are closed over endpoints that already existed: a run's result
         rows and the query that produced them reopen on demand (with the
         truncation notice when the stored result was capped), the plan's own
         contents - sub-questions, hypotheses with their rationale and check,
         steps, data requirements, the basis it was planned from - render
         instead of being written and never read back, and every column's
         measured null count shows at the Data stage. The two adjacent
         near-identical input boxes are separated by the zones themselves. One
         limitation worth naming rather than papering over: the overview's
         labels are unstyled text, because splitting a label into its own
         element breaks the text matching a test and a screen reader both read
         - the sentence stays whole, and the first two rows carry the weight
         instead.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
