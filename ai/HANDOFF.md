## Next action

**P9-F2-001 (the walk-test's last three findings) DONE.** F1 moved nothing
the analyst sees; this is the redesign's first surface change, and it closes
the three findings that stayed open because they were the shell's, not the
CSS's.

W-013: a run the generate panel posted landed in the core and the panel
cleared its proposal, but the panel never told the workspace to re-read the
case, so the runs panel kept saying no analysis had run until a reopen -
the walk-test's own report records the analyst double-running it. The panel
now calls `onChanged`, as every other writing panel does.

W-017: three causes answer 400 from the audit endpoint and the core's
sentences name the *artifact* in all three, so an analyst who left a field
blank read it as their SQL being refused. `EVALUATE_REFUSALS` maps each of
the core's own detail strings to its own sentence naming the field, and
`evaluateRefusal` is the one place the catch reads. The key is the core's
wording, so a reworded refusal is an unknown 400 shown verbatim rather than
hidden - the honesty budget is not paid by swallowing a reason the map
stops recognising.

W-018: the chat memory recalls other cases' findings and the shell never
said so. One muted sentence under the heading is the whole surface.

One operational lesson. The first mapping key I wrote was an invented code
(`empty_code`), and the test failed on the real message string. A refusal
map keyed on anything but the core's own sentence is a second contract the
core never agreed to; key on the words the endpoint actually sends.

**Gates:** web 184 (181 + 3), tsc clean, build ok, trace 48/48. Web-only -
no line outside `web/` moved, so the server suite (727), e2e (28/28),
golden (21/21), refine (AT-04) and measure (9/9) are not re-run.

**Next, in priority order:**

1. **P9-F2-002, the restyle.** The debt F2 took on: `lib/ui.tsx` ships a
   `surfaces` set (panel, heading, subpanel, proposal, card, row) and an
   `accent` that is a class rather than a hex, and nothing imports them yet
   - by the same rule that let F1 ship its dependencies unused. The panels
   swap their `className="panel"` / `"subpanel"` / `"proposal"` / `"run"`
   for those strings, one zone at a time (work, orientation, intelligence,
   then CaseList/CaseCreation), green at each. The old CSS rules stay until
   every consumer has moved, then the dead ones go in one pass - deleting a
   rule a panel still reads is how a restyle breaks an audit that reads the
   emitted stylesheet.
2. **Then F3** motion (respecting `prefers-reduced-motion`) and **F4** the
   chart surface (recharts, which F1 installed and F2 still does not
   import), then a re-walk.

The walk-test's findings are all closed now: W-013/W-017/W-018 here,
W-001/W-005/W-008/W-009/W-011/W-014/W-015/W-016 before it.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **P9-F2-001** - the walk-test's last three findings: a run now appears in
  the runs panel without a reopen, an EVALUATE refusal names the field that
  is wrong rather than the artifact, and the chat panel says its memory is
  cross-case. Closes W-013, W-017 and W-018.
- **P9-F1-001** - the redesign's foundation: the toolchain installed and
  unused, the light theme named as tokens, the 2,889-line workspace split
  into 15 panels under a 600-line ceiling. The split tool closes its loop
  with tsc rather than regex.
- **FIX-PYTHON-005** - the python run surface: the codegen panel offers an
  engine, the proposal matches it, the run posts to the sandbox's own
  endpoint and its refusal is a sentence. Closes W-016.
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
- **FIX-REFINE-007** - the refinement's rationale and grounds, already in
  the API, are shown under their own heading rather than collapsed in a
  `<details>` the analyst has to know to open; the accept keeps them
  visible.
- **FIX-TIMEOUT-006** - one configured LLM timeout (DAH_LLM_TIMEOUT_SECONDS,
  default 120) for all six assistant call sites, and a fallback announced as
  a sentence; v0.3.3 carries it.
- **FIX-VERSION-001** - the packaged core reports its own version; the spec
  stamps it from pyproject, `current_version` reads it first, and both
  packaged-core smokes assert it.
- **WALK-E2E-001** - the walk-test end-to-end; 19 findings (8 MAJOR), the
  report that prioritises them, and the list of what works that the fixes
  must not break.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
