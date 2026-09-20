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

## P4 Production Candidate

Goal: make DAH reliable, secure, usable and observable enough for controlled
external users (roadmap section 7). Entry order follows ai/ROADMAP.md's
checklist; the gate comes first because a phase is done when a gate says so.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P4-VERIFY-001 | Verification (P3 gate) | M | DONE | P3 complete | One journey exercises multi-dataset joins, the hard sandbox and all four assistant slices end to end |
| P4-RELIABILITY-002 | Reliability | M | DONE | P4-VERIFY-001 | Input errors answer 400 with the engine's message; a harness fault answers 500 instead of a 400 that blamed the analyst |
| P4-UX-003 | UX (case workspace + chat) | M | DONE | P4-RELIABILITY-002 | Cases can be searched and opened; the workspace shows the derived stage, datasets and runs, and the case answers questions with visible citations |
| P4-UX-004 | UX (run-scoped assistant surfaces) | M | DONE | P4-UX-003 | The workspace walks the loop one panel per step - attach+profile, generate code, run, interpret, draft, accept, validate - and every write posts to the endpoint that owns it |
| P4-VALID-005 | Validation (rerun determinism) | M | DONE | P4-UX-004 | Reproduction compares SQL rows as a multiset, so an unordered GROUP BY answering in a different order is a match, not a drift |
| P4-PERF-006 | Performance (large datasets) | M | DONE | P4-VALID-005 | Profiling no longer materialises every row to read a description; the result cap and profile correctness are pinned at scale |
| P4-CI-007 | Distribution (CI + signing decision) | M | DONE | P4-PERF-006 | macOS CI runs the server suite and both gates, the web suite and build, the desktop lifecycle tests against a live core, and a sidecar packaging build; signing deferred to P5 by DEC-004 |

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

## P5 Production Grade

Goal: make DAH tested, hardened, distributable, maintainable, observable and
supportable (roadmap section 8). Entry order follows ai/ROADMAP.md's checklist;
the gate comes first because a phase is done when a gate says so.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P5-VERIFY-001 | Verification (P4 gate) | M | DONE | P4 complete | One journey walks the edges: the error taxonomy, rerun determinism, the result cap, graceful degradation |
| P5-OBSERVE-002 | Observability | M | DONE | P5-VERIFY-001 | The core writes a size-capped rotating log into the user's data dir, `GET /logs` tails it read-only, and nothing the analyst typed ever lands in it |
| P5-RELIABILITY-003 | Error contract | M | DONE | P5-OBSERVE-002 | A 500 answers a JSON envelope with a request id that maps to the traceback in the log, and the id is surfaced to the user |
| P5-CI-004 | CI floor | S | DONE | P5-RELIABILITY-003 | Every job runs on macos-13 (Ventura), the minimum supported macOS, and the packaged-core smoke now asserts file logging lands in the data dir |
| P5-RELEASE-005 | Release automation | M | DONE | P5-CI-004 | A tag matching server/pyproject.toml's version builds, smokes and publishes an unsigned .app as a flagged pre-release with its checksum |
| P5-UX-006 | Shell UX | S | DONE | P5-RELEASE-005 | A Reveal DAH Logs menu item asks the core where its log is and opens the folder in Finder with it selected |

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