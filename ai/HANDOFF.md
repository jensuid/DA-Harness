## Next action

**W2X-006 + W2X-007 landed: the code is editable, and the engine has a door of
its own.** The walk-test's realest frustration loop was a 400 on a one-token
date fix that cost another LLM call, because the only copy of the code was a
read-only `<pre>`; and the stage guidance said "Run an analysis" while the
only paths into `/runs` were the non-editable codegen and the EDA presets.

- **W2X-006** - the proposal's `<pre>` is a `textarea`. The proposal stays
  immutable; a `draft` starts as its code and is what the run posts, so an
  untouched proposal runs unchanged and an edit costs no second call.
- **W2X-007** - a `RunCodePanel` in the work zone: an engine selector, a blank
  editor, and the run endpoints the codegen panel already posts to. The core's
  own SQL/Python capability has a surface, not just a stage instruction.

**What broke, both in the tests rather than the product.** The `vi.mock`
factories returned only the functions, so `ApiError` was undefined under the
mock and `messageOf`'s refusal branch was dead in those two files - the
panel's own refusal sentence was the thing a broken mock hid. Fixed by
spreading the original module. And `user.type` parses `[` as a keyboard
modifier, so one python snippet in a test had to drop its list comprehension.

**Gates:** web 246 (235 + 11), tsc clean, build ok. The server and cargo
gates are untouched this task - no core or shell code changed. Browser check
against a live core: the panel renders as "Run code on tickets.csv" with both
engine radios, and the proposal's code reaches an editable textarea.

**Next, in priority order:**

1. **W2X-002 and W2X-005** - an inline required-field message and a real
   action instead of the raw `POST` endpoint string. Both small.
2. **W2X-008, the density.** The largest effort and the original complaint:
   hide empty panels, collapse completed stages, narrow the orientation zone.
3. **W2X-001, W2X-009, then the five MINORs.**

**Two carried decisions stay, both unchanged and both not code:** the
packaged app is unsigned by DEC-006, and GitHub Actions' billing is
suspended (fix at Settings > Billing & plans; nothing since `c73118c` has
run in CI).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **W2X-006 + W2X-007, the analysis editor** - the proposal's `<pre>` is now a
  `textarea` whose `draft` is what the run posts, so a one-token fix costs no
  second LLM call; and a `RunCodePanel` in the work zone gives the core's own
  SQL/Python engine a door of its own, posting to the endpoints that already
  existed.
- **W2X-012 phase B** - the settings surface: `dah-llm.json` in the shell's
  data dir, read at boot and applied on save (no restart), `GET/PUT
  /llm/config`, a three-field panel in the bundle opened from a menu item
  through the DOM-event channel that needs no permission, and the banner's
  Configure button with a one-off refetch. The BLOCKER's credential half is
  closed; W2X-012 is done.
- **WALK-UX-002 (recorded, not fixed)** - the second walk-test, the first
  since the redesign: thirteen findings against the designed surfaces,
  `walktest-w2/` committed as the evidence.
- **v0.3.4** - the close-out: the DMG bundler's non-determinism traced to the
  vendored create-dmg's Finder AppleScript (fixed by `--sandbox-safe` in
  `desktop/bundle_dmg.sh`), the icon's proportion measured rather than
  guessed (51.4%, centred, correct squircle - not a defect), and the fragile
  question-refinement test layout given the refusals its `beforeEach` needed.
- **P9-F4-001** - the on-screen chart: recharts draws the same stored result
  the core's artifact came from, with a tooltip a static image cannot give.
  The re-walk found the `format` field the core's response never carried, so
  the tree rendered in jsdom and nowhere else; one field, one regression
  test, and the tooltip verified in a browser. Closes P9.
- **P9-F3-001** - the motion layer: three transitions and three variants, a
  gate mounted at the root that collapses every surface to its shown state
  under reduced motion, and a CSS rule that holds the content visible when
  the motion does not run.
- **P9-F2-002** - the restyle: every panel and screen renders through the
  token layer, 109 lines of hand-written CSS retired with the class names it
  defined, and one test asserts the debt stays paid.
- **P9-F2-001** - the walk-test's last three findings: a run now appears in
  the runs panel without a reopen, an EVALUATE refusal names the field that
  is wrong rather than the artifact, and the chat panel says its memory is
  cross-case. Closes W-013, W-017 and W-018.
- **P9-F1-001** - the redesign's foundation: the toolchain installed and
  unused, the light theme named as tokens, the 2,889-line workspace split
  into 15 panels under a 600-line ceiling.
- **FIX-PYTHON-005** - the python run surface: the codegen panel offers an
  engine, the proposal matches it, the run posts to the sandbox's own
  endpoint and its refusal is a sentence. Closes W-016.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
