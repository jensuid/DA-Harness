# DAH - Task Backlog

## P0 Foundation - PASSED

| Task ID | Status | Verification |
|---------|--------|--------------|
| P0-INFRA-001 | DONE | pytest passes; live `GET /health` returns 200 |
| P0-WEB-002 | DONE | Vitest 2/2 pass; build succeeds; `/api` proxy reaches backend |
| P0-DATA-003 | DONE | 5/5 pytest pass; case survives restart; DuckDB profiles CSV |

## P1 Vertical Slice - PASSED

| Task ID | Status | Verification |
|---------|--------|--------------|
| P1-DATA-001 | DONE | CSV attaches, file on disk, survives reopen |
| P1-DATA-002 | DONE | profile (rows/columns/null counts) stored against dataset |
| P1-ANALYSIS-003 | DONE | read-only SQL runs persisted with results |
| P1-EVIDENCE-004 | DONE | evidence chain finding -> run -> dataset |
| P1-VALID-005 | DONE | rerun reproduces or demotes the finding |

## P2 MVP

Goal: turn the vertical slice into a genuinely usable analytical application.
The loop is proven; P2 broadens it. AI joins last, only after the deterministic
surface is complete (roadmap section 5).

```
Parquet/Excel + richer profiling + Python execution + charts
+ case management + AI planning (structured) + export
```

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P2-DATA-006 | Data Layer (breadth) | M | DONE | P1 done | Parquet and Excel attach alongside CSV |
| P2-DATA-007 | Data Layer (depth) | M | DONE | P2-DATA-006 | Profile covers duplicates, types, basic stats |
| P2-ANALYSIS-008 | Analysis Workspace | M | DONE | P2-DATA-006 | Read-only Python executes against a dataset, result persisted |
| P2-ANALYSIS-009 | Analysis Workspace | M | DONE | P2-ANALYSIS-008 | Chart image persisted from a run result |
| P2-CASE-010 | Analysis Case | M | DONE | P1 done | Rename, duplicate, delete cases |
| P2-AI-011 | AI Planning | M | DONE | P2-ANALYSIS-008 | Structured plan (sub-questions, hypotheses) from a question + profile |
| P2-CASE-012 | Export | M | DONE | P2-AI-011 | Case exports as a self-contained JSON package |

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

## P3 V1

Goal: make the MVP substantially better for repeated real-world use (roadmap
section 6). Entry order follows ai/ROADMAP.md; hardening first because the P3
AI code-generation work multiplies the risk of the P2 soft sandbox.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P3-SEC-001 | Analysis Workspace (hardening) | M | DONE | P2-ANALYSIS-008 | Python runs in a separate process under an OS sandbox; writes outside scratch, network, and runaway CPU are bounded and reported as 400 |
| P3-CHART-002 | Analysis Workspace (raster charts) | M | DONE | P3-SEC-001 | PNG rendering behind the same interface; bar geometry and export round trip verified |
| P3-DATA-003 | Data Layer (multi-dataset) | M | DONE | P2 done | Join runs across attached files; validation, duplicate, export all carry the dataset list |
| P3-FLOW-004 | Analysis workflow (guided) | M | DONE | P3-DATA-003 | Derived stage and single next action from the case's artifacts |
| P3-ANALYSIS-005 | Analysis Workspace (richer EDA) | M | DONE | P3-FLOW-004 | Segment / correlate / distribution compile to read-only SQL |
| P3-EVIDENCE-006 | Evidence (richer lineage) | M | DONE | P3-ANALYSIS-005 | Case-wide evidence graph with claim-to-source tracing |
| P3-CASE-007 | Analysis Case (reuse) | M | DONE | P3-EVIDENCE-006 | Case search, case history timeline, and case templates |

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

### Carried follow-ups (still open)

- Validation of Python runs still answers a clear 400 "not supported yet". The
  hard sandbox (P3-SEC-001) makes re-execution safe, so the gate is now
  implementable: rerun the stored script in the sandbox and compare the result
  shape, the way SQL validation compares rows. DELIVERED as P3-VALID-010.
- The packaged app is unsigned: macOS gatekeeps the first launch (right-click,
  Open). Signing and notarization are P5.

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
