# DAH - Current State

 - **Phase:** P5 Production Grade - COMPLETE. P6 Post-Launch Evolution - COMPLETE: all 5 entry-checklist items. P7 Product Modes is IN PROGRESS (1 of 4, with four web surfaces delivered): EVALUATE mode is DONE in the core and in the shell, the agent has a surface, a case can be renamed, duplicated and deleted from the list, and templates are reachable from the shell. The web-shell gap is item 2 and is partly closed; cross-case memory, EDA, the evidence graph and case history still have endpoints and no UI. P4 Production Candidate was COMPLETE (all 5 checklist items: P4 Production Candidate was COMPLETE (all 5 checklist items:
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
any past release opens, upgrades and keeps its rows (P6-MIGRATE-004);
and an update check that tells an installed app a newer build exists - or
says honestly that it could not tell (P6-UPDATE-005)**
- **Active task:** P7-SHELL-005 DONE - templates in the web shell. The four
  template endpoints (promote, list, start a case, retire) answered only
  through the API. A workspace now carries a **Save as a template** panel -
  the name is optional and defaults to the case's question - and the case-list
  screen carries a **Templates** section below the list, because templates are
  not case children and outlive the case they came from. Each row shows the
  name, the question and dataset label it seeds, and a shape summary (how many
  proposals, how many findings and their validation verdicts); a shapeless
  template says so rather than showing zeroes. **Start a case from this**
  creates and opens the seeded case, and **Retire** removes the template in one
  click - it carries no data of its own, and the core degrades a case that
  loses its template to normal derivation, so nothing is lost the way it is
  when a case is deleted.
  Wiring the DELETE surfaced a bug older than this task: the shared client
  helper parsed every successful body as JSON, and the core answers 204 with an
  empty body for each of the shell's DELETEs, so the write landed and the
  client then threw "Unexpected end of JSON input" and reported a success as a
  failure. The case delete P7-SHELL-004 shipped was broken this way - its test
  mocked the client, so the path never ran for real. The helper now returns
  nothing for an empty body.
  Before it: P7-SHELL-004 (case management), P7-SHELL-003 (the agent surface),
  P7-SHELL-002 (EVALUATE's surface), P7-EVAL-001 (EVALUATE's core), P6 CLOSED. The three
  everyday operations on the front door answered only through the API; the list
  rendered a row whose only affordance was opening it. Each row now keeps
  opening the case as its primary action and gains **Rename** (inline, with
  Save and Cancel - a correction never needs a second screen), **Duplicate**
  and **Delete**. Delete asks twice because the core's deletion is final and
  takes the case's on-disk directory: the first click arms the row, the second
  is labelled with the case's own question, and the armed state is per row so
  confirming one case never endangers another.
  Before it: P7-SHELL-003 (the agent surface), P7-SHELL-002 (EVALUATE's
  surface), P7-EVAL-001 (EVALUATE's core), P6 CLOSED.
- **Known issues:** CI's runner is `macos-latest`, not the Ventura/Intel pin
  P5-CI-004 intended - GitHub retired the macos-13 pool, so the label hangs
  forever (probed empirically; see DEC-005). The Ventura floor stays the
  documented minimum but is no longer enforced by CI, and a green run no longer
  proves the exact Intel triple a local build produces. Restoring that needs a
  self-hosted Intel runner.
- **Test status:** server 358 passed (336 + 22 evaluate); web 50 passed
  (CaseList 10, CaseCreation 3, CaseWorkspace 24, Templates 8, api 6 - the
  workspace gained the promote panel, the list screen gained the templates
  section, and the client learned to answer an empty 204); desktop shell 22 Rust tests
  (`cd desktop/src-tauri && cargo test [--features e2e]`, 19 unit + 3 e2e);
  P2, P3 and P4 gates PASS (P4: all 18 journey steps, all 10 exit criteria);
  first release v0.1.0 published from tag and checksum-verified.
- **Next task:** the rest of the web-shell gap (P7 item 2). EVALUATE, the agent,
  case management and templates have surfaces; these still do not: cross-case
  memory, EDA (`/eda`), the evidence graph (`/evidence-graph`), and case
  history. Each
  is a panel over an existing contract - no new endpoints. After item 2:
  **LEARN** mode, a guided Why -> What -> How -> Validate walk (mostly
  sequencing over P3-FLOW-004), then multi-agent workflows, which only make
  sense after EVALUATE - that is how an agent's own output gets audited.
  Deferred, not dropped: signing (DEC-006, the slot is in `release.yml`), cloud
  sync, team collaboration, warehouse connectors, enterprise governance. None
  pays for itself at a user count of one.
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
- Audit submitted work (EVALUATE mode): `POST /cases/{id}/datasets/{id}/evaluate`
  with `{code, claim, kind?: "sql"|"python"}` - the code and the claim it was
  offered to support, judged on nine axes (question, data, quality, method,
  calculation, evidence, claim, visualization, limitations), each a
  pass / concern / fail verdict with a sentence. The artifact runs under the
  same read-only gate, row cap and sandbox as any other run, is stored as a
  run, and the evaluation beside it; audits at `GET .../evaluations` newest
  first. A non-read-only artifact is a 400 before anything executes; a
  read-only artifact that fails at run time is a Calculation *finding*, not
  a 400, because the work is not the user's to fix.
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
- Check for a newer build: `GET /updates/latest` (read-only, GET-only,
  unauthenticated; answers `current`, `available` with the tag and the release
  page, or `unknown` with a reason - a private repository answers `unknown`,
  never a silent `current`)
- Chart from a run: `POST /cases/{id}/runs/{id}/charts` with `{"kind": "bar|line", "x": ..., "y": ..., "series": ...}`; image at `GET /cases/{id}/charts/{id}/image`
- Rename: `PATCH /cases/{id}` with `{question?, dataset?}`; duplicate: `POST /cases/{id}/duplicate`;
  delete: `DELETE /cases/{id}` (removes the case row, all children, and its on-disk data)

## P7 progress

| Task | Status |
|------|--------|
| P7-EVAL-001 EVALUATE mode | DONE |
| P7-SHELL-002 EVALUATE in the web shell | DONE |
| P7-SHELL-003 the agent in the web shell | DONE |
| P7-SHELL-004 rename, duplicate, delete a case | DONE |
| P7-SHELL-005 templates in the web shell | DONE |

## P6 progress

| Task | Status |
|------|--------|
| P6-MEMORY-001 cross-case recall | DONE |
| P6-AGENT-002 agentic analysis | DONE |
| P6-TEMPLATE-003 templates carry the analytical shape | DONE |
| P6-MIGRATE-004 versioned migration path | DONE |
| P6-UPDATE-005 update check for the packaged app | DONE |

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
