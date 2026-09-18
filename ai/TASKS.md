# DAH - Task Backlog

| Task ID | Milestone | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P0-INFRA-001 | P0 Foundation | M | IN_PROGRESS | none | pytest smoke test passes; `GET /health` returns 200 |
| P0-WEB-002 | P0 Foundation | M | NOT_STARTED | P0-INFRA-001 | Vite build succeeds; case-creation screen renders; Vitest smoke passes |
| P0-DATA-003 | P0 Foundation | M | NOT_STARTED | P0-INFRA-001 | Case persists to SQLite, survives reopen; DuckDB answers a trivial analytical query |
