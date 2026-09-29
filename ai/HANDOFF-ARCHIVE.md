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


---

## W2X-008 + W2X-013

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
The archive of `ai/HANDOFF.md`'s `## Next action` sections. Each section is
moved here verbatim, never edited or summarised, when the task that wrote it
completes - it is the record of what a session thought mattered before it
knew how it would end.

---

## W2X-002 + W2X-005

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
(`matrix.py:167`), which a failed measure run had itself just written red.
That was wrong, and chasing it was the wrong place. The real failure was one
test in a suite the runner collects first alphabetically: `test_refine.py::
test_create_refinement_reports_the_engine_that_spoke` asserted
`source == "deterministic"` and got `"deterministic fallback"` because a
*previous* test in `test_llm_config.py` had left `DAH_LLM_API_KEY` set in
`os.environ`, so the refiner was configured, made a real network call to
api.openai.com, got a 401, and fell back. The fallback label was the only
evidence of the leak. `apply_config` writing `os.environ` directly is the
whole point of "no restart" and is correct production code; `monkeypatch`
restores only the variables a test declared, and the PUT endpoint's write is
not one of them. The suite's own comment claimed the opposite
(`test_llm_config.py:162-168`). Fixed by restoring the four variables in the
autouse fixture's teardown, converting `test_env_config.py` off its
hand-rolled `try/finally` pops for the same reason, and pinning it with a
regression test that names any variable that outlives the suite. The 401 also
explains the "stale background notifications": those runs were the same leak,
not the same suite. Lesson: an order-dependent failure in one test file is an
environment leak in another one that runs first.

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

## W2X-006 + W2X-007

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

---

## W2X-012 phase B

**W2X-012 phase B landed: the walk-test's BLOCKER is closed on both halves.**
Phase A made the LLM's degradation sayable; this made it fixable from inside
the app. The credential lives in `dah-llm.json` in the data dir the shell
already injects - mode 0o600, written atomically, outside the repo, the bundle
and git, so the analyst can edit or delete it without a rebuild - read into
`os.environ` once at boot and applied on every save, which works because the
six adapters read the environment at call time and need no restart. `GET
/llm/config` reads the file and never the environment (an exported key the
shell cannot overwrite would otherwise reach the CORS-permitted webview);
`PUT /llm/config` writes, applies, and answers phase A's own `LlmStatus`, so
the panel reports the core's verdict and not its own write. The surface is
three fields in the bundle itself, opened from a "DAH Settings…" menu item
through the same `window.eval()` DOM CustomEvent channel `updates.rs` already
used - no permission, no capability change, and a no-op in a browser host.

**Two design decisions from this task are worth carrying.** The capability set
does not change: the handoff's phase-B note said the shell gains a Tauri
command, but `updates.rs` had already proven that a script dispatching a DOM
event reaches the bundle without one, so `core:default` stays as the
deliberate property it is. And the write path applies rather than yields: a
blank save unsets `DAH_LLM_API_KEY` instead of blanking it, because the form
is the thing that just wrote it - that the clear did not work was a real bug
the tests found, not a test error.

**Gates:** server 772 (741 + 31), cargo 30 (26 + 4), web 235 (223 + 12), tsc
clean, build ok (CSS 17.92 kB, JS 747 kB), trace 48/48, measure 9/9. The full
save loop verified in a real browser against a live core: the concern banner,
the Configure button opening the panel, a save answering "no restart needed",
and the banner leaving the screen without a reload.

**Two defects found by the measure gate and fixed in the same commit:** the
AT-38 line counter imported every app module before pytest registered, so
`configure_logging()` installed a real file handler into the repo; and the new
config tests leaked `os.environ` into other suites, so `test_refine` made a
real LLM call and failed on a hostname lookup. The first is a pre-existing
runner bug, the second is the tests this task wrote.

Reading this is not part of resuming; `ai/HANDOFF.md` is.

## Next action

**W2X-012 phase A landed: the LLM degradation is no longer silent.** The
walk-test's BLOCKER had two halves - a credential that never reaches the
packaged app, and an analyst who was told nothing about it - and this session
closed the second. `server/app/llm.py` is the one place the three env vars the
six adapters each read for themselves get read for an answer, `GET
/llm/status` carries it (configured, the provider *name*, the model and base
URL, never the key), the core writes one boot line about which engine is in
play, and `LlmStatusBanner` renders on every screen: nothing when an LLM is
configured, because a green banner on every screen is noise the analyst learns
to dismiss, and a concern banner naming the deterministic engines when one is
not. Both states were verified against a real browser with the core started
both ways.

**The finding is not gone, only honest now.** The credential still does not
reach `/Applications/DAH.app` - `.env` is gitignored and un-bundled, `main.py`
loads it relative to a path that does not exist inside a PyInstaller bundle,
and the shell does not inject the key. That is phase B, and it needs a design
decision before code: a first-run UI prompt writing into the app data dir (the
recommendation, and the one the status surface is built to pre-fill), or
build-time secret injection into the bundle (works today, burns the key into a
binary that can be reversed). Phase A is the floor either of them builds on -
without a way to ask the core what it has, phase B's own UI cannot tell the
analyst whether it worked.

**Gates:** server 741 (728 + 13), web 223 (216 + 7), tsc clean, build ok
(CSS 16.84 kB, JS 744 kB), trace 48/48, e2e 28/28, golden 21/21, refine AT-04
(100/100/0/0), measure 9/9.

**Next, in priority order:**

1. **W2X-012 phase B - the design decision, then the settings surface.** A
   first-run prompt plus a "DAH Settings…" menu item writing
   `DAH_LLM_*` into the app data dir and telling the core where to read
   them, with the banner now able to say "configured" the moment it works.
   The shell gains a Tauri command (a capability change - `core:default`
   grants nothing today, and that permission set is a deliberate property)
   and the core gains a read path for the data-dir file, so this is two or
   three commits, not one.
2. **W2X-007 + W2X-006, the analysis editor** - one surface: an editable
   textarea replacing the `<pre>` the generated code shows, posting to the
   endpoints that already exist. The realest frustration loop in the
   walk-test.
3. **W2X-002 and W2X-005** - an inline required-field message and a real
   action instead of the raw `POST` endpoint string. Both small.
4. **W2X-008, the density.** The largest effort and the original complaint:
   hide empty panels, collapse completed stages, narrow the orientation zone.
5. **W2X-001, W2X-009, then the five MINORs.**

**Two carried decisions stay, both unchanged and both not code:** the
packaged app is unsigned by DEC-006, and GitHub Actions' billing is
suspended (fix at Settings > Billing & plans; nothing since `c73118c` has
run in CI).
