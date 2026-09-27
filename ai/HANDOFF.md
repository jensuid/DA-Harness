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

**Next, in priority order:**

1. **W2X-012, the design decision.** Read the three sites -
   `server/dah-core.spec` (bundled data), `server/app/main.py` (env loading),
   `desktop/src-tauri/src/core_server.rs` (the child env) - then decide how
   a credential reaches the sidecar and how the shell knows whether it did.
   A review first, implementation after the go-ahead.
2. **W2X-007 + W2X-006, the analysis editor.** The two are one surface: a
   textarea where the generated code is shown and edited, posting to the
   endpoints that already exist (`/runs`, the sandbox). W2X-006 is that
   textarea replacing `<pre>`; W2X-007 is the same component answering the
   stage guidance's "Run an analysis."
3. **W2X-002 and W2X-005, the two small UX fixes** - inline required-field
   message, and a real action instead of a raw endpoint string.
4. **W2X-008, the density.** Largest effort, and the user's original
   complaint. Hide empty panels, collapse completed stages, narrow the
   orientation zone to rail + overview + next action.
5. **W2X-001, W2X-009, then the five MINORs.**

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **W2X-012 phase A** - the status surface: the core answers `GET
  /llm/status`, one boot line names the engine in play, and a banner says
  what the analyst is actually getting. The degradation stops being silent;
  the credential still does not reach the packaged app, which is phase B.
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
  the motion does not run. Twelve tests, and the disclosure the measurement
  layer times is inside its budget with the motion in the tree.
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
