# DAH - Global Roadmap Status

Source of truth for **where we are** on the global roadmap
(`docs/Implementation Roadmap.md`). Every phase completion must update this
file together with `CURRENT_STATE.md` and `TASKS.md`.

**Current stage: P2 MVP — COMPLETE. P3 V1 — NOT STARTED.**

```
P0 Foundation          DONE  ✓
P1 Vertical Slice      DONE  ✓
P2 MVP                 DONE  ✓   ← we are here (all gates green)
P3 V1                  NOT STARTED
P4 Production Candidate NOT STARTED
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
| P3 V1 | Repeated real-world use: multi-dataset, joins, richer EDA, contextual AI | NOT STARTED | — | — |
| P4 Production Candidate | Serious software: reliability, security, performance, UX, observability | NOT STARTED | — | — |
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
- **Test status:** server 79 passed; web 2 passed.
- **Active task:** none — P2 milestone closed.
- **Known issues / blockers:** none.
- **Repository:** private, `master` tracks `origin/master`.

## P3 V1 — entry checklist (next work, nothing started)

Ordered so each step unblocks the next; the hardening items deferred from P2
come first because P3 code generation multiplies the risk.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | Hard OS-level sandbox for Python execution — **DONE (P3-SEC-001)** | P2 shipped a process-level read-only guard; P3 code generation multiplies the risk | P4 Security (pulled forward) |
| 2 | LLM key for the planner (`DAH_LLM_API_KEY`) | Deterministic path is verified; P3 contextual AI needs the real backend | P3 AI |
| 3 | Raster chart backend — **DONE (P3-CHART-002)** | SVG covers MVP; richer visualization needs PNG/high-DPI | P3 Analysis |
| 4 | Multiple datasets per case + joins | Core P3 capability; everything below depends on it | P3 Data |
| 5 | Guided workflow + stage completion | Turns features into a repeatable process | P3 Analysis workflow |
| 6 | Richer EDA, segmentation, statistical tests | Depth after the multi-dataset base | P3 Analysis |
| 7 | Contextual AI assistant, code generation, result interpretation, finding drafting | Only after the deterministic surface is complete | P3 AI |
| 8 | Evidence graph / claim-to-source tracing | Trust layer for repeated use | P3 Evidence |
| 9 | Case templates, search, case history | Repeatability and reuse | P3 Case management |
| 10 | Tauri desktop shell | Wraps the existing React bundle; post-MVP as planned | Platform decision |

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
