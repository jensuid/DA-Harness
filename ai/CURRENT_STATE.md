**Phase:** P9 UI/UX Redesign - COMPLETE (4 of 4: the foundation, the surfaces,
the motion, the on-screen chart). P8, P7, P6, P5, P4, P3, P2, P1 and P0 are all
COMPLETE (see the phase table below). Every phase the roadmap and the
conformance evaluation asked for is delivered; no phase is open.

- **Active task:** **W2X-002 + W2X-005 DONE - the first thing the app says.**
  The second walk-test's two "what do I do first" findings, both about the
  app's own answering behaviour rather than its capability. W2X-002:
  submitting "New Analysis Case" with a blank field was total silence - no
  request, no alert, nothing changed - because only HTML5 native validation
  stood behind the submit, and its message is invisible headlessly and
  undiscoverable for a first-time analyst. The form now names the fields it
  still needs in `role="alert"` live regions, marks each `aria-invalid`,
  clears a message once the field is filled, and never leaves the page; both
  labels carry `*` and the dataset's says what belongs there. W2X-005: the
  rail's "Next:" showed the raw `POST /cases/…/datasets` with a
  `{dataset_id}` placeholder unfilled - an answer to a developer's question,
  that read as a bug, on the surface an analyst reads first. The rail now
  shows the action and a "Go to the Data panel" button that scrollIntoViews
  the panel that performs it, with the path behind a "developer info"
  disclosure; the core half fills the placeholder with the first attached
  dataset and drops it when none exists yet, so the quoted path is a path
  that runs instead of a literal that 404s. Gates: web 257 (246 + 11), tsc
  clean, test_workflow 16 (14 + 2). Browser check against a live core: the
  empty submit fires zero fetches and answers two `role="alert"`, the rail's
  button scrolls the right anchor, and the disclosed endpoint is a real
  dataset id.
  **STATUS: COMMITTED, all gates green.** The one gate that had held the
  commit - measure AT-38 - turned out not to be the circular dependency the
  handoff hypothesised. The suite's real failure inside the line counter was
  `test_refine.py` seeing a `deterministic fallback` label, because
  `test_llm_config.py`'s PUT endpoint had left `DAH_LLM_API_KEY` in
  `os.environ` and the refiner made a real 401 call before falling back;
  monkeypatch restores only the variables a test declared. Fixed with an
  autouse teardown in `test_llm_config.py` (and a matching one in
  `test_env_config.py`), pinned by a regression test.
  Sebelumnya: W2X-006 + W2X-007 (the analysis editor), W2X-012 phase B (the
  settings surface), W2X-012 phase A (the status surface), WALK-UX-002
  (recorded),
  v0.3.4, P9-F4-001 (the on-screen chart), P9-F3-001 (the motion layer),
  P9-F2-002 (the restyle), P9-F2-001 (the walk-test's last three
  findings), P9-F1-001 (the redesign's foundation), FIX-PYTHON-005,
  FIX-CHART-004, FIX-VERSION-010, FIX-UPDATES-009, FIX-PROFILE-008,
  FIX-REFINE-007, FIX-TIMEOUT-006, FIX-PLAN-003, FIX-EVIDENCE-002,
  WALK-E2E-001 — the first walk's nineteen findings are all resolved; the
  second walk's twelve others are still open.

- **Done before that:** P8-TRACE-010 - the requirement-traceability matrix
  (AT-48). The PRD's section 59 control artifact is code: 48 rows, one per
  acceptance threshold, each carrying the PRD header it quotes, the UX
  surface, the implementation, the tests, the threshold in the PRD's own words
  and where the measured number lives. `verification/trace/verify_trace.py`
  resolves every cell against the repository as it stands - a missing file, a
  renamed symbol, a deleted test, a moved UX section, an uncommitted report or
  a red one is a named failure, so the matrix cannot quietly disagree with
  what it traces. The requirement set is checked against the PRD's own
  headers: 48/48 traced, no requirement untraced, no phantom. Fifteen rows are
  P0 by the PRD's section 53 and each names the category it guards; AT-48's
  thresholds compute from the resolved rows, 15/15 (100%) and 33/33 against
  >= 95%. The report is at verification/trace/REPORT.md.
  One gap the resolution surfaced and fixed: the AST check for a module-level
  name missed annotated constants, so a cell citing `INPUT_ERROR_TYPES` read
  as undefined until the check learned `AnnAssign`.
  Before it: P8-MEASURE-009, P8-DECISION-008, P8-REFINE-007, P8-SHELL-006,
  P8-GOLDEN-005, P8-CAUSAL-004, P8-VALID-003, P8-QUALITY-002, P8-CONTEXT-001,
  the v0.2.0 release.

  Three findings the measurement made, all fixed with their own tests:
  profiling re-parsed the CSV once per bounded lookup (12.5s over the 5s
  target) and now materialises once into a temp table (1.7s, no measured
  result changed); the counter's denominator counted function-signature lines
  the interpreter never reports, so coverage read lower than it was; and the
  guards `python_exec` enforces in the child are now tested in the process
  that measures them, which is what lifted the evidence group to its target.
  Before it: P8-DECISION-008, P8-REFINE-007, P8-SHELL-006, P8-GOLDEN-005,
  P8-CAUSAL-004, P8-VALID-003, P8-QUALITY-002, P8-CONTEXT-001, the v0.2.0
  release.

- **Known issues:** CI's billing is suspended: every workflow (Release, and both CI suites) is
  rejected at start with "recent account payments have failed or your spending
  limit needs to be increased", so nothing pushed since c73118c has run in CI.
  The v0.2.0 artifacts were therefore built and published locally from the same
  steps release.yml runs, and the server suite was run by hand on the tag. Fix
  at GitHub Settings > Billing & plans; no code change is involved. Separately,
 CI's runner is `macos-latest`, not the Ventura/Intel pin
  P5-CI-004 intended - GitHub retired the macos-13 pool, so the label hangs
  forever (probed empirically; see DEC-005). The Ventura floor stays the
  documented minimum but is no longer enforced by CI, and a green run no longer
  proves the exact Intel triple a local build produces. The `arch-mismatch` CI
  job (P9-F4) now emits a `::warning` on every run recording the gap, and the
  release artifact is built locally from an Intel machine with
  `desktop/bundle_dmg.sh`, so the shipped triple is what the developer's
  machine produces. Restoring an enforced Intel lane needs a self-hosted
  runner.
- **Test status:** server 773 passed (772 + 1: the AT-38 regression pin, see
  below). The web suite is 257 (+11 for W2X-002 and W2X-005, the
  first-thing-the-app-says fixes: four for the form's inline required-field
  answers and seven for the rail's action-plus-button guidance).
  The one server test that is not new this task is the AT-38 fix itself:
  `test_llm_config.py`'s PUT endpoint writes `os.environ` (the "no restart"
  property, correct in production), and monkeypatch restores only the
  variables a test declared - so `DAH_LLM_API_KEY` outlived the suite and
  `test_refine.py` read a `deterministic fallback` label after a real 401.
  Restored in an autouse teardown and pinned by
  `test_the_suite_leaves_no_configured_llm_behind`.
  Desktop shell 30 Rust tests (25 + 4 for W2X-012 phase B's settings
  surface); P2, P3 and P4 gates
  PASS; **v0.2.0, v0.3.0, v0.3.1, v0.3.2, v0.3.3 and v0.3.4 released** (tags
  `v0.2.0` on `ec819fc`, `v0.3.0` on `ab56541`, `v0.3.1` on `19cefc1`,
  `v0.3.2` on `2ff1bca`, `v0.3.3` on `30db6e9`, `v0.3.4` on `d8bec6a`).
- **e2e:** all 28 real-server steps PASS; the golden suite and the refinement
  runner green, and the measurement layer 9/9 - the reports the matrix cites as
  its measured evidence, regenerated on the current tree.

- **Next task:** **P9 is now COMPLETE** - all four phases green: F1 the
  foundation, F2 the surfaces, F3 the motion, F4 the chart surface and the
  re-walk. Every dependency F1 installed is used, every walk-test finding is
  closed, and 48/48 requirements still trace. What follows is whatever the
  re-walk found - and it found one thing this phase fixed as it stood (the
  missing `format` field), so the phase closes with the shell's own surface
  verified in a browser rather than only in the suite. The carried
  follow-ups that remain in `ai/TASKS.md` are the DMG bundler, the icon
  proportion (52%, chosen blind), one fragile web test layout, and two
  environmental items (signing deferred by DEC-006, CI billing suspended).


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
- Read the LLM's state (W2X-012): `GET /llm/status` (read-only; answers
  `configured` with the provider env var's *name*, the model and base URL -
  never any part of a key value - so the shell can say what the analyst is
  actually getting rather than letting a deterministic fallback read as an
  LLM answer)
- Export: `GET /cases/{id}/export` (self-contained JSON package); `POST /cases/import`
  reconstructs it with fresh IDs
- Plan: `POST /cases/{id}/datasets/{id}/plan` (structured plan from question + profile; deterministic by default, LLM when DAH_LLM_API_KEY is set, source field records which); latest at `GET .../plan`, history at `GET .../plans`
- Refine the question (AT-04): `POST /cases/{id}/refine` proposes a
  sharpening grounded in the profile's measured columns and ranges
  (deterministic by default, LLM when DAH_LLM_API_KEY is set, `source` records
  which); idempotent while a proposal is pending and the question unmoved.
  Read-only: latest at `GET .../refine`, history at `GET .../refinements`.
  `POST .../refine/{proposal}/accept` makes the refined question the case's;
  `POST .../refine/{proposal}/reject` keeps the original and writes nothing but
  the no; `POST .../refine/{proposal}/edit {question}` makes the analyst's own
  wording the case's. Accept and edit are the only paths that move the
  question; the original rides on the proposal row and survives both.
- Read the case's decision (UX 46, AT-43): `GET /cases/{id}/decision`
  (read-only, deterministic, executes nothing - the validated findings with
  their residual uncertainty, the claims still open, and the analyst's
  implications). Write the implications - the view's only write: `PUT
  /cases/{id}/decision` with `{"implications": [...]}`; a malformed entry is a
  400 naming the first one to fix, an empty list clears them.
- Read the verdict validation computed: `GET /cases/{id}/findings/{fid}/validation`
  (read-only; 404 when the finding was never validated). The verdict is
  persisted by `POST .../validate`, so a reopened case shows the same nine
  checks without re-validating.
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
- The analytical golden suite: `server/.venv/bin/python
  verification/golden/verify_golden.py` (starts a real server on a free port
  with an isolated data dir and the LLM vars empty; measures AT-40's
  reference-match rate and AT-01's workflow-completion rate over 21 scripted
  runs and 3 datasets, writing verification/golden/REPORT.md; exit 0 only when
  both thresholds hold; ~60s cold)
- AT-04's refinement suite: `server/.venv/bin/python
  verification/refine/verify_refine.py` (starts a real server on a free port
  with an isolated data dir and the LLM vars empty; drives 50 cases over 6
  datasets through accept / edit / keep / pending, and measures the four
  thresholds - preserve >= 95%, relevant >= 90%, 0 silent overwrites, 0
  fabricated data references - writing verification/refine/REPORT.md; exit 0
  only when all four hold; ~40s cold)
- The measurement layer (AT-27..30/32/37/38/45/46): `server/.venv/bin/python
  verification/measure/verify_measure.py` (starts a real core on a free port
  for the timings, runs the suite itself under a line counter for coverage,
  scans the production inventory against OSV, and runs the web suite for the
  shell's own targets; writes verification/measure/REPORT.md and exits 0 only
  when every measured threshold holds; ~7 min. Each module is runnable on its
  own: `python -m verification.measure.{coverage,deps,perf}`). The three
  browser-side targets are asserted in the web suite rather than measured
  here, because jsdom is not a browser - the report says where the number
  lives.
- The requirement-traceability matrix (AT-48): `server/.venv/bin/python
  verification/trace/verify_trace.py` (reads the PRD, the UX document and every
  file the matrix names, resolves every cell of all 48 rows and writes
  verification/trace/REPORT.md; exits 0 only when every row traces and AT-48's
  two thresholds hold - 100% of the release-blocking requirements and >= 95% of
  the rest; ~2s, deterministic, offline and read-only)
- End-to-end against a REAL server: `server/.venv/bin/python
  verification/e2e/verify_e2e.py` (starts uvicorn on a free port with an
  isolated data dir, drives the whole journey over HTTP - the case built
  by hand, the reviewer's audit, an agent-driven second case, the decision
  view and its implications, the export round trip; ~3s, deterministic and
  offline, 28 asserted steps)

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
