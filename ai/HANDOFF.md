# DAH - Handoff

## What was completed

- DEC-001 recorded: web-first MVP, Tauri desktop shell post-MVP
- FastAPI, SQLite, DuckDB locked as platform decisions
- Four master docs updated to reflect web-first delivery
- graphify skill installed for Codex; AGENTS.md guidance live
- P0-INFRA-001 DONE: git repo, repo scaffold, FastAPI skeleton, health endpoint, pytest
- P0-WEB-002 DONE: Vite + React + TS shell, case-creation screen, api client, Vitest

## What changed

- docs/: six Tauri-as-initial-platform references corrected
- ai/: DECISIONS.md, TASKS.md, CURRENT_STATE.md maintained
- server/: FastAPI app + GET /health + pytest test
- web/: Vite/React/TS app, CaseCreation screen, api.ts client (GET /health, POST /cases), setup-tests.ts, Vitest tests

## Tests performed

- server `pytest`: 1 passed (test_health_returns_ok)
- web `npm test`: 2 passed (renders form; core reachable via mocked /health)
- web `npm run build`: tsc -b + vite build succeed (145 KB bundle)
- Live: uvicorn + vite booted together; `/api/health` proxied through Vite -> 200 `{"status":"ok"}`

## Unresolved problems

- POST /cases endpoint does not exist yet - intentionally deferred to P0-DATA-003.
  The frontend client is already written against it.

## Next action

Start P0-DATA-003: SQLite-backed case persistence (create/save/reopen) behind
POST /cases + GET /cases/{id}, plus DuckDB wired for analytical queries only.
Add golden tests for persistence. Then rerun the frontend against the real endpoint.

## Important context

- server venv at server/.venv (Python 3.14); install with `uv pip install --python .venv/bin/python -e ".[dev]"`
- web deps installed; node_modules gitignored
- graph is stale vs docs (doc-only semantic changes); rebuild after P0 code lands.
