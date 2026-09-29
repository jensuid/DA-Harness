## Next action

**W2X-009 landed: the drafter stopped promoting the outlier.** The walk
planted revenue 99,589 where the rest were ~99; the profile flagged it at
758.6x, the deterministic draft crowned it anyway ("North has the highest
total_revenue at 99589.5"), and the trust loop closed on a number 758x too
large wearing a partially_supported badge.

**The root cause was two lines, and neither was in the drafter.** main.py's two
profile readers - the interpretation endpoint and the draft-finding endpoint -
selected columns_json and stats_json and never quality_json. The quality column
was added by migration 11 before either reader existed, so profile[quality] was
silently an empty list for the entire analysis path. The drafter could not have
read the outlier; nothing on that path could. Both readers now select
quality_json. The validator path and the import path already read it - the two
broken readers were the outliers, and that is why the walk saw the validator
blame the wrong column: it was the only one of the three actually looking at
quality, and it had nothing else to work with.

**With quality present, the draft reads it.** drafter.py gains _extreme_for,
which parses the detector own sentence back into (value, multiple). The
detector is the one place the rule lives, so re-deriving the comparison here is
how two detectors drift apart. When the result leader is the flagged value, the
caveat names it as an outlier ("at 758.6x the next-largest value, so the
ranking describes the extreme, not the distribution") and points at the largest
group that is not the outlier. The extreme is still stated - the honest answer
names it and steps down, rather than deleting it. Only the measure is checked,
so a quality issue in a column the result never selected stays a fact about the
dataset, not a reason to distrust this draft.

**What broke.** Nothing. The gate caught one thing worth keeping: the planted
test fixture yields 761.5x, not the 758.6x the walk measured, because the
detector computes over the dataset and the test uses six rows while the walk
shipped 110. The assertion takes the profile own sentence rather than
hard-coding the figure.

**Next, in priority order.** The MAJORs are done; what remains is four MINORs
and one packaging decision carried from before:
1. **W2X-004** - the false "unsaved edits" claim from the moment a case
   opens, which is the last thing that reads like a fault to a new analyst.
2. **W2X-003** - the chart is gone after a reopen (0 svgs) though the artifact
   is stored and the evidence graph records it.
3. **W2X-010** - no duplicate notice at case-creation time.
4. **W2X-011** - a case row text does nothing; only the Open button opens.

**Two carried decisions stay, both unchanged and both not code:** the packaged
app is unsigned by DEC-006, and GitHub Actions billing is suspended (fix at
Settings > Billing & plans; nothing since commit c73118c has run in CI).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **W2X-009, the outlier promotion** - two profile readers in main.py never selected quality_json, so the entire analysis path saw an empty quality list and the deterministic draft crowned the planted 99589.5 the profile had already flagged at 758.6x. Both readers now carry it, and the draft names the outlier and steps down to the largest remaining group.
- **W2X-001, the timeout surface** - the wait stopped being one word: a hook
  owning one call's AbortController and elapsed clock, a row each slow panel
  renders ("Generating the plan… 12s elapsed" plus a Cancel button), every
  LLM-backed call carrying the signal, per-action busy state so only the
  button in flight says it, and a cancel reported as a sentence rather than a
  failure.
- **W2X-008 + W2X-013, the density** - the case page's 13.1 viewports: a
  disclosure primitive that is a real control (`<button>` + `role="region"`,
  not native `<details>`), the record group collapsed to summaries that name
  their own counts, the panels whose empty state carries no control waiting
  until the case has them while the overview's "Still to come" names them, and
  the orientation column's fixed 15rem becoming `minmax(15rem, 17rem)`.
- **W2X-002 + W2X-005, the first-thing-the-app-says** - the new-case form
  answers a blank submit by naming the fields it needs in live regions instead
  of going silent, and the workflow rail's "Next" is an action with a button
  to the panel that performs it, the raw endpoint behind a developer-info
  disclosure and its `{dataset_id}` filled with the first attached dataset.
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
