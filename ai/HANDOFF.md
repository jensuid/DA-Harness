## Next action

**W2X-001 landed: the wait stopped being one word.** The walk measured three
of four LLM calls timing out at the 120s ceiling while the UI showed a single
static word - and in the runs panel three "Working…" at once, because one
shared `busy` flag served three unrelated requests.

- **The row** (`web/src/lib/progress.tsx`) is a hook owning one call's
  `AbortController` and a one-second elapsed clock, plus the row a panel
  renders from it: "Generating the plan… 12s elapsed" and a Cancel button.
  `role="status"`, so a screen reader announces the wait without an alert
  - the wait is expected, not a fault.
- **Every LLM-backed call carries the signal**: plan, code, interpret, draft,
  refine, chat, agent proposal. The shell cannot know which engine the core
  will pick before it answers, so a fast deterministic call shows the same row
  for a moment rather than two surfaces for two engines.
- **Per-action busy state.** The runs panel's three buttons each have their
  own flag now, so the one in flight is the only one that says so. The agent
  panel's three actions likewise - a shared flag had "Reject" reading
  "Running…" while a proposal was what was in flight.
- **A cancel is a sentence, not a failure.** "Cancelled - the plan was not
  generated", "Cancelled - the question is still here", and chat keeps the
  question the analyst typed.

**What this is not.** The shell does not shorten the core's own 120s timeout
(`server/app/timeouts.py`) and does not retry: cancelling aborts the browser's
request, and a fallback that arrives after a cancel is the core's business.
The deterministic-fallback banner was already shipped - `sourceLabel` reads
`deterministic fallback` and announces the substitution - so this task is the
wait itself, and the fallback notice it would arrive with was done first.

**What broke.** Four spy assertions in CaseWorkspace.test.tsx matched exact
argument lists that now carry a trailing `AbortSignal`; the calls themselves
are unchanged, so the assertions take `expect.anything()` for it. And the
AT-27 motion-budget test was flaky on this machine - an absolute 200ms
threshold it hit at 200ms and missed at 470ms on the same commit, so it was
measuring the host rather than the layer. It now measures the layer's own
added cost: the median of five renders with the motion against five without
it, so the machine's noise is in both numbers and cancels in the difference.

**Gates:** web 257, tsc clean, build ok, server 775, trace 48/48, e2e all
steps. Not run this task: measure and desktop cargo - no Rust moved, and
nothing the measurement layer reports changed. Every gate that could regress
is green; this task commits.

**Next, in priority order:**

1. **W2X-009, the drafter that promoted the planted outlier** - the trust
   finding: a 758.6x revenue outlier became the case's finding and the
   validator then blamed the wrong column, so the loop closed on a false
   number wearing a `partially_supported` badge.
2. **The MINORs** - W2X-003 (the chart gone after a reopen), W2X-004 (the
   false "unsaved edits" from the moment a case opens), W2X-010 (no duplicate
   notice at create time), W2X-011 (a case row's text does nothing, only the
   Open button).

**Two carried decisions stay, both unchanged and both not code:** the
packaged app is unsigned by DEC-006, and GitHub Actions' billing is
suspended (fix at Settings > Billing & plans; nothing since `c73118c` has
run in CI).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
