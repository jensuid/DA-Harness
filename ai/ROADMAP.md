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
P4 Production Candidate IN PROGRESS  ← we are here
                              (P4-VERIFY-001 and P4-RELIABILITY-002 done;
                              UX, performance, distribution remain)
P5 Production Grade    NOT STARTED
P6 Evolution           NOT STARTED
```

North-star progression: prove the loop → make it useful → make it repeatable
→ make it reliable → make it production-grade → make it intelligent →
make it scale. We are at the **make it useful** stage; P3 is **make it
repeatable**.

## Phase status

| Phase | Goal | Status | Gate | Evidence |
|-------|------|--------|------|----------|
| P0 Foundation | Runnable app, cross-layer comms, basic persistence, tests | DONE | PASS | `verification/p0/REPORT.md` |
| P1 Vertical Slice | One complete analytical case end to end | DONE | PASS | `verification/p1/REPORT.md` |
| P2 MVP | Usable analytical application; inspectable, reproducible case | DONE | PASS | `verification/p2/REPORT.md` (16 steps, 10 exit criteria) |
| P3 V1 | Repeated real-world use: multi-dataset, joins, richer EDA, contextual AI | DONE | P2 gate PASS (re-verified during close, 211 tests) | hard sandbox, raster charts, multi-dataset joins, workflow, EDA, evidence graph, case reuse, desktop shell and all four contextual AI slices DONE |
| P4 Production Candidate | Serious software: reliability, security, performance, UX, observability | IN PROGRESS | P3 gate PASS | `verification/p3/REPORT.md` (23 journey steps, 15 exit criteria, all PASS) |
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
- **Test status:** server 223 passed; web 2 passed; desktop shell 7 Rust tests (5 unit + 2 e2e);
  P2 and P3 gates PASS.
- **Active task:** P4-RELIABILITY-002 DONE - error semantics. Input errors
  answer 400 with the engine's own message and a harness fault answers 500,
  where before a single broad `except Exception` flattened both into a 400
  that blamed the analyst.
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

## P4 Production Candidate — entry checklist (proposed, not started)

Ordered oldest-risk first; a proposal for the user to reorder before work
starts. P3 has no gate of its own yet, so that comes first.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | P3 gate script (`verification/p3/verify_p3.py`) — **DONE (P4-VERIFY-001)**: 23 steps joining a CSV and a Parquet, refusing a sandbox escape, firing all four assistant slices, validating a join finding and round-tripping through export/import | The P2 gate re-verifies the suite but nothing walked the P3 capabilities end to end; a phase is done when a gate says so. Now it does | P4 Verification |
| 2 | Error semantics - **DONE (P4-RELIABILITY-002)**: input errors answer 400 with the engine's own message; a harness fault answers 500 instead of the old broad `except Exception -> 400` that blamed the analyst for our own bugs. The five LLM fallbacks stay broad (degradation is the contract) but now log the reason | P3 added four LLM fallback paths, each intentionally broad; P4 is where that breadth stops hiding real bugs | P4 Reliability |
| 3 | Assistant surfaces in the React shell (generate-code, draft-finding, interpret, chat) | The widest gap between what DAH can do and what it shows; the backend is complete, the UI is still the P0/P1 surface | P4 UX |
| 4 | Large-dataset behaviour: result caps, profiling cost, export package size | P3 caps results at 1000 rows but nothing has been measured at scale | P4 Performance |
| 5 | Desktop shell lifecycle under CI; app signing decision (sign now, or formally defer to P5) | The shell is tested locally; the unsigned first launch is the carried P3 item | P4 Distribution |




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
