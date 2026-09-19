# DAH - Current State

 - **Phase:** P4 Production Candidate - IN PROGRESS (P4-VERIFY-001 and
  P4-RELIABILITY-002 done). P3 V1 is COMPLETE: all 10 entry-checklist items,
  223 tests, and a P3 gate of its own (`verification/p3/verify_p3.py` -> PASS).
- **Global roadmap status:** ai/ROADMAP.md (phase tracker - current stage, phase table, next-phase entry checklist)
- **Milestone status:** P1 Vertical Slice PASSED (verification/p1/REPORT.md); P0 PASSED
- **Completed capabilities:** FastAPI core; SQLite case persistence; DuckDB engine; Vite/React shell; P0 verification harness; CSV dataset attachment; deterministic dataset profiling; read-only SQL analysis runs with persisted results; findings with evidence chain; validation via rerun; parquet + xlsx ingest; deep profiling; **read-only Python execution with persisted results (P2-ANALYSIS-008); chart images rendered and persisted from run results (P2-ANALYSIS-009);
case management - rename, duplicate, delete (P2-CASE-010);
AI planning with structured output (P2-AI-011); case export as a self-contained
JSON package with import round trip (P2-CASE-012)**
- **Active task:** P4-RELIABILITY-002 DONE - error semantics. The five
  engine endpoints (single/multi SQL run, Python run, EDA, chart render) ended
  in `except Exception as error: raise 400`, which did two jobs at once: it was
  the only thing keeping a user's SQL syntax error a 400 (DuckDB raises
  `duckdb.Error`, which is *not* a `ValueError`), and it flattened every real
  server fault into a 400 that blamed the analyst. Now each site catches the
  input-error families only - `ValueError` plus `duckdb.Error`, gathered once in
  `app/errors.py` - and a harness fault propagates to an honest 500 that uvicorn
  logs. The five LLM fallbacks stay broad because degradation is the contract,
  but each now logs the reason, so a fallback caused by our own bug surfaces
  instead of vanishing into `source=deterministic`.
  Before it: P4-VERIFY-001, the P3 gate script - 23 journey steps, 15 exit
  criteria, all PASS. Every entry-checklist item is DONE: P3-SEC-001, P3-CHART-002, P3-DATA-003, P3-FLOW-004, P3-ANALYSIS-005, P3-EVIDENCE-006, P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010 and the four contextual AI slices P3-AI-011..014. P4's entry checklist is sketched in ai/ROADMAP.md as a proposal for the user to reorder.
- **Known issues:** none
- **Test status:** server 223 passed (211 + 12 error semantics); web 2 passed;
  desktop shell 7 Rust tests (5 unit + 2 e2e, `cd desktop/src-tauri && cargo test [--features e2e]`);
  P2 and P3 gates PASS
- **Next task:** continue the P4 entry checklist - the assistant surfaces in
  the React shell (the widest gap between what DAH can do and what it shows),
  large-dataset behaviour, and the desktop shell lifecycle under CI plus the
  signing decision. A small follow-up surfaced by this task: a 500 answers with
  Starlette's plain-text "Internal Server Error", not JSON - the shell will
  want a JSON envelope; fold that into the UX work.
  Carried: nothing agent-shaped remains. The packaged app is unsigned
  (macOS gatekeeps the first launch; signing is P5)
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

## How to run (P4)

- P3 verification: `server/.venv/bin/python verification/p3/verify_p3.py`
  (in-process, ~3-4 min; the last step re-runs the suite)
