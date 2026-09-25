## Next action

**FIX-PYTHON-005 (W-016) DONE.** The codegen panel generated SQL only and
posted to the SQL runs endpoint; a python run was reachable only by curl, so
the hard sandbox (P3-SEC-001) - the hardening the sandbox exists to prove -
was untested by anyone using the app. `grep -rn "runs/python" web/src` was
empty; the generator, the endpoint and its `PythonRunCreate` model already
existed.

The panel now offers an engine, and the choice is what it carries. A kind
selector (SQL the default, Python) picks the code `generateCode` is asked for
and persists across proposals in the same panel. `runPython` in
`web/src/api.ts` posts to the sandbox's own endpoint, and the run posts to the
endpoint matching the *proposal's* kind, not the selector's current value -
the code the analyst read is the code that executes, so a proposal the panel
is still showing cannot be sent to the other engine. A python run persists
exactly like a SQL one, so the runs panel, the evidence graph and the
validation are all shared. A sandbox refusal is the analyst's input: its 400
detail is the sentence the panel shows and the proposal stands to be fixed.

Two things the first test run caught: two radios named python and sql on the
same page - the EVAL panel's own kind-toggle - matched every `/python/i`
query, so the codegen radios carry their own aria-label and the audit test now
scopes its click to its own panel; and a multi-line script does not survive
`getByText`'s whitespace normalisation, so the `pre`'s own textContent is what
the assertion reads.

**Gates:** 727 server (unchanged), web 177 (+4), tsc clean, build ok,
e2e 28/28, golden both thresholds, refine AT-04, measure 9/9, trace 48/48.

**Next, in priority order:**

1. **P9, the UI/UX redesign** the user asked for: npm (CI hardcodes `npm ci`),
   light theme first, recharts on screen because the server's chart SVG bakes
   a white background and is static, while its layout engine and PNG export
   stay for the export path. Four phases, green at each: F1 the foundation
   (tailwind, shadcn, framer-motion, recharts, splitting `CaseWorkspace.tsx`'s
   2,900 lines into `web/src/panels/`), F2 the surfaces (closing what remains
   of W-013, W-017, W-018 - W-011 and W-016 are now closed), F3 motion
   (respecting `prefers-reduced-motion`), F4 the chart surface and a re-walk.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **FIX-PYTHON-005** - the python run surface: the codegen panel offers an
  engine, the proposal matches it, the run posts to the sandbox's own endpoint
  and its refusal is a sentence. Closes W-016.
- **FIX-CHART-004** - the chart surface: a run row renders a chart the core
  draws, sees it inline as the core's own SVG, the pickers offer only the
  run's columns, and the evidence count moves with it.
- **FIX-VERSION-010** - a dev checkout answers its pyproject's version, not
  the editable install's stale 0.1.0; stamp > pyproject > metadata, the
  metadata demoted not discarded, and a disagreement logged rather than
  silently believed. Closes the walk-test's last MAJOR finding.
- **FIX-PLAN-003** - the plan stage's missing button: the empty state's own
  sentence finally has the control that performs it, the plan renders in
  place, the rail and the counts reload with it, and an existing plan offers
  nothing.
- **FIX-UPDATES-009** - the Check for Updates item reaches the window: three
  statuses, each a visible answer, the log line still writing and the browser
  still opening for an available build.
- **FIX-PROFILE-008** - opening a case reads its profile instead of POSTing
  it (twice, under strict mode); the re-profile is now a control in the Data
  panel, and a dataset without a profile is offered rather than fabricated.
- **FIX-REFINE-007** - the refinement's rationale and grounds, already in the
  API, are shown under their own heading rather than collapsed in a
  `<details>` the analyst has to know to open; the accept keeps them visible.
- **FIX-TIMEOUT-006** - one configured LLM timeout (DAH_LLM_TIMEOUT_SECONDS,
  default 120) for all six assistant call sites, and a fallback announced as a
  sentence; v0.3.3 carries it.
- **FIX-VERSION-001** - the packaged core reports its own version; the spec
  stamps it from pyproject, `current_version` reads it first, and both
  packaged-core smokes assert it.
- **WALK-E2E-001** - the walk-test end-to-end; 19 findings (8 MAJOR), the
  report that prioritises them, and the list of what works that the fixes
  must not break.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
