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

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
