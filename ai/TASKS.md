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
| P6-MIGRATE-004 | Maintainability (versioned migration path) | DONE | 13 tests in test_migrations.py; P2/P3/P4 gates PASS |
| P6-UPDATE-005 | Distribution (update check) | DONE | 21 tests in test_updates.py + 7 Rust tests; P2/P3/P4 gates PASS |

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


Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
### P7-AGENT-001 contract

```
TASK ID: P7-AGENT-001
MILESTONE: P7 Product Modes
CAPABILITY: P6 Agentic Analysis (continued) - multi-agent workflows
GOAL: A case can be worked by more than one agent, each with a role of its own,
      and the roles disagree in the case's own audit trail rather than in
      private. The single driver (P6-AGENT-002) proposes the analysis loop one
      human-approved step at a time; nothing examines what it produced. This
      task adds a second role whose entire method is EVALUATE (P7-EVAL-001) -
      the reason the roadmap gated multi-agent work behind it - so an
      agent-proposed finding is audited by a different agent with a different
      objective, and a verdict that fails the analyst's own finding is recorded
      where a reviewer can read it.

CONTEXT: the spec names "autonomous multi-agent system" as an explicit
         non-goal and "Human control" in its Never-lose list, while "Agent
         orchestration" sits on the LEVEL 5 -> 6 ladder. So this is
         orchestration, not autonomy: every role shares the one approval gate
         the existing driver already uses, every write still runs through the
         endpoint that owns it, and a page refresh commits nothing. What is new
         is specialisation and a second point of view, not self-direction.

INPUTS: the case's artifacts - for the analyst, exactly what it reads today;
        for the reviewer, the findings and the runs that back them, plus the
        evaluations already recorded (an audit matching a finding's run and its
        statement means that finding has been examined).
RELEVANT FILES: server/app/agent.py, server/app/db.py, server/app/main.py,
                server/app/models.py, server/tests/test_multi_agent.py (new),
                server/tests/test_migrations.py (a case for the new migration)
REQUIRED CHANGE:
  - server/app/db.py: migration 9 - `agent_steps` gains a `role` column
    defaulting to `analyst`, so every step recorded before this task reads as
    the analyst role and the legacy paths keep their meaning. LATEST_SCHEMA_VERSION
    becomes 9.
  - server/app/agent.py: the driver becomes role-aware - the pending step, the
    history, the proposals and the settle/decide path all take a role. The
    `analyst` role is today's decision procedure, unchanged. The `reviewer`
    role is new and small: derive the case's first finding whose (run, claim)
    has no evaluation, and propose an `evaluate` step carrying the run's own
    code and the finding's statement. Every finding audited means no step, and
    an end row names what the reviewer is waiting for rather than falling
    silent.
  - server/app/main.py: `/cases/{case_id}/agents/{role}` with the same four
    verbs the single driver answers (GET state, POST propose, approve, reject),
    and the `evaluate` step kind applied through the existing evaluate
    endpoint - the reviewer has no write path of its own, exactly as the
    analyst has none. The existing `/cases/{case_id}/agent` family stays, as
    the analyst role, so the shell's agent panel and every existing test keep
    working. An unknown role is a 400 naming the roles that exist.
  - server/app/models.py: `AgentState` carries the role; `AgentStep` already
    exists.
  - The case export and the duplicate path carry the role with the steps they
    copy, so an agent-run case round-trips with its roles intact.
NON-GOALS: autonomy (the spec's own non-goal - a role never writes without an
           approval, and a GET never proposes), inter-agent messages or
           negotiation (two agents do not talk to each other; each addresses
           the case, and the case's rows are the shared state), resolving a
           disagreement (a reviewer's failing verdict is recorded beside the
           analyst's finding, not folded into the finding's own validation
           status - rerun support and an audit are two honest notions, and
           conflating them would make both say less), new analysis capability
           (the reviewer audits; it does not discover), the shell surface (its
           own task, P7-SHELL-011).
CONSTRAINTS: no new dependency; at most one pending step per role, and an
             approval that is not that role's live step is a 409; the
             reviewer's audits land in the evaluations table through the same
             endpoint a human audit uses; the existing agent tests stay green
             unchanged.
ACCEPTANCE CRITERIA:
- [x] a case carries agents in two roles, each with its own pending step and
      audit trail
- [x] the analyst role behaves exactly as P6-AGENT-002's driver did
- [x] the reviewer proposes an evaluate step over an unaudited finding, and
      approving it records an evaluation whose claim is the finding's
      statement and whose code is the run's
- [x] a finding that has been audited is not re-proposed
- [x] an approval for one role is not the other's; a mismatch answers 409 with
      that role's own pending step
- [x] an unknown role answers 400 naming the roles that exist
- [x] a reviewer's failing verdict does not touch the finding's
      validation_status
- [x] the legacy /agent paths are the analyst role and keep working
- [x] a store from before this task upgrades and its existing steps read as
      analyst
- [x] the export round trip carries the role
- [x] the endpoint family writes only through approvals; the server suite and
      the three gates stay green
TESTS: server/tests/test_multi_agent.py - the two roles side by side, the
       reviewer's audit and its idempotence, the 409 naming the right role's
       step, the unknown-role 400, the failing verdict leaving the finding's
       own status alone, the legacy paths as the analyst role, and the export
       round trip carrying the role; test_migrations.py gains a case for
       migration 9.
VERIFICATION: cd server && .venv/bin/python -m pytest PASS (367 + N); the P2,
              P3 and P4 gates PASS. The web suite is untouched by this change
              and stays at 73.
STATE UPDATE: mark P7-AGENT-001 done on pass; ROADMAP item 4 records the core
              of multi-agent workflows as delivered, with the surface still to
              build.

```

TASK: P7-AGENT-001 - multi-agent workflows, roles over one case (core)
ID: P7-AGENT-001
PRIORITY: medium
STATUS: DONE
SUMMARY: A case can be worked by more than one agent, each with a role of its
         own - and the roles disagree in the case's own audit trail rather than
         in private. The single driver (P6-AGENT-002) proposes the analysis
         loop one human-approved step at a time; nothing examined what it
         produced. This task adds a second role whose entire method is
         EVALUATE, so an agent-proposed finding is audited by a different agent
         with a different objective, and a verdict that fails the analyst's own
         finding is recorded where a reviewer can read it.

The design turns on a distinction the spec itself draws: an *autonomous*
multi-agent system is an explicit non-goal, and "Human control" is in the
Never-lose list, while "Agent orchestration" is on the LEVEL 5 -> 6 ladder. So
this is orchestration, not autonomy. Every role shares the one approval gate
the existing driver already uses, every write still runs through the endpoint
that owns it, and a GET never proposes - a page refresh commits nothing no
matter how many roles are open.

Two roles, one case:

- **analyst** - the existing decision procedure, unchanged: profile, plan,
  analyze, interpret, accept, chart, validate.
- **reviewer** - deliberately small, and deliberately not the analyst's. It
  derives the case's first finding whose (code, claim) has no evaluation and
  proposes the EVALUATE audit of the run that backs it: the claim is the
  finding's own statement, the code is the run's own query. The reviewer
  invents neither, discovers nothing, and writes nothing of its own - the audit
  goes through the same evaluate endpoint a human audit uses, and the verdict
  lands in the evaluations table beside every other audit.

Three things that had to be right rather than present:

- **Idempotence keyed on code and claim, not run.** EVALUATE stores the
  artifact as a run of its own, so an evaluation's run_id is the audit's
  artifact, not the finding's - joining on it would never match, and the
  reviewer would re-audit forever. The (code, claim) pair is exactly what the
  reviewer proposed, so matching it is a projection: an audit cannot be
  repeated without an evaluation existing, and a finding cannot be skipped by
  forgetting.
- **Two honest notions stay distinct.** A failing audit is recorded beside the
  finding; it does not touch the finding's own validation_status, which is
  about rerun support. Folding them together would make both say less.
- **One role's approval never authorises another role's write.** A mismatch is
  a 409 naming that role's own pending step, so two open panels cannot collide
  into a double write.

NON-GOALS held: autonomy (a role never writes without an approval), inter-agent
             messages or negotiation (the roles do not talk to each other; each
             addresses the case, and the case's rows are the shared state),
             resolving disagreement (a failing verdict is recorded, not folded
             in), new analysis capability (the reviewer audits; it does not
             discover), the shell surface (its own task, P7-SHELL-011).
CONSTRAINTS held: no new dependency; at most one pending step per role; the
             reviewer's audits land through the evaluate endpoint; the existing
             agent tests stayed green unchanged.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 12 in server/tests/test_multi_agent.py (server suite 367 -> 380, with one
       migration case) - the two roles side by side, the audit's claim and code
       being the finding's own, the recorded evaluation, idempotence, the
       no-findings reason, the cross-role 409, the unknown-role 400, the
       failing verdict leaving the finding's status alone, rejection writing
       nothing, the export round trip carrying the role, and the GET that never
       proposes. Plus test_migrations.py: a pre-roles store whose steps read as
       analyst.
VERIFICATION: cd server && .venv/bin/python -m pytest - 380 passed; the P2, P3
              and P4 gates each PASS (each re-ran the suite at 380). The web
              suite is untouched and stays at 73.
LESSON: most of the failures on the way to green were the migration's own
        bookkeeping - a changed INSERT column list here, a values tuple that
        kept its old length there, a SELECT that gained a WHERE column without
        gaining the SELECT column - each surfacing as "incorrect number of
        bindings" or a KeyError far from the site of the edit. The discipline
        that caught them was running the existing agent and export suites
        first, before writing a new test, because those suites already encode
        every write path and said exactly which statement was wrong. A schema
        change is not one edit; it is one edit per writer, and the writers are
        found by the tests, not by grep.


### P7-SHELL-010 contract

```
TASK ID: P7-SHELL-010
MILESTONE: P7 Product Modes
CAPABILITY: UX (LEARN mode's surface)
GOAL: A learner can open a case and be walked through the analytical process.
      P7-LEARN-001 ships `GET /cases/{id}/learn` - the four phases, each with
      what it teaches, the question a learner answers, and workflow's own
      action for the stage to do next - and none of it is reachable from the
      shell, so the mode exists as an endpoint and not as a product.

CONTEXT: the walk is a read-side projection over the artifact counts; the
         workspace already loads it per case. The endpoint answers 404 for an
         unknown case, which the workspace's own load reports at the top, and a
         done walk only ever claims the trust loop closed.

INPUTS: the walk, read read-only.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `LearnStage`, `LearnStep` and `LearnWalk` matching the
    core's models, and `getLearnWalk(caseId)` for the GET.
  - web/src/CaseWorkspace.tsx: a **Learn panel** beside the workflow panel it
    explains - the workflow says where the case stands, this says why each
    step of that exists and what a learner should be able to answer before
    leaving it. It loads with the workspace, read-only. Each phase renders
    its name, its status, what it is for, the question that tests
    understanding, and the stages it covers as the actions that close them
    (with workflow's own hints), so a learner reads what to do and why in one
    place. The panel names the single phase and action to work on now, the
    way the workflow panel names the next stage; a completed walk says the
    loop closed, and says it as the core does - the loop ran, not that the
    answer is right.
  - A 404 degrades to muted guidance rather than an alert, for the same
    reason as every other read-only panel: the workspace loads its own case
    on mount, so the failure is already reported at the top. Any other
    failure is the sentence in an alert.
NON-GOALS: scoring or assessing the learner (the core has no measure of
           understanding and the shell invents none), writing anything (the
           panel calls only the GET; the learner's work happens through the
           endpoints the stages name), a separate route or mode switch (the
           workspace is one page, and the walk is a sequencing and teaching
           layer over the panels already below it, not a second app),
           dataset-specific teaching content (the phases are the process; the
           specifics come from the profile and plan the learner reads).
CONSTRAINTS: the panel calls only the read-only GET and writes nothing; `tsc
             -b` passes; no new dependency; the existing workspace tests stay
             green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] the four phases render with their names and statuses
- [x] each phase shows what it is for, and the question that tests it
- [x] the stages render as the actions that close them, complete and incomplete
- [x] the panel names the one phase and action to work on now
- [x] a completed walk says the loop closed, without claiming the answer is
      right
- [x] an unknown case degrades to guidance rather than a duplicate alert
- [x] the panel writes nothing and reloads with the workspace
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the four phases of a fresh case with
       the first current and the next action named, the teaching (purpose and
       prompt per phase), the stage actions with their marks, a mid-walk case
       whose current phase is What, the completed walk's sentence, and the 404
       as guidance.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-010 done on pass; ROADMAP item 3 records LEARN
              mode as delivered in core and shell.

```

TASK: P7-SHELL-010 - LEARN mode in the web shell
ID: P7-SHELL-010
PRIORITY: medium
STATUS: DONE
SUMMARY: P7-LEARN-001 ships the guided walk - the four phases, each with what
         it teaches, the question a learner answers, and workflow's own action
         for the stage to do next - and none of it was reachable from the
         shell, so LEARN existed as an endpoint and not as a product.

A **Learn this case panel** now sits beside the workflow panel it explains: the
workflow says where the case stands, this says why each step of that exists and
what a learner should be able to answer before leaving it. It loads with the
workspace, read-only. Each phase renders its name and status, what it is for,
the question that tests understanding, and the stages it covers as the actions
that close them - with the workflow's own hints - so a learner reads what to do
and why in one place, and a complete stage is marked while an open one is not.

Two things carried from the core into the shell rather than reinvented:

- **One thing to do next, never two.** The core guarantees at most one current
  phase; the panel names that phase and its action as a single sentence, the
  way the workflow panel names the next stage. A completed walk does not offer
  one, because there is nothing to do.
- **Graduation is not a claim about the answer.** A finished walk says the loop
  closed - a finding was validated - and says it as the core does: the trust
  loop *ran*, not that the answer is right. A learner is not graduated on a
  stronger claim than the artifacts support.

NON-GOALS held: no scoring or assessment (the core has no measure of
             understanding and the shell invents none), no writes (the panel
             calls only the GET; the learner's work happens through the
             endpoints the stages name), no separate route or mode switch (the
             workspace is one page, and the walk is a sequencing and teaching
             layer over the panels already below it, not a second app), no
             dataset-specific teaching content.
CONSTRAINTS held: the panel calls only the read-only GET and writes nothing; no
             new endpoint and no new dependency; `tsc -b` passes; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 6 added to web/src/CaseWorkspace.test.tsx (web suite 67 -> 73) - the four
       phases with exactly one current and the next action named, the teaching
       per phase, the stage actions with their marks, a mid-walk case whose
       current phase is How, the completed walk's honest sentence, and a 404
       as guidance rather than an alert.
VERIFICATION: cd web && npm test - 73 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: three existing tests broke, and all three for the reason the workspace
        is one page. The ladder's stage rows are labelled with the workflow's
        own actions, so "attach a dataset" now names both the data panel's
        uploader and a stage row - and the uploader's test found two. Fixed by
        saying which panel the input is in, which is the accessible thing too.
        The other two were the same trap from the previous task come back: a
        phrase that spans a <strong> cannot be matched by text, because the
        matcher reads an element's own text nodes and not its descendants'. The
        "work on now" sentence is plain text now. And one failure was not a
        failure of its own test at all - the ambiguous-label test died midway
        and left a queued mock value behind, so the next test received a
        dataset id from the case before it. A test that fails can corrupt the
        one after it, which is why the fix belongs to the first one.
