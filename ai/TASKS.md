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

### P2-DATA-006 contract

```
TASK ID: P2-DATA-006
MILESTONE: P2 MVP
CAPABILITY: Data Layer (breadth)
GOAL: Accept Parquet and Excel in addition to CSV.

CONTEXT: CSV attach works; profile_csv handles any tabular file DuckDB reads.
INPUTS: multipart upload (.csv/.parquet/.xlsx).
RELEVANT FILES: server/app/main.py, models.py, tests/test_datasets.py
REQUIRED CHANGE: accept the two new extensions; store with a format field.
NON-GOALS: profiling depth (P2-DATA-007), schema detection heuristics, UI.
CONSTRAINTS: read via DuckDB throughout - one engine, one path.
ACCEPTANCE CRITERIA:
- [x] .parquet and .xlsx attach and are stored
- [x] each profiles correctly (rows/columns) via the existing profile endpoint
- [x] unsupported extension rejected with 400
TESTS: golden parquet, golden xlsx, unsupported type.
VERIFICATION: pytest + in-process round-trip.
STATE UPDATE: mark P2-DATA-006 done on pass.
```

### P2-DATA-007 contract

```
TASK ID: P2-DATA-007
MILESTONE: P2 MVP
CAPABILITY: Data Layer (depth)
GOAL: Deepen the profile so it carries what an analyst (and later the AI planner)
      needs before writing a query.

CONTEXT: csv/parquet/xlsx all attach and profile (rows/columns/null counts).
         The profile is the input to the AI planning step, so it has to describe
         the data, not just count rows.
INPUTS: an attached, profiled dataset (any supported format).
RELEVANT FILES: server/app/analysis.py, models.py, main.py, db.py,
                tests/test_profiles.py
REQUIRED CHANGE: extend the profile with
  - per column: inferred DuckDB type, null count, null percentage, distinct count
  - per numeric column: min, max, average
  - per dataset: duplicate row count (total rows minus distinct rows)
NON-GOALS: no visualization, no AI interpretation, no UI, no heuristic schema
           repair, no per-value histograms.
CONSTRAINTS: read via DuckDB throughout - one engine, one path; every new
             stat must survive across formats (csv/parquet/xlsx); the existing
             validation null_count sum must keep working unchanged.
ACCEPTANCE CRITERIA:
- [x] every column reports type, null_count, null_percentage, distinct_count
- [x] numeric columns report min/max/avg
- [x] duplicate row count is reported and correct
- [x] empty (header-only) datasets profile without error
- [x] existing profiles and the validation gate still pass
TESTS: numeric stats; type inference; distinct counts; duplicate rows;
       header-only dataset; full regression suite.
VERIFICATION: pytest + in-process round-trip.
STATE UPDATE: mark P2-DATA-007 done on pass.
```

## P3 V1

Goal: make the MVP substantially better for repeated real-world use (roadmap
section 6). Entry order follows ai/ROADMAP.md; hardening first because the P3
AI code-generation work multiplies the risk of the P2 soft sandbox.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P3-SEC-001 | Analysis Workspace (hardening) | M | DONE | P2-ANALYSIS-008 | Python runs in a separate process under an OS sandbox; writes outside scratch, network, and runaway CPU are bounded and reported as 400 |
| P3-CHART-002 | Analysis Workspace (raster charts) | M | TODO | P3-SEC-001 | PNG/high-DPI rendering behind the same chart interface |
| P3-DATA-003 | Data Layer (multi-dataset) | M | TODO | P2 done | Multiple datasets per case with joins |

### P3-SEC-001 contract

```
TASK ID: P3-SEC-001
MILESTONE: P3 V1
CAPABILITY: Analysis Workspace (hardening)
GOAL: Move Python execution out of the API process and under an OS-level
      sandbox.

CONTEXT: P2-ANALYSIS-008 shipped an in-process soft sandbox (import allowlist,
         restricted builtins, dunder-hardened handle, CPU/wall-clock limits).
         It stops accidental damage, not a determined escape, and a crash or
         unbounded allocation in user code hits the API process itself.
INPUTS: an attached dataset and a user Python script (unchanged API).
RELEVANT FILES: server/app/python_exec.py, server/app/python_worker.py (NEW),
                server/app/main.py (unchanged), server/tests/test_python_hard_sandbox.py (NEW)
REQUIRED CHANGE: execute user code in a child process; on macOS wrap it with
         sandbox-exec under a profile that denies every filesystem write
         outside the run's scratch directory and denies all network access;
         scrub the child environment so API-process secrets never reach it;
         bound wall clock at the process-group level (kill the tree, not just
         the wrapper) and keep the in-process guards as defense in depth.
NON-GOALS: Linux landlock / Windows job-object sandboxes (the separate process
           plus inner guards remain the floor on those hosts); address-space
           caps (macOS rejects useful RLIMIT_AS values); validation of Python
           runs by re-execution.
CONSTRAINTS: the /runs/python contract is unchanged - same request, same
             response, same 400 messages; existing tests must pass unmodified.
ACCEPTANCE CRITERIA:
- [x] user Python runs in a process separate from the API
- [x] on macOS the child is under sandbox-exec; a write outside scratch and a
      network connection are denied by the kernel
- [x] an unbounded loop ends at the time limit and the API answers 400
- [x] a worker that dies is reported as 400, never raised into the API
- [x] API-process environment secrets are absent from the child environment
- [x] full server suite and the P2 gate still pass
TESTS: seatbelt enforcement probe (scratch write allowed, outside write and
       network denied), child env scrub, process-group kill, runaway loop,
       dead worker, contract violation.
VERIFICATION: pytest + verification/p2/verify_p2.py regression.
STATE UPDATE: mark P3-SEC-001 done on pass.
```
