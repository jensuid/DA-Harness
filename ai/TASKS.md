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
| FIX-EVIDENCE-002 | Validation (the evidence check's number regex, W-015) | DONE | +5 tests (699 server, 138 web); golden 21/21, e2e all pass, refine AT-04, measure 9/9, trace 48/48 |
| FIX-PLAN-003 | UX (the plan stage's missing button, W-011) | PENDING | the rail's named action is reachable from the shell |
| FIX-CHART-004 | UX (a chart surface, W-016) | PENDING | a chart can be rendered and seen from a run |
| FIX-PYTHON-005 | UX (a python run surface, W-016) | PENDING | a python run can be generated and executed from the shell |
| FIX-TIMEOUT-006 | Reliability (the interpret/draft LLM timeout, W-014) | DONE | +24 tests (723 server, 140 web); every adapter posts one configured 120s timeout; a fallback source renders as a sentence; e2e all pass, golden 21/21, refine AT-04, measure 9/9, trace 48/48 |
| FIX-REFINE-007 | UX (the refinement's rationale, W-009) | DONE | +3 web tests (143 web total); "Why these changes" renders the rationale and grounds the API returns, shown rather than disclosed, and stays readable after an accept |
| FIX-PROFILE-008 | Reliability (the automatic re-profiling, W-008) | DONE | +4 web tests (147 web total); the mount GETs the profile and the analyst's POST is on request - no write on open, an offer when there is none, a re-profile when there is |
| FIX-UPDATES-009 | Distribution (the silent update check, W-005) | DONE | web 163 (+16), Rust 25 (+6); the three statuses reach the window as the shell's own notice, the log line still writes, the browser still opens an available build |
| FIX-VERSION-010 | Distribution (the dev checkout's stale version, W-001) | DONE | 4 tests added (727 server, 163 web); a dev checkout answers `current: 0.3.3` at `/updates/latest`, the source's number, with a stale metadata's drift logged rather than silently believed |

Prioritas adalah urutan tabel di atas (WALK-E2E-001's report menetapkannya:
W-015, W-011, W-016, W-014, lalu W-009, W-008, W-005, W-001). Satu commit per
fix. W-016 pecah jadi dua task (chart, python) karena keduanya tidak berbagi
kode selain panel tempatnya mendarat. Contract masing-masing di bawah.

Urutan eksekusi untuk session baru: FIX-EVIDENCE-002 dulu (paling terlokalisir,
hanya `server/app/evaluator.py`, tidak butuh infrastruktur walk-test yang
masih hidup). Lalu FIX-PLAN-003, FIX-CHART-004, FIX-PYTHON-005 (web), dan
baru FIX-TIMEOUT-006 (server + web). Empat terakhir (FIX-REFINE-007,
FIX-PROFILE-008 web; FIX-UPDATES-009 Rust; FIX-VERSION-010 server) bebas
urutan, dan ketiganya selain FIX-VERSION-010 sudah selesai; FIX-VERSION-010
selesai juga sekarang - urutan resolusinya menjadi stamp > pyproject >
metadata. Setiap fix: baca contractnya di file ini, implementasi, tes, full
gate (server pytest + e2e + golden + refine + measure + trace, web test +
build), lalu commit + push. Walk-test infra (core :8123 pid 84940, web :5273,
Tauri dah-shell 84919) masih hidup bila perlu memverifikasi ulang; cara
menjalankannya di `walktest/HANDOFF.md`.


### FIX-EVIDENCE-002 contract

```
TASK ID: FIX-EVIDENCE-002
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: Validation (the evidence check's number regex, W-015)
GOAL: a finding whose statement names a `YYYY-MM` period - or any value whose
      digits sit inside a longer token - fails the evidence dimension with
      "quotes values absent from its own result", and the dimension is HARD,
      so the verdict is insufficient_evidence. The finding was correct: every
      magnitude it quoted was a cell value in its own run. The check invented
      two numbers by splitting a token, then refused the finding for quoting
      them. This makes the check compare the magnitudes a statement actually
      quotes against the magnitudes the result actually holds.
CONTEXT: found by WALK-E2E-001's Fase C, reproduced directly in the
         interpreter: `_numbers_in("2026-07 has the highest revenue at
         1526309.57, the largest of 44 grouped value(s)")` returns
         `[-7.0, 44.0, 2026.0, 1526309.57]`, and `2026.0` and `-7.0` are not
         in `_allowed_numbers`. The same `_numbers_in` backs
         `drafter.py:246`, `evaluator.py:379` and `validation.py:220`
         (check_evidence, the HARD one), so the fix lands once and all four
         sites stop splitting tokens. A second defect surfaced in the same
         run: `_allowed_numbers` does not include the row count or the number
         of groups a result has, so "44 grouped value(s)" - which the
         deterministic drafter writes and which is true - was also reported
         invented. Both are the evidence dimension's honesty budget.
INPUTS: the statement and the run's columns and rows, exactly as check_evidence
        receives them; the deterministic drafter's own sentence shapes, which
        are what a correct regex must accept; the EVALUATE corpus, which
        judges the same field.
RELEVANT FILES: server/app/evaluator.py (`_numbers_in`, `_allowed_numbers`),
                server/app/validation.py (no change beyond the behaviour it
                reads), server/tests/test_validation.py and
                server/tests/test_evaluator.py (the tests), ai/HANDOFF.md,
                ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - A numeric token is only a magnitude when it is a token, not a fragment of
    one. A run of digits that sits inside a longer alphanumeric run - a date
    like 2026-07, an id like ORD-100331, a code like SKU-4001 - is not a
    number the statement quotes, so the regex must not emit it. The
    neighbouring characters are what decide: digits bounded by digits,
    commas, dots, whitespace or string edges are magnitudes; digits with a
    letter or a hyphen-then-digit against them are part of something larger.
    A negative number is only negative when its minus is a sign, not a date's
    separator, which is the exact confusion that produced -7.
  - `_allowed_numbers` gains the row count and the number of groups the
    result has (the distinct count per column already covers frequency, but
    not the totals the drafter names as "N grouped value(s)" or "N row(s)"),
    so a statement that names the shape of its own result is quoting a
    magnitude the result holds.
  - A claim that names a magnitude a result does not hold still fails - the
    honesty budget's purpose is unchanged, and a fabricated number in a
    correct-looking sentence still must not pass.
NON-GOALS: changing the verdict vocabulary or the HARD/soft classification;
           re-judging the golden suite's reference claims (they pass and keep
           passing); teaching the check to parse dates semantically (the fix
           is that it stops counting them, not that it understands them).
CONSTRAINTS: green only. No new dependency (DEC-001). Deterministic and
             offline: the check is pure over its inputs. Read-only: it
             judges, it never writes.
ACCEPTANCE CRITERIA:
- [x] a finding naming `YYYY-MM` periods with correct magnitudes passes its
      evidence dimension, where before it failed as insufficient_evidence
- [x] a date, an id and a sku are not extracted as magnitudes, verified per
      shape
- [x] a negative number inside a longer token is not emitted as one
- [x] a statement naming its result's own row count or group count passes
- [x] a genuinely fabricated magnitude still fails, and the failure names the
      invented number
- [x] the golden suite's reference claims still hold their evidence verdicts
- [x] the evidence check's sentence, when it fails, still names what the
      statement quoted that the result does not hold
TESTS: test_validation.py (+5) - the WALK-E2E-001 regression as a literal case
       (a `YYYY-MM` statement over twelve monthly rows passes evidence), a
       date / id / sku shape emitting no magnitude, a negative inside a token
       versus a real negative, the group-count allowance, and a fabricated
       magnitude still failing.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
               .venv/bin/python -m pytest -q` green (694 + 5 = 699);
               `verification/e2e/verify_e2e.py` green (all steps);
               `verify_golden.py` green (21/21 reference, 21/21 workflow);
               `verify_refine.py` green (AT-04);
               `verify_measure.py` green (9/9);
               `verify_trace.py` green (48/48);
               `cd web && npm test && npm run build` green (138).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the walk-test's
              W-015 closes. No schema change, no version bump.
```

### FIX-PLAN-003 contract

```
TASK ID: FIX-PLAN-003
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (the plan stage's missing button, W-011)
GOAL: the orientation rail names "Generate an analysis plan" and the endpoint
      that performs it, and nothing in the shell performs it. The plan panel
      reads a plan and, when there is none, tells the analyst to generate one
      - with no control that does. The loop's own to-do list points at a step
      the shipped UI cannot take, so the plan stage is only finishable from a
      terminal. The endpoint exists, is schema-validated and answers 201; the
      shell never calls it.
CONTEXT: WALK-E2E-001 Fase C reached this by following the rail and finding
         no control; `grep -rn "POST.*plan" web/src` is empty and
         `PlanPanel` holds only `getPlan`. The plan is what makes the next
         action legible, so a case that cannot plan cannot reach the stages
         after it either - the rail and the shell disagree about where the
         case stands.
INPUTS: the plan endpoint's request and response shape (main.py:3750), the
        rail's next_action and next_endpoint (workflow.py:31), the plan
        panel's empty state, and the panel's reload contract.
RELEVANT FILES: web/src/CaseWorkspace.tsx (PlanPanel, the new control),
                web/src/api.ts (a POST helper), web/src/CaseWorkspace.test.tsx
                (the tests), ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The plan panel's empty state gains a control that POSTs the plan
    endpoint for the dataset it already reads, and busy and error states like
    every other panel's: a generation in flight is labelled, a 400 (the
    endpoint refuses to plan an unprofiled dataset) is a sentence, and a
    success reloads the plan and the case, so the rail and the panel move
    together.
  - The generated plan renders in the same panel that reads it, so the
    analyst sees what was produced without a reload, and the control is what
    the empty state's own sentence asks for.
  - A plan that already exists is not regenerated: the control is the empty
    state's answer, and a case that has planned shows its plan.
NON-GOALS: auto-generating the plan (the plan is the analyst's to ask for);
           planning against a dataset other than the first attached one; a
           plan editor (the planner writes it, the shell reads it).
CONSTRAINTS: green only. No new dependency. The POST goes to the endpoint
             that already owns the write; the panel does not fabricate a
             plan client-side.
ACCEPTANCE CRITERIA:
- [ ] a case with a profile and no plan offers a control that generates the
      plan, and the plan renders without a manual reload
- [ ] the rail's next_action and the control agree while generation is in
      flight and after it lands
- [ ] a generation that fails shows the endpoint's own reason as a sentence
- [ ] a case that already has a plan does not offer to regenerate it
- [ ] the workspace's reload contract is used, so progress counts and the
      rail move with the plan
TESTS: CaseWorkspace.test.tsx (+~4) - the control generates and the plan
       renders, the failure surfaces, an existing plan suppresses the
       control, and the reload fires.
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green (142).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-011 closes.
```

### FIX-CHART-004 contract

```
TASK ID: FIX-CHART-004
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (a chart surface, W-016)
GOAL: a chart is an evidence artifact the core renders, stores and exports,
      and the shell cannot produce one. The runs panel runs a query and the
      evidence graph counts the charts, but between them there is no control
      that asks for a chart, and no surface that shows the one the core drew.
      Every chart is only reachable through its file path. This closes that
      gap for the run that produced the numbers.
CONTEXT: WALK-E2E-001 Fase C created a chart by curl to verify the renderer,
         and the evidence graph, the history and the export all carried it -
         only the shell could not. `grep -c chart web/src/api.ts` is zero.
         The endpoint validates its columns against the run's own result, so
         the control's pickers can only offer what the run produced.
INPUTS: the chart endpoint's payload and response (main.py:2884), the chart
        kinds and formats the renderer supports, the run row's columns, and
        the stored path the response returns.
RELEVANT FILES: web/src/api.ts (a chart helper), web/src/CaseWorkspace.tsx
                (RunRow gains the control and the surface), the renderer and
                the endpoint (unchanged), web/src/CaseWorkspace.test.tsx,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - A run row offers "Render a chart" once it has a result, with pickers for
    the x and y columns the run actually produced and the kind the renderer
    supports, and the control posts to the endpoint that owns the write.
  - The response's chart is shown in the shell - as an inline SVG for the
    default format, and as a link for the others - so a chart is evidence
    the analyst can see, not a path on disk.
  - A chart that fails to render shows the endpoint's own reason as a
    sentence, because the renderer's refusal is the analyst's input.
NON-GOALS: a chart gallery or a chart history view (the evidence graph
           counts them and the export carries them); editing a chart; new
           chart kinds (the renderer's vocabulary is what it is).
CONSTRAINTS: green only. No new dependency. The POST goes to the endpoint
             that owns the write and renders from the stored result.
ACCEPTANCE CRITERIA:
- [ ] a run with a result can render a chart, and the chart appears in the
      shell without leaving the case
- [ ] the pickers offer only the columns the run produced
- [ ] an unsupported choice is refused with the endpoint's own sentence
- [ ] the SVG the response carries is what the shell displays
- [ ] the evidence graph's chart count moves when a chart is rendered
TESTS: CaseWorkspace.test.tsx (+~4) - the control renders and the SVG shows,
       the pickers are the run's columns, a failure surfaces.
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green (142).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the chart half of
              W-016 closes.
```

### FIX-PYTHON-005 contract

```
TASK ID: FIX-PYTHON-005
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (a python run surface, W-016)
GOAL: the sandbox executes user Python against an attached dataset and
      persists the result exactly like a SQL run, and the shell has no way to
      ask for one. The codegen panel generates SQL only, and the runs
      endpoint it posts to is the SQL one. A python run is only reachable by
      curl, so the hardening the sandbox exists to prove is untested by
      anyone using the app.
CONTEXT: WALK-E2E-001 Fase C ran python through the endpoint: the seatbelt
         refused a bad script with a 400 and an honest reason, and a correct
         one produced a run that the evidence graph, the history and the
         export all carried. `grep -rn "runs/python" web/src` is empty. The
         generator already supports kind 'python' and the endpoint and its
         model already exist; only the shell's request is missing.
INPUTS: the python run endpoint (main.py:1778), its `PythonRunCreate` model,
        the generator's kind parameter and its python output, the sandbox's
        contract (a `dataset` handle, a `result` the run tabulates), and the
        codegen panel's existing propose-and-run shape.
RELEVANT FILES: web/src/api.ts (a python run helper), web/src/CaseWorkspace.tsx
                (the codegen panel gains a kind, the run posts to the python
                endpoint), web/src/CaseWorkspace.test.tsx, the endpoint and
                the sandbox (unchanged), ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The codegen panel offers SQL and Python, and the proposal it generates
    matches the kind chosen, so a python question is answered with python.
  - Running a python proposal posts to the python endpoint, and the run it
    persists is a run like any other - the same runs panel, the same
    evidence chain, the same validation.
  - A sandbox refusal is the analyst's input: its detail is the sentence the
    panel shows, not a broken panel.
NON-GOALS: a python editor with a console; a package installer; changing the
           sandbox (its allowlist, its seatbelt profile and its row cap are
           the contract the surface now exposes).
CONSTRAINTS: green only. No new dependency. The POST goes to the endpoint
             that owns the write; the panel does not execute code itself.
ACCEPTANCE CRITERIA:
- [ ] the panel generates python for a python question and the code it
      proposes is what the sandbox accepts
- [ ] running a python proposal creates a run the runs panel and the
      evidence graph carry
- [ ] a script the sandbox refuses answers a 400 whose detail the panel
      shows as a sentence
- [ ] the kind persists across proposals in the same panel
- [ ] the SQL path is unchanged in behaviour and in its tests
TESTS: CaseWorkspace.test.tsx (+~4) - python generation and its run, the
       refusal surfaced, SQL unaffected.
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green (142).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the python half of
              W-016 closes and W-016 is done.
```

### FIX-TIMEOUT-006 contract

```
TASK ID: FIX-TIMEOUT-006
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: Reliability (the interpret/draft LLM timeout, W-014)
GOAL: two of the three assistant slices never use the LLM in practice: the
      interpret and draft endpoints wait exactly thirty seconds, time out,
      and fall back to deterministic, and the shell shows "Working…" for the
      whole thirty seconds with no indication that an engine failed and
      another answered. The planner and refine endpoints, at sixty seconds,
      finish. The analyst reads a deterministic reading believing it was the
      LLM's, because the only tell is a small source label.
CONTEXT: WALK-E2E-001 Fase C reproduced this on every interpret and draft
         call: the log line is `llm read failed; falling back to
         deterministic: The read operation timed out` at 30133ms and
         30184ms, while the generator at 30s and refine at 60s succeeded.
         The timeouts are interpreter.py:239, drafter.py:312 and
         assistant.py:576 at 30.0; planner.py:366 and refine.py:595 at 60.0.
INPUTS: the five LLM call sites and their timeouts, the fallback contract
        (any failure degrades, the source field records which engine
        answered), and the panels that render the source label.
RELEVANT FILES: server/app/interpreter.py, server/app/drafter.py,
                server/app/assistant.py (the timeouts), the web panels that
                render `by <source>` (the announcement), the tests for both,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The timeouts are one configured value the environment can raise, default
    high enough that a slow endpoint answers before the harness gives up on
    it, so the engine a case configured is the engine that answers.
  - A fallback is announced rather than labelled: the panel says the LLM was
    unavailable and a deterministic reading was used in its place, in the
    same place the source label sits, so the analyst knows which engine
    spoke and that it was not the one asked.
  - The contract that any failure degrades is untouched: a plan, a reading
    and a draft are still always returned, and the source still records
    which engine produced them.
NON-GOALS: changing the fallback itself (the contract is the point);
           retrying (a second thirty seconds is not a better answer);
           streaming (the endpoints answer once, whole).
CONSTRAINTS: green only. No new dependency. The default is a number, not a
             behaviour; the tests inject the failure rather than waiting for
             it, so no test is slower for the change.
ACCEPTANCE CRITERIA:
- [ ] the three 30s call sites read the same configured value, and the
      planner's 60s is the same value's neighbour
- [ ] a slow endpoint that would have timed out answers before the timeout
- [ ] the source the response carries still records which engine answered
- [ ] a panel showing a deterministic answer after an LLM failure says so in
      a sentence the analyst reads
- [ ] no test waits the timeout to reach its failure
TESTS: test_interpreter.py / test_drafter.py (+~4, the timeout is read from
       the value and a slow engine still answers), the web panel's
       announcement (+~2).
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-014 closes.
```

### FIX-REFINE-007 contract

```
TASK ID: FIX-REFINE-007
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (the refinement's rationale, W-009)
GOAL: accepting a refinement is a black box. The API returns a rationale and
      the grounds it rests on, and the panel renders neither, so the analyst
      approves a change to their own question without being told why the
      change was proposed or what in the profile supports it. "Why these
      changes" is the panel's own heading and it sits empty.
CONTEXT: WALK-E2E-001 Fase B accepted a deterministic refinement and the
         heading stayed blank; the response carries the fields the panel
         does not read.
INPUTS: the refinement response's rationale and grounds fields, the panel's
        heading and its accepted state.
RELEVANT FILES: web/src/RefinePanel.tsx, web/src/CaseWorkspace.test.tsx,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The proposal renders its rationale as the answer to the heading that
    asks, and the grounds it names - the profile's own columns and measures,
    which is what makes the suggestion honest - are listed where the analyst
    can see what the suggestion rests on.
  - The accepted state keeps the proposal readable, so the change the
    analyst accepted stays explained after it is applied.
NON-GOALS: changing the refinement engines or their output; editing a
           rationale; re-proposing automatically.
CONSTRAINTS: green only. No new dependency. The fields are already in the
             response; this is rendering what the API returns.
ACCEPTANCE CRITERIA:
- [x] a proposal shows its rationale under its own heading
- [x] the grounds the proposal names are listed, and they are the response's
- [x] an accepted refinement keeps its rationale and grounds readable
- [x] a proposal without grounds renders nothing rather than an empty list
TESTS: CaseWorkspace.test.tsx / RefinePanel (+~3).
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-009 closes.
```

TASK: FIX-REFINE-007 - the refinement's rationale is rendered
ID: FIX-REFINE-007
PRIORITY: high
STATUS: DONE
SUMMARY: accepting a refinement was a black box. The API returned a
         `rationale` and the `grounds` it rests on - the profile's own
         columns and measured ranges, which is what makes a suggestion
         honest - and `RefinePanel` had both inside a `<details>` that
         renders collapsed, so "Why these changes" read as inert text and
         the analyst approved a change to their own question without being
         told why it was proposed or what supports it. The disclosure is
         gone: the rationale sits under a real `<h4>` heading of its own,
         the grounds list below it, both always visible, and both still
         rendered after an accept so a change the analyst made stays
         explained. `.rationale` carries the proposals' left rule and
         ground so the block reads as support rather than another paragraph,
         and `.panel h4` exists because no panel had used a fourth-level
         heading. Three tests cover it: the proposal shows its rationale and
         both grounds under the heading, an accepted proposal keeps them
         readable, and a proposal without grounds renders no empty list.

### FIX-PROFILE-008 contract

```
TASK ID: FIX-PROFILE-008
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: Reliability (the automatic re-profiling, W-008)
GOAL: opening a case re-profiles its dataset, twice, every time. The panel
      POSTs the profile endpoint on every mount, so a profile that already
      exists is recomputed and rewritten on each visit, and the stage that
      reads it is ambiguous - the rail can show "profile" current while the
      panel is the thing that completes it. Profiling is the analyst's step,
      and the shell takes it for them without being asked.
CONTEXT: WALK-E2E-001 Fase B watched the core log receive two POST /profile
         calls each time the case view opened; `profileDataset` in api.ts:572
         is a POST and the useEffect at CaseWorkspace.tsx:191 calls it on
         mount. The profile is what the planner and the missing-data check
         read, so a silent rewrite of it is not free.
INPUTS: the profile endpoint's GET and POST shapes, the panel's mount effect,
        and the profile's own read contract.
RELEVANT FILES: web/src/CaseWorkspace.tsx (the mount effect), web/src/api.ts
                (a read helper if the endpoint offers none), the tests, the
                core if a GET is needed, ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The panel reads the profile it has before asking for one: a case with a
    profile renders it, and a POST happens when the analyst asks for a
    re-profile or when there is nothing to read - not on every mount.
  - The double invocation is one invocation; if the effect must remain, its
    dependency array and the strict-mode double render no longer both reach
    the endpoint.
  - The rail and the panel agree about the profile stage, because the panel
    no longer completes it by opening.
NON-GOALS: caching a profile client-side (a read per mount is correct, a
           write is not); changing the profiler; dropping the re-profile
           control (a stale profile must be refreshable, on request).
CONSTRAINTS: green only. No new dependency. A GET is preferred to a POST
             when the endpoint can answer one; if it cannot, the change adds
             one and the tests cover it.
ACCEPTANCE CRITERIA:
- [x] opening a case with a profile does not POST the profile endpoint
- [x] opening a case without a profile does not fabricate one
- [x] an explicit re-profile works and the panel reflects it
- [x] the profile the panels render is the stored one
- [x] the rail's profile stage and the panel's state agree
TESTS: CaseWorkspace.test.tsx (+~4) - no POST on mount with a profile, one
       on request, the panel renders the stored profile.
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-008 closes.
```

TASK: FIX-PROFILE-008 - opening a case reads its profile, and does not write one
ID: FIX-PROFILE-008
PRIORITY: high
STATUS: DONE
SUMMARY: opening a case re-profiled its datasets, twice. The mount effect
         called `profileDataset` - a POST - per attached dataset on every
         visit, and strict mode's double render made it two writes, so a
         profile that already existed was recomputed and rewritten, and the
         step the rail names as the analyst's was silently completed by the
         shell. The GET endpoint already existed (`main.py:1654`, a 404 when
         there is nothing stored), so the mount now reads through a new
         `getProfile` helper and the POST is the analyst's explicit ask.
         A dataset with a profile shows it and offers Re-profile; one
         without shows an offer to profile it rather than a "profiling…"
         placeholder that was the shell completing the step - so the panel
         and the rail now agree about where the profile stage stands. Four
         tests cover it: the mount GETs and never POSTs and a request POSTs,
         an unprofiled dataset is offered rather than fabricated, a failed
         profiling surfaces the endpoint's own reason, and the panel renders
         the stored profile.

### FIX-UPDATES-009 contract

```
TASK ID: FIX-UPDATES-009
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: Distribution (the silent update check, W-005)
GOAL: the Check for Updates menu item performs a check and reports it to a
      log, and nothing reports it to the user. The item is silent whether it
      finds an update, finds none, or cannot reach the feed - three outcomes
      the core distinguishes and the shell never shows. On a private
      repository the feed is unreachable and the item is permanently,
      silently dead.
CONTEXT: WALK-E2E-001 Fase A triggered the item, watched the core receive
         the request, and saw nothing in the window; the handler prints its
         result to stderr and stops there (main.rs:48-60). The core already
         answers three statuses with a reason for every UNKNOWN, so the
         information exists and is not delivered.
INPUTS: the core's `/updates/latest` statuses and their reasons, the menu
        item's handler, and the shell's own surface for reporting to the
        user.
RELEVANT FILES: desktop/src-tauri/src/main.rs (the handler and its delivery),
                the update status vocabulary in server/app/updates.py, the
                desktop tests, ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The check's outcome reaches the user as the window's own message - a
    dialog or an equivalent surface - for each of the three statuses, so the
    item always answers something and the analyst never waits on a silent
    one.
  - An unreachable feed says it is unreachable rather than appearing to have
    checked nothing, which is the honest reason the vocabulary already
    carries.
  - The handler's result still reaches the log; the delivery is added, not
    substituted.
NON-GOALS: an updater (the check remains the verifiable half, per DEC-006);
           a settings pane; polling.
CONSTRAINTS: green only. No new dependency. The delivery uses the window the
             app already has; the statuses come from the core.
ACCEPTANCE CRITERIA:
- [x] each of the three statuses produces a visible answer in the window
- [x] an unreachable feed answers with its reason, not silence
- [x] the core's own status vocabulary is what the message reports
- [x] the log line the handler already writes still writes
TESTS: NoticeLayer.test.tsx (+8) and shell.test.ts (+8) on the web side;
       notice_tests in updates.rs (+6) on the Rust side - the event-name
       agreement, the body riding along, the no-body and non-JSON cases, and
       each of the three statuses.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (723, unchanged);
              `cd desktop/src-tauri && cargo test` green (25, +6);
              `cd web && npm test && npm run build` green (163, +16);
              `verify_e2e.py` green; `verify_golden.py` green (21/21);
              `verify_refine.py` green (AT-04); `verify_trace.py` green
              (48/48).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-005 closes. No
              schema change, no version bump.
```

TASK: FIX-UPDATES-009 - the silent update check reaches the window
ID: FIX-UPDATES-009
PRIORITY: high
STATUS: DONE
SUMMARY: the Check for Updates menu item performed a check the core
         distinguishes three ways and told only stderr about it, so on this
         private repository - where the feed always answers 404 - the item was
         permanently, silently dead. The delivery is the bundle's own surface,
         because the shell is the only host with a menu bar and a native dialog
         was not available: `tauri-plugin-dialog` is a network-fetched plugin
         on Tauri 2 and the app is offline once installed, so depending on it
         would break DEC-001. The shell evaluates a script in the webview it
         already holds, posting a `dah-notice` event whose detail is the core's
         own JSON body - never a sentence the shell reworded, so an unreachable
         feed stays "could not tell" instead of becoming the silent "up to
         date" P6-UPDATE-005 built the check to avoid. The bundle's
         `describeUpdate` mirrors the shell's `update_summary`, so the window
         and the log line always say the same thing about the same answer.
         One thing the tests caught and fixed: a body that is not JSON cannot
         be embedded in the script, because the eval would throw a
         `SyntaxError` and silence the item a second time - so `notice_script`
         validates the body and falls back to a body the shell rebuilds from
         the parsed answer, which is also how a transport that kept no body at
         all still reaches the window.

### FIX-VERSION-010 contract

```
TASK ID: FIX-VERSION-010
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: Distribution (the dev checkout's stale version, W-001)
GOAL: a dev checkout answers `current: 0.1.0` at `/updates/latest`, which is
      a specific wrong number the resolution order produced by trusting
      installed metadata that has gone stale over the pyproject beside the
      source. FIX-VERSION-001 fixed the bundle's unknown by stamping the
      build; the dev checkout never sees the stamp, so its half of the answer
      is still the metadata's, and 0.1.0 is worse than unknown because a
      wrong number is believed where an absent one is questioned.
CONTEXT: WALK-E2E-001 Fase A read `current: 0.1.0` from a checkout whose
         pyproject states 0.3.2; the venv holds `dah_server-0.1.0.dist-info`
         from an editable install of an older name and version.
         `current_version` reads the stamp, then the installed metadata, then
         the pyproject beside the source.
INPUTS: the resolution order in current_version, the three sources it reads,
        and the dev checkout's own venv state.
RELEVANT FILES: server/app/updates.py (the order), server/tests/test_updates.py,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - In a checkout, the pyproject beside the source is read before the
    installed metadata, because the source is the truth the checkout is
    running and the metadata is what an install left behind; the stamp stays
    first, because it was read from the source of truth at build time.
  - The installed metadata is not discarded, only demoted: an installed
    wheel without a pyproject beside it still answers, which is the case the
    metadata was right for.
  - A disagreement is not papered over: when the metadata and the source
    both answer and disagree, the source wins and the reason records it, so
    a stale install is visible rather than silently believed.
NON-GOALS: reinstalling or rewriting the venv; changing the bundle's order
           (the stamp stays first there); detecting editable installs by
           name.
CONSTRAINTS: green only. No new dependency. Deterministic and offline: the
             sources are files. The smoke's assertion on `current` is what a
             dev checkout now satisfies.
ACCEPTANCE CRITERIA:
- [x] a dev checkout reports its pyproject's version, not the installed
      metadata's
- [x] the stamped bundle still wins, so the packaged path is unchanged
- [x] an installed wheel with no pyproject beside the source still answers
- [x] a stale metadata disagrees with the source and the source wins, with
      the reason recorded
- [x] the dev-checkout smoke that asserted on `current` passes
TESTS: test_updates.py (+4, 33 in the file) - the source beats the stale
       metadata, the stamp still beats both, the wheel-alone case, and the
       disagreement's log.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (727);
              `verify_e2e.py` green (28/28); `verify_golden.py` green
              (21/21 both); `verify_refine.py` green (AT-04);
              `verify_measure.py` green (9/9); `verify_trace.py` green
              (48/48); `cd web && npm test && npm run build` green (163);
              and this checkout: `current: 0.3.3`, not the metadata's 0.1.0.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-001 closes and the
              walk-test's eight MAJOR findings are all resolved.
```

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
