# DAH — UI/UX Audit & Redesign Plan

**Artifact:** Scan & diagnosis (redesign-existing-projects skill)
**Date:** 2025-09-30
**Scope:** `web/` (React 18 + TypeScript + Vite 6 + Tailwind v4), `desktop/` (Tauri 2 shell)
**Mode:** Diagnosis only. No code changed.

---

## 1. Executive summary

DAH's web shell is unusually disciplined for a generated frontend: a real token layer,
a motion budget with a `prefers-reduced-motion` gate, a zero-dependency structural
accessibility audit, inline error and empty states everywhere, and prose that
deliberately avoids cliché. The architecture (three-zone workspace, sticky workflow
rail, state-based navigation) already matches the "modern analytical workspace" thesis
in `docs/UX- UI Architecture.md`.

The weaknesses are **visual craft and interaction feedback**, not structure:

1. **The primary button is dead** — no hover, no press feedback, no transition. Minor
   buttons and case rows react; the most important actions ("New case", "Ask", "Save")
   do not. Highest-impact fix.
2. **Typography has no character** — `system-ui` (the browser default), a single
   display size at `1.5rem`, no letter-spacing work, no `text-wrap: balance` on the
   long user-written headings that dominate the app.
3. **Two gray families and two reds** — the shell's neutral palette is clean and
   consistent, but the data-quality block imports Material Design colors
   (`#202124`, `#5f6368`, `#9aa0a6`, `#b3261e`) that clash with it.
4. **Every surface looks identical** — one `0.4rem` radius, one hairline border, one
   white. Nothing says "this panel is the anchor" or "this is the loop's exit." The
   workflow rail — the app's orientation spine — renders as a bulleted list rather
   than a connected step ladder.
5. **Dead dependency and missing document metadata** — `lucide-react` is declared in
   `package.json` but imported nowhere; `index.html` has no favicon, description, or
   theme-color.

The fix plan (§9) respects the project's hard constraints: **DEC-001** (no new
browser-side dependencies that touch the filesystem or DuckDB; a bundled webfont is
fine), **AT-32** (0 critical a11y violations; the tests are the contract), the **motion
budget** (AT-27's 200ms interaction response, AT-30's visible state), and the rule that
a panel's rendered output is a contract the test suite asserts on.

---

## 2. Stack and surface inventory

| Layer | Technology |
|---|---|
| Framework | React 18.3 + TypeScript 5.6, Vite 6 |
| Styling | Tailwind v4 (CSS-first: `@import "tailwindcss"`, no config file) **coexisting with** hand-written CSS in `web/src/index.css` |
| Design system | `web/src/lib/ui.tsx` — `tokens`, `surfaces`, `Button`/`Panel`/`Card` primitives (CVA-typed variants) |
| Motion | framer-motion 13 via `web/src/lib/motion.tsx` (`MotionSurface`, `ReducedMotion` gate) |
| Charts | recharts 3 (`web/src/lib/chart.tsx`) + core-generated inline SVG fallback |
| Icons | **`lucide-react` 1.48 — declared, imported nowhere** |
| Desktop | Tauri 2, single 1280×800 window, `dah-core` sidecar binary, `com.jensuid.dah` |
| Navigation | State-based (`View` union in `App.tsx`): `list` / `create` / `workspace`; no router |
| Views | `CaseList`, `CaseCreation`, `CaseWorkspace` (three-zone grid) + global `NoticeLayer`, `LlmStatusBanner`, `LlmSettingsPanel` |
| Panels | 20 in `web/src/panels/` plus `ContextPanel`, `DecisionPanel`, `RefinePanel`, `Chat` |

Styling debt is self-documented: `lib/ui.tsx` states "F1 ships this and uses it nowhere;
F2 pays the debt." Only `WorkflowRail` explicitly migrated to the token layer; every
other panel composes `surfaces.panel` (which still contains the raw `panel` class), so
`index.css` and Tailwind remain two systems in one stylesheet.

---

## 3. Typography

**Already right:** body width is constrained (`max-width: 48rem`); monospace is used
consistently for code, chips, EDA tables and verdicts; headers are sentence case.

| # | Finding | Evidence | Severity |
|---|---|---|---|
| T1 | **Browser default font stack.** `font-family: system-ui, sans-serif` carries no character or brand. | `index.css:37` | High |
| T2 | **Weak display hierarchy.** `h1` = `1.5rem`, panel heading = `1.1rem`. The workspace `h1` is a long user-written case question and nothing on the page has presence. | `h1 {}`, `surfaces.heading` | High |
| T3 | **No letter-spacing discipline.** No negative tracking on headings, no positive tracking on the small `.note` labels. | absent | Medium |
| T4 | **Only 400 / 600 / 700 in use.** No Medium (500) for intermediate hierarchy, though the workspace has five heading levels. | `index.css`, `surfaces` | Medium |
| T5 | **No `text-wrap` anywhere.** Long case questions orphan single words onto a last line; the overview's weighted facts wrap freely. | absent | Medium |
| T6 | **Tabular figures used once.** Only `.call-progress p` sets `font-variant-numeric: tabular-nums`. CaseOverview's artifact counts and the rail's stage list are numeric and proportional. | `index.css:896` | Low |

**Fixes:** bundle a webfont with character (Geist, Outfit, Cabinet Grotesk or Satoshi —
all bundleable as static assets, satisfying DEC-001's offline rule). Raise the workspace
`h1` toward a display size with tightened tracking and `text-wrap: balance`. Add a 500
weight for sub-labels. Extend `tabular-nums` to overview counts and the rail.

---

## 4. Color and surfaces

**Already right:** `#fafafa`/`#ffffff` off-white base (not pure black), a single
desaturated accent (`#4a6fa5`), one neutral gray family for the shell, three status
tokens (ok/warn/danger) pairing ink with tint, and deliberate avoidance of the purple
"AI gradient" aesthetic.

| # | Finding | Evidence | Severity |
|---|---|---|---|
| C1 | **Two gray families.** The data-quality block uses Material grays (`#202124`, `#5f6368`, `#9aa0a6`, `#f1f3f4`) alongside the shell's `#1a1a1a` / `#666` / `#ddd` / `#f4f4f4`. Two gray families read as copy-paste. | `.quality-*` rules | High |
| C2 | **Two reds for one meaning.** `.quality-issue.severity-high` uses `#b3261e` + `#fdecea` while `.danger` uses `#a03a2a` + `#faf0ee` — same semantics, different red. | `index.css` | Medium |
| C3 | **Untinted shadows.** `.llm-settings`, `.shell-notice` and `.llm-status` use pure-black shadows (`rgba(0,0,0,0.18)` / `0.08`, overlay `0.35`). They should carry the background's hue. | `index.css` | Low |
| C4 | **Zero texture or depth.** Flat white panels with hairline borders and no layering. Defensible for an IDE-like workspace, but the result is that every surface weighs the same. | `surfaces.panel` | Medium |
| C5 | **No dark mode.** The tokens are named so "dark is a swap of these same names," but the swap does not exist and `prefers-color-scheme` is never read. Long analytical sessions in a desktop app commonly expect it. | `index.css:12` comment | Medium (opportunity) |
| C6 | **Uniform radius.** `0.4rem` on panels, cards and buttons; `1rem` on chips and verdicts. No variation — the audit wants tighter inner elements and softer containers. | `--radius`, `surfaces` | Low |

**Fixes:** remap `.quality-*` onto the shell's tokens (`--color-danger`,
`--color-text`, `--color-text-muted`, `--color-border`). Tint shadows toward a cool dark
(`rgba(20,30,50,…)`) instead of pure black. Vary radius by level. Implement the dark
theme as the token swap the architecture already anticipates.

---

## 5. Layout

**Already right:** a container constraint (`48rem`, `90rem` wide), an asymmetric
three-column grid (not equal cards), a sticky workflow rail (UX 5), CSS Grid rather
than flexbox math, a `64rem` collapse-to-one-column breakpoint, and a reserved
`min-height` on the chart container so a dropped recharts frame cannot collapse it.

| # | Finding | Evidence | Severity |
|---|---|---|---|
| L1 | **Identical surfaces flatten the hierarchy.** The rail, the overview, the decision panel and every minor picker are the same card. The loop's exit (`DecisionPanel`) carries no visual distinction from a column picker. | `surfaces.panel` | High |
| L2 | **The workflow rail reads as a bulleted list, not a spine.** Stage marks are text glyphs (`✓ ⚠ ● ○`) with no connecting rule between steps, so progress is not perceived as a ladder. | `WorkflowRail.tsx`, `.stage` | High |
| L3 | **Density vs. the thesis.** The orientation zone stacks rail + overview + refine + record group; the work zone stacks 7 panels; the intelligence zone stacks 5 with Chat last. `docs/UX- UI Architecture.md` explicitly warns against information overload. W2X-008 already collapsed three panels into a disclosure group. | `CaseWorkspace.tsx` | Medium |
| L4 | **Chat sits below the fold** in the right zone, though the copilot is a thesis-level element of the mental model. | intelligence zone | Medium |
| L5 | **Symmetrical vertical padding** (`margin: 2rem auto`) — optical adjustment usually wants slightly more at the bottom. | `main` | Low |
| L6 | No inner constraint inside the wide workspace; very wide monitors stretch panels edge-to-edge within the `90rem` cap. | `main.wide` | Low |

**Fixes:** differentiate anchor surfaces (rail, decision) with a tinted background or a
stronger left rule rather than more borders. Connect the rail's stages with a vertical
rule so the ladder reads at a glance. Consider moving Chat above the agent panels or
pinning a compact input.

---

## 6. Interactivity and states

**Already right:** a guaranteed `:focus-visible` ring (asserted by
`focusIsGuaranteed()`), inline `role="alert"` errors on every async surface, inline
field validation (W2X-002), composed empty states ("No cases yet — create one.",
"Profile a dataset first"), `CallProgress` with an elapsed timer and a stop button
rather than a bare spinner, disabled-while-busy as visible state, smooth-scroll on the
rail's "Go to panel" links, and a motion layer that animates only `transform`/`opacity`
behind a reduced-motion gate with explicit `animation: none` fallbacks.

| # | Finding | Evidence | Severity |
|---|---|---|---|
| I1 | **The primary button has no hover, no press feedback and no transition.** The base `button` rule sets padding and cursor only; hover exists on `.case-open`, `button.danger` and `.collapse-toggle` — three sites out of the whole app. The most-used actions feel inert. | `index.css button {}` | **Highest** |
| I2 | **No active/pressed state anywhere** — no `scale(0.98)` or `translateY(1px)`. | absent | High |
| I3 | **Flat button hierarchy.** Four variants (default/link/small/danger); primary ("Ask", "Save", "New case") and secondary ("Rename", "Duplicate") look near-identical. No filled-vs-ghost distinction. | `buttonVariants` | High |
| I4 | **No skeleton loaders.** Loading is a sentence ("Loading…", "Asking…"). Intentional and screen-reader-friendly, but a workspace that loads ~12 artifacts on case open could shape-match its panels. | `CaseWorkspace.load()` | Medium |
| I5 | **No skip-to-content link**, though `<main>` is the landmark and keyboard users tab through a sticky rail and many panels before reaching content. | absent | Medium |
| I6 | `scroll-behavior: smooth` is set inline per click only; the document has no rule, so any other jump is instant. | `index.css` lacks `html { scroll-behavior }` | Low |
| I7 | **No keyboard shortcuts or command palette.** The IDE-like thesis points at a `⌘K`-style menu, which the docs name as a sidebar alternative. | absent | Opportunity |

**Fixes:** give the base button a hover background shift, a `transform` press, and a
200–250ms transition — inside the motion budget, extending the existing reduced-motion
rules to cover it. Add a filled "primary" and a ghost variant so the one action that
matters per panel reads as such. Add a skip link.

---

## 7. Content, components, iconography

**Already right:** copy is plain and specific — no "Elevate / Seamless / Unleash /
Next-Gen", no "Oops!", no exclamation marks; headers are sentence case; placeholder
text is real draft copy ("How many datasets does this case have?"); status is carried
by text and glyph, never colour alone (pinned by `auditStatusNotColorOnly`).

| # | Finding | Evidence | Severity |
|---|---|---|---|
| P1 | **`lucide-react` is a dead dependency** — declared in `package.json`, imported in zero `src/` files. The app is effectively icon-less (status uses text glyphs). Either remove it or adopt it deliberately. | grep `lucide` in `src/` = 0 hits | High |
| P2 | **No favicon or document metadata.** The Tauri bundle ships `icons/icon.icns` for the OS, but `index.html` has no `<link rel="icon">`, no `<meta name="description">`, no `theme-color`, no `og:*`. | `web/index.html` | Medium |
| P3 | **Pill-shaped monospace badges.** `.chip` (`border-radius: 1rem`) and `.verdict` (1rem) are the pill "New/Beta" pattern the audit flags; squarer badges would read as data rather than marketing. | `index.css` | Low |
| P4 | **Div-soup in panels.** `<main>` and `<section aria-label>` are used well, but most panels are `<div className={surfaces.panel}>`, the zones lack `<aside>` semantics, and `<nav>`/`<header>`/`<footer>` appear nowhere. | grep of semantic tags | Medium |
| P5 | **Two styling systems in one stylesheet.** Hand-written `.panel`, `.chip`, `.case`, `.stage`, `.eda` rules coexist with the Tailwind token layer; the F2 migration is partial. This is the stated plan, but it is why a restyle can need two edits in two places. | `index.css` + `lib/ui.tsx` | Medium (process) |

**Fixes:** decide the icon question — if adopting icons, the audit recommends Phosphor or
Heroicons over Lucide for differentiation, but check DEC-001 before adding a package;
`lucide-react` is already installed and bundleable. Add document metadata and a favicon
generated from the existing Tauri icon. Migrate panel roots toward `<section>`/`<aside>`.

---

## 8. Strategic omissions and accessibility

| # | Finding | Severity |
|---|---|---|
| S1 | **No skip-to-content link** (see I5). | Medium |
| S2 | **No dark mode / theme preference** (see C5) — the token layer was designed for exactly this swap. | Medium |
| S3 | Legal links, cookie consent, custom 404: **not applicable** — state-based navigation in a local desktop app with no routes and no network tracking. Deliberately out of scope. | N/A |
| S4 | **Contrast remains a manual item.** `accessibility.ts` is honest: it audits structure, not computed contrast. Muted `#666` on `#fafafa` (about 5.7:1) passes AA for body text, but the small `.note` at `0.9rem` sits close to the boundary and should be measured. | Low |
| S5 | **Chart accessibility:** the recharts tree is reached via `data-testid='chart-tree'` with a reserved `min-height` and a core-SVG fallback — good practice, with tooltip/hover coverage tested. Confirm the core's inline SVG carries an accessible name (`<title>`/`aria-label`). | Low |

---

## 9. Prioritized fix plan

Ordered by the skill's "biggest visual impact, minimum risk" principle, adapted to this
stack. Each item names the files it touches.

### Phase 1 — High impact, low risk (do first)

1. **Button feedback (I1, I2, I3)** — `web/src/index.css` base `button` rule plus
   `buttonVariants` in `web/src/lib/ui.tsx`. Add a hover background shift, an
   `active:scale(0.98)` press, and a 200ms transition; add a filled `primary` and a
   `ghost` variant. Extend the existing `prefers-reduced-motion` block to cover it.
   Biggest single improvement; touches no panel logic.
2. **Font swap (T1, T2, T4)** — bundle a webfont as a static asset under `web/public/`,
   reference it in `index.css`, and set the workspace `h1` to a display size with
   tightened tracking. Re-run the a11y audit after, since font-size changes can shift
   the `.note` contrast boundary (S4).
3. **Palette consolidation (C1, C2)** — remap the `.quality-*` rules onto
   `--color-danger` / `--color-text` / `--color-text-muted` in `index.css`. Purely
   visual; no DOM changes, so no test churn.
4. **Document metadata and favicon (P2)** — `web/index.html`; derive the favicon from
   `desktop/src-tauri/icons/`.

### Phase 2 — Hierarchy and craft

5. **Workflow rail as a spine (L2)** — `WorkflowRail.tsx` + a `.stage` connector rule in
   `index.css`: a vertical line through the marks so the ladder reads as progress.
   Keep the text glyphs; they are what makes status screen-reader-safe.
6. **Anchor surfaces (L1, C6)** — differentiate the rail and `DecisionPanel` with a
   tinted background (`tokens.accentSurface`) and varied radius rather than new borders.
   Introduces a filled `primary` button from step 1 to mark the loop's exit.
7. **Heading polish (T3, T5, T6)** — letter-spacing on headings and `.note` labels;
   `text-wrap: balance` on `h1` and the overview's weighted facts; `tabular-nums` on
   CaseOverview counts and the rail.
8. **Skip link (I5, S1)** — one link in `App.tsx` targeting `<main id="content">`;
   styled with the existing `.visually-hidden` pattern.

### Phase 3 — Considered, larger

9. **Dark mode (C5, S2)** — the token layer anticipates it; implement as a
   `prefers-color-scheme` (or Tauri theme) swap of the same names. Verify the status
   tokens and the `.quality-*` remap both survive the swap.
10. **Skeleton loaders (I4)** — shape-matched per panel behind the existing sentence
    states, gated through the same reduced-motion rule.
11. **Zone composition (L3, L4, P4)** — P4 RESOLVED as ZONE-A: every panel
    root is now a `<section aria-labelledby>` named by the `<h2>` it already
    rendered, so a reader navigating by region finds the zones *and* the
    fourteen panels inside them (a `<div>` carried no role). The ids come from
    `useId`, so the two mounted `AgentPanel`s keep distinct names. The three
    zones stay labelled `<section>` — `<aside>` was declined, measured: the
    zones' names (orientation / work / intelligence) are the mental model the
    workspace is built on, and a named region is a better navigation surface
    than an unnamed complementary one; the work zone is the page's primary
    content. `<header>` wraps the two mastheads that already existed
    (workspace and case list); `<nav>`/`<footer>` were declined — the shell
    has no link set and no footer content, so either would be semantic
    washing. The three panels nested in a `Disclosure` (Learn, History,
    PromoteTemplate) keep their `<div>` root on purpose: the disclosure is
    already the named region, so a second one inside it would name the same
    thing twice. The swap was geometry-neutral by construction (no class,
    text or CSS change) and measured: four of six shots byte-identical, and
    the settled workspace's full-page shot identical in both appearances.
    STILL OPEN as ZONE-B: L3 (the zones' density) and L4 (Chat below the fold
    in the intelligence zone). RESOLVED as ZONE-B. L4: the copilot moved to the
    top of the intelligence zone (Chat, then Context, then the two agents) —
    open question 4 above records the §2/§8/§22 reasoning, and the move is a
    reorder, never an enlargement, because §22 says the copilot must not
    dominate. L3: the density is grouped, not spaced away — the architecture's
    own principles ("visual grouping: related information should appear
    physically together", "progressive disclosure, not information overload";
    §1's thesis lists "Modern IDE + Notion-like workspace + analytical notebook
    + AI copilot") are served by putting the flat stacks into surfaced groups so
    a zone reads as two or three blocks instead of seven equal cards. A
    disclosure collapse was measured as unavailable here: every work-zone panel
    is a rail anchor (`#data`, `#plan`, `#runs`, `#findings`, `#evaluate`), so a
    collapsed group would send "Go to the Evaluate panel" to a hidden surface,
    and ZONE-A's landed contract makes each panel a named `<section>` region
    while W2X-008's rule makes a Disclosure-nested panel a `<div>` — the two
    cannot both hold. So the groups are visual: a `.zone-group` block that
    holds its panels the way `.record-group` already holds the case's record,
    and the panels inside keep their region, their heading id and their
    `.panel` class. Grouped: Plan + EDA (the two "what to look at" surfaces over
    the profile), Evaluate + Evidence (the two "what backs the claim" review
    surfaces), and the two agents (one mechanism in two roles).
12. **Iconography decision (P1)** — RESOLVED (typographic): `lucide-react` was
    removed in UI-REDUX, and the audit's open question is closed in favour of
    text glyphs formalized as one vocabulary - `MARKS` in `web/src/lib/ui.tsx`
    names the shell's five statuses (pass / concern / fail / current /
    pending) and `Mark` renders the one treatment for a mark that stands
    alone. A drawn set was declined measured: status is text-plus-glyph by
    contract (AT-32), so an `aria-hidden` drawn mark needs a duplicated label
    to carry what the sentence already states; DEC-001 bars a package; and the
    app has no icon-shaped slots - verb icons would restate the verb every
    button already names. What the inventory showed was an unowned vocabulary,
    not the wrong medium: `concern` had two glyphs (`!` in the audit's chips,
    `⚠` elsewhere), the unvalidated finding read as the stage the loop is on
    (`●`), and a pending step sat on an amber chip. All three now read the one
    glyph and the one colour their status owns. Marks inside a sentence stay
    text nodes (`getByText` joins only direct text children, so wrapping them
    would break the contract tests).

### Explicitly not in scope

- Marketing-page patterns the audit lists but this app does not have: footer link
  farms, testimonial carousels, pricing towers, accordion FAQs, cookie consent,
  custom 404 (S3). Judged N/A rather than missed.
- Whitespace doubling ("let the design breathe") — conflicts with the data-density the
  thesis requires. Applied per-panel in Phase 2 instead of globally.
- Any change to panel contracts, API calls, or rendered text that the test suite
  asserts on — those are the contract, not styling.

---

## 10. Constraints to honor while fixing

- **DEC-001**: no new dependency that touches the filesystem or DuckDB from the
  browser. A bundled webfont or icon set is a static asset, not a dependency on this
  rule — but check before adding any package.
- **AT-32**: `web/src/accessibility.ts` audits structure; `0 critical violations` is
  the target. Re-run `npm test` after every phase. Status must stay text-plus-glyph.
- **Motion budget (AT-27/AT-30)**: every transition stays inside the 200ms interaction
  budget; the `prefers-reduced-motion` gate in `lib/motion.tsx` and the explicit
  `animation: none` blocks in `index.css` must be extended to cover anything new.
- **Tests are the contract**: panels assert on rendered output (`heading.closest('.panel')`,
  `data-testid` values, sentence text). A restyle must not change DOM text or the
  `.panel` class name; it restyles around them.
- **Green state only**: no commit until the suite passes; the `ai/` docs get updated
  in the same commit as any change (see `AGENTS.md`).

---

## 11. Open questions

1. **Icons or not?** RESOLVED — typographic. See phase 3 item 12 above for the
   measured reasoning and the vocabulary that replaced the ad-hoc glyphs.
2. **Dark mode priority.** The token layer is ready, but is a theme toggle a user need
   for this product, or polish? The docs name "Modern IDE" as the reference, which
   argues for it.
3. **Webfont choice.** Geist and Outfit are the closest fits to an IDE/analytical
   aesthetic; a serif header pairing suits "Notion-like" but may clash with monospace
   data. Needs a decision before Phase 1 item 2.
4. **Chat placement (L4).** RESOLVED (ZONE-B) — the copilot sits at the **top** of
   the intelligence zone: Chat first, then Context, then the two agents. Three
   readings of the architecture decided it, and the first is the one that made
   it a decision rather than a preference. (a) `docs/UX-UI Architecture.md` §2's
   diagram has **no copilot node**: its nodes are the three inputs (CONTEXT,
   DATA, QUESTION) and the loop's seven stages. The copilot is not a stage and
   not an input; it is the per-stage support that answers "What should I do
   next?" — one of the three questions §2 says the user must *always*
   understand. A surface answering an always-question cannot sit below the
   fold of the zone that exists to answer it. (b) §8 lists the intelligence
   zone's contents with "AI assistance" first, before "context" and before
   "suggestions"; the layout had that inverted (Context, Agent, Agent, Chat),
   the AI surfaces second-to-fourth and the conversational one last. (c) §22
   constrains the copilot's *form*, not its rank: "The AI should not dominate
   the application" — so the fix is a reorder, never an enlargement. Chat
   stays a panel among panels, the same size and the same contract, no
   chatbot frame; the turn list grows downward as it does today and the two
   agents sit directly below it rather than three panels above it. §22's
   warning is about the copilot taking over the page, which a same-size panel
   in first position does not do.
   possibly its tests; worth confirming against `docs/UX- UI Architecture.md` §2's
   mental model before acting.
