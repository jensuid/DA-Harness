# DAH - Current State

 - **Phase:** P5 Production Grade - COMPLETE. P6 Post-Launch Evolution - COMPLETE: all 5 entry-checklist items. P7 Product Modes is IN PROGRESS (1 of 4, with eight web surfaces delivered): EVALUATE mode is DONE in the core and in the shell, the agent has a surface, a case can be renamed, duplicated and deleted from the list, templates are reachable from the shell, a cited previous case is something the analyst can follow, the "what should I look at first" steps are one panel away, a case's evidence graph is a review surface, and its history is one too. The web-shell gap - item 2 - is CLOSED: every capability with an endpoint has a surface. LEARN mode - item 3 - is DONE in the core (P7-LEARN-001) and in the shell (P7-SHELL-010): the guided Why -> What -> How -> Validate walk is a read-side projection over the workflow stages, and a Learn this case panel walks it beside the workflow it explains. The P7 checklist has EVALUATE and LEARN delivered; multi-agent workflows and the release are what remain. P4 Production Candidate was COMPLETE (all 5 checklist items: P4 Production Candidate was COMPLETE (all 5 checklist items:
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
- **Active task:** P7-SHELL-010 DONE - LEARN mode in the web shell.
  P7-LEARN-001 shipped the guided walk as an endpoint; nothing in the shell
  reached it, so LEARN existed as a contract and not as a product. A **Learn
  this case panel** now sits beside the workflow panel it explains: the workflow
  says where the case stands, this says why each step exists and what a learner
  should be able to answer before leaving it. Each phase renders its name and
  status, what it is for, the question that tests understanding, and the stages
  it covers as the actions that close them, with the workflow's own hints. It
  loads read-only with the workspace, names the one phase and action to work on
  now, and a completed walk says the trust loop closed - the loop ran, not that
  the answer is right.
  Before it: P7-LEARN-001 (LEARN's core), P7-SHELL-009 (case history),
  P7-SHELL-008 (the evidence graph), P7-SHELL-007 (EDA), P7-SHELL-006
  (cross-case memory), P7-SHELL-005 (templates), P7-SHELL-004 (case
  management), P7-SHELL-003 (the agent surface), P7-SHELL-002 (EVALUATE's
  surface), P7-EVAL-001 (EVALUATE's core), P6 CLOSED. The spec's third product mode is a sequencing and teaching layer
  over the workflow P3-FLOW-004 already ships: `server/app/learn.py` (new)
  regroups the seven ANALYZE stages into the spec's four phases - why
  (question, data), what (profile, plan), how (analyze, evidence), validate
  (validate) - every stage in exactly one phase, and each phase carrying what
  it *teaches* and the question a learner should be able to answer before
  leaving it. It is a read-side projection like the evidence graph and the
  case history: nothing stored, nothing executed, and deleting an artifact
  moves the walk back as honestly as adding one. At most one phase is
  current, and `done` says only that the trust loop closed - a finding was
  validated - never that the answer is right. Endpoint: `GET
  /cases/{id}/learn` (read-only, 404 for an unknown case).
  Next: P7-SHELL-010, the walk as a panel - the surface this core still
  lacks. Before it: P7-SHELL-009 (case history), P7-SHELL-008 (the evidence
  graph), P7-SHELL-007 (EDA), P7-SHELL-006 (cross-case memory),
  P7-SHELL-005 (templates), P7-SHELL-004 (case management),
  P7-SHELL-003 (the agent surface), P7-SHELL-002 (EVALUATE's surface),
  P7-EVAL-001 (EVALUATE's core), P6 CLOSED.
  P3-CASE-007 could answer "what did I do here, and when?" and nothing in the
  shell showed it, so the shape of a case - how it grew, and in what order -
  was reconstructible only by opening every panel and comparing timestamps.
  A **Case history panel** now sits at the end of the workspace, after the
  evidence panel, because the two are the read-only review surfaces: the graph
  says what backs each claim, the timeline says what happened in the case at
  all. It loads with the workspace and writes nothing; each event is one line
  in the order the core sends them, with the kind as a phrase ("dataset
  attached", not "dataset_attached"), the artifact's own label and its detail,
  and the counts as one summary sentence naming only the kinds the case has.
  A 404 is guidance rather than a second alert - the workspace loads its own
  case on mount, so an unknown case is already reported at the top of the page
  - and a young case renders its single event rather than an empty list.
  Before it: P7-SHELL-008 (the evidence graph), P7-SHELL-007 (EDA),
  P7-SHELL-006 (cross-case memory), P7-SHELL-005 (templates),
  P7-SHELL-004 (case management), P7-SHELL-003 (the agent surface),
  P7-SHELL-002 (EVALUATE's surface), P7-EVAL-001 (EVALUATE's core), P6 CLOSED. P3-EVIDENCE-006 could answer "what backs each claim, and does every
  one of them reach the data?" and nothing in the shell showed it, so a case's
  evidence was inspectable only one finding at a time and a claim with no
  source was invisible. An **Evidence panel** now sits after the findings panel
  and loads read-only with the workspace. Each trace renders the finding's
  statement with its validation status and the chain back to the data as chips;
  each edge renders as a sentence ("chart 'Revenue by region' is rendered from
  the sql run"); and a node with no edge is still listed under its kind, so the
  graph never says the case has less than it does. A finding whose run is gone
  is flagged as **a claim with no source** rather than smoothed over, and its
  broken edge says "an artifact no longer in the case" rather than showing a
  uuid. The endpoint's 400 for an artifact-free case is muted guidance, not an
  alert - a young case is not a failed review.
  Before it: P7-SHELL-007 (EDA), P7-SHELL-006 (cross-case memory),
  P7-SHELL-005 (templates),
  P7-SHELL-004 (case management), P7-SHELL-003 (the agent surface),
  P7-SHELL-002 (EVALUATE's surface), P7-EVAL-001 (EVALUATE's core), P6 CLOSED. P6-MEMORY-001 let a chat answer cite what a previous case found, and
  the shell rendered that citation as an inert chip carrying a uuid - the one
  thing recall exists for, going to read what was concluded last time, was a
  click that did nothing. The Chat panel now resolves each `case:<id>` ground
  to the prior case's own question (one lookup per cited case, shared across
  every turn) and renders it as a **button that opens that case as its own
  workspace**. A lookup that fails - the cited case was deleted, or the core
  could not answer - records the id as absent and degrades to a chip saying
  the case is no longer available, so the answer stays readable and the
  missing case is not refetched on every render. Grounds of other kinds
  (columns, datasets, runs, findings) render exactly as before.
  Before it: P7-SHELL-005 (templates), P7-SHELL-004 (case management),
  P7-SHELL-003 (the agent surface), P7-SHELL-002 (EVALUATE's surface),
  P7-EVAL-001 (EVALUATE's core), P6 CLOSED. The four
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
- **Test status:** server 367 passed (336 + 22 evaluate + 9 learn); web 73 passed
  (CaseList 10, CaseCreation 3, CaseWorkspace 47, Templates 8, api 6 - the
  workspace gained the LEARN panel, on top of the history panel, the evidence
  graph, EDA, the cited-case buttons, the promote panel, the templates section
  and the empty-204 fix); desktop shell 22 Rust tests
  (`cd desktop/src-tauri && cargo test [--features e2e]`, 19 unit + 3 e2e);
  P2, P3 and P4 gates PASS (P4: all 18 journey steps, all 10 exit criteria);
  first release v0.1.0 published from tag and checksum-verified.
- **Next task:** LEARN mode is delivered in core and shell (P7-LEARN-001,
  P7-SHELL-010), and with EVALUATE before it, the P7 checklist's product modes
  are both built. What remains on it: **multi-agent workflows** - the spec's
  ladder above the single driver that exists (P6-AGENT-002) - which only make
  sense after EVALUATE because that is how an agent's own output gets audited,
  and the release itself (thirteen tasks have landed since v0.1.0, so `0.2.0`
  is the honest next label when one is wanted). Deferred, not dropped: signing
  (DEC-006, the slot is in `release.yml`), cloud sync, team collaboration,
  warehouse connectors, enterprise governance.
  Deferred, not dropped: signing (DEC-006, the slot is in `release.yml`), cloud
  sync, team collaboration, warehouse connectors, enterprise governance.
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
