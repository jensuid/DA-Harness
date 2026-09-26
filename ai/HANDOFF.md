## Next action

**P9-F3-001 (the motion layer and its gate) DONE.** framer-motion@13 was
installed in F1 and imported nowhere - the same debt F2 paid for the tokens,
one phase earlier. The motion is paid too, and the gate that decides whether
any of it runs is the task's real subject.

`web/src/lib/motion.tsx` names three transitions - `surface` at 0.18s for
what a click opens, `enter` at 0.28s for what a case loads, `arrive` as a
spring for what a verdict does - and three variants to match, each a
`hidden` and a `shown` state with the transition riding inside the target.
The movement is 4-6px and never an element's own height, because layout
shift is the frame AT-27 counts; the verdict scales by 2% rather than
sliding, because the loop's exit is the one place weight reads.

The gate is `prefers-reduced-motion`, and the collapse is this layer's own
rather than the library's. framer-motion makes positional keys instant under
reduced motion but still fades opacity, so a reduced-motion setting that
still moves the surface is a setting the surface is not honouring:
`MotionSurface` reads `useReducedMotionConfig()` and sets `initial={false}`,
rendering the shown state with no animation at all - the same result the CSS
gives the shell notice. A second `prefers-reduced-motion` rule in
`index.css` holds a `[data-motion-surface]` at opacity 1, because a surface
that starts hidden and is never animated to shown - the engine absent, a
frame dropped on a slow machine - is invisible content, and that failure is
the one the JS gate cannot see itself out of.

The lesson the gate earned, and the reason the test reads the preference
from inside the provider: `useReducedMotion()` caches the OS preference in
`useState` at first read, so a probe that reads it outside `MotionConfig`
always answers the default. The preference is a context, not a global, and
the two are not interchangeable. jsdom has no `matchMedia` either, so a shim
in `setup-tests.ts` is what makes the gate behave in the suite the way it
behaves in a browser - stubbed per test and unstubbed after, so it does not
leak into the accessibility audit or the measurement layer.

**Gates:** web 197 (185 + 12), tsc clean, build ok (CSS 15.11 kB, JS 347 kB,
still resolving the focus rule), trace 48/48. Web-only - no line outside
`web/` moved, so the server suite (727), e2e (28/28), golden (21/21), refine
(AT-04) and measure (9/9) are not re-run.

**Next, in priority order:**

1. **P9-F4, the chart surface and a re-walk.** recharts@3 is installed and
   unused - the last of F1's three dependencies still at zero imports. The
   on-screen chart is the server's SVG replaced by an interactive one: a
   tooltip and a hover state are what the static SVG cannot give, and the
   evidence the chart is does not change with the renderer. The server's
   layout engine and its PNG export stay for the export path, because a
   chart that changes shape between the screen and the exported artifact is
   not evidence. The re-walk is the same kind of check the walk-test was:
   use the shipped shell, and record what the redesign changed for a reader
   who is not the one who built it.
2. **Then P9 closes.** Four phases, green at each: F1 the foundation, F2 the
   surfaces, F3 the motion, F4 the chart and the re-walk. Nothing after F4 is
   planned against the redesign itself; what follows it is whatever the
   re-walk finds.

F3's surfaces are the wrappers F2 already rendered - a run row, a verdict, a
chat answer, a case row, the three zones of the workspace - now a
`MotionSurface` carrying the same `className`. No markup was added and no
surface was restyled; the motion is the surface's own, not a second layer
over it.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
