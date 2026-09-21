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


Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.

### P7-CSV-002 contract

```
TASK: P7-CSV-002 - a CSV with a stray trailing comma no longer collapses to one column
ID: P7-CSV-002
MILESTONE: P7 Product Modes
CAPABILITY: Data Layer (reliability)
GOAL: an analyst's CSV is accepted as it arrives. A row carrying more fields
      than the header - a stray trailing comma, as a spreadsheet export or a
      hand-edit produces - derails read_csv_auto's delimiter guess, and the
      whole file then reads as one column holding each raw line. The profile
      answers `columns: ['order_id,quarter,region,revenue']` and describes
      nothing, and the SQL the analyst then writes from those columns fails on
      the same file it was derived from. The file is not corrupt; one cell is.
CONTEXT: found while seeding the shipped app with worked cases - the first
         draft of a fixture carried `106,2024q3,west,,` and the profile
         collapsed to a single column. Bisected exactly: a trailing empty that
         matches the header's width (`106,2024q3,west,`) is a honest null and
         always worked; the collapse needs a row *wider* than the header, and
         only when more rows follow it. Neither the profiler nor the run path
         was at fault alone: both build the same reader, so a profile that
         recovered while its runs collapsed would describe columns the SQL
         cannot see.
INPUTS: a CSV whose header claims four fields and whose third row carries five
        (the last two empty), followed by further rows; read_csv_auto alone
        answers one column for it, `ignore_errors=true` answers four with
        every row present and the stray field gone, and `null_padding=true`
        answers five - a synthetic column invented for the stray field.
RELEVANT FILES: server/app/analysis.py (the recovery, and its four call sites),
                server/tests/test_analysis.py (+3), server/tests/test_profiles.py
                (+1), ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `_sniffed_reader_for` chooses the reader for a file: the format's own
    reader, unless the header's comma count claims more columns than sniffing
    found, in which case it re-sniffs with `ignore_errors=true` and takes that
    when it widens the description. Both the profile and the run path go
    through it - `_bind_dataset`, `_bind_datasets`, `profile_csv` and
    `_duplicate_row_count` - so a file reads the same way everywhere.
  - The retry is conditional on purpose. `ignore_errors` on a well-formed file
    would turn a genuine conversion error into a silent null, so it is earned
    by a collapse, never applied by default; a recovery that does not widen
    the description is discarded, so a quoted header containing a comma costs
    one sniff and changes nothing.
  - No contract changed; no endpoint changed; no new feature.
NON-GOALS: repairing the data - the stray field becomes a null and the profile
           reports it as one, which is what the missing-data check exists to
           catch. Quoted fields containing commas are not re-parsed in Python;
           DuckDB's own header is authoritative once the recovery widens it.
CONSTRAINTS: green only - nothing committed while red, and each new test was
             proven to fail without the fix.
ACCEPTANCE CRITERIA:
- [x] a CSV with a stray trailing comma profiles as the header's columns, with
      every row counted and the malformed cell reported as a null
- [x] SQL written against those columns runs on the same file and returns the
      same columns - profile and run read alike
- [x] a well-formed CSV and a parquet file keep the strict reader, so a
      genuine conversion error is still an error and never a silent null
- [x] 388 server tests pass and all 25 real-server e2e steps pass
TESTS: 4 added - test_analysis.py gains the reader-selection unit tests (the
       clean file and the parquet keep their reader, the collapsed file gains
       ignore_errors, and profile_csv itself reads four columns from the
       malformed file), and test_profiles.py drives the same file through the
       attach -> profile -> run path over HTTP. All four fail on the pre-fix
       code.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` -> 388 passed in 180s;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` ->
              ALL STEPS PASS.
STATE UPDATE: TASKS/CURRENT_STATE gain the fix; the three seeded cases and the
              sidecar rebuild are recorded in HANDOFF.
LESSON: the malformed shape is not exotic - it is one keystroke past a null,
        and the honest null next to it works perfectly, so the failure looked
        like a fixture bug for a while before it was a product bug. The tell
        was that the *recovery* options disagree: null_padding widens the row
        to cover the mistake and ignore_errors narrows the mistake to a null.
        Only one of those keeps the table the analyst uploaded.
```

TASK: P7-CSV-002 - a CSV with a stray trailing comma no longer collapses to one column
ID: P7-CSV-002
PRIORITY: medium
STATUS: DONE
SUMMARY: read_csv_auto's delimiter guess dies on a row wider than its header,
         and the whole file then reads as a single column of raw lines - the
         profile describes nothing and the SQL derived from it cannot run.
         `_sniffed_reader_for` compares the sniffed width against the header's
         own comma count and re-sniffs with ignore_errors when sniffing
         collapsed, keeping every row and dropping only the stray field to a
         null. Both profiling and the run path go through it, so a file reads
         the same way everywhere. The retry is earned by a collapse, never on
         by default, because ignore_errors on a clean file would silence real
         conversion errors.

### P7-CORS-001 contract

```
TASK ID: P7-CORS-001
MILESTONE: P7 Product Modes
CAPABILITY: Reliability (the packaged desktop app talking to its own core)
GOAL: The shipped .app opened to "Failed to load cases: Failed to fetch", and
      its New Case form was unreachable behind that. Every fetch the packaged
      frontend makes is cross-origin - the webview is served from Tauri's own
      scheme, the core from 127.0.0.1:8123 - and the core answered with no
      `Access-Control-Allow-Origin`, so the browser discarded each response
      before the app saw it. The core's own log showed a clean 200 for the very
      request the shell reported as failed, which is why no test caught it.
CONTEXT: every in-process and real-server verification drives the core from an
         origin it does not gate. Starlette's TestClient does not enforce CORS,
         and the e2e script talks to the core directly. The browser is the only
         gate, and nothing in the repo drove a browser at the core until a human
         opened the app.
INPUTS: the packaged .app as built; a real headless Chrome over the DevTools
        protocol, serving the shipped bundle from a foreign origin to reproduce
        the browser's view of the fetch.
RELEVANT FILES: server/app/main.py (the CORS middleware and its allowlist),
                server/tests/test_cors.py (new),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `server/app/main.py` gains an `ALLOWED_ORIGINS` frozenset and a CORS
    middleware: an origin on the list is echoed back with `Vary: Origin`, an
    OPTIONS preflight is answered 204 with the allowed methods and the
    content-type header, and any other origin gets neither - the response still
    succeeds, because CORS is the browser's gate and not the server's, but the
    browser will not release it.
  - The allowlist is narrow and deliberately has no wildcard: the core is a
    local process holding an analyst's cases and chat history, and `*` would let
    a webpage the user merely visits read them. Tauri's own two origins plus the
    dev-server ports are every origin this frontend legitimately has.
NON-GOALS: changing the frontend (it was correct - it fetched the right URL and
           reported the browser's error honestly), changing the shell's origin
           handling, allowing credentials, broadening the allowlist to user
           configuration.
CONSTRAINTS: no new dependency (the middleware is a plain FastAPI middleware,
             not starlette's CORSMiddleware, so the preflight answers 204 rather
             than 405 and nothing else changes); the core stays unreadable to
             origins it does not know.
ACCEPTANCE CRITERIA:
- [x] a real browser, served the shipped bundle from a foreign origin, sees the
      fetch refused; served from an allowed origin, sees it succeed
- [x] the shell's own origin is echoed, a preflight answers 204 with methods and
      headers, and an unknown origin gets no CORS header at all
- [x] 4 new tests in tests/test_cors.py, proven to fail without the fix and pass
      with it
- [x] 384 server tests pass (was 380) and all 25 real-server e2e steps pass
TESTS: tests/test_cors.py - 4 tests. Two were verified against a temporarily
       disabled middleware: the origin-echo and the preflight both fail, so the
       suite cannot go green with the bug present.
VERIFICATION: `server/.venv/bin/python -m pytest` -> 384 passed;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` -> ALL
              STEPS PASS; reproduced in headless Chrome that the same fetch that
              failed before the fix succeeds after it.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF name the CORS gap and the rebuild
              that remains before a release ships it.
```

TASK: P7-CORS-001 - the packaged app could not reach its own core
ID: P7-CORS-001
PRIORITY: high
STATUS: DONE
SUMMARY: The shipped .app opened to a dead screen - "Failed to load cases:
         Failed to fetch" - with the New Case form unreachable behind it. The
         frontend was never at fault and neither was the core: the browser was
         the only thing between them that knew. Tauri serves the bundled
         frontend from its own scheme while the core answers on
         127.0.0.1:8123, so every fetch the app makes is cross-origin, and the
         core answered with no `Access-Control-Allow-Origin`. The browser
         discarded each response - while the core's own log recorded a clean
         200 for the identical request.

Reproduced twice before the fix, in a real headless Chrome over the DevTools
protocol: serving the shipped bundle from a foreign origin, the fetch failed
with exactly the message the user saw; the core logged 200. After the fix the
same fetch returns the case list and the page renders it.

`server/app/main.py` gains `ALLOWED_ORIGINS` and a CORS middleware. An origin on
the list is echoed with `Vary: Origin`; an OPTIONS preflight is answered 204
with the allowed methods and the content-type header - written as a plain
middleware rather than starlette's CORSMiddleware because no endpoint handles
OPTIONS, and leaving the preflight to Starlette answers 405 and the real
request is never sent. Anything not on the list gets neither header: the
response still succeeds, since CORS is the browser's gate and not the server's,
but the browser will not release it. No wildcard - the core holds an analyst's
cases and chat history, and `*` would let a webpage the user merely visits read
them.

LESSON: this is the sharpest illustration yet of the gap P7-WALK-001 named.
Every automated artifact in this repo drives the core from a position CORS does
not gate - TestClient does not enforce it, and the e2e script talks to the core
directly. The browser is the only gate, and nothing in the repo drove a browser
at the core. The core logging 200 while the app reported failure was not a
contradiction; it was the whole bug, and only a human opening the .app could
see it. The desktop suite's 22 Rust tests verified the shell could start the
core and that the port was theirs - and stopped exactly one step short of
asking whether the webview could read an answer.


