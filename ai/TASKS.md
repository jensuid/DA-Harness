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
| P2-DATA-007 | Data Layer (depth) | M | NOT_STARTED | P2-DATA-006 | Profile covers duplicates, types, basic stats |
| P2-ANALYSIS-008 | Analysis Workspace | M | NOT_STARTED | P2-DATA-006 | Read-only Python executes against a dataset, result persisted |
| P2-ANALYSIS-009 | Analysis Workspace | M | NOT_STARTED | P2-ANALYSIS-008 | Chart image persisted from a run result |
| P2-CASE-010 | Analysis Case | M | NOT_STARTED | P1 done | Rename, duplicate, delete cases |
| P2-AI-011 | AI Planning | M | NOT_STARTED | P2-ANALYSIS-008 | Structured plan (sub-questions, hypotheses) from a question + profile |
| P2-CASE-012 | Export | M | NOT_STARTED | P2-AI-011 | Case exports as a self-contained JSON package |

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
