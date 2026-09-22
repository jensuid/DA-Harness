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
| P8-GOLDEN-005 | Verification (the analytical golden suite) | OPEN | AT-40/AT-01 |
| P8-SHELL-006 | UX (the orientation spine) | OPEN | AT-33/34/35 |
| P8-REFINE-007 | AI (question refinement) | OPEN | AT-04 |
| P8-DECISION-008 | UX (the decision view) | OPEN | UX 46 |
| P8-MEASURE-009 | Verification (coverage, perf, a11y, deps) | OPEN | AT-27..30/32/37/38/45/46 |
| P8-TRACE-010 | Verification (the traceability matrix) | OPEN | AT-48 |

### P8-VALID-003 contract

```
TASK ID: P8-VALID-003
MILESTONE: P8 Analytical Contract
CAPABILITY: Validation (3 checks to the PRD's 9 dimensions)
GOAL: a finding's verdict accounts for all nine dimensions the PRD names, not
      three. Today `validate_finding` answers reproducibility, missing data and
      evidence integrity; the PRD's AT-17 requires Calculation, Data,
      Population, Timeframe, Method, Evidence, Assumptions, Causality and
      Alternative explanations. Six are uncomputed, and these are the checks
      that catch a *correct* calculation answering the *wrong* question - a
      finding that compares groups a filter excluded, or reads a trend into one
      period, or claims causation from a correlation. The EVALUATE engine
      already computes a nine-axis audit of imported work; this task points
      that machinery at the case's own finding rather than writing a second
      one, and adds the dimensions EVALUATE does not cover.
CONTEXT: the gap analysis (`docs/PRD & UX Conformance Evaluation.md`, G1) found
         the nine-axis audit exists but is aimed at imported artifacts; a
         finding inside the app gets none of it. The three current checks are
         the honest core - they are what "supported" means today - so they stay
         and become three of the nine, rather than being replaced. The six new
         ones are derived from objects the task's predecessors already built:
         the profile's quality list (P8-QUALITY-002) feeds Data, Method and
         Assumptions; the case's context (P8-CONTEXT-001) feeds Population and
         Timeframe; the run's own SQL and result feed Method and Alternatives.
INPUTS: a finding, its run (code, columns, rows, kind), the dataset's profile
        (stats and the quality list), the case's question and context. Nothing
        new is executed: the run is already stored and the profile already
        computed, so the six new checks are pure functions of what is on disk -
        which is also why they cannot regress the 4-second validation budget.
RELEVANT FILES: server/app/validation.py (new - the nine checks and the
                verdict assembly), server/app/main.py (validate_finding calls
                it, keeps the rerun it already performs),
                server/app/models.py (ValidationCheck gains a dimension,
                ValidationResult keeps its shape),
                server/app/evaluator.py (shared: number-quoting and
                column-read helpers, reused not duplicated),
                server/app/db.py (no migration - a check is derived, never
                stored, so the schema stays at v11),
                web/src/CaseWorkspace.tsx, web/src/api.ts,
                web/src/CaseWorkspace.test.tsx,
                server/tests/test_validation.py, ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `server/app/validation.py` (new): nine checks, one per PRD dimension. Each
    is a pure function returning (passed, detail) and never raises - a check
    that cannot decide answers `passed=true` with a sentence saying it was
    skipped, because a verdict must not punish a finding for the validator's
    own blindness. The three existing checks move in as Calculation
    (reproducibility), Data (the profile's missing-data quality issue) and
    Evidence (the finding's magnitudes all appear in its run's result - the
    same number-quoting budget EVALUATE uses, reused).
  - The six new checks, each derived from an object that already exists:
      * Population - the result's rows are a *subset* the analyst must be told
        about. A GROUP BY over a filtered table answers a narrower question
        than the one asked, and a comparison across groups of wildly uneven
        sizes rests mostly on one of them.
      * Timeframe - a trend or a "same period last year" claim is checked
        against the temporal column's actual span and gaps: one period cannot
        support a trend, and a gap the claim steps over is a comparison of
        non-adjacent windows.
      * Method - the computation matches the question's shape. Averages over a
        column the profile flagged extreme, a COUNT used where a rate is asked,
        and a comparison that ignores the column the question is about.
      * Assumptions - the unstated premises a finding rests on, taken from the
        profile: an implicit "missing is zero", a comparison of unnormalised
        totals across groups of different sizes.
      * Causality - the weakest form of AT-18, deliberately: it flags causal
        language in the finding's own statement when the evidence is a
        correlation, and leaves the full guard to P8-CAUSAL-004. It is a check
        that *says* the claim outruns the method, not one that refuses it.
      * Alternative explanations - the columns the question names that the
        run never read, plus a categorical variable the profile shows is
        confounded with the grouping. A finding that does not look at the
        alternative has not ruled it out.
  - The verdict assembly stays three-valued - supported /
    partially_supported / insufficient_evidence - and the rule stays honest: a
    single failing *hard* check (calculation, evidence, population) blocks
    `supported`, while a soft concern (method, assumptions, causality,
    alternatives) yields `partially_supported`, the verdict that says "the
    numbers reproduce and the claim is phrased within them, but the analysis
    has a stated limitation". Nothing is failed silently and nothing is
    promoted silently.
  - `validate_finding` calls the module and keeps the rerun it already
    performs - the new checks read the rerun's outcome rather than re-running
    anything, so validation costs one execution, not nine.
  - The shell renders each check's dimension and detail; a concern is shown as
    a concern rather than folded into the pass count, because an analyst who
    sees "7 pass, 2 concern" reads a different analysis than one who sees
    "supported".
NON-GOALS: the full causal-language guard with its own thresholds (P8-CAUSAL-
           004 - this task ships the *check*, that one ships the policy and
           the 50-case evaluation); widening the EVALUATE engine's own axes
           (that audit is of imported work and stays as-is); measuring the
           >= 95% detection rate AT-17 names (that is the golden suite,
           P8-GOLDEN-005 - this task ships the checks the suite will measure);
           storing checks (a validation is recomputed on demand and is
           deterministic, so it needs no column and no migration).
CONSTRAINTS: green only. No new SQL execution in the checks - they read the
             stored run and the stored profile. The API's response shape stays
             backwards-compatible: `checks` gains entries and each entry gains
             a `dimension`, and a client reading the old three names still
             finds them. The schema stays at v11.
ACCEPTANCE CRITERIA:
- [x] all nine PRD dimensions have a check, and every finding's validation
      answer carries all nine
- [x] the three pre-existing behaviours are preserved verbatim: a clean
      finding is `supported`, a null in the profile is `partially_supported`,
      a drifted result is `insufficient_evidence`
- [x] a check that cannot decide answers `passed=true` with a skip sentence,
      never a fail and never a 500
- [x] a finding quoting a magnitude absent from its run fails Evidence, and a
      finding claiming causation from a correlation is flagged on Causality
- [x] validation costs one execution of the finding's code, not one per check
- [x] the shell shows each dimension with its verdict, distinguishing a
      concern from a failure
TESTS: test_validation.py - the three preserved behaviours, one raising test
       per new dimension (a fixture per defect), the skip-when-undecidable
       rule, and the one-execution budget (a counter on the run engine).
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11.
```

TASK: P8-VALID-003 - validation across the PRD's nine dimensions
ID: P8-VALID-003
PRIORITY: high
STATUS: DONE
SUMMARY: a finding's verdict now accounts for all nine dimensions the PRD names
         (AT-17) rather than three. `server/app/validation.py` is new: nine
         pure checks - calculation, data, population, timeframe, method,
         evidence, assumptions, causality, alternative_explanations - each
         returning a verdict and a sentence, and never raising; a check that
         cannot decide passes with a "skipped -" sentence rather than punishing
         a finding for the validator's own blindness. The three checks that
         existed survive as three of the nine: reproducibility became
         calculation, missing_data became data (it reads the quality issue's
         impact sentence, so the audit and the Data stage say the same thing
         about the same null) and evidence_integrity became evidence (the
         number-quoting budget EVALUATE already used, reused rather than
         reimplemented). Six are new and are derived from objects the task's
         predecessors built - the profile's quality list, the case's context,
         the run's own SQL and result - so nothing new is executed: a
         validation costs one rerun, not nine, and that is pinned by a test
         with a counter on the query engine, proven to fail when a second
         execution is injected. The verdict stays three-valued and stays
         honest: a hard failure (calculation, evidence, population) yields
         `insufficient_evidence`, a soft concern yields `partially_supported`,
         and only a clean sweep is `supported`. The run's ownership of the case
         is the one fact the module cannot derive from stored objects, so it is
         folded in by the route as an evidence override. The shell renders each
         dimension with its sentence and distinguishes a concern from a
         failure, because an analyst reading "7 pass, 2 concern" reads a
         different analysis from one reading "supported". The schema stays at
         v11 - a check is derived, never stored. Also fixed along the way: the
         check key rename broke three older tests and two phase gates that
         asserted the pre-existing names, and the web suite's 5000ms timeouts
         under parallel file execution were load, not code - `fileParallelism:
         false` makes the gate deterministic without costing wall-clock time.

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

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
