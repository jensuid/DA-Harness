# DAH - Task Archive

Completed task contracts and their done-records, moved out of `ai/TASKS.md` by
the rolling-window rule in `AGENTS.md`. Nothing is edited on the way in - these
are the records as they were written, in their original order. `ai/TASKS.md`
holds the phase summary tables, the still-open carried follow-ups and the
rolling window (the two most recent tasks); everything else is here.

---

### P2-DATA-006 contract

```
TASK ID: P2-DATA-006
MILESTONE: P2 MVP
CAPABILITY: Data Layer (breadth)
GOAL: Accept Parquet and Excel in addition to CSV.

CONTEXT: CSV attach works; profile_csv handles any tabular file DuckDB reads.
INPUTS: multipart upload (.csv/.parquet/.xlsx).
RELEVANT FILES: server/app/main.py, models.py, tests/test_datasets.py
REQUIRED CHANGE: accept the two new extensions; store with a format field.
NON-GOALS: profiling depth (P2-DATA-007), schema detection heuristics, UI.
CONSTRAINTS: read via DuckDB throughout - one engine, one path.
ACCEPTANCE CRITERIA:
- [x] .parquet and .xlsx attach and are stored
- [x] each profiles correctly (rows/columns) via the existing profile endpoint
- [x] unsupported extension rejected with 400
TESTS: golden parquet, golden xlsx, unsupported type.
VERIFICATION: pytest + in-process round-trip.
STATE UPDATE: mark P2-DATA-006 done on pass.
```

### P2-DATA-007 contract

```
TASK ID: P2-DATA-007
MILESTONE: P2 MVP
CAPABILITY: Data Layer (depth)
GOAL: Deepen the profile so it carries what an analyst (and later the AI planner)
      needs before writing a query.

CONTEXT: csv/parquet/xlsx all attach and profile (rows/columns/null counts).
         The profile is the input to the AI planning step, so it has to describe
         the data, not just count rows.
INPUTS: an attached, profiled dataset (any supported format).
RELEVANT FILES: server/app/analysis.py, models.py, main.py, db.py,
                tests/test_profiles.py
REQUIRED CHANGE: extend the profile with
  - per column: inferred DuckDB type, null count, null percentage, distinct count
  - per numeric column: min, max, average
  - per dataset: duplicate row count (total rows minus distinct rows)
NON-GOALS: no visualization, no AI interpretation, no UI, no heuristic schema
           repair, no per-value histograms.
CONSTRAINTS: read via DuckDB throughout - one engine, one path; every new
             stat must survive across formats (csv/parquet/xlsx); the existing
             validation null_count sum must keep working unchanged.
ACCEPTANCE CRITERIA:
- [x] every column reports type, null_count, null_percentage, distinct_count
- [x] numeric columns report min/max/avg
- [x] duplicate row count is reported and correct
- [x] empty (header-only) datasets profile without error
- [x] existing profiles and the validation gate still pass
TESTS: numeric stats; type inference; distinct counts; duplicate rows;
       header-only dataset; full regression suite.
VERIFICATION: pytest + in-process round-trip.
STATE UPDATE: mark P2-DATA-007 done on pass.
```

### P3-SEC-001 contract

```
TASK ID: P3-SEC-001
MILESTONE: P3 V1
CAPABILITY: Analysis Workspace (hardening)
GOAL: Move Python execution out of the API process and under an OS-level
      sandbox.

CONTEXT: P2-ANALYSIS-008 shipped an in-process soft sandbox (import allowlist,
         restricted builtins, dunder-hardened handle, CPU/wall-clock limits).
         It stops accidental damage, not a determined escape, and a crash or
         unbounded allocation in user code hits the API process itself.
INPUTS: an attached dataset and a user Python script (unchanged API).
RELEVANT FILES: server/app/python_exec.py, server/app/python_worker.py (NEW),
                server/app/main.py (unchanged), server/tests/test_python_hard_sandbox.py (NEW)
REQUIRED CHANGE: execute user code in a child process; on macOS wrap it with
         sandbox-exec under a profile that denies every filesystem write
         outside the run's scratch directory and denies all network access;
         scrub the child environment so API-process secrets never reach it;
         bound wall clock at the process-group level (kill the tree, not just
         the wrapper) and keep the in-process guards as defense in depth.
NON-GOALS: Linux landlock / Windows job-object sandboxes (the separate process
           plus inner guards remain the floor on those hosts); address-space
           caps (macOS rejects useful RLIMIT_AS values); validation of Python
           runs by re-execution.
CONSTRAINTS: the /runs/python contract is unchanged - same request, same
             response, same 400 messages; existing tests must pass unmodified.
ACCEPTANCE CRITERIA:
- [x] user Python runs in a process separate from the API
- [x] on macOS the child is under sandbox-exec; a write outside scratch and a
      network connection are denied by the kernel
- [x] an unbounded loop ends at the time limit and the API answers 400
- [x] a worker that dies is reported as 400, never raised into the API
- [x] API-process environment secrets are absent from the child environment
- [x] full server suite and the P2 gate still pass
TESTS: seatbelt enforcement probe (scratch write allowed, outside write and
       network denied), child env scrub, process-group kill, runaway loop,
       dead worker, contract violation.
VERIFICATION: pytest + verification/p2/verify_p2.py regression.
STATE UPDATE: mark P3-SEC-001 done on pass.
```

### P3-CHART-002 contract

```
TASK ID: P3-CHART-002
MILESTONE: P3 V1
CAPABILITY: Analysis Workspace (raster charts)
GOAL: Render charts as PNG behind the same interface, for consumers that need
      a bitmap rather than vector markup.

CONTEXT: P2-ANALYSIS-009 renders deterministic, dependency-free SVG. SVG stays
         the default; raster is an opt-in format on the same endpoint.
INPUTS: a persisted run result plus chart parameters, now including `format`.
RELEVANT FILES: server/app/charts.py, server/app/main.py, server/app/models.py,
                server/app/exporter.py, server/pyproject.toml,
                server/tests/test_charts_raster.py (NEW)
REQUIRED CHANGE: split render_chart into a shared ChartModel (one geometry, one
         category order, one bar geometry) plus two backends; add the PNG
         backend with Pillow, drawn at 2x and LANCZOS-downscaled; thread
         `format` through ChartCreate, the create endpoint, the artifact
         extension, and the served media type (sniffed from stored bytes so old
         rows stay correct); carry binary artifacts through the export/import
         package as base64 with an explicit format (legacy `svg` text field
         kept for older consumers); declare the `charts` optional dependency.
NON-GOALS: new chart kinds, interactive charts, font/vector improvements, a
           Linux-only raster path.
CONSTRAINTS: the SVG path stays dependency-free and byte-identical to before;
             the PNG path is deterministic (same input -> identical bytes).
ACCEPTANCE CRITERIA:
- [x] `format=png` yields a real, decodable PNG of the requested size
- [x] the same input renders byte-identical PNGs across calls
- [x] bar geometry carries over: taller bars top out higher, bars sit on the
      zero baseline, every category gets a bar on canvas
- [x] multi-series charts draw in more than one series colour
- [x] unknown format and unknown kind are both 400s
- [x] the API stores a .png artifact and serves it as image/png
- [x] export/import round trips PNG bytes losslessly and serves them again
- [x] SVG charts are unchanged; full suite and the P2 gate still pass
TESTS: 9 raster tests - real image, determinism, bar geometry by pixel scan,
       multi-series, rejections, SVG default, PNG and SVG API round trips.
VERIFICATION: pytest (94 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-CHART-002 done on pass.
```

### P3-DATA-003 contract

```
TASK ID: P3-DATA-003
MILESTONE: P3 V1
CAPABILITY: Data Layer (multi-dataset)
GOAL: Let one analysis run join several attached datasets.

CONTEXT: attaching several datasets per case already worked (the datasets table
         is case-scoped); the query layer bound every placeholder to a single
         file, so joins across attached files were impossible.
INPUTS: a case, two or more attached datasets, and one SQL statement with one
        placeholder per dataset.
RELEVANT FILES: server/app/analysis.py, server/app/main.py, server/app/models.py,
                server/app/db.py, server/app/exporter.py,
                server/tests/test_multi_dataset_runs.py (NEW)
REQUIRED CHANGE: run_query_multi binds the k-th placeholder to the k-th dataset
         positionally; new POST /cases/{id}/runs endpoint; runs store
         dataset_ids_json alongside the single dataset_id kept as the primary;
         validation re-runs through the multi path; duplicate remaps the list to
         the copy's own datasets; export/import carries it as a JSON list.
NON-GOALS: cross-case datasets, a join builder UI, multi-dataset Python runs
           (the Python handle stays single-dataset - documented).
CONSTRAINTS: the single-dataset endpoints and their responses are unchanged;
             placeholder count must equal dataset count (a mismatch is a 400,
             never a guess); the read-only gate and row cap apply unchanged.
ACCEPTANCE CRITERIA:
- [x] a join across two attached files returns correct results
- [x] binding is positional - swapping the dataset list changes which file each
      placeholder reads
- [x] placeholder/dataset count mismatch, unknown dataset, and duplicate ids are
      clean 400/404s
- [x] multi runs are read-only and reopen/list with their dataset list
- [x] a finding on a join run validates (reproduces) through the multi path
- [x] duplicating a case repoints the copied run at the copied datasets
- [x] export/import round trips a join run with its dataset list
- [x] full suite and the P2 gate still pass
TESTS: 10 tests - join correctness, positional binding, count mismatch, unknown
       dataset, uniqueness, read-only, reopen/list, finding validation,
       duplicate remap, export round trip.
VERIFICATION: pytest (104 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-DATA-003 done on pass.
```

### P3-FLOW-004 contract

```
TASK ID: P3-FLOW-004
MILESTONE: P3 V1
CAPABILITY: Analysis workflow (guided)
GOAL: Tell the analyst where they are in the loop and what to do next.

CONTEXT: every stage of the core loop already had an endpoint, but nothing
         reported which stage a case was in, so the UI could not guide and the
         analyst had to hold the sequence in their head.
INPUTS: a case id.
RELEVANT FILES: server/app/workflow.py (NEW), server/app/main.py, models.py,
                server/tests/test_workflow.py (NEW)
REQUIRED CHANGE: derive the stage from the artifacts a case actually has
         (datasets, profiles, plans, runs, charts, findings, validated findings)
         rather than storing it; expose GET /cases/{id}/progress returning the
         current stage, the completed stages, the single next action, the
         endpoint that performs it, artifact counts, and whether the trust loop
         has closed.
NON-GOALS: storing stage state (by design), UI, recommendations from the LLM
           (deterministic only - the LLM path waits on DAH_LLM_API_KEY), a
           dataset-delete endpoint (surfaced as a follow-up below).
CONSTRAINTS: no schema change - the stage is a pure function of the data, so it
             can never claim a step the artifacts do not support, and deleting
             an artifact would move a case back without a migration.
ACCEPTANCE CRITERIA:
- [x] a fresh case reports stage=data with the attach action and endpoint
- [x] walking the whole loop ends at stage=validated, loop_closed, no next action
- [x] the profile stage only closes when every attached dataset is profiled
- [x] progress is recomputed per request and never leaks across cases
- [x] unknown case answers 404
- [x] full suite and the P2 gate still pass
TESTS: 5 tests - start state, full-loop advance, partial profiling, per-request
       derivation and case scoping, 404.
VERIFICATION: pytest (109 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-FLOW-004 done on pass.

FOLLOW-UP (not this task): there is no DELETE endpoint for a single dataset, so
nothing can currently walk a case backwards. Adding one (cascade to its runs,
charts and anchored findings, or refuse with 409 while runs exist) is what makes
the derived stage's "moves back" property observable.
```

### P3-ANALYSIS-005 contract

```
TASK ID: P3-ANALYSIS-005
MILESTONE: P3 V1
CAPABILITY: Analysis Workspace (richer EDA)
GOAL: Answer "what should I look at first" without writing a query.

CONTEXT: profiling describes a dataset and runs answer a specific question,
         but the step between them - segmentation, correlation, distribution -
         had no surface, so the analyst re-derived common SQL by hand.
INPUTS: an attached dataset, an op name, and its column parameters.
RELEVANT FILES: server/app/eda.py (NEW), server/app/main.py, models.py,
                server/tests/test_eda.py (NEW)
REQUIRED CHANGE: compile each op to a read-only DuckDB statement and run it
         through the same run_query - one engine, one gate, one row cap; expose
         POST /cases/{id}/datasets/{id}/eda returning the standard result shape.
NON-GOALS: persisting EDA as evidence (a finding must anchor on a query the
           analyst wrote), formal hypothesis tests (need a stats story of their
           own), charts from EDA (the result shape already feeds the chart
           endpoint through a run).
CONSTRAINTS: column names are quoted and refused if they contain a quote;
             unknown op/column and missing parameters are 400s; results are
             read-only and row-capped like any query.
ACCEPTANCE CRITERIA:
- [x] segment reports rows/mean/median/min/max/stddev per category
- [x] correlate reports Pearson r and paired row count
- [x] distribution reports the numeric spread, and falls back to top values for
      a categorical column
- [x] unknown op, unknown column, and missing parameter are clean 400s
- [x] a quote-bearing column name cannot reach the SQL
- [x] full suite and the P2 gate still pass
TESTS: 9 tests - segment, correlate, numeric and categorical distribution, and
       six error cases.
VERIFICATION: pytest (118 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-ANALYSIS-005 done on pass.
```

### P3-EVIDENCE-006 contract

```
TASK ID: P3-EVIDENCE-006
MILESTONE: P3 V1
CAPABILITY: Evidence (richer lineage)
GOAL: Show every claim in a case and what it rests on.

CONTEXT: the single-finding chain (`GET .../findings/{id}/evidence`) answers
         "what backs this claim"; nothing answered the case-level question a
         reviewer asks: which claims exist, what each rests on, and does every
         one trace back to stored data.
INPUTS: a case id.
RELEVANT FILES: server/app/evidence.py (NEW), server/app/main.py, models.py,
                server/tests/test_evidence_graph.py (NEW)
REQUIRED CHANGE: project the case into a graph - nodes for datasets, runs,
         charts, plans and findings; edges for how each was derived
         (anchored_on / queries / rendered_from / planned_from); a per-claim
         trace walking finding -> run -> dataset(s); orphan findings listed
         rather than hidden. Exposed as GET /cases/{id}/evidence-graph.
NON-GOALS: storing the graph (it is a pure projection of the persisted rows),
           visual rendering, cross-case lineage.
CONSTRAINTS: read-only; every edge must connect nodes that exist; a case with
             no artifacts answers 400 rather than returning an empty diagram.
ACCEPTANCE CRITERIA:
- [x] the graph covers every artifact kind with correct counts
- [x] edges describe derivation and all connect real nodes
- [x] a claim's trace reaches the dataset it stands on
- [x] a join run's trace covers every dataset it bound
- [x] a claim anchored on nothing is reported as an orphan with reaches_source
      false, never hidden
- [x] an artifact-free case answers 400; unknown case answers 404
- [x] full suite and the P2 gate still pass
TESTS: 7 tests - coverage, edge relations, single and multi-dataset traces,
       orphan reporting, empty case, 404.
VERIFICATION: pytest (125 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-EVIDENCE-006 done on pass.
```

### P3-CASE-007 contract

```
TASK ID: P3-CASE-007
MILESTONE: P3 V1
CAPABILITY: Analysis Case (reuse)
GOAL: Make a finished investigation reusable: find a case again, see what
      happened in it, and start a new one from its shape.

CONTEXT: P2 proved the loop and P3 widened it, but nothing helps the analyst
         the *second* time through. Cases accumulate with no way to find one,
         no way to see what was done without opening every artifact, and no
         way to start a new case shaped like a previous one.
INPUTS: an existing case (for history and templates); a search term (for
        listing).
RELEVANT FILES: server/app/history.py (NEW), server/app/main.py,
                server/app/models.py, server/app/db.py,
                tests/test_case_history.py (NEW),
                tests/test_case_templates.py (NEW),
                tests/test_cases.py (search)
REQUIRED CHANGE:
  - search: optional `q` on GET /cases, case-insensitive substring over the
    question and the dataset label, with LIKE wildcards in the term treated as
    literals; absent or blank `q` lists everything
  - history: GET /cases/{id}/history - a timeline derived from each artifact's
    own timestamp (datasets, profiles, plans, runs, charts, findings), a
    read-side projection like the evidence graph; a finding's validation status
    rides along as its event detail because validation has no persisted
    timestamp of its own
  - templates: a `templates` table (id, name, question, dataset, created_at)
    created with IF NOT EXISTS so older databases need no migration;
    POST /cases/{id}/template (promote, name defaults to the question),
    GET /templates (newest first), POST /cases/from-template (with optional
    question/dataset overrides), DELETE /templates/{id}
NON-GOALS: template categories or tagging, template versioning, sharing
           templates across installs (export/import already moves whole
           cases), full-text search across artifact bodies (the search covers
           case-level fields only), a history UI.
CONSTRAINTS: history and search are pure reads - no schema change for either,
             so the timeline cannot drift from the persisted rows; templates
             are not case children, so deleting a case leaves its template and
             deleting a template leaves its cases; existing endpoints and their
             responses are unchanged.
ACCEPTANCE CRITERIA:
- [x] `q` filters case-insensitively on question and dataset; a blank or absent
      `q` lists every case
- [x] `%` and `_` in a search term are literals, never wildcards
- [x] the history covers every artifact kind in chronological order and is
      recomputed per request, never leaking across cases
- [x] a just-created case has exactly one event; an unknown case answers 404
- [x] a promoted template keeps question and dataset label only - no data,
      runs or findings are copied
- [x] a templated case starts clean and accepts inline overrides
- [x] a template survives its source case; deleting a template leaves the
      cases it seeded untouched
- [x] full suite and the P2 gate still pass
TESTS: 20 tests - 4 search (question, dataset label, wildcard escaping,
       no-filter paths), 6 history (fresh case, full-loop ordering, event
       details, validation status, case scoping, 404), 10 templates (default
       and explicit name, empty name 400, 404s, newest-first listing, clean
       start, overrides, survives source case, delete with cascades).
VERIFICATION: pytest (145 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-CASE-007 done on pass.
```

### P3-SHELL-008 contract

```
TASK ID: P3-SHELL-008
MILESTONE: P3 V1
CAPABILITY: Desktop shell
GOAL: DAH becomes a double-clickable app instead of two terminals, without
      changing the frontend or the core.

CONTEXT: P0-P3 built a browser-served UI over a FastAPI core. Everything works,
         but starting it means running a Python server and a vite dev server.
         DEC-001 said the Tauri host would wrap the same React bundle post-MVP;
         this is that step.
INPUTS: the existing web/ React bundle (unchanged), server/ (unchanged),
        a Rust toolchain + npm.
RELEVANT FILES: desktop/ (NEW: package.json, README.md, .gitignore,
                src-tauri/{Cargo.toml,Cargo.lock,build.rs,tauri.conf.json,
                capabilities/default.json,icons/,src/main.rs,src/core_server.rs}),
                server/app/supervisor.py (NEW), server/dah_core_main.py (NEW),
                server/dah-core.spec (NEW), server/build_sidecar.sh (NEW),
                server/tests/test_supervisor.py (NEW),
                server/app/main.py (watchdog start), web/package.json
                (build:desktop + build:desktop:watch), web/vite.config.ts
                (dev port pinned to 5273), .gitignore (web/dist-desktop/,
                server/build/)
REQUIRED CHANGE:
  - host swap only: the shell serves the same React bundle the browser host
    serves, and the bundle keeps talking to the same FastAPI core over HTTP
  - the shell spawns the core (the packaged PyInstaller sidecar when present,
    server/.venv's uvicorn in a dev checkout; DAH_DEV_CORE=1 forces dev),
    waits for GET /health before showing the window, and stops the core when
    the window closes or the app exits
  - the core cannot be orphaned: process-group kill handles the PyInstaller
    bootloader's forked child, and a parent-pid watchdog in the core ends it
    when the shell dies without running any cleanup (a SIGKILL reaches neither
    a destructor nor a Tauri event)
  - per-user data dir (DAH_DATA_DIR/DAH_DB_PATH) so a packaged app keeps its
    cases in app support, not next to the binary
  - the webview loads only the embedded bundle (no remote URL), so the
    capability file grants nothing but core:default
NON-GOALS: signing/notarization (P5), a Windows/Linux build (needs its own
           icon set and sidecar triple), frontend changes, a one-dir
           PyInstaller build (would cut the 40s one-file unpack; deferred
           because it changes how externalBin addresses the binary).
CONSTRAINTS: no frontend or core behaviour changes; the browser host keeps
             working exactly as before; the 85MB sidecar is gitignored and
             never committed.
ACCEPTANCE CRITERIA:
- [x] the packaged app opens a window whose webview renders the real DAH UI,
      with the core answering /health, and closing the window stops the core
- [x] a debug build serves the embedded bundle - no devUrl that can point the
      webview at a port nothing is serving
- [x] SIGKILL of the shell frees port 8123 (the watchdog), so the next launch
      is not left looking dead
- [x] cargo test: 5 unit + 2 e2e (live uvicorn through the resolver, and the
      sidecar path asserting no orphan)
- [x] server suite (155) and web suite (2) unchanged; P2 gate PASS
TESTS: 7 Rust tests - resolution for both hosts, the DAH_DEV_CORE override, the
       health URL, the silent-port gate, a live dev core answering /health, and
       the sidecar stopping without orphaning its forked child. Plus 7 Python
       tests for the supervisor watchdog (two live process tests).
VERIFICATION: cargo test --features e2e; pytest 155 passed; the P2 gate PASS
              with all 18 steps green; manual: window renders, /health 200,
              window-close and SIGKILL both free the port.
STATE UPDATE: mark P3-SHELL-008 done on pass.

### P3-DATA-009 contract

```
TASK ID: P3-DATA-009
MILESTONE: P3 V1
CAPABILITY: Dataset lifecycle
GOAL: Walk a case backwards - remove one dataset without destroying the case -
      so a wrong file can be dropped and replaced.

CONTEXT: Cases can be created, duplicated, and deleted wholesale, and runs can
         be deleted... but nothing can remove a single dataset. An analyst who
         attaches the wrong CSV has to throw the whole case away and rebuild
         it. P3-FLOW-004 derives the workflow stage from the artifacts a case
         has, so removing a dataset is also the only way to observe the stage
         moving backwards.
INPUTS: an existing case with at least one attached dataset.
RELEVANT FILES: server/app/main.py (the endpoint + the run-touches check),
                server/tests/test_dataset_delete.py (NEW)
REQUIRED CHANGE:
  - DELETE /cases/{case_id}/datasets/{dataset_id} removes the dataset row, its
    profile, its plans, and its on-disk file; the case, other datasets and
    every unrelated artifact survive. 204 on success, 404 for an unknown case
    or dataset.
  - It REFUSES with 400 while any run still touches the dataset - a run is the
    evidence a finding and a chart stand on (the evidence chain is
    finding -> run -> dataset), so removing a dataset that a run binds would
    leave a dangling trace. The refusal names how many runs block it. The check
    covers both runs.dataset_id and runs.dataset_ids_json, because a
    multi-dataset run (P3-DATA-003) binds several datasets at once.
  - Deleting the last dataset is allowed and leaves an empty-but-valid case.
NON-GOALS: cascade deletion of runs/findings/charts (that is what
           DELETE /cases/{id} is for - silently destroying evidence is not
           this endpoint's job), a soft-delete/trash bin, undo, batch delete.
CONSTRAINTS: no schema change, no change to any existing endpoint or response;
             the on-disk file must go with the row, so no orphaned storage.
ACCEPTANCE CRITERIA:
- [x] the dataset row, its profile and its plans are gone; the file on disk is
      gone; the case and every other dataset and artifact are byte-identical
- [x] a run touching the dataset (single-dataset or multi-dataset) blocks
      deletion with a 400 that names the blocker count; deleting the run frees
      it
- [x] deleting the last dataset leaves a valid empty case that still accepts a
      new dataset and a fresh profile
- [x] 404 for an unknown case and for an unknown dataset; a dataset in another
      case is not reachable through this endpoint
- [x] full suite and the P2 gate still pass
TESTS: 8 tests - happy path with a sibling dataset untouched, profile + plans
       removed, file removed, blocked by a single-dataset run, blocked by a
       multi-dataset run, unblocked after the run goes, last-dataset case,
       404s (unknown case, unknown dataset, cross-case dataset).
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-DATA-009 done on pass.
```

### P3-VALID-010 contract

```
TASK ID: P3-VALID-010
MILESTONE: P3 V1
CAPABILITY: Validation
GOAL: Close the last gap in the trust loop - a finding built on a Python run
      can now be validated, not just assumed.

CONTEXT: Validation reruns a finding's stored computation and compares it to
         the persisted result. SQL runs have had that since P1; Python runs
         answered a flat 400 "not supported yet" because re-executing user
         script in-process was unsafe. P3-SEC-001 changed that: the script now
         runs in a separate, OS-sandboxed process with a scrubbed environment,
         so re-execution carries no more risk than the original run.
INPUTS: a finding whose run has kind=python.
RELEVANT FILES: server/app/main.py (validate_finding's Python branch +
                the two reproduction helpers), server/tests/test_validation.py
                (NEW, or extended if it exists)
REQUIRED CHANGE:
  - validate_finding reproduces a Python run by re-executing the stored code
    through run_python against the stored dataset and comparing the tabulated
    columns AND rows to what the run persists - the same reproducibility check
    SQL gets.
  - A script that no longer runs (changed data, a now-broken assumption, a
    time limit) is a FAILED reproducibility check with the reason in its
    detail, never a 500 - mirroring how SQL validation treats a query that no
    longer binds.
  - The missing_data and evidence_integrity checks, and the status arithmetic
    (supported / partially_supported / insufficient_evidence), are shared with
    the SQL path unchanged.
NON-GOALS: validating chart rendering, validating plans, a diff view of
           stored-vs-rerun rows, comparing anything but the tabulated result.
CONSTRAINTS: no schema change; the SQL path's behaviour and response shape are
             unchanged; the sandbox posture of run_python is unchanged (this
             task only calls it again).
ACCEPTANCE CRITERIA:
- [x] a finding on a reproducible Python run validates to supported, with a
      reproducibility check that says the rerun matches
- [x] a finding on a Python run whose stored result was tampered with
      validates to not-supported (partially_supported at minimum), with a
      reproducibility check that says the rerun differs
- [x] a finding whose script now raises validates with a failed check and the
      reason in the detail, and the endpoint returns 200 (a verdict, not a 500)
- [x] the SQL validation path still behaves exactly as before
- [x] full suite and the P2 gate still pass
TESTS: 4 tests - reproduces, tampered result is caught, failing script is a
       verdict, and SQL validation is unchanged.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-VALID-010 done on pass.
```

### P3-AI-011 contract

```
TASK ID: P3-AI-011
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 1 of 4: result interpretation)
GOAL: Tell the analyst what a persisted result actually shows, in the language
      of the case's own question, without making them re-derive it.

CONTEXT: The loop can run, chart, validate and export - but reading a result
         still means reading a table. A non-trivial result needs a human to
         re-derive what it says about the question. The planner (P2-AI-011)
         already proved the two-engine pattern: a deterministic engine that is
         always available, and an LLM behind it that degrades to the
         deterministic read on any failure. This is that pattern applied to a
         result instead of to a profile.
INPUTS: a persisted run (SQL or Python), the case's question, and the primary
        dataset's profile.
RELEVANT FILES: server/app/interpreter.py (NEW), server/app/db.py (table),
                server/app/models.py (Interpretation), server/app/main.py
                (endpoints + duplicate/delete), server/tests/test_interpretations.py
                (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/runs/{run_id}/interpret (201) reads the run's own
    persisted columns and rows, the question, the SQL or Python that produced
    it, and the dataset profile, then returns {summary, observations, caveats}
    and persists it as an artifact of the run.
  - GET .../interpret returns the latest, GET .../interpretations the history
    newest first.
  - Two engines behind one interface, exactly as the planner does it:
    `interpret_result` is deterministic and always available, reading the
    result's own numbers (row counts, numeric min/max/mean, the most frequent
    value per text column); `LLMInterpreter` calls the OpenAI-compatible
    endpoint when DAH_LLM_API_KEY is set, schema-validated by this module, and
    any failure - bad JSON, schema violation, network - falls back to the
    deterministic read. `source` records which engine spoke.
  - An interpretation is a child of a run: duplicated with the case (remapped
    to the copy's run ids) and removed with it.
NON-GOALS: finding drafting (slice 2), code generation (slice 3),
           conversational memory (slice 4), streaming, per-row narration,
           interpretation of charts as distinct from the runs behind them.
CONSTRAINTS: every observation must reference a value that is actually in the
             persisted result - the deterministic engine computes from the rows
             and the LLM is prompted with them, so an interpretation can never
             invent a number. The persisted source field always says which
             engine spoke. No existing endpoint or response changes.
ACCEPTANCE CRITERIA:
- [x] a deterministic interpretation is produced with no key configured; its
      summary and observations reference the result's real columns and values
- [x] a configured LLM's valid output is persisted with source=llm
- [x] an LLM that raises, returns malformed JSON, or violates the schema
      falls back to source=deterministic and the endpoint still answers 201
- [x] an interpretation survives a session restart and is retrievable, and the
      history is newest first
- [x] 404 for an unknown case, an unknown run, and a run belonging to another
      case
- [x] duplicating a case copies its interpretations onto the copy's own runs;
      deleting a case removes them
- [x] full suite and the P2 gate still pass
TESTS: 9 tests - deterministic read, real values referenced, LLM persisted,
       LLM failure/malformed/schema-violation fallbacks (3), retrieval across a
       session + newest-first history, 404 contract, duplicate/delete
       survival.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-011 done on pass.
```

### P3-AI-012 contract

```
TASK ID: P3-AI-012
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 2 of 4: finding drafting)
GOAL: Draft the *candidate* finding a result would support, so the analyst
      decides whether it becomes evidence rather than finding out an LLM
      already decided for them.

CONTEXT: Slice 1 (P3-AI-011) reads a result. The next step in the loop is a
         finding - and a finding is the trust artifact: it is what the evidence
         chain, validation and export are built on. So this slice stops one
         step short of it. The LLM drafts; a human accepts; only the acceptance
         writes a row to findings, through the endpoint that already exists.
INPUTS: a persisted run, the case question, and the dataset profile - the same
        inputs interpretation takes, so the two slices compose.
RELEVANT FILES: server/app/drafter.py (NEW), server/app/models.py (DraftFinding),
                server/app/main.py (endpoint), server/tests/test_drafting.py (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/runs/{run_id}/draft-finding (200 - nothing is
    created) returns {statement, interpretation, caveat, grounds, source}.
    `grounds` is the list of values from the result that the statement stands
    on, so a human can check the claim against the numbers.
  - Two engines, one interface, as before: `draft_finding` is deterministic and
    always available - it finds the result's measure and dimension, and states
    which category leads on the measure at what value; `LLMDrafter` calls the
    OpenAI-compatible endpoint when DAH_LLM_API_KEY is set.
  - Honesty is enforced, not hoped for: every number the LLM quotes in its
    statement or its grounds must be a value the result actually contains (a
    cell, the row count, or a derived count). An invented magnitude is a
    validation failure and the draft falls back to the deterministic one.
  - Drafting writes no state. Accepting a draft is a POST to the existing
    /findings endpoint - the only path that creates a finding.
NON-GOALS: persisting drafts (a draft is a proposal, not state; rejected drafts
           are deliberately not kept), batch drafting, drafting from a chart,
           accepting a draft in one call (acceptance is the existing endpoint,
           so the human-owns-the-finding property is structural, not a flag).
CONSTRAINTS: the findings table is untouched by this task - same schema, same
             endpoints, same responses. No existing behaviour changes.
ACCEPTANCE CRITERIA:
- [x] a deterministic draft is produced with no key; statement, interpretation
      and caveat are non-empty and it names the run's real columns
- [x] every value in grounds appears in the result's rows or columns
- [x] an LLM draft quoting only real values is returned with source=llm
- [x] an LLM draft that invents a magnitude falls back to source=deterministic
- [x] an LLM that raises or returns malformed output falls back
- [x] drafting leaves the findings table empty - nothing is created
- [x] a draft's statement is accepted through the existing findings endpoint,
      lands as a real finding, and validates
- [x] a result with no numeric column still yields an honest weaker draft
- [x] 404 for unknown case, unknown run, and a cross-case run
- [x] full suite and the P2 gate still pass
TESTS: 10 tests - deterministic draft, grounds are real, LLM accepted, invented
       magnitude rejected, LLM failure and malformed fallbacks, no state
       written, accept-then-validate round trip, no-numeric-column result, 404s.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-012 done on pass.
```

### P3-AI-013 contract

```
TASK ID: P3-AI-013
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 3 of 4: code generation)
GOAL: Describe what you want to know; the harness proposes the read-only
      computation that would answer it. The analyst decides whether it runs.

CONTEXT: Slices 1 and 2 read a result and draft the finding it would support.
         The step before either is the analysis itself, and writing SQL or
         Python is the part of the loop a non-programmer analyst cannot do
         alone. So this slice generates the code - and stops one step short of
         running it, exactly as drafting stops one step short of a finding.
INPUTS: a question in plain language, a dataset profile (columns, types, nulls),
        and the desired kind (sql | python).
RELEVANT FILES: server/app/generator.py (NEW), server/app/models.py
                (GeneratedCode), server/app/main.py (endpoint),
                server/tests/test_code_generation.py (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/datasets/{dataset_id}/generate-code (200 - nothing is
    created) with {question, kind?} returns {kind, code, explanation,
    columns_used, source}.
  - Two engines, one interface, as before: `generate_code` is deterministic and
    always available - it picks the profile's first numeric measure and its
    first categorical (or temporal) dimension and writes a GROUP BY
    aggregation, or a count-by-dimension query when there is no measure;
    `LLMGenerator` calls the OpenAI-compatible endpoint when DAH_LLM_API_KEY
    is set.
  - Honesty is enforced, not hoped for: every column the generated code
    references must be a column the dataset actually has. An invented column is
    a validation failure and the proposal falls back to the deterministic one.
    Safety likewise: a generated SQL proposal that is not a single read-only
    statement is rejected, not handed to the analyst.
  - Generation writes no state. Running a proposal is a POST to the existing
    runs endpoint (`/runs` for sql, `/runs/python` for python) - the only path
    that persists a run, so the human decides what executes.
NON-GOALS: executing generated code from this endpoint (it proposes; the
           existing endpoints run), generating joins or multi-dataset queries,
           generating chart or finding artifacts, persisting proposals,
           iterating on a proposal conversationally (slice 4).
CONSTRAINTS: no new table; runs endpoints, schema and responses unchanged.
ACCEPTANCE CRITERIA:
- [x] a deterministic proposal is produced with no key; code, explanation and
      columns_used are non-empty and every column named is a real profile column
- [x] a generated SQL proposal runs as-is through the existing /runs endpoint
- [x] a generated Python proposal runs as-is through /runs/python and tabulates
- [x] the deterministic proposal is a single read-only statement
- [x] an LLM proposal referencing only real columns is returned with source=llm
- [x] an LLM proposal that invents a column falls back to source=deterministic
- [x] an LLM proposal that is not read-only (a DELETE/DROP) falls back
- [x] an LLM that raises or returns malformed output falls back
- [x] generation writes no state - no run is created
- [x] 404 for unknown case, unknown dataset, and a cross-case dataset
- [x] full suite and the P2 gate still pass
TESTS: 13 tests - deterministic SQL, deterministic Python, columns are real,
       LLM accepted, invented column rejected, non-read-only rejected, failure
       and malformed fallbacks, no state written, accept-then-run round trip,
       404s.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-013 done on pass.
```

### P3-AI-014 contract

```
TASK ID: P3-AI-014
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 4 of 4: conversational memory)
GOAL: Ask the case a question in plain language and get an answer grounded in
      what the case actually contains - with the citations to prove it.

CONTEXT: Slices 1-3 propose: a question yields the computation that would
         answer it, a result yields a reading and a candidate finding. Each
         stops one step short of writing state. This slice is the last piece:
         the assistant remembers the conversation and answers from the case's
         own artifacts, so the analyst can ask rather than dig.
INPUTS: a case (its datasets, profiles, runs, findings, plans, charts, derived
        workflow stage), the conversation so far, and a message.
RELEVANT FILES: server/app/assistant.py (NEW), server/app/db.py (table),
                server/app/models.py (ChatRequest, ConversationTurn),
                server/app/main.py (endpoints),
                server/tests/test_conversation.py (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/chat with {message} -> 201
    {id, case_id, message, answer, grounds, source, created_at}.
    GET /cases/{case_id}/chat returns the whole conversation oldest-first, so
    a reopened case resumes mid-thought.
  - `summarize_case` reads the case's rows and builds the facts an answer may
    draw on: datasets with their columns and stats, runs with their columns and
    row counts, findings with their validation status, plans, charts, and the
    derived workflow stage. A pure projection, like the evidence graph and the
    history timeline, so it cannot drift from what is on disk.
  - Two engines, one interface: `answer_question` is deterministic and always
    available - it answers count questions, column and dataset questions, and
    otherwise states where the case stands and the one action that advances it
    (reusing P3-FLOW-004's derived stage); `LLMAssistant` calls the
    OpenAI-compatible endpoint when DAH_LLM_API_KEY is set and receives the
    recent turns as context - that is the memory.
  - Honesty is enforced, not hoped for: every citation in `grounds` must be an
    artifact the case actually has (a dataset, run, finding, plan, chart or
    column that exists). An invented citation is a validation failure and the
    answer falls back to the deterministic one. An answer about a case that has
    artifacts must cite at least one of them.
NON-GOALS: executing analysis from chat (the proposal slices do that; chat
           answers and cites), streaming, multi-case conversations, exporting
           or duplicating a conversation (a duplicate starts a fresh
           investigation), tool calling / function calling.
CONSTRAINTS: no existing endpoint, schema or response changes. The new
             conversations table is created under CREATE TABLE IF NOT EXISTS,
             so older databases need no migration. DELETE /cases/{id} removes a
             case's conversation; nothing else writes to the table.
ACCEPTANCE CRITERIA:
- [x] a deterministic answer is produced with no key; answer and grounds are
      non-empty
- [x] every ground cites an artifact the case actually has
- [x] a "how many" question is answered with the case's real counts
- [x] a question naming a column is answered with that column's real profiled
      stats
- [x] a question about nothing specific is answered with the case's derived
      stage and next action
- [x] an LLM answer citing real artifacts is returned with source=llm
- [x] an LLM answer that invents a citation falls back to source=deterministic
- [x] an LLM that raises or returns malformed output falls back
- [x] the LLM receives the prior turns as context - a second question is
      answered with the first one in view
- [x] the conversation persists across a restart, oldest-first
- [x] deleting the case removes its conversation rows
- [x] 404 for an unknown case (posting and reading)
- [x] full suite and the P2 gate still pass
TESTS: 12 tests - counts, column stats, stage fallback, grounds are real, LLM
       accepted, invented citation rejected, failure and malformed fallbacks,
       memory (prior turn in context), persistence oldest-first, delete
       cleanup, 404s.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-014 done on pass; this closes roadmap item 7.
```

### P4-VERIFY-001 contract

```
TASK ID: P4-VERIFY-001
MILESTONE: P4 Production Candidate
CAPABILITY: Verification (P3 gate)
GOAL: Prove the P3 capabilities work as one journey, not just as separate
      suites.

CONTEXT: the P2 gate re-verifies the test suite, and every P3 task shipped its
         own tests, but nothing walked the P3 surface end to end - multi-dataset
         joins, the OS-level sandbox, the four assistant slices, raster charts,
         the derived workflow and case reuse. A phase is done when a gate says
         so, and P3 had no gate of its own.
INPUTS: none (the gate builds its own data: a CSV and a Parquet written from a
        table, so the join deliberately mixes formats).
RELEVANT FILES: verification/p3/verify_p3.py (NEW),
                verification/p3/REPORT.md (generated), ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE: write verification/p3/verify_p3.py after the P0/P1/P2 gates -
         in-process TestClient, one atomic journey, a step table and an exit
         criteria table in verification/p3/REPORT.md, exit 0 only when every
         step passes. The journey is: question -> attach CSV + Parquet ->
         profile both -> generate-code (writes nothing) -> plan -> join run ->
         hard-sandbox escape attempt refused -> interpret -> draft-finding
         (writes nothing) -> accept through the only endpoint that writes ->
         raster chart -> validation closes the loop -> evidence graph reaches
         both datasets -> workflow reports loop_closed -> chat with citations
         -> EDA -> history -> search -> template outlives the case -> dataset
         deletion blocked by evidence -> export -> import -> join reproduces
         elsewhere -> suite green.
NON-GOALS: new server behaviour (the gate exercises what exists; if the journey
           exposes a bug, that is a separate task), LLM live calls in the
           journey (the gate is hermetic - see CONSTRAINTS), a UI, performance
           measurement (that is the P4 performance task).
CONSTRAINTS: deterministic by construction - app.main loads server/.env at
             import and every assistant engine reads the LLM credentials at
             call time, so the gate scrubs those variables from its own process
             after import and from the pytest subprocess it spawns; the journey
             therefore reports source=deterministic on every assistant step and
             makes no network call. The LLM paths stay covered by the suite,
             which tests both engines explicitly. The journey's data is clean
             (no nulls, no duplicates) so validation reaching `supported` proves
             the join reproduces, not that a messy finding was tolerated.
ACCEPTANCE CRITERIA:
- [x] the gate runs standalone and exits 0 only when every step passes
- [x] the journey joins two attached datasets of different formats in one run
- [x] a sandbox escape attempt is a 400 that leaves no run behind
- [x] each assistant slice fires once, writes nothing where the contract says
      so, and the human-only action (accept the draft) is what creates state
- [x] a finding on the join run validates to supported with the reproducibility
      check passing
- [x] the evidence graph's claim trace reaches both datasets the join bound
- [x] the derived workflow reports stage=validated and loop_closed
- [x] the case survives search, templating (template outlives the case), and an
      export/import round trip that reproduces the join
- [x] dataset deletion is refused while evidence stands on it
- [x] the full server suite passes as the gate's last step
TESTS: the gate itself is the test - 23 journey steps + the 211-test suite.
VERIFICATION: server/.venv/bin/python verification/p3/verify_p3.py -> PASS
      (verification/p3/REPORT.md, all 15 exit criteria PASS).
STATE UPDATE: mark P4-VERIFY-001 done on pass; P4's checklist item 1 is
      complete.
```

### P4-RELIABILITY-002 contract

```
TASK ID: P4-RELIABILITY-002
MILESTONE: P4 Production Candidate
CAPABILITY: Reliability
GOAL: An input error always answers 400 with a reason, and a server failure
      always answers 500 and gets logged - never the other way round.

CONTEXT: five API endpoints (single SQL run, multi SQL run, Python run, EDA,
         chart render) end in `except Exception as error: raise 400`,
         "... failed: {error}". That clause is doing two jobs at once: it is
         the only thing turning a user's SQL syntax error into a 400 (DuckDB
         raises duckdb.Error, which is not a ValueError, so the `except
         ValueError` above it does not catch it), and it is also flattening
         every real server fault - a sqlite error, an unreadable stored file, a
         KeyError in our own code - into a 400 that blames the user. A bug in
         the harness currently looks like bad input, to the analyst and in the
         logs. Separately, the five LLM fallback paths catch `except Exception`
         deliberately - degradation is the contract - but silently, so a bug in
         our own code vanishes into source=deterministic and is never surfaced.
INPUTS: any request to the five engine endpoints, plus the LLM fallback paths.
RELEVANT FILES: server/app/errors.py (NEW), server/app/main.py,
                server/app/planner.py, server/app/interpreter.py,
                server/app/drafter.py, server/app/generator.py,
                server/app/assistant.py,
                server/tests/test_error_semantics.py (NEW)
REQUIRED CHANGE:
  - app/errors.py owns the taxonomy once: INPUT_ERROR_TYPES is the tuple of
    exception families that mean the input cannot be honoured - ValueError
    (every engine's own validation: the read-only gate, unknown columns, a
    sandbox rejection, a missing result) and duckdb.Error (SQL that cannot
    parse or bind, which is not a ValueError). Those answer 400. Everything
    else is a server failure and is let through to FastAPI's 500, which logs
    the traceback instead of hiding it in a 400.
  - the five engine sites become `except INPUT_ERROR_TYPES as error:
    raise 400`; the broad clause goes away. The chart site keeps ValueError
    alone, because render_chart validates everything itself and raises
    ValueError for all of it.
  - the five LLM fallbacks stay broad - an unavailable or misbehaving LLM may
    never block the loop - but the reason is logged at warning level, so a
    fallback caused by our own bug is visible instead of silent.
NON-GOALS: changing any success-path behaviour or response shape; touching the
           validation endpoints, whose `except (ValueError, Exception)` is
           correct - a finding that no longer reproduces must answer 200 with a
           failed check, never a 500; rewriting the duckdb error text; a global
           error handler or structured logging framework (that is observability,
           a later P4 item); the two `referenced run/dataset is missing` 500s
           and the plan-validation 500, which are integrity violations the
           server allowed and where 500 is the honest answer.
CONSTRAINTS: no existing endpoint contract changes - every request that
             answers 400 today still answers 400, with the engine's own message
             rather than the generic "X failed: ..." wrapper; the LLM
             degradation contract is unchanged (any failure still falls back).
ACCEPTANCE CRITERIA:
- [x] SQL that cannot parse, and SQL naming an unknown column, answer 400 with
      the engine's message - narrowing the catch did not make bad input a 500
- [x] a sandbox rejection (script with no result, write attempt) still answers
      400
- [x] an injected server-side fault in each of the five engines answers 500
      instead of a 400 that blames the input
- [x] an LLM that raises anything - expected or not - still falls back to
      source=deterministic, and the reason is logged
- [x] no success path changed; full suite, the P2 gate and the P3 gate pass
TESTS: server/tests/test_error_semantics.py - bad SQL (syntax and unknown
       column), injected 500s for all five engines (run_query, run_query_multi,
       run_python, run_eda, render_chart), and the LLM fallback on an
       unexpected error type. Uses a TestClient with raise_server_exceptions
       off, which is the only way a 500 is observable in process.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS +
              verification/p3/verify_p3.py PASS.
STATE UPDATE: mark P4-RELIABILITY-002 done on pass.
```

### P4-UX-003 contract

```
TASK ID: P4-UX-003
MILESTONE: P4 Production Candidate
CAPABILITY: UX (case workspace + chat)
GOAL: DAH can be *used* from the shell, not only from curl: find a case, open
      it, see where it stands, and ask it a question.

CONTEXT: the React bundle still shows the P0/P1 surface - one case-creation
         form. Every P3 capability - the derived workflow, the evidence graph,
         the four assistant slices - is reachable only through the API. The
         assistant surfaces need somewhere to live, so the workspace comes
         first; chat is the one assistant slice that needs nothing but a case,
         and its citations are the honesty property the UI should make visible.
         The run-scoped slices (interpret, draft-finding, generate-code) need a
         run-selection surface and are P4-UX-004.
INPUTS: a case id; a chat message.
RELEVANT FILES: web/src/api.ts, web/src/App.tsx, web/src/CaseList.tsx (NEW),
                web/src/CaseWorkspace.tsx (NEW), web/src/CaseCreation.tsx,
                web/src/index.css, web/src/CaseList.test.tsx (NEW),
                web/src/CaseWorkspace.test.tsx (NEW)
REQUIRED CHANGE:
  - api.ts becomes a typed client over the real contracts: GET /cases (with
    q), GET /cases/{id}, GET .../progress, GET .../datasets, GET .../runs,
    POST + GET .../chat. One shared request() throws an ApiError carrying the
    status and a message parsed from the body only when the body is JSON - a
    500 answers plain text (P4-RELIABILITY-002), and res.json() on it must not
    become a second, hiding failure.
  - CaseList lists cases with a literal-substring search box; opening one
    navigates to the workspace. CaseCreation survives as the way a new case
    starts, and creating one opens it.
  - CaseWorkspace shows the question, the derived stage and single next action
    (progress is recomputed on open, so the UI can never show a stage the data
    does not support), the attached datasets, the runs with their kind and row
    counts, and the chat panel: a message box, the answer, each ground rendered
    as a citation chip, and a badge for which engine spoke (source). Prior
    turns load oldest-first, so a reopened case resumes mid-thought.
  - App.tsx owns state-based navigation - list, workspace, create - with no
    router dependency, keeping the bundle dependency-free as DEC-001 intends.
NON-GOALS: the run-scoped assistant surfaces (P4-UX-004); running queries or
           accepting drafts from the UI (those still belong to the endpoints
           that write); charts and evidence-graph rendering; styling beyond
           readable; a router or state-management library.
CONSTRAINTS: every screen reads its own data from the API on mount - nothing
             is cached across navigation, so the UI cannot go stale against
             the core; the existing two web tests keep passing; the bundle
             gains no dependency.
ACCEPTANCE CRITERIA:
- [x] cases list, and the search box filters them by the API's q parameter
- [x] opening a case shows its question, its derived stage and next action,
      its datasets and its runs
- [x] a chat message is posted and the answer renders with its grounds as
      citation chips and the engine that spoke
- [x] prior turns load on open, oldest-first
- [x] an API failure renders as readable text and never as a crash; a
      plain-text 500 body does not break the client
- [x] creating a case lands in its workspace
- [x] web tests pass; the server suite and both gates stay green
TESTS: web/src/CaseList.test.tsx and CaseWorkspace.test.tsx - render from
       mocked api responses, search, open, chat round trip with grounds and
       source badge, and an error rendered rather than thrown.
VERIFICATION: cd web && npm test green + the P2/P3 gates as regression.
STATE UPDATE: mark P4-UX-003 done on pass; the run-scoped slices are next.
```

### P4-UX-004 contract

```
TASK ID: P4-UX-004
MILESTONE: P4 Production Candidate
CAPABILITY: UX (run-scoped assistant surfaces)
GOAL: The three remaining assistant slices are reachable from the workspace:
      generate code from a question, read what a run shows, and draft the
      finding it would support - each proposing, none deciding.

CONTEXT: P4-UX-003 gave the shell a case workspace with chat, the one slice
         that needs nothing but a case. The other three are run-scoped: they
         need a dataset to generate against and a run to read or draft from.
         They also need the analyst to be able to attach data, profile it and
         run a query in the first place, or the surfaces have nothing to hang
         on - so the workspace gains the steps the core loop actually walks.
INPUTS: a case; a dataset; a run; a question in plain language.
RELEVANT FILES: web/src/CaseWorkspace.tsx, web/src/api.ts,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - api.ts gains the remaining contracts: attach a dataset, profile one, run
    SQL (single- and multi-dataset), the three assistant calls
    (generate-code, interpret, draft-finding) and the two that accept a
    proposal (POST /findings, POST .../validate).
  - CaseWorkspace becomes the loop the core walks, one panel per step, each
    reading its own data and each proposal surfaced as a decision the human
    makes:
      * Attach + profile: file picker, then profile, then the columns and
        nulls it found;
      * Generate code: a question against a profiled dataset returns code,
        explanation and the columns it reads, with a Run button that posts it
        to the runs endpoint - the only path that persists a run;
      * Runs: each lists its kind and row count, with Interpret (what it
        shows) and Draft finding (what it claims) buttons;
      * A draft renders its statement, interpretation, caveat and grounds,
        and Accept posts it to /findings - the only path that writes one -
        after which Validate reruns the computation and reports the verdict.
  - Every assistant panel shows which engine spoke (source), because a
    deterministic answer citing only real values and an LLM answer carry
    different weight.
NON-GOALS: a SQL editor with highlighting or schema introspection beyond the
           profile; charts in the UI (a later slice); multi-dataset join
           building (the attach UI stays one file at a time; the API still
           accepts a list); streaming; executing generated code without the
           human's explicit Run.
CONSTRAINTS: no server change - every call is an existing endpoint; no new
             runtime dependency; every screen reads its own data after an
             action, so the UI cannot go stale against the core; acceptance
             still goes through the findings endpoint and running still
             through the runs endpoint, so the propose/human-decides split
             stays structural rather than becoming a UI flag.
ACCEPTANCE CRITERIA:
- [x] a dataset attaches and profiles from the UI; the columns and null counts
      it reports are the profile's own
- [x] a question against a profiled dataset returns generated code with its
      explanation and columns used, and the code runs through the runs
      endpoint when the analyst chooses Run
- [x] a run interprets: summary, observations and caveats render, with the
      engine that spoke
- [x] a run drafts a finding: statement, interpretation, caveat and grounds
      render, and Accept creates a real finding (not_evaluated, as the API
      insists)
- [x] a created finding validates and the verdict renders
- [x] no assistant action writes state except through the endpoints that own
      it - generation and interpretation-creation aside, drafting and
      generating create nothing, and a rejected draft leaves nothing behind
- [x] an API failure renders as text, never a crash
- [x] web tests cover each surface; the server suite and both gates stay green
TESTS: web/src/CaseWorkspace.test.tsx extended - attach+profile, generate-code
       round trip with Run, interpret, draft + accept + validate, error
       rendering, no state written by a draft.
VERIFICATION: cd web && npm test green + the P2/P3 gates as regression.
STATE UPDATE: mark P4-UX-004 done on pass; this closes the assistant surfaces
              and roadmap item 3.
```

### P4-VALID-005 contract

```
TASK ID: P4-VALID-005
MILESTONE: P4 Production Candidate
CAPABILITY: Validation (rerun determinism)
GOAL: Validating the same finding twice always gives the same verdict.

CONTEXT: the live-LLM smoke of P4-UX-004 walked the whole loop repeatedly and
         validation started flipping between `supported` and
         `insufficient_evidence` on identical inputs. The cause was in the
         comparison, not the data: DuckDB does not promise a row order for a
         result that never asked for one, and a GROUP BY can return its groups
         in a different order on a different connection (observed: 2 distinct
         orders across 8 reruns of one query). `_reproduce_sql` compared rows
         positionally, so an unordered query validated as a rerun mismatch
         roughly half the time - and a verdict that depends on which
         connection happened to answer is not a verdict at all.
INPUTS: a finding whose run stored an unordered result set.
RELEVANT FILES: server/app/main.py, server/tests/test_validation.py
REQUIRED CHANGE:
  - `_row_key(row)` canonicalises one row as JSON, so the sort key is
    type-aware and deterministic;
  - `_reproduce_sql` compares `sorted(rerun rows) == sorted(stored rows)` - a
    multiset comparison. An SQL result set is a bag of rows; only ORDER BY
    makes it a sequence, and when the query asks for one DuckDB honours it
    deterministically, so the sort is a no-op there and a correction
    everywhere else;
  - `_reproduce_python` is deliberately unchanged: the Python tabulator is
    deterministic and column order is a shape signal (a changed shape is a
    changed result), so positional comparison stays right there.
NON-GOALS: normalising row order at store time; changing the verdict
           vocabulary; touching the null or duplicate checks; any UI change.
CONSTRAINTS: the fix must not weaken the gate - rows that differ as a
             multiset still fail reproducibility, and a query that no longer
             binds still reports a failed check rather than a 500.
ACCEPTANCE CRITERIA:
- [x] a stored result whose rows were deliberately reordered validates
      `supported`
- [x] an unordered GROUP BY validated 12 times returns exactly {"supported"}
- [x] a genuine multiset drift still fails reproducibility (the pre-existing
      drift test, which substitutes a value no rerun can produce)
- [x] the full suite and both the P2 and P3 gates stay green
TESTS: server/tests/test_validation.py +2 - `test_validate_accepts_reordered_unordered_result`
       (verified to FAIL without the fix) and
       `test_validate_unordered_groupby_is_stable_across_reruns` (12 reruns).
VERIFICATION: pytest green (225 passed) + P2/P3 gates PASS.
STATE UPDATE: mark P4-VALID-005 done on pass; a validation verdict no longer
              depends on which DuckDB connection answered.
```

### P4-PERF-006 contract

```
TASK ID: P4-PERF-006
MILESTONE: P4 Production Candidate
CAPABILITY: Performance (large-dataset behaviour)
GOAL: DAH stays responsive on a dataset too large to be a toy, and the
      behaviour that protects memory at scale is measured and pinned rather
      than assumed.

CONTEXT: the 1000-row result cap has existed since P1 and nothing had ever
         been measured at scale - "it probably holds" is not a property. A
         benchmark on a 200k-row / 13.4MB CSV found the real cost: attaching
         and querying were fine (0.2s and 0.8s), export was fine (0.4s,
         17.8MB package, dominated by the dataset bytes), but PROFILING took
         ~6s. Instrumented internally, the cause was exact and wasteful:
         profile_csv ran `SELECT *` and then `fetchall()` on the entire
         dataset purely to read the column description - 2.68s of materialising
         rows that were then thrown away - followed by four separate full
         scans (aggregates, COUNT(*), and duplicate-row count's own COUNT(*)
         plus DISTINCT). The description, names AND inferred types, is
         available with LIMIT 0 and fetches nothing.
INPUTS: a large CSV (100k+ rows); a case with several artifacts.
RELEVANT FILES: server/app/analysis.py, server/tests/test_profiles.py,
                server/tests/test_large_datasets.py (NEW)
REQUIRED CHANGE:
  - profile_csv reads the description via `SELECT * ... LIMIT 0` instead of
    materialising every row;
  - the row total is folded into the single per-column aggregate pass as a
    leading COUNT(*), so the separate COUNT(*) scan is gone;
  - _duplicate_row_count takes the already-known total instead of recounting;
  - the result cap and the truncation flag are exercised at scale, and the
    profile's correctness at scale is pinned by tests.
NON-GOALS: rewriting the profile vocabulary; streaming/async endpoints;
           paginating results; changing the 1000-row cap or the 100MB export
           guard; memory-profiling the Python sandbox worker; chart rendering
           cost.
CONSTRAINTS: the profile output must be byte-for-byte the same shape as
             before (the tests are the proof); correctness must not be traded
             for speed - a wrong fast profile is worse than a slow right one;
             the fix must not depend on file format (csv/parquet/xlsx all
             reach the same code path).
ACCEPTANCE CRITERIA:
- [x] profiling a 200k-row CSV is materially faster than before (measured
      ~6.0s -> ~1.9s, a 3x improvement) with an identical profile output
- [x] a SELECT * run at scale reports row_count=1000 and truncated=true
- [x] the profile at scale reports the right row count, nulls, distinct counts
      and duplicate rows (known-answer data, generated deterministically)
- [x] export on a case carrying a large dataset stays bounded and round-trips
- [x] the existing profile tests (including header-only and parquet/xlsx)
      stay green, and the full suite plus both gates pass
TESTS: server/tests/test_large_datasets.py (NEW) - a deterministic 50k-row
       generator, profile correctness at scale, the result cap truncating a
       full-table query, a wide table (many columns) profiling correctly, and
       the duplicate count on data with known duplicates.
VERIFICATION: pytest green + P2/P3 gates PASS; the benchmark numbers above
              are recorded in ai/CURRENT_STATE.md so the next regression is
              measured against a number, not a feeling.
STATE UPDATE: mark P4-PERF-006 done on pass; roadmap item 4 is measured and
              the profiling hot path is fixed.
```

### P4-CI-007 contract

```
TASK ID: P4-CI-007
MILESTONE: P4 Production Candidate
CAPABILITY: Distribution (CI + signing decision)
GOAL: Every layer is verified by CI on a clean machine, including the desktop
      shell's core lifecycle and the sidecar build, and the app-signing
      question is answered in writing rather than left open.

CONTEXT: P3-SHELL-008 shipped a desktop shell whose lifecycle was only ever
         tested locally - `cargo test --features e2e` spawns the real uvicorn
         and asserts the core answers and then stops, but nothing ran it on a
         fresh checkout. There was also no CI of any kind in the repo: no
         workflow file existed, so the 231 server tests, 17 web tests and 7
         Rust tests were green only because a developer happened to run them.
         Separately, the packaged app is unsigned and the question of when to
         sign was carried from P3 without a decision.
INPUTS: the repo as cloned (no local venv, no built sidecar, no LLM keys).
RELEVANT FILES: .github/workflows/ci.yml (NEW), README.md (NEW),
                ai/DECISIONS.md, server/pyproject.toml, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - .github/workflows/ci.yml: four jobs.
      * server - uv venv from pyproject, pytest, then the P2 and P3 gates
        in-process, with the gate reports uploaded as an artifact.
      * web - npm ci, npm test, npm run build (tsc -b runs first, so a type
        error the jsdom tests cannot see still fails CI).
      * desktop - the server venv at the exact path the resolver looks for,
        then cargo test (unit) and cargo test --features e2e (lifecycle:
        spawn a real core, wait on /health, assert the port is freed).
      * packaging - build the sidecar from declared extras and smoke it: the
        binary must actually serve /health, not merely build.
    macOS-only on purpose: the hard sandbox is macOS seatbelt and the packaged
    app and sidecar are macOS builds; another platform would skip the paths
    that most need exercising. No LLM credentials are ever set, so every
    assistant step is deterministic and the run makes no network call.
  - server/pyproject.toml: two fixes found by validating the install path on a
    clean venv. (1) `[tool.setuptools] packages = ["app"]` - flat-layout
    discovery saw `app` and `tests` as competing top-level packages and failed
    on a fresh checkout; a stale egg-info masked it locally. (2) a `packaging`
    extra declares PyInstaller, which was previously installed ad-hoc and was
    not reproducible.
  - README.md (NEW): the layers and their test commands, and the unsigned-app
    first-launch workaround in plain language.
  - ai/DECISIONS.md DEC-004: signing deferred to P5, with the reason, the
    alternatives considered (ad-hoc signing, xattr bypass), and the
    consequences - including that nothing in P4 may depend on the app being
    signed.
NON-GOALS: the P0 gate in CI (it binds a port and duplicates the later
           gates); Windows/Linux runners; release automation or artifact
           publishing; actually signing or notarizing the app (DEC-004 defers
           it); load/performance testing in CI.
CONSTRAINTS: every command in the workflow was validated by running it
             locally in the order the workflow runs it - the venv install on a
             clean directory, the suite and both gates, npm ci and the build,
             the cargo lifecycle tests, and the sidecar build plus a health
             smoke against the freshly built binary. The workflow must never
             need an LLM key or any other secret (DEC-004 keeps signing out,
             so no identity is required either).
ACCEPTANCE CRITERIA:
- [x] a workflow file exists and is valid YAML, covering server, web, desktop
      and packaging
- [x] the server job installs from pyproject on a clean venv and the suite
      plus both gates pass (231 tests)
- [x] the desktop job runs the two live-core lifecycle tests (7 Rust tests)
- [x] the packaging job builds the sidecar from declared extras and the built
      binary answers /health
- [x] no secret, key or credential is required for any job to pass
- [x] the signing question has a written decision with consequences, and the
      user-facing workaround is documented in the README
- [x] the local suite and both gates still pass on this machine
TESTS: none new - this task's verification is that the existing 231 + 17 + 7
       tests run under the CI it creates, plus a health smoke on the built
       sidecar.
VERIFICATION: validated step by step locally (venv install on a clean
              directory, suite + P2/P3 gates, npm ci + build, cargo test
              --features e2e, build_sidecar.sh + /health smoke); pytest 231
              passed, web 17 passed, cargo 7 passed, both gates PASS.
STATE UPDATE: mark P4-CI-007 done on pass; the P4 checklist's distribution
              item is closed (signing formally deferred to P5 by DEC-004).
```

### P5-VERIFY-001 contract

```
TASK ID: P5-VERIFY-001
MILESTONE: P5 Production Grade
CAPABILITY: Verification (P4 gate)
GOAL: Prove the P4 properties hold as one journey, not as separate suites.

CONTEXT: every earlier phase has a gate that walks its journey end to end -
         P4 alone relied on the P3 gate plus the per-task suite, which is
         honest but never exercised the P4 capabilities against each other.
         The two properties that make P4 *P4* - the error taxonomy
         (P4-RELIABILITY-002) and rerun determinism (P4-VALID-005) - are
         invisible on the happy path, so no existing gate saw them.
INPUTS: an in-process TestClient; a dataset larger than the result cap.
RELEVANT FILES: verification/p4/verify_p4.py (NEW), verification/p4/REPORT.md
                (emitted), .github/workflows/ci.yml, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - verification/p4/verify_p4.py: 18 steps walking the edges a controlled
    external user reaches - a 5000-row dataset, the result cap truncating a
    full scan while an aggregate over the same data stays exact, bad SQL
    answering 400 with the engine's own message and persisting nothing, a
    write and a sandbox escape both refused, an injected harness fault
    answering 500, a deliberately broken LLM degrading to deterministic, the
    assistant drafting without writing, the human accepting, eight repeat
    validations of an unordered result agreeing, and an export/import round
    trip.
  - .github/workflows/ci.yml: the server job runs the P4 gate alongside P2
    and P3, and its report is uploaded with the others.
NON-GOALS: the P0 gate (binds a port); testing the React shell (a vitest
           concern); testing CI itself; signing (DEC-004, P5-DIST).
CONSTRAINTS: hermetic - no LLM credential is ever set and the one step that
             sets a dummy key breaks the LLM on purpose, so no run makes a
             network call. Every dataset value is a closed function of the
             row index, so the expectations are known by construction rather
             than measured. Injected faults are restored in a finally block
             so a failure cannot leak a broken engine into later steps.
ACCEPTANCE CRITERIA:
- [x] the gate exits 0 with all 18 steps and all 10 exit criteria PASS
- [x] bad input answers 400 with a message and leaves no run behind
- [x] an injected harness fault answers 500, never 400
- [x] a broken LLM degrades to deterministic and still returns a plan
- [x] the result cap truncates a full scan but an aggregate reads every row
- [x] eight validations of an unordered GROUP BY return exactly {"supported"}
- [x] the case exports and reproduces elsewhere; the suite runs green (231)
- [x] CI runs the gate on every push
TESTS: the gate is the test; it also re-runs the suite as its last step.
VERIFICATION: verification/p4/REPORT.md PASS; P2/P3 gates still PASS.
STATE UPDATE: mark P5-VERIFY-001 done on pass; the P5 checklist's verification
              item is closed and P4 has the gate it previously lacked.
```

### P5-OBSERVE-002 contract

```
TASK ID: P5-OBSERVE-002
MILESTONE: P5 Production Grade
CAPABILITY: Observability
GOAL: When something goes wrong in a packaged app, there is a log to read.

CONTEXT: P4 made a 500 honest - the exception propagates and uvicorn logs a
         traceback. But in the packaged app the core is a PyInstaller sidecar
         whose stderr goes nowhere a user can read, so that traceback lands in
         a void and a support question has nothing behind it. uvicorn's stderr
         is a developer surface; a packaged app needs a file.
INPUTS: DAH_LOG_DIR (optional override), DAH_LOG_LEVEL (optional), the same
        DAH_DATA_DIR the shell already sets.
RELEVANT FILES: server/app/logging_config.py (NEW), server/app/main.py
                (configure at startup, the request middleware, GET /logs),
                server/tests/test_logging.py (NEW), docs/Observability.md (NEW),
                ai/ROADMAP.md, ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - app/logging_config.py owns one setup function, `configure_logging`, that
    installs a size-capped RotatingFileHandler (2MB x 3 backups, so the log
    can never eat the disk) plus a stderr handler, and points the uvicorn
    loggers at the same file so request logs are not lost. Idempotent - a
    second call replaces rather than stacks. The directory defaults to
    DAH_DATA_DIR/logs and DAH_LOG_DIR overrides it, exactly as DAH_DB_PATH
    overrides the default database location. An unwritable log dir degrades
    to stderr-only with a warning instead of preventing the server from
    starting - a log is not worth more than the app.
  - The file handler is NOT installed under pytest (the suite overrides
    DATA_DIR post-import, so an import-time handler would write into the
    repo); tests configure it explicitly against a tmp dir.
  - app/main.py: a request middleware logs method, path, status and duration
    per request. Only those four - the body is never logged, so an analyst's
    SQL, their question and their data stay out of the log.
  - GET /logs?lines=N returns the path, the size, the rotated file names and
    the last N lines (default 200, clamped to 1000) read-only, and reports
    `enabled: false` when file logging is off rather than erroring.
  - docs/Observability.md: where the log lives, how to read it, and the
    explicit privacy boundary - what is logged and what is not.
NON-GOALS: shipping logs anywhere off the machine, a UI for the log (the shell
           can call /logs; wiring a menu is a follow-up), serving the rotated
           backups' contents, structured JSON logs (a plain parseable line is
           enough and stays greppable), authentication on /logs (the core binds
           to 127.0.0.1 for a single local user, like every other endpoint).
CONSTRAINTS: no behaviour change to any existing endpoint; the gates and the
             test suite must be unaffected; nothing the analyst typed may
             appear in the log.
ACCEPTANCE CRITERIA:
- [x] a packaged-style core (DAH_DATA_DIR set) writes dah-core.log under it
      without any caller wiring
- [x] the log rotates at the cap and the total stays bounded (no unbounded
      growth, no rotation storm)
- [x] a 500's traceback is in the file, recoverable through GET /logs
- [x] each request logs method/path/status/duration and the *body* does not:
      an analyst's question text is provably absent from the log
- [x] an unwritable log dir does not stop the server
- [x] GET /logs is read-only (a POST to it changes nothing) and clamps lines
- [x] pytest never writes a log file into the repo
TESTS: server/tests/test_logging.py - 12 tests: default location, env override,
       rotation bound, idempotent reconfiguration, unwritable dir, tail reading,
       the 500 traceback round-tripped through /logs, the request line, the
       body-not-logged property, /logs when disabled, line clamping, and no
       repo writes under pytest.
VERIFICATION: `cd server && .venv/bin/python -m pytest -q` green (243 total);
              the P2, P3 and P4 gates still PASS; CI green.
STATE UPDATE: mark P5-OBSERVE-002 done on pass; the P5 checklist's
              observability item is closed.
```

### P5-RELIABILITY-003 contract

```
TASK ID: P5-RELIABILITY-003
MILESTONE: P5 Production Grade
CAPABILITY: Reliability (the carried 500 envelope)
GOAL: A 500 answers the same shape as every other error, and an id that finds
      its traceback.

CONTEXT: P4-RELIABILITY-002 made a fault answer 500 instead of a 400 that
         blamed the analyst, and deliberately declined to change the body -
         Starlette's plain-text "Internal Server Error". The client tolerates
         it (api.ts parses JSON only when the core sent it), but it is the one
         remaining rough edge in the error contract, and P5-OBSERVE-002 just
         put the traceback somewhere an id can point at.
INPUTS: an unhandled exception reaching the middleware stack.
RELEVANT FILES: server/app/main.py (the exception handler), server/app/models.py,
                server/tests/test_error_semantics.py, web/src/api.ts,
                web/src/api.test.ts (NEW), docs/Observability.md,
                ai/ROADMAP.md, ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - A registered handler for `Exception` answers 500 with
    `{"detail": "internal error", "request_id": "<hex>"}`, and logs the
    traceback under that id. Logging matters as much as the envelope: catching
    the exception means uvicorn no longer logs it, so without an explicit
    record the traceback P5-OBSERVE-002 promised would stop reaching the file.
  - The body carries no exception text. A fault's message can quote what it was
    holding - an unknown column, a filename, a value that failed to parse - so
    only the id and a fixed message leave the process. The traceback stays in
    the log, on the user's machine.
  - HTTPException is untouched: a 400/404 still answers its own `detail`.
  - api.ts surfaces the id on ApiError so a user can quote it and the UI can
    say "this is error <id>, it is in the log" instead of "request failed".
NON-GOALS: retry, rate limiting, user-visible log browsing in the shell (the
           endpoint exists; a menu item is a separate UI task), any change to
           the 4xx contract, correlation ids threaded through the request
           middleware (the handler's id is enough for a single-user local tool).
CONSTRAINTS: the status code must stay 500 - the whole point of P4 was that a
             fault is never flattened into a client error - and the P4 gate's
             fault step must still pass.
ACCEPTANCE CRITERIA:
- [x] a fault answers 500 with `detail` and a `request_id`
- [x] the same id is in the log line carrying the traceback
- [x] the exception's own message is in the log and NOT in the body
- [x] a 400 and a 404 are unchanged: their own `detail`, no request id
- [x] the client turns the envelope into an ApiError carrying the id
TESTS: server: the envelope, the id-in-log round trip, the no-leak property,
       and the 4xx contract unchanged. web: 3 tests on api.ts - the 500
       envelope yields an ApiError with the id, a plain 4xx is unchanged, and a
       500 that is not JSON still works (the fallback path the envelope
       replaced).
VERIFICATION: `cd server && .venv/bin/python -m pytest -q` green (256 total);
              `cd web && npm test` green (20 total); P2/P3/P4 gates PASS; CI
              green.
STATE UPDATE: mark P5-RELIABILITY-003 done on pass; the carried item from
              P4-RELIABILITY-002 is closed.
```

### P5-CI-004 contract

```
TASK ID: P5-CI-004
MILESTONE: P5 Production Grade
CAPABILITY: CI floor
GOAL: Make the minimum supported macOS version a real, tested floor rather
      than an assumption.
GOAL NOTE: "just CI refine, target Mac minimal Ventura" - the user asked for
      exactly this and nothing more.
CONTEXT: every job ran on macos-latest, which is whatever GitHub newest is at
         the moment - currently arm64, while the development machine and the
         sidecar triple are x86_64. A green run was therefore a binary nothing
         else in the project ever produced, and the oldest macOS DAH might be
         asked to run on had never been built against at all.
INPUTS: the runner image label.
RELEVANT FILES: .github/workflows/ci.yml, README.md, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - A single MACOS_RUNNER env (macos-13) drives all four jobs, so the floor is
    stated once and a bump touches one line. macos-13 is Ventura and the last
    Intel image, which matches the dev machine and the
    x86_64-apple-darwin sidecar triple.
  - The packaging job's smoke step now asserts the packaged core's file
    logging is on and lands under the data dir it was given - a packaged
    app's stderr is unreadable, so this is the one place the observability
    work is provable in the real PyInstaller bundle rather than a dev
    checkout.
NON-GOALS: arm64 as a second CI lane (real, but a separate task that needs a
           second runner and a second sidecar triple), signing (blocked on the
           Developer ID, DEC-004), any change to the jobs themselves beyond
           the runner and the smoke step, Windows or Linux.
CONSTRAINTS: no job may gain a secret; nothing may stop running on the floor.
ACCEPTANCE CRITERIA:
- [x] all four jobs run on macos-13 and the runner is defined once
- [x] the smoke step fails when the packaged core does not log into its data
      dir (verified locally against a stale binary, which 404'd on /logs and
      failed the new assertions)
- [x] the smoke step passes against a sidecar built from current source
- [x] README states the minimum supported version
TESTS: none new - this task is CI configuration. Verified by running the
       smoke block locally against both the stale sidecar (fails as designed)
       and a freshly built one (passes), and by parsing the workflow YAML.
VERIFICATION: workflow YAML valid; the four jobs' commands unchanged; server
              256 / web 21 / desktop 7 still green locally (this commit moves
              no code).
STATE UPDATE: mark P5-CI-004 done on pass; record the floor in README.
```

### P5-RELEASE-005 contract

```
TASK ID: P5-RELEASE-005
MILESTONE: P5 Production Grade
CAPABILITY: Release automation
GOAL: a versioned artifact a user can download instead of having to build.

CONTEXT: the packaging job in ci.yml already proves the sidecar builds and
         serves on a clean machine, but the output went nowhere - the artifact
         was uploaded for one job and deleted a day later. Three files held
         0.1.0 independently (server/pyproject.toml, web/package.json,
         desktop/package.json, tauri.conf.json) and nothing kept them honest
         with each other or with anything a user would see.
INPUTS: a git tag `v<x.y.z>` whose x.y.z matches server/pyproject.toml.
RELEVANT FILES: .github/workflows/release.yml (NEW), README.md, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - .github/workflows/release.yml: on a `v*` tag, one job on the CI floor -
    read the version from server/pyproject.toml and FAIL if the tag does not
    match it (so a stale version file can never publish a build whose label
    lies), run the server suite, build and smoke the sidecar (health plus the
    packaged-log assertions from P5-CI-004), build the .app with the version
    stamped from the pyproject, ditto-zip it with its architecture in the name,
    shasum it, generate notes that state the unsigned status and the Gatekeeper
    steps, and publish a flagged pre-release with the zip and its checksum.
  - server/pyproject.toml is the single version source of truth; tauri.conf.json
    is patched at build time by --config rather than kept in sync by hand.
NON-GOALS: signing and notarization (DEC-004, blocked on the Developer ID -
           this job has the slot they slot into, between build and upload),
           arm64 or universal builds (a second lane, this machine is x86_64),
           auto-changelog generation, publishing to a package registry,
           releasing from anywhere but a tag.
CONSTRAINTS: no secret is needed - the unsigned build uses only the default
             GITHUB_TOKEN with contents:write; the release must never be
             created from a version mismatch; nothing may publish on a branch
             push.
ACCEPTANCE CRITERIA:
- [x] a tag that disagrees with the pyproject version fails before any build
- [x] the server suite runs inside the release job
- [x] the packaged core is smoked (health + log in the data dir) before packaging
- [x] the .app's version is the pyproject's, not tauri.conf.json's
- [x] the published asset is a zip plus a sha256, with the architecture named
- [x] the release body states it is unsigned, how to open it, and that the
      published build is Intel
- [x] the release is flagged a pre-release
TESTS: none new - this task is a workflow. Verified by running every step it
       runs, locally: the tag-mismatch check (fails as designed), the sidecar
       smoke, `npm run tauri -- build --config '{"version":...}'`, the ditto
       zip, the shasum, and the generated notes. The only step not exercisable
       locally is `gh release create` against GitHub.
VERIFICATION: workflow YAML parses; every command in it was run by hand against
              the current tree; the zip contains a .app whose
              CFBundleShortVersionString is the pyproject version.
STATE UPDATE: mark P5-RELEASE-005 done on pass; the P5 checklist's release item
              is closed, leaving only signing (blocked) on it.
```

### P5-UX-006 contract

```
TASK ID: P5-UX-006
MILESTONE: P5 Production Grade
CAPABILITY: Shell UX
GOAL: A user hits a problem and finds the log without ever opening a terminal.

CONTEXT: P5-OBSERVE-002 made the core write a log next to the user's cases and
         answer GET /logs with its path - but a path inside a JSON body is
         still a terminal answer, and the shell exists precisely because this
         user does not have a terminal open.
INPUTS: the running core on port 8123; GET /logs.
RELEVANT FILES: desktop/src-tauri/src/logs.rs (NEW), desktop/src-tauri/src/main.rs
                (the menu and its handler), desktop/src-tauri/Cargo.toml,
                docs/Observability.md, ai/ROADMAP.md, ai/CURRENT_STATE.md,
                ai/HANDOFF.md
REQUIRED CHANGE:
  - logs.rs owns the bridge: logs_url, LogLocation (File | Disabled),
    parse_log_location, log_location (one GET through the ureq the shell
    already depends on), reveal_in_finder (`open -R`, macOS-native, no new
    dependency) and reveal_core_logs, which is the menu item's whole job.
  - Everything degrades to a sentence rather than an error. A core still
    booting, hung, or older than the endpoint is Disabled - a menu item that
    says "logging is off" beats one that fails when it is needed most - and a
    body that is not the expected shape is Disabled too, so a menu can never
    panic on a body it does not recognise.
  - main.rs: a real macOS menu bar. The app menu keeps About and Cmd+Q, which
    setting any custom menu takes away, Edit keeps the text editing a data
    tool needs, and DAH > Reveal DAH Logs is the one item DAH adds.
NON-GOALS: browsing the log inside the app (the terminal and the file are both
           already fine for that), a web UI button for the same command (the
           browser host has no core-spawned log to reveal), serving the
           rotated backups, anything but macOS (`open -R` is macOS-only, and
           so is the app).
CONSTRAINTS: no new runtime dependency beyond serde_json, which is already in
             the tree through tauri; the existing 7 Rust tests must still pass;
             the menu bar must not lose the standard macOS items.
ACCEPTANCE CRITERIA:
- [x] the menu item exists in the running app's menu bar
- [x] clicking it opens Finder on the log the running core is actually writing
- [x] a core with file logging off yields a stated reason, not a failure
- [x] a malformed or unexpected /logs body cannot panic the menu
- [x] the standard macOS app and Edit menus survive the custom menu
TESTS: 4 unit (enabled/disabled/odd-shape/url) plus 1 e2e that starts the real
       dev core and asserts the reported log is under the data dir the shell
       pointed it at and is a file that exists - 12 Rust tests total, was 7.
VERIFICATION: cargo test --features e2e green; the built app smoke-tested by
              hand - the menu bar introspected with AppleScript, the item
              clicked, and the handler's outcome in the shell log naming the
              real path; the core stopped and the port freed afterwards.
STATE UPDATE: mark P5-UX-006 done on pass; the "Reveal logs" follow-up is
              closed.
```

```
TASK: P5-CI-FIX-007 - repair CI: it had not run for three commits
ID: P5-CI-FIX-007
PRIORITY: high
STATUS: DONE
SUMMARY: CI was silently broken since 5e68fbb (P5-CI-004). Every push failed at
         parse time - 0s, no job ever started, both workflows - reported only as
         "a workflow file issue". Two separate bugs, one hiding the other.
WHAT CHANGED:
- 3ad554b: the immediate cause. P5-CI-004 referenced the runner label as
  `${{ env.MACOS_RUNNER }}` in every job's `runs-on`, and GitHub does not
  expand the `env` context there. Inlined the literal; the env entry and the
  misleading comment went with it. Recorded in both headers why runs-on is a
  literal, because a parse-time failure reports nothing and blocks all jobs at
  once - it had hidden itself for three commits.
- 37c6e16: the deeper cause the first fix exposed. GitHub has retired the
  macos-13 hosted pool, so the Ventura floor P5-CI-004 targeted was never
  provisionable - with the parse bug fixed, the jobs unblocked into a queue
  they never left. A throwaway probe workflow settled it: an identical pair of
  jobs, macos-latest completed in under a minute while macos-13 sat queued with
  zero steps for 18 minutes. All jobs moved to macos-latest; the Ventura floor
  stays documented as the minimum supported macOS but is no longer enforced by
  CI. See DEC-005 for what a green run no longer proves (the Intel triple) and
  what restoring it costs (a self-hosted runner).
- 4dca009: the release job's web install ran `npm ci` in desktop/ only, but the
  Tauri beforeBuildCommand is `npm --prefix ../web run build:desktop` - a
  script in web/package.json whose deps (vite, tsc) live in web/node_modules.
  desktop/ carries only the Tauri CLI, so the prefixed script had nothing to
  run and the build died with exit code 127. Both trees are now installed.
- The release notes no longer assert the build is Intel: the paragraph is
  chosen from the runner's actual triple, so an arm64 or Intel lane both
  describe themselves.
ACCEPTANCE CRITERIA:
- [x] all four ci.yml jobs pass on GitHub's own runners (server + 3 gates, web,
      packaging sidecar smoke, desktop lifecycle incl. both e2e tests)
- [x] release.yml runs end to end from a tag for the first time
- [x] the published zip's sha256 matches its checksum asset
- [x] the .app bundle carries the sidecar and the version the tag verified
VERIFICATION: run 35490199963 four-for-four green; run 35490519483 published
              v0.1.0. `shasum -a 256 -c` OK on the downloaded 79MB zip;
              Info.plist CFBundleShortVersionString 0.1.0; Contents/MacOS/
              carries dah-shell (15MB) and dah-core (78MB).
LESSON: two independent bugs compounded. The `env` context is unavailable in
        runs-on, and that silent parse failure masked a second problem - the
        label it was finally resolving to no longer exists. Fixing a reported
        error is not the same as fixing the underlying state; verify the
        workflow actually *runs*, not merely that it parses. CI visibility had
        been blocked all session, which is how three commits shipped without
        anyone noticing CI had stopped entirely.
```

```
TASK: P6-MEMORY-001 - cross-case recall: let an answer cite previous cases
ID: P6-MEMORY-001
PRIORITY: high
STATUS: DONE
SUMMARY: A case could already cite its own artifacts - runs, datasets, findings -
         via the grounds budget in assistant.py. Nothing let it cite a PREVIOUS
         case: summarize_case read exactly one case's rows, so every
         investigation started from scratch even when the same anomaly was
         found and explained last month. Analysis memory closes that. New
         app/memory.py derives, per question, which prior cases bear on it;
         the assistant can now cite `case:<id>` and the prior finding, both
         validated against real rows.
WHAT CHANGED:
- server/app/memory.py (NEW): summarize_memory is a pure projection over cases
  and findings. Relevance is a shared-content-word count against the question,
  the dataset label and every finding statement, with a hand-written stoplist
  and a threshold of 2 shared words - deliberately not an embedding: no
  dependency, no network, deterministic, and it makes the "nothing bears on
  this" answer honest. A case with no findings is skipped however similar its
  question sounds; there is nothing to recall. Writes nothing.
- server/app/assistant.py: a new KIND_CASE ground and a recall branch in the
  deterministic answer. It fires when the question is *about* prior work
  (before/previous/earlier/...) or when the case has nothing of its own - and
  it sits ahead of the column/dataset branches on purpose, because "what did I
  find before about revenue?" names a column and would otherwise be answered
  with this case's column stats: a true answer to a question nobody asked. A
  case with its own artifacts and no prior framing still gets its own stage.
  _references admits case: and the prior finding's id, so an invented
  cross-case citation is rejected exactly as an invented column is. The LLM
  prompt carries memory and its citation budget names the case kind.
- server/app/main.py: the chat endpoint passes the message to summarize_case,
  because which prior cases are relevant depends on what was asked.
- server/tests/test_memory.py (NEW): 11 tests.
NON-GOALS: replaying another case's result rows (a conversation points at
           evidence, it does not replay it), writing anything on read, a vector
           store (SQLite already holds everything), cloud sync.
CONSTRAINTS held: the P3 honesty budgets survive - a cross-case ground must
             resolve to a real finding in a real other case or be rejected;
             the deterministic path needs no LLM key; nothing logs what the
             analyst typed; no new runtime dependency.
ACCEPTANCE CRITERIA:
- [x] a question whose answer is in another case is answered citing that case
      by name, deterministically (source=deterministic)
- [x] an invented cross-case citation is rejected by validate_answer, exactly
      as an invented in-case ground is
- [x] an answer that no other case supports says so plainly rather than
      dragging in a weakly-related case
- [x] no read path writes; the memory is a projection over existing rows
- [x] the LLM path degrades to deterministic on any failure and records source
- [x] the P4 gate and the full suite stay green; new tests pin every criterion
TESTS: 11 in server/tests/test_memory.py - the headline recall, the cited case
       and finding are real rows, invented case and invented prior finding both
       rejected, an off-topic prior case is not dragged in, a case with its own
       artifacts answers from its own state, an explicit prior question recalls
       anyway, the LLM receives memory and validates, a malformed LLM memory
       answer falls back, recalling writes nothing, and a case is never its own
       previous case.
VERIFICATION: server suite 267 passed (was 256, +11); P4 gate PASS on all 18
              steps and all 10 exit criteria; P3 gate PASS; web 21 passed;
              desktop 12 Rust tests. All green locally.
LESSON: three of the eleven tests failed first run for the same reason - the
        test's own fixture. The helper hardcoded a finding about "revenue" in
        "sales.csv" while the question was about revenue, so an allegedly
        off-topic prior case still shared two content words and was correctly
        recalled. The code was right; the test was asserting a separation its
        own data did not have. A relevance threshold is only as honest as the
        corpus it is measured against - and a fixture that says "weather" while
        quoting "sales" is not a weather fixture.
```

```

### P6-AGENT-002 contract

```
TASK ID: P6-AGENT-002
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Agentic Analysis
GOAL: A plan that executes itself: walk the loop (generate code, run it, read
      the result, iterate, draft a finding) with the human approving each
      write, over the endpoints that already exist.

CONTEXT: every stage of the loop already has a validated endpoint with an
         honesty budget behind it - generate-code (P3-AI-013), runs, interpret
         (P3-AI-011), draft-finding (P3-AI-012), findings, charts, validate.
         What does not exist is the loop driver: a human still clicks through
         one panel at a time. P6-MEMORY-001 landed the recall an agent needs;
         this task is the orchestration over the validated primitives.

INPUTS: a case id (with at least one attached, profiled dataset).
RELEVANT FILES: server/app/agent.py (NEW), server/app/main.py, models.py, db.py,
                server/app/generator.py (variant), server/tests/test_agent.py (NEW)
REQUIRED CHANGE:
  - app/agent.py: a step machine, not a script. Each call to advance() performs
    ONE write or one read-only proposal and returns the next pending step.
    Steps: profile -> plan -> analyze (generate code, then run it) ->
    interpret -> draft -> accept -> chart -> validate -> done. The next step is
    DERIVED from the case's artifacts (the same projection workflow.py uses),
    so an interrupted agent resumes exactly where it stopped and can never
    claim a step the data does not support.
  - main.py: POST /cases/{id}/agent (start/advance), GET .../agent (state),
    POST .../agent/approve {step_id} (the human's yes), POST .../agent/reject
    {step_id, reason?}. Every write step requires an explicit approval id; a
    proposal step (generate code, draft) writes nothing and needs no approval,
    because its endpoints are already stateless by design.
  - The human's decision is recorded, not inferred: an agent_step row holds the
    step, the payload it proposed, the outcome and, for writes, the approval
    that let it run. An agent that was never approved has written nothing.
  - generator.py: generate_code gains an optional `variant` (default 0) so a
    retry proposes a genuinely different query - different measure/dimension
    axis - rather than re-proposing the one that just returned nothing.
NON-GOALS: autonomous write (a write without an approval id is a 500-class
           contract violation, tested as such), a new LLM engine or prompt
           chain (the agent composes the existing deterministic-or-LLM
           primitives and carries their `source` through unchanged), a web UI
           for the agent (the endpoints are the contract; the shell wires
           later), multi-dataset join planning by the agent, retries that
           re-propose identical code.
CONSTRAINTS: every run the agent makes goes through the same read-only gate
             and row cap as a hand-written one - the agent earns no
             privileges; a finding is still created only by POST /findings,
             never by the agent module; the honesty budgets of P3-AI-011..014
             are untouched and still reject an invented magnitude or column at
             the same boundaries; deterministic by default (source records
             which engine each proposal came from); nothing the analyst typed
             is logged; no new runtime dependency; the agent terminates
             (a bounded retry budget, and a case with no usable axis ends at
             a stated reason rather than looping).
ACCEPTANCE CRITERIA:
- [x] starting an agent on a profiled case proposes the plan step and nothing
      has been written
- [x] each write step performs exactly one write and only after its approval
      id is supplied; approving a stale or unknown step id is a 409/404
- [x] an empty first result makes the agent iterate: the next proposal is a
      different query (variant), not the same one
- [x] the retry budget is bounded; exhausting it ends the run at a stated
      reason, not a silent stop and not an infinite loop
- [x] the agent reaches a draft and, on approval, a validated finding - the
      full loop - on a case built through the public API alone
- [x] a case with no usable axis (no repeating numeric, no categorical) ends
      with a stated reason instead of proposing nothing forever
- [x] every step carries the source of the proposal that made it
- [x] no read path writes; the agent's own state is one append-only table
- [x] delete removes the agent state with the case; export carries it
- [x] the full server suite, the P2/P3/P4 gates and the web suite stay green
TESTS: server/tests/test_agent.py - the full happy walk (plan -> analyze ->
       interpret -> draft -> accept -> chart -> validate), write-without-
       approval refused, stale approval id, iteration on an empty result,
       budget exhaustion with a stated reason, no-axis early end, source
       propagation, resumption after interruption, delete cleanup, 404s.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS.
STATE UPDATE: mark P6-AGENT-002 done on pass; ROADMAP item 2 flips to DONE.
```

```
TASK: P6-AGENT-002 - agentic analysis: a plan that executes itself, one approved
write at a time
ID: P6-AGENT-002
PRIORITY: high
STATUS: DONE
SUMMARY: Every stage of the loop already had a validated endpoint with an
         honesty budget behind it. What did not exist was the driver over them:
         a human still walked the panels one click at a time even when the next
         click was never in doubt. The agent is that driver, and it is
         deliberately not an autonomous one. It proposes a step whose payload is
         settled at proposal time; a human approves that step by id; the write
         runs through the endpoint that already owns it. The agent holds no
         privilege a hand-written call lacks.
WHAT CHANGED:
- server/app/agent.py (NEW): a step machine, not a script. next_step() derives
  the one thing to do next as a pure projection over the case's artifacts - the
  same discipline as the workflow stage (P3-FLOW-004) - so an interrupted agent
  resumes exactly where it stopped and can never be ahead of or behind the data.
  Loop order: profile -> plan -> analyze -> interpret -> accept -> chart ->
  validate. `accept` carries the drafter's candidate finding inside its payload,
  because the draft is stateless by design (P3-AI-012) and there is no separate
  draft row to take; `analyze` carries its generate-code proposal the same way.
  An empty result is the one real decision point: the variant rotates so the
  retry is a *different* query, a proposal identical to one already tried is a
  dead end, and three empty attempts end the run at a stated reason rather than
  a silent stop. `end` is a terminal record, not work: it says why the agent
  stopped so an abandoned case falls silent nowhere.
- server/app/generator.py: _pick_axes and generate_code take a `variant` that
  rotates the measure/dimension/period through the usable columns, and the LLM
  retry prompt names the empty attempts so its proposal differs from the one
  that struck out. A family with a single usable column keeps that column, so a
  dataset with no alternative axis produces an identical proposal - which is how
  the caller detects the dead end rather than spending its budget.
- server/app/main.py: four endpoints over one path. GET /agent is strictly
  read-only (a refresh that proposed would commit work the human never saw);
  POST /agent derives and records the next pending step, idempotently;
  POST /agent/approve refuses any id that is not the case's *current* pending
  step with a 409, so a stale page can never cause a second write;
  POST /agent/reject records the analyst's reason and performs no write. Every
  approved step awaits the async endpoint that owns the write, which is what
  keeps the read-only gate, the row cap, the honesty budgets and the single
  finding-creation path in force for an agent-run case.
- server/app/exporter.py: the `agent_steps` section. Export carries the whole
  trail; import remaps the ids a payload cites (dataset, run, finding) to the
  restored case's own artifacts, so a package stands on its own. A package from
  before this task has no such section, so its absence is tolerated rather than
  treated as corruption.
- server/app/main.py duplicate: the trail travels with the copy, citing the
  copy's own rows - an agent-proposed finding keeps the approvals that let it
  run. Delete already removed it with the case.
- server/app/db.py: the `agent_steps` table, one row per step, created with the
  others under IF NOT EXISTS so older databases migrate in place.
- server/app/models.py: AgentStep, AgentState, AgentApproval.
- server/tests/test_agent.py (NEW): 24 tests.
NON-GOALS held: no autonomous write (an approval is required for every one, and
             approving a stale id is a 409 tested as such), no new LLM engine or
             prompt chain (the agent composes the existing deterministic-or-LLM
             primitives and carries each one's `source` through unchanged), no
             web UI for the agent, no multi-dataset join planning, no retry that
             re-proposes identical code.
CONSTRAINTS held: the agent's SQL passes the same read-only gate and row cap as
             a hand-written one; a finding is still created only by the findings
             endpoint, never by the agent module; the honesty budgets of
             P3-AI-011..014 are untouched; deterministic by default with `source`
             recorded at every step; nothing the analyst typed is logged; no new
             runtime dependency; the agent terminates (bounded budget, and a
             case with no usable axis ends at a stated reason).
ACCEPTANCE CRITERIA: all 10 - see the checked boxes above.
TESTS: 24 in server/tests/test_agent.py - the full happy walk to a validated
       finding, the seven kinds in loop order, write-without-approval refused,
       stale and unknown approval ids 409, rejection recording its reason and
       writing nothing, iteration to a different query on an empty result,
       budget exhaustion at a stated reason with three distinct queries, the
       no-axis early end, source propagation, resumption after interruption,
       the state never being ahead of the data, idempotent proposal, GET writing
       nothing, export carrying the trail, the import round trip with remapped
       references, an older package without the section, delete cleanup, the
       duplicate keeping a remapped trail, and the one-row-per-step invariant.
VERIFICATION: server suite 291 passed (was 267, +24); web 21 passed; desktop 12
              Rust tests; P2, P3 and P4 gates all PASS. All green locally; CI
              will run it on push.
LESSON: two of the first 24 tests failed on the first run and both were the
        tests' fault, not the code's. One asserted an import answers 200 when
        the endpoint answers 201; one ended with a leftover `del json` line that
        crashed at assertion time. Neither was a behaviour bug, and both were
        found only because the test ran - which is the smaller lesson, that a
        test file is itself untested code until its own suite is green. The
        larger one is the same one the memory task recorded: verify the
        assertion against the real contract, not against the shape you assumed
        while writing it.
```

### P6-TEMPLATE-003 contract

```
TASK ID: P6-TEMPLATE-003
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Case reuse
GOAL: Promote a finished investigation into a reusable template carrying its
      analytical shape - its plan, its proposals and how its findings validated
      - not just its question, and let a case started from it inherit that shape
      as validated starting proposals.

CONTEXT: P3-CASE-007 shipped templates that copy the question and the dataset
         label alone. The template machinery exists; the investigation does not
         travel with it, so "same analysis, new month's file" still means
         re-deriving the plan and re-typing the query that worked last time.
         The plan, the proposals and the finding outcomes are all already on
         disk; nothing new needs to be computed to carry them.

INPUTS: a case with a plan, runs and/or findings.
RELEVANT FILES: server/app/main.py, server/app/models.py, server/app/db.py,
                server/app/exporter.py, server/tests/test_case_templates.py
REQUIRED CHANGE:
  - promotion captures a shape: a pure projection over the case's artifacts -
    its latest plan and which engine produced it, the code proposals its agent
    run made (falling back to its runs when the case was hand-run), and its
    findings' statements with their validation status. A case with nothing to
    carry promotes a shapeless template and behaves exactly as before.
  - the template row gains a nullable shape_json; the Template model exposes it.
  - a case created from a template records its lineage (template_id), so the
    case knows where it came from rather than the connection being implicit.
  - the plan step prefers the template's plan when the case has one and has no
    plan of its own yet, validated through the same validate_plan and falling
    back to the normal derivation on any problem, with source recorded as
    "template" so a reviewer sees the plan came from history, not this dataset.
  - generate-code prefers a template proposal whose every column exists in the
    profiled dataset - the profile check is what makes a historical proposal
    safe to offer against different data - and falls back to the generator
    otherwise, again recording source="template".
  - export carries the lineage; import preserves it; duplicate keeps it.
NON-GOALS: copying data, runs, findings or charts into the templated case (it
           still starts clean; the shape is proposals a human accepts, not
           artifacts it inherits), reusing a proposal that names a column the
           new dataset lacks, autonomous application of a shape (every write
           is still a POST the human makes), a template editor, sharing
           templates between installs.
CONSTRAINTS: the honesty budgets are untouched - a reused plan is still just a
             plan, and a draft or interpretation still only quotes numbers the
             actual run produced; a shapeless or missing template degrades to
             the existing deterministic path with no error; nothing the
             analyst typed is logged; no new runtime dependency; the existing
             template tests must pass unmodified.
ACCEPTANCE CRITERIA:
- [x] promoting a case with a plan, runs and findings captures all three in the
      shape
- [x] promoting an empty case yields a shapeless template indistinguishable
      from today's
- [x] a templated case starts clean and records its template id
- [x] the plan step offers the template's plan, validated, with source=template
- [x] a malformed or missing template plan falls back to derivation
- [x] generate-code offers a template proposal only when every column it reads
      exists in the profiled dataset, with source=template
- [x] a proposal naming a column the new dataset lacks is never offered; the
      generator answers instead
- [x] every shape-derived answer records source=template
- [x] a shapeless older template still promotes, lists and instantiates
- [x] deleting a template a case points at degrades to the normal path, not an
      error
- [x] export/import and duplicate carry the lineage
- [x] the full server suite, the P2/P3/P4 gates and the web suite stay green
TESTS: server/tests/test_case_templates.py - shape capture for a finished case,
       a shapeless promotion, lineage recorded on instantiation, the plan step
       preferring the template plan, the fallbacks, a proposal accepted and
       refused by column existence, source propagation, a deleted template
       degrading, the export/import and duplicate round trips, and the
       unmodified existing behaviours.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS.
STATE UPDATE: mark P6-TEMPLATE-003 done on pass; ROADMAP item 3 flips to DONE.
```
```
TASK: P6-TEMPLATE-003 - templates carry the analytical shape of a finished case
ID: P6-TEMPLATE-003
PRIORITY: high
STATUS: DONE
SUMMARY: P3-CASE-007 shipped templates that copied the question and the dataset
         label alone, so "same analysis, new month's file" still meant
         re-deriving the plan and re-typing the query that worked last time. A
         template now carries the *shape* of a finished investigation too, and
         a case started from it inherits that shape as validated starting
         proposals - not as artifacts, and never applied without a human.

Five pieces, all projections over what is already on disk:

- **`_capture_shape` (main.py)** - a pure projection, nothing computed. The
  case's latest plan and which engine produced it; the code proposals its
  agent run made, falling back to its runs when a human drove the case; and
  its findings' statements with the verdicts validation already gave them. A
  case with none of these promotes the shapeless skeleton it always promoted
  and behaves exactly as before.
- **`templates.shape_json` + `cases.template_id` (db.py, models.py)** - the
  shape has somewhere to live and a case knows where it came from. Both
  nullable, both added to `_ensure_column`, so an older database migrates in
  place.
- **the plan step** prefers the template's plan when the case has none of its
  own, validated through the same `validate_plan` and falling back to the
  normal derivation on any problem, with `source="template"` so a reviewer
  sees the plan came from history rather than this dataset.
- **generate-code** prefers a template proposal only when every column it
  reads exists in the profiled dataset - that profile check is what makes a
  historical proposal safe to offer against different data - and falls back
  to the generator otherwise, again recording `source="template"`.
- **exporter.py** - the lineage travels with the package, import preserves it,
  and a duplicated case keeps it.

Two real bugs the tests found. `SOURCE_TEMPLATE` was referenced in two
helpers but its definition silently never landed, so the first request to a
templated case's plan step raised a `NameError` - a compile-time name in a
module that imports cleanly is still a runtime error when the path is never
exercised, and only a test that walked the path caught it. And hand-run
cases' proposals captured `columns_used: []`, which made the column-existence
safety check pass *vacuously* - a template query could be offered against a
dataset lacking its columns, which is exactly the one thing the check existed
to prevent. Proposals now compute their reach at capture time through
`generator._columns_referenced`, so a hand-run proposal carries the same
reach an agent's does. A guard that is never fed the data it guards is not a
guard.

NON-GOALS held: no data, runs, findings or charts are copied into a templated
             case (it starts clean; the shape is proposals a human accepts),
             no proposal naming a column the new dataset lacks is ever
             offered, no shape is applied autonomously (every write is still a
             POST the human makes), no template editor, no cross-install
             sharing.
CONSTRAINTS held: the honesty budgets are untouched (a reused plan is still
             just a plan, and a draft or interpretation still only quotes
             numbers the actual run produced); a shapeless, malformed or
             deleted template degrades to the existing deterministic path with
             no error; nothing the analyst typed is logged; no new runtime
             dependency; the 10 existing template tests pass unmodified.
ACCEPTANCE CRITERIA: all 12 - see the checked boxes above.
TESTS: 11 appended to server/tests/test_case_templates.py (21 total, the first
       10 unmodified) - shape capture for a finished case, a shapeless
       promotion, lineage recorded on instantiation, the plan step preferring
       the template plan, both fallbacks, a proposal accepted and refused by
       column existence, source propagation, a deleted template degrading, and
       the export/import and duplicate round trips.
VERIFICATION: server suite 302 passed (was 291, +11); P2, P3 and P4 gates all
              PASS (the P4 gate re-ran the suite at 302); web 21 passed;
              desktop 12 Rust tests. All green locally; CI will run it on push.
LESSON: a safety check whose input is collected at the wrong moment is a
        safety check that does not run. `columns_used` was captured empty for
        hand-run cases, so the column-existence gate passed vacuously and would
        have offered a template's query against a dataset that lacked its
        columns - the single failure the gate was written to prevent. The guard
        was in the right place; the data never reached it. Any check over a
        historical artifact must be verified against the path that created the
        artifact, not only against the path that consumes it.

```

### P6-MIGRATE-004 contract

```
TASK ID: P6-MIGRATE-004
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Maintainability
GOAL: Give the store a versioned, forward-only migration path, so a database
      written by any past release is brought to the current shape by a recorded
      chain of named migrations - and the app can state which shape it opened.

CONTEXT: the store grew by seven `_ensure_column` in-place additions across
         P2-P6, each guarded and each correct, but nothing records which of them
         a given database has had. There is no version number anywhere in the
         file, so no code can tell "is this store current?" - it can only probe
         for each column and hope. That was tolerable while the schema only ever
         gained nullable columns; it stops being tolerable the moment a task
         renames, splits or backfills anything, which is exactly what P6's
         remaining items (memory tables, release metadata) are about to do.

INPUTS: a SQLite store at DAH_DB_PATH, of any age (including one written by a
        release older than this task, which has no version recorded at all).
RELEVANT FILES: server/app/db.py, server/app/main.py, server/app/models.py,
                server/tests/test_migrations.py (NEW)
REQUIRED CHANGE:
  - a schema version number lives in the file itself, via SQLite's
    `user_version` (stored in the header, so it survives without a table), and
    a `schema_migrations` row records each migration actually applied, with its
    name and timestamp - the audit trail the `_ensure_column` list could never
    give. A fresh store records nothing: it was created whole at the current
    shape and nothing was applied to it, which is the truth.
  - an ordered `MIGRATIONS` list; each entry is a version, a name and a call.
    The seven historical additions become migrations 1-7, still guarded, so a
    store at any intermediate state converges instead of erroring on a column
    it already has. Migration N runs only when the recorded version is below N.
  - opening a store upgrades it in place, one migration per transaction, the
    version advanced after each; a failure mid-chain leaves a consistent store
    at the last good version, and the next open resumes from there rather than
    restarting. That resumability is the property that makes an in-place
    upgrade safe to run at request time.
  - the store refuses to operate against a version NEWER than the app knows
    (an older binary opening a newer store), rather than silently treating it
    as current; a downgrade against a schema it does not understand is how data
    is corrupted quietly.
  - `GET /schema-version` reports the recorded version, the target, and the
    applied migrations - the one way a user can ask "is my data safe with this
    build", and the answer a release note can point at.
NON-GOALS: down migrations (the store is forward-only, always; a local
           single-user database's rollback path is a backup, not a second
           schema to maintain and get wrong), destructive or backfilling
           migrations (this task establishes the mechanism; the first migration
           that moves data is a later one), online/rolling upgrades across a
           server fleet (one process, one store), a migration CLI (the app
           upgrades on open; a CLI is ceremony for a single-user tool).
CONSTRAINTS: an upgrade runs on the ordinary open path, so it must be
             idempotent (running it on an already-current store is a no-op that
             writes nothing), fast on the warm path (one PRAGMA read), and safe
             to interleave with reads; existing rows survive every migration
             unmodified; no existing test may change; nothing the analyst typed
             is logged; no new runtime dependency; a store written by v0.1.0 -
             which has no version and a pre-migration shape - must open, upgrade
             and work, because that is the one store that actually exists in the
             wild.
ACCEPTANCE CRITERIA:
- [x] a fresh store is created at the current version with an empty migration
      table, without running the historical ALTERs
- [x] a store written by a pre-migration release upgrades to the current shape
      and every historical column is present afterwards
- [x] existing rows survive the upgrade, byte for byte in value
- [x] reopening a current store is a no-op: version unchanged, no new migration
      rows, no writes
- [x] a partially-upgraded store (some migrations applied, version recorded
      mid-chain) resumes from where it stopped and reaches the current shape
- [x] a store claiming a version newer than the app is refused with a clear
      error, not silently downgraded
- [x] a fresh store and an upgraded store have identical table shapes - the
      schema and the migration chain agree
- [x] `GET /schema-version` reports the recorded version, whether it is
      current, and the applied migrations
- [x] the full server suite, the P2/P3/P4 gates and the web suite stay green
TESTS: server/tests/test_migrations.py - the fresh-store baseline, the legacy
       upgrade over a store built with the pre-migration schema, row survival,
       the no-op reopen, mid-chain resumption, the newer-than-app refusal, the
       fresh-vs-upgraded shape equivalence across every table, and the endpoint.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS.
STATE UPDATE: mark P6-MIGRATE-004 done on pass; ROADMAP item 4 flips to DONE.
```

```
TASK: P6-MIGRATE-004 - a versioned, forward-only migration path for the store
ID: P6-MIGRATE-004
PRIORITY: high
STATUS: DONE
SUMMARY: The store grew by seven ad-hoc `_ensure_column` additions across P2-P6.
         Each was guarded and each was correct, but nothing anywhere recorded
         which of them a given database had received. There was no version
         number in the file, so no code could answer "is this store current?" -
         it could only probe for each column and hope. That was tolerable while
         the schema only ever gained nullable columns; it stopped being
         tolerable the moment a task needed to rename, split or backfill
         anything, which is exactly what P6's remaining items do.

Four pieces, all in `server/app/db.py`:

- **The version lives in the file itself**, via SQLite's `PRAGMA user_version`.
  It is stored in the database header rather than a table, so it is readable
  before the schema exists and survives a crash that leaves tables half-made.
  `LATEST_SCHEMA_VERSION` is the shape this build understands.
- **`MIGRATIONS`** - an ordered, named, forward-only chain. The seven
  historical additions become migrations 1-7, still guarded, so a store at any
  intermediate state converges instead of erroring on a column it already has.
  Migration N runs only when the recorded version is below N. Entries are
  appended, never edited or renumbered.
- **`_migrate`** - one transaction per migration: the change, its audit row in
  `schema_migrations` and its version stamp land together or none of them does.
  A failure mid-chain leaves a consistent store at the last good version and
  the next open resumes there. Idempotent: a current store runs no migration
  and writes nothing but the pragma read.
- **`GET /schema-version`** - the one place to ask whether the local data is
  safe with the build being run. It reports the recorded version, the target,
  whether they match, and the audit trail. Read-only.

Two deliberate behaviours worth stating. A store whose recorded version is
*above* what this build knows is refused with a clear `SchemaVersionError`
naming both numbers, never silently treated as current - an older binary
writing against a schema it does not understand is how a store is corrupted
quietly. And a store created by this build is stamped current with an empty
migration table, because the truth is that nothing was applied to it: it was
born current. The audit trail records what *ran*, not a padding of entries that
never did.

One real constraint the implementation had to respect: SQLite refuses to add a
`NOT NULL` column to a table that already has rows unless the statement carries
a default. So `datasets.format` migrates as `TEXT NOT NULL DEFAULT 'unknown'`
and `profiles.duplicate_rows` as `INTEGER NOT NULL DEFAULT 0`, and SCHEMA
declares the same defaults so that a fresh store and an upgraded store are
identical - not merely compatible. A test pins that equivalence across every
table, because "the two agree by construction" is exactly the kind of claim
that silently stops being true when the next migration lands.

NON-GOALS held: no down migrations (forward-only, always; a local single-user
             store's rollback path is a backup, not a second schema to maintain
             and get wrong), no destructive or backfilling migration (this task
             establishes the mechanism; the first migration that moves data is
             a later one), no online/rolling upgrade across a fleet (one
             process, one store), no migration CLI (the app upgrades on open).
CONSTRAINTS held: an upgrade runs on the ordinary open path and is idempotent
             (a current store writes nothing but a pragma read), fast on the
             warm path, and safe to interleave with reads; existing rows survive
             every migration unmodified (verified against the real dev store,
             34 cases); no existing test changed; nothing the analyst typed is
             logged; no new runtime dependency; the v0.1.0 store - no version,
             pre-migration shape - opens, upgrades and works, because that is
             the one store that exists in the wild.
ACCEPTANCE CRITERIA: all 9 - see the checked boxes above.
TESTS: 13 in server/tests/test_migrations.py - the fresh-store baseline, the
       legacy upgrade over a store built with the pre-migration schema, the
       audit trail, row survival, the no-op reopen, mid-chain resumption, the
       newer-than-app refusal, fresh-vs-upgraded shape equivalence across every
       table, the endpoint, and the empty-legacy edge.
VERIFICATION: server suite 315 passed (was 302, +13); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 315); web 21 passed; desktop 12
              Rust tests. All green locally; CI will run it on push. The real
              dev store was upgraded in place as a live check, not only a
              synthetic one: 34 cases intact, 7 migrations recorded.
LESSON: the first version of `_migrate` decided "is this store new?" by counting
        tables - after running SCHEMA, which creates the `schema_migrations`
        table. Every newborn store therefore looked like an old one that needed
        the whole chain, and three tests failed on the empty-audit-trail
        assertion. The fix was to decide emptiness *before* creating anything.
        The general shape: a freshness check that runs after the thing it
        detects has been created cannot detect freshness. State inspected for a
        decision must be read before the action that would change it - the same
        lesson as P6-TEMPLATE-003's `columns_used`, in a different costume.

```

### P6-UPDATE-005 contract

```
TASK ID: P6-UPDATE-005
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Distribution
GOAL: A new release tag reaches an installed app: the app says a newer build
      exists and puts the download in front of the user, and when it cannot
      know, it says so instead of claiming the app is current.

CONTEXT: the release pipeline now publishes a versioned build per tag, but an
         installed app has no way to learn that. Two facts constrain what is
         buildable now, and both are already decisions rather than gaps: the
         repository is PRIVATE (an unauthenticated release-feed request answers
         404, verified), and the app is UNSIGNED (DEC-006), so an update payload
         cannot be signature-verified and a self-replacing updater cannot be
         tested end to end. So the task delivers the half that is verifiable -
         the check - and leaves the install half as a documented slot, exactly
         as DEC-004/006 left signing.

INPUTS: the version this build was published at; a release feed.
RELEVANT FILES: server/app/updates.py (NEW), server/app/main.py,
                server/app/models.py, server/tests/test_updates.py (NEW),
                desktop/src-tauri/src/updates.rs (NEW),
                desktop/src-tauri/src/main.rs, .github/workflows/release.yml
REQUIRED CHANGE:
  - the core learns its own version, one source of truth: the version the
    release workflow already stamps from server/pyproject.toml. Resolved by
    importlib.metadata when installed or bundled, falling back to reading the
    pyproject beside the source in a dev checkout, and finally to "unknown" -
    never to a guessed number.
  - server/app/updates.py: pure functions. `parse_version` and
    `is_update_available` (semver-style tuple comparison, no dependency), and
    `latest_release` over an injected HTTP client, so the parsing and the
    comparison are tested without a network and the transport is a seam.
  - GET /updates/latest: read-only, no body accepted, nothing the caller
    supplies is written anywhere. It answers one of three truths:
    `current` (the feed named a version and it is not newer),
    `available` (it named a newer one, with its tag, its page URL and the
    published notes), or `unknown` - and `unknown` carries a reason: the feed
    was unreachable, the repository is private, the rate limit was hit, or the
    body was not the shape expected. An unknown answer is never reported as
    current, because "could not check" and "is up to date" are different
    statements and only one of them is true.
  - the shell bridges it the way it bridges /logs: a DAH > Check for
    Updates... menu item asks the core, opens the release page in the user's
    browser when one exists, and otherwise shows the reason it could not tell.
    It degrades to a sentence rather than an error at every step, and never
    panics on a body it does not recognise.
  - release.yml publishes the version, the page URL and the notes the check
    reads, so the feed and the pipeline cannot drift apart.
NON-GOALS: a self-replacing updater (unsigned builds cannot verify a payload,
           DEC-006; tauri-plugin-updater slots in when signing does, and the
           check it would consume is what this task builds), background or
           scheduled checks (a single user does not need a poller burning
           battery and network; the menu item is the trigger), auto-download
           or auto-install, a channel/staging mechanism (one release stream),
           update notifications in the web bundle.
CONSTRAINTS: the check is read-only and makes no authenticated request - no
             token is shipped and none ever can be, so a private repository is
             answered with `unknown` and a reason, never with a silent guess;
             the network call is bounded by a timeout so a hung feed cannot
             freeze a menu; nothing the analyst typed is logged; no new runtime
             dependency (httpx is already in the tree; the browser opens
             through `open`, as the reveal-logs menu already does, so the shell
             gains no crate); the existing test suites stay green and hermetic.
ACCEPTANCE CRITERIA:
- [x] the core resolves its own version from the pyproject, and the endpoint
      reports it, never a guess
- [x] a newer published version is reported as available with its tag, its
      page URL and its notes
- [x] an equal or older published version is reported as current
- [x] an unreachable or private feed is reported as unknown WITH a reason, and
      never as current
- [x] a rate-limited feed and a malformed body are each reported as unknown
      with their own reason
- [x] the comparison is a pure function, tested without a network
- [x] the endpoint is read-only: it accepts no body and writes nothing
- [x] the menu item opens the release page when an update exists and shows a
      sentence when it cannot tell
- [x] the shell degrades on every failure path, including a body it does not
      recognise, without panicking
- [x] release.yml publishes the fields the check reads
- [x] the full server suite, the P2/P3/P4 gates, the web suite and the desktop
      tests stay green
TESTS: server/tests/test_updates.py - version resolution, the pure comparison
       across older/equal/newer and malformed inputs, the three feed outcomes
       and every failure reason, each driven through an injected client so no
       test touches a network; desktop/src-tauri unit tests for the parse and
       the degradation table.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS;
              cd desktop/src-tauri && cargo test PASS.
STATE UPDATE: mark P6-UPDATE-005 done on pass; ROADMAP item 5 flips to DONE and
              P6 closes.
```

```
TASK: P6-UPDATE-005 - a new release tag reaches an installed app
ID: P6-UPDATE-005
PRIORITY: high
STATUS: DONE
SUMMARY: The release pipeline publishes a build per tag, but an installed app
         had no way to learn that. This task delivers the half of an update
         flow that is verifiable today: the app says a newer build exists and
         puts its download page in front of the user - and when it cannot know,
         it says so, instead of claiming the app is current.

Two facts decided the scope, and both are recorded decisions rather than gaps:
the repository is **private**, so an unauthenticated release-feed request
answers 404 (verified, not assumed), and the app is **unsigned** (DEC-006), so
an update payload cannot be signature-verified and a self-replacing updater
cannot be tested end to end. A full `tauri-plugin-updater` integration would
have been unverifiable code claiming a capability it cannot prove. The check
ships; the install slots in when signing does, exactly as DEC-004/006 left
signing itself.

Three pieces:

- **`server/app/updates.py` (new)** - the honest core of it. `parse_version` and
  `is_update_available` are pure functions (semver-style tuple comparison, no
  dependency, tolerant of a leading `v` and a pre-release suffix); `latest_release`
  runs over an *injected* HTTP client, so the parsing is tested without a
  network and the transport is a seam. `check_for_update` answers one of three
  truths - `current`, `available`, or `unknown` - and `unknown` always carries a
  reason: the feed was unreachable, the repository may be private, the rate
  limit was hit, or the body was not the shape expected.
- **`GET /updates/latest`** - read-only, GET-only, unauthenticated, accepts no
  body and writes nothing. The core resolves its own version from the pyproject
  (importlib metadata when installed or bundled, the file beside the source in a
  dev checkout, then "unknown" - never a guessed number).
- **`desktop/src-tauri/src/updates.rs` (new)** - the bridge, shaped exactly like
  the reveal-logs menu it sits beside: it asks the core, opens the release page
  in the browser through `open` when one exists, and otherwise shows the
  sentence. **DAH > Check for Updates...** is the menu item. Every failure path,
  including a body it does not recognise, degrades to a sentence rather than
  panicking.

The property the tests actually pin is not "does it find an update" but "does
it tell the truth". An unreachable feed, a 404, a 403, a 503, a non-JSON body, a
body without a tag and a transport timeout are each `unknown` with their own
reason - never a silent `current`, because "could not check" and "is up to
date" are different statements and only one of them is true. Verified live
against the real private repository: the answer is `unknown`, "the release feed
is not reachable; the repository may be private" - the honest one, and it
answers properly the day the repository goes public with no code change.

NON-GOALS held: no self-replacing updater (unsigned builds cannot verify a
             payload, DEC-006; the plugin slots in when signing does, and the
             check it would consume is what this task builds), no background or
             scheduled checks (a single user does not need a poller), no
             auto-download or auto-install, no channel mechanism, no web-bundle
             notification surface.
CONSTRAINTS held: read-only and unauthenticated - no token is shipped and none
             ever can be, so a private repository is a *state to report*; the
             network call is bounded by a timeout so a hung feed cannot freeze
             a menu; nothing the analyst typed is logged; no new runtime
             dependency (httpx was already in the tree, and the browser opens
             through `open` as the reveal-logs menu already does, so the shell
             gains no crate); the existing suites stayed green and hermetic -
             every feed outcome in the tests is driven through the injected
             client, so no test touches a network.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 21 in server/tests/test_updates.py - version resolution, the pure
       comparison across older/equal/newer and malformed inputs, and every feed
       outcome and failure reason through the injected client; 7 in
       desktop/src-tauri/src/updates.rs - the parse table and the degradation
       cases, including a body that is not JSON and a newer build with no page.
VERIFICATION: server suite 336 passed (was 315, +21); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 336); web 21 passed; desktop 22
              Rust tests (19 unit + 3 e2e, was 12). The live check against the
              real private repository was run by hand and answered `unknown`
              with the private-repository reason, not a false "current".
LESSON: two of the first tests failed for the same reason, and it was the
        tests' fault both times. The endpoint holds its own *imported* reference
        to `httpx_client` (`from app.updates import httpx_client`), so
        monkeypatching `updates.httpx_client` patched a name the endpoint had
        already copied - the call escaped the fake and hit the real network.
        The seam is the module the call site reads, not the module the symbol
        came from. The same misreading produced the second failure: the test
        passed `json=` to a GET, asserting a property ("no body accepted") that
        a GET cannot even express. The real property is that the route is
        GET-only, so a POST is refused with 405 before any handler runs - and
        that is what the test now asserts. A test that fails because it
        misstates the contract is still a test failure worth having, but the
        contract is verified against the route, not against an assumption about
        it.

```

### P7-SHELL-002 contract

```
TASK ID: P7-SHELL-002
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A user can hand DAH work that came from elsewhere and read the nine-axis
      audit without a terminal. POST .../evaluate answers nine verdicts and
      nothing in the shell reaches it today; this task puts a surface in front
      of it.

CONTEXT: P7-EVAL-001 shipped the core half of EVALUATE mode. The web shell
         walks the ANALYZE loop one panel per step - data, runs, findings,
         chat - and every one of those panels posts to the endpoint that owns
         its write. The evaluate endpoint is the first endpoint with no panel
         at all, and it is the flagship capability of the phase, so closing
         that one gap is the slice of the web-shell work that pays first. The
         other un-UI'd endpoints (the agent, templates, memory, EDA, the
         evidence graph, case history, case management) are later tasks in the
         same checklist item, not this one.

INPUTS: a case with at least one attached, profiled dataset; the artifact's
        code, its kind (SQL or Python) and the claim it was offered to support,
        typed or pasted.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `AxisFinding` and `Evaluation` interfaces matching the
    core's models, plus `evaluateDataset(caseId, datasetId, code, claim, kind)`
    and `listEvaluations(caseId, datasetId)`. Failures travel as `ApiError`, so
    a 400's `detail` and a 500's `request_id` reach the panel unchanged - the
    existing error contract, not a new one.
  - web/src/CaseWorkspace.tsx: an `EvaluatePanel`, shown once the case has a
    profiled dataset (an unprofiled case has no columns to audit against, and
    the panel says so rather than offering a submission that cannot succeed).
    A kind toggle between SQL and Python, a textarea for the code, an input for
    the claim, and a submit that posts to the evaluate endpoint and nothing
    else. The audit renders as nine rows, one per axis in the spec's order,
    each with its verdict as a badge - pass / concern / fail - and its sentence;
    the verdict is the summary and the sentence is the substance, so neither is
    rendered without the other. Audits already recorded over that dataset are
    listed below, newest first, so an audit is itself inspectable from the
    workspace the way a run is.
  - The panel degrades rather than breaking: a 400 (a non-read-only artifact,
    an empty code or claim, an unknown kind) shows the core's own message
    inline and the panel stays usable, because that message is the actionable
    thing - "only single read-only SELECT queries are supported" tells the
    user what to change. A 500 shows the message with its request id, as every
    other panel does.
  - When the case has several datasets the panel offers a chooser, because the
    axis verdicts are per-dataset - an artifact audited against the wrong file
    would fail every column check for a reason that is not the artifact's.
NON-GOALS: ingesting a whole notebook, dashboard, spreadsheet or report as a
           file (this task takes the code and the claim, the common core, as
           P7-EVAL-001 did), editing or re-running a past audit's artifact (the
           artifact is already stored as a run and appears in the Runs panel),
           a chart or score over the audit (the core deliberately returns no
           score), an LLM phrasing of the verdicts (deterministic, as the core
           is), a mode switcher that reorganises the workspace around ANALYZE /
           EVALUATE / LEARN (the workspace is ANALYZE's loop; EVALUATE is a
           labelled panel beside it, and a mode architecture is a later
           design), the other un-UI'd endpoints (each is its own task).
CONSTRAINTS: every write posts to the evaluate endpoint - the panel proposes
             nothing else and creates no run, finding or chart of its own;
             deterministic; no new dependency; the existing panels and their
             tests are unchanged; `tsc -b` passes (the build is CI's type gate,
             and a type error the jsdom tests cannot see fails it); the desktop
             bundle builds from the same source, so nothing may assume a
             browser-only environment; nothing the analyst typed is logged by
             the core (P5-OBSERVE-002) and the shell adds no logging of its
             own; the server suite and the gates are untouched by this change
             and stay green.
ACCEPTANCE CRITERIA:
- [x] a case with a profiled dataset shows the EVALUATE panel; a case with no
      dataset or no profile does not
- [x] submitting clean work shows all nine axes, each with a pass verdict and
      its sentence, in the spec's order
- [x] a claim quoting a magnitude the run does not contain shows a fail on
      Evidence, with the value and the sentence
- [x] a non-read-only artifact shows the core's 400 message inline; the panel
      stays usable and no audit was recorded
- [x] an audit is recorded and listed afterwards, newest first, with its claim
      and its nine verdicts
- [x] the kind toggle switches the submission between SQL and Python
- [x] a failed request never crashes the workspace: the error is a sentence
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the clean nine-axis baseline, the
       invented magnitude on Evidence, the read-only refusal rendered as a
       sentence, the recorded audit listed newest first, the panel's absence
       without a profiled dataset, and the kind toggle.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS (tsc -b
              runs first, so a type error the jsdom tests cannot see fails
              it). The server suite and the three gates are unchanged.
STATE UPDATE: mark P7-SHELL-002 done on pass; ROADMAP item 2 records EVALUATE's
              surface as delivered.
```


```

TASK: P7-SHELL-002 - EVALUATE mode in the web shell
ID: P7-SHELL-002
PRIORITY: high
STATUS: DONE
SUMMARY: The core half of EVALUATE mode shipped with P7-EVAL-001 and nothing
         in the shell could reach it. The web workspace walks the ANALYZE loop
         one panel per step - data, runs, findings, chat - and the evaluate
         endpoint was the first one with no panel at all, in the phase whose
         flagship capability it is. This task puts a surface in front of it
         without adding a single endpoint, contract or dependency: the panel
         only renders what the core already answers.

Two files of substance:

- **`web/src/api.ts`** - `AxisFinding` and `Evaluation` interfaces matching the
  core's models, and the two functions the panel needs: `evaluateDataset` (the
  submission) and `listEvaluations` (so an audit is inspectable after the fact,
  the way a run is). Failures travel as `ApiError`, so a 400's `detail` and a
  500's `request_id` reach the panel unchanged - the error contract the rest of
  the shell already uses, not a new one.
- **`web/src/CaseWorkspace.tsx`** - an `EvaluatePanel` placed after the loop it
  audits and before the assistant. It appears once a dataset is profiled (an
  unprofiled case has no columns to audit against, so the panel says so rather
  than offering a submission that cannot succeed); offers a kind toggle, a code
  textarea and a claim input; and renders nine rows - one per axis in the
  spec's own order - each a verdict badge and its sentence, because the verdict
  is the summary and the sentence is the substance and neither is rendered
  without the other. Recorded audits list below, newest first. With several
  datasets there is a chooser, because the verdicts are per-dataset and an
  artifact audited against the wrong file fails every column check for a reason
  that is not the artifact's.

The panel holds to the discipline every other panel keeps: the submit posts to
the evaluate endpoint and nothing else. The panel never runs code and never
decides whether work is sound - the endpoint does, under the same read-only
gate, row cap and hard sandbox as any other run. A 400 is part of the contract
rather than a failure: a non-read-only artifact is refused before anything
executes, and its detail ("only single read-only SELECT queries are supported")
is shown as a sentence next to a panel still ready for corrected work.

NON-GOALS held: no whole-file ingestion of notebooks, dashboards or
             spreadsheets (the code and the claim, as P7-EVAL-001 took them),
             no editing or re-running a past audit's artifact (it is already a
             run, in the Runs panel), no chart or score over the audit (the core
             returns neither), no LLM phrasing of verdicts, no mode switcher
             reorganising the workspace around ANALYZE/EVALUATE/LEARN - the
             workspace is ANALYZE's loop and EVALUATE is a labelled panel
             beside it; a mode architecture is a later design, and the other
             un-UI'd endpoints (the agent, templates, memory, EDA, the evidence
             graph, case history, case management) are their own tasks.
CONSTRAINTS held: every write posts to the evaluate endpoint alone; the panel
             creates no run, finding or chart of its own; deterministic; no new
             dependency; the existing panels and their tests are unchanged;
             `tsc -b` passes (the build is CI's type gate, and a type error the
             jsdom tests cannot see fails it); the desktop bundle builds from
             the same source and nothing assumes a browser-only environment;
             the shell adds no logging of its own.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 6 added to web/src/CaseWorkspace.test.tsx (21 -> 27) - the clean
       nine-axis baseline scoped to the audit container, the failing Evidence
       axis with its value, the read-only refusal rendered as a sentence with
       the panel still usable, the recorded-audit listing newest first, the
       kind toggle reaching the endpoint with kind: "python", and the panel's
       absence without a profile.
VERIFICATION: cd web && npm test - 27 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS; the
              server suite is untouched by this change and stays at 358 passed.
LESSON: two of the six tests failed first for the same reason - the query, not
        the component. The nine verdict badges and the workflow's stage list
        both render a checkmark and an axis name ("✓ question"), so a page-wide
        `getByText` found two elements; and userEvent parses `[` and `]` as key
        descriptors, so typing `result = []` was read as a key sequence. The
        fix for the first was to scope the query to the audit's own container
        with `within` - an assertion should name where it is looking, because a
        page is not a component. The second is a reminder that `user.type`
        types *keys*, not text: fixtures that stay clear of `[]{}` are cheaper
        than escaping them.
```

### P7-SHELL-003 contract

```
TASK ID: P7-SHELL-003
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A plan that executes itself one approved write at a time is observable
      only through the API today. This task gives it a surface: the workspace
      shows what the agent proposes, and the human's yes or no is a button
      rather than a curl.

CONTEXT: P6-AGENT-002 shipped the driver. It proposes a step; the human
         approves it by id; the write runs through the endpoint that already
         owns it. Four endpoints serve it - a read-only GET, an idempotent
         proposing POST, /approve and /reject - and not one of them has a
         panel. This is the highest-value of the un-UI'd endpoints, because the
         agent is the capability that most changes what the workspace is for:
         every other panel is a step, and this one is the loop.

INPUTS: a case with artifacts (or none - the agent's first step is to profile,
        if a dataset is attached but unprofiled).
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `AgentStep` and `AgentState` interfaces matching the core's
    models, and the four functions - `getAgentState` (read-only),
    `proposeAgentStep` (idempotent), `approveAgentStep(stepId)` and
    `rejectAgentStep(stepId, reason?)`.
  - api.ts also fixes a real gap the 409 exposes: the agent's approve/reject
    answer 409 with an OBJECT as the detail (`{detail, expected, given}`), not
    a string. The existing client copies `body.detail` straight into the
    message, so a stale approval would render as "[object Object]". The client
    now unwraps a nested `detail` when the body sends one, so the sentence the
    core wrote reaches the user - the same standard every other failure path
    already meets.
  - web/src/CaseWorkspace.tsx: an `AgentPanel`, placed beside the workflow it
    drives. It loads the read-only state, a button proposes the next step
    (idempotent, so a second click is a no-op rather than a second write), and
    a pending step renders what it WILL do - one sentence per kind, built from
    the step's own payload, so the human approves something concrete rather
    than a promise, together with Approve and Reject buttons and an optional
    rejection reason that is recorded on the step. The history lists every
    step with its status and the note the write produced, so an agent-run case
    states what it did at every point. When nothing is pending and the trail
    ends in `end`, the panel shows why the agent stopped, because an abandoned
    case should say so rather than fall silent.
  - A stale approval is a 409, never a second write: the panel shows the
    sentence and reloads, because the pending step it was looking at is no
    longer the case's pending step.
NON-GOALS: autonomy (the write never happens without the button; that is
           P6-AGENT-002's contract and this task does not relax it), editing a
           proposal before approving it (the payload is settled at proposal
           time by design - rejecting and re-proposing is the path), running
           the agent in the background or on a timer, an agent over multiple
           cases, the other un-UI'd endpoints (templates, memory, EDA, the
           evidence graph, case history, case management - each its own task).
CONSTRAINTS: the panel writes only through the four agent endpoints, and each
             write those endpoints perform still goes through the endpoint
             that owns it - the panel introduces no new write path, so the
             read-only gate, the row cap and the single finding-creation path
             are all still in force; the GET never proposes, so a page refresh
             commits nothing; deterministic; no new dependency; `tsc -b`
             passes; the existing panels and tests are unchanged; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] the panel shows the agent's state: a pending proposal, or the absence of
      one, with the history behind it
- [x] proposing is idempotent: a second call returns the same pending step and
      creates no second write
- [x] a pending step states what it will do, in a sentence built from its own
      payload, before the human decides
- [x] approving runs the step and the next proposal appears without a second
      click, with the step's note in the history
- [x] rejecting records the reason and writes nothing: no run, no finding
- [x] a stale approval is shown as a sentence, not "[object Object]", and the
      panel reloads rather than writing twice
- [x] a case the agent finished shows why it stopped
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the state rendering, the idempotent
       proposal, the payload sentence, the approve round trip, the reject with
       a reason, the 409 degradation, and the end reason.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS. The server
              suite and the three gates are untouched by this change and stay
              green.
STATE UPDATE: mark P7-SHELL-003 done on pass; ROADMAP item 2 records the agent
              surface as delivered.
```


```

TASK: P7-SHELL-003 - the agent as a surface in the web shell
ID: P7-SHELL-003
PRIORITY: high
STATUS: DONE
SUMMARY: A plan that executes itself one approved write at a time was
         observable only through the API. P6-AGENT-002 shipped the driver and
         four endpoints serve it - a read-only GET, an idempotent proposing
         POST, /approve and /reject - and not one had a panel. The workspace
         now carries an Agent panel beside the workflow it drives: it shows the
         pending proposal as a sentence built from the step's own payload, and
         the human's yes or no is a button.

Every other panel in the workspace is a step; this one is the sequence. It
keeps the agent's contract exactly - the write never happens without the
button, and the write then runs through the endpoint that owns it, so the
read-only gate, the row cap and the single finding-creation path are all still
in force for an agent-run case. The GET never proposes, so a page refresh
commits nothing; the proposing POST is idempotent, so an impatient second
click is a no-op rather than a second write; and approving a step that is no
longer the case's pending one is a 409 the panel shows as a sentence before
resyncing - never a second write.

One real gap the panel exposed in the client itself: the agent's 409 answers
with an OBJECT as the detail (`{detail, expected, given}`), and the typed
client copied `body.detail` straight into the message, so a stale approval
would have rendered as "[object Object]". The client now unwraps a nested
detail, so the sentence the core wrote reaches the user - the same standard
every other failure path already met.

NON-GOALS held: no autonomy (the write still waits for the button; that is
             P6-AGENT-002's contract and this task does not relax it), no
             editing a proposal before approving it (the payload is settled at
             proposal time by design - reject and re-derive is the path), no
             background or timer-driven running, no agent across cases, no new
             endpoints for the other un-UI'd capabilities.
CONSTRAINTS held: writes only through the four agent endpoints, each of which
             still writes through the endpoint that owns it; no new write path;
             deterministic; no new dependency; `tsc -b` passes; the existing
             panels and tests unchanged; the desktop bundle builds from the
             same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 7 added (web suite 27 -> 34) - six in CaseWorkspace.test.tsx: the state
       rendering, the idempotent proposal, the payload sentence, the approve
       round trip with the next proposal arriving in the same response, the
       reject with a reason writing nothing, the 409 shown as a sentence and
       never as "[object Object]", and the end reason; one in api.test.ts for
       the nested-detail unwrap.
VERIFICATION: cd web && npm test - 34 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched and stay green.
LESSON: the suite had no spy-reset between tests, so the module-level mocks
        accumulated call history across the file; the first negative assertion
        ("approve was not called") therefore answered for every test that had
        run before it. A beforeEach with vi.clearAllMocks is what makes "not
        called" mean "not called in this test". The same class of bug hid
        inside the component too: the panel's refresh() cleared the error
        before resyncing, so a 409 message was set and then erased a tick
        later - an error handler that runs after the thing it prepared for.
        Both are the same shape: state that outlives the action that produced
        it, read as though it were fresh.
```

### P7-EVAL-001 contract
```
TASK ID: P7-EVAL-001
MILESTONE: P7 Product Modes
CAPABILITY: EVALUATE mode
GOAL: Audit existing analytical work. A user submits work someone already did -
      a SQL query and the claim it was used to support - and DAH answers the
      nine questions the specification names, each against the data rather than
      against the claim's own confidence.

CONTEXT: the master specification defines three product modes. ANALYZE is the
         one that exists and it is finished through P6. EVALUATE is the second:
         "audit existing analytical work", over inputs that can include SQL,
         Python, a notebook, a dashboard, a spreadsheet, a report or
         AI-generated analysis, judged on Question / Data / Quality / Method /
         Calculation / Evidence / Claim / Visualization / Limitations.
         Most of the machinery already exists and is validated - read-only
         execution with a row cap, deep profiling, rerun determinism, the
         evidence graph, the honesty budgets that bound what a claim may quote.
         What does not exist is the frame: today every one of those primitives
         serves the user's *own* analysis. EVALUATE turns them on work that
         came from elsewhere, and that turn is the whole task.

INPUTS: a case with at least one attached, profiled dataset; a submitted
        artifact - its code (SQL or Python), the kind, and the claim the code
        was offered as evidence for.
RELEVANT FILES: server/app/evaluator.py (NEW), server/app/main.py,
                server/app/models.py, server/app/db.py,
                server/tests/test_evaluator.py (NEW)
REQUIRED CHANGE:
  - server/app/evaluator.py: a pure module, the way evidence.py and workflow.py
    are pure. `evaluate` takes the artifact, the dataset's profile and the
    run it produced, and returns one finding per spec axis. Nothing is computed
    that the data does not contain; nothing is asserted the run does not show.
  - the nine axes, each a named check with a verdict and a sentence:
    * Question - the claim is stated and is answerable from this dataset.
    * Data - every column the code reads exists in the profile, and the
      profile's own caveats (nulls, duplicates) are surfaced as limitations.
    * Quality - the profile's missing-value and duplicate-row counts reach the
      verdict, so a claim over a column that is 40% null is a *finding*, not a
      pass.
    * Method - the code is read-only (the existing gate), bounded by the row
      cap, and deterministic: an artifact whose result depends on unordered
      output is flagged, because a rerun could disagree without anything
      changing.
    * Calculation - the code runs, and it reproduces: the artifact is executed
      twice and the two results must agree, the same standard a finding's
      validation holds (P4-VALID-005).
    * Evidence - the claim's magnitudes all appear in the result the code
      actually produced, checked against the same honesty budget a draft is
      checked against (P3-AI-012): a claim quoting a number the run does not
      contain is the single most common way an analysis lies.
    * Claim - the claim is specific enough to be wrong: it names a magnitude or
      a direction, not only a topic. "Revenue declined in north" is auditable;
      "revenue was analysed" is not, and the verdict says so.
    * Visualization - whether the artifact's result is chartable, and if a
      chart exists, whether its axes match the result's own columns. Not a
      requirement that one exist - an honest "no chart, and none needed" is a
      valid verdict.
    * Limitations - the accumulated caveats, stated as sentences rather than
      as an error code.
  - POST /cases/{id}/datasets/{id}/evaluate accepts the artifact and the claim,
    executes the code through the *existing* run endpoints' engine (never a
    second code path), and returns the evaluation. It writes the artifact as a
    run and the evaluation beside it, so an audit is itself inspectable and
    reproducible - the standard every other artifact in DAH is held to.
  - GET .../evaluations lists them, newest first, the same as runs and plans.
  - the endpoint refuses an artifact whose code is not read-only, exactly as
    the run endpoints do, and refuses a claim that is empty; both are 400s with
    a message, never a 500.
NON-GOALS: evaluating a notebook, a dashboard, a spreadsheet or a report as a
           whole file (this task takes the code and the claim, which is the
           common core of all of them; whole-file ingestion is a later task),
           an LLM judgement of the claim (deterministic by default, as every
           other assistant slice is - the LLM may later rephrase, never
           decide), a score or a grade (a verdict per axis with a sentence is
           the honest output; a number would imply a precision the axes do not
           have), evaluating an artifact against a dataset it never ran
           against, fixing the artifact.
CONSTRAINTS: the code executes under the same read-only gate, row cap and
             (for Python) hard sandbox as any other run - EVALUATE earns no
             privilege, and untrusted code is the *premise* of the mode; the
             honesty budgets from P3-AI-011..014 are reused unchanged; an
             evaluation never mutates the case, the dataset or any run, only
             appends its own row; nothing the analyst submitted is logged (the
             log holds method/path/status/duration, as P5-OBSERVE-002 pins);
             deterministic by default with `source` recorded; no new runtime
             dependency; the suite, the P2/P3/P4 gates, the web and desktop
             suites stay green.
ACCEPTANCE CRITERIA:
- [x] a clean artifact over a clean dataset passes all nine axes
- [x] an artifact reading a column the dataset lacks is flagged on Data, not
      silently passed
- [x] a claim quoting a magnitude absent from the result is flagged on
      Evidence with the value it should have been
- [x] a claim too vague to be wrong ("revenue was analysed") is flagged on
      Claim
- [x] a non-deterministic artifact (unordered output treated as a ranking) is
      flagged on Method
- [x] an artifact over a mostly-null column reports the null share as a
      Quality limitation, not a pass
- [x] an artifact that does not reproduce is flagged on Calculation
- [x] a non-read-only artifact is refused with 400 before anything executes
- [x] an evaluation is persisted, listed and inspectable; it never mutates
      another artifact
- [x] every verdict carries a sentence a reader can act on, not only a code
- [x] the full server suite, the P2/P3/P4 gates, the web suite and the desktop
      tests stay green
TESTS: server/tests/test_evaluator.py - the clean baseline; each axis's failure
       case (unknown column, invented magnitude, vague claim, unordered
       ranking, null-heavy column, non-reproducing artifact, non-read-only
      refusal); the persistence and listing round trip; the no-mutation
       invariant; 404s including a cross-case dataset.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS;
              cd desktop/src-tauri && cargo test PASS.
STATE UPDATE: mark P7-EVAL-001 done on pass; ROADMAP item 1 flips to DONE.
```


```
TASK: P7-EVAL-001 - audit existing analytical work against nine axes
ID: P7-EVAL-001
PRIORITY: high
STATUS: DONE
SUMMARY: EVALUATE mode - the spec's second product mode. Until now every
         primitive DAH has served the analyst's *own* work: read-only
         execution, deep profiling, rerun validation, the evidence graph, the
         honesty budgets. This task turns those primitives on work that came
         from elsewhere. A user submits an artifact - its code (SQL or Python)
         and the claim that code was offered to support - and DAH answers the
         nine questions the specification names, each against the data rather
         than against the claim's own confidence.

Three pieces:

- **`server/app/evaluator.py` (new)** - a pure module, the way evidence.py and
  workflow.py are pure. `evaluate()` returns one finding per axis - question,
  data, quality, method, calculation, evidence, claim, visualization,
  limitations - each a verdict (pass / concern / fail, deliberately not a
  score: a single number would imply a precision nine heterogenous axes do not
  have) and a sentence a reader can act on. The Evidence axis reuses the
  drafter's honesty budget unchanged (`_allowed_numbers`, `_numbers_in`), so a
  claim quoting a magnitude the run does not contain is caught by the same
  standard a draft is judged by.
- **`POST /cases/{id}/datasets/{id}/evaluate`** - executes the artifact through
  the *existing* run engine, never a second code path, so the read-only gate,
  the row cap and the hard sandbox are the ones every other run answers to.
  EVALUATE earns no privilege, and untrusted code is the premise of the mode.
  The artifact is stored as a run and the evaluation beside it, so an audit is
  itself inspectable and reproducible. `GET .../evaluations` lists them newest
  first.
- **`server/app/db.py`** - the `evaluations` table, migration 8, so an audit is
  a first-class artifact rather than a transient response.

Four judgement calls the contract left open, each written into the code:

- **A non-read-only artifact is a 400 before anything executes**, exactly as the
  run endpoints refuse one. A mutation is not an artifact to audit - it is a
  request the store must never honour, and it is refused before the engine is
  asked to do anything. But an artifact that *is* read-only and still fails at
  run time is a **Calculation finding, not a 400**: the work is not the user's
  to fix, it came from elsewhere, and "this does not run" is the answer an
  auditor exists to give.
- **An unknown column is a Data fail, never a silent pass.** The first version
  of the check intersected the code's identifiers with the profile's columns,
  which drops every name the dataset lacks - the axis passed on exactly the
  case it exists to catch. The fix reuses the generator's own notion of a
  column read (`_sql_identifiers`, `_python_read_columns`, `_SQL_KEYWORDS`),
  so an invented name is *reported* rather than filtered away.
- **A chart is not required.** The contract's baseline is that a clean artifact
  passes all nine axes, and "no chart, and none needed" is a valid verdict,
  because a table's numbers are checkable without one. What *is* a fail is a
  chart whose axes are not the result's own columns - a check the previous
  shape (a bare `has_chart` boolean) could not make, because a boolean cannot
  be wrong.
- **A single-row result is deterministic without an ORDER BY**, because one row
  has no row order to disagree about; the Method axis flags only an unordered
  *multi-row* result, whose order a rerun may present differently.

NON-GOALS held: no whole-file ingestion of notebooks, dashboards or
             spreadsheets (this task takes the code and the claim, which is the
             common core of all of them), no LLM judgement of the claim
             (deterministic by default, as every assistant slice is; an LLM may
             later rephrase a sentence, never decide one), no score or grade,
             no evaluating an artifact against a dataset it never ran against,
             no fixing the artifact.
CONSTRAINTS held: the code executes under the same read-only gate, row cap and
             hard sandbox as any other run; the honesty budgets from
             P3-AI-011..014 are reused unchanged; an evaluation appends its own
             row and mutates nothing else (pinned by a test that counts runs,
             findings and evaluations around one); nothing the analyst
             submitted is logged (the log holds method/path/status/duration, as
             P5-OBSERVE-002 pins); deterministic, `source` recorded; no new
             runtime dependency; the suite, the gates and the web and desktop
             suites stayed green.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 22 in server/tests/test_evaluator.py - the clean baseline across all nine
       axes, each axis's failure case (unknown column, invented magnitude, vague
       claim, unordered ranking, null-heavy column, non-reproducing artifact,
       artifact that does not run), the read-only refusal with nothing written,
       the empty-code / empty-claim / bad-kind 400s, both the SQL and the Python
       artifact paths, persistence and newest-first listing, the no-mutation
       invariant, 404s including a cross-case dataset, the unprofiled dataset,
       and the pure module's chart branches - which the endpoint cannot reach,
       because a chart cannot exist for the run the request itself creates.
VERIFICATION: server suite 358 passed (was 336, +22); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 358); web 21 passed; desktop 22
              Rust tests. All green locally; CI will run it on push.
LESSON: three of the eleven criteria were satisfied by code that had not been
        written yet, and the missing half was the interesting half. The Data
        axis "passed" an unknown column because it asked "which of the code's
        names are in the profile?" instead of "which are NOT?"; the
        Visualization axis could never pass at all, because it treated the
        absence of a chart as a defect the contract explicitly calls a valid
        verdict; and the read-only refusal had been softened into a Calculation
        finding, which is kinder but is not what the contract asks. Each was
        found the same way - reading the acceptance criteria as assertions and
        asking what code would make each one true. The general shape: a check
        that filters its inputs before testing them is testing the survivors,
        and a check that cannot fail cannot pass either.
```

### P7-SHELL-004 contract

```
TASK ID: P7-SHELL-004
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A case can be renamed, duplicated and deleted from the shell. These are
      the everyday operations on the front door, and today all three answer
      only through the API.

CONTEXT: the three endpoints have existed since P2-CASE-010 and are tested in
         the core, but the case list renders a row per case whose only
         affordance is opening it. A user who mistyped a question cannot fix
         it; a finished investigation cannot be copied as a starting point for
         a variant; and a case that has served its purpose cannot be removed,
         so the list only ever grows. This is the cheapest slice of the
         web-shell gap, and it is the one a user meets first.

INPUTS: the case list; for a rename, the edited question and the dataset label.
RELEVANT FILES: web/src/api.ts, web/src/CaseList.tsx, web/src/CaseList.test.tsx,
                web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `updateCase(caseId, {question?, dataset?})` for the PATCH,
    `duplicateCase(caseId)` for the POST, `deleteCase(caseId)` for the DELETE.
    The core's `Case` also carries `template_id`, which the shell's type now
    admits as optional so a templated case round-trips without the type
    disagreeing with the payload.
  - web/src/CaseList.tsx: each row keeps opening the case as its primary
    affordance and gains three actions - Rename, Duplicate, Delete. Rename is
    an inline edit of the question and the dataset label with Save and Cancel,
    so a correction never needs a second screen. Duplicate creates the copy and
    the list reloads with it. Delete is irreversible - the core removes the
    case row, every child and the case's on-disk directory - so it asks twice:
    a first click arms the row and a second, labelled with what will be lost,
    is the one that removes it. Nothing is deleted by a single click, and the
    armed state is per row, so confirming one case never endangers another.
  - Every action reports a failure as the core's own sentence and leaves the
    list usable, the way the list already does for a failed load.
NON-GOALS: bulk operations (a single-user tool with a handful of cases does not
           need selection machinery), undo for a delete (the core's contract is
           that deletion is final and its data dir goes with it; an undo would
           be a second store to keep consistent), renaming a dataset label that
           renames the file on disk (the label is a case property, not a
           filename), templates (their own task), case history and the evidence
           graph (read-only views, their own task).
CONSTRAINTS: each action calls its endpoint and nothing else; the list reloads
             after a write rather than mutating its own copy, so what it shows
             is what the core has; `tsc -b` passes; no new dependency; the
             existing list tests and the workspace stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case can be renamed inline, and the list shows the corrected question
- [x] a duplicate appears in the list after the action
- [x] a delete needs two clicks, and the second names what it removes
- [x] an armed delete is per row: confirming one case deletes no other
- [x] a failed action shows the core's message and leaves the list usable
- [x] opening a case is still the row's primary affordance
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseList.test.tsx - the rename round trip, the duplicate
       appearing, the two-click delete, the per-row isolation, and a failure
       rendered as a sentence.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS. The server
              suite and the three gates are untouched by this change and stay
              green.
STATE UPDATE: mark P7-SHELL-004 done on pass; ROADMAP item 2 records case
              management as delivered.
```


```
TASK: P7-SHELL-004 - rename, duplicate and delete a case from the shell
ID: P7-SHELL-004
PRIORITY: medium
STATUS: DONE
SUMMARY: The three everyday operations on the front door answered only through
         the API. The case list rendered a row per case whose only affordance
         was opening it: a mistyped question could not be fixed, a finished
         investigation could not be copied as the start of a variant, and a
         case that had served its purpose could not be removed, so the list
         only ever grew. All three are buttons now.

Each row keeps opening the case as its primary affordance and gains Rename,
Duplicate and Delete:

- **Rename** is inline - the question and the dataset label become inputs on
  the row itself, with Save and Cancel, so a correction never needs a second
  screen and a cancelled edit restores what was there.
- **Duplicate** creates the copy and the list reloads with it.
- **Delete** asks twice, because the core's deletion is final and takes the
  case's on-disk directory with it. A first click arms the row; the second is
  labelled with the case's own question ("Delete "Why did revenue decline?" for
  good"), because the question is the thing a user would be sorry to lose. The
  armed state is per row - confirming one case never endangers another, and an
  armed row offers "Keep it" as an escape.

Every action reports a failure as the core's own sentence and leaves the list
usable, the way a failed load already did.

NON-GOALS held: no bulk operations (a single-user tool with a handful of cases
             does not need selection machinery), no undo for a delete (the
             core's contract is that deletion is final; an undo would be a
             second store to keep consistent), no file rename behind a dataset
             label (the label is a case property), no templates, history or
             evidence-graph surfaces (their own tasks).
CONSTRAINTS held: each action calls its endpoint and nothing else, and the list
             reloads after a write rather than mutating its own copy, so what
             it shows is what the core has; `tsc -b` passes; no new dependency;
             the existing list and workspace tests stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 5 added to web/src/CaseList.test.tsx (web suite 34 -> 39) - the rename
       round trip, the duplicate appearing, the two-click delete whose second
       click names the case, the per-row isolation of an armed delete, and a
       failed delete rendered as a sentence with the case still present.
VERIFICATION: cd web && npm test - 39 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched and stay green.
LESSON: the two-click delete and the aria-labels solved each other. The first
        draft named the buttons "Rename"/"Duplicate"/"Delete" and the tests
        could not address one case among two; per-row aria-labels naming the
        question fixed the tests AND are the accessible thing to do - an action
        button that does not say which case it acts on is ambiguous to a screen
        reader for exactly the reason it was ambiguous to a test. The same
        spy-accumulation bug CaseWorkspace hit recurred here, and for the same
        reason: this file's module-level mocks had no reset between tests.
```

### P7-SHELL-005 contract

```
TASK ID: P7-SHELL-005
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A finished investigation becomes a reusable template and a template
      becomes a new case, both from the shell. Today the four template
      endpoints answer only through the API, so the shape of a case that was
      worked out once is never offered to the next one.

CONTEXT: P6-TEMPLATE-003 made a template carry the analytical shape of the case
         it came from - its plan and which engine produced it, the proposals it
         offered, and its findings' statements with the verdicts validation gave
         them - and made a case started from a template offer that shape as
         proposals a human accepts. Four endpoints serve it and all are tested
         in the core; none has a surface. Templates are not case children and
         outlive the case they came from, so they do not belong inside a case
         workspace - they belong on the front door beside the case list.

INPUTS: the case list screen (where templates are listed and started); a case
        workspace (where one is promoted); an optional name for a promotion.
RELEVANT FILES: web/src/api.ts, web/src/Templates.tsx (NEW), web/src/CaseList.tsx,
                web/src/CaseWorkspace.tsx, web/src/index.css,
                web/src/Templates.test.tsx (NEW), web/src/CaseWorkspace.test.tsx,
                web/src/api.test.ts
REQUIRED CHANGE:
  - web/src/api.ts: `Template`, `TemplateShape`, `TemplateProposal` and
    `TemplateFindingSummary` types matching the core's models, and four
    functions - `promoteCaseToTemplate(caseId, name?)` for the POST, a GET
    `listTemplates`, `createCaseFromTemplate(templateId, {question?, dataset?})`
    for the POST that seeds a case, and `deleteTemplate(templateId)` for the
    DELETE. A DELETE answers 204 and an empty body, so the shared request
    helper returns nothing for an empty body rather than trying to parse one -
    without that, every DELETE the shell makes fails at the parse after
    succeeding at the write.
  - web/src/Templates.tsx (NEW): a section for the front door. Each template
    row shows its name, the question and the dataset label it seeds, and a
    shape summary - how many proposals it carries and how many findings, with
    each finding's validation verdict - so a template says what kind of
    investigation it is, not only what it asked. A template with no shape says
    so instead of showing zeroes that imply an empty case. Each row has two
    actions: **Start a case from this**, which posts to the from-template
    endpoint and opens the seeded case, and **Retire**, which removes the
    template. A template carries no data of its own - no datasets, runs or
    findings travel with it - and the core's contract is that cases already
    created from a template are unaffected when it goes, degrading to normal
    derivation, so retiring needs no second confirmation the way deleting a
    case does.
  - web/src/CaseList.tsx: the templates section renders below the case list on
    the same screen, because templates are the other thing a user comes to the
    front door for.
  - web/src/CaseWorkspace.tsx: a **Save as a template** panel. The name is
    optional - the core defaults it to the case's question, because the common
    gesture needs no second prompt - and a promotion reports success as a
    sentence and leaves the workspace usable on failure.
  - Every write posts to its endpoint and nothing else; the list reloads after
    a write rather than mutating its own copy; a failure degrades to the
    core's own sentence.
NON-GOALS: editing a template (a template is a snapshot; changing one would
           make it disagree with the case it was captured from - the honest
           edit is to fix the case and promote again), a template gallery or
           sharing (single user, local-first), promoting from the case list
           (promotion belongs to the workspace that shows what would be
           captured), cross-case memory, EDA, the evidence graph and case
           history (read-only views, their own tasks).
CONSTRAINTS: each action calls its endpoint and nothing else; `tsc -b` passes;
             no new dependency; the existing list, workspace and client tests
             stay green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case can be saved as a template from its workspace, with an optional name
- [x] a promotion without a name is named for the case's question
- [x] the template list shows a template's name, question, dataset and shape
- [x] a shapeless template is shown as such, not as an empty case
- [x] a case started from a template is created and opened
- [x] a template can be retired, and cases created from it are unaffected
- [x] a failed write shows the core's message and leaves the screen usable
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/Templates.test.tsx - the list and its shape summary, the
       shapeless template, starting a case, retiring, and a failure rendered as
       a sentence; web/src/CaseWorkspace.test.tsx - the promotion, named and
       unnamed; web/src/api.test.ts - an empty 204 body parses to nothing.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-005 done on pass; ROADMAP item 2 records templates
              as delivered.
```


```
TASK: P7-SHELL-005 - templates in the web shell
ID: P7-SHELL-005
PRIORITY: medium
STATUS: DONE
SUMMARY: The four template endpoints answered only through the API, so the
         shape of an investigation worked out once was never offered to the
         next one from the shell. A finished case becomes a template from its
         workspace, and a template becomes a new case from the front door.

Two surfaces:

- **web/src/Templates.tsx (NEW)** sits on the case-list screen, because
  templates are not case children and outlive the case they came from - they
  are the other thing a user comes to the front door for. Each row shows the
  name, the question and the dataset label it seeds, and a **shape summary**:
  how many proposals it carries and how many findings, with each finding's
  validation verdict counted. A name alone cannot say whether a template is a
  finished method or a question-only skeleton, so a shapeless template *says
  so* - "A question-only skeleton - no shape was captured" - rather than
  showing zeroes that would imply an empty investigation. Each row has
  **Start a case from this**, which posts to the from-template endpoint and
  opens the seeded case, and **Retire**. Retiring is one click, deliberately:
  a template carries no data of its own, and the core's contract is that cases
  created from it are unaffected when it goes - `_template_of` answers None and
  the case degrades to normal derivation - so unlike deleting a case, nothing
  is lost.
- **CaseWorkspace** gains a **Save as a template** panel. The name is optional
  - the core defaults it to the case's question, because the common gesture
  needs no second prompt - and a promotion reports the saved name as a
  sentence, so a user learns where to find it.

One real bug surfaced while wiring the DELETE, and it was not in this task's
endpoints: the shared `request` helper parsed every successful body as JSON,
and the core answers 204 with an empty body for all three of the shell's
DELETEs (a case, a dataset, now a template). The write had already landed when
the response arrived, so the client threw "Unexpected end of JSON input" and
the row reported a success as "The action failed". The helper now returns
nothing for an empty body. The case-delete that P7-SHELL-004 shipped was
broken in exactly this way - its tests mocked the client, so the path never
ran for real - and it is fixed by the same two lines.

NON-GOALS held: no editing a template (a template is a snapshot; changing one
             would make it disagree with the case it was captured from, and
             the honest edit is to fix the case and promote again), no gallery
             or sharing (single user, local-first), no promoting from the list
             (promotion belongs to the workspace that shows what would be
             captured), and the remaining shell surfaces (cross-case memory,
             EDA, the evidence graph, case history) stay unowned.
CONSTRAINTS held: every write posts to its endpoint and nothing else, and the
             template list reloads after a write rather than mutating its own
             copy; `tsc -b` passes; no new dependency; the desktop bundle
             builds from the same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 11 added (web suite 39 -> 50) - 7 in the new web/src/Templates.test.tsx
       (the shape summary, the shapeless template, the empty list, starting a
       case, retiring, a failed start rendered as a sentence, a failed load),
       3 in web/src/CaseWorkspace.test.tsx (the unnamed promotion naming it for
       the question, a chosen name, a failed promotion leaving the panel
       usable), and 1 in web/src/api.test.ts (an empty 204 body parses to
       nothing).
VERIFICATION: cd web && npm test - 50 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: three of the eleven tests failed on the first run for reasons that
        were the fixtures' fault, and each taught the same thing - a test
        suite is only as honest as the DOM it asserts against. The template
        row renders the question and the dataset label as one sentence, so an
        exact `getByText('sales.csv')` could not find it; the list screen now
        loads templates beside the cases, so a test that mocked only the case
        calls saw a second alert from an unresolved spy; and the WHATWG
        Response constructor refuses a body with a 204, so the client's own
        fixture had to build one without. Each was the test describing a DOM
        the component did not produce, and the component was right.
```
