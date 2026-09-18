# DAH - Current State

- **Phase:** P0 Foundation
- **Milestone status:** IN PROGRESS
- **Completed capabilities:** FastAPI core with health endpoint; Vite/React/TypeScript shell with case-creation screen; pytest + Vitest infrastructure; git repository
- **Active task:** none (P0-WEB-002 complete)
- **Known issues:** none
- **Test status:** server 1 passed; web 2 passed
- **Architecture status:** web-first MVP decided (DEC-001); FastAPI + SQLite (state) + DuckDB (analytics); Tauri deferred to post-MVP
- **Next task:** P0-DATA-003 (SQLite case persistence + DuckDB analytical engine)
- **Blockers:** none

## Platform decisions (locked, see ai/DECISIONS.md)

- Backend: Python + FastAPI
- Case state: SQLite
- Analytical engine: DuckDB (analytical queries only)
- Frontend: React + Vite (browser-served; Tauri wraps the same bundle post-MVP)
- Frontend never touches filesystem or DuckDB directly - API only

## How to run

- Server: `cd server && .venv/bin/python -m uvicorn app.main:app --port 8123`
- Server tests: `cd server && .venv/bin/python -m pytest`
- Web dev: `cd web && npm run dev` (proxies /api to :8123)
- Web build: `cd web && npm run build`
- Web tests: `cd web && npm test`
