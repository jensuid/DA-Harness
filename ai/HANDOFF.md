## Next action

**FIX-PLAN-003 (W-011) DONE.** The orientation rail names "Generate an analysis
plan" and nothing in the shell performed it. `PlanPanel` read a plan and, when
there was none, told the analyst to generate one - with no control that does;
`POST .../plan` existed and answered 201 while the shell never called it, so
the plan stage was only finishable from a terminal.

The empty state's own sentence now has the control that performs it. The
button POSTs the endpoint that owns the write, labels itself while the
planner works, and on success renders the plan in place and calls the
workspace's reload - so the rail's stage, the progress counts and the panel
move together, because the plan is what makes the rail's next action
legible. A refusal shows the endpoint's own reason as a sentence and the
offer stays; a case that has already planned shows its plan and offers
nothing.

One thing the first test run caught and fixed: the generation's error shared
the read's `error` state, and the empty state rendered that only in its
non-missing branch - so a 400 in the missing branch was swallowed and the
panel stayed silent, exactly the failure the fix exists to remove. The two
are separate states now (`generateError`), because they are never both live:
the control lives where the read answered 404, and a 404 is not the reason a
generation failed.

**Gates:** 727 server (unchanged), web 167 (+4), tsc clean, build ok,
e2e 28/28, trace 48/48.

**Next, in priority order:**

1. **FIX-CHART-004 (W-016)** - a chart is an evidence artifact the core
   renders, stores and exports, and the shell cannot produce one. The runs
   panel runs a query and the evidence graph counts the charts, but between
   them there is no control that asks for one and no surface that shows it;
   every chart is reachable only through its file path. `web/src/api.ts`
   gains a chart helper and `RunRow` gains the control plus the surface
   (an inline SVG for the default format, a link for the others). Contract
   in `ai/TASKS.md`.
2. **FIX-PYTHON-005 (W-016)** - the python run surface, split from the chart
   because the two share no code but the panel they land in.
3. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,501 lines into `web/src/panels/`), F2 the surfaces
   (closing what remains of W-011, W-016, W-013, W-017, W-018), F3 motion
   (respecting `prefers-reduced-motion`), F4 the chart surface and a re-walk.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
