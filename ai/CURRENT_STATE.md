**Phase:** P8 Analytical Contract - IN PROGRESS (8 of 10 delivered: the case's
context object, quality beyond missingness, the PRD's nine validation
dimensions, the causal guard, the analytical golden suite that measures them,
the orientation spine that presents them, question refinement, and the decision
view that closes the loop). P7 Product Modes is COMPLETE - every checklist
item that builds something shipped, including the manual walkthrough and the
CORS fix, and the store's schema is at v13. P6, P5, P4, P3, P2, P1 and P0 are
all COMPLETE (see the phase table below). P8 closes the PRD's Level 1 breadth
gaps and makes "done" measurable: quality detection beyond missingness (2 of 7
defect classes today), validation from 3 checks to the PRD's 9 dimensions, the
causal-language guard, the analytical golden suite, the orientation spine,
question refinement, the decision view, and the measurement layer. The full gap
analysis is `docs/PRD & UX Conformance Evaluation.md`.

- **Active task:** P8-REFINE-007 DONE - question refinement (AT-04). The
  vague question is the one thing carried verbatim into every plan, query and
  finding after it; this task is the surface where its sharpening is proposed.
  Two engines behind one interface, as in every other assistant: a
  deterministic refiner that appends grounding the profiler measured (the
  measure, the split, the window, the comparison a direction word leaves
  unstated) and an LLM refiner gated by `validate_refinement` before the
  analyst sees it - original echoed verbatim, subject terms surviving, every
  cited and quoted column real, every figure measured, a rationale present.
  The refined question is the original plus clauses, never a replacement, so
  preserve and relevant are structural; the suite measures them anyway, because
  a structural guarantee is one renamed variable away from a regression. The
  engine declines rather than invents - no profile, nothing numeric or
  temporal, no subject terms, or an already-answerable question - and the
  decline is recorded, not answered as an empty proposal.
  Measured over 50 cases and 6 datasets against a real server: preserve 100%,
  relevant 100%, 0 silent overwrites, 0 fabrications. The three paths are the
  only three - accept and edit are the sole writes to the case's question,
  keep-original writes nothing but the no, a decided proposal is a 409 - and
  the original rides on the proposal row, so it survives the accept that
  replaced it, the export round trip and the duplicate, and it shows in the
  timeline as two new event kinds.
  Before it: P8-SHELL-006 (the orientation spine), P8-GOLDEN-005, P8-CAUSAL-004,
  P8-VALID-003, P8-QUALITY-002, P8-CONTEXT-001, the v0.2.0 release.

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
  proves the exact Intel triple a local build produces. Restoring that needs a
  self-hosted Intel runner.
- **Test status:** server 548 passed (30 for this task: the view's assembly -
  guidance before a finding, a supported finding with no uncertainty, a
  partially supported one carrying its failing checks verbatim from the
  verdict, a refused one as an open item naming the hard dimension that failed,
  the purpose, oldest-first ordering, loop-closed agreeing with /progress, the
  verdict readable without re-validating, reading changing nothing across
  repeated reads, the duplicate, the delete, the implications' write contract
  and its three 400 shapes, the two new timeline events, the export's two new
  sections and their round trip, an older package degrading rather than
  failing, the AT-43 measurement over two findings, and the v12 -> v13
  upgrade); web 116 passed (10 for this task: the panel in the work zone, the
  question and purpose, a validated finding with its caveat and no score
  anywhere in the panel, the failing checks as the uncertainty, the open claims
  and their reasons, the guidance before a closed loop, a failed read
  reported, the implications written and confirmed saved, a failed save
  reported with the server's own sentence, and the export downloaded as a
  named file). Before it, the server suite's own additions this phase: 6 golden (the ten
  shapes' coverage, the suite's own size floor, the two-way fixture audit, the
  deliberately-wrong expectation the audit catches, the comparator's tolerance,
  and the one slow measurement over a real server; +3 in test_analysis.py for
  the date/timestamp/numeric serialisation the suite surfaced), 16 causality
  (the corpus's three AT-18 thresholds computed and asserted, one test per
  detector path - hedging, negation, intervention-used-vs-mentioned, word
  boundaries - the verdict's new gate through validate_finding, and a hedged
  finding that can still be `supported`), 16 validation, 26 quality, 21
  context. Desktop shell 22 Rust tests; P2, P3 and P4 gates PASS;
  **v0.2.0 released** (tag `v0.2.0` on `ec819fc`).
- **e2e:** all 28 real-server steps PASS (the journey now closes the loop with
  a chart, reads the decision view, writes the implications, and asserts the
  export carries the verdicts and the decision through the round trip).

- **Next task:** P8-MEASURE-009 - the measurement layer (AT-27..30/32/37/38/
  45/46): coverage, perf, a11y, deps and the data-size envelope. Mechanical now
  that two measured suites exist to borrow the pattern from - the golden suite
  and the AT-04 refinement runner. After it: P8-TRACE-010 (the traceability
  matrix), last because it traces what 1-9 delivered.
  The release is done: **v0.2.0** is tagged on `ec819fc`. GitHub Actions is
  still refusing to start any job with "recent account payments have failed";
  that is an account billing problem (Settings > Billing & plans), not a code
  problem, and until it is fixed no push is verified by CI.

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
