## Next action
**All ten phases are complete and v0.3.2 is published.** P0 through P8 are
DONE; the last task (P8-TRACE-010) made the PRD's section 59 control artifact
code, and the three releases after it re-cut the app icon - v0.3.1 rounded the
full-bleed 60px-corner tile to the standard Ventura squircle, v0.3.2 scaled the
bar-chart artwork from 68% of the canvas to 52% and centred it. The tree is
green: 686 server, 138 web, 28/28 e2e, the measurement layer 9/9, the matrix
48/48.

There is no open task. What a next session inherits is the **open follow-up
list** in `ai/TASKS.md`, which is where to look first - it carries the
packaged-core version gap (`/updates/latest` answers `current: unknown`,
because the PyInstaller bundle sees neither the distribution metadata nor
`pyproject.toml`), the DMG bundling's dependence on a local `create-dmg` that
is not the bundler Tauri expects, the icon proportion still chosen blind
(52%; the source is the committed `icon.png`, and `ai/TASKS.md`'s carried
follow-ups carry the exact recipe to re-cut it), and the `web/src/CaseWorkspace.test.tsx` refinement describe that
still inherits the previous test's persistence.

**Gates:** 686 server, 138 web, build green, 28/28 e2e, golden 21/21, AT-04's
four thresholds, measurement 9/9, matrix 48/48. Two environmental notes carry:
CI's billing is suspended, so nothing since `c73118c` has run in CI and every
release artifact was built locally; and the Ventura floor is documented but no
longer CI-enforced (DEC-005).

### What is next, in priority order

- **Fix the packaged core's version** so `/updates/latest` can compare: carry
  the version into the PyInstaller bundle. It is the one open defect that
  touches a user-visible promise (the Check for Updates menu item), present
  since v0.2.0.
- **Restore CI** at GitHub Settings > Billing & plans, then re-run the suites
  against `v0.3.2`; nothing since `c73118c` has been verified by CI.
- **Then extension**, not before: the roadmap's scale ladder (cloud,
  collaboration, warehouse connectors, governance) is deferred at a user count
  of one, and the deliberately-not-built list in `docs/PRD & UX Conformance
  Evaluation.md` (the Analysis Canvas, the command palette, the Knowledge nav)
  is explicit deferral, not backlog - pick from it deliberately.

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
