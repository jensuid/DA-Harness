## Next action
**P8-DECISION-008 is DONE**: the loop has an exit. A validated finding used to be
the last thing the product did with itself - the verdict was computed, shown and
discarded, only the status surviving on the finding, and nothing closing over
what the loop had established. Two changes fix that. The verdict is now kept
(all nine checks, not only the status), so a decision is read without re-running
a single query and a reopened case shows what validation found; and a decision
view assembles it - the question, the findings validation stood behind with
their caveats and the checks that did not pass (a sentence each, never a score,
per UX 44), the claims still open with the reason each is unresolved, and the
implications the analyst writes.

The implications are the view's only write and the one thing in it a human
authors - nothing proposes them and nothing derives them, because a tool that
drafts the action to take is a tool making the decision. A malformed entry is a
400 naming the first one to fix. The loop's closure is the core's own value,
read from `workflow.case_progress` rather than restated, so the decision cannot
say the loop is open while the rail says it is closed - the same
one-definition discipline the rail itself used against the stage derivation.
The decision travels: the export carries the verdicts and the implications, the
round trip restores both with fresh ids, the duplicate carries them, the delete
removes them, and the timeline gains two events (the validation itself, now
that it has a timestamp of its own - AT-44 names it among its minimum events -
and the decision). Schema v12 -> v13, two tables, one in-place migration.

The shell gained the panel and, with it, the case's export, which existed as an
endpoint and had no surface in the product at all - its natural home is the
decision it sits beside, per UX 48's flow ending at Decision Support -> Export.

**Gates:** 548 server (+30), 116 web (+10), build green, 28/28 e2e, the golden
suite still 21/21 on both thresholds, AT-04's four still holding.

### What is next, in priority order

- **P8-MEASURE-009** - the measurement layer (AT-27..30/32/37/38/45/46):
  coverage, perf, a11y, deps and the data-size envelope. Mechanical now that
  two measured suites exist to borrow the pattern from.
- **P8-TRACE-010** - the traceability matrix (AT-48); last, it traces what
  1-9 delivered.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each is
in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`; the reasoning and
the bugs found are in `ai/HANDOFF-ARCHIVE.md`.

- **P8-DECISION-008** - the decision view (UX 46, AT-43); the persisted
  verdict, the read-only view, the implications as the only write, and the
  export that carries it.
- **P8-REFINE-007** - question refinement (AT-04); the deterministic
  engine, the LLM gate, the three paths, and the 50-case measurement.
- **P8-SHELL-006** - the orientation spine; the rail, the case overview and the
  three-zone workspace, and the three render gaps the walkthrough found.
- **P8-GOLDEN-005** - the analytical golden suite; AT-40's reference match rate
  and AT-01's workflow-completion rate are now measured numbers, not claims.
- **P8-CAUSAL-004** - the causal-language guard (AT-18); causality is a hard
  dimension, a 50-case corpus measures 100% on its three thresholds.
- **P8-VALID-003** - validation across the PRD's nine dimensions (AT-17).
- **P8-QUALITY-002** - quality detection beyond missingness (AT-08/AT-09).
- **P8-CONTEXT-001** - a case carries purpose, sub-questions, hypotheses and
  constraints (AT-03).
- **v0.2.0** - released and published (tag on `ec819fc`); CI's billing is
  suspended, so artifacts were built and uploaded locally.
