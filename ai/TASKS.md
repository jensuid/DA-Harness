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
| FIX-PLAN-003 | UX (the plan stage's missing button, W-011) | DONE | 4 tests added (727 server, 167 web); the empty state's own sentence finally has the control that performs it - a POST to the plan endpoint, the plan rendered in place, the rail and the counts reloaded with it, and an existing plan offers nothing |
| FIX-CHART-004 | UX (a chart surface, W-016) | DONE | 6 tests added (727 server, 173 web); a run with a result can render a chart and see it inline as the core's own SVG, the pickers offer only the run's columns, a refusal shows the renderer's sentence, and the evidence count moves |
| FIX-PYTHON-005 | UX (a python run surface, W-016) | DONE | 4 tests added (727 server, 177 web); a python run can be generated and executed from the shell - the panel offers SQL and Python, the proposal matches the kind, and the run posts to the sandbox's own endpoint |
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


## P9 UI/UX Redesign

Goal: the shell is functionally complete - every walk-test finding closed and
48/48 requirements traced - but the surfaces are the hand-written CSS and
hand-rolled markup of an MVP that grew. P9 makes them a designed system. The
stack, decided with the user: npm stays (CI hardcodes `npm ci`, Tauri's
beforeDevCommand uses `npm --prefix`), the theme is light first, and recharts
draws the on-screen chart because the server's chart SVG bakes a white
background into the image and is static - while its layout engine and PNG
export stay for the export path. Four phases, green at each: F1 the foundation,
F2 the surfaces, F3 motion, F4 the chart surface and a re-walk.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P9-F1-001 | Foundation (tooling, tokens, structure) | DONE | web 181 (177 + 4 panels tests), build ok, tsc clean, server 727, e2e 28/28, golden 21/21, refine AT-04, measure 9/9, trace 48/48 |
| P9-F2-001 | Surfaces (the walk-test's last three findings) | DONE | web 184 (+3), build ok, tsc clean, trace 48/48; W-013/W-017/W-018 closed |
| P9-F2-002 | Surfaces (the restyle onto the tokens) | DONE | web 185 (+1), tsc clean, build ok (CSS 14.44 kB), trace 48/48; 109 lines of hand-written CSS retired |
| P9-F3-001 | Motion (the motion layer and its gate) | DONE | web 197 (+12), tsc clean, build ok (CSS 15.11 kB, JS 347 kB), trace 48/48; framer-motion used, `prefers-reduced-motion` honoured by the JS-driven motion too |
| P9-F4-001 | Charts (the on-screen chart and a re-walk) | DONE | web 216 (+19), server 728 (+1), tsc clean, build ok (CSS 16.46 kB, JS 744 kB), trace 48/48, e2e 28/28; recharts used, the re-walk found the missing `format` field and the tooltip is verified in a browser |

### P9-F3-001 contract

```
TASK ID: P9-F3-001
MILESTONE: P9 UI/UX Redesign (phase F3, motion)
CAPABILITY: Motion (the motion layer and its gate)
GOAL: framer-motion@13 was installed in F1 and imported nowhere - the same
      debt shape F2 just paid, one phase earlier. This is the motion: a
      panel's content appearing as the case loads, a run row opening, a
      verdict landing. The constraint is `prefers-reduced-motion`, which the
      CSS already honours for the shell notice (`index.css`'s explicit
      `animation: none` rule); F3 makes the JS-driven motion honour it too
      rather than only the CSS-driven kind. A motion budget is the
      discipline: an animation that costs a frame the measurement layer
      (AT-27/AT-30) counts is a regression, not a polish.
CONTEXT: F1 shipped the toolchain and the tokens; F2 moved every surface onto
         them. The surfaces are the wrappers the panels already render - a
         run row is `surfaces.row`, a verdict is `surfaces.proposal` - so the
         motion attaches to those wrappers rather than to new elements, and a
         motion surface is the `div` the panel was already drawing. The
         measurement layer pins AT-27's interaction response at 200ms p95 and
         AT-30's visible state at 100% of long-running operations, and both
         are asserted in `measure.test.tsx` against the disclosure this layer
         animates - so the budget is measured, not asserted in prose.
INPUTS: framer-motion@13 (installed, unused), `web/src/index.css`'s existing
        reduced-motion rule for the shell notice, the panels' surface
        wrappers, and the measurement suite that pins the budget.
RELEVANT FILES: web/src/lib/motion.tsx (new - the variants, the transitions,
                the `ReducedMotion` gate, the `MotionSurface` component),
                web/src/motion.test.tsx (new, 12 tests),
                web/src/setup-tests.ts (the matchMedia shim),
                web/src/App.tsx (the gate mounted at the root),
                web/src/CaseWorkspace.tsx, web/src/CaseList.tsx,
                web/src/panels/RunsPanel.tsx, web/src/panels/FindingsPanel.tsx,
                web/src/panels/Chat.tsx, web/src/index.css (the CSS gate),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - The vocabulary: `transitions` names three - `surface` (0.18s, what a
    click opens), `enter` (0.28s, what a case loads) and `arrive` (a spring,
    what a verdict does) - and `variants` names the same three, each a
    `hidden` state and a `shown` one with the transition riding inside the
    target so the gate's collapse to `shown` is the end of the motion. The
    movement is 4-6px and never an element's own height, because layout
    shift is the cost AT-27 counts; the arrival scales by 2% rather than
    sliding, because it is the loop's exit and the weight reads.
  - The gate: `ReducedMotion` mounts `MotionConfig reducedMotion="user"`
    once at the root in `App.tsx`, so every screen resolves the analyst's
    OS preference through it. The collapse is this layer's own, not the
    library's: framer-motion makes positional keys instant under reduced
    motion but still fades opacity, and a reduced-motion setting that still
    moves the surface is a setting the surface is not honouring, so
    `MotionSurface` reads `useReducedMotionConfig()` and sets
    `initial={false}` - the surface renders its shown state with no
    animation at all, the same result the CSS gives the shell notice.
  - The CSS gate, `index.css`'s second `prefers-reduced-motion` rule, holds
    a `[data-motion-surface]` at opacity 1 and transform none. It is the belt
    to the JS braces: a surface that starts hidden and is never animated to
    shown - because the engine was absent, or a frame was dropped on a slow
    machine - is invisible content, and this rule is what keeps the content
    present when the motion does not run.
  - The matchMedia shim in `setup-tests.ts`: jsdom has no `matchMedia`, and
    the library's preference resolution reads through it, so the shim is what
    makes the gate behave in the suite the way it behaves in a browser. It is
    stubbed in `beforeEach` and unstubbed in `afterEach`, so a test that
    changes the preference does not leak into the accessibility audit or the
    measurement layer.
  - The surfaces that moved: the workspace's three zones (the panels appear
    as the case loads), a run row and its rows table, the chart surface, a
    verdict, a chat answer, and a case row on the list. Every one is the
    wrapper the panel already rendered, now a `MotionSurface` carrying the
    same `className`; no markup was added and no surface was restyled.
NON-GOALS: restyling anything (F2's parity stands; a new look is a later pass
           that decides on purpose what changes), the on-screen chart (F4 -
           recharts is installed and still unused, and the chart this phase
           animates is the core's own SVG, unchanged), a dark theme, touching
           the server, and changing any test's assertion rather than the
           element it reads.
CONSTRAINTS: green only. No new dependency (framer-motion is F1's, now used).
             Deterministic and offline. The accessibility audit's
             STATUS_CLASSES contract is unchanged, and the audit is
             structural - it does not read opacity, so a surface that starts
             hidden passes it; the CSS gate is what protects the analyst the
             audit cannot see. Web-only: no line outside `web/` moves.
ACCEPTANCE CRITERIA:
- [x] framer-motion is imported and the motion is the surfaces' own: a panel
      arriving, a row opening, a verdict landing, a case row on the list
- [x] every variant is inside the budget: 0.18s for a click's surface, 0.28s
      for a case load, and a spring whose settle (4 * mass / damping) is
      under 0.3s
- [x] a surface slides a little and never its own height - 6px or less, so
      no motion this layer adds moves another panel
- [x] the gate closes: `reducedMotion="always"` renders the shown state with
      no animation, and the surface's opacity is not the hidden one
- [x] the CSS gate holds a motion surface visible when the motion does not
      run, and the shell notice's own rule is still there beside it
- [x] the gate is mounted once at the root, so a screen it does not wrap is
      a screen the analyst's setting does not reach
- [x] no other behaviour moved: the existing 185 assertions pass unchanged,
      the emitted stylesheet still resolves the focus rule the accessibility
      audit reads, and the disclosure the measurement layer times is inside
      its budget with the motion in the tree
TESTS: `motion.test.tsx` (12) - the three variants each carry the state the
       gate collapses and come to rest visible, the movement is bounded, the
       transitions are inside the 200ms budget numerically and the
       disclosure's open is measured with the motion mounted, the gate
       renders visible content when open and its end state when closed, the
       helper reads the preference the same way, the CSS rules resolve from
       the shipped stylesheet, and the root wraps every screen.
VERIFICATION: `cd web && npm test && npm run build` green (197 = 185 + 12,
               tsc clean, build ok - the emitted CSS is 15.11 kB and still
               resolves the focus rule, the JS 347 kB);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48 rows, AT-48 PASS - the symbols the matrix cites
               still resolve). Web-only, so the server suite (727), the e2e
               (28/28), golden (21/21), refine (AT-04) and measure (9/9) are
               not re-run: no line outside `web/` moved (verified by
               `git status`), and their last runs are green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the task; the P9 table closes
              at F3-001. No schema change, no version bump.
```

TASK: P9-F3-001 - the motion layer and its gate
ID: P9-F3-001
PRIORITY: high
STATUS: DONE
SUMMARY: the motion the surfaces were missing, and the one gate that decides
         whether any of it runs. `web/src/lib/motion.tsx` names three
         transitions - a click's surface at 0.18s, a case load at 0.28s, a
         verdict's spring - and three variants to match, each a hidden state
         and a shown one with the transition riding inside the target. The
         movement is 4-6px and never an element's own height, because layout
         shift is the frame AT-27 counts; the verdict scales by 2% because
         the loop's exit carries weight. `ReducedMotion` mounts
         `MotionConfig reducedMotion="user"` once at the root, and the
         collapse is this layer's own rather than the library's:
         framer-motion makes positional keys instant under reduced motion but
         still fades opacity, so `MotionSurface` reads
         `useReducedMotionConfig()` and sets `initial={false}`, rendering the
         shown state with no animation at all - the same result the CSS gives
         the shell notice. A second `prefers-reduced-motion` rule holds a
         `[data-motion-surface]` visible, because a surface that starts
         hidden and is never animated to shown is invisible content, and that
         is the failure mode the JS gate cannot see itself out of. The lesson
         the gate earned: `useReducedMotion()` caches the OS preference in
         `useState` at first read, so a probe that reads it outside the
         `MotionConfig` provider always answers the default - the preference
         is a context, not a global, and the two are not interchangeable.


### P9-F4-001 contract

```
TASK ID: P9-F4-001
MILESTONE: P9 UI/UX Redesign (phase F4, charts)
CAPABILITY: Charts (the on-screen chart, and a re-walk)
GOAL: recharts@3 is the last of F1's three dependencies still at zero
      imports. The chart the shell shows is the core's own static SVG -
      white background baked in, no tooltip, no hover - because the shell
      draws what the core already drew rather than drawing a second time.
      This phase changes the renderer of what the analyst *looks at*, not
      of what the case *holds*: recharts draws the on-screen chart from the
      run's stored result, and the core's SVG and PNG stay the persisted
      artifact, the exported package and the evidence. What the new
      renderer adds is what a static image cannot: a tooltip that reads a
      point's own values, and a hover state that names what is under the
      cursor. What it must not add is a second source of truth for the
      numbers.
CONTEXT: F1 shipped the toolchain and the tokens, F2 the surfaces, F3 the
         motion. The chart surface this phase replaces is `ChartSurface` in
         `web/src/panels/RunsPanel.tsx`, which draws the core's SVG inline
         through `dangerouslySetInnerHTML` for an SVG chart and a link for a
         PNG one. The renderer the shell uses reads the same run result the
         core's renderer reads - `GET /cases/{id}/runs/{id}` gives the
         columns and the rows, which is what the chart controls already
         offer - so the geometry comes from the same stored numbers the
         finding rests on. F3's motion layer wraps the surface, and the
         surface keeps its `arrive` variant.
INPUTS: recharts@3 (installed, unused), the run result the chart controls
        read (`Run` in `web/src/api.ts`: `columns`, `rows`, `truncated`),
        `ChartModel`'s own rules in `server/app/charts.py` (the series
        split, the plottable-points filter, the palette, the
        zero-anchored bar scale), and the measurement suite that pins
        AT-27's 200ms budget.
RELEVANT FILES: web/src/lib/chart.tsx (new - the recharts surface, the
                shared geometry: series splitting, plottable points, the
                palette), web/src/panels/RunsPanel.tsx (ChartSurface
                replaced; the pickers, the refusal path and the PNG link
                stay), web/src/chart.test.tsx (new), web/src/index.css (a
                rule that holds the chart readable when recharts does not
                run - the CSS-side of the same failure F3's gate covers),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - One geometry, two renderers. The series split, the plottable-points
    filter and the palette are the core's own rules, so they live in one
    module the shell and the tests read, and a divergence between what the
    analyst sees and what the core drew is a named failure rather than a
    drift. The module exports the shape recharts takes - one record per x
    category, one key per series - and nothing else.
  - The surface: `bar` is a `BarChart` with `BarChart`'s bars at the
    palette's colours; `line` is a `LineChart` with `Line` and its points.
    Both carry `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip` and `Legend`
    when there is more than one series. The axes name themselves with the
    columns they plot, and the y axis is zero-anchored for a bar, because
    bar length reads as magnitude. The chart's own title and its source
    line stay where the static surface had them, and the surface keeps
    F3's motion wrapper and its `data-testid`.
  - What a chart must never do here: invent a series, drop a category the
    result had, or plot a point the measure column did not have. The
    transformation is the core's `_series_of`, not recharts' own
    grouping, so the on-screen chart and the stored SVG answer the same
    question the same way.
  - The fallback: the recharts surface is a React tree, and a React tree
    can fail to render - a measure column with no plottable points, a
    category list that came back empty, a shape recharts rejected. A
    surface that renders nothing is the static-SVG failure mode without
    the static SVG's saving grace, so the surface falls back to the
    core's own image the moment its own geometry is empty, and a CSS
    rule holds the container's height so the panel does not collapse.
  - The artifact is untouched: the PNG chart stays a link to the artifact
    the core wrote, the SVG chart is still stored by the core, and the
    export package and the evidence graph still carry the core's own
    image. No new endpoint, no new persistence, no server line moves.
NON-GOALS: new chart kinds (the PRD's `bar` and `line` are what the core
           renders; a third kind is a change to the core's contract, not
           to the shell), the export path (the core's SVG and PNG are the
           exported artifact and stay so - a chart that changes shape
           between the screen and the export is not evidence), touching
           the server, restyling anything outside the chart surface, and
           any measurement that is not the AT-27 budget the suite already
           asserts.
CONSTRAINTS: green only. No new dependency (recharts is F1's, now used).
             Deterministic and offline: the chart is drawn from a stored
             result, not from a live query, so a re-render is the same
             chart. Web-only: no line outside `web/` moves, so the server
             suite (727), e2e (28/28), golden (21/21), refine (AT-04) and
             measure (9/9) gates are not re-run. The accessibility audit
             is structural and does not read pixels; the tooltip is a
             keyboard-reachable element or it is not shipped.
ACCEPTANCE CRITERIA:
- [x] recharts is imported and the on-screen chart is its tree: a bar
      chart for `bar`, a line chart for `line`, with axes, gridlines, a
      tooltip and a legend when there is more than one series
- [x] the geometry is the core's own rules: the same result renders the
      same series, the same categories and the same points the core's SVG
      does, and a divergence is a test that names it
- [x] the tooltip reads a point's own values and the hover state names
      what is under the cursor - the thing the static SVG could not give
- [x] the axes name themselves with the columns they plot, and a bar's y
      axis is anchored at zero
- [x] the surface falls back to the core's own image when its geometry is
      empty, and the container's height is held by CSS when the tree does
      not render
- [x] the PNG chart is still a link to the core's artifact, and nothing
      about the stored chart, the export or the evidence graph changed
- [x] the disclosure the measurement layer times is inside its budget
      with the recharts tree mounted, and no existing assertion moved
TESTS: `web/src/chart.test.tsx` (19) - the two kinds each render their
       recharts tree from a fixture result, the geometry matches the
       core's own series split and point set for single- and multi-series
       results, a duplicated category keeps both points, a non-plottable
       measure drops a point but keeps its category, the tooltip is the
       live region a hovered point reaches, the axes carry the column
       names and a bar's height is proportional to its value (the
       zero-anchor, measured as a ratio because jsdom has no SVG getBBox),
       the legend appears only with more than one series and names the
       series, the palette agrees with the core's own, the fallback shows
       the core's image when there is nothing plottable, the CSS rule
       resolves from the shipped stylesheet, the PNG path is still a link,
       and a truncated result draws the rows it carries. Plus the existing
       chart assertions in `CaseWorkspace.test.tsx` pass (one updated: the
       source sentence and the testid, both changed by the renderer swap).
VERIFICATION: `cd web && npm test && npm run build` green (216 = 197 + 19,
               tsc clean, build ok - the emitted CSS is 16.46 kB and still
               resolves the focus rule, the JS 744 kB carrying recharts);
               `cd server && .venv/bin/python -m pytest -q` green (728 =
               727 + 1 - the `format` regression);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48); `verification/e2e/verify_e2e.py` green
               (28/28). F4 is not web-only as contracted: the re-walk
               found the core's `Chart` response missing `format`, which
               is why the recharts tree rendered in jsdom and nowhere
               else, so the server moved one field and one test.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the P9 table closes at
              F4, and the phase closes with a re-walk. No schema change.
```

TASK: P9-F4-001 - the on-screen chart, and a re-walk
ID: P9-F4-001
PRIORITY: high
STATUS: DONE
SUMMARY: recharts@3, the last of F1's three dependencies, draws the chart
         the analyst looks at, and the core's own SVG and PNG stay the
         chart the case holds. `web/src/lib/chart.tsx` is both halves: a
         geometry that is the core's `_series_of`/`_numeric`/palette copied
         into the shell, so the screen and the artifact cannot drift, and a
         recharts surface that carries axes naming their own columns, a
         zero-anchored bar, a legend only when there is more than one
         series, and a tooltip that is a live region. The fallback is the
         discipline: a geometry with nothing plottable shows the core's own
         image, because a chart the analyst cannot see is worse than a
         chart the analyst cannot hover, and a CSS rule holds the
         container's height when the tree does not render.
         The re-walk is what the task will be remembered for. The shell
         rendered every chart as a link - the recharts tree appeared in the
         suite and nowhere else, because the core's `Chart` model never
         returned `format` and the shell read `undefined` straight into the
         PNG branch. A jsdom fixture had supplied the field, which is why
         185 tests said green while the feature was dark. One field
         (`format: str = "svg"`, the default the image endpoint already
         sniffs), one regression test, and a browser confirmation: hovering
         a bar answers its own values, "north" and "total_total : 270".
         The lesson: a contract tested only against a fixture the test
         itself builds is a contract the fixture keeps, not the server.


### P9-F2-002 contract

```
TASK ID: P9-F2-002
MILESTONE: P9 UI/UX Redesign (phase F2, the surfaces)
CAPABILITY: Surfaces (the restyle onto the tokens)
GOAL: the debt F1 and F2-001 took on, paid. The token layer shipped in
      `lib/ui.tsx` and nothing imported it; the panels rendered class names
      the hand-written CSS defined. This moves every surface onto the tokens
      and deletes the CSS rules that only existed to name them, so the palette
      is one set of names in one file and a panel reads one surface name
      instead of a string of properties. The restyle is conservative by
      contract: nothing is restyled and nothing is invented, because the
      surfaces are the CSS rules they replace, as utility classes, with the
      same values. The theme is the existing one named, not a new one drawn.
CONTEXT: F1 shipped the tokens and the primitives and used them nowhere, by
         the same rule that let it install dependencies it did not import
         yet. F2-001 added the `surfaces` strings. The workspace is 15 panels
         in `web/src/panels/` plus five screens that are not panels
         (`CaseList`, `CaseCreation`, `Templates`, `ContextPanel`,
         `RefinePanel`, `DecisionPanel`, `NoticeLayer`), and each carried its
         own `className="panel"` / `"subpanel"` / `"proposal"` / `"run"` /
         `"turn"` / `"muted"` / `"row"`. The accessibility audit reads the
         emitted stylesheet (`accessibility.test.tsx`'s `focusIsGuaranteed`),
         so a rule the audit resolves must survive as a literal declaration.
INPUTS: `web/src/lib/ui.tsx` (the tokens and the `surfaces` strings), the 15
        panel files, the five non-panel screens, `web/src/index.css`, and the
        existing test suites, which are the behaviour contract.
RELEVANT FILES: every file above, `web/src/panels/panels.test.tsx` (+1 test -
                the debt-paid assertion), `ai/HANDOFF.md`, `ai/TASKS.md`,
                `ai/CURRENT_STATE.md`.
REQUIRED CHANGE:
  - Every panel and screen swaps its literal `className="panel"` /
    `"subpanel"` / `"proposal"` / `"run"` / `"turn"` / `"muted"` / `"row"` /
    `"stages"` / `"items"` / `"grounds"` / `"rationale"` for the `surfaces`
    string that holds the same values as utility classes. A panel keeps the
    `panel` word in its class because it is a structural landmark the
    workspace's own tests reach with `heading.closest('.panel')` and the zone
    CSS scopes to `.zone .panel`.
  - `lib/ui.tsx` gains the surfaces the restyle needed and F2-001 did not
    name: `labelheading` (the `.panel h4` size), `turn` (a chat turn's own
    padding), `rowGap` and `buttonRow` (a form's control row and the case
    list's action row), and `smallDanger` as a fifth button variant, because
    a variant that is both small and danger was a class string two panels
    composed by hand. `buttonVariants`'s default carries the base button
    rule's own properties, so a bare `<Button>` is the button the CSS drew.
  - The CSS rules those class names defined are deleted in the same pass:
    `.row` and `.row input` / `.row label`, `.panel h2` / `h3` / `h4`,
    `.muted`, `.stages` / `.items` / `.chat` / `.grounds`, `.stage.done`,
    `.turn`, `.turn .question`, `.subpanel`, `.rationale` and `.rationale p`,
    `.proposal` and `.proposal pre`, `.run`, and `.case-actions`. The rules
    that stay are the ones no token can own: the three-zone layout, the
    sticky rail, the verdict and chip shapes the status vocabulary renders
    as text-plus-chip, the quality-issue and shell-notice surfaces, and the
    literal `:focus-visible` rule the accessibility audit resolves.
  - One regression class, found by auditing the rules the deletion removed
    against the source that still used them, and fixed before any commit:
    `LearnPanel` rendered `className="stage done"` and `FindingsPanel`
    rendered `className="muted"`, both of which lost their rules. `.stage.done`
    stays in the CSS (a completed stage is the one green status, and it is
    the rail's and the ladder's shared vocabulary) and the muted check row
    moves to `surfaces.note`, which carries the size and the colour together.
NON-GOALS: restyling anything beyond parity (a new look is a later pass that
           decides on purpose what changes), motion (F3), the on-screen chart
           (F4), a dark theme, touching the server, changing any test's
           assertion rather than the class it reads, and deleting a rule a
           status chip or the audit resolves.
CONSTRAINTS: green only. No new dependency (DEC-001). The accessibility
             audit's STATUS_CLASSES contract is unchanged: no status class is
             added or removed, and nothing new carries a status by colour
             alone. Web-only: no line outside `web/` moves.
ACCEPTANCE CRITERIA:
- [x] every panel and screen renders its surfaces through the token layer,
      and no source file uses a literal `className` the deleted rules defined
- [x] the CSS the build emits no longer carries the retired rules, and the
      emitted stylesheet still resolves the focus rule the audit reads
- [x] the surfaces are the rules they replaced: same values, same specificity
      behaviour, so a panel on a token renders what the CSS rule rendered
- [x] no class that a surviving rule styles lost its rule - every literal
      className still in the source has its CSS (audited rule by rule, which
      is how the `stage done` / `muted` regressions were caught)
- [x] a test asserts the debt stays paid: a panel that goes back to a literal
      `className="panel"` fails by name
- [x] no other behaviour moved: the existing 184 assertions pass unchanged
TESTS: `panels/panels.test.tsx` (+1) - reads every panel's and screen's source
       through Vite's `?raw` and asserts none of the retired class names
       appears as a literal `className`, naming the file and the class. The
       suite's unchanged assertions are the rest of the contract.
VERIFICATION: `cd web && npm test && npm run build` green (185 = 184 + 1,
               tsc clean, build ok, the emitted CSS 14.44 kB and still
               resolving the focus rule);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48 rows, AT-48 PASS - the symbols the matrix cites
               still resolve). Web-only, so the server suite (727), the e2e
               (28/28), golden (21/21), refine (AT-04) and measure (9/9) are
               not re-run: no line outside `web/` moved (verified by
               `git status`), and their last runs are green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the task; the P9 table closes
              at F2-002. No schema change, no version bump.
```

TASK: P9-F2-002 - the restyle onto the tokens
ID: P9-F2-002
PRIORITY: high
STATUS: DONE
SUMMARY: the token layer is the vocabulary the panels use, and the
         hand-written CSS that named those surfaces is gone. Every panel and
         every screen renders through `surfaces` in `lib/ui.tsx`, and 109
         lines of CSS retired with them - `.panel h2/h3/h4`, `.muted`,
         `.stages`/`.items`/`.chat`/`.grounds`, `.turn`, `.subpanel`,
         `.rationale`, `.proposal`, `.run`, `.row` and `.case-actions`. What
         stays is the layout no token can own: the three-zone grid, the
         sticky rail, the verdict and chip shapes the status vocabulary
         renders as text-plus-chip, the quality and notice surfaces, and the
         literal `:focus-visible` the accessibility audit resolves. The
         restyle is parity by contract - a surface is the rule it replaced,
         as utility classes, with the same values, so nothing looks
         different and the palette is one set of names in one file.
         The lesson the audit earned: deleting the retired rules was only
         safe once the rules were checked against the source that used them,
         not against the list of rules the restyle touched. Two literals
         survived the move and lost their rules - `LearnPanel`'s
         `className="stage done"` and `FindingsPanel`'s `className="muted"`.
         The first keeps its rule, because a completed stage is the one
         green status and the word is the rail's and the ladder's shared
         vocabulary; the second moves to `surfaces.note`, which carries the
         size with the colour. The panels test now asserts the debt stays
         paid, reading every source file raw and naming the file and the
         class if a literal comes back.
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
- [x] a run with a result can render a chart, and the chart appears in the
      shell without leaving the case
- [x] the pickers offer only the columns the run produced
- [x] an unsupported choice is refused with the endpoint's own sentence
- [x] the SVG the response carries is what the shell displays
- [x] the evidence graph's chart count moves when a chart is rendered
TESTS: CaseWorkspace.test.tsx (+6) - the control appears only once the run's
       rows are open, the SVG shows inline and the payload carries the run's
       own columns, the measure picker defaults to the numeric column, the
       case reloads so the evidence count moves, a refusal surfaces the
       renderer's sentence with the control standing, and a bitmap is a link
       to the persisted artifact.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (727);
              `cd web && npm test && npm run build` green (173, build ok);
              `verify_e2e.py` green (28/28); `verify_trace.py` green (48/48).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the chart half of
              W-016 closes.
```
TASK: FIX-CHART-004 - the chart surface
ID: FIX-CHART-004
PRIORITY: high
STATUS: DONE
SUMMARY: a chart is now evidence the analyst can produce and see. The run row
         holds a "Render a chart" control that appears once the run's rows are
         open - those columns are the renderer's input and are exactly what
         the pickers offer, with the measure defaulting to a numeric column -
         and it POSTs the endpoint that owns the write. On success the shell
         fetches the SVG the core drew and renders it inline, because drawing
         it a second time would make the shell a second source of truth for
         what the chart looks like; a PNG is a link to the persisted artifact
         instead. The workspace reloads with a chart, so the evidence graph's
         count moves with the panel, and a refusal shows the renderer's own
         sentence with the control standing. Two things the first test run
         caught: the control was offered before the rows were read, which is
         before there is anything to draw from, so it now waits on the result;
         and the surface was asserted as an img role, which jsdom does not
         give an inline SVG - the assertion reads the element instead.

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
- [x] the panel generates python for a python question and the code it
      proposes is what the sandbox accepts
- [x] running a python proposal creates a run the runs panel and the
      evidence graph carry
- [x] a script the sandbox refuses answers a 400 whose detail the panel
      shows as a sentence
- [x] the kind persists across proposals in the same panel
- [x] the SQL path is unchanged in behaviour and in its tests
TESTS: CaseWorkspace.test.tsx (+4) - python generation and its run, the
       engine persisting across proposals, the refusal surfaced, SQL
       unaffected (its own test still asserts the run posts to the SQL
       endpoint and never the python one).
VERIFICATION: `cd server && ... pytest -q` green (727);
              `cd web && npm test && npm run build` green (177, build ok);
              verification/e2e, golden, refine (AT-04), measure (9/9) and
              trace (48/48) all green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the python half of
              W-016 closes and W-016 is done.
```

### FIX-PYTHON-005 done-record

```
TASK: FIX-PYTHON-005 - a python run surface
ID: FIX-PYTHON-005
PRIORITY: high
STATUS: DONE
SUMMARY: the codegen panel now offers two engines where it offered one. A
         kind selector (SQL, the default, and Python) picks the code the
         generator is asked for and persists across proposals in the same
         panel, and the run posts to the endpoint matching the proposal's own
         kind rather than the selector's current value - the code the analyst
         read is the code that executes. `runPython` posts to the sandbox's
         own endpoint, which was reachable only by curl before, so the hard
         sandbox P3-SEC-001 exists to prove is now exercised by someone using
         the app. A persisted python run is a run like any other: the same
         runs panel, the same evidence chain, the same validation. The
         seatbelt's 400 detail renders as a sentence and the proposal stands
         to be fixed and retried. Two things the first test run caught: two
         radios named python/sql on the same page (the EVAL panel's own
         kind-toggle) matched every /python/i query, so the codegen radios
         carry their own aria-label and the audit test now scopes its click to
         its panel; and a multi-line script does not survive getByText's
         whitespace normalisation, so the pre's own textContent is what the
         assertion reads.
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

### FIX-VERSION-001 done-record

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
