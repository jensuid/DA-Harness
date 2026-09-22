**Phase:** P8 Analytical Contract - IN PROGRESS (4 of 10 delivered: the case's
context object, quality beyond missingness, and the PRD's nine validation
dimensions). P7 Product Modes is COMPLETE - every checklist
item that builds something shipped, including the manual walkthrough and the
CORS fix, and the store's schema is at v11. P6, P5, P4, P3, P2, P1 and P0 are
all COMPLETE (see the phase table below). P8 closes the PRD's Level 1 breadth
gaps and makes "done" measurable: quality detection beyond missingness (2 of 7
defect classes today), validation from 3 checks to the PRD's 9 dimensions, the
causal-language guard, the analytical golden suite, the orientation spine,
question refinement, the decision view, and the measurement layer. The full gap
analysis is `docs/PRD & UX Conformance Evaluation.md`.

- **Active task:** P8-CAUSAL-004 DONE - the causal-language guard. Until this
  task the causality check raised a soft concern: a finding that said "spend
  drives signups" over six correlating rows could still be reported `supported`
  once the other eight dimensions were clean, and AT-18's zero-conversion
  clause ("0 cases convert an unsupported association into a validated causal
  finding") was not held. New `server/app/causality.py` makes the guard a gate:
  causality is now the fourth hard dimension, so an unsupported causal claim
  yields `insufficient_evidence`. Three judgements: an unhedged causal verb
  over an observational comparison is unsupported; a hedge ("may drive") or a
  negation ("does not cause") is the author naming the limit and passes; an
  intervention the case's context records *and the SQL compares across* earns
  causation, naming the intervention it read. The branch that matters: an
  intervention merely mentioned but never compared across still fails, because
  mentioning is not using. The 50-case corpus lives in the repository as data
  and the measurement computes AT-18's three numbers on every run - 100%
  detection, 100% discrimination, 0 conversions, against thresholds of 95%,
  95% and 0. The corpus found two bugs the eyeball missed: normalisation strips
  the slash so "a/b test" arrived as "a b test" and the intervention pattern
  missed it, and the negation window needed 5 words, not 3, to read "no
  evidence that ... caused". One limitation is recorded in the module rather
  than hidden: a causal word used as a noun ("the causes column") fires,
  because word-boundary matching cannot tell a noun from a verb.
  Before it: P8-VALID-003 (nine validation dimensions), P8-QUALITY-002
  (quality beyond missingness), P8-CONTEXT-001, the v0.2.0 release.

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
- **Test status:** server 468 passed (16 for the guard: the corpus's three
  AT-18 thresholds computed and asserted, one test per detector path - hedging,
  negation, intervention-used-vs-mentioned, word boundaries - the verdict's new
  gate through validate_finding, and a hedged finding that can still be
  `supported`; the 16 pre-existing validation tests gained the new `context`
  argument, and the concern-vs-failure test was rephrased to a non-causal
  concern, since a causal phrase now reaches `insufficient_evidence`)
  (16 quality; 21 context; 4 cors; 4 csv)
  (336 + 22 evaluate + 9 learn + 13 multi-agent + 4 cors + 4 csv + 21 context
  + 26 quality + 16 validation + 16 causality); web 86 passed (1 for the
  guard's refusal rendering: a guarded finding shows "the verdict refuses this
  finding" with the sentence to fix, distinguishable at a glance from a soft
  concern); desktop shell 22 Rust tests; P2, P3 and P4 gates PASS;
  **v0.2.0 released** (tag `v0.2.0` on `ec819fc`).
- **e2e:** all 25 real-server steps PASS.

- **Next task:** P8-GOLDEN-005 - the analytical golden suite with reference
  values (AT-40) and the workflow-completion rate (AT-01). This is what turns
  the trust machinery into measured numbers: the causal corpus from
  P8-CAUSAL-004 can fold into it, and it measures the 95% detection rate AT-17
  names and the 95%/5% AT-08 names, which the two tasks before it shipped
  checks for but could not measure. After it: P8-SHELL-006 (the orientation
  spine, AT-33/34/35) and P8-REFINE-007 (question refinement, AT-04, which
  edits the context object P8-CONTEXT-001 built).
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
