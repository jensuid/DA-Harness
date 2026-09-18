# DAH - Current State

- **Phase:** P2 MVP
- **Milestone status:** P1 Vertical Slice PASSED (verification/p1/REPORT.md)
- **Completed capabilities:** FastAPI core; SQLite case persistence; DuckDB engine; Vite/React shell; P0 verification harness; CSV dataset attachment; deterministic dataset profiling; read-only SQL analysis runs with persisted results; findings with evidence chain; validation via rerun
- **Active task:** P2-ANALYSIS-008 (Python execution) - DATA-007 complete
- **Known issues:** none
- **Test status:** server 32 passed; web 2 passed
- **Next task:** P2-ANALYSIS-008 - read-only Python executes against a dataset, result persisted
- **Blockers:** none

## P1 progress

| Task | Status |
|------|--------|
| P1-DATA-001 CSV ingest | DONE |
| P1-DATA-002 Dataset profiling | DONE |
| P1-ANALYSIS-003 SQL analysis run | DONE |
| P1-EVIDENCE-004 Findings & evidence | NOT STARTED |
| P1-VALID-005 Validation | DONE |

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
