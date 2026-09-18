# DAH — Decisions

## DEC-001 — Web-first MVP, Tauri desktop shell post-MVP

**Date:** 2026-09-18

### Decision

Build the MVP as a browser-served web application: **React + Vite** frontend, **Python
(FastAPI)** backend. Adopt **Tauri** as the desktop shell only **after the MVP passes**,
wrapping the existing React bundle with the Python core running as a sidecar.

### Technology selections (confirmed)

| Concern       | Choice          | Rationale                                |
|---------------|-----------------|------------------------------------------|
| Backend       | Python + FastAPI| Typed, structured I/O — fits the "structured not prose" AI rule |
| Case state    | SQLite          | Reliable transactional persistence for Analysis Cases |
| Analytical    | DuckDB          | Embedded, file-based analytical engine; kept strictly separate from state |

### Architectural contract

**The frontend must never touch the filesystem or DuckDB directly — only through the
API.** This is the single rule that makes the later Tauri migration a host swap rather
than a rewrite: the browser host is replaced by the desktop shell, and the React bundle
stays unchanged.

### Reason

A browser-served MVP is faster to iterate on and avoids coupling early feature work to
desktop packaging, signing, and sidecar complexity. Deferring Tauri removes a whole
class of P0 risk (shell integration, native build tooling) without compromising the
local-first execution model — datasets, DuckDB, and Analysis Cases all remain local.

### Alternatives considered

- **Tauri from P0 (previous plan):** earlier desktop value, but pays packaging and
  shell-integration cost before the core analytical loop is even proven.
- **Electron:** larger bundle and heavier resource use; no advantage over Tauri for a
  local-first Python-backed app.

### Consequences

- P0 exit criteria change: "Tauri shell works" becomes "web frontend builds and serves".
- Browser file-access limits are acceptable for the MVP; datasets are selected via the
  API, not by direct frontend filesystem reads.
- Tauri adoption becomes a P3 task with its own exit criteria, not a P0 dependency.
- FastAPI + SQLite + DuckDB are now fixed platform decisions (recorded here, not
  re-debated per task).
