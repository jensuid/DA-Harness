## Next action

**ZONE-A is done and pushed** - the semantic half of the audit's item 11
(finding P4): every panel root that carried `surfaces.panel` and was not
already inside a `Disclosure` is a `<section aria-labelledby>` named by the
`<h2>` it already rendered, so a reader navigating by region now finds the
zones *and* the fourteen panels inside them; a `<div>` carried no role. The
ids come from `useId` (the two mounted `AgentPanel`s keep distinct names),
the three zones stay labelled `<section>` (`<aside>` declined, measured), the
two mastheads gained a `<header>`, and `<nav>`/`<footer>` were declined - no
link set, no footer content. Learn, History and PromoteTemplate keep `<div>`
roots on purpose: their `Disclosure` is already the named region.

The swap was geometry-neutral by construction and measured against a
stashed baseline: four of six shots byte-identical, both full-page
workspace shots identical in both appearances, the list shot's diff
confined to the seeded case's own row band (rows 181-308, the same band the
ICON-vs-ICON same-code control reproduces) and the viewport workspace shot's
75 px all one grey-level of antialiasing. No layout moved. Five new landmark
tests assert the structure, and the zone-name regexes were anchored because
"Audit submitted work (EVALUATE)" contains the word "work". One latent
hazard fixed on the way: EvaluatePanel's hook block sat below its loading
early return, so a render that took the return skipped its hooks.

**Next: ZONE-B** - item 11's other two findings, L3 (the zones' density) and
L4 (Chat below the fold in the intelligence zone). Its contract is already
written (`ai/TASKS.md`, just after the ZONE-A block) with the acceptance
criteria, so the session starts there rather than re-deriving scope. Step 0
is a read, not a change: `docs/UX-UI Architecture.md` sec. 2, closing the
plan's open question 4 (where the mental model puts the copilot) as a
written decision before any layout moves - L3/L4 both change layout and
tests, unlike ZONE-A, and if the read says Chat belongs where it is, L4
closes as a decision and only L3 remains. With items 11 and 12 otherwise
closed, ZONE-B is the last of the plan's phase 3; after it, the next phase
is its own roadmap entry.

Gates now: web 325/325 (21 files, +5 landmark tests), tsc clean, build ok,
visual verify green in both appearances (78 checks), server 796/796.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **ZONE-A, panel landmarks** - every panel root that was not already inside a `Disclosure` is a `<section aria-labelledby>` named by the `<h2>` it already rendered, so region navigation reaches the fourteen panels, not just the three zones; `useId` keeps the two mounted `AgentPanel`s distinct. The zones stay labelled `<section>` (`<aside>` declined measured), the two mastheads gained `<header>`, `<nav>`/`<footer>` declined (no link set, no footer content), and Learn/History/PromoteTemplate keep `<div>` roots because their `Disclosure` is already the named region. Measured against a stashed baseline: four of six shots byte-identical, both full-page workspace shots identical in both appearances, the list shot's diff confined to the seeded case's row band (same band as the same-code control). Five new landmark tests; the zone-name regexes anchored. EvaluatePanel's hook block hoisted above its loading early return. Gates: web 325/325 (+5), tsc clean, build ok, visual verify green both appearances (78 checks), server 796/796.
- **SKEL, skeleton loaders** - one `Skeleton` component in `web/src/lib/ui.tsx` (five shapes composed from the surfaces the panels already render) and one `.skeleton` rule in `web/src/index.css` reading `--color-surface-muted` with a `--color-skeleton-shimmer` sweep, one keyframe, gated through `prefers-reduced-motion`. Each waiting panel keeps its sentence (`visually-hidden`, so assistive tech still announces it) and renders the shape it will fill; panels that read workspace-owned state take a new `loading` prop from one `CaseWorkspace` flag that is true only until the first `load()` resolves, so no panel flashes its skeleton at every save. CaseOverview stopped rendering zeros while unread; Evidence stopped rendering nothing; Plan stopped offering to plan a case the shell had not read. Measured: 13 new visual checks in both appearances, the gate read through Chrome's emulator, one composition test freezing case open in its first beat (twelve panels, each in the shape it will fill), and a pre-SKEL vs post-SKEL pixel diff of zero changed pixels in every settled workspace shot. Gates: web 312/312 (+11), tsc clean, build ok, visual verify green both appearances, server 796/796.
- **DMDARK, dark mode as a token swap** - a `data-theme` attribute on `<html>` driven by `web/src/theme.ts` (Light / Dark / System, System default, localStorage, live OS re-resolution), a single `[data-theme='dark']` token block, every component colour moved onto the tokens so the panels follow, a bootstrap that sets the attribute before first paint, and an Appearance row in the settings dialog. Light measured byte-identical; 53 visual checks green in both appearances with contrast measured per surface; six dark shots captured. Gates: web 301/301, tsc clean, build ok, visual verify green in both appearances, server 796/796 unchanged.
- **UI-REDUX, the shell's visual and interaction craft** - phase 1 and 2 of the audit in `docs/UI-UX Audit & Redesign Plan.md`: a base button system with hover/press/transition and a filled `primary` variant per screen's verb, the bundled Geist face with a display-weight h1, the quality ramp and shadows remapped onto the shell's tokens, the rail as a connected spine, accent-tinted anchor surfaces (rail, decision), a skip-to-content link, favicon and document metadata, and `lucide-react` removed. Verified live in Chrome over CDP on an isolated core. Phase 3 (dark mode and skeletons done; zone composition, iconography) remains open. Gates: server 796/796, web 287/287, tsc clean, build ok.
- **v0.3.7, the release W5X-001 ships in** - all three version files moved together, the sidecar repackaged so the stamp the spec writes is 0.3.7, and the DMG rebuilt from that bundle (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119). Smoke-tested as a real launch: health ok, and the packaged core's own `/updates/latest` answers `current: 0.3.7`, so the Check for Updates item reads this release's number. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
