# DAH - Handoff

## What was completed

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

- server pytest: 155 passed (145 + 7 supervisor + 3 env-config)
- desktop shell: 7 Rust tests - `cd desktop/src-tauri && cargo test` (5 unit)
  and `cargo test --features e2e` (+2 live-core tests)
- web: 2 passed
- P2 gate: `server/.venv/bin/python verification/p2/verify_p2.py` PASS on all
  18 steps (re-verified during this task; the gate re-runs the suite)

## Repository state

- Working tree clean; every P3 task is one atomic commit, all pushed to
  `origin/master` (github.com/jensuid/DA-Harness):
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, <this commit> P3-SHELL-008
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
  two ways: the gate scrubs the LLM vars from its subprocess, and
  `test_export.py` deletes them. Any future runner that spawns the suite must
  do the same.
- Python-run validation is still reported as a clear 400 "not supported yet".
  The hard sandbox (P3-SEC-001) unblocks it, but the validation gate itself is
  not yet implemented. Recorded in ai/TASKS.md.
- No single-dataset delete endpoint: nothing can walk a case backwards today.
  Recorded in ai/TASKS.md.
- Contextual AI (roadmap item 7) is BLOCKED on the user setting
  `DAH_LLM_API_KEY`. The planner's LLM path is coded and monkeypatch-tested but
  dormant without the key. Not an agent task.

## Next action

P3 has one item left: roadmap item 7, the contextual AI assistant (code
generation, result interpretation, finding drafting). The planner backend it
would build on is already live - `DAH_LLM_API_KEY` is configured in
`server/.env` and the P2 gate's plan step reports `source=llm` - so this is an
agent task now, not a user action. Everything else in the P3 entry checklist is
done, including the desktop shell.

Two carried follow-ups, both recorded in ai/TASKS.md and both unblocked by work
already landed:

- Validation of Python runs still answers a clear 400 "not supported yet". The
  hard sandbox (P3-SEC-001) makes re-execution safe, so the gate itself is now
  implementable: rerun the stored script in the sandbox and compare the result
  shape, the way SQL validation compares rows.
- No single-dataset delete endpoint, so nothing can walk a case backwards. It
  would also make the derived workflow stage's "moves back" property
  observable (P3-FLOW-004 follow-up).

Contextual AI (roadmap item 7) remains BLOCKED on the user setting
`DAH_LLM_API_KEY`; not an agent task.

## Important context

- Server venv: server/.venv (Python 3.14). There is no `pip` module - install
  with `uv pip install --python .venv/bin/python <package>`; PyPI is reachable.
- LLM config: `server/.env` is auto-loaded at server startup (see
  `docs/LLM Configuration.md`), so `uvicorn app.main:app` alone picks up
  DAH_LLM_API_KEY / DAH_LLM_BASE_URL / DAH_LLM_MODEL. The load is skipped under
  pytest so a configured key never makes test-time live calls; an exported
  variable always overrides the file.
- Run tests: `cd server && .venv/bin/python -m pytest -q`
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
