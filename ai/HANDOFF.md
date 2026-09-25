## Next action

**FIX-UPDATES-009 (W-005) DONE.** The Check for Updates menu item is silent no
more. The handler asked the core and wrote the answer to stderr, so on this
private repository - where the feed always 404s - the item was permanently dead
while the core answered honestly. The delivery is added, not substituted: the
log line still writes, and the answer also reaches the window.

The shell owns the delivery because the shell is the only host with a menu bar,
and it delivers through the bundle's own surface - `tauri-plugin-dialog` is a
network-fetched plugin on Tauri 2 and the app is offline after install, so a
native dialog was not available without breaking DEC-001. `updates.rs` gained
`notice_script` (a `CustomEvent('dah-notice')` carrying the core's own JSON
body, so the window's vocabulary is the core's - an unreachable feed stays
"could not tell" rather than becoming the silent "up to date" P6-UPDATE-005
built the check to avoid) and `deliver_update_notice`, plus a
`check_for_update_with_body` that keeps the raw body beside the parsed answer.
`main.rs` logs first, then opens the release page for an `Available`, then
delivers. A body that is not JSON is re-serialised from the parsed answer,
because embedding it would throw a `SyntaxError` in the webview and silence the
item a second time - that case is a test. The bundle side is `web/src/shell.ts`
(`describeUpdate`, mirroring `update_summary`) and `web/src/NoticeLayer.tsx`,
mounted on all three screens, inert until a notice arrives, dismissable, and a
`role="status"` region. One include_str test pins the event name both sides
must agree on, which is the single thing a rename would silently break.

**Gates:** 723 server (unchanged), web 163 (+16), Rust 25 (+6), tsc clean,
build ok, e2e, golden 21/21, refine AT-04, trace 48/48.

**Next, in priority order:**

1. **FIX-VERSION-010 (W-001)** - a dev checkout answers `current: 0.1.0`
   because `server/app/updates.py` reads the stale installed metadata before
   the pyproject beside the source. FIX-VERSION-001's stamp stays first; the
   source moves ahead of the metadata. Contract in `ai/TASKS.md`.
2. **Then FIX-PLAN-003 / FIX-CHART-004 / FIX-PYTHON-005** - the rail names
   "Generate an analysis plan" and no control performs it; the chart and python
   run surfaces are the same class of gap.
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
