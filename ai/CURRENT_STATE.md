# DAH - Current State

- **Phase:** P0 Foundation
- **Milestone status:** VERIFICATION (all three P0 tasks implemented; milestone gate pending)
- **Completed capabilities:** FastAPI core (health, case create/get/list); SQLite case persistence; DuckDB analytical engine; Vite/React/TS shell with case-creation screen; pytest + Vitest; git repository
- **Active task:** none (P0-DATA-003 complete)
- **Known issues:** none
- **Test status:** server 5 passed; web 2 passed
- **Architecture status:** web-first MVP decided (DEC-001); FastAPI + SQLite (state) + DuckDB (analytics); Tauri deferred to post-MVP
- **Next step:** run the P0 milestone exit test and evaluate exit criteria (see below)
- **Blockers:** none

## P0 exit criteria checklist

- [x] application launches (web frontend builds and serves)
- [x] web frontend builds and serves (was: Tauri shell works)
- [x] React UI renders
- [x] Python backend starts
- [x] frontend <-> backend communication works (proxy verified)
- [x] basic state can persist (SQLite, survives restart)
- [x] test suite runs (pytest 5, vitest 2)
- [x] repository structure is established
- [x] development documentation exists (docs/ + ai/)

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
