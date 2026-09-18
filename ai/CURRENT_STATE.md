# DAH - Current State

- **Phase:** P0 Foundation
- **Milestone status:** IN PROGRESS
- **Completed capabilities:** none yet (pre-code)
- **Active task:** P0-INFRA-001 - repository scaffold + FastAPI skeleton with health endpoint
- **Known issues:** none
- **Test status:** not yet run
- **Architecture status:** web-first MVP decided (DEC-001); FastAPI + SQLite (state) + DuckDB (analytics); Tauri deferred to post-MVP
- **Next task:** P0-WEB-002 (Vite/React shell) after P0-INFRA-001 passes
- **Blockers:** none

## Platform decisions (locked, see ai/DECISIONS.md)

- Backend: Python + FastAPI
- Case state: SQLite
- Analytical engine: DuckDB (analytical queries only)
- Frontend: React + Vite (browser-served; Tauri wraps the same bundle post-MVP)
- Frontend never touches filesystem or DuckDB directly - API only
