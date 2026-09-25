## Next action

**FIX-TIMEOUT-006 (W-014) DONE.** The assistant slices no longer wait a
hardcoded thirty seconds and then silently answer as the other engine. Six
call sites carried three different numbers - `interpreter.py`,
`drafter.py`, `generator.py` and `assistant.py` at `30.0`, `planner.py` and
`refine.py` at `60.0` - and none was configurable, so the interpret and draft
endpoints timed out while the planner at twice the budget finished, and the
shell showed "Working..." for the whole wait and then `by deterministic`,
which never says the engine the analyst configured had failed.

One value now: `server/app/timeouts.py` exports `LLM_TIMEOUT_SECONDS`
(`DAH_LLM_TIMEOUT_SECONDS`, default 120, non-numeric and non-positive values
ignored with a warning), and every adapter posts it. The fallback is announced
rather than labelled: the six modules gained `SOURCE_DETERMINISTIC_FALLBACK`
(`"deterministic fallback"`) and `source_sentence`, and the web panels -
interpret, draft, chat, plan, generate-code, agent proposal, refinement -
render `web/src/sourceLabel.ts`, so a fallback reads "The LLM was unavailable,
so a deterministic ... answered in its place" where the source label sat.

**Gates:** 723 server (+24 in test_llm_adapters.py), 140 web (+2), build ok,
golden 21/21, e2e all steps, refine AT-04, measure 9/9, trace 48/48.

A scope decision worth carrying: announcing the fallback by widening the
`source` vocabulary rather than adding a field keeps every stored artifact
readable - the export, the evidence graph and the timeline all carry `source`
as a string, and a new field would have made every one of them learn a new
shape for one panel's sentence. The web suite's text assertions took the
vocabulary change without a single `className` or test-structure edit, which
is the P9 restyle-safety property the tests were written for.

**Next, in priority order:**

1. **Tag v0.3.3 DONE** - tagged on `30db6e9`, published as a flagged
   pre-release with the ditto zip and its sha256. The packaged core answers
   `current: 0.3.3` and the `.app`'s version string is 0.3.3; CI's billing
   is still suspended, so the build and publish were local.
2. **Then FIX-REFINE-007 (W-009)** - the refinement's rationale and grounds
   are returned by the API and rendered by neither; the "Why these changes"
   heading sits empty. Contract in `ai/TASKS.md`; `RefinePanel.tsx` only.
3. **Then FIX-PROFILE-008 (W-008)**, **FIX-UPDATES-009 (W-005)** and
   **FIX-VERSION-010 (W-001)**, order free. FIX-PLAN-003 / FIX-CHART-004 /
   FIX-PYTHON-005 precede none of these in the table but FIX-PLAN-003 is the
   next of them in priority.
4. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,501 lines into `web/src/panels/`), F2 the surfaces
   (closing W-011, W-016, W-013, W-009, W-017, W-018), F3 motion (respecting
   `prefers-reduced-motion`), F4 the chart surface and a re-walk.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
