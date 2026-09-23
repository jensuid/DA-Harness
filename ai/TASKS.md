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
| P8-DECISION-008 | UX (the decision view) | DONE | 30 tests added (548 server, 116 web); schema v13; 28/28 e2e; the verdict persists, the export carries it |
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

### P8-DECISION-008 contract

```
TASK ID: P8-DECISION-008
MILESTONE: P8 Analytical Contract
CAPABILITY: UX (the decision view)
GOAL: UX 46 and AT-43: the loop's exit. A validated finding used to be the end
      of the road - the verdict was computed, shown and discarded, and nothing
      in the product closed over what the loop had established. The PRD's own
      flow (UX 48) ends at Decision Support -> Export. This task makes the
      decision a first-class object the case carries: the validated findings,
      each with its residual uncertainty - the checks that did not pass, never
      a score - the claims still open, and the implications the analyst writes.
      DAH informs decisions; it does not make them.
CONTEXT: the seven tasks before it built what the view reads - the nine
         validation dimensions and the causal guard that produce the verdicts
         (P8-VALID-003, P8-CAUSAL-004), the golden suite that measured them
         (P8-GOLDEN-005), the orientation spine that says where the case stands
         (P8-SHELL-006), and the refinement that sharpened the question the
         view opens on (P8-REFINE-007).
INPUTS: the case's question, the context's purpose, every finding with the
        verdict validation computed (status, nine checks, validated_at) and its
        own caveat, the workflow's own loop-closed flag, and the analyst's
        implications. Nothing is executed and nothing is derived that is not
        already on disk.
RELEVANT FILES: server/app/decision.py (new - the view's assembly and the
                implications' rules), server/app/main.py (the three endpoints,
                the persisted verdict, the duplicate and the delete),
                server/app/db.py (schema v13, two tables, one migration),
                server/app/models.py (DecisionView, DecisionWrite,
                DecisionFinding, DecisionOpenItem, DecisionCheck),
                server/app/history.py (two new event kinds),
                server/app/exporter.py (the two new package sections and their
                import), server/tests/test_decision.py (new, 30 tests),
                server/tests/test_case_history.py (the timeline's two new
                kinds), verification/e2e/verify_e2e.py (+3 steps, a PUT helper),
                web/src/DecisionPanel.tsx (new), web/src/CaseWorkspace.tsx,
                web/src/api.ts, web/src/CaseWorkspace.test.tsx (+10 tests),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The verdict stops being ephemeral. validate_finding computed nine checks
    and kept only the status; now the whole verdict (status, checks,
    validated_at) is persisted, so a decision is read without re-running a
    single query and a reopened case still shows what validation found. A new
    GET /cases/{id}/findings/{fid}/validation answers it read-only, and a
    never-validated finding is a 404 naming the endpoint that creates one
    rather than an empty list.
  - The view: GET /cases/{id}/decision is read-only, deterministic and executes
    nothing. It answers the question, the purpose the analyst stated, the key
    findings (supported / partially_supported) each carrying its caveat and the
    checks that did not pass as its uncertainty, the open items (a finding
    awaiting validation, or one the verdict refused, naming the hard dimension
    that failed), counts, and the analyst's implications. The loop's closure is
    the core's to declare - the view reads workflow.case_progress rather than
    restating it, so the decision cannot disagree with the rail.
  - The only write is the implications: PUT /cases/{id}/decision with a list of
    strings. It validates what it accepts - a list, each entry non-empty after
    trimming, at most twelve, at most two thousand characters - and answers 400
    naming the first entry that breaks a rule. An empty list clears them, which
    is a decision the analyst is allowed to make.
  - A case's decision travels: the export gains the verdicts and the decision,
    and the import round trip restores both, so AT-43's "validation states
    preserved" is a property of the package rather than a claim about it. The
    duplicate carries both; the delete removes both.
  - The timeline gains two events - the validation itself, now that it has a
    timestamp of its own (AT-44 names validation among its minimum events), and
    the decision the analyst wrote.
  - The shell (UX 46): the panel is last in the work zone, where the loop
    exits. Question, key findings with their caveats, the uncertainty, the
    claims still open, the implications the analyst edits, and the case's
    export - which had no surface in the shell at all, and whose natural home
    is the decision it sits beside.
NON-GOALS: the agent proposing implications - DAH informs decisions and does
           not make them, so no agent step touches the decision view;
           measurement of the view (P8-MEASURE-009); a formatted report output
           (PDF / markdown, UX 47's future list); scoring, ranking or
           recommending anything; the traceability matrix (P8-TRACE-010).
CONSTRAINTS: green only. No new dependency (DEC-001). Schema v12 -> v13, one
             in-place migration creating two tables. Read-only by default: the
             GET executes nothing, and the PUT is the only write. Deterministic
             and offline. UX 44's rule holds throughout - no confidence score
             appears anywhere in the view.
ACCEPTANCE CRITERIA:
- [x] every validated finding appears in the decision view with its residual
      uncertainty, and a check that did not pass is named, never scored
- [x] the view is read-only: reading it executes nothing and writes nothing,
      and the second read answers the first's verdict
- [x] the verdict persists, so a case reopened shows what validation found
      without re-validating
- [x] the implications are the only write, and a bad entry is a 400 naming it
- [x] export carries the verdicts and the decision, and the round trip
      restores both with fresh ids
- [x] the duplicate carries them; the delete removes them
- [x] the timeline records the validation and the decision
- [x] the shell renders the view, and the case's export is reachable from it
- [x] the view's loop-closed is the core's own value, so it cannot disagree
      with the workflow rail
TESTS: test_decision.py (30) - the empty case as guidance rather than an empty
       decision, a supported finding with no uncertainty, a partially
       supported finding carrying its failing checks verbatim from the verdict,
       a refused finding as an open item naming the hard dimension that failed,
       the awaiting-validation reason, the purpose, oldest-first ordering,
       loop-closed agreeing with /progress, the verdict readable without
       re-validating, the 404 for a never-validated finding and for another
       case's, reading changes nothing across repeated reads, re-validation
       keeping one row, the delete leaving no trace, the duplicate carrying
       both, the implications' round trip, trimming, the three 400 shapes and
       the empty-list clear, the unit rules on a non-list, the two new timeline
       events and their counts, the export carrying both sections, the round
       trip restoring both, an older package degrading rather than failing, the
       AT-43 measurement over two findings, and the v12 -> v13 upgrade plus the
       fresh store. CaseWorkspace.test.tsx (+10) - the panel in the work zone,
       the question and purpose, a validated finding with its caveat and no
       score anywhere, the failing checks as the uncertainty, the open claims
       and their reasons, the guidance before a closed loop, a failed read
       reported, the implications written and confirmed saved, a failed save
       reported with the server's sentence, and the export downloaded as a
       named file.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (548);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (28/28); `server/.venv/bin/python
              verification/golden/verify_golden.py` green (21/21 reference and
              workflow); `server/.venv/bin/python verification/refine/verify_refine.py`
              green (AT-04's four thresholds); `cd web && npm test && npm run
              build` green (116, build ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; schema v12 -> v13.
```

TASK: P8-DECISION-008 - the decision view
ID: P8-DECISION-008
PRIORITY: high
STATUS: DONE
SUMMARY: the loop has an exit. A validated finding used to be the last thing
         the product did with itself: the verdict was computed, shown and
         discarded, only the status surviving on the finding, and nothing closed
         over what the loop had established. Now the verdict is kept - all nine
         checks, not only the status - and the decision view reads it without
         re-running a single query. The view answers the question, the findings
         validation stood behind with their caveats and the checks that did not
         pass (a sentence each, never a score, per UX 44), the claims still open
         with the reason each is unresolved, and the implications the analyst
         writes - the view's only write, and the one thing in it a human
         authors, because a tool that drafts the action to take is a tool
         making the decision. The loop's closure is the core's own value, read
         from workflow.case_progress rather than restated, so the decision
         cannot say the loop is open while the rail says it is closed. The
         decision travels: the export carries the verdicts and the implications
         and the round trip restores both with fresh ids, the duplicate carries
         them, the delete removes them, and the timeline records the validation
         and the decision as their own events. The shell gained the panel and,
         with it, the case's export - which existed as an endpoint and had no
         surface in the product at all. Two bugs the work surfaced, both fixed
         with their own tests: the timeline asserted its event list exactly, so
         the two new kinds needed the assertions that name them, and the test
         file's decision describe sits outside the CaseWorkspace describe, so
         the plan and run read rejections it inherited by accident of the
         previous test's persistence are now its own beforeEach - a fragility
         the refinement describe beside it still has and this task did not
         touch.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
