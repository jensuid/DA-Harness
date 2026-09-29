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

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **W3X-003-PROMPT, the plan prompt's output size** - the walk-test measured a plan call that consumed all 120s and fell back deterministically, and the live measurement explained it: the prompt asked for the largest output of the six adapters and the provider runs at ~10-13 tok/s. `LLMPlanner.prompt` is now the text `plan` posts, on its own so a test can pin it, and it asks for at most 4 sub-questions / 3 hypotheses / 4 steps / 3 data requirements with one short clause per string. A live re-measurement answered 508 tokens in 52.3s (`finish_reason: stop`) instead of timing out. The validator's ceilings are untouched, so the request shrank the wait without shrinking what an engine may answer. Five tests pin it. Gates: server 793/793, web 285/285 unchanged, tsc clean, build ok, trace 48/48, e2e 28/28.

- **W3X-002, the fallback sentence glued to its label** - a panel that appends its own context to `sourceLabel` was gluing a lowercase fragment to a sentence that already ends with a period, and the substitution notice read as a typo. `sourceWith` capitalises the join; the sentences, the server's wording and the panels that render the label alone are untouched. Seven tests, one asserting the measured shape is absent. Gates: web 285/285, tsc clean, build ok, server 788/788, trace 48/48, e2e 28/28.

- **W3X-004, the Python surface refuses and teaches nothing** - the sandbox's own contract now sits on the panel that runs against it: the handle (`dataset.rows`), the importable subset with pandas/csv/numpy named as refused and `statistics` as the alternative, no file path, and the `result` shape a run takes. The placeholder is the canonical use, not `# python`. Six tests, one comparing the panel's module list to `_SAFE_MODULES` in the Python source. Shell-only; the sandbox, the endpoints and the refusal messages are untouched. Gates: web 278/278, tsc clean, build ok, server 788/788, trace 48/48, e2e 28/28.
- **WALK-UX-003, the third walk-test** - a complete end-to-end run on a new domain (SaaS helpdesk, seeded, six planted anomalies) with a real LLM and a live Chromium on an isolated data dir. The loop closed through the UI alone: attach, profile, plan, SQL, Python, chart, interpret, draft, validate, the reviewer's audit, chat, implications, export, and a reopen that kept all of it. Four findings (`walktest-w3/FINDINGS.md`), none a blocker: the fallback sentence is glued to its label (W3X-002), the Python surface refuses three times and teaches nothing (W3X-004), the plan call burns the whole 120s budget (W3X-003), and a filename accepted twice (W3X-001, a harness artifact). Nine W2X fixes confirmed still holding. Gates: server 788/788, web 272/272, tsc clean, build ok, e2e 28/28, trace 48/48.
- **v0.3.5, the release the fixes shipped in** - the v0.3.4 tag was hollow (it pointed at a version bump; every W2X fix landed after it) and the desktop version files had drifted from the core's, so a 0.3.4 core shipped in an app calling itself 0.3.3. `server/pyproject.toml`, `desktop/src-tauri/tauri.conf.json` and `desktop/package.json` move to 0.3.5 together, the sidecar is repackaged (`/updates/latest` answers 0.3.5) and the DMG rebuilt from that bundle. Gates: server 788/788, web 272/272, tsc clean; the packaged app was smoke-tested as a real launch, not just built.
- **W2X-010, the duplicate that said nothing** - `POST /cases` carries a `duplicate_of` when the question+dataset pair already exists (migration 14), the create form answers with a warn-toned sentence and a link, and the list row names the case it repeats.
- **W2X-011, the row that only opened at its text** - the Open button spanned the row's width but only its own text height, so the blank part of the row was the container, not the button. A flex stretch makes the whole row one button instead of adding a second listener.
- **W2X-003, the chart that vanishes on reopen** - the drawing was local state
  a remount resets, and the panel it sat in only mounted once the analyst
  showed the rows. The run row now reads its charts on mount and reads the
  rows unprompted when it has one.
- **W2X-004, the false unsaved-edits claim** - the finding named the Context panel; the Context panel was already correct. The Decision panel's implications editor derived `dirty` from a join comparison, so a parent reload handing it a fresh view object read as an edit. An `edited` flag now tracks the gesture instead.
- **W2X-009, the outlier promotion** - two profile readers in main.py never selected quality_json, so the entire analysis path saw an empty quality list and the deterministic draft crowned the planted 99589.5 the profile had already flagged at 758.6x. Both readers now carry it, and the draft names the outlier and steps down to the largest remaining group.
- **W2X-001, the timeout surface** - the wait stopped being one word: a hook
- **W2X-008 + W2X-013, the density** - the case page's 13.1 viewports: a
- **W2X-002 + W2X-005, the first-thing-the-app-says** - the new-case form
- **W2X-006 + W2X-007, the analysis editor** - the proposal's `<pre>` is now a
- **W2X-012 phase B** - the settings surface: `dah-llm.json` in the shell's
- **WALK-UX-002 (recorded, not fixed)** - the second walk-test, the first
- **v0.3.4** - the close-out: the DMG bundler's non-determinism traced to the
- **P9-F4-001** - the on-screen chart: recharts draws the same stored result
- **P9-F3-001** - the motion layer: three transitions and three variants, a
- **P9-F2-002** - the restyle: every panel and screen renders through the
- **P9-F2-001** - the walk-test's last three findings: a run now appears in
- **P9-F1-001** - the redesign's foundation: the toolchain installed and
- **FIX-PYTHON-005** - the python run surface: the codegen panel offers an
