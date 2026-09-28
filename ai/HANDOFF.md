## Next action

**W2X-008 + W2X-013 landed: the case page stopped showing everything it does
not have.** The walk measured 13.1 viewports, 18 flat panels, no disclosures
at all, and 12 of those panels showing an empty state on a case that had just
been created - the original complaint, and the redesign had restyled every
surface without hiding one.

- **The disclosure** (`web/src/lib/disclosure.tsx`) is a `<button>` with
  `aria-expanded` controlling a `role="region"`, the two linked by
  `aria-controls`/`aria-labelledby`. Native `<details>` was rejected: its open
  state is the browser's rather than React's, so it cannot be seeded from the
  case's artifacts and a test cannot read what the analyst chose. Uncontrolled
  after mount on purpose, so a reload does not re-close what the analyst opened.
- **The record group** - Learn, History, Save as a template - is one collapsed
  container in the orientation zone. Each summary names its own count, so a
  collapsed stage still says what it holds.
- **The panels whose empty state carries no control** wait until the case has
  the artifact: Findings and the Evidence graph. The overview's one-sentence
  "Still to come" names them, so the shape of an unfinished case is visible
  without scrolling past twelve nothings. Runs stays - it holds "Draft a
  finding", the only surface that creates one.
- **W2X-013** - the orientation column's fixed 15rem wrapped a long question
  into a 101pt block; `minmax(15rem, 17rem)` lets it breathe.

**What broke, and the fix at the source.** Two tests asserted a 404's guidance
text, which now lives behind a collapsed disclosure. The wrong answer was to
make the test open the group anyway; the right one was that a missing case
must not read as a case with no history. `historySummary` and `walkSummary`
now read the error first and name it - "Case history — could not be read" -
so the guidance is visible collapsed, and the tests open the group the way an
analyst does. A `loading` state that nothing read and an `evidence` expression
that was always false (`!evidenceEmpty && !!evidence`, where the 400 branch
sets the graph null and the error non-empty) were dead code the density
rewrite was the right moment to remove.

**Gates:** web 257 (no net new tests - density is a property the walk
measures, not one the suite asserts), tsc clean, build ok, server 775,
trace 48/48, e2e all steps. Not run this task: measure (its report and the
trace runner read each other, and nothing it measures moved) and desktop
cargo (no Rust touched). Every gate that could regress is green; this task
commits.

**Next, in priority order:**

1. **W2X-001, the timeout surface** - the largest remaining UX finding: three
   of four LLM calls timed out in the walk while the UI showed one static
   word with no elapsed time and no cancel.
2. **W2X-009, the drafter that promoted the planted outlier** - the trust
   finding: a 758.6x outlier became the case's finding and the validator
   blamed the wrong column.
3. **The five MINORs** - W2X-003 (the chart gone after a reopen), W2X-004
   (the false "unsaved edits"), W2X-010 (no duplicate notice), W2X-011 (a
   row's text does nothing).

**Two carried decisions stay, both unchanged and both not code:** the
packaged app is unsigned by DEC-006, and GitHub Actions' billing is
suspended (fix at Settings > Billing & plans; nothing since `c73118c` has
run in CI).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
