# DAH - Current State

 - **Phase:** P4 Production Candidate - COMPLETE (all 5 checklist items:
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003 + P4-UX-004, P4-VALID-005,
  P4-PERF-006, P4-CI-007). P3 V1 is COMPLETE: all 10 entry-checklist items,
  231 server tests, and a P3 gate of its own. P5 Production Grade is IN
  PROGRESS (3 of 5 checklist items: the P4 gate, observability and the 500
  envelope are done; signing and release automation remain).
- **Global roadmap status:** ai/ROADMAP.md (phase tracker - current stage, phase table, next-phase entry checklist)
- **Milestone status:** P1 Vertical Slice PASSED (verification/p1/REPORT.md); P0 PASSED
- **Completed capabilities:** FastAPI core; SQLite case persistence; DuckDB engine; Vite/React shell; P0 verification harness; CSV dataset attachment; deterministic dataset profiling; read-only SQL analysis runs with persisted results; findings with evidence chain; validation via rerun; parquet + xlsx ingest; deep profiling; **read-only Python execution with persisted results (P2-ANALYSIS-008); chart images rendered and persisted from run results (P2-ANALYSIS-009);
case management - rename, duplicate, delete (P2-CASE-010);
AI planning with structured output (P2-AI-011); case export as a self-contained
JSON package with import round trip (P2-CASE-012)**
- **Active task:** P5-RELIABILITY-003 DONE - the carried 500 envelope. A fault
  used to answer Starlette's plain-text "Internal Server Error", which the
  client tolerated but which was the last rough edge of the error contract. Now
  a registered handler for `Exception` answers
  `{"detail": "internal error", "request_id": <uuid4 hex>}`, logs the traceback
  under that same id (this matters as much as the envelope: catching the
  exception means uvicorn no longer logs it, so without an explicit record the
  traceback P5-OBSERVE-002 made recoverable would stop reaching the file), and
  puts nothing else in the body - a fault's message can quote the user data it
  was holding, so only the id and a fixed message leave the process. 4xx and
  404 are untouched: their own `detail`, no id. The client surfaces the id
  (`error 3f239488` in the message a user reads) so it is quotable. 16 server
  tests in the error-semantics suite (was 12) and 4 new web tests. Before it:
  P5-OBSERVE-002, observability. The packaged core is a
  PyInstaller sidecar whose stderr nobody reads, so a 500's traceback used to
  vanish. The core now writes a rotating log (2MB x 3 backups, bounded at ~8MB)
  into the same data directory the shell already points the cases at, overridable
  with DAH_LOG_DIR exactly as DAH_DB_PATH overrides the database. One line per
  request holds only the method, path, status and duration - the body is never
  logged, so an analyst's question, their SQL and every value in their data stay
  out of the file (a live smoke test against uvicorn verified the request path is
  logged and the question text is not). A real fault's traceback reaches the file
  through uvicorn's own logger, and GET /logs?lines=N tails it read-only,
  reporting `enabled: false` rather than erroring when file logging is off.
  21 tests. Before it: P5-VERIFY-001, the P4 gate. P4 relied on the P3 gate
  plus CI, which never exercised the P4 capabilities against each other, so it
  got a gate of its own. Where the earlier gates walk the happy path, this one
  walks the edges a controlled external user actually reaches: a 5000-row
  dataset with analytically-known aggregates, the result cap truncating a full
  scan while an aggregate over the same data stays exact, bad SQL answering 400
  with the engine's own message and persisting nothing, a write and a sandbox
  escape both refused, an injected harness fault answering 500 instead of
  blaming the analyst, a deliberately broken LLM degrading to the deterministic
  engine rather than blocking, the assistant drafting without writing, eight
  repeat validations of an unordered GROUP BY agreeing, and an export/import
  round trip. 18 steps and 10 exit criteria, all PASS; CI runs it on every
  push. Hermetic - no credential is ever set, and the one step that sets a
  dummy key breaks the LLM on purpose.
  Before it: P4 in full (the P3 gate, error semantics, the assistant surfaces,
  validation determinism, large-dataset performance, CI and the signing
  decision).
- **Known issues:** none. CI runs green on GitHub's own runners after five
  local-state bugs it exposed were fixed (see ai/HANDOFF.md, "What the first
  CI runs caught").
- **Test status:** server 256 passed (211 + 16 error semantics + 2 validation
  determinism + 6 large-dataset + 21 observability); web 17 passed (CaseList 5, CaseCreation 3,
  CaseWorkspace 9);
  desktop shell 7 Rust tests (5 unit + 2 e2e, `cd desktop/src-tauri && cargo test [--features e2e]`);
  P2 and P3 gates PASS
- **Next task:** the remaining P5 checklist - macOS signing + notarization
  (formally deferred by DEC-004, blocked on a Developer ID, so not agent work
  until the identity exists) and release automation on top of the packaging job.
  Smaller follow-ups now visible: a "Reveal logs" menu item in the desktop shell
  (the /logs endpoint is the contract; the menu is unverified UI work), and
  showing the request id's full value somewhere copyable.
  Carried: a 500 still answers with Starlette's plain-text "Internal Server
  Error"; the client handles it, but a JSON envelope is the last rough edge of
  the error contract.
- **Blockers:** none

## P2 progress

| Task | Status |
|------|--------|
| P2-DATA-006 parquet + xlsx ingest | DONE |
| P2-DATA-007 deep profiling | DONE |
| P2-ANALYSIS-008 Python execution | DONE |
| P2-ANALYSIS-009 charts | DONE |
| P2-CASE-010 case management | DONE |
| P2-AI-011 AI planning | DONE |
| P2-CASE-012 export | DONE |

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
- Desktop shell, dev (serves the embedded bundle): `cd desktop && npm install && npm run dev`
- Desktop shell, HMR (vite dev server, pinned to port 5273): `cd desktop && npm run dev:hmr`
- Desktop shell, packaged app: `cd server && ./build_sidecar.sh && cd ../desktop && npm run build`
- Desktop shell tests: `cd desktop/src-tauri && cargo test --features e2e`
- Web tests: `cd web && npm test`
- P0 verification: `python3 verification/p0/verify_p0.py` (needs port bind)
- P1 verification: `server/.venv/bin/python verification/p1/verify_p1.py` (in-process)
- P2 verification: `server/.venv/bin/python verification/p2/verify_p2.py` (in-process)
- Python analysis run: `POST /cases/{id}/datasets/{id}/runs/python` with `{"code": "..."}`
- Delete a dataset: `DELETE /cases/{id}/datasets/{id}` (removes the row, profile, plans and file; 400 while a run still binds it)
- Export: `GET /cases/{id}/export` (self-contained JSON package); `POST /cases/import`
  reconstructs it with fresh IDs
- Plan: `POST /cases/{id}/datasets/{id}/plan` (structured plan from question + profile; deterministic by default, LLM when DAH_LLM_API_KEY is set, source field records which); latest at `GET .../plan`, history at `GET .../plans`
- Search cases: `GET /cases?q=<term>` (case-insensitive substring over question and dataset; blank lists all)
- Case timeline: `GET /cases/{id}/history` (one event per artifact, chronological)
- Templates: `POST /cases/{id}/template` with `{"name"?}` (promote), `GET /templates`,
  `POST /cases/from-template` with `{"template_id", "question"?, "dataset"?}`,
  `DELETE /templates/{id}` (templates outlive their source case)
- Interpret a run: `POST /cases/{id}/runs/{id}/interpret` (plain-language read of the result; deterministic by default, LLM when DAH_LLM_API_KEY is set, `source` records which); latest at `GET .../interpret`, history at `GET .../interpretations`
- Draft a finding: `POST /cases/{id}/runs/{id}/draft-finding` (the candidate finding a result supports - statement, interpretation, caveat and grounds; deterministic by default, LLM when DAH_LLM_API_KEY is set, `source` records which; **writes nothing** - accepting a draft is a POST to `/cases/{id}/findings`, the only path that creates one)
- Generate code: `POST /cases/{id}/datasets/{id}/generate-code` with `{question, kind?: "sql"|"python"}` (the read-only computation a question needs - code, explanation, the columns it reads; deterministic by default, LLM when DAH_LLM_API_KEY is set, `source` records which; **writes nothing** - running a proposal is a POST to the `/runs` or `/runs/python` endpoint)
- Ask the case: `POST /cases/{id}/chat` with `{message}` (an answer grounded in the case's own artifacts, citing each claim in `grounds` as `kind:name`; deterministic by default, LLM when DAH_LLM_API_KEY is set, `source` records which); the whole conversation at `GET /cases/{id}/chat` oldest-first
- Chart from a run: `POST /cases/{id}/runs/{id}/charts` with `{"kind": "bar|line", "x": ..., "y": ..., "series": ...}`; image at `GET /cases/{id}/charts/{id}/image`
- Rename: `PATCH /cases/{id}` with `{question?, dataset?}`; duplicate: `POST /cases/{id}/duplicate`;
  delete: `DELETE /cases/{id}` (removes the case row, all children, and its on-disk data)

## P4 progress

| Task | Status |
|------|--------|
| P4-VERIFY-001 P3 gate script | DONE |
| P4-RELIABILITY-002 error semantics | DONE |
| P4-UX-003 case workspace + chat | DONE |
| P4-UX-004 run-scoped assistant surfaces | DONE |
| P4-VALID-005 validation rerun determinism | DONE |
| P4-PERF-006 large-dataset performance | DONE |
| P4-CI-007 CI + signing decision | DONE |

## How to run (P4)

- P3 verification: `server/.venv/bin/python verification/p3/verify_p3.py`
  (in-process, ~3-4 min; the last step re-runs the suite)

## How to run (web)

- Web tests: `cd web && npm test` (17 tests; vitest, jsdom, no network)
- Web build: `cd web && npm run build` (tsc -b + vite)
- Desktop bundle: `cd web && npm run build:desktop` (absolute API URL for the
  Tauri shell)
- Note for live checks: a background process started from a shell here does not
  outlive its command session - run uvicorn/vite in a persistent session, or
  the smoke test dies with ECONNREFUSED mid-run.

## P5 progress

| Task | Status |
|------|--------|
| P5-VERIFY-001 P4 gate | DONE |
| P5-OBSERVE-002 Observability | DONE |
| P5-RELIABILITY-003 500 envelope | DONE |
