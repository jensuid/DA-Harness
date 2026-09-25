## Next action

**FIX-REFINE-007 (W-009) DONE.** The refinement's "Why these changes" no longer
hides behind a click. The panel rendered the API's `rationale` and `grounds`
inside a `<details>` that ships collapsed, and the walk-test clicked the
heading and saw nothing - the data was a curl away in
`walktest/evidence/refine-latest.json`, complete, and the panel had it. A
disclosure widget was the wrong primitive for the answer to the panel's own
question, so it is gone: `web/src/RefinePanel.tsx:185-209` now renders a
real `<h4>Why these changes</h4>`, the rationale under it, and the grounds as
a list, always visible. `web/src/index.css` gives the block the same left rule
and ground the proposals use, so it reads as the proposal's support rather
than another paragraph, and gains `.panel h4` because no panel had used one.

**Gates:** 723 server (no change), web 95/95 in the file and the suite's
143 (+3), tsc clean, build ok, e2e all steps, golden both thresholds, refine
AT-04, measure 9/9, trace 48/48.

One diagnosis worth carrying: the instinct was a styling bug, and the fix is
not one. A collapsed `<details>` shows its summary but nothing else, with no
affordance the panel announces; the heading read as inert text. Where a panel
asks "why" and the API answers, the answer is shown - a disclosure is for
detail the analyst may want to skip, and this is the reason they are being
asked to decide at all.

**Next, in priority order:**

1. **FIX-PROFILE-008 (W-008)** - the shell POSTs the profile endpoint on every
   case mount, so opening a case re-profiles and rewrites, and strict mode's
   double render makes it two writes. `web/src/CaseWorkspace.tsx:191` is the
   effect; contract in `ai/TASKS.md`.
2. **Then FIX-UPDATES-009 (W-005)** (Rust + the window's own message surface)
   and **FIX-VERSION-010 (W-001)** (`server/app/updates.py`'s resolution order
   reads the stale metadata before the pyproject beside the source), order
   free. **FIX-PLAN-003 / FIX-CHART-004 / FIX-PYTHON-005** precede none of
   these in the table but FIX-PLAN-003 is the next of them in priority.
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
