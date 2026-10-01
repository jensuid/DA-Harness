# DAH - Global Roadmap Status

Source of truth for **where we are** on the global roadmap
(`docs/Implementation Roadmap.md`). Every phase completion must update this
file together with `CURRENT_STATE.md` and `TASKS.md`.

**Current stage: P9 UI/UX Redesign — COMPLETE (4 of 4). No phase is open; v0.3.8 is published.**

```
P0 Foundation          DONE  ✓
P1 Vertical Slice      DONE  ✓
P2 MVP                 DONE  ✓   (all gates green)
P3 V1                  DONE  ✓   (all 10 entry-checklist items, 211 tests;
                              verification/p3/REPORT.md PASS)
P4 Production Candidate DONE  ✓   (all 6 checklist items; CI runs every
                              layer)
P5 Production Grade    DONE  ✓   (all deliverables; signing deferred
                              indefinitely by DEC-006 - DAH is single-user)
P6 Evolution           COMPLETE ✓  (all 5 checklist items)
P7 Product Modes       COMPLETE ✓  (all 4 checklist items built; the web-shell
                              gap closed; EVALUATE, LEARN and multi-agent
                              workflows in core and shell; v0.1.0 and v0.2.0
                              published)
P8 Analytical Contract COMPLETE ✓  (all 10 checklist items; every PRD threshold
                              now carries a measured number and every requirement
                              traces end to end; v0.3.0, v0.3.1 and v0.3.2 are published)
P9 UI/UX Redesign       COMPLETE ✓  (all 4 phases: the foundation, the surfaces,
                              the motion, the on-screen chart; 19 walk-test
                              findings closed; v0.3.5 published; the walk-test
                              follow-ups W3X/W4X/W5X closed in v0.3.6 and v0.3.7;
                              the UI/UX audit plan's twelve items all resolved
                              in v0.3.8: the restyle, the dark mode, the
                              skeletons, the marks, the landmarks and the zone
                              composition)
                              ← we are here
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
| P5 Production Grade | Maintainable, distributable, secure product | DONE | — | P4 gate, observability, the 500 envelope, release automation, the Reveal-logs menu and the CI repair (P5-CI-FIX-007) DONE; v0.1.0 published. Only signing remains, blocked on the Apple Developer ID (DEC-004). CI runs on macos-latest - macos-13 is retired (DEC-005) |
| P6 Post-Launch Evolution | Scale and intelligence | DONE | — | all 5 checklist items: cross-case recall (P6-MEMORY-001), agentic analysis (P6-AGENT-002), analytical-shape templates (P6-TEMPLATE-003), the versioned migration path (P6-MIGRATE-004) and the update check (P6-UPDATE-005) |
| P7 Product Modes | The spec's LEARN and EVALUATE modes, and the UI surface for the P6 capabilities | DONE | — | all 4 checklist items: EVALUATE (P7-EVAL-001 + P7-SHELL-002), the closed web-shell gap (P7-SHELL-002..009, eight surfaces), LEARN (P7-LEARN-001 + P7-SHELL-010) and multi-agent workflows (P7-AGENT-001 + P7-SHELL-011); a real-server end-to-end run (P7-E2E-001), a hand walkthrough (P7-WALK-001), the packaged app's CORS fix (P7-CORS-001) and the CSV fix (P7-CSV-002) |
| P8 Analytical Contract | Close the PRD's Level 1 breadth gaps and make "done" measurable | DONE | — | all 10 checklist items: the case's context object (P8-CONTEXT-001), quality beyond missingness (P8-QUALITY-002), the nine validation dimensions (P8-VALID-003), the causal guard (P8-CAUSAL-004), the analytical golden suite (P8-GOLDEN-005), the orientation spine (P8-SHELL-006), question refinement (P8-REFINE-007), the decision view (P8-DECISION-008), the measurement layer (P8-MEASURE-009) and the traceability matrix (P8-TRACE-010); server 686, web 138, 28/28 e2e, schema v13 |
| P9 UI/UX Redesign | The redesign the walk-test and the conformance evaluation asked for | DONE | — | all 4 phases: the foundation (P9-F1-001: tooling, tokens, the panel split), the surfaces (P9-F2-001 the walk-test's last three, P9-F2-002 the restyle), the motion (P9-F3-001) and the on-screen chart (P9-F4-001, with the re-walk that found the missing `format` field). The audit plan's twelve items are all resolved: UI-REDUX (phases 1 and 2), DMDARK, SKEL, ICON, ZONE-A and ZONE-B. web 330, server 796, 28/28 e2e, trace 48/48; v0.3.5 published |

## Phase gate definitions (what "done" means)

- **P0:** start → communicate across layers → persist basic state → run tests.
- **P1:** a real user completes one complete analytical case beginning to end.
- **P2:** a user answers a real analytical question and produces a structured
  Analysis Case another person can inspect and reproduce.
- **P3 (V1):** a regular analyst uses DAH for multiple investigations, not a demo.
- **P4:** stable, secure, usable, reliable enough for controlled external users.
- **P5:** tested, hardened, distributable, maintainable, observable, supportable.

## Current position detail

- **Completed capabilities:** FastAPI core; SQLite case state (schema v13, with
  a versioned migration path); DuckDB analytical engine; React+Vite shell
  wrapped by the Tauri desktop app; CSV/Parquet/Excel ingest; deep profiling
  with seven defect classes; read-only SQL and Python execution (the latter
  under an OS-level sandbox) with persisted results; raster charts; case
  management, search, history, templates and cross-case recall; structured AI
  planning, code generation, interpretation, drafting and chat - deterministic
  by default, LLM behind `DAH_LLM_API_KEY`; EVALUATE and LEARN modes; analyst
  and reviewer agent roles behind one approval gate; question refinement; the
  decision view that closes the loop; case export/import round trip; the
  measurement layer and the requirement-traceability matrix.
- **Test status:** server 796 passed; web 330 passed; desktop shell 30 Rust
  tests. The P2, P3 and P4 gates PASS, and the verification runners are green:
  the real-server e2e journey (28/28), the analytical golden suite (21/21
  reference and workflow), AT-04's refinement thresholds, the measurement
  layer (9/9) and the traceability matrix (48/48 rows; AT-48's own 15/15 and
  33/33).
- **Active task:** none open. P9 UI/UX Redesign is COMPLETE (4 of 4) and the
  audit plan's twelve items are all resolved, so no phase and no task is
  queued. Every one of the PRD's 48 acceptance thresholds traces from the PRD,
  through the UX surface, the implementation and the test, to a measured or
  asserted threshold (`verification/trace/REPORT.md`). v0.3.8 is published
  (tag `v0.3.8`), bundling the five UI tasks that landed after v0.3.7:
  DMDARK, SKEL, ICON, ZONE-A and ZONE-B.
- **Known issues / blockers:** none in the code. Two are environmental:
  (1) GitHub Actions refuses every job with "recent account payments have
  failed" - an account-billing problem (Settings > Billing & plans), so
  nothing pushed since `c73118c` has run in CI and the v0.2.0 artifacts were
  built and published locally from the same steps `release.yml` runs;
  (2) the documented Ventura floor is no longer CI-enforced because GitHub
  retired the `macos-13` pool (DEC-005) - restoring it needs a self-hosted
  Intel runner. Signing and notarization are deferred indefinitely by DEC-006
  (DAH is single-user), so the published app is unsigned and Gatekeeper needs
  right-click → Open on first launch.
- **Supported platform:** macOS. See `README.md`.
- **Desktop shell:** **DAH > Reveal DAH Logs** asks the core where its log is
  and opens the folder in Finder with the file selected (P5-UX-006).
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

## P5 Production Grade — entry checklist (COMPLETE; signing retired by DEC-006)

Ordered oldest-risk first; a proposal for the user to reorder before work
starts. P4 closed with the signing question decided rather than open
(DEC-004), so the distribution items below carry a written rationale instead
of a shrug.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | macOS code signing + notarization — **retired by DEC-006**: DAH is single-user for the foreseeable future, so the notarized identity is not needed and the once-per-machine right-click > Open cost is paid by the one person who uses it. The slot stays in `release.yml` between build and upload if that ever changes | P4 shipped unsigned with a documented right-click > Open workaround; DEC-004 deferred the pipeline cost (identity, rotation, re-signing an in-flight bundle) to P5; DEC-006 retires it as an unblocked-but-unwanted item rather than leaving P5 blocked on a purchase nobody needs | P5 Distribution |
| 2 | The P4 gate — **DONE (P5-VERIFY-001)**: `verification/p4/verify_p4.py` walks the *edges* rather than the happy path - a 5000-row dataset, the result cap truncating a full scan while an aggregate stays exact, bad SQL answering 400 with the engine's message and persisting nothing, a sandbox escape refused, an injected harness fault answering 500, a deliberately broken LLM degrading to deterministic, and eight repeat validations of an unordered result agreeing. 18 steps, 10 exit criteria, all PASS; CI runs it on every push | P4 relied on the P3 gate plus CI, which never exercised the P4 capabilities against each other - the error taxonomy and rerun determinism are invisible on the happy path | P5 Verification |
| 3 | Observability — **DONE (P5-OBSERVE-002)**: the core writes a size-capped rotating log (2MB x 3) into the user's data dir, `GET /logs?lines=N` tails it read-only, one line per request holds only method/path/status/duration, and nothing the analyst typed is ever logged | P4 made a 500 honest and logged with a traceback, but there was nowhere for that output to go in a packaged app a non-developer is running — now there is | P5 Observability |
| 4 | Give the 500 a JSON envelope — **DONE (P5-RELIABILITY-003)**: a fault answers `{"detail": "internal error", "request_id": ...}`, the id finds the traceback in the log, the exception's own message stays in the log and never the body, and the 4xx contract is untouched | The client tolerated the plain text; now it gets the same shape as every other error, plus an id a user can quote | P5 Reliability |
| 5 | Release automation — **DONE (P5-RELEASE-005)**: a `v<x.y.z>` tag matching `server/pyproject.toml` builds, smokes and publishes an unsigned `.app` as a flagged pre-release with its checksum and generated notes; the version has one source of truth and a tag that disagrees with it fails before any build. v0.2.0 was built and published by hand from these same steps because GitHub Actions would not start any job (account billing suspended) — the workflow is correct; the account is the blocker | The `packaging` job already built and smoked the sidecar on a clean machine, but its output went nowhere; now a user can download instead of build. Signing is the slot this job leaves open — it goes between the build and the upload | P5 Distribution |

## P6 Post-Launch Evolution — entry checklist (COMPLETE, 5 of 5)

Ordered by what makes the product more useful to its one current user first,
which is also the order the roadmap's own dependency chain dictates: memory
before agents, because an agent with nothing to remember repeats the same
investigation from scratch every time. A proposal for the user to reorder
before work starts.

The roadmap frames P6 as "scale and intelligence." For a single-user tool,
**intelligence is the whole value** and the scale items (cloud sync, team
collaboration, warehouse connectors, enterprise governance) are not - they are
listed as deferred rather than dropped, but none is on this checklist. What is
here is the half of "make it intelligent" that pays off for one person.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | **Analysis memory** — **DONE (P6-MEMORY-001)**: cross-case recall. A case can already cite its own artifacts; nothing lets it cite a *previous* case. The assistant answers from one case's rows today; with memory it answers from the pattern across all of them ("you found this same anomaly in the Q2 file, and it was a duplicate-row artifact then"). Implementation shape to decide: a case-indexed search over existing SQLite rows, or a separate memory store written on finding-accept | The master spec puts Analysis Memory at level 4 of its own evolution ladder (after the case builder, the workbench, and evidence + validation, which are all done) and before agentic analysis at level 5. Memory is the input an agent needs; building the agent first means building it amnesiac | P6 Analysis Memory |
| 2 | **Agentic analysis** — **DONE (P6-AGENT-002)**: a plan that executes itself. `app/agent.py` derives the next step as a pure projection over the case's artifacts, a human approves that step by id, and the write runs through the endpoint that already owns it. An empty result rotates to a different query, three empty attempts end the run at a stated reason, and every step records which engine proposed it. Every piece existed as an endpoint; the loop did not | The loop is currently driven by a human clicking through panels. The deterministic planner, generator, interpreter and drafter are all already composable, so an agent is orchestration over existing validated primitives - the highest capability-per-risk item left, and it is only safe because P4 pinned the honesty budgets and P5 made faults observable | P6 Agentic Analysis |
| 3 | **Case templates from real history** — **DONE (P6-TEMPLATE-003)**: promote a finished investigation into a reusable template *including its plan and validation shape, not just its question*. A nullable `templates.shape_json` carries a pure projection over the case's artifacts - its latest plan and source engine, the proposals its agent run made (falling back to its runs), and its findings' statements with their verdicts. A case started from a template records its lineage, the plan step offers the template's plan through the same `validate_plan`, and generate-code offers a template proposal only when every column it reads exists in the profiled dataset. Both record `source="template"` and both degrade to the deterministic path on any problem, so a shapeless, malformed or deleted template is never an error | Repeat use is the stated premise of P3/V1 and the one thing a single user actually does repeatedly; a template that carries the analytical shape is the difference between reuse and retyping | P6 Case reuse |
| 4 | **Schema evolution / migration story** — **DONE (P6-MIGRATE-004)**: the store's version lives in SQLite's `user_version` (the file header, readable before any table exists), the seven historical `_ensure_column` additions are an ordered, named, forward-only chain applied one transaction each - change, audit row and version stamp land together, so a crash mid-chain resumes at the next open - a store newer than the build is refused rather than silently downgraded, and `GET /schema-version` reports whether the local data is current for the build being run | P6 adds memory, which means new tables. Doing it after the tables exist is how the in-place additions became untrackable in the first place - now a future task appends a named migration instead | P6 Maintainability |
| 5 | **Update flow for the packaged app** — **DONE (P6-UPDATE-005)**: `GET /updates/latest` answers one of three truths - `current`, `available` (with the tag, the release page and the notes) or `unknown` with a reason - and the shell's **DAH > Check for Updates...** opens the release page or shows that sentence. The self-replacing install is deliberately not shipped: the repository is private (an unauthenticated feed answers 404, verified) and the app is unsigned (DEC-006), so a payload cannot be signature-verified. `tauri-plugin-updater` slots in when signing does, and the check it would consume is what this task built. Every failure degrades to `unknown` with a reason rather than a silent `current`, because "could not check" and "is up to date" are different statements | The release pipeline now publishes a build per tag, but the installed app has no way to know. Genuinely useful to one user across machines, and cheap now that releases exist | P6 Distribution |

Deferred (not dropped): cloud storage and sync, team collaboration, warehouse
connectors (Postgres/Snowflake/BigQuery/Databricks), enterprise governance.
Each is listed in the roadmap as a P6 capability; none pays for itself at a
user count of one, and the architecture is deliberately not shaped around
them - the spec's own instruction is that they "should be allowed without
making them MVP dependencies."


## P7 Product Modes — entry checklist (1 of 4 done)

P6 closed the roadmap's own ladder: P0 through P6 are all delivered, and the
scale half of the roadmap's P6 list (cloud, collaboration, warehouse
connectors, governance) stays deferred at a user count of one. What is left is
not more infrastructure - it is product. The master specification defines three
modes; ANALYZE is the one that exists and the other two are the checklist,
ordered by what the one user gains first.

| # | Capability | Why now | Roadmap section |
|---|-----------|---------|-----------------|
| 1 | **EVALUATE mode** — **DONE (P7-EVAL-001)**: `POST /cases/{id}/datasets/{id}/evaluate` takes submitted code and the claim it was offered to support, runs the code through the existing run engine under the same read-only gate, row cap and hard sandbox, and answers all nine axes (question, data, quality, method, calculation, evidence, claim, visualization, limitations) with pass / concern / fail verdicts and sentences - never a score. A claim quoting a magnitude the run does not contain fails on Evidence; a column the dataset lacks fails on Data; an unordered ranking is flagged on Method; a non-reproducing artifact fails on Calculation. 22 tests, all three gates green | The one capability DAH uniquely owns and the one no notebook provides. Most of the machinery already exists - read-only execution, deep profiling, rerun validation, the evidence graph and the honesty budgets - so the work is a new *frame* over validated primitives, and it is the frame that separates DAH from a notebook. It also gives the P6 agent's own output something to be audited against, which is why it precedes multi-agent work | Product mode: EVALUATE |
| 2 | **Close the web-shell gap** — **DONE**: eight surfaces delivered - EVALUATE (**P7-SHELL-002**), the agent (**P7-SHELL-003**), case management (**P7-SHELL-004**, rename inline / duplicate / a two-click delete), templates (**P7-SHELL-005**, promote from the workspace with an optional name, list with a shape summary, start a case, retire), cross-case memory (**P7-SHELL-006**, a cited prior case shown as a button that opens it), EDA (**P7-SHELL-007**, segment / correlate / distribute as one panel over the profile) and the evidence graph (**P7-SHELL-008**, each claim with the path it rests on, orphans flagged, every derivation as a sentence) and case history (**P7-SHELL-009**, every event in the order it happened, the counts as one sentence). `/schema-version` and `/updates/latest` stay endpoint-only by design: both are operational, not analytical - `/updates/latest` already has the **Check for Updates...** menu item, and `/schema-version` answers a question a support conversation asks, not a workflow | The core can already do all of it and a user can reach none of it. This is the distance between "works" and "usable", and it is the cheapest large win left - no new endpoints, no new contracts, only surfaces over the ones that exist | P7 UX |
| 3 | **LEARN mode** — **DONE**: the core (**P7-LEARN-001**) answers `GET /cases/{id}/learn` with the spec's four phases (why, what, how, validate) over the workflow's own seven stages, every stage in exactly one phase, each phase carrying what it *teaches* and the question a learner answers before leaving it, at most one phase current, nothing stored and nothing executed. The surface (**P7-SHELL-010**) walks it as the **Learn this case** panel: each phase's purpose, the question that tests it, the stages as the actions that close them, and one phase and action to work on now - and a finished walk says the trust loop closed, not that the answer is right. 9 server tests (three gates green) + 6 web tests | A sequencing and presentation layer over P3-FLOW-004 rather than new machinery, which is why it is third rather than first - the machinery all exists; the work is to sequence it as teaching | Product mode: LEARN |
| 4 | **Multi-agent workflows** — **core DONE (P7-AGENT-001)**: `/cases/{id}/agents/{role}` answers the same four verbs the single driver answers, for an `analyst` role (today's decision procedure, and the legacy `/agent` family) and a new `reviewer` role that derives the case's first unaudited finding and proposes the EVALUATE audit of the run that backs it - claim from the finding, code from the run, verdict through the same evaluate endpoint a human audit uses. Orchestration, not autonomy: one shared approval gate, a GET that never proposes, a role's approval never authorising the other's (409), a failing verdict recorded beside the finding rather than folded into its validation_status. `agent_steps` carries the role (migration 9) and the export round trip with it; 13 tests, three gates green. The **surface** is built too (**P7-SHELL-011**): a second agent panel beside
  the analyst's - both loading read-only, both proposing on request, one component
  with two sets of wording so two panels on one page stay distinguishable, and the
  reviewer placed after the findings it audits. 5 web tests (78 total), web build
  and desktop bundle green. Nothing on the checklist remains but the release | Only after EVALUATE, which is the audit layer an agent's own output has to survive. Without it, more agents means more unexamined output | P6 Agentic Analysis (continued) |

## P8 Analytical Contract — entry checklist (COMPLETE, 10 of 10)

The last phase, and the one the PRD's own rule ordered: *"DAH should sacrifice
convenience before it sacrifices analytical trust."* P7 delivered the product
modes; P8 closed the PRD's Level 1 breadth gaps (`docs/PRD & UX Conformance
Evaluation.md`) and replaced prose thresholds with measured numbers. The gap
analysis named nine gaps; the checklist answers each, and a tenth item traces
them.

| # | Capability | What landed | Closes |
|---|-----------|-------------|--------|
| 1 | **The case's context object** — DONE (**P8-CONTEXT-001**): purpose, sub-questions, hypotheses and constraints, persisted (schema v10) and read by the planner, so a plan is generated from stated intent rather than a question string | AT-03, AT-10 |
| 2 | **Quality beyond missingness** — DONE (**P8-QUALITY-002**): five new defect classes in the one-scan profile (invalid types, inconsistent categories, date gaps, extreme values, insufficient coverage), each with an impact sentence | AT-08, AT-09 |
| 3 | **Validation, 3 checks to 9 dimensions** — DONE (**P8-VALID-003**): question, data, quality, method, calculation, evidence, assumptions, alternatives, causality - each a check with a sentence, never a score | AT-17 |
| 4 | **The causal-language guard** — DONE (**P8-CAUSAL-004**): an unsupported causal claim is refused, not merely commented on; a 50-case corpus measures 100% on all three of AT-18's thresholds | AT-18 |
| 5 | **The analytical golden suite** — DONE (**P8-GOLDEN-005**): three fixtures, 21 reference calculations over all ten of AT-40's shapes, each expectation verified two ways before the engine ran; AT-40's match rate and AT-01's completion rate are measured numbers | AT-40, AT-01 |
| 6 | **The orientation spine** — DONE (**P8-SHELL-006**): the workflow rail, the case overview and the three-zone workspace; AT-33's seven questions answerable from the rendered workspace | AT-33..35, UX §5/7/8/45 |
| 7 | **Question refinement** — DONE (**P8-REFINE-007**): a sharpening grounded in the profile's measured columns and ranges, with the three paths (accept / edit / keep) and the original preserved on every one; 50 cases measure AT-04's four thresholds | AT-04 |
| 8 | **The decision view** — DONE (**P8-DECISION-008**): the loop's exit. The verdict is persisted (all nine checks, not only the status), the view reads it without executing anything, the implications are the view's only write, and the export carries both | UX 46, AT-43 |
| 9 | **The measurement layer** — DONE (**P8-MEASURE-009**): one runner folds five measurements into a report with a verdict per acceptance test and exits non-zero when one does not hold. AT-38 core 93.9% / analytical 92.9% / evidence 92.4%; AT-28 p95 223ms; AT-29 p95 1.5s; AT-46 at the envelope; AT-45 declared and enforced; AT-37 0 critical / 0 high | AT-27..30, 32, 37, 38, 45, 46 |
| 10 | **The requirement-traceability matrix** — DONE (**P8-TRACE-010**): the PRD's own section 59 control artifact, as code. 48 rows carry every acceptance threshold from the PRD through the UX surface, the implementation and the test to the threshold that says it holds, and one runner resolves every cell against the repository as it stands - a renamed symbol, a deleted test, a moved section or a red report fails the gate rather than reading as a claim. AT-48: 15/15 P0 (100%), 33/33 P1 (>= 95%) | AT-48 |

**What the phase leaves behind:** every PRD threshold is now either a measured
number with a committed report behind it or a threshold asserted by a named
test, and the matrix that says which is itself gated. Two bugs the phase's
measurement exposed, each fixed with its own tests: profiling re-parsed the CSV
once per bounded lookup (12.5s over a 5s target, now 1.7s with one
materialisation), and the coverage counter's denominator counted
function-signature lines the interpreter never reports.

**Releases:** v0.3.0 shipped the phase, and v0.3.1 re-masked the app icon to the
standard macOS squircle (the icon had been a full-bleed square with 60px
corners, so it rendered as a tile rather than a native Ventura icon) and v0.3.2
scaled its bar-chart artwork from 68% of the canvas to 52%, centred, after the
squircle alone still read as oversized. With CI's billing still suspended the artifacts
are built and published locally from the same steps `release.yml` runs, as
v0.2.0's were. After that the roadmap's remaining ladder - cloud,
collaboration, warehouse connectors, governance - stays deferred at a user
count of one, and the conformance evaluation's deliberately-not-built list
(the Analysis Canvas, the command palette, the Knowledge nav item) is explicit
deferral, not backlog.
