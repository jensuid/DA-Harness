# DAH - Current State

- **Phase:** P1 Vertical Slice
- **Milestone status:** P0 Foundation PASSED (2026-09-18, verification/p0/REPORT.md)
- **Completed capabilities:** FastAPI core (health, case create/get/list); SQLite case persistence; DuckDB analytical engine; Vite/React/TS shell with case-creation screen; pytest + Vitest; git repository; P0 verification harness
- **Active task:** none (P0 complete, P1 not yet decomposed)
- **Known issues:** none
- **Test status:** server 5 passed; web 2 passed
- **Architecture status:** web-first MVP decided (DEC-001); FastAPI + SQLite (state) + DuckDB (analytics); Tauri deferred to post-MVP
- **Next task:** decompose P1 into tasks (see P1 scope below)
- **Blockers:** none

## P1 scope - the vertical slice

One complete analytical investigation, end to end:

```
Create Case -> Question -> Load CSV -> Profile Data -> Generate Analysis Plan
-> Run Simple Analysis -> Create Finding -> Attach Evidence -> Validate Finding
-> Save Case
```

No expansion to broad MVP features until this gate passes. AI planning is
deferred to a later slice within P1 - the loop must work deterministically first.

## Platform decisions (locked, see ai/DECISIONS.md)

- Backend: Python + FastAPI
- Case state: SQLite
- Analytical engine: DuckDB (analytical queries only)
- Frontend: React + Vite (browser-served; Tauri wraps the same bundle post-MVP)
- Frontend never touches filesystem or DuckDB directly - API only

## How to run

- P0 verification: `python3 verification/p0/verify_p0.py`
- Server: `cd server && .venv/bin/python -m uvicorn app.main:app --port 8123`
- Server tests: `cd server && .venv/bin/python -m pytest`
- Web dev: `cd web && npm run dev` (proxies /api to :8123)
- Web build: `cd web && npm run build`
- Web tests: `cd web && npm test`
