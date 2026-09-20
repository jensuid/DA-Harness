# DAH - Handoff

## What was completed
- P7-EVAL-001 PASSED: EVALUATE mode, the spec's second product mode, and the
  largest capability DAH did not have. Until P7, every primitive served the
  analyst's *own* work - read-only execution, deep profiling, rerun validation,
  the evidence graph, the honesty budgets. This task turns those primitives on
  work that came from elsewhere, and that turn is the whole product difference:
  a user submits an artifact (its SQL or Python code) and the claim that code
  was offered to support, and DAH answers the nine questions the specification
  names, each against the data rather than against the claim's own confidence.
  Verdicts are pass / concern / fail - deliberately not a score, because a
  single number would imply a precision nine heterogenous axes do not have -
  and every verdict carries a sentence a reader can act on.

  Three pieces. `server/app/evaluator.py` is a pure module (like evidence.py
  and workflow.py) returning nine `AxisFinding`s; `POST .../evaluate` executes
  the artifact through the *existing* run engine - never a second code path, so
  the read-only gate, the row cap and the hard sandbox are the ones every other
  run answers to, and EVALUATE earns no privilege while untrusted code is the
  premise of the mode; and the `evaluations` table (migration 8) stores the
  artifact as a run and the audit beside it, so an audit is itself inspectable
  and reproducible - the standard every other artifact is held to.

  Four judgement calls the contract left open, each written into the code. A
  **non-read-only artifact is a 400 before anything executes** (a mutation is a
  request the store must never honour, not an artifact to audit), but a
  read-only artifact that **fails at run time is a Calculation finding, not a
  400** - the work came from elsewhere, it is not the user's to fix, and "this
  does not run" is the answer an auditor exists to give. An **unknown column is
  a Data fail, never a silent pass**: the first version of that check
  intersected the code's identifiers with the profile's columns, which drops
  every name the dataset lacks - the axis passed on exactly the case it exists
  to catch, and the fix reuses the generator's own notion of a column read. A
  **chart is not required**: the contract's baseline is a clean artifact
  passing all nine axes, and "no chart, and none needed" is a valid verdict -
  what *is* a fail is a chart whose axes are not the result's own columns, a
  check the previous `has_chart` boolean could not make because a boolean
  cannot be wrong. And a **single-row result is deterministic without an ORDER
  BY**, because one row has no row order to disagree about.

- P6-UPDATE-005 PASSED, and with it P6 closes: a new release tag reaches an
  installed app. The release pipeline publishes a build per tag, but the app
  had no way to learn that. `GET /updates/latest` answers one of three truths -
  `current`, `available` (with the tag, the release page and the notes), or
  `unknown` with a reason - and the shell's new **DAH > Check for Updates...**
  menu item opens the release page or shows that sentence. Everything degrades
  to a sentence, the way the reveal-logs menu does, and never panics on a body
  it does not recognise.
  What is deliberately *not* here is the self-replacing install, and the reason
  is two recorded facts rather than two gaps: the repository is private, so an
  unauthenticated feed request answers 404 (verified, not assumed), and the app
  is unsigned (DEC-006), so an update payload cannot be signature-verified.
  `tauri-plugin-updater` slots in when signing does, and the check it would
  consume is what this task built. The whole design turns on one distinction:
  "could not check" and "is up to date" are different statements, and only one
  of them is true - so every failure (404, 403, 503, a timeout, a non-JSON body,
  a body without a tag) is `unknown` with its own reason, never a silent
  `current`. Verified live against the real private repository: `unknown`,
  "the release feed is not reachable; the repository may be private".
- P6-MIGRATE-004 PASSED: a versioned, forward-only migration path for the store.
  The database had grown by seven ad-hoc `_ensure_column` additions across P2-P6
  - each guarded, each correct, and no version recorded anywhere in the file, so
  no code could answer "is this store current?" but only probe for each column
  and hope. That was tenable while the schema only ever gained nullable columns;
  it stopped being tenable the moment a task needed to rename, split or backfill
  anything. Now the version lives in SQLite's `user_version` (the file header,
  readable before any table exists and durable across a crash that leaves
  tables half-made), the seven historical additions are an ordered named chain
  applied one transaction at a time - the change, its audit row and its version
  stamp land together or none does, so a failure mid-chain leaves a consistent
  store that the next open resumes - and `GET /schema-version` reports the state
  so a user can ask whether their data is safe with the build they are running.
  Two deliberate behaviours: a store *newer* than the build is refused with both
  numbers named, never silently downgraded, and a store created by this build is
  stamped current with an empty audit trail, because the truth is that nothing
  was applied to it. SQLite itself set one constraint the implementation had to
  respect: a `NOT NULL` column cannot be added to a populated table without a
  default, so the historical migrations carry defaults that SCHEMA declares too -
  a test pins that a fresh store and an upgraded one are identical, not merely
  compatible, because "they agree by construction" is exactly the claim that
  silently stops being true when the next migration lands.
- P6-MIGRATE-004 PASSED: a versioned, forward-only migration path for the store.
  The database had grown by seven ad-hoc `_ensure_column` additions across P2-P6
  - each guarded, each correct, and no version recorded anywhere in the file, so
  no code could answer "is this store current?" but only probe for each column
  and hope. That was tenable while the schema only ever gained nullable columns;
  it stopped being tenable the moment a task needed to rename, split or backfill
  anything. Now the version lives in SQLite's `user_version` (the file header,
  readable before any table exists and durable across a crash that leaves
  tables half-made), the seven historical additions are an ordered named chain
  applied one transaction at a time - the change, its audit row and its version
  stamp land together or none does, so a failure mid-chain leaves a consistent
  store that the next open resumes - and `GET /schema-version` reports the state
  so a user can ask whether their data is safe with the build they are running.
  Two deliberate behaviours: a store *newer* than the build is refused with both
  numbers named, never silently downgraded, and a store created by this build is
  stamped current with an empty audit trail, because the truth is that nothing
  was applied to it. SQLite itself set one constraint the implementation had to
  respect: a `NOT NULL` column cannot be added to a populated table without a
  default, so the historical migrations carry defaults that SCHEMA declares too -
  a test pins that a fresh store and an upgraded one are identical, not merely
  compatible, because "they agree by construction" is exactly the claim that
  silently stops being true when the next migration lands.
- P6-TEMPLATE-003 PASSED: a template carries the analytical shape of a finished
  case, not just its question. The plan, the proposals and the finding outcomes
  were all already on disk, so promotion is a pure projection over them
  (`_capture_shape`), and a case started from the template inherits that shape
  as *proposals a human accepts* - the plan step offers the template's plan
  through the same `validate_plan`, and generate-code offers a template
  proposal only when every column it reads exists in the profiled dataset. Both
  record `source="template"` and both degrade to the deterministic path on any
  problem, so a shapeless, malformed or deleted template is never an error -
  it is the absence of a template, which the code already handled. No data,
  runs, findings or charts are copied; every write is still a POST the human
  makes, so the read-only gate, the row cap and the honesty budgets are all
  still in force for a templated case.
  Two bugs the new tests caught: `SOURCE_TEMPLATE` was referenced by two
  helpers whose definition never landed (a `NameError` at request time on a
  path no existing test walked), and hand-run cases' proposals carried
  `columns_used: []`, which made the column-existence check pass vacuously -
  the one failure it existed to prevent. A guard never fed the data it guards
  is not a guard.
- P6-AGENT-002 PASSED: a plan that executes itself, one approved write at a time.
  Every stage of the loop already had a validated endpoint; the agent is the
  driver over them, and it holds no privilege a hand-written call lacks. Its SQL
  passes the same read-only gate and row cap, its findings are created by the
  same POST, and its drafts and proposals come from the same stateless modules
  with the same validation. What it contributes is the sequence, the memory of
  what it already tried, and an audit row for every step. Nothing is written
  without an approval, and an approval id that is not the case's current pending
  step is a 409 rather than a second write.
- P5-UX-006 PASSED: a user can find the log without a terminal. The core answers
  `GET /logs` with a path, but a path in a JSON body is a terminal answer, and
  the shell exists precisely because this user does not have one open. New
  `desktop/src-tauri/src/logs.rs` is the bridge - `log_location` asks the core,
  `reveal_in_finder` hands the answer to Finder with `open -R` (macOS-native,
  no new dependency), and `reveal_core_logs` is the menu item's whole job.
  Everything degrades to a sentence rather than an error: a core still booting,
  hung, or older than the endpoint is `Disabled`, and a body that is not the
  expected shape is `Disabled` too, so a menu can never panic on a body it does
  not recognise. main.rs gains a real macOS menu bar - the app menu keeps About
  and Cmd+Q, which setting any custom menu otherwise takes away, Edit keeps the
  text editing a data tool needs, and **DAH > Reveal DAH Logs** is the one item
  DAH adds.
  Verified by hand, not only by test: the built app's menu bar was introspected
  with AppleScript (an earlier attempt ran a stale debug binary and showed a
  menu without the item - `cargo test` does not refresh the runnable
  `target/debug/dah-shell`, so an explicit `cargo build` is what makes a smoke
  honest), the item was clicked through AppleScript, and the shell's own log
  recorded `revealed the core's log at ~/Library/Application Support/
  com.jensuid.dah/logs/dah-core.log`. 5 new Rust tests, 12 total (was 7),
  including an e2e test that starts the real dev core and asserts the reported
  log is under the data dir the shell pointed it at and is a file that exists.

- P5-RELEASE-005 PASSED: a tag now produces a downloadable app. The packaging
  job in ci.yml proved the sidecar builds and serves on a clean machine, but
  its artifact was uploaded for one job and deleted a day later. Now
  `.github/workflows/release.yml` reads the version from server/pyproject.toml
  and FAILS if the tag does not match it, runs the server suite, builds and
  smokes the sidecar, builds the .app with the version stamped from the
  pyproject through `tauri build --config`, ditto-zips it with its architecture
  in the name, checksums it, generates notes stating the unsigned status and the
  Gatekeeper steps, and publishes a flagged pre-release with the zip and its
  sha256. UNSIGNED was the user's explicit call; signing slots in between the
  build and the upload when the Developer ID exists.

- P5-CI-004 PASSED:
## P1 vertical slice (verified)

```
Create Case -> Question -> Load CSV -> Profile -> SQL Analysis
-> Finding -> Evidence chain -> Validation (rerun) -> Save -> Reopen
```

## What the CI runs after the P4 gate caught (two test races)

Both were invisible locally - seven consecutive local runs passed before the
fix, which is the definition of passing by timing luck. CI failed twice, on a
*different* test each time, which is what pointed at interference rather than
a broken test.

1. **The two lifecycle tests raced for port 8123.** Both start a real core on
   the same fixed port and each asserts the port is its own afterwards (that is
   the orphan check). Cargo runs tests in parallel by default, so one won the
   bind and the other died on `[Errno 48] address already in use` - presenting
   as a 180s timeout that looked like a dead sidecar.
2. **The resolution tests shared `DAH_DEV_CORE`.** The override test sets that
   variable process-wide, resolves, and removes it. A concurrently-running
   resolution test observed it mid-flight and resolved to the virtualenv while
   a sidecar was present, so `release_resolution_uses_a_bundled_sidecar_when_present`
   panicked on an assertion about its own input.

The fix was `#[serial]` on all five tests, with a comment naming both races.
Serialization is right and a port is not: giving each test its own port would
have hidden the interference instead of removing it, and the tests exist to
assert exclusive use of the one port the app actually uses.

The general lesson, now stated twice in this handoff: **parallel test
interference presents as a flaky failure in whatever test happens to be
running alongside**. When a test fails intermittently and the failing test
changes between runs, suspect shared global state - a port, an env var, a
fixed temp path - before suspecting the code under test.

## What changed (P5-VERIFY-001)

- verification/p4/verify_p4.py (NEW): the gate, modelled on the P3 one. In-
  process TestClient, one journey, a step table and an exit-criteria table
  written to verification/p4/REPORT.md, exit 0 only when every step passes.
- Every dataset value is a closed function of the row index (revenue depends
  only on the region, so each region's sum is exactly rate x group size), so
  the expectations are known by construction rather than measured against a
  captured value that could drift.
- Hermeticity: the LLM credentials are scrubbed from the process and from the
  pytest subprocess, so no assistant step makes a live call. The one step that
  sets a dummy DAH_LLM_API_KEY does it to *break* the LLM on purpose and prove
  the fallback; `_BrokenLLM` raises without touching the network.
- The injected harness fault is observed through a second TestClient with
  `raise_server_exceptions=False` - the only way a 500 is visible in process -
  and the engine is restored in a `finally` so a failure cannot leak a broken
  function into later steps.
- .github/workflows/ci.yml: the server job runs the P4 gate alongside P2 and
  P3, and uploads its report with the others. A gate CI never runs is a gate
  that rots.
- One genuine bug in the gate itself, caught by its own first run: the journey
  never rendered a chart, so the workflow's `evidence` stage stayed open and
  the loop never closed. Not a code bug - the stage derives from artifacts and
  a chart is one of them. The gate now renders one.

## What the first CI runs caught (P4-CI-007, follow-up)

Five separate failures across five pushes, each a case of local state hiding a
gap that only a clean machine could see. All are fixed and the run is green;
this list is the reason the workflow was worth building, and it is the pattern
to expect whenever something "works on my machine":

1. **The gate scripts were invoked from the wrong directory.** They resolve
   the repo root from `__file__` and live at the repo root, but the server job
   runs with `working-directory: server`. `verification/p2/...` did not exist
   from there.
2. **The packaging job had no Rust toolchain.** `build_sidecar.sh` derives the
   target triple from `rustc -vV`, which macOS runners do not ship, so the
   triple came out empty and the sidecar would have landed under the wrong
   name.
3. **`@testing-library/jest-dom` was declared in the wrong package.json.**
   `setup-tests.ts` imports it, but it lived in the *root* package.json while
   the web job runs `npm ci` in `web/`. Locally the hoisted root node_modules
   resolved it; on the runner all three suites failed on the import.
4. **The shell could not compile at all.** `tauri::generate_context!()` embeds
   `web/dist-desktop` at compile time and `tauri-build` validates the
   `externalBin` resource - neither exists on a clean checkout. Two fixes: the
   desktop job builds the desktop web bundle, and it consumes the sidecar the
   packaging job builds (uploaded as an artifact) instead of each job building
   its own.
5. **The artifact transport dropped the executable bit.** The downloaded
   sidecar arrived without +x and `spawn()` failed with PermissionDenied. The
   workflow chmods it back rather than making the Rust test tolerant of a
   binary it could not run - that test's purpose is a real packaged sidecar.

The lesson carried forward: **anything that "works locally" but was never run
from a clean directory is suspect.** The stale egg-info, the hoisted
node_modules, the prebuilt dist-desktop and the local sidecar were all the same
bug in four costumes.

## What changed (P4-CI-007)

- .github/workflows/ci.yml (NEW): four jobs - `server` (uv venv from pyproject,
  pytest, P2 and P3 gates, reports uploaded), `web` (npm ci, npm test,
  npm run build - tsc -b runs first, so a type error the jsdom tests cannot see
  fails CI), `desktop` (the server venv at the exact path the resolver looks
  for, then `cargo test` and `cargo test --features e2e`), `packaging`
  (build_sidecar.sh plus a /health smoke against the built binary). Every
  command was validated by running it locally in the order the job runs it.
- server/pyproject.toml: two fixes found by validating the install path on a
  clean venv. `[tool.setuptools] packages = ["app"]` - flat-layout discovery
  saw `app` and `tests` as competing top-level packages and failed on a fresh
  checkout; a stale egg-info was masking it locally, which is exactly the kind
  of bug CI exists to catch. And a `packaging` extra declares PyInstaller,
  which was installed ad-hoc and was not reproducible.
- README.md (NEW): the layers and their test commands, the gates, and the
  unsigned-app first-launch workaround in plain language - DEC-004's
  consequence is that this is a documented user-facing behaviour, not an
  omission.
- ai/DECISIONS.md DEC-004: signing deferred to P5, with the reason, the
  alternatives considered (ad-hoc/self-signed, `xattr -cr` bypass) and why each
  is worse, and the consequences - chiefly that nothing in P4 may depend on the
  app being signed.
- ai/ROADMAP.md: P4 marked COMPLETE, the stage marker moved to P5, and a P5
  entry checklist proposed (signing first, then a P4 gate, observability, the
  carried 500 JSON envelope, release automation).

## What changed (P4-PERF-006)

- server/app/analysis.py: `profile_csv` reads the description via
  `SELECT * FROM <reader> LIMIT 0` instead of `SELECT *` + `fetchall()`. The
  per-column aggregate pass now leads with `COUNT(*) AS _total` and the row
  total is read from slot 0 (offset starts at 1), so the separate COUNT(*) scan
  is gone. `_duplicate_row_count(connection, path, total_rows)` takes the total
  it already has instead of rescanning for it.
- server/tests/test_large_datasets.py (NEW): 6 tests over a deterministic
  50k-row generated dataset whose stats are analytically known (id 1..N, region
  cycling through 5 values, quantity cycling 1..50, revenue = quantity * 2.5,
  one null every ten rows). Profile correctness at scale, the wide-table width
  slicing (40 columns), exact duplicate counts (500 groups x 4 repeats), the
  result cap truncating `SELECT *`, an aggregation summing every row, and an
  export/import round trip that re-profiles to the same row count.
- No API or output-shape change - the profile dict is identical, so nothing
  downstream (the planner, the generator, export) needed to move. The speedup
  is documented as benchmark numbers in ai/CURRENT_STATE.md so the next
  regression is measured against a number.

## What changed (P4-VALID-005)

- server/app/main.py: `_row_key(row)` (new) canonicalises one row as JSON so the
  sort key is type-aware and deterministic; `_reproduce_sql` now compares
  `sorted(rerun["rows"], key=_row_key) == sorted(stored, key=_row_key)`. Nothing
  else moved - the stored shape, the verdict vocabulary and the
  missing_data / evidence_integrity checks are untouched, and a query that no
  longer binds still records a failed reproducibility check rather than a 500.
- `_reproduce_python` was deliberately NOT changed: the Python tabulator is
  deterministic, and there a changed column order *is* a changed result, so the
  positional comparison stays correct.
- server/tests/test_validation.py: +2 tests.
  `test_validate_accepts_reordered_unordered_result` reverses the stored rows of
  a real GROUP BY run in SQLite and requires a `supported` verdict - this is the
  one verified to FAIL before the fix. `test_validate_unordered_groupby_is_stable_across_reruns`
  validates an ORDER BY-less GROUP BY 12 times and requires the verdict set to be
  exactly `{"supported"}`; repetition is the only honest way to pin it, since the
  order is not under the test's control. The pre-existing
  `test_validate_fails_when_result_drifts` (a substituted value no rerun can
  produce) is what proves the fix did not weaken the gate.
- ai/TASKS.md: the P4-VALID-005 contract, plus the P4-UX-004 table row that its
  commit had missed.

## What changed (P4-UX-004)

- web/src/CaseWorkspace.tsx: the workspace becomes the loop the core walks, one
  panel per step - attach + profile (file picker, then columns and nulls), a
  profile-scoped generate-code panel whose Run posts to the runs endpoint, the
  run list with Interpret and Draft-finding buttons, a draft rendered with its
  statement / interpretation / caveat / grounds and an Accept that posts to
  /findings, then a Validate that renders the verdict and its checks. Each
  assistant panel shows which engine spoke (source).
- web/src/api.ts: the remaining contracts - attach, profile, run SQL (single-
  and multi-dataset), generate-code, interpret, draft-finding, POST /findings,
  POST .../validate.
- web/src/index.css: panel and action styles for the new surfaces.
- web/src/CaseWorkspace.test.tsx: +9 tests (17 web total).
- No server change - every call is an existing endpoint, which is what keeps the
  propose / human-decides split structural rather than a UI flag.

## What changed (P4-UX-003)

- web/src/api.ts: rewritten as a typed client over the real contracts - GET
  /cases (with q), GET /cases/{id}, .../progress, .../datasets, .../runs,
  POST + GET .../chat. One shared request() throws ApiError carrying the status
  and a message parsed from the body only when the body is JSON.
- web/src/CaseList.tsx (NEW): the front door - list, search, open, or create.
  Exports messageOf(), the one place an error becomes readable text.
- web/src/CaseWorkspace.tsx (NEW): the question, the Workflow panel (stage,
  next action, per-stage completion), the Artifacts panel (datasets, runs), and
  the Chat panel with citation chips and an engine badge.
- web/src/CaseCreation.tsx: unchanged form, now navigates into the created
  case; takes onCreated/onCancel.
- web/src/App.tsx: state-based navigation (list | workspace | create) - no
  router, so the bundle gains no runtime dependency.
- web/src/index.css: panel, list, chip and stage styles.
- web/src/CaseList.test.tsx, CaseWorkspace.test.tsx (NEW), CaseCreation.test.tsx
  (+1 test).
- One real markup lesson, caught by the tests: React Testing Library's text
  matcher sees only an element's *direct* text nodes, so `Stage:
  <strong>analyze</strong>` could not be matched by any regex or function
  matcher. The sentences are now single text nodes - better for a screen
  reader and for translation too.
- No browser is registered with the computer-use surface on this machine, so
  the visual check is a data-path smoke: the exact calls the components make,
  run against the live core (create, list, search, progress, datasets, runs,
  chat round trip, 404 detail). The rendering is covered by vitest against the
  real response shapes, and the vite proxy was confirmed serving the bundle.

## What changed (P4-RELIABILITY-002)

- server/app/errors.py (NEW): the taxonomy in one place. `INPUT_ERROR_TYPES`
  is `(ValueError, duckdb.Error)` - the former is what every engine raises for
  what it validates, the latter is what DuckDB raises for SQL that cannot run
  and is deliberately *not* a ValueError. Importing duckdb here keeps that
  knowledge in the module that owns it.
- server/app/main.py: the five engine sites (single SQL run, multi-dataset SQL
  run, Python run, EDA, chart render) drop `except Exception -> 400` for
  `except INPUT_ERROR_TYPES`. The chart site catches ValueError alone, since
  render_chart validates everything itself.
- server/app/{planner,interpreter,drafter,generator,assistant}.py: the LLM
  fallback keeps catching everything but logs the reason first. `import
  logging` added to each.
- server/tests/test_error_semantics.py (NEW): 12 tests. Input errors stay 400
  (bad SQL, unknown column, multi-dataset bad SQL, a sandbox rejection, an
  unknown EDA op, an unknown chart kind); an injected harness fault answers 500
  in all five engines, via a TestClient with `raise_server_exceptions=False`
  - the only way a 500 is observable in process. Plus one pinning that an
  unexpected LLM failure still falls back *and* is logged.
- One nuance worth carrying: a 500 answers with Starlette's plain-text
  "Internal Server Error", not JSON. That is honest and logged, but the React
  shell does `res.json()` on errors, so the UX task should give it a JSON
  envelope - noted in CURRENT_STATE.md rather than expanded into this task.

## What changed (P4-VERIFY-001)

- verification/p3/verify_p3.py (NEW): the P3 gate, modelled on the P0/P1/P2
  gates. In-process TestClient, one atomic journey, a step table and an exit
  criteria table written to verification/p3/REPORT.md, exit 0 only when every
  step passes. It builds its own data - a CSV plus a Parquet written from a
  table with DuckDB, so the join deliberately mixes formats - and uses clean
  data on purpose, so validation reaching `supported` proves the join
  reproduces rather than that a messy finding was tolerated.
- Hermeticity is the one design decision worth stating: app.main loads
  server/.env at import (a gate is a script, not a pytest module) and every
  assistant engine reads DAH_LLM_API_KEY at *call* time, so scrubbing those
  variables after import is enough to make the whole journey deterministic.
  The LLM paths stay covered by the suite, which tests both engines
  explicitly; the gate's own report says source=deterministic on every
  assistant step.
- ai/ROADMAP.md, ai/CURRENT_STATE.md, ai/TASKS.md: P4 is IN PROGRESS with
  P4-VERIFY-001 DONE, the P3 gate added to the standing checks, and the
  P4-VERIFY-001 contract recorded.

## What changed (P3-EVIDENCE-006)

- server/app/evidence.py (NEW): `build_evidence_graph` reads the case's rows
  and builds nodes, edges and traces. Nothing is stored - it is a pure
  projection, so it cannot drift from what is on disk.
- server/app/main.py + models.py: the `/evidence-graph` endpoint and
  `EvidenceGraph` / `EvidenceNode` / `EvidenceEdge` / `ClaimTrace`.
- server/tests/test_evidence_graph.py (NEW): 7 tests, including orphan
  reporting (a dangling claim inserted directly into SQLite) and a join run
  whose trace covers both datasets it bound.

## What changed (P3-ANALYSIS-005)

- server/app/eda.py (NEW): `run_eda` compiles segment / correlate /
  distribution to SQL; column names are quoted and refused if they contain a
  quote; the numeric-vs-categorical choice for distribution reads DuckDB's own
  column types via DESCRIBE rather than probing with AVG.
- server/app/main.py + models.py: the `/eda` endpoint, `EdaCreate`, `EdaResult`.
- server/tests/test_eda.py (NEW): 9 tests.

## What changed (P3-FLOW-004)

- server/app/workflow.py (NEW): `case_progress` counts the case's artifacts and
  returns the first stage with nothing behind it, plus the deterministic next
  action and the endpoint that performs it. The loop closes when a finding has
  been validated.
- server/app/main.py + models.py: the `/progress` endpoint, `CaseProgress` and
  `WorkflowStage`.
- server/tests/test_workflow.py (NEW): 5 tests, including a full walk of the
  loop from case creation to a closed loop.

## What changed (P3-DATA-003)

- server/app/analysis.py: `run_query_multi(paths, sql)` binds placeholders
  positionally; `run_query` and the new path share `_execute_read_only`.
- server/app/main.py: `POST /cases/{case_id}/runs`; `dataset_ids_json` on the
  runs schema and in every read path; `_remap_dataset_ids` so a duplicated
  case's runs point at the copy's own datasets; validation reproduces through
  the multi path and now treats a query that no longer binds as a failed check
  rather than a 500.
- server/app/exporter.py: packages carry `dataset_ids` per run; import remaps
  them to the imported case's datasets.
- server/tests/test_multi_dataset_runs.py (NEW): 10 tests.
- Two real bugs surfaced and are pinned by tests: the placeholder regex needed
  escaping (a literal `?` inside a group is not a regex extension), and an
  INSERT value list had shifted a column (found by the validation tests).

## What changed (P3-CHART-002)

- server/app/charts.py: `render_chart(..., fmt="svg"|"png")` dispatches to
  `_render_svg` / `_render_png` after building a `ChartModel` that owns all
  geometry (scale, ticks, category order, bar geometry). Pillow is imported
  lazily; a missing install is a clear ValueError, not a crash.
- server/app/main.py: `ChartCreate.format`; artifact named `chart_<id>.<fmt>`;
  `_chart_media_type` sniffs PNG/SVG from stored bytes; duplicate preserves
  the source chart extension.
- server/app/exporter.py: charts exported with `format` + base64 `image_b64`
  (legacy `svg` text kept); import accepts both shapes.
- server/pyproject.toml: `charts` optional dependency (`pillow>=10`).
- server/tests/test_charts_raster.py (NEW): 9 tests, including a pixel scan of
  bar geometry and PNG export round trip.
- A refactor bug was caught here: the grouped-bar x-offset must use the series
  index, not the point index, or later bars slide off-canvas. Fixed in both
  backends and pinned by the new pixel test.

## What changed (P3-CASE-007)

- server/app/history.py (NEW): `build_case_history` reads the case's rows and
  derives a timeline - one event per artifact, stamped with that artifact's own
  timestamp. Like the evidence graph it is a pure projection, so it cannot drift
  from what is on disk. Validation has no persisted timestamp of its own, so a
  finding's validation status rides along as its event's detail rather than
  being invented as a separate timestamped entry.
- server/app/db.py: new `templates` table (`id, name, question, dataset,
  created_at`) under `CREATE TABLE IF NOT EXISTS` - older databases need no
  migration.
- server/app/main.py: `q` on `GET /cases` (LIKE on LOWER(question)/LOWER(dataset)
  with the term's wildcards escaped so a search is a literal substring);
  `GET /cases/{id}/history`; the four template endpoints. Case insertion is now
  a shared `_insert_case` helper so direct creation and templated creation
  cannot diverge on defaults.
- server/app/models.py: `Template`, `TemplateCreate`, `CaseFromTemplate`,
  `HistoryEvent`, `CaseHistory`.
- server/tests/test_case_history.py (NEW): 6 tests. server/tests/
  test_case_templates.py (NEW): 10 tests. tests/test_cases.py: 4 search tests,
  including one pinning that `%` and `_` in a term stay literal.

## What changed (P3-SEC-001)

- server/app/python_exec.py: `run_python` is now an orchestrator. It writes a
  JSON job into a per-run scratch dir, spawns `app.python_worker` as a child
  (sandbox-exec wrapped when available) with a scrubbed environment, and reads
  the tabulated result back from stdout. The old in-process body is
  `execute_user_code`, which the worker calls; timeouts are enforced three
  ways - parent kills the process group after limit + startup grace, child
  RLIMIT_CPU, child SIGALRM.
- server/app/python_worker.py (NEW): the in-sandbox entrypoint. Reads the job,
  runs `execute_user_code`, and emits either the result or `{"error": ...}`;
  it stays alive to report contract violations so the parent answers 400 with
  a useful message.
- server/tests/test_python_hard_sandbox.py (NEW): 6 tests at the process
  boundary - real seatbelt enforcement (scratch write allowed, outside write
  and network denied), child env scrub, process-group kill, runaway loop,
  dead worker, contract violation.

## What changed (P2-CASE-012)

- server/app/exporter.py (NEW): `export_case` assembles one self-contained JSON
  package (case, datasets with base64 bytes, profiles, runs, findings, charts
  with inline SVG, plans); `import_package` reconstructs it with fresh IDs and
  remapped references. `PackageError` covers malformed packages.
- server/app/main.py: `GET /cases/{id}/export` and `POST /cases/import`.
- server/tests/test_export.py (NEW): 5 tests - every section present with
  embedded bytes/SVG, 404 on unknown case, round trip restores state
  losslessly, references relink and artifacts are live (chart served, imported
  dataset queryable), malformed packages rejected.
- verification/p2/verify_p2.py (NEW): the P2 milestone gate, modelled on the P1
  gate. Walks the whole loop on deliberately messy data (a null, a duplicate
  row, a categorical split) and requires every P2 capability to fire.

## What changed (P2-AI-011)

- server/app/planner.py (NEW): the Analysis Planner. `plan_analysis` derives a
  structured plan deterministically from the question + profile - missingness,
  numeric spread/outliers, categorical splits, temporal trends, duplicates - so
  every item references real columns. `LLMPlanner` is an OpenAI-compatible
  backend on httpx (no SDK dependency), enabled by DAH_LLM_API_KEY (plus
  optional DAH_LLM_BASE_URL / DAH_LLM_MODEL). `create_plan` prefers the LLM,
  validates its output with `validate_plan`, and falls back to the deterministic
  planner on any failure - an unavailable or misbehaving LLM never blocks the
  loop. The persisted `source` field says which engine made the plan.
- server/app/main.py: `POST /cases/{id}/datasets/{id}/plan` (creates),
  `GET .../plan` (latest), `GET .../plans` (history). Planning requires a
  profile first (400 names the missing step). Duplicate now copies plans and
  delete now removes them.
- server/app/models.py: `Plan`, `PlanSummary`.
- server/app/db.py: new `plans` table.
- server/tests/test_plans.py (NEW): 10 tests - create/retrieve across sessions,
  plan references real columns, 400 without a profile, 404s, newest-first
  listing, LLM fallback on failure and on malformed output, valid LLM output
  persisted with source=llm, schema validation, and survival through
  duplicate/delete.

## What changed (P2-CASE-010)

- server/app/main.py: three endpoints - `PATCH /cases/{id}` (rename question
  and/or dataset label, bumps updated_at), `POST /cases/{id}/duplicate` (deep
  copy: case, datasets with bytes on disk, profiles, runs, findings, charts,
  all with fresh IDs and remapped references), `DELETE /cases/{id}` (children
  in FK order then the case row, plus `shutil.rmtree` of the case directory).
- server/app/models.py: `CaseUpdate`.
- server/tests/test_case_management.py (NEW): 9 tests - rename persists and
  leaves data alone, single-field rename, 404s, duplicate is deep and
  independent (new IDs, mutating the copy does not touch the original,
  dataset bytes copied into the copy's own directory), delete removes rows,
  files, and 404s afterwards, other cases untouched.

## What changed (P2-ANALYSIS-009)

- server/app/charts.py (NEW): deterministic, dependency-free SVG renderer.
  `bar` and `line` over one or more series (optional `series` column splits the
  result into legend-ordered series). Rendering from the *stored* run result
  keeps a chart reproducible after the run; SVG is stored in the case dir.
- server/app/main.py: chart endpoints - `POST /cases/{id}/runs/{id}/charts`,
  `GET .../charts` (list), `GET /cases/{id}/charts/{id}` (metadata),
  `GET /cases/{id}/charts/{id}/image` (serves the SVG as image/svg+xml).
- server/app/models.py: `ChartCreate`, `Chart`, `ChartSummary`.
- server/app/db.py: new `charts` table (run-scoped, case-owned).
- server/tests/test_charts.py (NEW): 11 tests - persist and serve, reopen in a
  new session, byte-identical re-render, multi-series line, chart from a Python
  run, rejection of unknown kind/column and non-numeric measure, 404s, and bar
  geometry (anchored on the zero baseline, heights proportional to values).

## What changed (P2-ANALYSIS-008)

- server/app/python_exec.py (NEW): restricted Python engine. User code gets a
  read-only `dataset` handle (`dataset.rows` as list of dicts, `dataset.query(sql)`
  under the same read-only SQL gate) and leaves its answer in `result`; a list of
  dicts or lists becomes the run's columns/rows.
- server/app/main.py: `POST /cases/{case_id}/datasets/{dataset_id}/runs/python`;
  `runs` read/write paths now carry `kind` and `code`; SQL runs unchanged.
- server/app/models.py: `PythonRunCreate`, `RUN_KINDS`, `Run`/`RunSummary` gained
  `kind` (`sql` | `python`) and nullable `code`; `sql` is now nullable.
- server/app/db.py: `runs` gained `kind` (default `sql`) and `code` columns, both
  added by `_ensure_column` so older databases migrate in place.
- server/tests/test_python_runs.py (NEW): 11 tests - persist/reopen, DuckDB query
  from Python, listing alongside SQL, and rejection of write queries, blocked
  imports, filesystem writes, dunder escapes, missing/empty `result`, 404s.

## What changed (P3-AI-011)

- app/interpreter.py (NEW): `interpret_result` (the deterministic reader -
  every figure it quotes is computed from the result's own rows, so it cannot
  invent a number), `LLMInterpreter` (OpenAI-compatible, httpx, JSON-only
  prompt), `validate_interpretation`, and `create_interpretation`, which prefers
  the LLM and falls back on any failure.
- app/db.py: the `interpretations` table (a child of a run, like charts).
- app/main.py: the three endpoints - POST (create), GET .../interpret (latest),
  GET .../interpretations (history, newest first) - plus duplication copying a
  case's readings onto the copy's own runs and deletion removing them.
- app/models.py: `Interpretation`.
- tests/test_interpretations.py (NEW): 9 tests, including one that pins the
  honesty property - the deterministic read may only quote values the result
  actually contains (the two aggregated totals, 80.5 and 325.0, and no others).

## What changed (P3-AI-014)

- app/assistant.py (NEW): `summarize_case` (the facts, read from the case's
  rows - runs carry columns and row counts, not result rows, because a
  conversation points at evidence rather than replaying it), `answer_question`
  (deterministic; counts, a named column's real profiled stats, a dataset
  summary, the latest finding, or the derived stage and next action),
  `_references` / `parse_ground` / `validate_answer` (the citation budget: each
  ground must be `kind:name` with name in the case), `LLMAssistant`
  (OpenAI-compatible, httpx, JSON-only prompt, told the exact artifact ids and
  the last ten turns) and `create_answer`, which prefers the LLM and falls back
  on any failure - unavailable, malformed, or citing an artifact the case does
  not have.
- app/db.py: the `conversations` table under `CREATE TABLE IF NOT EXISTS`, so
  older databases need no migration.
- app/main.py + models.py: `POST /cases/{id}/chat` (201, persists the turn) and
  `GET /cases/{id}/chat` (oldest first), `ChatRequest` and `ConversationTurn`.
  Case deletion now removes the conversation with the rest of the case's
  children; duplication deliberately does not copy one (a duplicate starts a
  fresh investigation).
- tests/test_conversation.py (NEW): 12 tests - counts, a column's real stats,
  the derived stage and next action, grounds checked against the case's own
  rows, LLM accepted, the prior turn reaching the LLM, invented citation
  rejected, failure and malformed fallbacks, persistence oldest-first, delete
  cleanup at the row level, 404s.

## What changed (P3-AI-013)

- app/generator.py (NEW): `generate_code` (deterministic; `_pick_axes` chooses
  the measure and dimension from the profile and `_is_identifier` keeps a unique
  key from being summed or grouped by), `_sql_identifiers` /
  `_python_read_columns` / `_columns_referenced` (the reach of a proposal -
  aliases, function calls, qualified names and SQL literals are treated as
  structure, and a Python proposal's *reads* are checked while its output dict
  keys are not, because inventing an output name invents nothing), the
  read-only check `_looks_read_only`, `validate_code`, `LLMGenerator`
  (OpenAI-compatible, httpx, JSON-only prompt, told the exact columns that
  exist) and `create_code`, which prefers the LLM and falls back on any failure
  - unavailable, malformed, a wrong `kind`, a statement that is not read-only,
  or a column the dataset does not have.
- app/main.py + models.py: the stateless `POST .../generate-code` endpoint (200
  - no INSERT, no new table), `GenerateCodeRequest` and `GeneratedCode`. It
  requires a profile first (400 names the missing step), exactly as planning
  does, because a proposal against an unprofiled dataset is a guess.
- tests/test_code_generation.py (NEW): 13 tests - deterministic SQL and Python
  proposals naming the dataset's real columns (and not its identifier), columns
  used checked against the profiled set, both proposals running as-is through
  the existing run endpoints, single-read-only check, LLM accepted, invented
  column rejected, DELETE rejected, failure and malformed fallbacks, no state
  written for either kind, 400 without a profile, 404s including a cross-case
  dataset.

## What changed (P3-AI-012)

- app/drafter.py (NEW): `draft_finding` (the deterministic drafter - every figure
  is computed from the result's own rows, and a result with no numeric measure
  gets an honest weaker draft that says so), `_allowed_numbers` (the honesty
  budget: cell values, the row/column counts, and how often each value repeats),
  `validate_draft`, `LLMDrafter` (OpenAI-compatible, httpx, JSON-only prompt)
  and `create_draft`, which prefers the LLM and falls back on any failure -
  unavailable, malformed, schema-invalid, or quoting a magnitude the result does
  not contain.
- app/main.py + models.py: the stateless `POST .../draft-finding` endpoint (200 -
  no INSERT, no new table) and `DraftFinding`. It loads exactly what an
  interpretation loads (run columns/rows, question, SQL or script, profile) so
  the two slices compose.
- tests/test_drafting.py (NEW): 10 tests - deterministic draft naming the run's
  real columns, grounds checked against the result's own honesty budget via the
  API, LLM accepted, invented magnitude rejected, failure and malformed
  fallbacks, the findings table left empty, accept-then-validate round trip
  (an accepted draft validates `supported`), the no-numeric-column draft, 404s.

## What changed (P3-VALID-010)

- server/app/main.py: validate_finding no longer special-cases Python runs
  aside with a 400. Reproduction is factored into `_reproduce_sql` and
  `_reproduce_python` (both record the same reproducibility check through
  `_record_repro`), and the missing_data / evidence_integrity checks and the
  status arithmetic are shared between the two kinds. Python compares both
  columns and rows, because the tabulator names columns in first-seen order and
  a shape change would otherwise hide behind matching values.
- One real bug surfaced and is pinned by a test: the run lookup in
  validate_finding did not select `runs.code`, so `run_row["code"]` raised
  sqlite3's IndexError "No item with that key" - which the broad except
  faithfully reported as "script rejected". Fixed by selecting the column.
- server/tests/test_validation.py: +4 tests (reproduces, row drift, shape drift,
  and a script that now raises returning a verdict rather than a 500).
  tests/test_python_runs.py: the one test that pinned the old 400 now asserts a
  real `supported` verdict.

## What changed (P3-DATA-009)

- server/app/main.py: `DELETE /cases/{case_id}/datasets/{dataset_id}` (204),
  plus `_runs_touching_dataset`, the lookup that decides whether deletion is
  safe. It scans a case's runs for the dataset as either the primary
  (runs.dataset_id) or one of several (runs.dataset_ids_json, P3-DATA-003) -
  legacy runs have no JSON list, so the primary column is checked on its own.
  Deletion removes the profile, the plans and the file alongside the row.
- server/tests/test_dataset_delete.py (NEW): 8 tests. The refusal is exercised
  both for a single-dataset run and for the non-primary member of a join run,
  and one proves the gate is live data rather than a stored flag by removing
  the run row directly (no run-delete endpoint exists yet) and watching
  deletion succeed.

## What changed (P3-SHELL-008)

- desktop/ (NEW): the whole Tauri 2 shell. `src/core_server.rs` is the pure,
  tested resolution + health-gate logic (`resolve_server_command`,
  `wait_for_health`, `ServerCommand::to_process`, group-kill `ServerChild`);
  `src/main.rs` is the window lifecycle; `tauri.conf.json` has **no `devUrl`**,
  so every build - debug included - serves the embedded bundle and can never
  point the webview at a port nothing is serving. Capabilities grant only
  `core:default`; the webview never loads a remote URL, so the desktop bundle
  is built with an absolute API URL (`VITE_API_URL=http://127.0.0.1:8123`).
- server/app/supervisor.py (NEW): `start_parent_watchdog()` - a daemon thread
  that `os._exit(0)`s the core when `DAH_PARENT_PID` is gone. No-op without the
  variable; rejects junk and <= 0. Called from main.py after the imports.
- server/dah_core_main.py + dah-core.spec + build_sidecar.sh (NEW): the
  PyInstaller one-file sidecar and the script that installs it as
  `desktop/src-tauri/binaries/dah-core-<triple>` (gitignored, 85MB, never
  committed).
- web: `build:desktop` and `build:desktop:watch` produce the desktop bundle;
  `vite.config.ts` pins the dev server to port **5273** with `strictPort` -
  5173 (vite's default) collides with another local dev server, and a silent
  port hop is what left the shell's webview on a dead page.
- Two test-hygiene fixes landed while verifying: `test_export.py` is now
  hermetic against an ambient LLM key, and the P2 gate no longer leaks
  `DAH_LLM_API_KEY` into the pytest subprocess it spawns (see below).

## Sandbox posture (documented, see module docstring)

Blocked: filesystem writes, process execution, network egress, resource
exhaustion (wall-clock + CPU limits). This is a *soft* sandbox for a local
single-user tool: it stops accidental writes and runaway AI-generated code, not a
hostile user who owns the machine. Address-space limits were tried and dropped -
macOS maps far more VM than a useful cap allows; a real memory bound needs the
separate-process hard sandbox planned for V1. Validation of Python runs is
reported as unsupported (clear 400) rather than faked; that gate is future work.

## Tests performed (current)

- server pytest: 336 passed (315 + 21 update check; verified again on a clean
  venv built from pyproject - the install path CI uses)
- CI on GitHub's own runners: ALL FOUR JOBS GREEN
  (run 35490199963, the first green run since ae0ba33 - server suite + P2/P3/P4
  gates, web suite + build, sidecar packaging + the /health and packaged-log
  smoke, desktop shell lifecycle with both e2e tests against the real sidecar).
  The runner is macos-latest; macos-13 is retired from the hosted pool (DEC-005)
- Release pipeline: v0.1.0 published end to end from tag (run 35490519483).
  The 79MB zip's sha256 verified against its checksum asset, Info.plist reads
  0.1.0, and the bundle carries dah-shell (15MB) + dah-core (78MB). The build
  is arm64 and unsigned, flagged pre-release
- P4 gate: `server/.venv/bin/python verification/p4/verify_p4.py` PASS on all
  18 journey steps and all 10 exit criteria (the last step re-runs the suite)
- desktop shell: 7 Rust tests, now stable - five are #[serial] after CI caught
  two interference races (port 8123 and the DAH_DEV_CORE env var)
- web: 17 passed (CaseList 5, CaseCreation 3, CaseWorkspace 9); `cd web && npm test`
- desktop shell: 12 Rust tests - `cd desktop/src-tauri && cargo test` (7 unit)
  and `cargo test --features e2e` (+2 live-core tests)
- P3 gate: `server/.venv/bin/python verification/p3/verify_p3.py` PASS on all
  23 journey steps and all 15 exit criteria (the last step re-runs the suite)
- P2 gate: `server/.venv/bin/python verification/p2/verify_p2.py` PASS on all
  18 steps

## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

**P7-EVAL-001 is DONE**, and with it the first of P7's four checklist items.
EVALUATE mode audits submitted work against the nine axes the specification
names; the core can now be pointed at an analysis it did not write and answer
whether it holds up. Everything below was verified green: 358 server tests
(was 336, +22 in `server/tests/test_evaluator.py`), the P2, P3 and P4 gates
each re-running the suite at 358, the web suite at 21 and the desktop shell at
22 Rust tests.

### What is unbuilt, in priority order

- **The web shell is behind the core** - P7 item 2, and the highest-value work
  left that needs no new core capability. These endpoints have no UI at all:
  the agent (`/agent`), templates (`/templates`, `/from-template`), cross-case
  memory, EDA (`/eda`), the evidence graph (`/evidence-graph`), case history,
  rename/duplicate/delete, `/schema-version`, `/updates/latest` - and now
  `/evaluate`, which currently answers only through the API. The core can do
  all of it; the shell is the distance between "works" and "usable".
- **LEARN mode** - a guided Why -> What -> How -> Validate walk over a dataset.
  Mostly a sequencing and presentation layer over the workflow stages that
  already exist (P3-FLOW-004), which is why it follows the shell gap.
- **Multi-agent workflows** - the spec's ladder above the single driver that
  exists (P6-AGENT-002). Only after EVALUATE, which is how an agent's own
  output gets audited.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.
  None pays for itself at a user count of one, and the architecture is
  deliberately not shaped around them.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build
is arm64 and unsigned, flagged pre-release (DEC-006). The version has not been
bumped since v0.1.0; five tasks have landed since, so a `0.2.0` is the honest
next label when a release is wanted.

Nothing is unblocked-but-undone.
## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

**P6 is CLOSED.** All five entry-checklist items are delivered: cross-case
recall, agentic analysis, analytical-shape templates, the versioned migration
path, and the update check. P0 through P6 are complete.

The last task, P6-UPDATE-005, delivered the half of an update flow that is
verifiable and deliberately not the other half. `GET /updates/latest` answers
one of three truths and the shell's **DAH > Check for Updates...** menu item
opens the release page or shows why it could not tell. The self-replacing
install did not ship, because the repository is private (an unauthenticated
feed answers 404, verified) and the app is unsigned (DEC-006), so a payload
cannot be signature-verified. That is a slot, not a gap: `tauri-plugin-updater`
consumes exactly this check when signing lands, and the design's core
distinction - "could not check" is never reported as "is up to date" - is what
makes the slot safe to fill later.

### What is unbuilt, in priority order

- **EVALUATE mode** - the spec's third product mode, and the one DAH uniquely
  owns. Import existing analytical work (SQL, a Python script, a notebook, a
  dashboard export, a spreadsheet, an AI-generated analysis) as the *thing under
  inspection*, and audit it against nine axes the spec names: question, data,
  quality, method, calculation, evidence, claim, visualization, limitations.
  Most of the machinery already exists - read-only execution, deep profiling,
  rerun validation, the evidence graph, the honesty budgets. What does not is
  importing an artifact *as a claim being evaluated* rather than as data to
  analyse. This is the largest genuine capability left, and it is the one that
  separates DAH from a notebook.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk over a dataset.
  Mostly a sequencing and presentation layer over the workflow stages that
  already exist (P3-FLOW-004), which is why it is second.
- **The web shell is behind the core.** These endpoints have no UI at all: the
  agent (`/agent`), templates (`/templates`, `/from-template`), cross-case
  memory, EDA (`/eda`), the evidence graph (`/evidence-graph`), case history,
  rename/duplicate/delete, `/schema-version` and `/updates/latest`. The core
  can do all of it; the shell is the distance between "works" and "usable".
- **Multi-agent workflows** - the spec's ladder above the single driver that
  exists. Only after EVALUATE, which is how an agent's own output gets audited.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.
  None pays for itself at a user count of one, and the architecture is
  deliberately not shaped around them.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). The version has not been
bumped since v0.1.0; four tasks have landed since, so a `0.2.0` is the honest
next label when a release is wanted.

Nothing is unblocked-but-undone.
## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

P6-MEMORY-001 is **DONE**: cross-case recall. A case could already cite its own
artifacts - runs, datasets, findings - through the grounds budget in
`assistant.py`, but `summarize_case` read exactly one case's rows, so every
investigation started from scratch even when the same anomaly was found and
explained last month. Now an answer can cite a *previous* case.

Three pieces:

- **`server/app/memory.py` (new)** - `summarize_memory` is a pure projection
  over the cases and findings already on disk. Relevance is a
  shared-content-word count against the prior case's question, dataset label
  and finding statements, with a hand-written stoplist and a threshold of two
  shared words. Deliberately not an embedding: no dependency, no network call,
  deterministic, and it makes the "nothing bears on this" answer honest rather
  than a confident stretch. A case with no findings is skipped however similar
  its question sounds - there is nothing to recall. It writes nothing; memory
  is derived, never stored, so it cannot drift from what is on disk any more
  than the evidence graph can.
- **`server/app/assistant.py`** - a new `case:` ground kind, a recall branch in
  the deterministic answer, and `_references` admitting both the prior case and
  its finding id. The recall branch fires when the question is *about* prior
  work (before/previous/earlier/...) or when the case has nothing of its own.
  It sits **ahead** of the column and dataset branches on purpose: "what did I
  find before about revenue?" names a column, and would otherwise be answered
  with this case's column stats - a true answer to a question nobody asked. A
  case with its own artifacts and no prior framing still gets its own stage and
  next action, because its own state is the more actionable thing. The LLM
  prompt now carries memory and its citation budget names the case kind.
- **`server/app/main.py`** - the chat endpoint passes the message through to
  `summarize_case`, because which prior cases are relevant depends on what was
  asked, not on the case.

The honesty budgets from P3-AI-011..014 survive by construction: a cross-case
ground must resolve to a real finding in a real other case or the answer is
rejected, exactly as an invented column is. The deterministic path needs no LLM
key, nothing logs what the analyst typed, and no new runtime dependency was
added - SQLite already holds everything.

**Verified:** server suite 267 passed (was 256, +11 in
`server/tests/test_memory.py`); the P4 gate PASS on all 18 journey steps and
all 10 exit criteria; the P3 gate PASS; web 21 passed; desktop 12 Rust tests.
Everything green locally; CI will run it on push.

One lesson worth carrying: three of the eleven tests failed on the first run
for a reason that was the *test's* fault, not the code's. The helper hardcoded
a finding about revenue in sales.csv while the question was about revenue, so
an allegedly off-topic prior case still shared two content words and was
correctly recalled. The code was right; the test asserted a separation its own
data did not have. A relevance threshold is only as honest as the corpus it is
measured against, and a fixture that says "weather" while quoting "sales" is
not a weather fixture.

**Next on the P6 checklist: agentic analysis** - a plan that executes itself
over the endpoints that already exist (generate code, run it, interpret, draft,
accept), with the human approving each write. It is the highest
capability-per-risk item left, and it is only safe because P4 pinned the
honesty budgets and P5 made faults observable. Its contract is not yet written;
the memory it will need is now in place, which is exactly why it was second.

After that: case templates carrying the analytical shape rather than just the
question, a versioned migration path before memory grows new tables, and a
Tauri update flow now that releases publish per tag.

Releasing: tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The
published build is arm64 and unsigned, flagged pre-release (DEC-006).

Nothing is unblocked-but-undone.
