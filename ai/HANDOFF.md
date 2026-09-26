## Next action

**P9-F2-002 (the restyle onto the tokens) DONE.** The debt F1 and F2-001 took
on is paid: the token layer in `lib/ui.tsx` is the vocabulary every panel and
screen renders, and 109 lines of the hand-written CSS that named those
surfaces retired with them.

The panels swapped their literal `className="panel"` / `"subpanel"` /
`"proposal"` / `"run"` / `"turn"` / `"muted"` / `"row"` for the `surfaces`
string holding the same values as utility classes. The restyle is parity by
contract - a surface is the rule it replaced, so nothing looks different and
the palette is one set of names in one file. What stays in the CSS is what no
token can own: the three-zone grid, the sticky rail, the verdict and chip
shapes the status vocabulary renders as text-plus-chip, the quality and
notice surfaces, and the literal `:focus-visible` the accessibility audit
resolves.

One lesson the audit earned, and the reason this task's own test exists.
Deleting the retired rules was only safe once the rules were checked against
the source that used them, not against the list of rules the restyle
touched. Two literals survived the move and lost their rules:
`LearnPanel`'s `className="stage done"` (the rule is kept - a completed stage
is the one green status, and the word is the rail's and the ladder's shared
vocabulary) and `FindingsPanel`'s `className="muted"`, which moved to
`surfaces.note`. A panel that goes back to a literal now fails by name.

**Gates:** web 185 (184 + 1), tsc clean, build ok (the emitted CSS is
14.44 kB and still resolves the focus rule), trace 48/48. Web-only - no line
outside `web/` moved, so the server suite (727), e2e (28/28), golden (21/21),
refine (AT-04) and measure (9/9) are not re-run.

**Next, in priority order:**

1. **P9-F3, motion.** framer-motion@13 is installed and imported nowhere -
   the same debt shape F2 just paid, one phase earlier. The motion is the
   surfaces' own: a panel's content appearing as the case loads, a run row
   opening, a verdict landing. The constraint is `prefers-reduced-motion`,
   which the CSS already honours for the shell notice (`index.css`'s
   explicit `animation: none` rule); F3 makes the JS-driven motion honour it
   too rather than only the CSS-driven kind. A motion budget is the
   discipline: an animation that costs a frame the measurement layer
   (AT-27/AT-30) counts is a regression, not a polish.
2. **Then P9-F4, the chart surface and a re-walk.** recharts@3 is installed
   and unused. The on-screen chart is the server's SVG replaced by an
   interactive one - the server's layout engine and PNG export stay for the
   export path, because a chart that changes shape between the screen and
   the exported artifact is not evidence.

F2's two tasks are done: F2-001 the walk-test's last three findings,
F2-002 the restyle. The walk-test's findings are all closed, and the
redesign's foundation is now the surface the analyst reads.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
