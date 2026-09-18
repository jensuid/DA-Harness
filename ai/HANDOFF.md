# DAH - Handoff

## What was completed

- P0 PASSED: all exit criteria, verification/p0/REPORT.md
- P1 decomposed into 5 tasks (ai/TASKS.md)
- P1-DATA-001 DONE: CSV dataset attachment (multipart upload, on-disk storage)

## What changed

- server/app/db.py: datasets table; DATA_DIR (env-overridable); executescript for multi-statement schema
- server/app/models.py: Dataset model
- server/app/main.py: POST/GET /cases/{id}/datasets; validates .csv and non-empty; DATA_DIR via module for test patching
- server/tests/test_datasets.py: upload, reopen, 404, non-csv, empty-file tests
- .gitignore: server/data/ excluded

## Tests performed

- server pytest: 9 passed (5 prior + 4 new dataset tests)
- Live: uploaded sales.csv, restarted server, dataset listed and file intact

## Unresolved problems

- none. Profiling stats not yet computed at ingest - that is P1-DATA-002.

## Next action

P1-DATA-002: profile an attached dataset via DuckDB (rows, columns, per-column
missingness), store the profile JSON against the dataset, expose
GET /cases/{id}/datasets/{dataset_id}/profile.

## Important context

- python-multipart added for uploads
- DATA_DIR defaults to server/data/ (gitignored); tests patch app.db.DATA_DIR
- server venv at server/.venv (Python 3.14)
