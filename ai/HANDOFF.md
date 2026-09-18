# DAH - Handoff

## What was completed

- P0 PASSED: all exit criteria, verification/p0/REPORT.md
- P1 decomposed into 5 tasks (ai/TASKS.md)
- P1-DATA-001 DONE: CSV dataset attachment
- P1-DATA-002 DONE: deterministic dataset profiling
- P1-ANALYSIS-003 DONE: read-only SQL analysis runs, persisted with results

## What changed

- server/app/analysis.py: run_query - read-only check (single SELECT-family statement,
  no semicolons), parameter-bound dataset path, 1000-row cap + truncation flag
- server/app/db.py: runs table
- server/app/models.py: RunCreate / Run / RunSummary
- server/app/main.py: POST /cases/{id}/datasets/{dataset_id}/runs,
  GET /cases/{id}/runs (summaries, no rows), GET /cases/{id}/runs/{run_id} (full)
- server/tests/test_runs.py: aggregation+reopen, list excludes rows, DELETE rejected,
  multi-statement rejected, unknown dataset 404

## Tests performed

- server pytest: 18 passed
- Live: SUM(revenue) GROUP BY region -> 2 rows correct; DELETE and multi-statement
  both rejected with 400; run reopened with rows intact

## Unresolved problems

- none. The read-only check is a prefix/semicolon gate, not a full SQL parser -
  acceptable for local single-user MVP; the Verification Plan's Gate K security
  work hardens this later with sandboxing.

## Next action

P1-EVIDENCE-004: findings linked to runs. Establishes the trust chain
finding -> result -> query -> dataset. Then P1-VALID-005 reruns the query to
prove reproducibility.

## Important context

- python-multipart installed for uploads
- DATA_DIR defaults to server/data/ (gitignored); tests patch app.db.DATA_DIR
- server venv at server/.venv (Python 3.14)
