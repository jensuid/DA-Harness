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

### Carried follow-ups (still open)

- Validation of Python runs still answers a clear 400 "not supported yet". The
  hard sandbox (P3-SEC-001) makes re-execution safe, so the gate is now
  implementable: rerun the stored script in the sandbox and compare the result
  shape, the way SQL validation compares rows. DELIVERED as P3-VALID-010.
- The packaged app is unsigned: macOS gatekeeps the first launch (right-click,
  Open). Signing and notarization are P5.

## P6 Post-Launch Evolution

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P6-MEMORY-001 | Analysis memory (cross-case recall) | DONE | 11 tests in test_memory.py; P2/P3/P4 gates PASS |
| P6-AGENT-002 | Agentic analysis | DONE | 24 tests in test_agent.py; P2/P3/P4 gates PASS |
| P6-TEMPLATE-003 | Case reuse (templates carry the shape) | DONE | +11 tests in test_case_templates.py; P2/P3/P4 gates PASS |

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
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