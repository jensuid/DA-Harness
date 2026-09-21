**Phase:** P8 Analytical Contract - IN PROGRESS (1 of 10 delivered: the case's
context object, P8-CONTEXT-001). P7 Product Modes is COMPLETE - every checklist
item that builds something shipped, including the manual walkthrough and the
CORS fix, and the store's schema is at v10. P6, P5, P4, P3, P2, P1 and P0 are
all COMPLETE (see the phase table below). P8 closes the PRD's Level 1 breadth
gaps and makes "done" measurable: quality detection beyond missingness (2 of 7
defect classes today), validation from 3 checks to the PRD's 9 dimensions, the
causal-language guard, the analytical golden suite, the orientation spine,
question refinement, the decision view, and the measurement layer. The full gap
analysis is `docs/PRD & UX Conformance Evaluation.md`.

- **Active task:** P8-CONTEXT-001 DONE - a case carries the analyst's stated
  intent, not just a question string. The PRD's AT-03 requires purpose,
  sub-questions and hypotheses to be captured, edited and reopened, and the UX
  architecture (section 13) treats context as a first-class object the AI
  reasons over; a case was `question + dataset` before it. A new `contexts`
  table (schema v10, migration guarded and resumable like every other) holds a
  purpose and three lists; GET answers an empty default rather than a 404 so the
  shell's form always renders, and PUT replaces the whole object so a retry
  after a failed save cannot merge two drafts. The planner reads it - the
  analyst's sub-questions and hypotheses outrank the ones the profile suggests,
  a stated purpose stands in for a thin objective - and the plan records a
  `context_basis` naming the fields it actually read, on both the deterministic
  and the LLM path. The assistant cites `context:purpose` and
  `context:hypotheses` when asked what the case is for. Export carries it in
  both directions, duplicate carries it, delete removes it.
  Before it: P7-CSV-002 (a stray trailing comma no longer collapses a file),
  P7-CORS-001 (the packaged app's webview could not reach its own core). The
  (a stray trailing comma, as a spreadsheet export or a hand-edit produces)
  no longer reads as one column of raw lines. read_csv_auto's delimiter guess
  dies on that row, so the profile answered
  `columns: ['order_id,quarter,region,revenue']` and described nothing, and
  the SQL an analyst wrote from those columns then failed on the same file.
  `_sniffed_reader_for` compares the sniffed width against the header's own
  comma count and re-sniffs with `ignore_errors=true` when sniffing collapsed
  - keeping every row and dropping only the stray field to a null, rather
  than null_padding's synthetic extra column. Both profiling and the run path
  go through it, so a file reads the same way everywhere, and the retry is
  earned by a collapse: a clean file keeps the strict reader, so a genuine
  conversion error is still an error and never a silent null.
  Before it: P7-CORS-001 (the packaged app's webview could not reach its own
  core), P7-WALK-001 (the shipped shell, used by hand). The
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
- **Test status:** server 409 passed (21 for the context object: persistence
  and reopen, the edit and the malformed-input 400s, the v9->v10 migration, the
  export round trip, the planner's basis recording and precedence, and three
  chat tests for the new citation kind) (4 for the shell's CORS; 4 for the
  stray-trailing-comma recovery - a CSV with a row wider than its header no
  longer collapses to one column, in the profile *and* in the SQL written
  from it; all 4 fail on the pre-fix code) (336 + 22 evaluate + 9 learn
  + 13 multi-agent + 4 cors + 4 csv + 21 context); web 82 passed (4 for the
  Context panel: render, save with precedence, remove without saving, a failed
  save that keeps the edit)
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
| P7-CORS-001 the packaged app could not reach its own core | DONE |
| P7-CSV-002 a stray trailing comma no longer collapses a file | DONE |

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
