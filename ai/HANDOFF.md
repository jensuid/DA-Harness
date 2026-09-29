## Next action

**v0.3.5 shipped: the thirteen walk-test fixes are released.** The v0.3.4 tag
was hollow - it pointed at a version bump, and every W2X fix (W2X-001 through
W2X-013) landed after it, so nothing the second walk-test found was ever in a
release. The desktop version files had also drifted: the bump commit touched
only `server/pyproject.toml`, so a 0.3.4 core shipped inside an app that called
itself 0.3.3.

This release closes both. `server/pyproject.toml`,
`desktop/src-tauri/tauri.conf.json` and `desktop/package.json` move to 0.3.5
together (the `30db6e9` convention: all three, or none), the sidecar is
repackaged so `/updates/latest` answers 0.3.5, and the DMG is rebuilt from
that bundle. The window title, the plist and the feed all agree now.

Gates at the bumped HEAD: server 788/788, web 272/272, tsc clean, desktop
build ok. The packaged app was smoke-tested as a real launch, not just built:
health ok, `/updates/latest` answers `current: 0.3.5` with an honest `unknown`
(the feed is unreachable from this machine), the case list and Templates
section render, and no test data was left behind.

**Next: nothing is queued.** All thirteen walk-test findings are closed and
released. Two things remain outside this repo's control: GitHub Actions still
refuses every job (billing suspended since before c73118c, so CI never ran on
any W2X commit - the artifact was built and verified locally from the same
steps `release.yml` runs), and the packaged app is unsigned by DEC-006.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

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
