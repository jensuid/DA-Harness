## Next action

**W2X-004 landed: the false unsaved-edits claim stopped firing on open.** The
walk saw "unsaved edits" the moment a case opened, on context nothing had
touched, and again after every reopen.

**The finding named the wrong panel.** The Context panel already did this
correctly - it initialises `dirty` false, sets it false again after load, and
only flips it on a keystroke, an add, or a remove. The false signal came from
the Decision panel's implications editor, one zone over. Its `dirty` was
derived, not tracked: `const dirty = draft.join('\\n') !== (saved ?? view.implications).join('\\n')`. `saved` starts null and the effect seeds it from
the view, but the parent reloads the whole workspace on every change in the
case, handing the panel a fresh `view` object whose `implications` array is a
different identity than the array the effect seeded `draft` from. Same
contents, different array - so the comparison read as an edit on a case
nothing touched.

**The fix is an `edited` flag** the three edit gestures set, with `dirty` now
the flag AND a divergence, so a reload alone cannot flip it and an analyst who
reverts to the stored text sees the claim clear. The save path clears it, and
the effect seeds it false too, so a re-fetched view is not an edit.

**Why this is trust, not polish:** a warning that fires on every open is one
the analyst stops reading, and the moment real unsaved edits arrive it carries
no weight. Both panels now claim it only when an actual edit is pending.

**What broke.** Nothing in the suite. One new regression test mounts a case
whose stored context has a purpose and entries and asserts no "unsaved edits"
and a "saved" label. Isolating it fails it - the workspace's other readers
need the mocks `mockEmptyCase()` installs - but it passes in the file run,
which is how the suite has always run.

**Next, in priority order.** Three MINORs remain, then the carried packaging
decision:
1. **W2X-003** - the chart is gone after a reopen (0 svgs) though the artifact
   is stored and the evidence graph records it. `RunsPanel`.
2. **W2X-011** - a case row's text does nothing; only the Open button opens
   it. `CaseList.tsx`.
3. **W2X-010** - no duplicate notice at case-creation time.

**One carried decision stays, unchanged and not code:** GitHub Actions billing
is suspended (fix at Settings > Billing & plans; nothing since commit c73118c
has run in CI). The packaged app is unsigned by DEC-006.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **W2X-004, the false unsaved-edits claim** - the finding named the Context panel; the Context panel was already correct. The Decision panel's implications editor derived `dirty` from a join comparison, so a parent reload handing it a fresh view object read as an edit. An `edited` flag now tracks the gesture instead.
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
