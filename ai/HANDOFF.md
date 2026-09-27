## Next action

**The v0.3.4 close-out is done.** P9 closed the last functional phase, and
this session closed the carried follow-ups that were the only remaining
loose ends: the DMG bundler's flakiness, the icon's blind-chosen proportion,
and the one fragile test layout. `ai/TASKS.md`'s carried list is down to two
environmental items, both of them decisions rather than defects.

**The DMG finding is the one worth carrying.** The non-determinism was never
the tool; it was the vendored `create-dmg`'s Finder-prettifying AppleScript,
which fails when the build runs without a GUI session and succeeds when it
has one - an npm-run subprocess and an interactive shell build the same code,
and one of them answers 64. `--sandbox-safe` skips the AppleScript, so
`desktop/bundle_dmg.sh` passes it and verifies the image. A second run still
moves the container hash, because `hdiutil` stamps the image's creation time;
the mounted contents are byte-identical, and that is the property a build is
reproducible by. The lesson is the shape of the bug: a failure that depends
on *how* the build is invoked rather than on *what* it builds, which is why
"it worked on my machine" was the whole report.

**The icon was measured, not re-cut.** Its artwork covers 51.4% of the canvas,
is dead-centre, carries the correct squircle, and reads as an ascending bar
chart - cyan bars, the tallest in amber. Apple's own guidance says you don't
need to fill the entire canvas with content, so the blind 52% guess was right;
the follow-up was the guess, not the proportion.

**Gates:** web 216, server 728, tsc clean, build ok (JS 744 kB), trace 48/48,
e2e 28/28, the packaged core smokes 0.3.4 end to end (health, version, logs).

**v0.3.4 is published** - tag `d8bec6a`, built locally on Intel with the new
`bundle_dmg.sh`, release created by hand from the steps `release.yml` runs.
The release artifact is `x86_64-apple-darwin` and unsigned, as DEC-006
decided.

**Next, in priority order:**

1. **CI billing, when you want it** - GitHub Settings > Billing & plans. Pure
   account administration, no code; the workflow is correct, the account is
   the blocker. The new `arch-mismatch` CI job will then warn on every run
   that the hosted `macos-latest` lane is arm64 while the shipped artifact is
   x86_64, so a green run no longer reads as proof of the shipped triple.
2. **Nothing else is open.** All nine phases are delivered, all carried
   follow-ups closed, all 48 acceptance thresholds trace. The roadmap's
   deferred list (cloud, collaboration, warehouse connectors, governance)
   stays deferred at a user count of one, and the conformance evaluation's
   deliberately-not-built list (Analysis Canvas, command palette, Knowledge
   nav, AI confidence, dashboards) stays deliberately not built - the command
   palette is the only one that would be cheap to add.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **v0.3.4** - the close-out: the DMG bundler's non-determinism traced to the
  vendored create-dmg's Finder AppleScript (fixed by `--sandbox-safe` in
  `desktop/bundle_dmg.sh`), the icon's proportion measured rather than
  guessed (51.4%, centred, correct squircle - not a defect), and the fragile
  question-refinement test layout given the refusals its `beforeEach` needed.
  Carried follow-ups: two, both decisions (DEC-006's unsigned build, CI
  billing).
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
