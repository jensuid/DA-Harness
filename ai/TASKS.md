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


Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.

### P7-E2E-001 contract

```
TASK ID: P7-E2E-001
MILESTONE: P7 Product Modes
CAPABILITY: Verification (the whole app over real HTTP)
GOAL: The P2/P3/P4 gates drive the app in-process through Starlette's
      TestClient. That is fast and is what caught every regression this repo
      has fixed, but it never binds a port, never parses a real multipart
      upload and never runs uvicorn's startup or shutdown. This task adds the
      complement: a fresh uvicorn server on a free port, an isolated data dir,
      and the whole product driven over real HTTP - the case built by hand, the
      reviewer agent auditing it, a second case driven entirely by the analyst
      agent, and the export round trip.
CONTEXT: every verification artifact so far is in-process. A release is the
         next step on the roadmap, and a release ships a packaged server a
         user runs for real; something should have started the actual server
         and talked to it before that.
INPUTS: none from the caller. A free port is chosen by binding a socket, the
        data dir and the database are temp directories, and the LLM env vars
        are emptied for the server's subprocess so the deterministic engines
        answer and the run needs no network.
RELEVANT FILES: verification/e2e/verify_e2e.py (new),
                verification/e2e/REPORT.md (written by the run),
                .github/workflows/ci.yml (the server job runs it after the
                gates and uploads its report)
REQUIRED CHANGE:
  - verification/e2e/verify_e2e.py starts uvicorn as a subprocess, waits for
    its listening line and then /health, drives the journey, and terminates the
    server in a finally. A failure in any step still writes the report and
    exits 1.
  - The journey asserts the real contracts, not approximations of them: the
    profile counts the null and the duplicate in the fixture, a write attempt
    is a 400 from the read-only gate, validation's verdict is accepted as
    honest when the data has a null (partially_supported, with the
    reproducibility check passed), EVALUATE answers all nine axes, the
    reviewer's GET proposes nothing, the reviewer's proposal carries the
    finding's own statement, a cross-role approval is a 409 in either of its
    two real shapes, an unknown role is a 400 naming the roles, and the
    analyst agent terminates with every step's source recorded.
  - No new dependency: urllib from the stdlib, not requests.
NON-GOALS: replacing the in-process gates (they stay; this is the complement
           and is slower), testing the web shell (the web suite does), testing
           the desktop lifecycle (the Rust e2e does), anything that needs an
           LLM key or a network.
CONSTRAINTS: deterministic and offline - the run repeats green; no new
             dependency; exits 1 on any failure; leaves no server process
             behind.
ACCEPTANCE CRITERIA:
- [x] a real uvicorn server starts on a free port and answers /health before
      any step runs
- [x] one case is built by hand end to end: upload, profile, plan, generated
      SQL, a refused write, interpretation, a drafted finding accepted,
      validation, EVALUATE on nine axes
- [x] the reviewer agent audits the finding through the shared approval gate,
      and the audit is recorded with its verdict
- [x] a cross-role approval is refused with a 409, and an unknown role is a
      400 naming the roles
- [x] a second case is driven entirely by the analyst agent to a stated stop,
      with every step's source recorded and the loop closed
- [x] the read-side surfaces answer: the evidence graph, the case history, the
      LEARN walk's four phases, a cited chat answer
- [x] the case round-trips through export/import
- [x] three consecutive runs exit 0, and the server leaves no process behind
- [x] CI runs it after the gates and uploads its report
TESTS: the script IS the test - 25 steps, each asserted, exit code 1 on any
       failure. No pytest file: a journey against a live server is not a unit.
VERIFICATION: three consecutive `server/.venv/bin/python
              verification/e2e/verify_e2e.py` runs, all exit 0, all 25 steps
              PASS, 3.1s each. CI runs it in the server job.
STATE UPDATE: mark P7-E2E-001 done; CURRENT_STATE and ROADMAP name the real-
              server e2e beside the in-process gates.
```

TASK: P7-E2E-001 - the whole app against a real server
ID: P7-E2E-001
PRIORITY: medium
STATUS: DONE
SUMMARY: Every verification artifact in this repo drives the app in-process
         through Starlette's TestClient, which is fast and is what caught every
         regression fixed here - but it never binds a port, never parses a real
         multipart upload, and never runs uvicorn's lifecycle. This task adds
         the complement: a fresh uvicorn server on a free port with an isolated
         data dir, and the whole product driven over real HTTP.

`verification/e2e/verify_e2e.py` starts uvicorn as a subprocess, reads its
listening line for the port, waits on /health, drives the journey, and
terminates the server in a finally so a failure still writes the report and
exits 1. The LLM env vars are emptied for the subprocess rather than merely
unset, because `app.main` loads `server/.env` on a plain uvicorn start and
`load_dotenv` never overrides a variable that is already set - an empty value
wins over the file, and the engines treat an empty key as absent. The first
draft scrubbed the parent environment instead, and the live key from .env made
the plan answer `source=llm` mid-journey.

The journey asserts the real contracts rather than approximations of them, and
four of them were wrong on the first run for assuming instead of reading:

- `SchemaVersion` is `version`/`target`, not `recorded`; `Profile.columns` is a
  list of names with the per-column detail in `stats`; validation answers
  `status`, not `validation_status`; the history counts are keyed by kind with
  no `total`; the LEARN walk's phases are `steps`.
- Validation's verdict on this fixture is `partially_supported`, not
  `supported`: the null revenue trips the missing-data check. That is the
  honesty budget working, so the assertion now accepts the honest verdict and
  checks that reproducibility itself passed and that the null was flagged -
  which is a stronger statement than the one it replaced.
- The cross-role 409 has two shapes, both of which refuse: a dict naming the
  role's own live step when one is pending, and a plain sentence when none is.
  The check handles both and, in the dict case, asserts the `expected` id is
  the analyst's actual pending step, so it cannot pass vacuously.
- The `run_query` read-only gate answers the attempted write with the engine's
  own sentence, quoted in the report rather than summarised.

The agent half drives a second case with no human choice in it: the loop
proposes, each write is approved by id, and it terminates at a stated reason
(profile -> plan -> analyze -> interpret -> accept -> chart -> validate, then
no further step) with the loop closed and every step's `source` recorded as
deterministic.

NON-GOALS held: the in-process gates are unchanged and still the primary
             suite; the web shell and the desktop lifecycle are untouched; no
             step needs a network.
CONSTRAINTS held: no new dependency (urllib, not requests); deterministic
             offline - three consecutive runs green; exit 1 on any failure; no
             server process left behind.
ACCEPTANCE CRITERIA: all 9 - see the checked boxes above.
TESTS: the script is the test - 25 asserted steps over real HTTP.
VERIFICATION: three consecutive runs, all exit 0, all 25 steps PASS, ~3.1s
              each; CI runs it in the server job after the gates and uploads
              its report.
LESSON: four endpoint-shape assumptions were wrong on the first run, and every
        one of them came from reading the contract's prose instead of the
        response model - `version` for `recorded`, `stats` for per-column
        detail, `status` for `validation_status`, `steps` for `phases`. The
        response models in `app/models.py` are the contract and they are one
        grep away; the prose paraphrases them, and a paraphrase is where a
        false assumption enters. The fifth failure was the interesting one:
        the journey went to the live LLM because `.env` is loaded by the server
        itself, so scrubbing the parent environment was not enough. An empty
        value beats the file, and the empty is what the engines treat as
        absent - two behaviours that only compose into "deterministic" if both
        are known.

