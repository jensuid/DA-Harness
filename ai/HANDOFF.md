# DAH - Handoff

## What was completed

- P0 PASSED: all exit criteria, verification/p0/REPORT.md
- P1 decomposed into 5 tasks (ai/TASKS.md)
- P1-DATA-001 DONE: CSV dataset attachment (multipart upload, on-disk storage)
- P1-DATA-002 DONE: deterministic dataset profiling (rows, columns, per-column null counts)

## What changed

- server/app/analysis.py: profile_csv now returns rows/columns/stats with null counts
- server/app/db.py: profiles table added
- server/app/models.py: Profile model
- server/app/main.py: POST/GET /cases/{id}/datasets/{dataset_id}/profile
- server/tests/test_analysis.py: updated for new profile_csv shape + missingness test
- server/tests/test_profiles.py: profile+reopen, 404 for unknown dataset, 404 before profiling

## Tests performed

- server pytest: 13 passed
- Live: profiled messy.csv -> 3 rows, null counts correct (revenue=1, region=1)

## Unresolved problems

- none. SQL execution is next - profiles are read-only inputs to it.

## Next action

P1-ANALYSIS-003: run user SQL against an attached dataset via DuckDB and persist
the result. Introduces the evidence chain: result -> query -> dataset.
Consider SQL safety (read-only, single statement) since query text is user input.

## Important context

- python-multipart installed for uploads
- DATA_DIR defaults to server/data/ (gitignored); tests patch app.db.DATA_DIR
- server venv at server/.venv (Python 3.14)
