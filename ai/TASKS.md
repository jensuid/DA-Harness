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
