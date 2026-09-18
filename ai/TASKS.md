# DAH - Task Backlog

## P0 Foundation - PASSED

| Task ID | Status | Verification |
|---------|--------|--------------|
| P0-INFRA-001 | DONE | pytest passes; live `GET /health` returns 200 |
| P0-WEB-002 | DONE | Vitest 2/2 pass; build succeeds; `/api` proxy reaches backend |
| P0-DATA-003 | DONE | 5/5 pytest pass; case survives restart; DuckDB profiles CSV |

## P1 Vertical Slice

Goal: one complete analytical investigation end to end.

```
Create Case -> Question -> Load CSV -> Profile -> Plan -> Analysis
-> Finding -> Evidence -> Validation -> Save -> Reopen
```

AI planning is deliberately excluded from these tasks. The deterministic loop
must work first; AI assistance joins in a later slice once the chain is proven.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P1-DATA-001 | Data Ingestion | M | DONE | none (P0 done) | CSV attaches to a case, file on disk, survives reopen |
| P1-DATA-002 | Data Profiling | M | DONE | P1-DATA-001 | Profile (rows/columns/missingness) stored against the dataset |
| P1-ANALYSIS-003 | Analysis Execution | M | NOT_STARTED | P1-DATA-002 | SQL run against attached CSV via DuckDB, result persisted |
| P1-EVIDENCE-004 | Evidence & Findings | M | NOT_STARTED | P1-ANALYSIS-003 | Finding links to result -> query -> dataset chain |
| P1-VALID-005 | Validation | M | NOT_STARTED | P1-EVIDENCE-004 | Rerun reproduces result; missing-data caveat attached |

### P1-DATA-001 contract

```
TASK ID: P1-DATA-001
MILESTONE: P1 Vertical Slice
CAPABILITY: Data Ingestion
GOAL: Attach a CSV dataset to an Analysis Case and persist it.

CONTEXT: Cases already persist in SQLite; profile_csv exists but has no endpoint.
INPUTS: multipart CSV upload.
RELEVANT FILES: server/app/main.py, models.py, db.py, tests/test_datasets.py
REQUIRED CHANGE: datasets table + storage dir; POST/GET /cases/{id}/datasets.
NON-GOALS: profiling stats, Parquet/Excel, AI, UI.
CONSTRAINTS: frontend never touches the filesystem (DEC-001).
ACCEPTANCE CRITERIA:
- [ ] CSV uploads to a case and is stored on disk
- [ ] dataset row recorded and linked to the case
- [ ] reopening the case lists the dataset
- [ ] unknown case returns 404
TESTS: golden upload, reopen, 404, empty file.
VERIFICATION: pytest + live curl round-trip.
STATE UPDATE: mark P1-DATA-001 done on pass.
```
