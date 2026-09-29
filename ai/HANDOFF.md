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

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
