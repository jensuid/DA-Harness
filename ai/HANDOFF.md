## Next action

**ZONE-B is done and pushed** - the layout half of the audit's item 11,
findings L3 and L4. L4: the copilot moved to the **top** of the
intelligence zone (Chat, then Context, then the two `AgentPanel`s).
`docs/UX-UI Architecture.md` sec. 2 settled it as a decision rather than a
preference: the mental-model diagram has no copilot node because the copilot
answers "What should I do next?" - one of the three always-questions - so it
cannot sit below the fold; sec. 8 lists "AI assistance" first in the zone;
sec. 22 constrains its form ("must not dominate"), not its rank. Open
question 4 in the plan is closed with that reasoning.

L3 closed through grouping, not disclosure: a new `.zone-group` block
modelled on `.record-group` gathers Plan + EDA (the explore pair), Evaluate +
Evidence (the review pair) and the two agents (one mechanism in two roles).
The wrapper carries no `panel` class because the workspace reaches a panel
through `heading.closest('.panel')`; collapse was measured unavailable and
declined, because every work-zone panel is a rail anchor and ZONE-A's landed
contract conflicts with W2X-008's Disclosure rule.

Measured against a stashed pre-ZONE-B baseline, with a same-code control to
separate the change from the harness's variance: the masthead unchanged to
the pixel, the orientation zone 10-13 px of one grey-level antialiasing, the
whole intended diff inside the work and intelligence zones, and both
full-page shots 23 px shorter (the grouping removing duplicate borders and
padding). The list shots differ only in the seeded case's own row band,
which the same-code control reproduces identically on an unchanged tree -
the isolated core's random case id, not layout. Five new composition tests
assert the copilot's rank, the three groups, the group-is-not-a-panel floor
and that a grouped panel keeps its named `<section>`.

**Next: nothing is queued.** Item 11's four findings are all landed (P4 via
ZONE-A, P1 via ICON, L3 and L4 via ZONE-B), so the plan's phase 3 is
complete. The next work is its own roadmap entry, not an open item.

Gates now: web 330/330 (21 files, +5 composition tests), tsc clean, build ok,
visual verify green in both appearances (78 checks, 0 fail), server 796/796,
trace 48/48, e2e ALL PASS.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **ZONE-B, zone composition** - the layout half of the audit's item 11. The copilot moved to the top of the intelligence zone (Chat, then Context, then the two `AgentPanel`s), decided by `docs/UX-UI Architecture.md` sec. 2: the copilot answers "What should I do next?", one of the three always-questions, so it cannot sit below the fold; sec. 8 lists "AI assistance" first in the zone; sec. 22 constrains form, not rank. Density closed through grouping, not disclosure: a new `.zone-group` block (modelled on `.record-group`) gathers Plan + EDA, Evaluate + Evidence and the two agents. The wrapper carries no `panel` class because panels are reached through `heading.closest('.panel')`; collapse was declined (every work-zone panel is a rail anchor; ZONE-A's `<section>` contract conflicts with W2X-008's Disclosure rule). Measured against a stashed baseline with a same-code control: masthead unchanged to the pixel, orientation zone 10-13 px of antialiasing, the intended diff confined to the work and intelligence zones, both full-page shots 23 px shorter; the list shots' diff is the seeded case's row band, reproduced identically by the control. Five new composition tests. Gates: web 330/330 (+5), tsc clean, build ok, visual verify green both appearances (78 checks), server 796/796, trace 48/48, e2e ALL PASS.
- **ZONE-A, panel landmarks** - every panel root that was not already inside a `Disclosure` is a `<section aria-labelledby>` named by the `<h2>` it already rendered, so region navigation reaches the fourteen panels, not just the three zones; `useId` keeps the two mounted `AgentPanel`s distinct. The zones stay labelled `<section>` (`<aside>` declined measured), the two mastheads gained `<header>`, `<nav>`/`<footer>` declined (no link set, no footer content), and Learn/History/PromoteTemplate keep `<div>` roots because their `Disclosure` is already the named region. Measured against a stashed baseline: four of six shots byte-identical, both full-page workspace shots identical in both appearances, the list shot's diff confined to the seeded case's row band (same band as the same-code control). Five new landmark tests; the zone-name regexes anchored. EvaluatePanel's hook block hoisted above its loading early return. Gates: web 325/325 (+5), tsc clean, build ok, visual verify green both appearances (78 checks), server 796/796.
- **SKEL, skeleton loaders** - one `Skeleton` component in `web/src/lib/ui.tsx` (five shapes composed from the surfaces the panels already render) and one `.skeleton` rule in `web/src/index.css` reading `--color-surface-muted` with a `--color-skeleton-shimmer` sweep, one keyframe, gated through `prefers-reduced-motion`. Each waiting panel keeps its sentence (`visually-hidden`, so assistive tech still announces it) and renders the shape it will fill; panels that read workspace-owned state take a new `loading` prop from one `CaseWorkspace` flag that is true only until the first `load()` resolves, so no panel flashes its skeleton at every save. CaseOverview stopped rendering zeros while unread; Evidence stopped rendering nothing; Plan stopped offering to plan a case the shell had not read. Measured: 13 new visual checks in both appearances, the gate read through Chrome's emulator, one composition test freezing case open in its first beat (twelve panels, each in the shape it will fill), and a pre-SKEL vs post-SKEL pixel diff of zero changed pixels in every settled workspace shot. Gates: web 312/312 (+11), tsc clean, build ok, visual verify green both appearances, server 796/796.
- **DMDARK, dark mode as a token swap** - a `data-theme` attribute on `<html>` driven by `web/src/theme.ts` (Light / Dark / System, System default, localStorage, live OS re-resolution), a single `[data-theme='dark']` token block, every component colour moved onto the tokens so the panels follow, a bootstrap that sets the attribute before first paint, and an Appearance row in the settings dialog. Light measured byte-identical; 53 visual checks green in both appearances with contrast measured per surface; six dark shots captured. Gates: web 301/301, tsc clean, build ok, visual verify green in both appearances, server 796/796 unchanged.
- **UI-REDUX, the shell's visual and interaction craft** - phase 1 and 2 of the audit in `docs/UI-UX Audit & Redesign Plan.md`: a base button system with hover/press/transition and a filled `primary` variant per screen's verb, the bundled Geist face with a display-weight h1, the quality ramp and shadows remapped onto the shell's tokens, the rail as a connected spine, accent-tinted anchor surfaces (rail, decision), a skip-to-content link, favicon and document metadata, and `lucide-react` removed. Verified live in Chrome over CDP on an isolated core. Phase 3 (dark mode and skeletons done; zone composition, iconography) remains open. Gates: server 796/796, web 287/287, tsc clean, build ok.
- **v0.3.7, the release W5X-001 ships in** - all three version files moved together, the sidecar repackaged so the stamp the spec writes is 0.3.7, and the DMG rebuilt from that bundle (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119). Smoke-tested as a real launch: health ok, and the packaged core's own `/updates/latest` answers `current: 0.3.7`, so the Check for Updates item reads this release's number. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
