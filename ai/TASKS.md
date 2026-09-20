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

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
### P7-EVAL-001 contract
```
TASK ID: P7-EVAL-001
MILESTONE: P7 Product Modes
CAPABILITY: EVALUATE mode
GOAL: Audit existing analytical work. A user submits work someone already did -
      a SQL query and the claim it was used to support - and DAH answers the
      nine questions the specification names, each against the data rather than
      against the claim's own confidence.

CONTEXT: the master specification defines three product modes. ANALYZE is the
         one that exists and it is finished through P6. EVALUATE is the second:
         "audit existing analytical work", over inputs that can include SQL,
         Python, a notebook, a dashboard, a spreadsheet, a report or
         AI-generated analysis, judged on Question / Data / Quality / Method /
         Calculation / Evidence / Claim / Visualization / Limitations.
         Most of the machinery already exists and is validated - read-only
         execution with a row cap, deep profiling, rerun determinism, the
         evidence graph, the honesty budgets that bound what a claim may quote.
         What does not exist is the frame: today every one of those primitives
         serves the user's *own* analysis. EVALUATE turns them on work that
         came from elsewhere, and that turn is the whole task.

INPUTS: a case with at least one attached, profiled dataset; a submitted
        artifact - its code (SQL or Python), the kind, and the claim the code
        was offered as evidence for.
RELEVANT FILES: server/app/evaluator.py (NEW), server/app/main.py,
                server/app/models.py, server/app/db.py,
                server/tests/test_evaluator.py (NEW)
REQUIRED CHANGE:
  - server/app/evaluator.py: a pure module, the way evidence.py and workflow.py
    are pure. `evaluate` takes the artifact, the dataset's profile and the
    run it produced, and returns one finding per spec axis. Nothing is computed
    that the data does not contain; nothing is asserted the run does not show.
  - the nine axes, each a named check with a verdict and a sentence:
    * Question - the claim is stated and is answerable from this dataset.
    * Data - every column the code reads exists in the profile, and the
      profile's own caveats (nulls, duplicates) are surfaced as limitations.
    * Quality - the profile's missing-value and duplicate-row counts reach the
      verdict, so a claim over a column that is 40% null is a *finding*, not a
      pass.
    * Method - the code is read-only (the existing gate), bounded by the row
      cap, and deterministic: an artifact whose result depends on unordered
      output is flagged, because a rerun could disagree without anything
      changing.
    * Calculation - the code runs, and it reproduces: the artifact is executed
      twice and the two results must agree, the same standard a finding's
      validation holds (P4-VALID-005).
    * Evidence - the claim's magnitudes all appear in the result the code
      actually produced, checked against the same honesty budget a draft is
      checked against (P3-AI-012): a claim quoting a number the run does not
      contain is the single most common way an analysis lies.
    * Claim - the claim is specific enough to be wrong: it names a magnitude or
      a direction, not only a topic. "Revenue declined in north" is auditable;
      "revenue was analysed" is not, and the verdict says so.
    * Visualization - whether the artifact's result is chartable, and if a
      chart exists, whether its axes match the result's own columns. Not a
      requirement that one exist - an honest "no chart, and none needed" is a
      valid verdict.
    * Limitations - the accumulated caveats, stated as sentences rather than
      as an error code.
  - POST /cases/{id}/datasets/{id}/evaluate accepts the artifact and the claim,
    executes the code through the *existing* run endpoints' engine (never a
    second code path), and returns the evaluation. It writes the artifact as a
    run and the evaluation beside it, so an audit is itself inspectable and
    reproducible - the standard every other artifact in DAH is held to.
  - GET .../evaluations lists them, newest first, the same as runs and plans.
  - the endpoint refuses an artifact whose code is not read-only, exactly as
    the run endpoints do, and refuses a claim that is empty; both are 400s with
    a message, never a 500.
NON-GOALS: evaluating a notebook, a dashboard, a spreadsheet or a report as a
           whole file (this task takes the code and the claim, which is the
           common core of all of them; whole-file ingestion is a later task),
           an LLM judgement of the claim (deterministic by default, as every
           other assistant slice is - the LLM may later rephrase, never
           decide), a score or a grade (a verdict per axis with a sentence is
           the honest output; a number would imply a precision the axes do not
           have), evaluating an artifact against a dataset it never ran
           against, fixing the artifact.
CONSTRAINTS: the code executes under the same read-only gate, row cap and
             (for Python) hard sandbox as any other run - EVALUATE earns no
             privilege, and untrusted code is the *premise* of the mode; the
             honesty budgets from P3-AI-011..014 are reused unchanged; an
             evaluation never mutates the case, the dataset or any run, only
             appends its own row; nothing the analyst submitted is logged (the
             log holds method/path/status/duration, as P5-OBSERVE-002 pins);
             deterministic by default with `source` recorded; no new runtime
             dependency; the suite, the P2/P3/P4 gates, the web and desktop
             suites stay green.
ACCEPTANCE CRITERIA:
- [x] a clean artifact over a clean dataset passes all nine axes
- [x] an artifact reading a column the dataset lacks is flagged on Data, not
      silently passed
- [x] a claim quoting a magnitude absent from the result is flagged on
      Evidence with the value it should have been
- [x] a claim too vague to be wrong ("revenue was analysed") is flagged on
      Claim
- [x] a non-deterministic artifact (unordered output treated as a ranking) is
      flagged on Method
- [x] an artifact over a mostly-null column reports the null share as a
      Quality limitation, not a pass
- [x] an artifact that does not reproduce is flagged on Calculation
- [x] a non-read-only artifact is refused with 400 before anything executes
- [x] an evaluation is persisted, listed and inspectable; it never mutates
      another artifact
- [x] every verdict carries a sentence a reader can act on, not only a code
- [x] the full server suite, the P2/P3/P4 gates, the web suite and the desktop
      tests stay green
TESTS: server/tests/test_evaluator.py - the clean baseline; each axis's failure
       case (unknown column, invented magnitude, vague claim, unordered
       ranking, null-heavy column, non-reproducing artifact, non-read-only
      refusal); the persistence and listing round trip; the no-mutation
       invariant; 404s including a cross-case dataset.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS;
              cd desktop/src-tauri && cargo test PASS.
STATE UPDATE: mark P7-EVAL-001 done on pass; ROADMAP item 1 flips to DONE.
```


```
TASK: P7-EVAL-001 - audit existing analytical work against nine axes
ID: P7-EVAL-001
PRIORITY: high
STATUS: DONE
SUMMARY: EVALUATE mode - the spec's second product mode. Until now every
         primitive DAH has served the analyst's *own* work: read-only
         execution, deep profiling, rerun validation, the evidence graph, the
         honesty budgets. This task turns those primitives on work that came
         from elsewhere. A user submits an artifact - its code (SQL or Python)
         and the claim that code was offered to support - and DAH answers the
         nine questions the specification names, each against the data rather
         than against the claim's own confidence.

Three pieces:

- **`server/app/evaluator.py` (new)** - a pure module, the way evidence.py and
  workflow.py are pure. `evaluate()` returns one finding per axis - question,
  data, quality, method, calculation, evidence, claim, visualization,
  limitations - each a verdict (pass / concern / fail, deliberately not a
  score: a single number would imply a precision nine heterogenous axes do not
  have) and a sentence a reader can act on. The Evidence axis reuses the
  drafter's honesty budget unchanged (`_allowed_numbers`, `_numbers_in`), so a
  claim quoting a magnitude the run does not contain is caught by the same
  standard a draft is judged by.
- **`POST /cases/{id}/datasets/{id}/evaluate`** - executes the artifact through
  the *existing* run engine, never a second code path, so the read-only gate,
  the row cap and the hard sandbox are the ones every other run answers to.
  EVALUATE earns no privilege, and untrusted code is the premise of the mode.
  The artifact is stored as a run and the evaluation beside it, so an audit is
  itself inspectable and reproducible. `GET .../evaluations` lists them newest
  first.
- **`server/app/db.py`** - the `evaluations` table, migration 8, so an audit is
  a first-class artifact rather than a transient response.

Four judgement calls the contract left open, each written into the code:

- **A non-read-only artifact is a 400 before anything executes**, exactly as the
  run endpoints refuse one. A mutation is not an artifact to audit - it is a
  request the store must never honour, and it is refused before the engine is
  asked to do anything. But an artifact that *is* read-only and still fails at
  run time is a **Calculation finding, not a 400**: the work is not the user's
  to fix, it came from elsewhere, and "this does not run" is the answer an
  auditor exists to give.
- **An unknown column is a Data fail, never a silent pass.** The first version
  of the check intersected the code's identifiers with the profile's columns,
  which drops every name the dataset lacks - the axis passed on exactly the
  case it exists to catch. The fix reuses the generator's own notion of a
  column read (`_sql_identifiers`, `_python_read_columns`, `_SQL_KEYWORDS`),
  so an invented name is *reported* rather than filtered away.
- **A chart is not required.** The contract's baseline is that a clean artifact
  passes all nine axes, and "no chart, and none needed" is a valid verdict,
  because a table's numbers are checkable without one. What *is* a fail is a
  chart whose axes are not the result's own columns - a check the previous
  shape (a bare `has_chart` boolean) could not make, because a boolean cannot
  be wrong.
- **A single-row result is deterministic without an ORDER BY**, because one row
  has no row order to disagree about; the Method axis flags only an unordered
  *multi-row* result, whose order a rerun may present differently.

NON-GOALS held: no whole-file ingestion of notebooks, dashboards or
             spreadsheets (this task takes the code and the claim, which is the
             common core of all of them), no LLM judgement of the claim
             (deterministic by default, as every assistant slice is; an LLM may
             later rephrase a sentence, never decide one), no score or grade,
             no evaluating an artifact against a dataset it never ran against,
             no fixing the artifact.
CONSTRAINTS held: the code executes under the same read-only gate, row cap and
             hard sandbox as any other run; the honesty budgets from
             P3-AI-011..014 are reused unchanged; an evaluation appends its own
             row and mutates nothing else (pinned by a test that counts runs,
             findings and evaluations around one); nothing the analyst
             submitted is logged (the log holds method/path/status/duration, as
             P5-OBSERVE-002 pins); deterministic, `source` recorded; no new
             runtime dependency; the suite, the gates and the web and desktop
             suites stayed green.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 22 in server/tests/test_evaluator.py - the clean baseline across all nine
       axes, each axis's failure case (unknown column, invented magnitude, vague
       claim, unordered ranking, null-heavy column, non-reproducing artifact,
       artifact that does not run), the read-only refusal with nothing written,
       the empty-code / empty-claim / bad-kind 400s, both the SQL and the Python
       artifact paths, persistence and newest-first listing, the no-mutation
       invariant, 404s including a cross-case dataset, the unprofiled dataset,
       and the pure module's chart branches - which the endpoint cannot reach,
       because a chart cannot exist for the run the request itself creates.
VERIFICATION: server suite 358 passed (was 336, +22); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 358); web 21 passed; desktop 22
              Rust tests. All green locally; CI will run it on push.
LESSON: three of the eleven criteria were satisfied by code that had not been
        written yet, and the missing half was the interesting half. The Data
        axis "passed" an unknown column because it asked "which of the code's
        names are in the profile?" instead of "which are NOT?"; the
        Visualization axis could never pass at all, because it treated the
        absence of a chart as a defect the contract explicitly calls a valid
        verdict; and the read-only refusal had been softened into a Calculation
        finding, which is kinder but is not what the contract asks. Each was
        found the same way - reading the acceptance criteria as assertions and
        asking what code would make each one true. The general shape: a check
        that filters its inputs before testing them is testing the survivors,
        and a check that cannot fail cannot pass either.
```

### P6-UPDATE-005 contract

```
TASK ID: P6-UPDATE-005
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Distribution
GOAL: A new release tag reaches an installed app: the app says a newer build
      exists and puts the download in front of the user, and when it cannot
      know, it says so instead of claiming the app is current.

CONTEXT: the release pipeline now publishes a versioned build per tag, but an
         installed app has no way to learn that. Two facts constrain what is
         buildable now, and both are already decisions rather than gaps: the
         repository is PRIVATE (an unauthenticated release-feed request answers
         404, verified), and the app is UNSIGNED (DEC-006), so an update payload
         cannot be signature-verified and a self-replacing updater cannot be
         tested end to end. So the task delivers the half that is verifiable -
         the check - and leaves the install half as a documented slot, exactly
         as DEC-004/006 left signing.

INPUTS: the version this build was published at; a release feed.
RELEVANT FILES: server/app/updates.py (NEW), server/app/main.py,
                server/app/models.py, server/tests/test_updates.py (NEW),
                desktop/src-tauri/src/updates.rs (NEW),
                desktop/src-tauri/src/main.rs, .github/workflows/release.yml
REQUIRED CHANGE:
  - the core learns its own version, one source of truth: the version the
    release workflow already stamps from server/pyproject.toml. Resolved by
    importlib.metadata when installed or bundled, falling back to reading the
    pyproject beside the source in a dev checkout, and finally to "unknown" -
    never to a guessed number.
  - server/app/updates.py: pure functions. `parse_version` and
    `is_update_available` (semver-style tuple comparison, no dependency), and
    `latest_release` over an injected HTTP client, so the parsing and the
    comparison are tested without a network and the transport is a seam.
  - GET /updates/latest: read-only, no body accepted, nothing the caller
    supplies is written anywhere. It answers one of three truths:
    `current` (the feed named a version and it is not newer),
    `available` (it named a newer one, with its tag, its page URL and the
    published notes), or `unknown` - and `unknown` carries a reason: the feed
    was unreachable, the repository is private, the rate limit was hit, or the
    body was not the shape expected. An unknown answer is never reported as
    current, because "could not check" and "is up to date" are different
    statements and only one of them is true.
  - the shell bridges it the way it bridges /logs: a DAH > Check for
    Updates... menu item asks the core, opens the release page in the user's
    browser when one exists, and otherwise shows the reason it could not tell.
    It degrades to a sentence rather than an error at every step, and never
    panics on a body it does not recognise.
  - release.yml publishes the version, the page URL and the notes the check
    reads, so the feed and the pipeline cannot drift apart.
NON-GOALS: a self-replacing updater (unsigned builds cannot verify a payload,
           DEC-006; tauri-plugin-updater slots in when signing does, and the
           check it would consume is what this task builds), background or
           scheduled checks (a single user does not need a poller burning
           battery and network; the menu item is the trigger), auto-download
           or auto-install, a channel/staging mechanism (one release stream),
           update notifications in the web bundle.
CONSTRAINTS: the check is read-only and makes no authenticated request - no
             token is shipped and none ever can be, so a private repository is
             answered with `unknown` and a reason, never with a silent guess;
             the network call is bounded by a timeout so a hung feed cannot
             freeze a menu; nothing the analyst typed is logged; no new runtime
             dependency (httpx is already in the tree; the browser opens
             through `open`, as the reveal-logs menu already does, so the shell
             gains no crate); the existing test suites stay green and hermetic.
ACCEPTANCE CRITERIA:
- [x] the core resolves its own version from the pyproject, and the endpoint
      reports it, never a guess
- [x] a newer published version is reported as available with its tag, its
      page URL and its notes
- [x] an equal or older published version is reported as current
- [x] an unreachable or private feed is reported as unknown WITH a reason, and
      never as current
- [x] a rate-limited feed and a malformed body are each reported as unknown
      with their own reason
- [x] the comparison is a pure function, tested without a network
- [x] the endpoint is read-only: it accepts no body and writes nothing
- [x] the menu item opens the release page when an update exists and shows a
      sentence when it cannot tell
- [x] the shell degrades on every failure path, including a body it does not
      recognise, without panicking
- [x] release.yml publishes the fields the check reads
- [x] the full server suite, the P2/P3/P4 gates, the web suite and the desktop
      tests stay green
TESTS: server/tests/test_updates.py - version resolution, the pure comparison
       across older/equal/newer and malformed inputs, the three feed outcomes
       and every failure reason, each driven through an injected client so no
       test touches a network; desktop/src-tauri unit tests for the parse and
       the degradation table.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS;
              cd desktop/src-tauri && cargo test PASS.
STATE UPDATE: mark P6-UPDATE-005 done on pass; ROADMAP item 5 flips to DONE and
              P6 closes.
```

```
TASK: P6-UPDATE-005 - a new release tag reaches an installed app
ID: P6-UPDATE-005
PRIORITY: high
STATUS: DONE
SUMMARY: The release pipeline publishes a build per tag, but an installed app
         had no way to learn that. This task delivers the half of an update
         flow that is verifiable today: the app says a newer build exists and
         puts its download page in front of the user - and when it cannot know,
         it says so, instead of claiming the app is current.

Two facts decided the scope, and both are recorded decisions rather than gaps:
the repository is **private**, so an unauthenticated release-feed request
answers 404 (verified, not assumed), and the app is **unsigned** (DEC-006), so
an update payload cannot be signature-verified and a self-replacing updater
cannot be tested end to end. A full `tauri-plugin-updater` integration would
have been unverifiable code claiming a capability it cannot prove. The check
ships; the install slots in when signing does, exactly as DEC-004/006 left
signing itself.

Three pieces:

- **`server/app/updates.py` (new)** - the honest core of it. `parse_version` and
  `is_update_available` are pure functions (semver-style tuple comparison, no
  dependency, tolerant of a leading `v` and a pre-release suffix); `latest_release`
  runs over an *injected* HTTP client, so the parsing is tested without a
  network and the transport is a seam. `check_for_update` answers one of three
  truths - `current`, `available`, or `unknown` - and `unknown` always carries a
  reason: the feed was unreachable, the repository may be private, the rate
  limit was hit, or the body was not the shape expected.
- **`GET /updates/latest`** - read-only, GET-only, unauthenticated, accepts no
  body and writes nothing. The core resolves its own version from the pyproject
  (importlib metadata when installed or bundled, the file beside the source in a
  dev checkout, then "unknown" - never a guessed number).
- **`desktop/src-tauri/src/updates.rs` (new)** - the bridge, shaped exactly like
  the reveal-logs menu it sits beside: it asks the core, opens the release page
  in the browser through `open` when one exists, and otherwise shows the
  sentence. **DAH > Check for Updates...** is the menu item. Every failure path,
  including a body it does not recognise, degrades to a sentence rather than
  panicking.

The property the tests actually pin is not "does it find an update" but "does
it tell the truth". An unreachable feed, a 404, a 403, a 503, a non-JSON body, a
body without a tag and a transport timeout are each `unknown` with their own
reason - never a silent `current`, because "could not check" and "is up to
date" are different statements and only one of them is true. Verified live
against the real private repository: the answer is `unknown`, "the release feed
is not reachable; the repository may be private" - the honest one, and it
answers properly the day the repository goes public with no code change.

NON-GOALS held: no self-replacing updater (unsigned builds cannot verify a
             payload, DEC-006; the plugin slots in when signing does, and the
             check it would consume is what this task builds), no background or
             scheduled checks (a single user does not need a poller), no
             auto-download or auto-install, no channel mechanism, no web-bundle
             notification surface.
CONSTRAINTS held: read-only and unauthenticated - no token is shipped and none
             ever can be, so a private repository is a *state to report*; the
             network call is bounded by a timeout so a hung feed cannot freeze
             a menu; nothing the analyst typed is logged; no new runtime
             dependency (httpx was already in the tree, and the browser opens
             through `open` as the reveal-logs menu already does, so the shell
             gains no crate); the existing suites stayed green and hermetic -
             every feed outcome in the tests is driven through the injected
             client, so no test touches a network.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 21 in server/tests/test_updates.py - version resolution, the pure
       comparison across older/equal/newer and malformed inputs, and every feed
       outcome and failure reason through the injected client; 7 in
       desktop/src-tauri/src/updates.rs - the parse table and the degradation
       cases, including a body that is not JSON and a newer build with no page.
VERIFICATION: server suite 336 passed (was 315, +21); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 336); web 21 passed; desktop 22
              Rust tests (19 unit + 3 e2e, was 12). The live check against the
              real private repository was run by hand and answered `unknown`
              with the private-repository reason, not a false "current".
LESSON: two of the first tests failed for the same reason, and it was the
        tests' fault both times. The endpoint holds its own *imported* reference
        to `httpx_client` (`from app.updates import httpx_client`), so
        monkeypatching `updates.httpx_client` patched a name the endpoint had
        already copied - the call escaped the fake and hit the real network.
        The seam is the module the call site reads, not the module the symbol
        came from. The same misreading produced the second failure: the test
        passed `json=` to a GET, asserting a property ("no body accepted") that
        a GET cannot even express. The real property is that the route is
        GET-only, so a POST is refused with 405 before any handler runs - and
        that is what the test now asserts. A test that fails because it
        misstates the contract is still a test failure worth having, but the
        contract is verified against the route, not against an assumption about
        it.

```
