## Next action
**P8-MEASURE-009 is DONE**: the PRD's thresholds were prose, and nine of them
are numbers now. One runner folds five measurements into a report with a
verdict per acceptance test and exits non-zero when one does not hold -
`server/.venv/bin/python verification/measure/verify_measure.py`, 9/9 PASS.

Measured: AT-38 is the suite itself under a `sys.monitoring` line counter
(core 93.9%, analytical 92.9%, evidence 92.4%, all above the PRD's targets);
AT-28 an opening p95 of 223ms against 2s over the heaviest case in the
envelope; AT-29 a profiling p95 of 1.5s against 5s over a generated 50k-row
benchmark; AT-46 a case built at the boundary - a hundred multi-dataset runs,
two hundred findings, twelve hundred evidence edges - with every surface a
reopened case offers answering in budget, export round trip included; AT-45
declared with the PRD's numbers and refused at each limit; AT-37 scanned
against OSV, 0 critical / 0 high over 22 packages. AT-27, AT-30 and AT-32 are
asserted in the web suite and the report says where the number lives rather
than inventing one - jsdom is not a browser.

Three findings the measurement made, each fixed with its own tests. Profiling
a 50k-row dataset took 12.5s against AT-29's 5s, because each of the profile's
dozen bounded lookups re-parsed the CSV; one materialisation into a temp table
gives every later query an in-memory table and the same profile takes 1.7s,
with no measured result changed. The counter's denominator counted
function-signature lines the interpreter never reports, so coverage read lower
than it was - the exclusion is AST-derived and the numerator is intersected
with the executable set. And the guards `python_exec` enforces in the child
were unreachable by measurement, so eighteen tests now exercise them in the
process that measures them - which is what lifted the evidence group to its
target, and is worth more than relying on the child to reach them.

**Gates:** 644 server (+44: 26 measurement, 18 guards), 138 web, build green,
28/28 e2e, the golden suite still 21/21 and AT-04's four still holding.

### What is next, in priority order

- **P8-TRACE-010** - the traceability matrix (AT-48); last, because it traces
  what 1-9 delivered. Every AT now has a number for it to point at.

## Recent completions


The last tasks to land, newest first. The contract and done-record for each is
in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`; the reasoning and
the bugs found are in `ai/HANDOFF-ARCHIVE.md`.

- **P8-MEASURE-009** - the measurement layer (AT-27..30/32/37/38/45/46); the runner that folds five measurements into one report, the profiling
  cost it found and fixed, and the counter's corrected denominator.
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
