/**
 * The design system's foundation (P9-F1-001).
 *
 * Two things live here, and neither is a styled component yet: the light
 * theme as named tokens, and the primitives the panels will be built on in
 * F2. The values are the palette the hand-written CSS already used, named
 * rather than invented - the CSS stayed because it was a good light theme,
 * and because dark is a swap of these same names rather than a second theme
 * to maintain.
 *
 * F1 ships this and uses it nowhere; F2 pays the debt.
 */

import type { PropsWithChildren, ElementType, ButtonHTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'

// The tokens are plain class strings so a className composes them without a
// runtime dependency on a styled library. DEC-001's "no new dependency" is
// about the browser contract - the frontend never touches the filesystem or
// DuckDB directly - and a class vocabulary does not touch it.
//
// DMDARK: every colour here reads the custom properties `index.css` owns, so
// the appearance swap is the whole of dark mode and this vocabulary does not
// need a second, dark copy of itself. The arbitrary values are the same names
// the stylesheet declares, and the light values are exactly the ones these
// classes held inline, so light is the appearance it was.
export const tokens = {
  // The page and the surfaces on it.
  bg: 'bg-[var(--color-bg)]',
  surface: 'bg-[var(--color-surface)]',
  surfaceMuted: 'bg-[var(--color-surface-muted)]',
  // The hairlines that separate them.
  border: 'border-[var(--color-border)]',
  // The ink.
  text: 'text-[var(--color-text)]',
  textMuted: 'text-[var(--color-text-muted)]',
  // The one accent the current CSS uses for its rules and links.
  accent: 'text-[var(--color-accent)]',
  accentText: 'text-[var(--color-accent-text)]',
  accentRule: 'border-[var(--color-accent)]',
  accentSurface: 'bg-[var(--color-accent-surface)]',
  // The three statuses DAH renders as text-plus-chip, never as colour alone
  // (accessibility.ts's STATUS_CLASSES audit pins this). Each is a pair: the
  // ink and the tint it sits on, so a chip reads at any size.
  ok: {
    text: 'text-[var(--color-ok)]',
    bg: 'bg-[var(--color-ok-bg)]',
    border: 'border-[var(--color-ok-border)]',
  },
  warn: {
    text: 'text-[var(--color-warn)]',
    bg: 'bg-[var(--color-warn-bg)]',
    border: 'border-[var(--color-warn-border)]',
  },
  danger: {
    text: 'text-[var(--color-danger)]',
    bg: 'bg-[var(--color-danger-bg)]',
    border: 'border-[var(--color-danger-border)]',
  },
  // The page's hairline rules and the borders a panel draws between its own
  // parts are two different weights on purpose: a panel's own separator is
  // lighter than the panel's own border, so a group inside reads as inside.
  hairline: 'border-[var(--color-hairline)]',
} as const

// The composed surfaces the panels build on. A panel is a card with a border
// and a heading; the strings here are the whole style so a panel reads one
// name and the decision is made once for all of them.
//
// The rule for every string here: it is the CSS rule it replaces, as utility
// classes, with the same values and the same specificity behaviour. Nothing is
// restyled and nothing is invented - a panel that moves onto a token renders
// what the CSS rule it replaced rendered. The values are the ones the tokens
// above name, so the palette stays one set of names in one file.
export const surfaces = {
  // The panel: the bordered card every surface in the workspace is built on.
  // `my-4` is the margin a panel carries outside the three zones; inside a
  // zone `.zone .panel { margin: 0 }` cancels it (the zone's gap does that job
  // instead), which is why the margin stays here rather than being dropped.
  // The word `panel` stays in the class because the panel is a structural
  // landmark, not only a style: the workspace's own tests reach a panel with
  // `heading.closest('.panel')` and the zone CSS scopes to `.zone .panel`.
  panel:
    'panel border border-[var(--color-border)] rounded-[0.4rem] bg-[var(--color-surface)] p-4 my-4 ' +
    tokens.text,
  // A panel whose own list is its body: the panel's padding already frames it,
  // so the list is flush rather than indented, and the margins below the
  // hairline rule are the same every list had (my-2).
  panelList: 'list-none p-0 m-0 my-2',
  // A panel's heading and its sub-headings, replacing `.panel h2/h3/h4`. The
  // sizes are the ones the old rules set; the selector is gone with them.
  heading: 'text-[1.1rem] m-0 mb-2 ' + tokens.text,
  subheading: 'text-[1rem] mt-4 mb-1 ' + tokens.text,
  labelheading: 'text-[0.95rem] m-0 mb-1.4 ' + tokens.text,
  body: 'text-sm ' + tokens.textMuted,
  // `.muted`: a muted line is smaller than the body around it, and the old
  // rule set both. Note carries the size with the colour, so 92 sites stay
  // what they were (D2).
  note: 'text-[0.9rem] ' + tokens.textMuted,
  // A panel's own separator and the block it opens below it. The old rule
  // set no display, so a `subpanel` div was a block; a `label` needs `block`
  // explicitly or a border-top stretches with the label's inline width
  // (RefinePanel, ContextPanel).
  subpanel: 'block border-t border-[var(--color-hairline)] mt-3 pt-3',
  // A proposal or a rationale: the accent's left rule marks it as the panel's
  // own support rather than another paragraph (W-009). `.rationale` is the
  // same surface with its own tighter padding; both are the one accent rule.
  proposal:
    'border-l-[3px] ' + tokens.accentRule + ' ' + tokens.accentSurface + ' p-2 px-3 my-2',
  rationale:
    'border-l-[3px] ' + tokens.accentRule + ' ' + tokens.accentSurface + ' p-2 px-3 mt-3 mb-2',
  card: 'border border-[var(--color-border)] rounded-[0.4rem] bg-[var(--color-surface)] p-3 ' + tokens.text,
  // A run row and a chat turn are separated by hairlines, not by margins. The
  // turn keeps its own name because the padding it carries (0.75rem) is
  // tighter than a run row's (0.5rem), and both are what the CSS set.
  row: 'py-2 border-t border-[var(--color-hairline)]',
  turn: 'py-3 border-t border-[var(--color-hairline)]',
  // A form's control row: a flex gap with the vertical margin the CSS set.
  rowGap: 'flex gap-2 my-4',
  // The case list's action row: flex with wrap (the buttons are short and
  // narrow screens stack them), and no margin, because the container above
  // already carries its own.
  buttonRow: 'flex flex-wrap gap-2 mt-2',
} as const

// The four button shapes the current CSS defines: `button`, `button.link`,
// `button.small` and `button.danger`, plus `primary` (UI-REDUX I3). class-variance-authority types the
// variants so a typo is a compile error rather than an unstyled button.
// `button` is the shape everything renders when no variant is named, and it
// carries the base rule's own properties so a bare `<Button>` is the button
// the CSS used to draw (D4).
export const buttonVariants = cva('button', {
  variants: {
    variant: {
      default: 'mt-4 px-4 py-2',
      // I3: the one action a panel asks for. Filled with the accent so the
      // loop's next step and the screens' primary verbs stop sharing a shape
      // with Rename and Cancel - the shape is the hierarchy the panels lost
      // when every button looked alike.
      primary: 'mt-4 px-4 py-2 primary',
      link: 'link',
      small: 'small',
      danger: 'danger',
      smallDanger: 'small danger',
    },
  },
  defaultVariants: { variant: 'default' },
})

export type ButtonVariantProps = VariantProps<typeof buttonVariants>

/**
 * The panel primitive: a bordered card with a heading and a body.
 *
 * Every surface in the workspace is a panel; F2 rebuilds each one on this
 * rather than on its own `<section className="panel">`, so the border, the
 * radius and the padding are one decision rather than thirty.
 */
export function Panel({
  children,
  className,
  as: Tag = 'section',
  ...rest
}: PropsWithChildren<{
  className?: string
  // A panel is a section by default; a form or an aside is still a panel.
  as?: ElementType
}>) {
  return (
    <Tag className={className ?? 'panel'} {...rest}>
      {children}
    </Tag>
  )
}

/**
 * The button primitive: the four shapes the CSS has today, typed.
 *
 * `type="button"` is the default because a panel's button that submits a
 * form it is not part of is a bug that reads as a page reload. A button that
 * passes no className takes its variant's own classes, so the base shape is
 * the variant instead of a class a panel has to remember.
 */
export function Button({
  variant,
  className,
  type = 'button',
  ...rest
}: ButtonVariantProps & ButtonHTMLAttributes<HTMLButtonElement>) {
  return (
    <button
      type={type}
      className={className ?? buttonVariants({ variant })}
      {...rest}
    />
  )
}

/**
 * The card primitive: a panel whose content is a titled block. The case list
 * rows and the run rows are cards; the workspace's surfaces are panels.
 */
export function Card({
  children,
  className,
  as: Tag = 'section',
  ...rest
}: PropsWithChildren<{
  className?: string
  as?: ElementType
}>) {
  return (
    <Tag className={className ?? 'panel'} {...rest}>
      {children}
    </Tag>
  )
}

/**
 * SKEL (I4): the one waiting surface.
 *
 * Loading is a sentence today, and the sentence stays - it is what assistive
 * tech announces, and removing it would make the wait silent. What the eye
 * gets is this: the shape the panel is about to render, built from the same
 * surfaces and the same row classes the real content uses, so a waiting panel
 * occupies the room its data will and nothing reflows when the data lands.
 *
 * ONE mechanism, the way DMDARK taught: one component, one CSS rule, one
 * animation. The shapes are the geometries the workspace already owns - a
 * list of rows, the rail's rungs, the overview's facts, a table, a form - and
 * each panel passes the count it will render, so a waiting shape cannot
 * disagree with the data that replaces it. A shape this file does not know
 * is a new shape the shell does not have.
 */
export type SkeletonShape = 'rows' | 'stages' | 'facts' | 'table' | 'form'

// The count a shape renders when the panel does not know its own yet - the
// rail's seven stages, the overview's seven facts, three rows or three
// fields. These are the shapes' own sizes, not guesses: a panel that can
// count its real rows passes them.
const SKELETON_COUNT: Record<SkeletonShape, number> = {
  rows: 3,
  stages: 7,
  facts: 7,
  table: 4,
  form: 3,
}

// One bar of a waiting shape. `.skeleton` (index.css) is the animated surface
// and the token read; the classes a caller adds are the bar's size alone, so
// the shape is the geometry the real content will occupy.
function Bar({ className = '' }: { className?: string }) {
  return <span className={'skeleton ' + className} />
}

const BAR = 'h-[0.85rem] rounded-[0.2rem]'

export function Skeleton({
  shape = 'rows',
  count,
  className,
}: {
  shape?: SkeletonShape
  count?: number
  className?: string
}) {
  const n = count ?? SKELETON_COUNT[shape]
  const items = Array.from({ length: n }, (_, i) => i)
  // The shape is presentational. The sentence beside it is what assistive
  // tech announces - it stays in the DOM, visually hidden - and a reader who
  // hears "loading" followed by a list of bars gains nothing from the bars.
  return (
    <div className={className} aria-hidden="true" data-skeleton={shape}>
      {shape === 'rows' && (
        // A case row, a run row, a timeline event, a finding: a hairline-
        // separated row carrying a line and a shorter line under it, on the
        // same `surfaces.row` the real rows separate with.
        <ul className={surfaces.panelList}>
          {items.map((i) => (
            <li key={i} className={surfaces.row}>
              <Bar className={BAR + ' w-[65%]'} />
              <Bar className={BAR + ' w-[38%] mt-[0.4rem]'} />
            </li>
          ))}
        </ul>
      )}
      {shape === 'stages' && (
        // The rail's rungs: the fixed-width mark a stage glyph sits in, then
        // the stage's name. `stage-list` draws the spine the marks mask, so
        // a waiting rail reads as the rail.
        <ul className={surfaces.panelList + ' stage-list'}>
          {items.map((i) => (
            <li key={i} className="stage">
              <Bar className="w-[1.1rem] h-[1.1rem] rounded-full" />
              <Bar className={BAR + ' w-[55%]'} />
            </li>
          ))}
        </ul>
      )}
      {shape === 'facts' && (
        // The overview: one line per fact, on the same `ul.overview` the real
        // facts tabulate. The widths alternate the way a label-and-value line
        // does, so the shape does not read as seven identical rules.
        <ul className="overview">
          {items.map((i) => (
            <li key={i}>
              <Bar className={BAR + (i % 2 === 0 ? ' w-[72%]' : ' w-[56%]')} />
            </li>
          ))}
        </ul>
      )}
      {shape === 'table' && (
        // The Data panel: a filename line, then its columns as a row of
        // cells the width of a table's, so a waiting dataset reads as the
        // overview-plus-table the profile fills in.
        <ul className={surfaces.panelList}>
          {items.map((i) => (
            <li key={i} className={surfaces.row}>
              <Bar className={BAR + ' w-[42%]'} />
              <ul className={surfaces.panelList + ' mt-[0.4rem]'}>
                {[0, 1, 2].map((cell) => (
                  <li key={cell} className="skeleton h-[0.8rem] mt-[0.3rem] rounded-[0.2rem]" />
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
      {shape === 'form' && (
        // Context, EDA, Evaluate: a label and the field under it, on the
        // subpanel's own separator so a waiting form reads as its fields.
        <ul className={surfaces.panelList}>
          {items.map((i) => (
            <li key={i} className={surfaces.subpanel}>
              <Bar className="h-[0.8rem] w-[30%] mb-[0.4rem]" />
              <Bar className="h-[2.6rem] w-full rounded-[0.35rem]" />
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
