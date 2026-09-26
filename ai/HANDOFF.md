## Next action

**P9-F4-001 (the on-screen chart and a re-walk) DONE - and P9 closes.**
recharts@3 was the last of F1's three dependencies at zero imports, and the
chart the shell showed was the core's own static SVG: white background baked
in, no tooltip, no hover. This phase changes the renderer of what the analyst
*looks at*, not of what the case *holds*.

`web/src/lib/chart.tsx` is both halves of that split. `chartGeometry` is the
core's own rules - the series split, the plottable-points filter, the palette
- copied into the shell so the screen and the artifact cannot drift; the
recharts surface carries axes naming their own columns, a bar anchored at
zero because bar length reads as magnitude, a legend only when there is more
than one series, and a tooltip that is a live region. A geometry with
nothing plottable falls back to the core's own image, because a chart the
analyst cannot see is worse than a chart the analyst cannot hover, and a CSS
rule holds the container's height when the tree does not render.

The re-walk is what the task will be remembered for. The shell rendered every
chart as a link: the core's `Chart` model never returned `format`, so the
shell read `undefined` and took the PNG-link branch for *every* chart - the
recharts tree rendered in jsdom, where a fixture supplies the field, and
nowhere else. One field (`format: str = "svg"`, the default the image
endpoint already sniffs), one regression test, and a browser confirmation:
hovering a bar answers its own values, "north" and "total_total : 270". The
lesson worth carrying: a contract tested only against a fixture the test
itself builds is a contract the fixture keeps, not the server. The same gap
is open wherever else a panel mocks a response the server shapes.

**Gates:** web 216 (197 + 19), server 728 (727 + 1), tsc clean, build ok
(CSS 16.46 kB, JS 744 kB), trace 48/48, e2e 28/28.

**Next, in priority order:**

1. **Whatever the next session wants.** P9 is complete - four phases, green
   at each: F1 the foundation, F2 the surfaces, F3 the motion, F4 the chart
   surface and the re-walk. Every dependency F1 installed is used, every
   walk-test finding is closed, and 48/48 requirements still trace. Nothing
   after F4 was planned against the redesign itself; what followed it was
   to be whatever the re-walk found, and the one thing it found was fixed
   inside the task rather than carried.
2. **The carried follow-ups remain**, unchanged: the DMG bundler's
   non-determinism, the icon's blind-chosen proportion, one fragile test
   layout in `CaseWorkspace.test.tsx`, signing deferred by DEC-006, and
   CI's suspended billing (a Settings > Billing fix, not a code one).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **P9-F4-001** - the on-screen chart: recharts draws the same stored result
  the core's artifact came from, with a tooltip a static image cannot give.
  The re-walk found the `format` field the core's response never carried, so
  the tree rendered in jsdom and nowhere else; one field, one regression
  test, and the tooltip verified in a browser. Closes P9.
- **P9-F3-001** - the motion layer: three transitions and three variants, a
  gate mounted at the root that collapses every surface to its shown state
  under reduced motion, and a CSS rule that holds the content visible when
  the motion does not run. Twelve tests, and the disclosure the measurement
  layer times is inside its budget with the motion in the tree.
- **P9-F2-002** - the restyle: every panel and screen renders through the
  token layer, 109 lines of hand-written CSS retired with the class names it
  defined, and one test asserts the debt stays paid. Two literals that lost
  their rules in the deletion were caught by auditing the rules against the
  source.
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

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
