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
| P8-SHELL-006 | UX (the orientation spine) | OPEN | AT-33/34/35 |
| P8-REFINE-007 | AI (question refinement) | OPEN | AT-04 |
| P8-DECISION-008 | UX (the decision view) | OPEN | UX 46 |
| P8-MEASURE-009 | Verification (coverage, perf, a11y, deps) | OPEN | AT-27..30/32/37/38/45/46 |
| P8-TRACE-010 | Verification (the traceability matrix) | OPEN | AT-48 |

### P8-CAUSAL-004 contract

```
TASK ID: P8-CAUSAL-004
MILESTONE: P8 Analytical Contract
CAPABILITY: Validation (the causal-language guard)
GOAL: an unsupported causal claim is not just commented on, it is *guarded*.
      P8-VALID-003 shipped AT-18's weakest form on purpose: a 14-phrase
      substring match over the finding's statement that raises a soft concern
      and yields `partially_supported`. That names the gap; it never refuses
      anything, and the concern can be read as a footnote rather than a
      verdict. AT-18's actual thresholds are a measurement contract - across
      50 cases, >= 95% of unsupported causal claims are flagged, >= 95%
      distinguish association from causation, and **0** cases convert an
      unsupported association into a validated causal finding. The last clause
      is the one the current check does not hold: a finding that says "spend
      drives signups" over six correlating rows can still be accepted and
      reported as `supported` once the other eight dimensions are clean,
      because causality is a soft concern. This task makes the guard a
      gate on the verdict and ships the 50-case corpus that measures it.
CONTEXT: the gap analysis (G5) said EVALUATE's claim axis flags causal
         language; it does not - that axis tests *specificity* (a direction or
         a magnitude), never causation, so there is no existing machinery to
         reuse. The only causal detector is `check_causality` itself. The
         verdict vocabulary P8-VALID-003 formalised is what this guard acts on,
         and the context object P8-CONTEXT-001 built is what distinguishes a
         claim the case *can* support from one it cannot: a finding that
         asserts causation over an observational comparison is unsupported,
         while one over a documented intervention (a launch date, an A/B test,
         a change recorded in the case's constraints) is a different claim.
         Measuring is the other half of AT-18 - the corpus is the artefact the
         threshold is computed over, and it is deliberately data rather than
         assertions so P8-GOLDEN-005 can fold it into the golden suite.
INPUTS: the finding's statement and interpretation, the case's context
        (purpose, hypotheses, constraints - the last is where an intervention
        is recorded), the run's SQL, and the profile. Nothing is executed and
        nothing is stored: the guard is a pure function of objects already on
        disk, same rule as every other check.
RELEVANT FILES: server/app/causality.py (new - the detector, the hedging and
                intervention logic, the corpus and the measurement),
                server/app/validation.py (check_causality calls it; the
                verdict rule changes from a concern to a gate),
                server/app/main.py (validate_finding passes the context),
                server/tests/test_causality.py (new - the corpus as data, the
                measurement over it, the intervention and hedging paths),
                server/tests/test_validation.py (the verdict's new behaviour),
                web/src/CaseWorkspace.tsx (a guarded finding renders as a
                refusal with the sentence to fix, not a warning),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `server/app/causality.py` (new):
      * A detector wider than the substring list: causal verbs and connectives
        ("drives", "causes", "leads to", "results in", "because of", "due to",
        "so", "therefore", "thus", "hence", "is why", "the reason", "brings
        about", "generates"), matched as word boundaries on normalised text so
        "causes" does not fire inside "because".
      * Hedging: a modal or qualifier immediately before the causal phrase
        ("may drive", "could lead to", "might affect", "appears to influence",
        "seems to cause") is an *associative* claim wearing causal words - the
        hedge is the author stating the limitation themselves, so it does not
        trip the guard. An unhedged phrase does.
      * Negation: "does not drive", "no evidence that X causes Y" asserts the
        absence of causation, which is the guard's own conclusion; it must not
        be flagged as a violation.
      * An intervention basis: the case's context records a change - a launch
        date, an experiment, an A/B test, a policy change in the constraints or
        the hypotheses - and the SQL compares across it (a before/after window
        over a temporal column, or a control comparison). A causal claim over
        an intervention is supported, and the guard says which intervention it
        read rather than refusing everything causal by default. Without a
        recorded intervention, an observational comparison supports
        association only.
      * A 50-case corpus as data - 25 unsupported causal claims, 15
        associative claims that must not be flagged, 10 hedged or negated
        claims - each with its expected verdict, drawn from the phrasings a
        finding actually carries rather than synthetic one-liners. The
        measurement computes the three AT-18 numbers from the corpus.
  - `check_causality` becomes a gate rather than a comment: an unsupported
    causal claim is a hard failure for the verdict, so the status is
    `insufficient_evidence` (the claim outruns the evidence, which is what
    that verdict means) rather than `partially_supported`. The three hard
    dimensions become four. A hedged or associative statement stays clean, and
    an intervention-backed claim passes with its basis named.
  - `validate_finding` passes the case's context to the causality check, so
    the intervention basis is read from the object the analyst already edits
    rather than from a new field.
  - The shell renders a guarded finding as a refusal with the sentence the
    analyst must change, not as a yellow warning beside a green verdict; the
    verdict is the message.
NON-GOALS: the golden suite's other measurements (P8-GOLDEN-005 - this ships
           the causal corpus, that one ships the workflow-completion rate and
           the analytical reference values, and may fold this corpus in);
           detecting confounding or deriving a causal graph (the guard is
           about language and method shape, not about estimating effects);
           causal discovery over the data itself; refusing the write - the
           finding is still stored, it is the *verdict* that refuses.
CONSTRAINTS: green only. The guard is deterministic and offline - no LLM call,
             no new scan, no new schema. The corpus lives in the repository and
             the measurement runs in the suite, so AT-18's threshold is
             asserted on every run rather than quoted.
ACCEPTANCE CRITERIA:
- [x] an unhedged causal claim over an observational comparison yields
      `insufficient_evidence`, not `supported`
- [x] a hedged ("may drive", "could lead to") or negated ("does not cause")
      claim is not flagged, and the corpus's false-positive rate shows it
- [x] a causal claim over an intervention recorded in the case's context is
      supported, and the detail names the intervention it read
- [x] the 50-case corpus is data in the repository, and the measurement over
      it reports >= 95% detection, >= 95% association/causation
      discrimination and 0 conversions, asserted in the suite
- [x] the guard costs no execution and no schema change
- [x] the shell shows a guarded finding as a refusal naming the sentence to
      fix, not a warning beside a pass
TESTS: test_causality.py - the corpus as data with its measurement (the three
       AT-18 numbers computed, not hardcoded), one test per detector path
       (hedging, negation, intervention, word-boundary matching), the verdict's
       new gate behaviour through validate_finding; test_validation.py's
       causality tests updated to the new verdict; web test for the refusal's
       rendering.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11 and
              the hard dimensions become four.
```

TASK: P8-CAUSAL-004 - the causal-language guard
ID: P8-CAUSAL-004
PRIORITY: high
STATUS: DONE
SUMMARY: an unsupported causal claim is guarded, not merely commented on. Until
         this task the causality check raised a *soft concern* - a finding that
         said "spend drives signups" over six correlating rows could still be
         reported `supported` once the other eight dimensions were clean, and
         AT-18's zero-conversion clause was not held. New
         `server/app/causality.py` makes three judgements: an unhedged causal
         verb over an observational comparison is unsupported and gates the
         verdict (`insufficient_evidence`, causality now the fourth hard
         dimension); a hedge ("may drive") or a negation ("does not cause") is
         the author stating the limitation themselves and passes; and an
         intervention the case's context records *and the SQL compares across*
         earns causation, naming the intervention it read. The branch that
         matters most: an intervention the case merely mentions but the query
         never compares across still fails - mentioning is not using. The
         corpus is 50 cases held as data (20 unsupported, 12 associative, 8
         hedged, 10 intervention-backed), and the measurement computes AT-18's
         three numbers over it on every run: 100% detection, 100%
         discrimination, 0 conversions. Two detector bugs the corpus found
         rather than assumed: normalisation strips the slash so "a/b test"
         arrived as "a b test" and the intervention pattern missed it, and the
         negation window had to widen from 3 to 5 words to read "no evidence
         that ... caused". The guard costs no execution and no schema. The
         shell renders a guarded finding as a refusal naming the sentence to
         fix. One limitation recorded in the module rather than papered over: a
         causal word used as a noun ("the causes column") fires, because
         word-boundary matching cannot tell a noun from a verb.


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
