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