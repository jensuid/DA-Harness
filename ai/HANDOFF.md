# DAH - Handoff

## What was completed
- P4-VALID-005 PASSED: validating the same finding twice now always gives the
  same verdict. The live-LLM smoke of P4-UX-004 walked the whole loop
  repeatedly and validation started flipping between `supported` and
  `insufficient_evidence` on identical inputs - a real bug, not a test artifact.
  DuckDB gives no row-order promise for a result that never asked for one, and a
  GROUP BY returns its groups in either order across connections (verified: 2
  distinct orders across 8 reruns of one query). `_reproduce_sql` compared rows
  positionally, so an unordered query was a rerun mismatch roughly half the time.
  It now compares `sorted(rerun) == sorted(stored)` - a multiset comparison,
  which is what an SQL result set actually is (a bag of rows; only ORDER BY makes
  it a sequence, and DuckDB honours that deterministically, so the sort is a
  no-op there and a correction everywhere else). `_reproduce_python` is
  deliberately left positional: the tabulator is deterministic and column order is
  a shape signal there. Two regression tests, one of which was verified to FAIL
  without the fix.

- P4-UX-004 PASSED: the three remaining assistant slices are reachable from the
  workspace - generate code from a question, read what a run shows, draft the
  finding it would support - each proposing and none deciding. CaseWorkspace is
  now the loop the core walks, one panel per step: attach + profile, generate
  code (Run posts to the only endpoint that persists a run), runs with Interpret
  and Draft-finding buttons, a draft that Accept posts to the only endpoint that
  writes a finding, then Validate with its verdict and checks. Every assistant
  panel names the engine that spoke. 9 new web tests (17 total, was 13). The
  full loop was smoked against the live core with the LLM live, which is exactly
  what exposed the DuckDB GROUP BY ordering flake fixed as P4-VALID-005.


- P4-UX-003 PASSED: DAH can be used from the shell instead of curl. The React
  bundle was still the P0/P1 surface - one case-creation form and no way to
  open a case - so the assistant surfaces had nowhere to live. Now cases list
  with a literal-substring search, creating one opens its workspace, and the
  workspace shows the question, the *derived* stage and the single next action
  (recomputed from the core on open, so the UI cannot show a stage the data
  does not support), the attached datasets and the runs, and the chat panel.
  Chat is the assistant slice that needs nothing but a case, and it is where
  the honesty property becomes visible: each ground renders as a citation chip
  and a badge says which engine spoke. Prior turns load oldest-first. api.ts is
  a typed client whose request() parses a JSON detail only when the core sent
  JSON - a 500 answers plain text, and res.json() on it would have thrown a
  second, hiding the failure. 13 web tests (was 2: CaseList 5, CaseCreation 3, CaseWorkspace 5), and the API contract was
  verified field-for-field against the live core rather than only against
  mocks.

- P4-RELIABILITY-002 PASSED: an input error now answers 400 with the engine's
  own message, and a fault in the harness answers 500 - before this, five
  engine endpoints ended in `except Exception as error: raise 400`, which did
  two jobs at once and got them both subtly wrong. It was the *only* thing
  keeping a user's SQL syntax error a 400 (DuckDB raises `duckdb.Error`, which
  is not a `ValueError`, so the `except ValueError` above it never fired), and
  it also flattened every real server fault - sqlite, an unreadable stored file,
  a KeyError in our own code - into a 400 that blamed the analyst. `app/errors.py`
  now owns the taxonomy once: `INPUT_ERROR_TYPES` is `(ValueError, duckdb.Error)`,
  the families that mean the input cannot be honoured; each site catches only
  those and anything else propagates to an honest 500 that uvicorn logs with a
  traceback. The five LLM fallbacks were deliberately broad and stay broad -
  degradation is the contract - but each now logs the reason at warning level,
  so a fallback caused by our own bug surfaces instead of vanishing into
  `source=deterministic`. 12 new tests pin both directions: bad SQL, an unknown
  column and a sandbox rejection stay 400, while an injected fault in all five
  engines answers 500.

- P4-VERIFY-001 PASSED (first P4 task): P3 now has a gate of its own. `verification/p3/verify_p3.py`
  walks one journey in-process - a question, a CSV and a Parquet attached to the
  same case, both profiled, the assistant proposing the query and creating
  nothing, a plan, one SQL run joining both files positionally, a hard-sandbox
  escape attempt refused with a 400 that leaves no run behind, the assistant
  reading the result and drafting the finding (still writing nothing), the human
  accepting the draft through the only endpoint that writes, a raster chart,
  validation closing the loop on the join finding, an evidence graph whose claim
  trace reaches *both* datasets, the derived workflow reporting stage=validated
  and loop_closed, chat with citations, EDA without a query, the case history,
  search, a template that outlives its case, dataset deletion refused while
  evidence stands on it, and an export/import round trip that reproduces the
  join elsewhere - then re-runs the suite. 23 journey steps and 15 exit
  criteria, all PASS (`verification/p3/REPORT.md`). The gate is hermetic: the
  LLM credentials are scrubbed from its own process and from the pytest
  subprocess, so every assistant step reports source=deterministic and the gate
  makes no network call.

- P3-AI-011 PASSED (contextual AI, slice 1 of 4): a persisted result can now be
  *read*. `POST /cases/{id}/runs/{id}/interpret` returns a plain-language
  summary, observations and caveats grounded in the result's own numbers, in
  the language of the case's question. Two engines behind one interface, as the
  planner does it: a deterministic reader that computes row counts, numeric
  ranges and the most frequent value per column from the persisted rows, and an
  LLM behind `DAH_LLM_API_KEY` that degrades to the deterministic read on any
  failure. `source` records which one spoke. Three slices remain: finding
  drafting, code generation, conversational memory.

- P3-AI-014 PASSED (contextual AI, slice 4 of 4 - and the last P3 item): a
  case can now be asked questions, and every answer cites its evidence. `POST
  /cases/{id}/chat` with a message returns an answer plus `grounds` - citations
  of the form `kind:name` naming the dataset, run, finding, plan, chart or
  column behind each claim; `GET /cases/{id}/chat` replays the conversation
  oldest-first, so a reopened case resumes mid-thought. `summarize_case` reads
  the case's rows and builds the facts an answer may draw on - a pure
  projection, like the evidence graph and the history timeline, so it cannot
  drift from what is on disk. Two engines behind one interface, as in every
  other slice: a deterministic assistant that answers count, column and dataset
  questions and otherwise states the case's derived workflow stage and the one
  action that advances it (reusing P3-FLOW-004, so it cannot claim a step the
  data does not support), and an LLM behind `DAH_LLM_API_KEY` that receives the
  recent turns as context - that is the memory. Honesty is enforced: every
  citation must be an artifact the case actually has, and an answer about a case
  with artifacts must cite at least one. An invented citation is a validation
  failure and the answer falls back to the deterministic one. **This closes
  roadmap item 7 and the whole P3 phase.**

- P3-AI-013 PASSED (contextual AI, slice 3 of 4): a question in plain
  language now yields the read-only computation that would answer it. `POST
  /cases/{id}/datasets/{id}/generate-code` takes `{question, kind}` and returns
  `{kind, code, explanation, columns_used, source}` - a proposal that creates
  nothing; running it is a POST to the existing `/runs` or `/runs/python`
  endpoint, the only paths that persist a run, so the human decides what
  executes. Two engines behind one interface, as before: a deterministic
  generator that reads the profile's own structure (its measure, its widest
  categorical or temporal dimension, its nulls) and writes a GROUP BY
  aggregation - counting by dimension when the data has no measure to sum, and
  skipping identifier columns, which are keys rather than quantities - and an
  LLM behind `DAH_LLM_API_KEY`. Honesty is enforced: every column the generated
  code reads must be a column the dataset actually has (aliases, function calls
  and qualified names are structure, not reads), and a generated SQL proposal
  must be a single read-only statement, so nothing is handed to the analyst that
  the runner would refuse. One slice remains: conversational memory.

- P3-AI-012 PASSED (contextual AI, slice 2 of 4): a result can now propose
  the finding it would support, and the proposal creates nothing. `POST
  /cases/{id}/runs/{id}/draft-finding` returns a candidate - statement,
  interpretation, caveat and grounds (the values the statement stands on) -
  computed from the run's own rows. Two engines behind one interface, as the
  planner and interpreter do it: a deterministic drafter that finds the result's
  measure and dimension and states which category leads at what value, and an
  LLM behind `DAH_LLM_API_KEY`. Honesty is enforced rather than hoped for: every
  number in the statement or the grounds must be one the result actually contains
  (a cell, a row count, or a repeat count), so an invented magnitude fails
  validation and the draft falls back to the deterministic one. Accepting a draft
  is a POST to the existing `/findings` endpoint - the only path that writes a
  finding - which makes "the LLM proposes, the human disposes" structural instead
  of a flag. The findings table is untouched by this task. Two slices remain:
  code generation and conversational memory.

- P3-AI-011 PASSED the trust loop has no gaps left. A finding built on a
  Python run now validates the same way a SQL one does - the stored script is
  re-executed through the hard sandbox against the stored dataset and its
  tabulated columns AND rows are compared to what the run persists. A script
  that no longer runs is a failed reproducibility check with the reason in its
  detail, never a 500, exactly like a SQL query that no longer binds. This was
  the last place the loop answered "not supported".

- P3-DATA-009 PASSED: a dataset can now be removed from a case without throwing
  the case away. `DELETE /cases/{id}/datasets/{id}` drops the row, its profile,
  its plans and its on-disk file, and refuses with a 400 while any run still
  binds it - because a run is the evidence a finding or a chart stands on (the
  chain is finding -> run -> dataset), and deleting underneath it would leave a
  dangling trace. The refusal names the blocker count, and the check reads both
  runs.dataset_id and the multi-dataset JSON list. This is also the first thing
  that makes the derived workflow stage observable moving *backwards*
  (P3-FLOW-004).

- P3-SHELL-008 PASSED: DAH is a double-clickable app. A Tauri 2 shell serves the
  *same* React bundle (`web/`, built into `web/dist-desktop`) and that bundle
  keeps talking to the *same* FastAPI core over HTTP - a host swap, not a
  rewrite, exactly as DEC-001 planned. The shell spawns the core (the packaged
  PyInstaller sidecar, or `server/.venv` uvicorn in a dev checkout), keeps the
  window hidden until `/health` answers, and stops the core on close and on
  exit. A parent-pid watchdog ends the core even when the shell is SIGKILLed,
  which is the death that reaches no Tauri event and no destructor.

- P3-CASE-007 PASSED: a finished investigation is now reusable. `GET /cases?q=`
  finds a case by question or dataset label (case-insensitive, literal
  substring); `GET /cases/{id}/history` replays everything that happened in a
  case as a chronological timeline derived from each artifact's own timestamp;
  templates (`POST /cases/{id}/template`, `GET /templates`,
  `POST /cases/from-template`, `DELETE /templates/{id}`) capture a case's
  skeleton so a new one can start shaped like a previous one. Templates are not
  case children - they outlive the case they came from.

- P3-EVIDENCE-006 PASSED: GET /cases/{id}/evidence-graph projects a case into
  its evidence graph - every dataset, run, chart, plan and finding as a node,
  each derivation as an edge, and a per-claim trace walking a finding out to
  the data it stands on. Claims that reach no dataset are listed as orphans,
  which is what makes it a review tool.

- P3-ANALYSIS-005 PASSED: POST /cases/{id}/datasets/{id}/eda runs segmentation,
  correlation, and distribution summaries. Each op compiles to read-only
  DuckDB through the existing run_query, so the read-only gate and row cap
  apply and output is the standard result shape.

- P3-FLOW-004 PASSED: GET /cases/{id}/progress reports where a case stands in
  the loop and the single action that advances it. The stage is *derived* from
  the case's artifacts - no schema change - so it cannot claim a step the data
  does not support.

- P3-DATA-003 PASSED: one run can now join several attached datasets.
  POST /cases/{id}/runs takes dataset_ids and binds the k-th placeholder in the
  SQL to the k-th dataset, in order - any mix of csv/parquet/xlsx. Runs record
  the full dataset list (dataset_ids_json) with the first kept as the primary,
  and validation, duplicate, and export/import all carry it.

- P3-CHART-002 PASSED: charts can now render as PNG behind the same interface.
  charts.py is now a shared ChartModel plus SVG and PNG backends, so the two
  cannot drift apart; the PNG path draws at 2x and downscales with LANCZOS.
  The `format` field threads through the API (artifact extension, sniffed media
  type) and the export package carries chart bytes as base64 with an explicit
  format, keeping the legacy `svg` text field for older consumers.

- P3-SEC-001 PASSED: Python analysis runs now execute in a separate process
  under an OS-level sandbox (macOS sandbox-exec / seatbelt). Writes outside
  the per-run scratch directory and all network access are denied by the
  kernel; the child environment carries no API-process secrets; runaway loops
  are killed at the process-group level and reported as a 400. The P2 soft
  guards remain as defense in depth inside the child.

- P2-ANALYSIS-008 PASSED: read-only Python execution against an attached dataset,
  result persisted and retrievable like a SQL run
- P2-ANALYSIS-009 PASSED: chart images rendered from a persisted run result and
  stored with the case as evidence artifacts
- P2-CASE-010 PASSED: rename, duplicate (deep copy, new IDs throughout), and
  delete (rows + on-disk data) of Analysis Cases
- P2-AI-011 PASSED: AI planning with structured output - objective, primary
  question, sub-questions, hypotheses, data requirements, analysis steps
- P2-CASE-012 PASSED: case export as a self-contained JSON package, with import
  as the round-trip proof
- **P2 MILESTONE COMPLETE**: verification/p2/verify_p2.py PASS on all 16 steps
  and all 10 exit criteria
- P2-DATA-007 PASSED: deep profile (types, null %, distinct counts, min/max/avg, duplicate rows)
- P2-DATA-006 PASSED: parquet + xlsx attach, profile, and query alongside CSV
- P0 PASSED: verification/p0/REPORT.md (re-run during this task: PASS)
- P1 PASSED: verification/p1/REPORT.md - re-run during this task: PASS (43 tests)

## P1 vertical slice (verified)

```
Create Case -> Question -> Load CSV -> Profile -> SQL Analysis
-> Finding -> Evidence chain -> Validation (rerun) -> Save -> Reopen
```

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

- server pytest: 225 passed (was 223; +2 validation determinism)
- web: 17 passed (CaseList 5, CaseCreation 3, CaseWorkspace 9); `cd web && npm test`
- desktop shell: 7 Rust tests - `cd desktop/src-tauri && cargo test` (5 unit)
  and `cargo test --features e2e` (+2 live-core tests)
- P3 gate: `server/.venv/bin/python verification/p3/verify_p3.py` PASS on all
  23 journey steps and all 15 exit criteria (the last step re-runs the suite)
- P2 gate: `server/.venv/bin/python verification/p2/verify_p2.py` PASS on all
  18 steps

## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004 and P4-VALID-005 as
  their own commits.
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

P4 is four tasks in and the assistant surfaces are finished - the workspace now
walks the whole loop the core walks (P4-UX-003 + P4-UX-004), and validation is
deterministic across connections (P4-VALID-005, a real bug the live smoke
exposed). What remains of the P4 checklist, oldest risk first:

- large-dataset behaviour: the 1000-row result cap exists but nothing has been
  measured at scale. Profiling cost, query cost and export package size on a
  case with many artifacts are all unmeasured. This is the performance task.
- the desktop shell lifecycle under CI (the Rust tests run locally, including
  the two live-core e2e tests), and the app-signing decision - sign now or
  formally defer to P5.
- carried: a 500 still answers with Starlette's plain-text "Internal Server
  Error". The client handles it (it parses JSON only when the core sent it),
  but giving the 500 a JSON envelope remains worth doing.

Nothing is unblocked-but-undone. The one remaining carried item is not agent
work: the packaged app is unsigned, so macOS gatekeeps the first launch
(right-click, Open); signing and notarization are P5.

## Important context

- Server venv: server/.venv (Python 3.14). There is no `pip` module - install
  with `uv pip install --python .venv/bin/python <package>`; PyPI is reachable.
- LLM config: `server/.env` is auto-loaded at server startup (see
  `docs/LLM Configuration.md`), so `uvicorn app.main:app` alone picks up
  DAH_LLM_API_KEY / DAH_LLM_BASE_URL / DAH_LLM_MODEL. The load is skipped under
  pytest so a configured key never makes test-time live calls; an exported
  variable always overrides the file.
- Run tests: `cd server && .venv/bin/python -m pytest -q`
- P3 gate: `server/.venv/bin/python verification/p3/verify_p3.py` (~3-4 min; it
  re-runs the suite, and its journey is deterministic - the LLM vars are
  scrubbed, so no assistant step makes a live call)
- P2 gate: `server/.venv/bin/python verification/p2/verify_p2.py` (~70-90s; it
  re-runs the suite)
- P1 gate (in-process): `server/.venv/bin/python verification/p1/verify_p1.py`
- P0 gate binds a port - run it outside the sandbox if it fails
- Web: `cd web && npm run dev` (deps installed; UI is P0/P1 scope, case creation
  only). The vite dev server is pinned to port **5273** with `strictPort` -
  5173 collides with another local dev server here, and a silent hop to the
  next free port is what made the shell show an empty window.
- Desktop shell: `cd desktop && npm install` once, then `npm run dev` (serves
  the embedded bundle - what the packaged app serves) or `npm run dev:hmr`
  (vite dev server, port 5273, true HMR). Packaged: `cd server &&
  ./build_sidecar.sh && cd ../desktop && npm run build`. Tests:
  `cd desktop/src-tauri && cargo test --features e2e`.
- A uvicorn server may still be running on port 8123 from the MVP demo - check
  `curl -s localhost:8123/health` before starting another
- python-multipart installed; DATA_DIR gitignored
- No pandas/numpy available - the Python engine is dependency-free and works on
  plain dicts
