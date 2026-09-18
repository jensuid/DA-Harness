# DAH - Task Backlog

| Task ID | Milestone | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P0-INFRA-001 | P0 Foundation | M | DONE | none | pytest passes; live `GET /health` returns 200 `{"status":"ok"}` |
| P0-WEB-002 | P0 Foundation | M | DONE | P0-INFRA-001 | Vitest 2/2 pass; `tsc -b && vite build` succeeds; `/api` proxy reaches backend |
| P0-DATA-003 | P0 Foundation | M | NOT_STARTED | P0-WEB-002 | Case persists to SQLite, survives reopen; DuckDB answers a trivial analytical query |
