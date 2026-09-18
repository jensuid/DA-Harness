# DAH - Current State

- **Phase:** P1 Vertical Slice
- **Milestone status:** IN PROGRESS
- **Completed capabilities:** FastAPI core; SQLite case persistence; DuckDB engine; Vite/React shell; P0 verification harness; CSV dataset attachment; deterministic dataset profiling
- **Active task:** none (P1-DATA-002 complete)
- **Known issues:** none
- **Test status:** server 13 passed; web 2 passed
- **Next task:** P1-ANALYSIS-003 (SQL run against attached CSV via DuckDB, result persisted)
- **Blockers:** none

## P1 progress

| Task | Status |
|------|--------|
| P1-DATA-001 CSV ingest | DONE |
| P1-DATA-002 Dataset profiling | DONE |
| P1-ANALYSIS-003 SQL analysis run | NOT STARTED |
| P1-EVIDENCE-004 Findings & evidence | NOT STARTED |
| P1-VALID-005 Validation | NOT STARTED |

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
- P0 verification: `python3 verification/p0/verify_p0.py`
