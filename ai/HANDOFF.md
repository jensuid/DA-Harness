## Next action

**W2X-002 + W2X-005 landed: the first thing the app says is no longer
silence, and no longer an endpoint.** Both were the walk-test's "what do I
do first" findings, and both were the app answering a question the analyst
hadn't asked - or not answering at all.

- **W2X-002** - submitting "New Analysis Case" with a blank field used to be
  total silence: no request, no alert, nothing changed, because only HTML5
  native validation stood behind the submit. The form now names the fields it
  still needs in `role="alert"` live regions, marks them `aria-invalid`,
  clears a message when the field is filled, and labels both with `*`. The
  browser's own refusal was correct; its message was the part nobody could
  see.
- **W2X-005** - the rail's "Next:" showed `POST /cases/…/datasets` with a
  `{dataset_id}` placeholder unfilled, which read as a bug and answered a
  developer's question. It now shows the action and a "Go to the Data panel"
  button that scrolls to the panel that performs it; the path lives behind a
  "developer info" disclosure. The core half fills the placeholder with the
  first attached dataset and drops it when none exists, so the quoted path
  is a path that runs.

**What broke, all in the tests.** jsdom renders `<details>` open (no
content-visibility), so the test that asserted the endpoint was absent had to
assert it is *inside* the disclosure instead - the browser behaviour and the
jsdom behaviour are both right, and the assertion now names the contract
rather than the rendering. The sentence "Next: Attach a dataset" spans a
`<strong>`, so `getByText` needed the container's own text. And
`vi.clearAllMocks` was missing from one file, so a `createCase` spy carried a
call from the test before it - the "silence" the test saw was its own leak.

**Gates:** web 257 (246 + 11), tsc clean, build ok, server full suite 773
(772 + 1), test_workflow 16 (14 + 2), trace 48/48, e2e all steps,
measure 9/9. Every gate is green; this task commits.

**The AT-38 circle is broken, and it was never a circle.** The handoff's
hypothesis was that the suite fails only *inside* the line counter because the
seven `test_trace` tests read `verification/measure/REPORT.md`
(`matrix.py:167`), which a failed measure run had itself just written red. That
was wrong, and chasing it was the wrong place. The real failure was one test in
a suite the runner collects first alphabetically: `test_refine.py::
test_create_refinement_reports_the_engine_that_spoke` asserted
`source == "deterministic"` and got `"deterministic fallback"` because a
*previous* test in `test_llm_config.py` had left `DAH_LLM_API_KEY` set in
`os.environ`, so the refiner was configured, made a real network call to
`api.openai.com`, got a 401, and fell back. The fallback label was the only
evidence of the leak. `apply_config` writing `os.environ` directly is the whole
point of "no restart" and is correct production code; `monkeypatch` restores
only the variables a test declared, and the PUT endpoint's write is not one of
them. The suite's own comment claimed the opposite
(`test_llm_config.py:162-168`). Fixed by restoring the four variables in the
autouse fixture's teardown, converting `test_env_config.py` off its hand-rolled
`try/finally` pops for the same reason, and pinning it with a regression test
that names any variable that outlives the suite. The 401 also explains the
"stale background notifications": those runs were the same leak, not the same
suite. Lesson: an order-dependent failure in one test file is an environment
leak in another one that runs first.

**Next, in priority order:**

1. **W2X-008, the density.** The largest effort and the original complaint:
   hide empty panels, collapse completed stages, narrow the orientation zone.
2. **W2X-001, W2X-009, then the five MINORs.**
3. **W2X-004, the timeout surface** - three of four calls timed out in the
   walk and the UI showed one static word with no elapsed time and no cancel.

**Two carried decisions stay, both unchanged and both not code:** the
packaged app is unsigned by DEC-006, and GitHub Actions' billing is
suspended (fix at Settings > Billing & plans; nothing since `c73118c` has
run in CI).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
