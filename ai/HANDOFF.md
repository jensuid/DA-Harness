## Next action

**FIX-CHART-004 (W-016) DONE.** A chart is an evidence artifact the core
renders, stores and exports, and the shell could not produce one. The chart
endpoint answered 201 while `web/src` never called it - `grep -c chart
web/src/api.ts` was zero - so every chart was reachable only through its file
path and every PNG only through that.

The run row now holds the control and the surface. `web/src/api.ts` gained
`createChart`, `chartImageUrl` and `getChartImage`; `RunRow` gained a
`ChartPanel`. The control appears once the analyst has opened the run's rows,
because those columns are the renderer's input and are exactly what its
pickers offer - a column the run does not have is not among the choices, and
the measure defaults to a numeric column. A success POSTs the endpoint that
owns the write, fetches the SVG the core drew and renders it inline through
`dangerouslySetInnerHTML`: the shell draws what the core already drew rather
than re-rendering it, because a second renderer would be a second source of
truth for what the chart looks like. A PNG is a link to the persisted artifact
instead of a redrawn image. The workspace reloads with a chart, so the
evidence graph's count moves with the panel; a refusal shows the renderer's
own sentence and the control stands.

Two things the first test run caught: the control was offered before the rows
were read, which is before there is anything to draw from, so it now waits on
the result; and the surface was asserted as an img role, which jsdom does not
give an inline SVG - the assertion reads the element instead.

**Gates:** 727 server (unchanged), web 173 (+6), tsc clean, build ok,
e2e 28/28, trace 48/48.

**Next, in priority order:**

1. **FIX-PYTHON-005 (W-016)** - the other half. The codegen panel generates
   SQL only and posts to the SQL runs endpoint; a python run is only
   reachable by curl, so the hard sandbox (P3-SEC-001, the hardening the
   sandbox exists to prove) is untested by anyone using the app. The
   generator already supports kind 'python' and the endpoint and its
   `PythonRunCreate` model already exist; only the shell's request is
   missing. `web/src/api.ts` gains a python run helper and the codegen panel
   gains a kind, its proposal matching it. Contract in `ai/TASKS.md`.
2. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,800 lines into `web/src/panels/`), F2 the surfaces
   (closing what remains of W-013, W-017, W-018 - W-011 and W-016 are now
   closed), F3 motion (respecting `prefers-reduced-motion`), F4 the chart
   surface and a re-walk.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
