## Next action
**FIX-VERSION-001 is DONE: the packaged core reports its own version.** Since
v0.2.0 a bundled core answered `current: unknown` at `/updates/latest`, so the
Check for Updates item could never compare - neither the installed metadata nor
`pyproject.toml` survives a one-file PyInstaller bundle, and PyInstaller ships
no stdlib `importlib.metadata` hook. `dah-core.spec` now reads the version from
pyproject with tomllib and stamps `dah-build-version.txt` into the bundle root,
where `current_version` finds it through `sys._MEIPASS` - ahead of installed
metadata, which goes stale when a version is bumped without reinstalling. A
version the spec cannot read aborts the build, and both packaged-core smokes
now assert the number, which is what makes the recurrence fail a build instead
of hiding for four releases. Verified against the binary `build_sidecar.sh`
produces: `current: 0.3.2`.

**Gates:** 694 server (+8 in test_updates.py), 138 web, build green, 28/28
e2e, golden green, refine green, measure 9/9, matrix 48/48 - plus the packaged
binary itself answering over real HTTP. CI's billing is still suspended, so
nothing since `c73118c` has run in CI; the smokes were exercised locally.

### What is next, in priority order

- **Tag the release that ships it** (v0.3.3): the fix is on master, but no
  published binary carries it - v0.2.0 through v0.3.2 still answer "unknown",
  and that cannot be repaired without rebuilding. The release procedure is
  unchanged; the new smoke step does the verification.
- **Restore CI** at GitHub Settings > Billing & plans, then re-run the suites
  against the tag; nothing since `c73118c` has been verified by CI.
- **Then extension**, not before: the roadmap's scale ladder (cloud,
  collaboration, warehouse connectors, governance) is deferred at a user count
  of one, and the deliberately-not-built list in `docs/PRD & UX Conformance
  Evaluation.md` (the Analysis Canvas, the command palette, the Knowledge nav)
  is explicit deferral, not backlog - pick from it deliberately.

## Recent completions


The last tasks to land, newest first. P8 is complete; a post-phase fix closes
the carried follow-up that touched a user-visible promise. The contract and
done-record for each task below is in `ai/TASKS.md` (rolling window) or
`ai/TASKS-ARCHIVE.md`.

- **FIX-VERSION-001** - the packaged core reports its own version; the spec
  stamps it from pyproject, `current_version` reads it first, and both
  packaged-core smokes assert it.
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
