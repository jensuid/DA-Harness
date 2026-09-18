# DAH - Current State

- **Phase:** P0 Foundation
- **Milestone status:** IN PROGRESS
- **Completed capabilities:** FastAPI core with health endpoint; pytest infrastructure; git repository
- **Active task:** none (P0-INFRA-001 complete)
- **Known issues:** none
- **Test status:** 1 passed (server/tests/test_health.py)
- **Architecture status:** web-first MVP decided (DEC-001); FastAPI + SQLite (state) + DuckDB (analytics); Tauri deferred to post-MVP
- **Next task:** P0-WEB-002 (Vite/React shell + case-creation screen)
- **Blockers:** none

## Platform decisions (locked, see ai/DECISIONS.md)

- Backend: Python + FastAPI
- Case state: SQLite
- Analytical engine: DuckDB (analytical queries only)
- Frontend: React + Vite (browser-served; Tauri wraps the same bundle post-MVP)
- Frontend never touches filesystem or DuckDB directly - API only

## How to run

- Server: `cd server && .venv/bin/python -m uvicorn app.main:app --port 8123`
- Tests: `cd server && .venv/bin/python -m pytest`
