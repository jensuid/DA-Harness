## Next action

**DMDARK is done and pushed** (`286b3fa`) - dark mode as a token swap, 53
visual checks green in both appearances, light measured byte-identical. Its
contract and its measured done-record are in `ai/TASKS.md`; the lessons worth
carrying are in the archive entry this section replaced.

**Next: SKEL, skeleton loaders** - phase 3 item 10 of
`docs/UI-UX Audit & Redesign Plan.md` (observation I4). The contract is
written and sitting in `ai/TASKS.md`; the shape of it mirrors DMDARK: ONE
mechanism (`surfaces.skeleton` in `lib/ui.tsx` + one `.skeleton` rule in
`index.css`), not a skeleton per panel; each panel wraps the shape it already
renders with the same row and wrap counts; the sentence states stay for
assistive tech (`role="status"` / `aria-busy` unchanged); the shimmer is one
animation gated through `prefers-reduced-motion` and the gate is measured; the
skeleton reads a token so `verify` is green in both appearances.

**Two decisions the contract leaves open**, and they are the only things to
confirm before writing code: whether case open loads its ~12 artifacts
concurrently or in stages (which decides one full-workspace skeleton beat
against per-panel skeletons - measure it first, the way DMDARK measured its
surfaces), and whether to shimmer at all rather than ship a static darker
surface. Lean shimmer-with-gate: one animation, and the gate is the
constraint that makes it safe.

Phase 3's other two items stay queued after SKEL: the iconography decision
(item 12) before zone composition (item 11), because stage marks may become
icons and zone composition migrates panel roots from `<div>` to
`<section>`/`<aside>` - the largest test surface, deliberately last and
per-panel. No carried follow-up is open and no walk-test finding is queued.

Gates now: web 301/301, tsc clean, build ok, visual verify green in both
appearances, server 796/796.

## Recent completions## Recent completions

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
