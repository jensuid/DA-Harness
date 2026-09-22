## Next action
**P8-GOLDEN-005 is DONE**: the trust machinery is measured. Three fixtures
(sales, spend, tickets) carry 21 reference calculations covering all ten of
AT-40's shapes; each golden value is computed twice before the engine is asked
- by hand, and by an independent Python path over the CSV, never DuckDB - and a
disagreement fails the suite, because a fixture the two paths disagree on is a
wrong fixture. Then a real server answers the same question over HTTP: 21/21
match (AT-40, threshold 100%). The same 21 journeys answer AT-01, because the
query a scripted run makes *is* the reference query - 21/21 complete the loop
over 3 datasets (thresholds 95%, 20 runs, 3 datasets). Both numbers are
asserted in test_golden.py, and a deliberately wrong expectation is caught by
the audit, so the measurement is known to be able to fail. The suite is offline
by construction: the runner fails the `plan` stage unless the planner answers
`source: "deterministic"`, so a completion rate above zero proves no LLM was
called. An `insufficient_evidence` verdict still counts complete - a finding
the evidence does not support is a finished analysis.

**Two real bugs the suite surfaced**, each fixed with its own test: grouping by
a date column handed a raw `datetime.date` to `json.dumps` and answered a 500
for a valid query (the profile already described a date as an ISO string; the
run path now agrees, and Decimals and bytes are covered by the same rule); and
the runner's health check raced the stdout pump thread for the server's
announcement, blocking forever on a `readline()` with no timeout.

**Gates:** 477 server (6 for this task: 5 fast data-layer tests plus the one
slow measurement), 86 web, build green, 25/25 e2e.

### What is next, in priority order

- **P8-SHELL-006** - the orientation spine (AT-33/34/35): the shell tells an
  analyst where they are in the loop and what the next action is.
- **P8-REFINE-007** - question refinement (AT-04), editing the context object
  P8-CONTEXT-001 built.
- **P8-DECISION-008** - the decision view (UX 46).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each is
in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`; the reasoning and
the bugs found are in `ai/HANDOFF-ARCHIVE.md`.

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
