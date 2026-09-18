# DAH - Task Backlog

| Task ID | Milestone | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P0-INFRA-001 | P0 Foundation | M | DONE | none | pytest passes; live `GET /health` returns 200 `{"status":"ok"}` |
| P0-WEB-002 | P0 Foundation | M | DONE | P0-INFRA-001 | Vitest 2/2 pass; `tsc -b && vite build` succeeds; `/api` proxy reaches backend |
| P0-DATA-003 | P0 Foundation | M | DONE | P0-WEB-002 | 5/5 pytest pass; case survives server restart; DuckDB profiles a CSV; proxy round-trip works |

## P1 task decomposition (pending)

Not yet decomposed - see ai/HANDOFF.md next action.
