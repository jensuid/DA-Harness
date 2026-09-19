# DAH - Global Roadmap Status

Source of truth for **where we are** on the global roadmap
(`docs/Implementation Roadmap.md`). Every phase completion must update this
file together with `CURRENT_STATE.md` and `TASKS.md`.

**Current stage: P4 Production Candidate — IN PROGRESS (P3 gate complete).**

```
P0 Foundation          DONE  ✓
P1 Vertical Slice      DONE  ✓
P2 MVP                 DONE  ✓   (all gates green)
P3 V1                  DONE  ✓   (all 10 entry-checklist items, 211 tests;
                              verification/p3/REPORT.md PASS)
P4 Production Candidate DONE  ✓   (all 6 checklist items; CI runs every
                              layer, signing formally deferred to P5 by
                              DEC-004)
P5 Production Grade    NOT STARTED  ← we are here
P5 Production Grade    NOT STARTED
P6 Evolution           NOT STARTED
```

North-star progression: prove the loop → make it useful → make it repeatable
→ make it reliable → make it production-grade → make it intelligent →
make it scale. P4 was **make it reliable**; P5 is **make it
production-grade**.

## Phase status

| Phase | Goal | Status | Gate | Evidence |
|-------|------|--------|------|----------|
| P0 Foundation | Runnable app, cross-layer comms, basic persistence, tests | DONE | PASS | `verification/p0/REPORT.md` |
| P1 Vertical Slice | One complete analytical case end to end | DONE | PASS | `verification/p1/REPORT.md` |
| P2 MVP | Usable analytical application; inspectable, reproducible case | DONE | PASS | `verification/p2/REPORT.md` (16 steps, 10 exit criteria) |
| P3 V1 | Repeated real-world use: multi-dataset, joins, richer EDA, contextual AI | DONE | P2 gate PASS (re-verified during close, 211 tests) | hard sandbox, raster charts, multi-dataset joins, workflow, EDA, evidence graph, case reuse, desktop shell and all four contextual AI slices DONE |
| P4 Production Candidate | Serious software: reliability, security, performance, UX, observability | DONE | P3 gate PASS | `verification/p3/REPORT.md` (23 journey steps, 15 exit criteria, all PASS); CI runs every layer (P4-CI-007); signing deferred to P5 by DEC-004 |
| P5 Production Grade | Maintainable, distributable, secure product | NOT STARTED | — | — |
| P6 Post-Launch Evolution | Scale and intelligence | NOT STARTED | — | — |

## Phase gate definitions (what "done" means)

- **P0:** start → communicate across layers → persist basic state → run tests.
- **P1:** a real user completes one complete analytical case beginning to end.
- **P2:** a user answers a real analytical question and produces a structured
  Analysis Case another person can inspect and reproduce.
- **P3 (V1):** a regular analyst uses DAH for multiple investigations, not a demo.
- **P4:** stable, secure, usable, reliable enough for controlled external users.
- **P5:** tested, hardened, distributable, maintainable, observable, supportable.

## Current position detail

- **Completed capabilities:** FastAPI core; SQLite case state; DuckDB analytical
  engine; React+Vite shell; CSV/Parquet/Excel ingest; deep profiling; read-only
  SQL and Python execution with persisted results; deterministic SVG charts;
  case management (rename/duplicate/delete); structured AI planning
  (deterministic default, LLM behind `DAH_LLM_API_KEY`); case export/import
  round trip.
- **Test status:** server 231 passed; web 17 passed; desktop shell 7 Rust
  tests (5 unit + 2 e2e); P2, P3 **and P4** gates PASS. All of it runs in CI
  (`.github/workflows/ci.yml`) - before P4-CI-007, every test was green only
  because a developer happened to run it.
- **Active task:** P5-VERIFY-001 DONE - the P4 gate exists, so P4 finally
  has what every earlier phase has: one journey that walks its capabilities end
  to end. Where P3's gate proved the loop is *useful*, this one proves it is
  *safe to hand to someone else* by walking the edges instead of the happy
  path: a 5000-row dataset, the result cap truncating a full scan while an
  aggregate over the same data stays exact, bad SQL answering 400 with the
  engine's own message and leaving nothing behind, a write and a sandbox escape
  both refused, an injected harness fault answering 500 rather than blaming the
  analyst, a deliberately broken LLM degrading to the deterministic engine, and
  eight repeat validations of an unordered GROUP BY agreeing every time. 18
  steps and 10 exit criteria, all PASS; CI runs it on every push.
  Before it (P4, now closed): the P3 gate, error semantics, the assistant
  surfaces in the shell, validation determinism, large-dataset performance, and
  CI plus the signing decision.
- **Known issues / blockers:** none.
- **Repository:** private, `master` tracks `origin/master`.

## P3 V1 — entry checklist (COMPLETE)

All ten items delivered. Contextual AI (item 7) landed as four slices - result
interpretation (P3-AI-011), finding drafting (P3-AI-012), code generation
(P3-AI-013) and conversational memory (P3-AI-014) - each behind one interface
with a deterministic engine that is always available and an LLM that degrades
to it on any failure, and each validated so it cannot invent a number, a column
or a citation.

Ordered so each step unblocks the next; the hardening items deferred from P2
come first because P3 code generation multiplies the risk.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | Hard OS-level sandbox for Python execution — **DONE (P3-SEC-001)** | P2 shipped a process-level read-only guard; P3 code generation multiplies the risk | P4 Security (pulled forward) |
| 2 | LLM key for the planner (`DAH_LLM_API_KEY`) — **configured** (`server/.env`; the P2 gate's plan step reports `source=llm`) | Deterministic path is verified; P3 contextual AI needs the real backend | P3 AI |
| 3 | Raster chart backend — **DONE (P3-CHART-002)** | SVG covers MVP; richer visualization needs PNG/high-DPI | P3 Analysis |
| 4 | Multiple datasets per case + joins — **DONE (P3-DATA-003)** | Core P3 capability; everything below depends on it | P3 Data |
| 5 | Guided workflow + stage completion — **DONE (P3-FLOW-004)** | Turns features into a repeatable process | P3 Analysis workflow |
| 6 | Richer EDA, segmentation, statistical tests — **DONE (P3-ANALYSIS-005)** | Depth after the multi-dataset base (formal hypothesis tests deferred) | P3 Analysis |
| 7 | Contextual AI assistant — **DONE (P3-AI-011, P3-AI-012, P3-AI-013, P3-AI-014)**: result interpretation, finding drafting, code generation, conversational memory | Only after the deterministic surface is complete (it now is) | P3 AI |
| 8 | Evidence graph / claim-to-source tracing — **DONE (P3-EVIDENCE-006)** | Trust layer for repeated use | P3 Evidence |
| 9 | Case templates, search, case history — **DONE (P3-CASE-007)** | Repeatability and reuse | P3 Case management |
| 10 | Tauri desktop shell — **DONE (P3-SHELL-008)** | Wraps the existing React bundle; post-MVP as planned | Platform decision |

## P4 Production Candidate — entry checklist (COMPLETE)

All six items delivered. The last one closes the phase: the desktop shell's
lifecycle is now verified by CI rather than by a developer remembering to run
it, and signing is a written decision instead of an open question.

Ordered oldest-risk first.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | P3 gate script (`verification/p3/verify_p3.py`) — **DONE (P4-VERIFY-001)**: 23 steps joining a CSV and a Parquet, refusing a sandbox escape, firing all four assistant slices, validating a join finding and round-tripping through export/import | The P2 gate re-verifies the suite but nothing walked the P3 capabilities end to end; a phase is done when a gate says so. Now it does | P4 Verification |
| 2 | Error semantics - **DONE (P4-RELIABILITY-002)**: input errors answer 400 with the engine's own message; a harness fault answers 500 instead of the old broad `except Exception -> 400` that blamed the analyst for our own bugs. The five LLM fallbacks stay broad (degradation is the contract) but now log the reason | P3 added four LLM fallback paths, each intentionally broad; P4 is where that breadth stops hiding real bugs | P4 Reliability |
| 3 | Assistant surfaces in the React shell - **DONE (P4-UX-003 + P4-UX-004)**: the case workspace plus chat (each citation a chip, the engine that spoke badged), and the run-scoped slices - attach+profile, generate code, run, interpret, draft, accept, validate - one panel per step with every write posted to the endpoint that owns it. The live smoke of P4-UX-004 exposed a validation flake, fixed as **P4-VALID-005**: DuckDB returns an unordered GROUP BY's groups in either order across connections, so reproduction now compares rows as a multiset and a verdict no longer depends on which connection answered | The widest gap between what DAH can do and what it shows; the backend is complete, the UI was the P0/P1 surface | P4 UX |
| 4 | Large-dataset behaviour - **DONE (P4-PERF-006)**: benchmarked at 200k rows - attach 0.2s, query 0.8s, export 0.4s / 17.8MB, but profiling ~6.0s. Fixed: the description is read with `LIMIT 0` instead of a full `fetchall()` (2.7s of rows materialised then discarded), the row total is folded into the one aggregate pass, and the duplicate count reuses it - ~6.0s -> ~2.4s, peak RSS 147 -> 111MB, profile output unchanged. Six tests pin profile correctness, the wide-table width slicing, duplicate counts and the result cap at scale | P3 caps results at 1000 rows and nothing had been measured at scale | P4 Performance |
| 5 | Desktop shell lifecycle under CI + app signing - **DONE (P4-CI-007)**: `.github/workflows/ci.yml` runs the server suite and both gates, the web suite and build, the desktop lifecycle tests against a live core, and a sidecar packaging build with a /health smoke. macOS-only (seatbelt sandbox, macOS sidecar and .app); no job needs any secret. Signing **deferred to P5 by DEC-004** - the cost is the pipeline, not the fee, and Gatekeeper's prompt is a once-per-machine cost that degrades gracefully; the README documents the workaround | The shell was tested locally only; the unsigned first launch was a carried item with no decision behind it | P4 Distribution |




## Rules this file enforces

- A phase is complete only when Feature + Tests + Verification + Documentation
  + State Update are all in place (roadmap section 13).
- Never hand a coding agent an entire phase; decompose to
  Phase → Milestone → Capability → Task → Implementation → Test → Verification
  (roadmap section 14).
- When a phase closes: update this file's stage marker, the phase table, and
  the entry checklist of the next phase.
- Commit and push continuously: one atomic commit per task and one per phase
  close, green state only, pushed to origin/master before work is called done
  (see the commit and push discipline section of AGENTS.md).

## P5 Production Grade — entry checklist (1 of 5 done)

Ordered oldest-risk first; a proposal for the user to reorder before work
starts. P4 closed with the signing question decided rather than open
(DEC-004), so the distribution items below carry a written rationale instead
of a shrug.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | macOS code signing + notarization — **formally deferred here by DEC-004**: provision a Developer ID identity, store it as a CI secret in the `packaging` job, notarize the bundle, and keep the unsigned build as a fallback target | P4 shipped unsigned with a documented right-click > Open workaround; the pipeline cost (identity, rotation, re-signing an in-flight bundle) is the reason it waited, and P5 is where the bundle becomes final | P5 Distribution |
| 2 | The P4 gate — **DONE (P5-VERIFY-001)**: `verification/p4/verify_p4.py` walks the *edges* rather than the happy path - a 5000-row dataset, the result cap truncating a full scan while an aggregate stays exact, bad SQL answering 400 with the engine's message and persisting nothing, a sandbox escape refused, an injected harness fault answering 500, a deliberately broken LLM degrading to deterministic, and eight repeat validations of an unordered result agreeing. 18 steps, 10 exit criteria, all PASS; CI runs it on every push | P4 relied on the P3 gate plus CI, which never exercised the P4 capabilities against each other - the error taxonomy and rerun determinism are invisible on the happy path | P5 Verification |
| 3 | Observability: structured logs and a way to read them when a user hits a problem, beyond uvicorn's stderr | P4 made a 500 honest and logged with a traceback, but there is nowhere for that output to go in a packaged app a non-developer is running | P5 Observability |
| 4 | Give the 500 a JSON envelope — **carried from P4-RELIABILITY-002**: the core still answers Starlette's plain-text "Internal Server Error", which the client already tolerates but which is the one remaining rough edge in the error contract | Small, self-contained, and it closes the last item the reliability task explicitly declined to expand into | P5 Reliability |
| 5 | Release automation: versioned, notarized artifacts published from CI rather than built by hand | The `packaging` job already builds and smokes the sidecar on a clean machine; publishing is the step after signing lands | P5 Distribution |
