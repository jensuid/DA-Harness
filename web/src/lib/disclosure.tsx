/**
 * W2X-008: the disclosure primitive.
 *
 * The walk measured the case page at 13.1 viewports with every panel flat -
 * no disclosures anywhere, and twelve of eighteen panels showing an empty
 * state on a case that had only just been created. A surface with nothing
 * to say should not occupy the first screen, but the shell's own discipline
 * says why it cannot simply be removed: five of those empty states are the
 * next action's own panel. So the missing thing is a disclosure that is a
 * real control, and this is it.
 *
 * Native `<details>` is not used for the workspace's groups. Its open state
 * is the browser's rather than React's, so it cannot be seeded from the
 * case's artifacts (a stage that finished collapses itself) and a test
 * cannot read what it chose. This is a `<button>` with `aria-expanded`
 * controlling a region, seeded by `defaultOpen` and then the analyst's own:
 * the state is uncontrolled on purpose, because a disclosure that re-closed
 * itself every time the case reloaded would close the thing the analyst just
 * opened. The native disclosure the rail uses for its developer info stays -
 * that one's open state is the developer's own, and nothing derives it.
 *
 * AT-32: the toggle is a `<button>`, so it is keyboard-reachable and
 * announced as a button; the region carries `role="region"` and the toggle's
 * id in `aria-controls`, so the control/region link points somewhere real;
 * and nothing here carries status by colour alone - the summary is text, and
 * the mark is decorative and hidden from the name.
 */

import { useState, type ReactNode } from 'react'

export function Disclosure({
  id,
  summary,
  defaultOpen = false,
  children,
}: {
  /** The id the region and its toggle share. A group with several disclosures
   * has to name them, or the pairs collide and `aria-controls` points at the
   * last one the DOM found. */
  id: string
  /** What the collapsed state shows: the sentence a reader scans. For the
   * workspace's groups that is the surface's name and its count, so a
   * collapsed stage still says what it holds. */
  summary: ReactNode
  /** The state on mount, so a parent that knows the case can start a
   * finished stage collapsed. After mount it is the analyst's: the case
   * reloading around the analyst does not re-close what the analyst opened. */
  defaultOpen?: boolean
  children: ReactNode
}) {
  const [open, setOpen] = useState(defaultOpen)
  const toggleId = `${id}-toggle`
  const regionId = `${id}-region`

  return (
    <div className="collapse">
      <button
        type="button"
        id={toggleId}
        className="collapse-toggle"
        aria-expanded={open}
        aria-controls={regionId}
        onClick={() => setOpen((prior) => !prior)}
      >
        <span className="collapse-mark" aria-hidden="true">
          {open ? '▾' : '▸'}
        </span>
        <span className="collapse-summary">{summary}</span>
      </button>
      {open && (
        <div
          id={regionId}
          role="region"
          aria-labelledby={toggleId}
          className="collapse-body"
        >
          {children}
        </div>
      )}
    </div>
  )
}
