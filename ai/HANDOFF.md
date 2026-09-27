## Next action

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

**Next, in priority order:**

1. **W2X-007 + W2X-006, the analysis editor** - one surface: an editable
   textarea replacing the `<pre>` the generated code shows, posting to the
   endpoints that already exist. The realest frustration loop in the
   walk-test.
2. **W2X-002 and W2X-005** - an inline required-field message and a real
   action instead of the raw `POST` endpoint string. Both small.
3. **W2X-008, the density.** The largest effort and the original complaint:
   hide empty panels, collapse completed stages, narrow the orientation zone.
4. **W2X-001, W2X-009, then the five MINORs.**

**Two carried decisions stay, both unchanged and both not code:** the
packaged app is unsigned by DEC-006, and GitHub Actions' billing is
suspended (fix at Settings > Billing & plans; nothing since `c73118c` has
run in CI).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **W2X-012 phase B** - the settings surface: `dah-llm.json` in the shell's
  data dir, read at boot and applied on save (no restart), `GET/PUT
  /llm/config`, a three-field panel in the bundle opened from a menu item
  through the DOM-event channel that needs no permission, and the banner's
  Configure button with a one-off refetch. The BLOCKER's credential half is
  closed; W2X-012 is done.
- **W2X-012 phase A** - the status surface: the core answers `GET
  /llm/status`, one boot line names the engine in play, and a banner says
  what the analyst is actually getting. The degradation stopped being silent;
  phase B put the fix in the analyst's hands.
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
  the motion does not run.
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
