## Next action
**P8-TRACE-010 is DONE, and P8 with it.** The PRD's own control artifact
(section 59) is code rather than a document: forty-eight rows carry every
acceptance threshold from the PRD, through the UX surface, the implementation
and the test, to the threshold that says it holds. `verification/trace/
verify_trace.py` resolves every cell against the repository as it stands, so
a renamed symbol, a deleted test, a renumbered UX section, an uncommitted
report or a red one is a named failure instead of a claim that quietly stopped
being true. 48/48 rows PASS, and AT-48's own thresholds compute from that:
15/15 release-blocking requirements traceable (100%) and 33/33 of the rest
against a >= 95% target.

The requirement set is checked against the PRD's own headers, so an acceptance
threshold the PRD adds is a red gate until a row exists for it - and a row the
PRD no longer states is a phantom the gate rejects. Fifteen rows are P0 by the
PRD's section 53, each naming the release-blocking category it guards. The
matrix is honest about which rows are measured and which asserted: the measured
ones cite a runner and its committed report, the asserted ones name the suite.

**Gates:** 686 server (+42 in test_trace.py), 138 web, build green, 28/28 e2e,
golden 21/21, refinement's four thresholds, the measurement layer 9/9, and the
matrix 48/48.

### What is next, in priority order

- **Nothing is open.** P8 is complete (10 of 10) and **v0.3.0 is published**
  (`ab56541`, pre-release with its checksum): the phase's releases are v0.2.0
  and v0.3.0. The roadmap's remaining ladder - cloud, collaboration, warehouse
  connectors, governance - stays deferred at a user count of one, and the
  conformance evaluation's deliberately-not-built list is explicit deferral.
  Two environmental notes carry: CI's billing is still suspended, so nothing
  since `c73118c` has run in CI; and the Ventura floor is documented but no
  longer CI-enforced (DEC-005).

## Recent completions


The last tasks to land, newest first. P8 is complete; the matrix closes the
phase, and the contract and done-record for each task below is in
`ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **P8-TRACE-010** - the requirement-traceability matrix (AT-48); 48 rows,
  resolved rather than asserted, and the 42 tests that prove a broken row
  fails the gate.
- **P8-MEASURE-009** - the measurement layer (AT-27..30/32/37/38/45/46); the
  runner that folds five measurements into one report, the profiling cost it
  found and fixed, and the counter's corrected denominator.

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
