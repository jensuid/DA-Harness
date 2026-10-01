## Next action

**ICON is done and pushed** - the audit's open icon question is closed
typographically: `MARKS` in `web/src/lib/ui.tsx` names the shell's five
statuses to their glyphs and `Mark` renders the one treatment a mark that
stands alone gets, so no component outside that file names a glyph
character. A drawn set was declined measured - status is text-plus-glyph by
contract (AT-32), so an `aria-hidden` drawn mark needs a duplicated label to
carry what the sentence already states; DEC-001 bars a package; and the app
has no icon-shaped slots, only buttons that already name their verb. The
inventory showed an unowned vocabulary, not the wrong medium: `concern` had
two glyphs, an unvalidated finding read as the stage the loop is on (`●`
where it means pending), and a pending agent step sat on an amber chip. All
three now read the one glyph and the one colour their status owns.

Criterion 4 was pixel-measured against a stashed pre-ICON baseline: the
settled workspace differs by 857 px (light) / 1395 px (dark) out of 2.1M -
0.041% / 0.061% - and every changed cell is one column wide, the rail's seven
rungs. No layout moved. The visual harness gained a `.mark` probe read
through the cascade, so each mark's token resolution is measured in both
appearances (12 new checks, 78 total).

**Next: phase 3's last item, zone composition (11)** - the position the plan
left it in, because it migrates panel roots from `<div>` to
`<section>`/`<aside>`, the largest test surface in the phase, done last and
per-panel. Read `docs/UI-UX Audit & Redesign Plan.md` around line 229 for the
scope (Chat's position in the intelligence zone is bundled with it). After
that the plan's phase 3 is closed and the next phase is its own roadmap
entry. No carried follow-up is open and no walk-test finding is queued.

Gates now: web 320/320, tsc clean, build ok, visual verify green in both
appearances (78 checks, +12 mark/token), server 796/796.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **SKEL, skeleton loaders** - one `Skeleton` component in `web/src/lib/ui.tsx` (five shapes composed from the surfaces the panels already render) and one `.skeleton` rule in `web/src/index.css` reading `--color-surface-muted` with a `--color-skeleton-shimmer` sweep, one keyframe, gated through `prefers-reduced-motion`. Each waiting panel keeps its sentence (`visually-hidden`, so assistive tech still announces it) and renders the shape it will fill; panels that read workspace-owned state take a new `loading` prop from one `CaseWorkspace` flag that is true only until the first `load()` resolves, so no panel flashes its skeleton at every save. CaseOverview stopped rendering zeros while unread; Evidence stopped rendering nothing; Plan stopped offering to plan a case the shell had not read. Measured: 13 new visual checks in both appearances, the gate read through Chrome's emulator, one composition test freezing case open in its first beat (twelve panels, each in the shape it will fill), and a pre-SKEL vs post-SKEL pixel diff of zero changed pixels in every settled workspace shot. Gates: web 312/312 (+11), tsc clean, build ok, visual verify green both appearances, server 796/796.
- **DMDARK, dark mode as a token swap** - a `data-theme` attribute on `<html>` driven by `web/src/theme.ts` (Light / Dark / System, System default, localStorage, live OS re-resolution), a single `[data-theme='dark']` token block, every component colour moved onto the tokens so the panels follow, a bootstrap that sets the attribute before first paint, and an Appearance row in the settings dialog. Light measured byte-identical; 53 visual checks green in both appearances with contrast measured per surface; six dark shots captured. Gates: web 301/301, tsc clean, build ok, visual verify green in both appearances, server 796/796 unchanged.
- **UI-REDUX, the shell's visual and interaction craft** - phase 1 and 2 of the audit in `docs/UI-UX Audit & Redesign Plan.md`: a base button system with hover/press/transition and a filled `primary` variant per screen's verb, the bundled Geist face with a display-weight h1, the quality ramp and shadows remapped onto the shell's tokens, the rail as a connected spine, accent-tinted anchor surfaces (rail, decision), a skip-to-content link, favicon and document metadata, and `lucide-react` removed. Verified live in Chrome over CDP on an isolated core. Phase 3 (dark mode and skeletons done; zone composition, iconography) remains open. Gates: server 796/796, web 287/287, tsc clean, build ok.
- **v0.3.7, the release W5X-001 ships in** - all three version files moved together, the sidecar repackaged so the stamp the spec writes is 0.3.7, and the DMG rebuilt from that bundle (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119). Smoke-tested as a real launch: health ok, and the packaged core's own `/updates/latest` answers `current: 0.3.7`, so the Check for Updates item reads this release's number. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **W5X-001, the Data panel's duplicate filename** - the attach endpoint refuses a filename already attached to the case before it writes the file, answering 409 with a sentence naming the existing dataset and how to replace it. The check is per-case, so another case may still attach the same filename, and case creation's duplicate handling is untouched. The panel's existing `Attach failed:` surface renders the sentence, so no UI changed. Three server tests and one web test pin it. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
