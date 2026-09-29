## Next action

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

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
