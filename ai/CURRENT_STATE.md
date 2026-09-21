# DAH - Current State

 - **Phase:** P5 Production Grade - COMPLETE. P6 Post-Launch Evolution - COMPLETE: all 5 entry-checklist items. P7 Product Modes is IN PROGRESS (1 of 4, with eight web surfaces delivered): EVALUATE mode is DONE in the core and in the shell, the agent has a surface, a case can be renamed, duplicated and deleted from the list, templates are reachable from the shell, a cited previous case is something the analyst can follow, the "what should I look at first" steps are one panel away, a case's evidence graph is a review surface, and its history is one too. The web-shell gap - item 2 - is CLOSED: every capability with an endpoint has a surface. LEARN mode - item 3 - is DONE in the core (P7-LEARN-001) and in the shell (P7-SHELL-010): the guided Why -> What -> How -> Validate walk is a read-side projection over the workflow stages, and a Learn this case panel walks it beside the workflow it explains. The P7 checklist has EVALUATE, LEARN and multi-agent workflows delivered - the last as a core (P7-AGENT-001): a case carries agents in two roles, analyst and reviewer, each with its own pending step and audit trail behind the one approval gate both share. The reviewer's shell surface is built too (P7-SHELL-011), so every P7 checklist item that builds something is delivered; the release is what remains. P4 Production Candidate was COMPLETE (all 5 checklist items: P4 Production Candidate was COMPLETE (all 5 checklist items:
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
- **Active task:** P7-WALK-001 DONE - the shipped shell, used by hand. The
  automated artifacts drive contracts: the core through TestClient, the shell
  through jsdom. Neither renders, so a walkthrough is the only check that a
  panel shows the analyst the number behind it. This one drove the real shell
  one keyboard action at a time - case created, file attached, the agent's
  plan approved, its SQL run, interpreted, the draft accepted, validated, the
  reviewer's audit approved, the chart rendered, the case asked a question, a
  template promoted and a case started from it - reading the rendered DOM at
  every step.
  The loop closes honestly: validation answers `partially_supported` (the null
  revenue trips the missing-data check while reproducibility passes) and the
  LEARN panel says the trust loop ran, not that the answer is right.
  One bug fixed: the reviewer's settled-step summary summed over a SET of
  verdict strings, so a nine-axis audit reported at most one pass and one
  concern ("9 axes, 1 pass, 1 concern, 0 fail" for 7 pass / 2 concern). Every
  audit the shell has ever shown understated its own pass count. Counted per
  axis now; the two audit tests derive their tallies from the recorded
  evaluation.
  Five findings are recorded, not fixed: evaluations do not travel with an
  exported case (exporter.py never reads them); a stale agent step can be
  approved after its write happened out of band, producing a duplicate
  finding; the plan's contents, a run's result rows and the profile's
  per-column null count are all persisted and none rendered; a draft's
  grounds run together with its count ("2..32 row(s)"); and the chat and
  generate-code inputs are adjacent near-identical single-line boxes.
  Before it: P7-E2E-001 (real-server e2e), P7-SHELL-011 (the reviewer's
  surface), P7-AGENT-001 (multi-agent core), P7-SHELL-010 (LEARN's surface),
  P7-LEARN-001 (LEARN's core), P7-SHELL-009..002, P7-EVAL-001, P6 CLOSED.
  Every verification artifact in the repo drives the app in-process through
  Starlette's TestClient, which is fast and is what caught every regression
  fixed here - but it never binds a port, never parses a real multipart upload
  and never runs uvicorn's lifecycle. `verification/e2e/verify_e2e.py` is the
  complement: a fresh uvicorn server on a free port with an isolated data dir,
  driven over real HTTP. One case is built by hand end to end and audited by
  the reviewer agent; a second case is driven entirely by the analyst agent,
  one approved write at a time, to a closed loop; then the export round trip.
  The LLM env vars are *emptied* for the subprocess rather than unset, because
  `app.main` loads `server/.env` itself on a plain uvicorn start and
  `load_dotenv` never overrides a variable already set - so the run is
  deterministic and needs no network. 25 steps, three consecutive green runs,
  CI runs it after the gates.
  Before it: P7-SHELL-011 (the reviewer's surface), P7-AGENT-001
  (multi-agent core), P7-SHELL-010 (LEARN's surface), P7-LEARN-001 (LEARN's
  core), P7-SHELL-009 (case history), P7-SHELL-008 (the evidence graph),
  P7-SHELL-007 (EDA), P7-SHELL-006 (cross-case memory), P7-SHELL-005
  (templates), P7-SHELL-004 (case management), P7-SHELL-003 (the agent
  surface), P7-SHELL-002 (EVALUATE's surface), P7-EVAL-001 (EVALUATE's core),
  P6 CLOSED.

- **Known issues:** CI's runner is `macos-latest`, not the Ventura/Intel pin
  P5-CI-004 intended - GitHub retired the macos-13 pool, so the label hangs
  forever (probed empirically; see DEC-005). The Ventura floor stays the
  documented minimum but is no longer enforced by CI, and a green run no longer
  proves the exact Intel triple a local build produces. Restoring that needs a
  self-hosted Intel runner.
- **Test status:** server 380 passed (the 2 multi-agent audit tests now assert the verdict tallies) (336 + 22 evaluate + 9 learn + 13 multi-agent); web 78 passed
  (CaseList 10, CaseCreation 3, CaseWorkspace 52, Templates 8, api 6 - the
  workspace gained the reviewer panel, on top of the LEARN panel, the evidence
  graph, EDA, the cited-case buttons, the promote panel, the templates section
  and the empty-204 fix); desktop shell 22 Rust tests
  (`cd desktop/src-tauri && cargo test [--features e2e]`, 19 unit + 3 e2e);
  P2, P3 and P4 gates PASS (P4: all 18 journey steps, all 10 exit criteria);
  first release v0.1.0 published from tag and checksum-verified.
- **Next task:** the release. Every P7 checklist item that builds something is
  delivered and now verified against a real server as well as in-process -
  EVALUATE, the web-shell gap, LEARN and multi-agent workflows, the last in
  core (P7-AGENT-001) and in the shell (P7-SHELL-011). Sixteen tasks have
  landed since v0.1.0, so `0.2.0` is the honest next label: tag `v0.2.0`, which
  must match server/pyproject.toml, and the pipeline builds, smokes and
  publishes an unsigned .app as a flagged pre-release with its checksum.
  Deferred, not dropped: signing (DEC-006, the slot is in `release.yml`), cloud
  sync, team collaboration, warehouse connectors, enterprise governance.

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
- Walk a case as the LEARN ladder: `GET /cases/{id}/learn` (read-only; the four
  phases - why, what, how, validate - over the workflow's own stages, each with
  what it teaches, the question a learner answers, and the action that
  advances); the shell walks it as the **Learn this case** panel
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
- Run the agents: `GET /cases/{id}/agents/{role}` (state, read-only - nothing is proposed
  on a read; `role` is `analyst` or `reviewer`); `POST /cases/{id}/agents/{role}` derives and
  records that role's next step, idempotent so a pending step is returned unchanged;
  `POST .../approve {step_id}` runs the step's write through the endpoint that owns it (for
  the reviewer, an `evaluate` step auditing the finding's own run and claim) and proposes the
  next one; `POST .../reject {step_id, reason?}` records the analyst's no and writes nothing.
  The analyst role is the legacy `/agent` family exactly. An approval that is not that role's
  live step is a 409 naming that role's pending step; an unknown role is a 400 naming the
  roles that exist.
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
| P7-SHELL-006 cross-case memory, actionable | DONE |
| P7-SHELL-007 EDA in the web shell | DONE |
| P7-SHELL-008 the evidence graph in the shell | DONE |
| P7-SHELL-009 case history in the shell | DONE |
| P7-LEARN-001 LEARN mode, the guided walk (core) | DONE |
| P7-SHELL-010 LEARN mode in the web shell | DONE |
| P7-AGENT-001 multi-agent workflows (roles, core) | DONE |
| P7-SHELL-011 the multi-agent surface (the reviewer) | DONE |
| P7-E2E-001 the whole app against a real server | DONE |
| P7-WALK-001 the shipped shell, used by hand | DONE |

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
- End-to-end against a REAL server: `server/.venv/bin/python
  verification/e2e/verify_e2e.py` (starts uvicorn on a free port with an
  isolated data dir, drives the whole journey over HTTP - the case built
  by hand, the reviewer's audit, an agent-driven second case, the export
  round trip; ~3s, deterministic and offline, 25 asserted steps)

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
