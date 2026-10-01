## Next action

**SKEL is done and pushed** - one skeleton surface, one CSS rule, one
animation, one gate. Loading is still a sentence for assistive tech
(`visually-hidden` beside the shape, DOM text and testids untouched); what
the eye gets is the shape the panel is about to render, built from the same
`surfaces` classes. `web/src/lib/ui.tsx` gained one `Skeleton` component
(five shapes: rows / stages / facts / table / form); `web/src/index.css`
gained one `.skeleton` rule reading `--color-surface-muted` plus a new
`--color-skeleton-shimmer` token, one keyframe, and one reduced-motion block
that stops it. Contract and measured done-record are in `ai/TASKS.md`.

Both open decisions were measured and closed: the workspace's 16 reads are
9-40 ms each (368 ms wall), so case open is one beat and per-panel skeletons
fit without restructuring `load()`; and the reduced-motion gate is read
through Chrome's media emulator, where `animation-name` resolves to `none`
in both appearances. The third question the contract asked - whether the five
existing `prefers-reduced-motion` blocks should merge - was checked and left
alone: the motion suite reads them with anchored regexes, and merging is a
refactor with no measured benefit.

**Next: phase 3's last two items, iconography (12) before zone composition
(11)** - the order the plan set, because stage marks may become icons and
zone composition migrates panel roots from `<div>` to `<section>`/`<aside>`,
the largest test surface, deliberately last and per-panel. Iconography is a
decision task first: the audit's item 12 asks whether the stage marks, the
severity glyphs and the verb icons should be a drawn set or typographic, and
`lucide-react` was already removed (UI-REDUX), so a drawn set means new SVG
assets. Read `docs/UI-UX Audit & Redesign Plan.md` around line 162 before
starting. No carried follow-up is open and no walk-test finding is queued.

Gates now: web 312/312, tsc clean, build ok, visual verify green in both
appearances (66 checks, +13 skeleton/gate), server 796/796.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **SKEL, skeleton loaders** - one `Skeleton` component in `web/src/lib/ui.tsx` (five shapes composed from the surfaces the panels already render) and one `.skeleton` rule in `web/src/index.css` reading `--color-surface-muted` with a `--color-skeleton-shimmer` sweep, one keyframe, gated through `prefers-reduced-motion`. Each waiting panel keeps its sentence (`visually-hidden`, so assistive tech still announces it) and renders the shape it will fill; panels that read workspace-owned state take a new `loading` prop from one `CaseWorkspace` flag that is true only until the first `load()` resolves, so no panel flashes its skeleton at every save. CaseOverview stopped rendering zeros while unread; Evidence stopped rendering nothing; Plan stopped offering to plan a case the shell had not read. Measured: 13 new visual checks in both appearances, the gate read through Chrome's emulator, one composition test freezing case open in its first beat (twelve panels, each in the shape it will fill), and a pre-SKEL vs post-SKEL pixel diff of zero changed pixels in every settled workspace shot. Gates: web 312/312 (+11), tsc clean, build ok, visual verify green both appearances, server 796/796.
- **DMDARK, dark mode as a token swap** - a `data-theme` attribute on `<html>` driven by `web/src/theme.ts` (Light / Dark / System, System default, localStorage, live OS re-resolution), a single `[data-theme='dark']` token block, every component colour moved onto the tokens so the panels follow, a bootstrap that sets the attribute before first paint, and an Appearance row in the settings dialog. Light measured byte-identical; 53 visual checks green in both appearances with contrast measured per surface; six dark shots captured. Gates: web 301/301, tsc clean, build ok, visual verify green in both appearances, server 796/796 unchanged.
- **UI-REDUX, the shell's visual and interaction craft** - phase 1 and 2 of the audit in `docs/UI-UX Audit & Redesign Plan.md`: a base button system with hover/press/transition and a filled `primary` variant per screen's verb, the bundled Geist face with a display-weight h1, the quality ramp and shadows remapped onto the shell's tokens, the rail as a connected spine, accent-tinted anchor surfaces (rail, decision), a skip-to-content link, favicon and document metadata, and `lucide-react` removed. Verified live in Chrome over CDP on an isolated core. Phase 3 (dark mode and skeletons done; zone composition, iconography) remains open. Gates: server 796/796, web 287/287, tsc clean, build ok.
- **v0.3.7, the release W5X-001 ships in** - all three version files moved together, the sidecar repackaged so the stamp the spec writes is 0.3.7, and the DMG rebuilt from that bundle (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119). Smoke-tested as a real launch: health ok, and the packaged core's own `/updates/latest` answers `current: 0.3.7`, so the Check for Updates item reads this release's number. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **W5X-001, the Data panel's duplicate filename** - the attach endpoint refuses a filename already attached to the case before it writes the file, answering 409 with a sentence naming the existing dataset and how to replace it. The check is per-case, so another case may still attach the same filename, and case creation's duplicate handling is untouched. The panel's existing `Attach failed:` surface renders the sentence, so no UI changed. Three server tests and one web test pin it. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
