# DAH - Current State

 - **Phase:** P4 Production Candidate - COMPLETE (all 5 checklist items:
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003 + P4-UX-004, P4-VALID-005,
  P4-PERF-006, P4-CI-007). P3 V1 is COMPLETE: all 10 entry-checklist items,
  231 server tests, and a P3 gate of its own. P5 Production Grade is IN
  PROGRESS (4 of 5 checklist items: the P4 gate, observability, the 500
  envelope and release automation are done; only signing remains, and it is
  blocked on the Apple Developer ID).
- **Global roadmap status:** ai/ROADMAP.md (phase tracker - current stage, phase table, next-phase entry checklist)
- **Milestone status:** P1 Vertical Slice PASSED (verification/p1/REPORT.md); P0 PASSED
- **Completed capabilities:** FastAPI core; SQLite case persistence; DuckDB engine; Vite/React shell; P0 verification harness; CSV dataset attachment; deterministic dataset profiling; read-only SQL analysis runs with persisted results; findings with evidence chain; validation via rerun; parquet + xlsx ingest; deep profiling; **read-only Python execution with persisted results (P2-ANALYSIS-008); chart images rendered and persisted from run results (P2-ANALYSIS-009);
case management - rename, duplicate, delete (P2-CASE-010);
AI planning with structured output (P2-AI-011); case export as a self-contained
JSON package with import round trip (P2-CASE-012)**
- **Active task:** P5-RELEASE-005 DONE - release automation. A `v<x.y.z>` tag
  now builds and publishes a versioned macOS app from CI: the version is read
  from server/pyproject.toml and a tag that disagrees with it fails before any
  build (so a stale version file can never publish a build whose label lies
  about what it contains); the server suite runs; the sidecar is built and
  smoked (health plus the packaged-log assertions); the .app is built with the
  version stamped from the pyproject via `tauri build --config` - one source of
  truth, with tauri.conf.json patched at build time instead of four files kept in
  sync by hand; ditto-zipped with its architecture in the name; checksummed; and
  published as a flagged pre-release whose generated notes state it is unsigned,
  how to open it past Gatekeeper, and that the published build is Intel.
  UNSIGNED was the user's explicit call - the job needs no secret beyond the
  default GITHUB_TOKEN with contents:write, and signing slots in between the
  build and the upload when the Developer ID exists. Before it: P5-CI-004, the
  CI floor; P5-RELIABILITY-003, the 500 envelope; P5-OBSERVE-002,
  observability.
- **Known issues:** none. CI runs green on GitHub's own runners after five
  local-state bugs it exposed were fixed (see ai/HANDOFF.md, "What the first
  CI runs caught").
- **Test status:** server 256 passed (211 + 16 error semantics + 2 validation
  determinism + 6 large-dataset + 21 observability); web 17 passed (CaseList 5, CaseCreation 3,
  CaseWorkspace 9);
  desktop shell 7 Rust tests (5 unit + 2 e2e, `cd desktop/src-tauri && cargo test [--features e2e]`);
  P2 and P3 gates PASS
- **Next task:** the last P5 checklist item is macOS signing + notarization,
  formally deferred by DEC-004 and **blocked on an external dependency only you
  can provision** - a $99 Apple Developer ID. The release job already has the
  slot: signing goes between the build and the upload, and the `--prerelease`
  flag is what to revisit once a build is notarized. Not agent work until the ID
  exists. Everything else unblocked is smaller: an arm64 release lane (a second
  runner and sidecar triple, unverifiable on this x86_64 machine except by CI
  itself), a "Reveal logs" menu item in the desktop shell calling `GET /logs`,
  and showing the request id's full value somewhere copyable.
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
| P5-CI-004 CI floor (Ventura) | DONE |
| P5-RELEASE-005 Release automation | DONE |
