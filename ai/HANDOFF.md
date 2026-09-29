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

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
