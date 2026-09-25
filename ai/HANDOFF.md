## Next action

**FIX-PROFILE-008 (W-008) DONE.** Opening a case no longer writes to it. The
mount effect called `profileDataset` - a POST - per attached dataset on every
visit, and strict mode's double render made it two, so a profile that already
existed was recomputed and rewritten, and the step the rail names as the
analyst's was being silently completed by the shell. The GET endpoint already
existed (`server/app/main.py:1654`, a 404 when nothing is stored), so the fix
is a new `getProfile` in `web/src/api.ts` and a one-word change at
`web/src/CaseWorkspace.tsx:196`: the mount reads. The POST moved to a control
in the Data panel - "Re-profile" beside a dataset that has a profile, "Profile
this dataset" for one that does not, replacing the "profiling…" placeholder
that was the shell finishing the step.

**Gates:** 723 server (no change), web 147 (+4), tsc clean, build ok.

A design note worth carrying: the contract's "a GET is preferred to a POST
when the endpoint can answer one" turned out to already be answered - the
read endpoint shipped in P2-DATA-007 and the write was the only thing the
shell ever called. The panel and the rail now agree about the profile stage
because the panel is no longer the thing that completes it; a read per mount
is correct and a write is not.

**Next, in priority order:**

1. **FIX-UPDATES-009 (W-005)** - the Check for Updates item performs a check
   and reports it to a log only; the three statuses the core distinguishes
   never reach the window. `desktop/src-tauri/src/main.rs:48-60` is the
   handler; the delivery is added, not substituted. Contract in
   `ai/TASKS.md`.
2. **Then FIX-VERSION-010 (W-001)** - a dev checkout answers `current: 0.1.0`
   because `server/app/updates.py` reads the stale installed metadata before
   the pyproject beside the source. Fix-VERSION-001's stamp stays first; the
   source moves ahead of the metadata.
3. **FIX-PLAN-003 / FIX-CHART-004 / FIX-PYTHON-005** precede none of these in
   the table but FIX-PLAN-003 is the next of them in priority - the rail
   names "Generate an analysis plan" and no control performs it.
4. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
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
