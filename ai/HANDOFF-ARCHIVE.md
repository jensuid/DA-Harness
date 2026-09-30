## Next action

**W3X-004 is fixed: the Python run surface teaches its own contract.** The
engine a Python-fluent analyst reaches for first refused them three times in a
row (`import pandas`, `import csv`, the `path` variable the SQL placeholder
implies exists) and put none of the answers on the page - the placeholder was
`# python`. The sandbox was correct to refuse, so nothing about it moved: no
allowlist change, no endpoint, no capability, no refusal message. What changed
is the sign on the wall. While Python is chosen, `RunCodePanel` shows the
handle (`dataset.rows` / `.columns` / `.query(sql)`, and that there is no file
path), the importable subset as one sentence that names pandas, csv and numpy
as refused with `statistics` as the alternative, and the list-of-dicts-in-
`result` shape a run takes. The placeholder became the canonical use the
core's own tests write, so running it as it stands produces a run. The
contract is the Python engine's own - absent on SQL, whose placeholder carries
`read_csv_auto(?)`. Six tests cover it, one of which reads `_SAFE_MODULES`
out of `server/app/python_exec.py` and compares sets, so the page cannot claim
a door the wall refuses.

Gates: web 278/278 (was 272; +6 in RunCodePanel.test.tsx), tsc clean, build ok;
server 788/788 unchanged (this task moved no server code); trace 48/48, e2e
28/28. `graphify update .` ran clean.

**Next: W3X-002, the fallback sentence glued to its label.** `sourceLabel`
returns the substitution sentence and the panel appends ` for {filename}`, so
it renders "...answered in its place. for helpdesk_tickets_2026.csv" - a
lowercase fragment that reads as a typo. Cheapest fix of the remaining three,
and it lands on every LLM-backed panel. After it, W3X-003: why the plan call
burns the whole 120s budget when the chat call on the same provider answers
in 67s - the root cause before the timeout number moves.

## Next action

Two things the gate caught that were not the W2X-004 code (from the W2X-001
gate run, kept as the record of why those tests moved). Four spy assertions in
CaseWorkspace.test.tsx matched exact argument lists that now carry a trailing
`AbortSignal`; the calls themselves are unchanged, so the assertions take
`expect.anything()` for it. And the AT-27 motion-budget test was flaky on this
machine - an absolute 200ms threshold it hit at 200ms and missed at 470ms on
the same commit, so it was measuring the host rather than the layer. It now
measures the motion layer's own added cost: the median of five renders with the
motion against five without it, so the machine's noise is in both numbers and
cancels in the difference.


**W2X-010 landed: the duplicate case stops being silent.** The walk-test's last
finding - two rows for the same question and the same dataset, nothing to tell
them apart but a timestamp nobody reads.

The core answers the question itself now. `POST /cases` carries a `duplicate_of`
when another case already asks this exact question about this exact dataset, so
the shell reads a fact rather than guessing at similarity. Migration 14 adds
`cases.duplicate_of`, advisory the way `template_id` already is: read to warn,
never to enforce, and a store that predates it degrades to "not a duplicate".

The pair is not a constraint, and that was the design call. A duplicate is a
case in its own right and re-running an old question is a normal thing to do, so
the case is still made - the notice is what was missing. The create form keeps
it and stays put with a warn-toned sentence naming the question and dataset plus
a link to the case it repeats, instead of opening a workspace the analyst may
not have wanted. The list row carries `repeats case <id>` so the two are
distinguishable at a glance later too.

The same read serves the other two creation paths: a template-seeded case is
flagged when its question+dataset already exists, and a duplicate keeps the
lineage its source carried rather than naming the case it was made from.

Gates: server 788/788 (777 + 11), web 272/272 (262 + 10), tsc clean, build ok,
trace 48/48, e2e ALL PASS, golden 21/21, refine AT-04 PASS. The schema moved to
14, so every gate that reads the store was re-run. CI billing is still
suspended (nothing since c73118c has run in CI); the packaged app is unsigned
by DEC-006.

**Next: all thirteen walk-test findings are closed.** WALK-UX-002 is finished -
nothing remains open from `walktest-w2/FINDINGS.md`. No task is queued; the next
move is the user's.

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

## Next action

**W2X-003 landed: the chart stops vanishing when a case reopens.** The walk
rendered a chart, left the case, came back to 0 svgs while the evidence graph
still said the case had one.

**Two causes, both about where the chart lived.** First, the drawing was local
state: the panel kept the chart it rendered in a useState a remount resets, so
there was no way for it to reappear. Second, the panel itself only mounted once
the analyst clicked "Show the rows" - the chart sits below the rows table, so
even a restored chart had nowhere to draw. Fixing only one of the two would
have left the bug standing.

**The fix restores both.** The run row reads its charts on mount; when it has
one it reads the rows automatically, the same read "Show the rows" makes, only
unprompted. The chart is re-read from the core: the chart endpoint for its
metadata, the image endpoint for the bytes. The image endpoint sniffs its
format from the stored bytes rather than from a column the charts table keeps,
so a new `api.getChart` answers "is this SVG or PNG" before the image is
fetched - an inline drawing and a bitmap link are the surface's two shapes. A
restored chart yields to a fresh render the analyst makes in the same session,
and a chart whose image is missing from disk restores silently, leaving the
control where it always was.

**What broke.** The test's first draft asserted `chart-svg`, the testid of the
inline-SVG branch - but a plottable geometry draws on screen as `chart-tree`
(recharts), and the SVG branch is the fallback for a geometry with nothing to
plot. The assertion now reads the drawing itself, not one of its two shapes.

**Next, in priority order.** Two MINORs remain:
1. **W2X-011** - a case row's text does nothing; only the Open button opens
   it. `CaseList.tsx`.
2. **W2X-010** - no duplicate notice at case-creation time.

**One carried decision stays, unchanged and not code:** GitHub Actions
billing is suspended (fix at Settings > Billing & plans; nothing since commit
c73118c has run in CI). The packaged app is unsigned by DEC-006.

## Next action
**W2X-011 landed: the case row opens the case anywhere it is clicked.** The
walk clicked a row's text and nothing happened; only the Open button worked.

The button already spanned the row's width, but it was only as tall as its own
text, so the blank space below the text was not the button - it was the
container the button sat in. `flex: 1 0 auto` in `web/src/index.css` stretches
the button to the row's height instead of adding a second listener, so the row
is one button and the click that missed before now lands on the same handler.

The buttons beside it (rename, duplicate, delete) are siblings, not children,
so they keep their own targets; the row stays openable until deletion is armed,
and `disabled` still suppresses the open while the confirmation is showing.

Gates: web 262/262 (259 + 3), tsc clean, build ok. Shell-only: nothing the core
tests exercise changed, so the server (777) and e2e (28) gates were not
re-run. CI billing is still suspended (nothing since c73118c has run in CI);
the packaged app is unsigned by DEC-006.

**Next in priority order: W2X-010** - the last walk-test finding. The case list shows duplicate rows for the same question and dataset without any warning at create time, and the gap is the missing duplicate notice.


## Next action

**Walk-test 3 is complete: the loop runs end to end on a domain the project
had never analysed, with a real LLM and a live browser.** A fresh core on an
isolated data dir, a seeded helpdesk dataset with six planted anomalies, and
one case driven through every surface the shell owns - attach, profile, plan,
SQL, Python, chart, interpret, draft, validate, the reviewer's audit, chat, the
decision's implications and the export - without a terminal anywhere in the
path. `loop_closed` read true and the export round-tripped.

Four findings, none a blocker. Two are microcopy on surfaces that work: the
fallback sentence is glued to the label it replaces ("...answered in its place.
for helpdesk_tickets_2026.csv"), and the Python surface refuses three times
(`pandas`, `csv`, `path`) without putting the answer - `dataset.rows` and the
importable subset - on the page. The third is the wait that remains after
W2X-001 fixed the silence: the plan call consumed the whole 120s budget for an
answer the deterministic engine writes in under a second, while the chat call
on the same provider answered in 67s - so the timeout change is second, and
finding out why the plan call differs is first. The fourth is a harness
artifact (a filename accepted twice) and is recorded, not fixed.

Nine confirmations were measured, not assumed: every W2X fix the last walk
forced still holds against the running core. Gates at this tree: server 788/788,
web 272/272 (one timing test timed out under load and re-ran green), tsc clean,
build ok, e2e 28/28, trace 48/48.

**Next: nothing is queued.** The three MAJOR findings each carry its own fix
shape, and the W3X-003 root cause - why the plan call takes 120s when the chat
call takes 67s - is the one that should be looked at before any timeout is
moved.

## Next action

**W3X-002 is fixed: the fallback announcement reads as a sentence again.** The
walk-test measured the rendering - "...answered in its place. for
helpdesk_tickets_2026.csv" - because a panel appended its own context to a
label that is already a complete sentence, and a period followed by a
lowercase fragment reads as a typo rather than as the substitution notice
W2X-001/FIX-TIMEOUT-006 put there.

The fix moved only the join. `sourceLabel` and the five sentences it returns
are byte-identical (the server's wording, and the panels that render the label
with no context of their own - RunsPanel, Chat, RefinePanel - are untouched).
The three panels that append their own context go through a new `sourceWith`,
which capitalises the context so a sentence ending in a period takes a
grammatical clause. DraftPanel's "accepting records a real finding" became the
sibling `<p>` it always read as. Seven unit tests pin it, including one that
asserts the measured typo shape is absent.

Gates: web 285/285 (was 278; +7 in sourceLabel.test.ts), tsc clean, build ok;
server 788/788 unchanged (this task moved no server code); trace 48/48, e2e
28/28. `graphify update .` ran clean.

**Next: one task is queued — the W3X-003 follow-up, `W3X-003-PROMPT`.** The
root cause is measured and recorded (`walktest-w3/FINDINGS.md`): the plan
prompt asks for the largest output of the six LLM adapters (6 sub-questions,
5 hypotheses, 6 analysis steps) and the provider generates at ~13 completion
tokens per second, so 1785 tokens is ~137s against a 120s timeout. The path
to a faster plan runs through the prompt's output size, not `timeouts.py`.

The task: shrink what the LLM plan prompt asks for, so a complete plan arrives
inside the budget on a ~13 tok/s provider. Fix shape (measured baseline above):
- `server/app/planner.py` `LLMPlanner.plan` — the prompt's schema text and the
  instruction voice. Candidates: cap the requested lists in the prompt itself
  (e.g. 4 sub-questions, 3 hypotheses, 4 steps), and add an explicit "be
  concise; one short clause per field" instruction. `_MAX_LLM_CHARS` (input
  truncation) is not the variable - the output is.
- Keep `_MAX_SUB_QUESTIONS = 6`, `_MAX_HYPOTHESES = 5`, `_MAX_STEPS = 6` as the
  *validator's* ceilings (the deterministic planner and every existing test
  still produces up to those counts), so a smaller *request* must not shrink
  what the deterministic path or validation accepts. Only the LLM prompt asks
  for less.
- Do not add `max_tokens`: measured, it truncates the JSON mid-object
  (`finish_reason: length`) and the schema validator refuses it - a cap buys a
  faster fallback, not a faster answer.
- `temperature` is not the variable either (measured: 141s with, 103s without,
  the difference is only output length).

Gates: server pytest (788, plus any new tests), web unchanged (285/285 unless
shell text moves), tsc clean, build ok, e2e 28/28, trace 48/48.

Gates now: web 285/285, tsc clean, build ok; server 788/788, trace 48/48,
e2e 28/28.

## Next action

**W3X-003-PROMPT is done: the LLM plan prompt asks for less, so the answer
arrives inside the budget.** The third walk-test's measured wait (a plan call
that burned all 120s and fell back deterministically) was root-caused as the
prompt's output size, not the timeout: the plan is the only one of the six
adapters that asks for a large structured object, and the provider generates
at ~10-13 tokens per second, so the 1785-token plan the prompt asked for was
~137s. The fix moved the request, not the contract.

The prompt is now reachable without posting it — `LLMPlanner.prompt` holds the
text `plan` sends, byte-for-byte — and it asks for at most 4 sub-questions, 3
hypotheses, 4 steps and 3 data requirements, one short clause per string. A
live re-measurement against the same provider answered 508 tokens in 52.3s
(`finish_reason: stop`) — inside the budget, not a truncated object the
validator would refuse. The validator's ceilings are untouched: an engine that
answers with the full contract still passes, and the deterministic planner
still produces up to it. Only what the LLM is *asked* for shrank.

Honest about the limit: a ~10 tok/s provider is never fast, and the rate is the
provider's. The fix moved the plan from "times out and falls back" to "answers
inside the budget" — a faster plan still needs a faster provider, and the
measurement (`walktest-w3/measure_plan_prompt.py`) is committed so the next
session can re-check rather than assume.

Gates: server 793/793 (was 788; +5 in test_llm_adapters.py), web 285/285
unchanged (this task moved no web code), tsc clean, build ok; trace 48/48,
e2e 28/28. `graphify update .` ran clean.

**Next: nothing is queued.** Every phase the roadmap asked for is delivered,
all three walk-test findings are closed, and the W3X-003 follow-up this queued
task existed for is done. W3X-001 (a filename accepted twice by the Data
panel) is recorded as an observation, unqueued because its frequency is
unmeasured — the cheapest guard if it repeats is a same-filename refusal
naming the existing dataset. Two things outside this repo's control, unchanged:
GitHub Actions still refuses every job (billing suspended, so CI never ran on
any W3X commit; v0.3.5 was built and verified locally from the same steps
`release.yml` runs), and the packaged app is unsigned by DEC-006.

Gates now: web 285/285, tsc clean, build ok; server 793/793, trace 48/48,
e2e 28/28.

## Recent completions

## Next action

**WALK-UX-004 is done: both W3X fixes held, and the walk-test found the one
thing no suite could.** The fourth walk-test ran the full loop on a new
domain (B2B SaaS renewals, 3,000 seeded rows) with the same slow provider W3
measured, and answered the two questions it existed for: the LLM plan
answered in 12.4 seconds with `source: llm` (W3: 120 seconds and a
deterministic fallback), and the Python panel's contract turned the naive
analyst's first interaction from three blind refusals into zero — the first
run used `dataset.rows` straight from the page and returned a 201.

The run's one finding was the regression the fix it validated had
introduced: W3X-003-PROMPT's shrunken prompt no longer asks for
`context_basis`, `validate_plan` treats the field as optional, and
`PlanPanel` read it unconditionally — so a case with an LLM plan could not
be reopened, the whole workspace blanking with a TypeError. W4X-001 guards
the field, marks it optional in the type, and adds one test; the prompt,
validator and deterministic planner are untouched, because the shrink is
what keeps the plan inside the budget and this is its cost, paid on the
client. Verified live: the case reopened and rendered `by llm for
saas_renewals_2026.csv`.

**Next: nothing is queued.** Every phase is delivered, all four walk-test 3
findings are closed, and their fixes are now validated in an analyst's
hands. W3X-001 (a filename accepted twice) stays an unmeasured observation;
the same Data panel accepted the same name four times in this run's failed
attach attempts, all from the harness's own file-synthesis path, so a human
selecting a file twice is still the only way to reach it. Two things
outside this repo's control, unchanged: GitHub Actions still refuses every
job (billing), and the packaged app is unsigned by DEC-006.

**v0.3.6 is the release the W3X fixes and this fix ship in.**

Gates now: web 285/285, tsc clean, build ok; server 793/793, trace 48/48,
e2e 28/28.

## Recent completions

## Next action

**WALK-UX-005 is done, and it upgraded one observation to a task.** The
fifth walk-test had one question — can a human reach W3X-001 (the Data
panel accepting the same filename twice), or is it only an artefact of the
harness synthesising a `File`? — and the answer is measured: **a human can
reach it, and it needs a fix.** A real file on disk, attached a second time
through the same file input a human re-selecting a file uses, was accepted
silently: `POST .../datasets -> 201 in 39ms` with no warning, "Data sources:
2", two dataset rows with the identical filename, and every panel that
labels by filename left ambiguous. W3 recorded this as an observation
because its second attach came from a synthesised `File`; W5 reproduced it
through the real input path, so the frequency is now "every time the same
file is attached twice to one case".

The queued task is **W5X-001** (contract in `ai/TASKS.md`): a same-filename
refusal with a full sentence naming the existing dataset, matching how
`POST /cases` answers a duplicate question+dataset. The endpoint keeps no
duplicate check for filename within a case today; only case creation does.
Cheapest guard, no dedupe, no silent behaviour change.

Everything else held, on a new retail-inventory domain with no terminal:
the LLM plan answered in **6.5 seconds** with `source: llm` (W4: 12.4s; W3:
120s timeout), the Python contract was used with zero refusals, the case
reopened after the loop and rendered its LLM plan (W4X-001 did not
regress), and the finding validated honestly as `insufficient_evidence` so
`loop_closed` stayed false — the contract behaving, not a failure.

**Next: W5X-001 is the only open task.** Its acceptance criteria are written;
the walk-test material is the measured record.

Gates now: web 286/286, tsc clean, build ok; server 793/793, trace 48/48,
e2e 28/28. No code changed this walk-test, so the gate numbers carried from
v0.3.6.

## Recent completions
