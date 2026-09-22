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
| P8-REFINE-007 | AI (question refinement) | OPEN | AT-04 |
| P8-DECISION-008 | UX (the decision view) | OPEN | UX 46 |
| P8-MEASURE-009 | Verification (coverage, perf, a11y, deps) | OPEN | AT-27..30/32/37/38/45/46 |
| P8-TRACE-010 | Verification (the traceability matrix) | OPEN | AT-48 |

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

### P8-GOLDEN-005 contract

```
TASK ID: P8-GOLDEN-005
MILESTONE: P8 Analytical Contract
CAPABILITY: Verification (the analytical golden suite)
GOAL: the trust machinery P8 built is unmeasured. AT-40 names ten analytical
      shapes a product like this must compute correctly - aggregation,
      filtering, joins, missingness, duplicates, dates, percentages,
      segmentation, statistical calculations, validation - and requires 100% of
      deterministic reference calculations to match expected results. AT-01
      requires >= 95% of scripted workflow attempts to complete the full loop
      over >= 20 runs and >= 3 datasets. Today neither number exists: the
      detectors and the nine dimensions are pinned by per-feature tests, but a
      test that asserts its own fixture cannot tell you the product computes a
      percentile correctly against data it did not write. This task ships the
      golden datasets as fixtures with hand-computed reference values, and a
      suite that runs the real workflow over them and reports the two numbers.
CONTEXT: the phase's own rule is that convenience is sacrificed before
         analytical trust, and the three tasks before this built the objects a
         measurement would cover - quality detection (P8-QUALITY-002), the nine
         validation dimensions (P8-VALID-003) and the causal guard with its
         50-case corpus (P8-CAUSAL-004). That corpus is the model for this one:
         data plus a measurement, not a wall of assertions. The golden values
         are computed by hand and by an independent path (Python's statistics
         module over the same fixture), never by running the query and
         recording what came back - which would make the suite tautological.
INPUTS: three or more deterministic CSV fixtures, each covering a subset of
        AT-40's ten shapes, each with: the reference SQL or Python the analyst
        would run, and the expected rows computed independently. The workflow
        measurement drives the loop over them - create, question, attach,
        profile, plan, run, interpret, draft, accept, validate, reopen.
RELEVANT FILES: verification/golden/datasets/*.csv (new fixtures),
                verification/golden/reference.py (new - the hand-computed
                expectations and the independent-path recomputation),
                verification/golden/verify_golden.py (new - the runner: the
                reference-calculation check and the workflow-completion
                measurement, writing verification/golden/REPORT.md),
                server/tests/test_golden.py (new - asserts the runner's two
                numbers in the suite, so a regression fails a test rather
                than a report nobody reads),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - Deterministic fixtures, at least three, each exercising several of AT-40's
    shapes: a sales dataset with missingness, duplicates, dates and
    segmentation; a spend/signups dataset for joins and correlation; a tickets
    dataset for percentages and statistical calculations. Small enough to hold
    a reference value in the head, real enough that the shapes are not
    synthetic one-rows.
  - Reference values computed two ways: by hand from the fixture's own numbers,
    and independently in the suite by a second path (Python over the parsed
    CSV, not the engine's own SQL), so the golden value is not the engine
    agreeing with itself. Where the two paths disagree the fixture is wrong,
    not the engine.
  - A runner that, per dataset and shape: attaches the fixture to a real server
    on an isolated store, runs the reference query over HTTP, and compares the
    result to the golden value within a stated tolerance. Floats compare to a
    tolerance; exact types (counts, category labels) compare exactly.
  - The workflow-completion measurement: a scripted run over each dataset
    walking the whole loop AT-01 names, counting a run complete when every
    stage produced its artifact and the case reopens with it. >= 20 scripted
    runs, >= 3 datasets, reported as a rate.
  - Both numbers asserted in the test suite, not only written to a report.
NON-GOALS: the traceability matrix (P8-TRACE-010); coverage/perf/a11y
           measurement (P8-MEASURE-009); new core capability - every shape the
           suite measures is computed by code that already exists, and a
           failure in the suite is a finding about an existing calculation, not
           a reason to build one; LLM-judged quality.
CONSTRAINTS: green only. Deterministic and offline - no LLM calls (the planner
             falls back to deterministic with the LLM vars empty, which the
             e2e already relies on). The suite runs against a real server with
             an isolated data dir, the pattern verify_e2e.py established, so it
             exercises the HTTP surface a user actually touches. Reference
             values are never derived from the engine's own output.
ACCEPTANCE CRITERIA:
- [x] at least 3 fixtures exist, covering all 10 of AT-40's shapes between them
- [x] every reference calculation matches its golden value, 100%, within a
      stated tolerance, and each golden value is independently recomputed
- [x] no golden value is derived from the engine's own output
- [x] >= 20 scripted workflow runs across >= 3 datasets complete, and the
      measured completion rate is >= 95%
- [x] the two numbers are asserted in the test suite, so a regression fails a
      test
- [x] the suite is deterministic and offline, no LLM call
TESTS: test_golden.py - the fixtures' shapes are all covered, the runner's two
       measurements meet their thresholds, and at least one fixture carries a
       deliberately-wrong reference value that the runner catches (proving the
       measurement can fail, per the repo's proven-to-fail discipline).
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11.
```

TASK: P8-GOLDEN-005 - the analytical golden suite
ID: P8-GOLDEN-005
PRIORITY: high
STATUS: DONE
SUMMARY: the trust machinery P8 built is now measured, and the two numbers the
         PRD names exist. Three fixtures (sales, spend, tickets) carry 21
         reference calculations covering all ten of AT-40's shapes, and each
         golden value is computed twice before the engine is ever asked: by
         hand from the fixture's own numbers, and again by an independent
         implementation (plain Python and `statistics` over the parsed CSV -
         never DuckDB). Where the two disagree the fixture is wrong, and the
         suite fails before a single query runs. Only then does the runner ask
         a real server the same question over HTTP and compare: 21/21 match,
         100%, against a threshold of 100%. The same 21 journeys answer
         AT-01's workflow rate, because the query a scripted run makes *is* the
         reference query - create, attach, profile, plan, run, interpret,
         draft, accept, validate, reopen - and 21/21 complete the loop over 3
         datasets, against thresholds of 95%, 20 runs and 3 datasets. A verdict
         of `insufficient_evidence` still counts as a complete run: a finding
         the evidence does not support is a finished analysis, not a failed
         one. Both numbers are asserted in test_golden.py rather than only in a
         report, and the proven-to-fail discipline holds - a deliberately wrong
         expectation (average resolution time claimed as 25.0h against a true
         19.83h) is caught by the audit. The suite is offline by construction:
         the runner fails the `plan` stage unless the planner answers
         `source: "deterministic"`, so a completion rate above zero is itself
         proof no LLM was called. Two real bugs the suite surfaced on the way,
         both fixed with their own tests: grouping by a date column handed a
         raw `datetime.date` to `json.dumps` and answered a 500 for a valid
         query (the profile already described one as an ISO string; the run
         path now agrees), and the runner's own health check raced the stdout
         pump thread for the server's announcement and blocked forever on a
         `readline()` with no timeout.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
