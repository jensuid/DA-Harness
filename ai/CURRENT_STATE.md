**Phase:** P8 Analytical Contract - COMPLETE (10 of 10 delivered: the case's
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
question refinement, the decision view, the measurement layer and the
requirement-traceability matrix. The full gap analysis is `docs/PRD & UX Conformance Evaluation.md`.

- **Active task:** **FIX-UPDATES-009 DONE** — W-005 (walk-test finding): menu
  "Check for Updates..." melakukan check tapi hanya `eprintln!` ke stderr; tiga
  status yang core bedakan (available / current / unknown) tidak pernah sampai
  ke window. Di repo privat feed selalu 404, jadi item ini selalu diam dan
  terlihat mati. Delivery ditambahkan, bukan menggantikan: log line masih
  tetap ditulis, dan jawaban juga sampai ke window. Shell adalah satu-satunya
  host dengan menu bar, dan `tauri-plugin-dialog` di Tauri 2 adalah plugin
  yang di-fetch dari network (app offline setelah install), jadi native dialog
  tidak bisa dipakai tanpa melanggar DEC-001 — jadi delivery-nya adalah
  surface bundle sendiri: shell mengevaluasi script di webview yang sudah
  dipegangnya, posting `CustomEvent('dah-notice')` yang detail-nya adalah JSON
  body core sendiri (tidak direword shell — unreachable feed tetap
  "could not tell", bukan silent "up to date", persis kebohongan yang
  P6-UPDATE-005 cegah). `web/src/shell.ts` `describeUpdate` mirror
  `update_summary` di Rust. Satu hal yang tes tangkap dan diperbaiki: body
  yang bukan JSON tidak bisa ditanam di script (eval akan throw
  `SyntaxError` dan item diam untuk kedua kalinya), jadi `notice_script`
  memvalidasi body dan fallback ke body yang dibangun dari parsed answer —
  jalur yang sama untuk transport yang tidak menyimpan body sama sekali.
  723 server (tak berubah), web 163 (+16), Rust 25 (+6), tsc bersih, build
  ok, e2e, golden 21/21, refine AT-04, measure 9/9, trace 48/48.
  Selanjutnya: **FIX-VERSION-010 (W-001)** —
  `server/app/updates.py` `current_version` baca metadata stale (0.1.0) dari
  editable install sebelum pyproject di sisi source; urutannya jadi: stamp >
  pyproject > metadata. Lalu FIX-PLAN-003 / FIX-CHART-004 / FIX-PYTHON-005,
  lalu **P9 redesign UI/UX** (npm, light theme, tailwind + shadcn +
  framer-motion + recharts untuk layar; SVG/PNG server tetap untuk export;
  4 fase F1-F4 hijau tiap fase).
  Sebelumnya: FIX-PROFILE-008 (W-008) DONE - membuka case POST `/profile`
  untuk tiap dataset di setiap mount (StrictMode double render = 2 write),
  sehingga profile yang sudah ada direcompute-ditulis ulang, dan shell
  diam-diam menyelesaikan langkah yang rail namakan milik analyst; mount
  sekarang GET via `getProfile` di `web/src/api.ts`, POST jadi control di
  panel Data. 723 server, 147 web (+4).
  Sebelumnya: FIX-REFINE-007 (W-009) DONE - panel refinement sudah punya
  "Why these changes" diklik dan tidak muncul apa-apa. Widget disclosure
  bukan primitive yang tepat untuk jawaban atas pertanyaan panelnya sendiri,
  jadi diganti blok yang selalu terlihat: `<h4>Why these changes</h4>`,
  paragraf rationale, daftar grounds; tetap dirender setelah accept.
  `.rationale` di `web/src/index.css` memakai left rule + ground yang sama
  dengan proposal, dan `.panel h4` baru (belum ada panel pakai h4).
  723 server (tak berubah), 143 web (+3), tsc bersih, build ok, e2e, golden,
  refine AT-04, measure 9/9, trace 48/48.
  Sebelumnya: FIX-TIMEOUT-006 (W-014) DONE - satu
  `LLM_TIMEOUT_SECONDS` (`DAH_LLM_TIMEOUT_SECONDS`, default 120) di
  `server/app/timeouts.py` dipakai semua 6 call site; fallback diumumkan
  lewat vocabulary `source` baru — `SOURCE_DETERMINISTIC_FALLBACK` +
  `source_sentence` di tiap modul, dan `web/src/sourceLabel.ts` di 7 panel
  (interpret, draft, chat, plan, generate-code, agent proposal, refinement).
  723 server (+24), 140 web (+2), build ok, golden 21/21, e2e, refine
  AT-04, measure 9/9, trace 48/48; v0.3.3 dirilis membawanya.
  Sebelumnya: FIX-EVIDENCE-002 (W-015) DONE - regex `_numbers_in`
  (`server/app/evaluator.py`) `-?\d[\d,]*\.?\d*` memotong token "2026-07"
  menjadi `2026` dan `-7`; keduanya absen dari `_allowed_numbers`, jadi
  verdict `insufficient_evidence` pada HARD check — setiap analisis
  time-series `YYYY-MM` gagal validasi. Sekarang run-regex + accept step
  yang membaca karakter di kedua sisi: digit / huruf / hyphen di tepi =
  bagian token lebih panjang, minus hanya tanda saat memulai.
  `_allowed_numbers` juga mendapat panjang kolom sendiri (bentuk "N
  grouped value(s)"). 699 server, 138 web, golden 21/21, e2e, refine
  AT-04, measure 9/9, trace 48/48.
  Sebelumnya: WALK-E2E-001 (walk-test end-to-end) SELESAI - 19 temuan
  (8 MAJOR, 8 MINOR, 3 OBS) di `walktest/FINDINGS.md`, laporan
  `walktest/REPORT.md`, state mesin live `walktest/HANDOFF.md`; hasilnya
  jadi post-phase fix, satu commit per temuan.
  Sebelum itu: FIX-VERSION-001 DONE - the packaged core reports its own
  version. Since v0.2.0 a bundled core answered `current: unknown` at
  `/updates/latest`, because neither the installed distribution's metadata
  nor `pyproject.toml` survives a one-file PyInstaller bundle, and
  PyInstaller ships no stdlib `importlib.metadata` hook. `dah-core.spec`
  now reads the version from pyproject with tomllib and stamps
  `dah-build-version.txt` into the bundle root, where `current_version`
  finds it through `sys._MEIPASS` - ahead of installed metadata, which goes
  stale when a version is bumped without reinstalling. A version the spec
  cannot read aborts the build, and both packaged-core smokes now assert
  the number, which is what makes the recurrence fail a build instead of
  hiding for four releases. Verified against the binary `build_sidecar.sh`
  produces: `current: 0.3.2`.
  Before it: P8-TRACE-010, P8-MEASURE-009, P8-DECISION-008, P8-REFINE-007,
  P8-SHELL-006, P8-GOLDEN-005, P8-CAUSAL-004, P8-VALID-003, P8-QUALITY-002,
  P8-CONTEXT-001, the v0.2.0 release.

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
  proves the exact Intel triple a local build produces. Restoring that needs a
  self-hosted Intel runner.
- **Test status:** server 723 passed (unchanged by this fix, which is
  web-only). The web suite is 163 (+16 for FIX-UPDATES-009 - the three
  statuses the update check distinguishes each reach the window, the layer is
  inert until one arrives, a stashed pre-mount notice is read once, and the
  vocabulary is the core's own). Desktop shell 25 Rust tests; P2, P3 and P4 gates
  PASS; **v0.2.0, v0.3.0, v0.3.1, v0.3.2 and v0.3.3
  released** (tags `v0.2.0` on `ec819fc`, `v0.3.0` on `ab56541`, `v0.3.1` on
  `19cefc1`, `v0.3.2` on `2ff1bca`, `v0.3.3` on `30db6e9`).
- **e2e:** all 28 real-server steps PASS; the golden suite and the refinement
  runner green, and the measurement layer 9/9 - the reports the matrix cites as
  its measured evidence, regenerated on the current tree.

- **Next task:** **FIX-UPDATES-009 (W-005)** - the Check for Updates menu item
  performs a check and prints the result to stderr, and nothing reports it to
  the user: three statuses the core distinguishes (up to date, an update
  available, the feed unreachable) never reach the window. The delivery is
  added, not substituted - the log line the handler already writes still
  writes. `desktop/src-tauri/src/main.rs:48-60`, plus desktop tests per
  status. Then FIX-VERSION-010 (W-001, `server/app/updates.py`'s resolution
  order - the source's pyproject ahead of the stale installed metadata, the
  stamp still first). The carried follow-ups that remain in `ai/TASKS.md` are
  the DMG bundler, the icon proportion (52%, chosen blind), one fragile web
  test layout, and two environmental items (signing deferred by DEC-006, CI
  billing suspended). P8 is complete (10 of 10) and
  **v0.3.0, v0.3.1, v0.3.2 and v0.3.3 are released** (tags `v0.3.0` on `ab56541`,
  `v0.3.1` on `19cefc1`, `v0.3.2` on `2ff1bca`, `v0.3.3` on `30db6e9`), 686 server tests passing on the
  tag. Both were built locally from
  the same steps `release.yml` runs - CI's billing is still suspended - with the
  packaged core proven on an isolated store and the ditto zip plus its sha256
  published as flagged pre-releases. v0.3.1 re-masks the app icon to the
  standard macOS squircle: the icon had been a full-bleed 1024 square with 60px
  corners, so it rendered as a tile rather than a native Ventura icon. The
  artwork is unchanged inside the mask (verified numerically - zero RGB pixels
  changed inside it, zero opaque pixels left outside), and `icon.icns` was
  regenerated through `iconutil` with every standard size.
  One defect the packaging surfaced, present in v0.2.0 and v0.3.0 too and not
  fixed here: the packaged core answers `current: unknown` at
  `/updates/latest`, because neither the distribution's metadata nor
  `pyproject.toml` is reachable inside the PyInstaller bundle. The update
  check therefore cannot compare versions until the bundle is taught to carry
  one. The DMG also bundles only when the local `create-dmg` happens to be the
  tool Tauri's bundler expects; the published artifact is the zip, which is
  what the workflow ships.
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
