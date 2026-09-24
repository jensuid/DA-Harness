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

- DMG bundling depends on the local `create-dmg` happening to be the tool
  Tauri's `bundle_dmg.sh` expects; it failed on one build and succeeded on
  another with no code change between. The published artifact is the ditto
  zip, which is what `release.yml` ships, so this is cosmetic - but a
  deterministic local build is worth either pinning the tool or dropping the
  DMG from the local steps.
- The app icon's proportion was chosen blind (52% of the canvas), because
  icons cannot be viewed. `desktop/src-tauri/icons/icon.png` is the committed
  52% source. The recipe to re-cut it: flatten the source onto opaque
  navy, scale the flattened artwork, centre it on a fresh navy canvas, apply
  the squircle mask (rounded rectangle, 224px radius on a 1024 canvas), then
  `iconutil -c icns` from a full iconset. Rebuild with
  `cd desktop && npm run tauri -- build --config '{"version":"x.y.z"}'`.
- `web/src/CaseWorkspace.test.tsx`'s question-refinement describe still sits
  outside the `CaseWorkspace` describe, so it inherits the previous test's
  persisted plan and run reads. P8-DECISION-008 gave its own decision
  describe a `beforeEach` for the same reason and noted this one; it is a
  fragility, not a failure.
- The packaged app is unsigned: macOS gatekeeps the first launch (right-click,
  Open). Signing and notarization are deferred indefinitely by DEC-006 (DAH is
  single-user) - not blocked, and worth revisiting if the user count moves
  beyond one.
- GitHub Actions refuses every job with "recent account payments have failed";
  nothing pushed since `c73118c` has run in CI, and v0.2.0-v0.3.2 were built
  locally from the same steps `release.yml` runs. Fix at Settings > Billing &
  plans; no code change.

## P6 Post-Launch Evolution

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P6-MEMORY-001 | Analysis memory (cross-case recall) | DONE | 11 tests in test_memory.py; P2/P3/P4 gates PASS |
| P6-AGENT-002 | Agentic analysis | DONE | 24 tests in test_agent.py; P2/P3/P4 gates PASS |
| P6-TEMPLATE-003 | Case reuse (templates carry the shape) | DONE | +11 tests in test_case_templates.py; P2/P3/P4 gates PASS |
| P6-MIGRATE-004 | Maintainability (versioned migration path) | DONE | 13 tests in test_migrations.py; P2/P3/P4 gates PASS |
| P6-UPDATE-005 | Distribution (update check) | DONE | 21 tests in test_updates.py + 7 Rust tests; P2/P3/P4 gates PASS |

## Walk-test (selesai, bukan phase)

Tugas evaluasi flow/UI/UX yang TIDAK tercatat di `ai/HANDOFF.md` saat mulai
(tugas tambahan dari user). Bukan lulus gate, bukan membuka phase; tujuannya
menemukan bahan perbaikan. State mesin live: `walktest/HANDOFF.md` (dibaca
pertama oleh session lanjutan). Mekanisme akses + rencana: `walktest/PLAN.md`.
Temuan: `walktest/FINDINGS.md` (append-only, 19 blok). Laporan akhir:
`walktest/REPORT.md`.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| WALK-E2E-001 | Walk-test end-to-end (flow, UI, UX) | DONE | 19 temuan (8 MAJOR, 8 MINOR, 3 OBS); laporan `walktest/REPORT.md`; trust loop case B2B 484-baris tertutup (`loop_closed: true`) |

Konfigurasi target: core master diluncurkan via `.app` v0.3.2 dengan
`DAH_DEV_CORE=1` (venv checkout, fix version aktif), LLM dari `server/.env`;
deep DOM walk via Chromium di `:5273` (bundle yang sama dengan Tauri);
permukaan Tauri (menu) diverifikasi via Accessibility.

## P7 Product Modes

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P7-EVAL-001 | EVALUATE mode (audit existing work) | DONE | 22 tests in test_evaluator.py; P2/P3/P4 gates PASS |
| P7-SHELL-002 | UX (EVALUATE in the web shell) | DONE | +6 tests in CaseWorkspace.test.tsx; web build PASS |
| P7-SHELL-003 | UX (the agent in the web shell) | DONE | +7 tests; web build PASS |
| P7-SHELL-004 | UX (rename, duplicate, delete a case) | DONE | +5 tests; web build PASS |
| P7-SHELL-005 | UX (templates in the web shell) | DONE | +11 tests; web build PASS |
| P7-SHELL-006 | UX (cross-case memory actionable in the shell) | DONE | +4 tests; web build PASS |
| P7-SHELL-007 | UX (EDA in the web shell) | DONE | +6 tests; web build PASS |
| P7-SHELL-008 | UX (the evidence graph in the web shell) | DONE | +4 tests; web build PASS |
| P7-SHELL-009 | UX (case history in the web shell) | DONE | +3 tests; web build PASS |
| P7-LEARN-001 | LEARN mode (the guided walk, core) | DONE | +9 tests; P2/P3/P4 gates PASS |
| P7-SHELL-010 | UX (LEARN mode in the web shell) | DONE | +6 tests; web build PASS |
| P7-AGENT-001 | Multi-agent workflows (roles, core) | DONE | +13 tests; P2/P3/P4 gates PASS |
| P7-SHELL-011 | UX (the multi-agent surface) | DONE | +5 web tests; web build PASS |
| P7-E2E-001 | Verification (real-server e2e) | DONE | 25 steps over real HTTP; 3 runs green |
| P7-WALK-001 | Verification (manual shell walkthrough) | DONE | walked the shipped shell by hand; 1 bug fixed, 380 tests + e2e green |
| P7-CORS-001 | Reliability (the packaged app's webview) | DONE | CORS for the shell's origins; 4 tests, +4 (384), e2e green |
| P7-CSV-002 | Data Layer (a stray trailing comma) | DONE | 4 tests, +4 (388), e2e green |


## P8 Analytical Contract

Goal: close the PRD's Level 1 breadth gaps and make "done" measurable. DAH
implements its trust model narrowly (validation 3 of 9 dimensions, quality
detection 2 of 7 defect classes, question capture one text field) and measures
nothing; this phase widens the trust machinery first - the PRD's own rule is
that convenience is sacrificed before analytical trust - and then measures it.
See `docs/PRD & UX Conformance Evaluation.md` for the gap analysis this phase
answers.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P8-RELEASE | Distribution (the phase's releases) | DONE | tags v0.2.0 (ec819fc, 409 tests), v0.3.0 (ab56541, 686 tests) v0.3.1 (19cefc1, the squircle icon) and v0.3.2 (2ff1bca,
  the icon's artwork scaled to 52% of the canvas); artifacts built locally - CI's billing is suspended - and published as flagged pre-releases with checksums |
| P8-CONTEXT-001 | Data Layer (the case's context object) | DONE | 21 tests added (409 server, 82 web); schema v10; e2e green |
| P8-QUALITY-002 | Data Layer (quality beyond missingness) | DONE | 26 tests added (435 server, 84 web); schema v11; e2e green |
| P8-VALID-003 | Validation (3 checks to 9 dimensions) | DONE | 16 tests added (451 server, 85 web); e2e green; schema v11 |
| P8-CAUSAL-004 | Validation (the causal-language guard) | DONE | 16 tests added (468 server, 86 web); 50-case corpus measures 100% on AT-18's three thresholds; e2e green; schema v11 |
| P8-GOLDEN-005 | Verification (the analytical golden suite) | DONE | 21 reference calculations match at 100% (AT-40); 21/21 scripted runs complete the loop at 100% over 3 datasets (AT-01); 477 server, 86 web; e2e green |
| P8-SHELL-006 | UX (the orientation spine) | DONE | 13 tests added (477 server, 99 web); AT-33's seven questions answerable from the rendered workspace; e2e green |
| P8-REFINE-007 | AI (question refinement) | DONE | 41 tests added (518 server, 106 web); schema v12; AT-04's four thresholds measured over 50 cases at 100%/100%/0/0; e2e green |
| P8-DECISION-008 | UX (the decision view) | DONE | 30 tests added (548 server, 116 web); schema v13; 28/28 e2e; the verdict persists, the export carries it |
| P8-MEASURE-009 | Verification (the measurement layer) | DONE | 644 server, 138 web, e2e 28/28; every measured AT holds - AT-38 core 93.9% / analytical 92.9% / evidence 92.4%, AT-37 0/0, AT-28 p95 223ms, AT-29 p95 1.5s, AT-46 at the envelope |
| P8-TRACE-010 | Verification (the traceability matrix) | DONE | 48/48 rows resolve; P0 15/15 (100%), P1 33/33 (target >= 95%); 686 server, 138 web; e2e 28/28 |

### P8-TRACE-010 contract

```
TASK ID: P8-TRACE-010
MILESTONE: P8 Analytical Contract
CAPABILITY: Verification (the requirement-traceability matrix)
GOAL: AT-48, the PRD's section 59 control artifact. The PRD asks for a matrix
      that carries each requirement from the PRD through the UX surface, the
      implementation and the test to the threshold that says it holds - and
      until now that matrix was the PRD's own table, nine rows of checkmarks a
      human keeps up to date. This task makes it code: 48 rows, one per
      acceptance threshold, each cell naming a real thing in the repository,
      and one runner that resolves every cell against the repository as it
      actually stands. A matrix someone types drifts the moment a symbol is
      renamed; a matrix the gate resolves does not.
CONTEXT: last in the phase because it traces what the first nine delivered,
         and every AT now has a measured number for it to point at - the
         golden suite (AT-40/AT-01), the refinement runner (AT-04) and the
         measurement layer (AT-27..30/32/37/38/45/46) each wrote a committed
         report the matrix cites as evidence, and the suites hold the rest.
INPUTS: the PRD (its 48 AT headers and its section 53 release-blocking list),
        the UX architecture document (its numbered sections), the source of
        every module and component the matrix names, the test modules it
        cites, and the committed reports the measured rows point at.
RELEVANT FILES: verification/trace/matrix.py (new - the 48 rows, the cell
                types, the release-blocking categories), verification/trace/
                verify_trace.py (new - the resolver, the requirement-set check,
                the AT-48 fold, the report), verification/trace/REPORT.md
                (written by the runner), server/tests/test_trace.py (new, 42
                tests), ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The matrix is data, not prose. Each row carries the AT id and title, the
    PRD header line quoted exactly, whether the requirement is
    release-blocking and which of the PRD's section 53 categories it guards,
    the UX surface (a shipped component, a section of the UX document, or an
    explicit "no surface, and here is why"), the implementation (a file and a
    name defined in it), the tests (a file and the tests defined in it), the
    threshold in the PRD's own words, and where the measured number lives.
  - The runner resolves every cell: the PRD header must appear in the PRD, a
    component must ship and define the component named, a UX section must
    still carry its number and its title, a Python implementation or test must
    define the name at module level (an AST check), a cited runner must exist
    and the report it wrote must be committed, mention the AT and carry its
    own green sentence. A report carrying a failure marker is a red gate,
    because a measurement that stopped holding is not evidence.
  - The requirement set is checked against the PRD itself: the matrix's ids
    must be exactly the PRD's ids, so a requirement the PRD adds is a red gate
    until a row exists for it, and a row the PRD no longer states is a phantom
    the gate rejects.
  - Fifteen rows are P0, each naming one of the PRD's eight section 53
    categories: data loss, fabricated evidence, fabricated execution, an
    incorrect validated finding, a broken evidence chain, a critical security
    vulnerability, a critical analytical calculation error, and an
    unrecoverable case. AT-48's two thresholds compute from the resolved rows
    - 100% of P0 and >= 95% of P1 - rather than being asserted.
  - The report is the PRD's own table shape (requirement, UX, implementation,
    test, verification, threshold, verdict) plus the two AT-48 numbers, so a
    release gate can read it.
NON-GOALS: re-measuring anything - the matrix cites the runners and reports
           that already measure (golden, refine, measure) and points at the
           suites that assert, it does not run them; a browser-side
           measurement; a product surface for the matrix (section 59 calls it
           an engineering control artifact, not a user feature).
CONSTRAINTS: green only. No new dependency (DEC-001 - the resolver is ast and
             re). Deterministic and offline: the runner reads files that are
             committed and never touches the network. Read-only: it resolves,
             it does not execute the product.
ACCEPTANCE CRITERIA:
- [x] every one of AT-01..AT-48 has a row, and the row's ids are exactly the
      PRD's ids - no requirement untraced, no phantom row
- [x] every cell resolves: a missing file, a renamed symbol, a deleted test, a
      moved UX section, an uncommitted report or a red one is a named failure
- [x] the PRD header each row quotes is the PRD's own line, so a drift in the
      PRD is caught rather than silently mirrored
- [x] every P0 row guards a category the PRD's section 53 actually names
- [x] AT-48's thresholds are computed: 100% of P0 (15/15) and >= 95% of P1
      (33/33), and a single broken P0 row turns them red
- [x] the matrix can fail: a deliberately broken row is caught for each of the
      six ways a row can break, and the failure names the requirement
- [x] every cited measurement is real: the runner exists, the report is
      committed, it mentions the AT, and it carries its green sentence
- [x] the report renders the PRD's control-artifact table with a verdict per
      requirement, and is written to verification/trace/REPORT.md
TESTS: test_trace.py (42) - the 48 ids are the PRD's 48 in order, no
       requirement untraced or phantom, a requirement the PRD adds is an
       untraced red gate and a row it does not state is a phantom one, no AT
       traced twice, every row states a threshold and names an implementation,
       tests and evidence, the P0/P1 split is real and the section 53
       categories are the PRD's, an invented category fails, one broken P0 row
       fails the 100% threshold, and the six ways a row breaks - a missing
       file, a renamed symbol, a deleted test, a renumbered and a renamed UX
       section, a component that no longer ships and one that changed name, a
       no-surface cell without a reason, an uncommitted report, a missing
       runner, a report that went red, one that lost its marker, one that no
       longer mentions the requirement, and a missing suite - each fail and
       name what broke. Plus the gate itself green, the report written and
       readable, and AT-48's own row tracing to the matrix and these tests.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (686);
              `server/.venv/bin/python verification/trace/verify_trace.py`
              green (48/48 rows, AT-48 PASS);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (28/28); `server/.venv/bin/python
              verification/golden/verify_golden.py` green;
              `server/.venv/bin/python verification/refine/verify_refine.py`
              green; `server/.venv/bin/python verification/measure/
              verify_measure.py` green (9/9); `cd web && npm test && npm run
              build` green (138, build ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the P8 table closes at 10 of
              10. No schema change.
```

TASK: P8-TRACE-010 - the requirement-traceability matrix
ID: P8-TRACE-010
PRIORITY: high
STATUS: DONE
SUMMARY: the PRD's control artifact is code. Forty-eight rows carry every
         acceptance threshold from the PRD through the UX surface, the
         implementation and the test to the threshold that says it holds, and
         one runner resolves every cell against the repository as it stands.
         What makes it a control artifact rather than a document is that a
         renamed symbol, a deleted test, a renumbered UX section, an uncommitted
         report or a red one is a named failure - the matrix cannot quietly
         disagree with the thing it traces. The requirement set is checked
         against the PRD's own headers, so an acceptance threshold the PRD adds
         is a red gate until a row exists for it. Fifteen rows are
         release-blocking by the PRD's section 53, each naming the category it
         guards, and AT-48's thresholds compute from the resolved rows: 15/15
         (100%) and 33/33 against a >= 95% target. The matrix's own measurement
         is honest about which rows are measured and which asserted: the
         measured ones cite a runner and its committed report, and the asserted
         ones name the suite that pins them. One thing the resolution made
         visible and fixed: the AST check for a module-level name missed
         annotated constants (`INPUT_ERROR_TYPES: tuple[...] = ...`), so an
         implementation cell citing one read as undefined until the check
         learned `AnnAssign` - the kind of gap a matrix that only listed paths
         would never have found.

## Post-phase fixes

Fixes worked off the carried follow-up list after P8 closed - each is one
defect the shipped product still carried, taken in priority order. A phase is
not reopened for these; the fix's own contract and verification are below.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| FIX-VERSION-001 | Distribution (the packaged core's own version) | DONE | 8 tests added (694 server, 138 web); the packaged binary answers `current: 0.3.2` at `/updates/latest`; both packaged-core smokes now assert it |

### FIX-VERSION-001 contract

```
TASK ID: FIX-VERSION-001
MILESTONE: post-phase (the carried follow-up list)
CAPABILITY: Distribution (the packaged core's own version)
GOAL: the packaged core answered `current: unknown` at `/updates/latest`, so
      the Check for Updates menu item could never compare - it has reported
      "could not check" for a reason that is honest but incomplete, because the
      half of the answer the app owns (its own version) was missing. Neither
      the installed distribution's metadata nor `pyproject.toml` survives a
      one-file PyInstaller bundle, and PyInstaller ships no stdlib
      `importlib.metadata` hook, so `current_version` fell through every
      source to "unknown". Present since v0.2.0. This carries the version into
      the bundle as a build-time constant stamped from pyproject - the same
      file the release tag is checked against - and asserts it in both
      packaged-core smokes, so a bundle built without the stamp fails CI or the
      release rather than shipping a menu item that cannot work.
CONTEXT: P6-UPDATE-005 built the honest check - three statuses, a reason for
         every UNKNOWN, no silent "up to date" - and its tests drove every feed
         outcome through an injected transport. What it could not test was the
         frozen interpreter, so the packaged-core smoke was the only place the
         gap was visible, and it did not look. The fix touches the resolution
         order, the spec, both smokes and the tests; the endpoint, the feed
         parsing and the transport are unchanged.
INPUTS: server/pyproject.toml (the single source of truth the tag check reads),
        server/app/updates.py's resolution order, server/dah-core.spec's datas,
        the packaged-core smoke steps in .github/workflows/{ci,release}.yml.
RELEVANT FILES: server/app/updates.py (BUILD_VERSION_FILE,
                _frozen_build_version, current_version's new first source),
                server/dah-core.spec (_build_version, the stamped data file),
                server/tests/test_updates.py (+8), .github/workflows/ci.yml and
                .github/workflows/release.yml (the smoke assertion),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The spec reads the version from pyproject with tomllib (the interpreter's
    own, no hand-rolled line match) and refuses to build when the version is
    missing or not a release number - a bundle that would answer "unknown" is
    a build failure, not a shipped one. It writes the number to
    `dah-build-version.txt` into the bundle root, which is `sys._MEIPASS` at
    runtime.
  - `current_version` reads that stamp first, ahead of the installed metadata
    and the pyproject beside the source, because the stamp was read from the
    source of truth at build time while an editable install's metadata can go
    stale when a version is bumped without reinstalling. A missing or empty
    stamp is None, so resolution degrades to the next source instead of
    answering empty.
  - The stamp's filename is agreed on by both sides but the spec is executed by
    PyInstaller rather than importable, so the agreement is guarded as a test
    reading the spec as text - a spec that renamed the file without the app
    would ship a bundle that answers "unknown" and nothing else would catch it.
  - Both packaged-core smokes assert `/updates/latest` reports the version the
    tag named (release.yml) or pyproject states (ci.yml), so the regression
    that hid for four releases now fails the build.
NON-GOALS: shipping the release that carries it - that is a tag, and this is
           the fix; an updater (DEC-006 keeps the app unsigned, so the check
           remains the verifiable half); reordering the dev sources, where the
           installed metadata is still read first and is still right for a
           venv that installed the wheel.
CONSTRAINTS: green only. No new dependency (DEC-001 - tomllib is stdlib, the
             stamp is a text file). Deterministic and offline: the stamp is
             written at build time and read from disk; the smoke's
             `/updates/latest` call reports UNKNOWN with its reason on a
             private or unreachable repository and the assertion is on `current`
             alone, which the app always answers.
ACCEPTANCE CRITERIA:
- [x] the packaged core answers its own version at `/updates/latest`, not
      "unknown" - verified against the binary built by build_sidecar.sh
- [x] the stamp is read from pyproject, so the number the bundle reports is the
      number the release tag was checked against
- [x] a spec that cannot read a release version aborts the build rather than
      shipping a bundle that cannot answer
- [x] a missing or empty stamp degrades to the next source instead of
      answering empty or "unknown"
- [x] the stamp wins over installed metadata that has gone stale
- [x] the endpoint carries the stamped version to the response a shell renders
- [x] both packaged-core smokes assert it, so the defect cannot recur silently
- [x] the spec and the app agree on the stamp's filename, and a drift is a
      failing test
TESTS: test_updates.py (+8, 29 in the file) - the stamped bundle reports the
       version, the stamp beats the installed metadata, an empty stamp falls
       through, the stamp is read from `sys._MEIPASS`, no `_MEIPASS` means no
       stamp, a missing or empty stamp is None, the spec writes the file the
       app reads, and the endpoint carries the stamped version.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (694);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              golden, refine, measure green; trace 48/48;
              `cd web && npm test && npm run build` green (138);
              and the packaged binary itself:
              `curl -s localhost:8126/updates/latest` -> `current: 0.3.2`.
STATE UPDATE: TASKS/CURRENT_STATE gain the fix; the carried follow-up closes
              and leaves the list. No schema change, no version bump - the next
              tag ships it.
```

TASK: FIX-VERSION-001 - the packaged core reports its own version
ID: FIX-VERSION-001
PRIORITY: high
STATUS: DONE
SUMMARY: a packaged core answered `current: unknown` at `/updates/latest`, so
         the Check for Updates item could never compare versions - the honest
         half of its answer was missing because neither the installed
         distribution's metadata nor `pyproject.toml` survives a one-file
         PyInstaller bundle, and PyInstaller has no stdlib
         `importlib.metadata` hook. The spec now reads the version from
         pyproject with tomllib and stamps `dah-build-version.txt` into the
         bundle root, where `current_version` finds it through
         `sys._MEIPASS` - ahead of the installed metadata, which can go stale
         when a version is bumped without reinstalling. A version the spec
         cannot read aborts the build rather than shipping a bundle that
         cannot answer. Both packaged-core smokes now assert the number, which
         is what makes the recurrence fail the build instead of hiding for
         four releases. Verified against the binary itself: the sidecar built
         by build_sidecar.sh answers `current: 0.3.2`.



Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
