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

**Next in priority order: W2X-010** - the last walk-test finding. The case list
shows duplicate rows for the same question and dataset without any warning at
create time, and the gap is the missing duplicate notice.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
