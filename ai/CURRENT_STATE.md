# DAH - Current State

 - **Phase:** P5 Production Grade - COMPLETE (all deliverables; signing retired indefinitely by DEC-006 - DAH is single-user, not blocked). P6 Post-Launch Evolution is IN PROGRESS, with P6-MEMORY-001 (cross-case recall), P6-AGENT-002 (agentic analysis), P6-TEMPLATE-003 (templates that carry the analytical shape) and P6-MIGRATE-004 (versioned migration path) all DONE. P4 Production Candidate was COMPLETE (all 5 checklist items:
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
JSON package with import round trip (P2-CASE-012);
**agentic analysis - the loop drives itself over those endpoints, one
human-approved write at a time (P6-AGENT-002);
case templates that carry the analytical shape of a finished case - its plan,
its proposals and how its findings validated - not just its question
(P6-TEMPLATE-003);
a versioned, forward-only migration path for the store, so a database from
any past release opens, upgrades and keeps its rows (P6-MIGRATE-004)**
- **Active task:** P6-MIGRATE-004 DONE - a versioned migration path. The store had
  grown by seven ad-hoc `_ensure_column` additions across P2-P6, each guarded
  and correct, with no version recorded anywhere in the file - so no code could
  answer "is this store current?", only probe for each column and hope. Now the
  version lives in SQLite's `user_version` (in the file header, readable before
  the schema exists), an ordered named chain replays the seven historical
  additions one transaction each (change + audit row + stamp together, so a
  crash mid-chain resumes at the next open), a store newer than the build is
  refused rather than silently downgraded, and `GET /schema-version` reports the
  state. A store created by this build is stamped current with an empty audit
  trail, because nothing was applied to it. Before it: P6-TEMPLATE-003
  (analytical-shape templates) DONE, P6-AGENT-002 (agentic analysis) DONE,
  P6-MEMORY-001 (cross-case recall) DONE, P5 CLOSED.
  answers `GET /logs` with a path, but a path in a JSON body is a terminal
  answer, and the shell exists because this user does not have a terminal. New
  `desktop/src-tauri/src/logs.rs` is the bridge: it asks the core, then hands
  the answer to Finder with `open -R` (macOS-native, no new dependency -
  serde_json is the only addition and it is already in the tree through tauri).
  Everything degrades to a sentence: a core still booting, hung, or older than
  the endpoint is "logging is off", and a body that is not the expected shape
  cannot panic a menu. main.rs gets a real macOS menu bar - the app menu keeps
  About and Cmd+Q, which setting any custom menu takes away, Edit keeps the
  text editing a data tool needs, and DAH > Reveal DAH Logs is the one item DAH
  adds. 5 new Rust tests (12 total, was 7), including an e2e test that starts
  the real dev core and asserts the reported log is under the data dir the
  shell pointed it at. Before it: P5-RELEASE-005, release automation.
- **Known issues:** CI's runner is `macos-latest`, not the Ventura/Intel pin
  P5-CI-004 intended - GitHub retired the macos-13 pool, so the label hangs
  forever (probed empirically; see DEC-005). The Ventura floor stays the
  documented minimum but is no longer enforced by CI, and a green run no longer
  proves the exact Intel triple a local build produces. Restoring that needs a
  self-hosted Intel runner.
- **Test status:** server 315 passed (302 + 13 migrations); web 21 passed
  (CaseList 5, CaseCreation 3, CaseWorkspace 9); desktop shell 12 Rust tests
  (`cd desktop/src-tauri && cargo test [--features e2e]`, 9 unit + 3 e2e);
  P2, P3 and P4 gates PASS (P4: all 18 journey steps, all 10 exit criteria);
  first release v0.1.0 published from tag and checksum-verified.
- **Next task:** the Tauri update flow (ROADMAP item 5) - releases now publish a
  build per tag, but an installed app has no way to know. `tauri-plugin-updater`
  against the GitHub releases feed, with a version compare and a download-and-
  replace that respects the unsigned-app first-launch step. It is the last item
  on the P6 entry checklist; after P6 closes, the unbuilt product work is
  EVALUATE mode (audit existing SQL/notebook/dashboard work - the spec's third
  mode, and the one DAH uniquely owns) and LEARN mode. P6-MIGRATE-004 (the
  versioned migration path) is DONE. Before it, P6-TEMPLATE-003, P6-AGENT-002
  and P6-MEMORY-001 were DONE. The last P5 item was macOS signing +
  notarization, retired indefinitely by DEC-006 - DAH is single-user, so the
  right-click > Open cost is paid once per machine by the one person who uses
  the app. The release job keeps the slot between the build and the upload if
  that changes. Not blocked, and not agent work.
- **Blockers:** none.

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
- Run the agent: `POST /cases/{id}/agent` (derive and record the next step -
  profile, plan, analyze, interpret, accept, chart, validate; idempotent, so a
  pending step is returned unchanged); state at `GET .../agent` (read-only:
  nothing is proposed on a read); `POST .../agent/approve {step_id}` runs the
  step's write through the endpoint that owns it and proposes the next one;
  `POST .../agent/reject {step_id, reason?}` records the analyst's no and
  writes nothing. An id that is not the case's current pending step is a 409.
- Check the store's schema: `GET /schema-version` (read-only; reports the
  recorded version, whether it is current for this build, and the migrations
  that were applied - the answer to "is my data safe with this build")
- Chart from a run: `POST /cases/{id}/runs/{id}/charts` with `{"kind": "bar|line", "x": ..., "y": ..., "series": ...}`; image at `GET /cases/{id}/charts/{id}/image`
- Rename: `PATCH /cases/{id}` with `{question?, dataset?}`; duplicate: `POST /cases/{id}/duplicate`;
  delete: `DELETE /cases/{id}` (removes the case row, all children, and its on-disk data)

## P6 progress

| Task | Status |
|------|--------|
| P6-MEMORY-001 cross-case recall | DONE |
| P6-AGENT-002 agentic analysis | DONE |
| P6-TEMPLATE-003 templates carry the analytical shape | DONE |
| P6-MIGRATE-004 versioned migration path | DONE |

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
| P5-UX-006 Reveal logs menu | DONE |
| P5-CI-FIX-007 CI repair + first real release | DONE |
