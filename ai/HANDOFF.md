## Next action

**FIX-VERSION-010 (W-001) DONE.** A dev checkout answered `current: 0.1.0` at
`/updates/latest` - four releases wrong, and a wrong number is believed where
an absent one is questioned. `current_version` read the editable install's
stale `dah_server-0.1.0.dist-info` before the pyproject beside the source the
checkout was actually running.

The order is now stamp > pyproject > metadata. The stamp stays first because
it was read from pyproject at build time (FIX-VERSION-001's packaged path is
unchanged, and a test now pins it against both other sources). The metadata is
demoted, not discarded: an installed wheel with no pyproject beside the source
still answers, which is the case the metadata was right for. A disagreement is
not papered over - when both answer and disagree the source wins and the two
numbers plus the reason land in the log at WARNING, so a stale install is
visible rather than silently believed. `_read_pyproject_version` and the new
`_installed_version` also treat `0.0.0` as "no answer", a placeholder a build
never replaced being no more a version in the source than in the metadata.
This checkout now answers `current: 0.3.3`.

**Gates:** 727 server (+4), web 163 (unchanged, server-only fix) green at the
second run, tsc clean, build ok, e2e 28/28, golden 21/21, refine AT-04,
measure 9/9, trace 48/48.

**W-001 closes, and with it the walk-test's last MAJOR finding:** all eight
WALK-E2E-001 majors (W-015, W-011 twice, W-014, W-009, W-008, W-005, W-001)
now have their fixes committed.

**Next, in priority order:**

1. **FIX-PLAN-003 (W-011)** - the rail names "Generate an analysis plan", the
   plan panel's empty state tells the analyst to generate one, and no control
   performs it; `POST .../plan` exists and answers 201 while
   `grep -rn "POST.*plan" web/src` is empty, so the stage is only finishable
   from a terminal. PlanPanel gains the control, `web/src/api.ts` a POST
   helper. Contract in `ai/TASKS.md`.
2. **FIX-CHART-004 / FIX-PYTHON-005 (W-016)** - the chart and the python run
   surfaces, the same class of gap; split because they share no code but the
   panel they land in.
3. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,501 lines into `web/src/panels/`), F2 the surfaces
   (closing W-011, W-016, W-013, W-017, W-018), F3 motion (respecting
   `prefers-reduced-motion`), F4 the chart surface and a re-walk.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **FIX-VERSION-010** - a dev checkout answers its pyproject's version, not
  the editable install's stale 0.1.0; stamp > pyproject > metadata, the
  metadata demoted not discarded, and a disagreement logged rather than
  silently believed. Closes the walk-test's last MAJOR finding.
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
