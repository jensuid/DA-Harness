# DAH - Handoff

## What was completed

- DEC-001 recorded: web-first MVP, Tauri desktop shell post-MVP
- FastAPI, SQLite, DuckDB locked as platform decisions
- Four master docs updated to reflect web-first delivery
- graphify skill installed for Codex; AGENTS.md guidance live
- P0-INFRA-001 DONE: git repo, repo scaffold, FastAPI skeleton, health endpoint, pytest
- P0-WEB-002 DONE: Vite + React + TS shell, case-creation screen, api client, Vitest
- P0-DATA-003 DONE: SQLite case persistence, DuckDB analytical engine, case endpoints

## What changed

- server/app/db.py: SQLite connection + cases schema (check_same_thread=False for FastAPI threadpool)
- server/app/models.py: CaseCreate / Case pydantic models
- server/app/analysis.py: DuckDB profile_csv (row count + columns) - the seed of the Data & Evidence Engine
- server/app/main.py: POST /cases, GET /cases/{id}, GET /cases
- server/tests/test_cases.py: create/reopen golden test, 404, list
- server/tests/test_analysis.py: DuckDB CSV profiling test
- .gitignore: excludes the local dev database

## Tests performed

- server `pytest`: 5 passed (health, create+reopen, 404, list, profile_csv)
- Live golden test: created case, killed server, restarted, case reopened intact
- End-to-end: POST /api/cases through the Vite proxy -> 201; list returned the case
- web `npm test` / `npm run build`: still green (2 passed, build ok)

## Unresolved problems

- none blocking. CSV profiling is engine-only (no endpoint yet) - the API surface
  arrives in P1 when the vertical slice needs it.

## Next action

Run the P0 milestone verification: execute the exit-test sequence
(start app -> backend op -> persist state -> restart -> recover -> run tests)
and confirm all nine P0 exit criteria pass (see ai/CURRENT_STATE.md).
On PASS, begin P1 task decomposition: Case -> Question -> CSV -> Profile -> Plan
-> Analysis -> Evidence -> Finding -> Validation -> Save.

## Important context

- server venv at server/.venv (Python 3.14); install with `uv pip install --python .venv/bin/python -e ".[dev]"`
- web deps installed; node_modules gitignored
- dev DB is server/dah.db (gitignored); tests use tmp_path
- graph is stale vs docs (doc-only semantic changes); rebuild now that real code exists.
