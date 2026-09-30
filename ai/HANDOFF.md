## Next action

**DMDARK is done: dark mode is a token swap.** One driver (`web/src/theme.ts`)
writes `data-theme` on `<html>` and the meta `theme-color`; one mechanism (the
`[data-theme='dark']` block in `index.css`) redefines the `:root` tokens; one
control (an Appearance fieldset in the settings dialog) offers Light / Dark /
System, System by default, persisted in localStorage and re-resolved live when
the OS preference moves. Every hardcoded colour in the component rules, in
`lib/ui.tsx` and in `lib/chart.tsx` moved onto the tokens, so the panels
follow the swap - a pure CSS-var swap in `index.css` alone would not have
themed them, and that was the one finding worth carrying.

Light is byte-for-byte the appearance it was, and this was measured rather
than asserted: the visual harness's 15 computed reads and both hover reads are
identical to the pre-DMDARK baseline, and 53 checks are green with the dark
tokens resolving, contrast measured per surface in both appearances (light min
4.68:1, dark min 5.11:1, all above 4.5), the three statuses keeping their hue
families, the severity ramp keeping its climb, and a control pass that clicks
the dialog, persists a choice, flips the emulated OS and watches the attribute
re-resolve. Six dark shots are captured alongside the light set.

Two lessons for the next measurement-driven surface: assert a surface against
the token it reads, not against a hardcoded expectation - `document.body`
carries no background (it is on `<html>`) and the first `.panel` is the
accent-surface anchor, so the first two assertions measured the wrong things;
and Chrome's CSSOM does not expand a `var()` inside a shorthand, so the ramp
is measured by putting the elements on the page and reading the cascade
instead of walking `cssRules`. The reused Chrome profile keeps localStorage
between runs, so the harness clears it at the start of every run.

**Next: phase 3's remaining three items** - skeleton loaders, semantic zone
composition and iconography, documented in section 9 of
`docs/UI-UX Audit & Redesign Plan.md` and not started. Nothing else is open:
the carried follow-ups are closed and no walk-test finding is queued.

The visual harness in `verification/visual/` is the gate for any surface:
`verify_visual.py verify` starts an isolated core on 8124, seeds a case,
serves the bundle and drives Chrome over CDP, and its assertions now fail the
run (`process.exit(1)` propagates through the wrapper's `check=True`). Run it
before claiming a surface changed.

Gates now: web 301/301, tsc clean, build ok, visual verify green in both
appearances, server 796/796 (no server file changed).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **DMDARK, dark mode as a token swap** - a `data-theme` attribute on `<html>` driven by `web/src/theme.ts` (Light / Dark / System, System default, localStorage, live OS re-resolution), a single `[data-theme='dark']` token block, every component colour moved onto the tokens so the panels follow, a bootstrap that sets the attribute before first paint, and an Appearance row in the settings dialog. Light measured byte-identical; 53 visual checks green in both appearances with contrast measured per surface; six dark shots captured. Gates: web 301/301, tsc clean, build ok, visual verify green in both appearances, server 796/796 unchanged.
- **UI-REDUX, the shell's visual and interaction craft** - phase 1 and 2 of the audit in `docs/UI-UX Audit & Redesign Plan.md`: a base button system with hover/press/transition and a filled `primary` variant per screen's verb, the bundled Geist face with a display-weight h1, the quality ramp and shadows remapped onto the shell's tokens, the rail as a connected spine, accent-tinted anchor surfaces (rail, decision), a skip-to-content link, favicon and document metadata, and `lucide-react` removed. Verified live in Chrome over CDP on an isolated core. Phase 3 (dark mode done; skeletons, zone composition, iconography) remains open. Gates: server 796/796, web 287/287, tsc clean, build ok.
- **v0.3.7, the release W5X-001 ships in** - all three version files moved together, the sidecar repackaged so the stamp the spec writes is 0.3.7, and the DMG rebuilt from that bundle (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119). Smoke-tested as a real launch: health ok, and the packaged core's own `/updates/latest` answers `current: 0.3.7`, so the Check for Updates item reads this release's number. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **W5X-001, the Data panel's duplicate filename** - the attach endpoint refuses a filename already attached to the case before it writes the file, answering 409 with a sentence naming the existing dataset and how to replace it. The check is per-case, so another case may still attach the same filename, and case creation's duplicate handling is untouched. The panel's existing `Attach failed:` surface renders the sentence, so no UI changed. Three server tests and one web test pin it. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **WALK-UX-005, the fifth walk-test** - a focused validation of the one open observation: W3X-001 (the Data panel accepts the same filename twice). A real file on disk, attached a second time through the same file input, was accepted silently (201 in 39ms, no warning, "Data sources: 2"), so the observation became a MAJOR finding with measured frequency - queued as W5X-001, now closed. Everything else held: the LLM plan answered in 6.5s with `source: llm`, the Python contract was used with zero refusals, and the case reopened with its LLM plan intact. Material and the harness's honest limits are in `walktest-w5/FINDINGS.md`.
- **WALK-UX-004, the fourth walk-test** - a validation run on a new domain with the same slow provider: the plan answered in 12.4s as an LLM (W3: 120s timeout and fallback), and the Python surface's first interaction went from three blind refusals to zero. Its one finding was a regression W3X-003-PROMPT introduced: PlanPanel read the optional `context_basis` unconditionally, so a case with an LLM plan could not be reopened. Fixed as W4X-001, verified live in the same run.
- **W4X-001, the plan panel's optional field** - a two-line guard for a bug every test fixture inoculated against: each one supplies `context_basis`, so the suite could not see it, and only reopening a real case with a real LLM plan could. Gates: web 286/286 (one test added), tsc clean, build ok; server unchanged.
- **v0.3.6, the release the W3X fixes ship in** - all three version files moved together, the sidecar repackaged so `/updates/latest` answers 0.3.6, and the DMG rebuilt from that bundle. Smoke-tested as a real launch: health ok, the case list and Templates render, the core exits with the shell. Gates: server 793/793, web 286/285 (five timing tests timed out under a parallel server run and re-ran green in isolation), tsc clean, build ok, trace 48/48, e2e 28/28.
