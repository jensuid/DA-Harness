## Next action

**UI-REDUX is done: the shell's surfaces, type and buttons now carry hierarchy
and give feedback.** Phase 1 and phase 2 of the audit in
`docs/UI-UX Audit & Redesign Plan.md` landed: a base button system (hover
shift, one-pixel press, transitions, a filled `primary` variant for each
screen's one verb), the bundled Geist face with a display-weight h1, the
quality severity ramp and every shadow remapped onto the shell's own tokens,
the workflow rail as a connected spine, accent-tinted anchor surfaces for the
rail and the decision, a skip-to-content link, and favicon plus document
metadata. `lucide-react` (declared, imported nowhere) is gone.

Verified in a real Chrome over CDP against a real core on an isolated data
dir, reading computed styles rather than source: the body resolves
`Geist, system-ui, sans-serif` with `document.fonts.check('16px Geist')`
true, a real pointer move moves a button's background to the accent surface,
and the link-styled next-action keeps its transparent hover. The one subtlety
worth carrying: `button.link` keeps its link character on hover by source
order (it is defined after the base `button:hover`), but `.next-action-link`
is a class lower in specificity and needed its own `background: none` on
hover or the base rule painted a tint box behind inline link text.

**Next: DMDARK, dark mode as a token swap** - the contract is written and
sitting in `ai/TASKS.md`, including the decision made with the analyst: a
three-state Light / Dark / System control (System by default) as a new
Appearance row in the existing DAH Settings dialog, driven by ONE mechanism -
a `data-theme` attribute on `<html>` resolved from `matchMedia`, with no
`@media` block racing the class. Phase 3's other three items (skeleton
loaders, zone composition, iconography) are documented in the audit's section
9 and are not started.

The visual verification harness now lives in `verification/visual/` -
`verify_visual.py` starts an isolated core on 8124, seeds a case, serves the
bundle, and drives Chrome over CDP; `drive_chrome.js` has a `shots` mode and a
`verify` mode that reads the browser's COMPUTED styles. Run it before
claiming a surface changed. It is verified working from its new home: every
UI-REDUX assertion reproduces. It refuses to start if 8124 is busy, because a
core already there would answer the health check and a seeded case would
land in its store - the running app's own core owns 8123.

Gates now: server 796/796, web 287/287, tsc clean, build ok.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **UI-REDUX, the shell's visual and interaction craft** - phase 1 and 2 of the audit in `docs/UI-UX Audit & Redesign Plan.md`: a base button system with hover/press/transition and a filled `primary` variant per screen's verb, the bundled Geist face with a display-weight h1, the quality ramp and shadows remapped onto the shell's tokens, the rail as a connected spine, accent-tinted anchor surfaces (rail, decision), a skip-to-content link, favicon and document metadata, and `lucide-react` removed. Verified live in Chrome over CDP on an isolated core. Phase 3 (dark mode, skeletons, zone composition, iconography) remains open. Gates: server 796/796, web 287/287, tsc clean, build ok.
- **v0.3.7, the release W5X-001 ships in** - all three version files moved together, the sidecar repackaged so the stamp the spec writes is 0.3.7, and the DMG rebuilt from that bundle (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119). Smoke-tested as a real launch: health ok, and the packaged core's own `/updates/latest` answers `current: 0.3.7`, so the Check for Updates item reads this release's number. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **W5X-001, the Data panel's duplicate filename** - the attach endpoint refuses a filename already attached to the case before it writes the file, answering 409 with a sentence naming the existing dataset and how to replace it. The check is per-case, so another case may still attach the same filename, and case creation's duplicate handling is untouched. The panel's existing `Attach failed:` surface renders the sentence, so no UI changed. Three server tests and one web test pin it. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **WALK-UX-005, the fifth walk-test** - a focused validation of the one open observation: W3X-001 (the Data panel accepts the same filename twice). A real file on disk, attached a second time through the same file input, was accepted silently (201 in 39ms, no warning, "Data sources: 2"), so the observation became a MAJOR finding with measured frequency - queued as W5X-001, now closed. Everything else held: the LLM plan answered in 6.5s with `source: llm`, the Python contract was used with zero refusals, and the case reopened with its LLM plan intact. Material and the harness's honest limits are in `walktest-w5/FINDINGS.md`.
- **WALK-UX-004, the fourth walk-test** - a validation run on a new domain with the same slow provider: the plan answered in 12.4s as an LLM (W3: 120s timeout and fallback), and the Python surface's first interaction went from three blind refusals to zero. Its one finding was a regression W3X-003-PROMPT introduced: PlanPanel read the optional `context_basis` unconditionally, so a case with an LLM plan could not be reopened. Fixed as W4X-001, verified live in the same run.
- **W4X-001, the plan panel's optional field** - a two-line guard for a bug every test fixture inoculated against: each one supplies `context_basis`, so the suite could not see it, and only reopening a real case with a real LLM plan could. Gates: web 286/286 (one test added), tsc clean, build ok; server unchanged.
- **v0.3.6, the release the W3X fixes ship in** - all three version files moved together, the sidecar repackaged so `/updates/latest` answers 0.3.6, and the DMG rebuilt from that bundle. Smoke-tested as a real launch: health ok, the case list and Templates render, the core exits with the shell. Gates: server 793/793, web 286/285 (five timing tests timed out under a parallel server run and re-ran green in isolation), tsc clean, build ok, trace 48/48, e2e 28/28.
- **W3X-003-PROMPT, the plan prompt's output size** - the walk-test measured a plan call that consumed the whole 120s budget and fell back deterministically, and the live measurement explained it: the prompt asked for the largest output of the six adapters and the provider runs at ~10-13 tok/s. The fix moved the request, not the contract, and a live re-measurement answered 508 tokens in 52.3s with `finish_reason: stop`. Five tests pin it.
- **W3X-002, the fallback sentence glued to its label** - a panel that appends its own context to `sourceLabel` was gluing a lowercase fragment to a sentence that already ends with a period. `sourceWith` capitalises the join; the sentences and the server's wording are untouched. Seven tests.
- **W3X-004, the Python surface refuses and teaches nothing** - the sandbox's own contract now sits on the panel that runs against it: the handle, the importable subset with the refused modules named, no file path, and the `result` shape. Six tests.
