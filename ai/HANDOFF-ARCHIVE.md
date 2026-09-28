The archive of `ai/HANDOFF.md`'s `## Next action` sections. Each section is
moved here verbatim, never edited or summarised, when the task that wrote it
completes - it is the record of what a session thought mattered before it
knew how it would end.

---

## W2X-012 phase B

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

**Two defects found by the measure gate and fixed in the same commit:** the
AT-38 line counter imported every app module before pytest registered, so
`configure_logging()` installed a real file handler into the repo; and the new
config tests leaked `os.environ` into other suites, so `test_refine` made a
real LLM call and failed on a hostname lookup. The first is a pre-existing
runner bug, the second is the tests this task wrote.

Reading this is not part of resuming; `ai/HANDOFF.md` is.

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
