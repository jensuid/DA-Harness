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
| P8-MEASURE-009 | Verification (the measurement layer) | DONE | 644 server, 138 web, e2e 28/28; every measured AT holds - AT-38 core 93.9% / analytical 92.9% / evidence 92.4%, AT-37 0/0, AT-28 p95 223ms, AT-29 p95 1.5s, AT-46 at the envelope |
| P8-TRACE-010 | Verification (the traceability matrix) | OPEN | AT-48 |

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

### P8-MEASURE-009 contract

```
TASK ID: P8-MEASURE-009
MILESTONE: P8 Analytical Contract
CAPABILITY: Verification (the measurement layer)
GOAL: the PRD's measurement targets existed as prose and nothing in the
      product computed one of them. AT-38's coverage, AT-27..30's performance
      budgets, AT-32's accessibility, AT-37's dependency security and AT-45/
      46's size envelopes each had a threshold and no number. This task
      attaches a measured number to each - measured against a real core over
      real HTTP, against the OSV database, or by running the suite itself
      under a line counter - and asserts every one of them in the test suite,
      so a regression fails a test rather than a report nobody reads.
CONTEXT: the eight tasks before it built what the layer measures and two
         measured suites to borrow the pattern from - the golden suite
         (AT-40/AT-01) and the refinement runner (AT-04), both of which start
         a real uvicorn on a free port with an isolated data dir and the LLM
         vars scrubbed. The web side (AT-27, AT-30, AT-32) was already
         asserted in the shell's own suite by the a11y and measure test files
         this task found in flight; what was missing was the fold that reads
         them as a measurement and the server-side numbers beside them.
INPUTS: the suite (coverage's driver - its calls are what coverage means),
        the production inventory computed from pyproject.toml and
        package.json plus the installed distributions' own metadata, the OSV
        database over HTTP, a generated 50k-row benchmark dataset, and the
        envelope's own declared limits.
RELEVANT FILES: verification/measure/verify_measure.py (new - the runner,
                the fold, the report), verification/measure/perf.py (new -
                AT-28/29/46 against a real core), verification/measure/
                coverage.py (AT-38, the line counter - in flight, its
                denominator corrected), verification/measure/deps.py (AT-37,
                in flight), server/app/limits.py (AT-45/46, in flight),
                server/app/main.py (GET /envelope, the attach-time refusal),
                server/app/analysis.py (the profiling fix AT-29's measurement
                forced), server/tests/test_measure.py (new, 26),
                server/tests/test_python_guards.py (new, 18),
                server/tests/test_envelope.py and test_llm_adapters.py (in
                flight), web/src/{accessibility,measure}.{ts,test.tsx} (in
                flight), web/vite.config.ts (css: true, so the a11y audit
                reads the shipped stylesheet), ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The runner folds five measurements into one report, one line per
    acceptance test, and exits non-zero when a measured threshold did not
    hold. Each measurement is injected so a test can prove a failure fails
    the gate, and each can be skipped - a skipped measurement is named in the
    report rather than silently making it smaller.
  - AT-27/30/32 are asserted in the web suite, not measured here, and the
    report says so: jsdom is not a browser, and a millisecond there is not a
    millisecond in one. The suite's green is the measurement; the thresholds
    are pinned in its tests. Its summary line is the evidence the report
    quotes.
  - AT-28 measures an opening as the workspace actually opens one - the case,
    its datasets, runs, findings, decision and history as one user-visible
    wait - and takes the p95 over the heaviest case in the envelope, because a
    percentile over an empty case measures nothing.
  - AT-29 profiles a generated 50k-row benchmark dataset (the scale P4 pinned,
    with a date, a split, a measure, a duplicate and a null) and takes the p95.
  - AT-46 builds a case *at* the envelope - ten datasets, a hundred
    multi-dataset runs that each bind all ten so the evidence graph crosses a
    thousand edges, two hundred findings - then reads every surface a reopened
    case offers and requires each to answer, in budget, at that scale.
    Stability is a measured property of the reads at the boundary, and the
    import round trip is among them, so a case that heavy must still restore
    or the boundary is a dead end.
  - AT-45's two halves are both measured: the declaration is the PRD's literal
    numbers, and a dataset past each limit is refused through the same
    function the attach endpoint calls. The row refusal runs at a tightened
    value because the PRD's own five million rows would be the fixture the
    refusal exists to avoid loading; the suite pins the real number.
  - AT-37 scans the computed inventory against OSV and classifies severity
    from the advisory's own CVSS vector. An unreachable database answers
    `unknown` with a reason and the gate is red for it, because "could not
    check" and "nothing to fix" are different statements.
  - Two bugs the measurement surfaced, both fixed with their own tests. (1)
    Profiling a 50k-row dataset took 12.5s against AT-29's 5s, because every
    one of the profile's dozen bounded lookups re-read and re-parsed the CSV.
    One materialisation into a temp table gives every later query an
    in-memory table - same types, same values, same counts - and the same
    profile takes 1.7s. (2) The coverage counter's denominator counted
    function-signature continuation lines, which the compiler attributes to
    the function's code object but the interpreter never reports; the
    denominator was bigger than the numerator could reach, so coverage read
    lower than it was. The exclusion is AST-derived and signature-only, and
    the numerator is intersected with the executable set so a line cannot
    count as covered outside the denominator either.
  - The guards python_exec enforces in the child are now tested in the process
    that measures them: the dunder-hardened handle, the import wall, the
    restricted builtins, the tabulation shapes and the wall-clock alarm. They
    are security-relevant (AT-36) and they ran only in a process the line
    counter cannot instrument, so testing them directly is worth more than
    relying on the child to reach them - and it is what lifted the evidence
    group to its target.
NON-GOALS: the traceability matrix (P8-TRACE-010); re-measuring AT-01, AT-04
           or AT-40, which have their own runners and reports (the report
           points at them); a browser-side p95, which needs benchmark hardware
           and a browser this layer does not have; numeric contrast
           measurement (jsdom does not paint), recorded in the audit itself.
CONSTRAINTS: green only. No new dependency (DEC-001 - the coverage counter is
             sys.monitoring, the scanner is urllib, the p95 is arithmetic).
             Deterministic and offline: the LLM vars are scrubbed from every
             server the runner starts, and a passing run needs no network
             except AT-37's scan, which reports `unknown` rather than a
             fabricated clean when it cannot reach OSV. The profiling fix
             changes no measured result - the existing at-scale correctness
             tests pin the values.
ACCEPTANCE CRITERIA:
- [x] every one of AT-27..30, AT-32, AT-37, AT-38, AT-45 and AT-46 has a
      measured number attached, not a claim
- [x] AT-38 holds at every target: core >= 80%, analytical >= 90%, evidence
      >= 90%
- [x] AT-37 scans the real inventory: 0 critical, 0 high, with the scan's
      state named when it could not run
- [x] AT-28 and AT-29 hold at their p95 targets over the benchmark shapes
- [x] AT-46's boundary case holds - the counts reach the envelope and every
      surface answers in budget, including the export round trip
- [x] AT-45 is both declared with the PRD's numbers and enforced at each limit
- [x] the measurement can fail: a deliberately wrong expectation is caught for
      the percentile, the coverage ratio, the dependency counts, the envelope
      drift, the refusal and the fold
- [x] the numbers are asserted in the suite, so a regression fails a test
- [x] the profiling cost the measurement exposed is fixed and its at-scale
      correctness is unchanged
TESTS: test_measure.py (26) - the percentile's interpolation and its empty
       sample, a timing over budget failing and a timing with no samples
       measuring nothing, the boundary counts being the PRD's envelope, a
       boundary case below it or that does not answer failing, the import's
       201 as its success and a refused round trip named, the declaration
       being the PRD's numbers and a drifted limit caught, both refusals and a
       check that stopped refusing, the dependency classifier counting a
       Critical from its vector and an unreachable database answering unknown
       never clean, the coverage groups' ratios and their named shortfalls, a
       vacuous group failing, the fold green with all measurements holding,
       one failing measurement failing the gate and being named, an offline
       dependency scan red with its reason, a red web suite failing the shell
       targets, and a skipped measurement named rather than silent.
       test_python_guards.py (18) - the dunder-hardened handle and its query
       callable, read-only SQL through the handle, the import wall's refusals
       and its allowlist, the meta_path finder's installation and removal, the
       builtins' dangerous omissions, the tabulation's three shapes and two
       rejections, in-process execution and its three contract violations, the
       resource limits' restoration, and the wall-clock alarm. The suite's own
       process is kept away from the CPU rlimit the child is meant to enforce.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (644);
              `server/.venv/bin/python verification/measure/verify_measure.py`
              green (every measured threshold holds, the report written to
              verification/measure/REPORT.md);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (28/28); `cd web && npm test && npm run build` green (138).
STATE UPDATE: TASKS/CURRENT_STATE gain the task. No schema change.
```

TASK: P8-MEASURE-009 - the measurement layer
ID: P8-MEASURE-009
PRIORITY: high
STATUS: DONE
SUMMARY: the PRD's thresholds were prose; nine of them are numbers now. One
         runner folds five measurements into a report with a verdict per
         acceptance test and exits non-zero when one does not hold. AT-38 is
         the suite run under a sys.monitoring line counter - core 93.9%,
         analytical 92.9%, evidence 92.4%. AT-28 and AT-29 are measured
         against a real core over HTTP: an opening p95 of 223ms against a 2s
         target over the heaviest case in the envelope, and a profiling p95 of
         1.5s against 5s over a generated 50k-row benchmark. AT-46 builds a
         case at the boundary itself - a hundred multi-dataset runs, two
         hundred findings, twelve hundred evidence edges - and requires every
         surface a reopened case offers to answer in budget, the export round
         trip among them. AT-45 is both halves: the declaration is the PRD's
         literal numbers, and a dataset past each limit is refused through the
         same function attach calls. AT-37 scans the computed inventory
         against OSV and classifies from the CVSS vector: 0 critical, 0 high,
         22 of 22 packages. AT-27, AT-30 and AT-32 are asserted in the web
         suite and the report says where the number lives instead of inventing
         one, because jsdom is not a browser.
         Two bugs the measurement surfaced, both fixed with their own tests.
         Profiling a 50k-row dataset took 12.5s against AT-29's 5s, because
         each of the profile's dozen bounded lookups re-parsed the CSV; one
         materialisation gives every later query an in-memory table and the
         same profile takes 1.7s, with no measured result changed. And the
         counter's denominator counted function-signature lines the
         interpreter never reports, so coverage read lower than it was - the
         exclusion is AST-derived, and the numerator is intersected with the
         denominator's notion of line. A third gap the coverage number named:
         the guards python_exec enforces in the child were unreachable by
         measurement, so they are tested in the process that measures them -
         eighteen tests of the dunder wall, the import wall, the builtins and
         the tabulation, which is what lifted the evidence group to its
         target. One hazard the work surfaced along the way: the CPU rlimit is
         process-wide and cumulative, so an in-process test that sets it
         delivers SIGXCPU to the suite itself once it has burned more CPU
         seconds than one run allows; the fixture that fakes the setter is
         documented for the same reason.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
