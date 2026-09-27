## Next action

**The second walk-test (WALK-UX-002) is recorded, and nothing was fixed.**
The last session walked the shell again as a junior analyst - the first walk
since P9's redesign landed - and found thirteen things the shipped product
still does, this time against the *designed* surfaces: 1 BLOCKER, 7 MAJOR,
5 MINOR. The walk's own summary, findings, capture sheet and phase-2 notes
are now in `walktest-w2/` (committed; its `data/` and `logs/` are gitignored
runtime state), and `ai/TASKS.md` carries the thirteen as its carried list.
This is the state the project is in: everything that was planned is
delivered, and everything open is a walk-test finding.

**The BLOCKER is the one that decides whether the product has an intelligent
layer at all.** W2X-012: the packaged app has no LLM credentials. `.env` is
gitignored so it is not bundled, `main.py` loads it relative to source - a
path that does not exist inside a PyInstaller bundle - and the shell does
not inject `DAH_LLM_API_KEY` into the sidecar. The proof is a
`POST /generate-code` in the shipped app answering `source: template` where
the dev checkout answered `by llm`. So every LLM feature silently degrades
to deterministic for the one user the app is built for. This needs a design
decision before code, not a patch - the three options (build-time secret
injection, a first-run UI prompt writing to the app data dir, or an LLM
status surface) make different trade-offs about a secret on a machine the
user controls - so propose, then implement.

**What else is open, in the walk-test's own priority order:** W2X-007/W2X-006
(no editor for the code the app generates and rejects - the single realest
frustration loop), W2X-002 (an empty-dataset submit is total silence),
W2X-001 (a two-minute LLM wait with one word on screen and no cancel),
W2X-005 (the next-action guidance shows the raw `POST` endpoint, twice),
then W2X-008 (the measured core complaint: 13.1x viewport, 18 flat panels,
12 of them empty on a new case, zero progressive disclosure - the redesign
restyled the surfaces but did not make any of them hide), W2X-009 (the
deterministic drafter promoted the planted 758x outlier as a finding), then
the five small ones. The carried list in `ai/TASKS.md` has all thirteen with
their code locations.

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
