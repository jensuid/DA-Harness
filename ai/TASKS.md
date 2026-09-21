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
| P8-VALID-003 | Validation (3 checks to 9 dimensions) | OPEN | AT-17 |
| P8-CAUSAL-004 | Validation (the causal-language guard) | OPEN | AT-18 |
| P8-GOLDEN-005 | Verification (the analytical golden suite) | OPEN | AT-40/AT-01 |
| P8-SHELL-006 | UX (the orientation spine) | OPEN | AT-33/34/35 |
| P8-REFINE-007 | AI (question refinement) | OPEN | AT-04 |
| P8-DECISION-008 | UX (the decision view) | OPEN | UX 46 |
| P8-MEASURE-009 | Verification (coverage, perf, a11y, deps) | OPEN | AT-27..30/32/37/38/45/46 |
| P8-TRACE-010 | Verification (the traceability matrix) | OPEN | AT-48 |

### P8-CONTEXT-001 contract

```
TASK ID: P8-CONTEXT-001
MILESTONE: P8 Analytical Contract
CAPABILITY: Data Layer (the case's context object)
GOAL: a case carries the analyst's intent, not just a question string. Today a
      case is `question + dataset`; the PRD (AT-03) requires purpose, primary
      question, sub-questions and hypotheses to be captured, edited and
      restored, and the UX architecture (section 13) treats context as a
      first-class analytical object - business objective, time period,
      relevant changes, known constraints - that the planner and the assistant
      reason over. The generated plan already carries sub-questions and
      hypotheses, but they are the engine's, not the analyst's, they are not
      editable, and P7-WALK-001 recorded that they are persisted and never
      rendered. This task is the dependency for P8-REFINE-007 (refinement edits
      this object), P8-DECISION-008 (the decision view closes over it) and the
      case overview in P8-SHELL-006.
CONTEXT: AT-03's threshold is persistence across edit and reopen; AT-10 wants
         the plan to hold an objective, sub-questions, hypotheses and methods;
         UX 13 wants context available to the AI. Nothing in the loop currently
         reads intent - the planner takes `(question, profile)` and the
         assistant's facts carry no context - so this adds the object and wires
         the two readers that already exist.
INPUTS: a case's context: a free-text purpose, a list of sub-questions, a list
        of hypotheses to test, and a list of known constraints. The primary
        question stays on the case row (it is already editable and persisted)
        rather than being duplicated.
RELEVANT FILES: server/app/db.py (migration 10, the contexts table),
                server/app/models.py (CaseContext, ContextUpdate),
                server/app/main.py (GET/PUT /cases/{id}/context, plan wiring),
                server/app/planner.py (reads context, records a context_basis),
                server/app/assistant.py (context in facts, one citation kind),
                server/app/exporter.py (the context section, both directions),
                web/src/ContextPanel.tsx, web/src/CaseWorkspace.tsx,
                web/src/api.ts, web/src/CaseWorkspace.test.tsx,
                server/tests/test_context.py, ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - A `contexts` table, one row per case (case_id PRIMARY KEY), holding purpose
    and three JSON lists: sub_questions, hypotheses, constraints. Migration 10,
    guarded so it is a no-op on a store that already has it and resumable after
    a crashed upgrade - the standard every other migration is held to.
  - `GET /cases/{case_id}/context` answers the context, defaulting to an empty
    one for a case that never set it, so the shell's form always has something
    to render; `PUT /cases/{case_id}/context` replaces it wholesale (idempotent
    form semantics). A 404 for an unknown case; a 400 for a malformed list -
    never a silent drop, the discipline AT-20 applies to our own inputs.
  - The planner accepts an optional context and lets the analyst's intent
    outrank the derivation: their sub-questions and hypotheses come first, the
    purpose stands in for a thin objective. The plan records a `context_basis`
    list naming the fields it actually read, so a reader can tell a plan built
    from stated intent from one built from a profile alone.
  - The assistant's facts carry the context, and one deterministic branch
    answers a question about the case's purpose or its hypotheses citing a
    `context:` ground - the same shape as the column and dataset branches.
  - Export carries the context section and import restores it; an older package
    without one degrades to an empty context rather than erroring.
NON-GOALS: AI question refinement (P8-REFINE-007 - this object is what that
           task edits); rendering the plan's own contents (P8-SHELL-006, which
           is the panel for everything the core computes and the shell does not
           show); quality detection (P8-QUALITY-002).
CONSTRAINTS: green only - nothing committed while red, and the schema version
             climbs to 10 with the migration recorded in the audit trail.
ACCEPTANCE CRITERIA:
- [x] entered purpose, sub-questions, hypotheses and constraints persist across
      a save, close and reopen
- [x] edited text persists and reopening restores the latest version
- [x] a plan generated for a case with context records which fields it read in
      `context_basis`, and the analyst's sub-questions outrank the derived ones
- [x] 3 sub-questions and 2 hypotheses survive an export -> import round trip
- [x] a malformed context (non-list, empty item, overlong text) answers 400 and
      changes nothing
- [x] a store from v9 opens, upgrades to v10 and keeps every row it had
TESTS: test_context.py - persistence and reopen, edit, the 400 paths, the
       migration from v9, the round trip; planner tests for context precedence
       and basis recording; assistant tests for the new citation kind; web
       tests for the panel's edit and remove paths.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task and the raised schema version;
              the store is at v10.
```

TASK: P8-CONTEXT-001 - the case's context object
ID: P8-CONTEXT-001
PRIORITY: high
STATUS: DONE
SUMMARY: a case gains structured, editable intent - purpose, sub-questions,
         hypotheses, known constraints - persisted in a new table (migration
         10), edited through a GET/PUT pair, read by the planner so a plan is
         built from stated intent rather than a question string plus a
         profile, read by the assistant so a question about purpose cites it,
         and carried by export in both directions. The primary question stays
         on the case row where it already lives.

### P8-QUALITY-002 contract

```
TASK ID: P8-QUALITY-002
MILESTONE: P8 Analytical Contract
CAPABILITY: Data Layer (quality beyond missingness)
GOAL: a profile states what the data *cannot* support, before the analyst
      spends a question on it. The profiler finds missing values and duplicate
      rows today (2 of the PRD's 7 defect classes, AT-08); it does not detect
      invalid types, inconsistent categories, date gaps, extreme values or
      insufficient coverage - and these are the defects that make a *correct*
      calculation answer the *wrong* question. Each detected issue must carry
      an impact sentence (AT-09): not "1 null value(s)" but "Revenue contains
      4.8% missing values; revenue comparisons may be understated." Per the UX
      architecture (section 15) this belongs at the Data stage, *before*
      analysis - today it surfaces only at validation, after a finding exists.
CONTEXT: the profile is deterministic (DEC-001) and is already the object the
         planner and the generator read, so quality detection belongs in the
         same pass rather than a second scan. AT-08's thresholds are a >= 95%
         detection rate and <= 5% false positives on the golden suite, which
         does not exist yet (P8-GOLDEN-005) - so this task ships the detectors
         and the tests that pin each one, and the *measurement* against a
         golden corpus is the later task. The context object (P8-CONTEXT-001)
         is already in place; an impact phrased against a stated purpose is
         better than a generic one, but deriving impact from purpose is
         P8-DECISION-008's territory, so impacts are per-defect-class and
         column-specific here, not case-specific.
INPUTS: a profiled dataset's per-column stats (type, null count, distinct
        count, min/max/avg), its row count and its duplicate count - all
        already computed by profile_csv. The detectors add no new scan of the
        file for the classes the existing aggregates already prove; the classes
        that need more (type violations, category inconsistency, date gaps,
        extremes) compute from the same stats plus one targeted query each,
        kept cheap because a profile already costs one scan.
RELEVANT FILES: server/app/analysis.py (the detectors and the quality list),
                server/app/db.py (migration 11, the profile's quality column),
                server/app/models.py (QualityIssue, Profile carries the list),
                server/app/main.py (persist and return the list; the validate
                endpoint's missing-data check reads the derived impact),
                web/src/api.ts, web/src/CaseWorkspace.tsx (the Data-stage
                panel renders the list with its impact sentences),
                web/src/CaseWorkspace.test.tsx,
                server/tests/test_quality.py, ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - Five new defect detectors alongside the two that exist (missing values,
    duplicate rows):
      * invalid_types - a column the profiler typed `other` that reads as
        numeric for most rows but not all, or a date-shaped column holding
        unparsable values. Reported per column with the count and the failing
        examples.
      * inconsistent_categories - a low-cardinality `other` column whose
        distinct values differ only by case or whitespace ("north" vs "North"),
        which silently splits a GROUP BY.
      * date_gaps - a temporal column whose values are not contiguous at the
        granularity the rest of the series implies, so a "same period last
        year" comparison looks at different windows.
      * extreme_values - a numeric column whose max or min is many standard
        deviations out, which skews every average the generator proposes.
      * insufficient_coverage - the dataset is too small for the question's
        implied comparison (a two-row dataset cannot support a trend), or a
        category column is dominated by one value.
    Each returns a structured issue: class, column, severity (high/medium/low),
    an observed sentence and an impact sentence. An issue is only ever raised
    on evidence the profile itself computed - never on a heuristic that could
    fire on clean data, which is how the 5% false-positive budget is held.
  - The profile carries the list: a `quality` key on profile_csv's result and
    on the stored Profile. Persisted in the profiles table as JSON
    (migration 11), so a reopened case shows the same warnings without
    reprofiling.
  - The Data-stage panel renders each issue's observed and impact sentences
    inline under the dataset, with the duplicate and null counts it already
    shows - not behind a tab, because the UX document's rule is that quality
    is visible *before* analysis. A dataset with no issues says so plainly
    rather than rendering nothing.
  - The validation endpoint's missing-data check derives its detail from the
    same impact sentence when the profile has one, so the finding's audit and
    the Data stage cannot drift apart.
NON-GOALS: the 9-dimension validation expansion (P8-VALID-003 - this adds the
           quality *detection*, that consumes it as one of the nine axes); the
           causal-language guard (P8-CAUSAL-004); the golden suite that
           *measures* the 95%/5% budgets (P8-GOLDEN-005 - this ships the
           detectors it will measure); the orientation spine that places these
           in a per-stage rail (P8-SHELL-006); LLM-written impacts (the
           sentences are templated from the profile's own numbers and are
           deterministic, by DEC-001).
CONSTRAINTS: green only. The detectors are pure functions of the profile plus
             at most one bounded query each, deterministic and offline, so a
             profile costs what it costs today plus the targeted queries. The
             schema climbs to 11 and a v10 store opens, upgrades and keeps
             every row.
ACCEPTANCE CRITERIA:
- [x] each of the 7 PRD defect classes has a fixture where the detector raises
      the issue, and the issue carries both an observed and an impact sentence
- [x] a clean dataset (no nulls, no duplicates, consistent categories, no
      extremes) raises no issues - the false-positive guard, asserted
- [x] the quality list persists: profile, close the case, reopen, the list is
      the same without reprofiling
- [x] the Data-stage panel renders the impact sentence for a dataset carrying
      an issue, and states plainly when a dataset is clean
- [x] a store from v10 opens, upgrades to v11 and keeps every row
- [x] validation's missing-data detail uses the impact sentence when present
TESTS: test_quality.py - one raising test per defect class (7), one
       clean-dataset test, persistence across reopen, the v10->v11 migration;
       web tests for the panel's rendering of an issue and of a clean dataset.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task and the raised schema version;
              the store is at v11.
```

TASK: P8-QUALITY-002 - quality detection beyond missingness
ID: P8-QUALITY-002
PRIORITY: high
STATUS: DONE
SUMMARY: a profile now states what the data *cannot* support. Seven defect
         classes (AT-08) each carry an observed fact and an analytical impact
         sentence (AT-09), computed in the profiler's own pass and shown at the
         Data stage, before analysis, rather than only after a finding exists.
         The two classes that existed as bare counts - missing values and
         duplicate rows - gained impacts; five are new: invalid types (a column
         typed `other` that is mostly numeric or temporal but not entirely),
         inconsistent categories (case/whitespace variants that split a GROUP
         BY), date gaps (a hole in an otherwise regular series), extreme values
         (a value dwarfing its neighbour, compared against the next value
         rather than a mean the outlier itself moved) and insufficient coverage
         (too few rows, or a category so dominant a group-by is about one
         group). Every detector raises only on evidence the profile measured,
         never on a guess about what the data should look like, which is what
         holds the 5% false-positive budget before the golden suite that will
         measure it exists. The list persists (schema v11), travels with an
         exported case and survives a duplicate; the validation endpoint's
         missing-data check now reads the same impact sentence the Data stage
         shows, so the audit and the panel cannot drift apart.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
