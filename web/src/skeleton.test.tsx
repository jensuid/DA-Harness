// SKEL (I4): the contract pins the mechanism, not its appearance - one
// component, one CSS rule, one animation, one gate, and the sentence the shape
// stands in for still announced. What is under test here is the mechanism's
// invariants, because those are what the panels and the appearance swap rely
// on: a shape is the geometry its panel will render, the sentence is not
// removed, the animation is one keyframe with one gate, and the surface reads
// the tokens rather than a hex.

import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import './index.css'

import { Skeleton } from './lib/ui'
import { WorkflowRail } from './panels/WorkflowRail'
import { CaseOverview } from './panels/CaseOverview'
import { RunsPanel } from './panels/RunsPanel'
import { EvidencePanel } from './panels/EvidencePanel'

function styles(): string {
  return Array.from(document.querySelectorAll('style'))
    .map((style) => style.textContent ?? '')
    .join('\n')
}

describe('the waiting surface', () => {
  it('renders the shape it was asked for, and only that shape', () => {
    const shapes: Array<Parameters<typeof Skeleton>[0]['shape']> = [
      'rows',
      'stages',
      'facts',
      'table',
      'form',
    ]
    for (const shape of shapes) {
      const { container, unmount } = render(<Skeleton shape={shape} />)
      const root = container.querySelector(`[data-skeleton="${shape}"]`)
      // Each shape carries its own name, so a panel that asks for a shape the
      // file does not have is a new shape the shell does not render.
      expect(root, `${shape} did not mark its root`).not.toBeNull()
      expect(root!.querySelectorAll('.skeleton').length).toBeGreaterThan(0)
      expect(container.querySelectorAll('[data-skeleton]').length).toBe(1)
      unmount()
    }
  })

  it('renders the count it was given, or the shape own default', () => {
    const { container, unmount } = render(<Skeleton shape="rows" count={5} />)
    expect(container.querySelectorAll('li').length).toBe(5)
    unmount()
    // The default is the shape's own size - the rail's seven stages - so a
    // panel that cannot count its real rows still waits in the right shape.
    const two = render(<Skeleton shape="stages" />)
    expect(two.container.querySelectorAll('li.stage').length).toBe(7)
  })

  it('keeps the shape out of the accessibility tree', () => {
    // The sentence beside the shape is what assistive tech announces; bars it
    // would then announce twice are decoration, and `aria-hidden` is how a
    // purely visual stand-in says so.
    render(<Skeleton shape="rows" />)
    const shape = document.querySelector('[data-skeleton="rows"]')
    expect(shape).not.toBeNull()
    expect(shape).toHaveAttribute('aria-hidden', 'true')
  })
})

describe('the sentence the shape stands in for', () => {
  it('stays in the DOM while the rail waits', () => {
    // The panel's contract is unchanged - the sentence is what it rendered
    // before this task - so a screen reader that announced "Loading workflow…"
    // still announces it.
    render(<WorkflowRail progress={null} qualityWarning={false} />)
    expect(screen.getByText(/Loading workflow/i)).toBeInTheDocument()
    expect(screen.getByText(/Loading workflow/i)).toHaveClass('visually-hidden')
    expect(document.querySelector('[data-skeleton="stages"]')).not.toBeNull()
  })

  it('stays in the DOM while the overview waits', () => {
    // Without a skeleton this panel renders zeros for every count - a young
    // case and an unread case read the same, which is the I4 observation. The
    // shape separates them, and the sentence stays.
    render(
      <CaseOverview
        question="what happened"
        purpose=""
        progress={null}
        datasets={0}
        findings={0}
        openIssues={0}
        pendingValidation={0}
        pending={['a finding', 'an audit']}
      />,
    )
    expect(screen.getByText(/Reading the case/i)).toBeInTheDocument()
    expect(document.querySelector('[data-skeleton="facts"]')).not.toBeNull()
    // The counts the shape stands in for are not rendered as zeros while the
    // read is in flight.
    expect(screen.queryByText(/^0$/)).not.toBeInTheDocument()
  })

  it('stays in the DOM while a workspace-owned panel waits', () => {
    render(<RunsPanel caseId="c" runs={[]} datasets={[]} loading={true} onChanged={() => {}} />)
    expect(screen.getByText(/Reading the runs/i)).toBeInTheDocument()
    expect(document.querySelector('[data-skeleton="rows"]')).not.toBeNull()
  })

  it('stays in the DOM while a panel that renders nothing waits', () => {
    // Evidence renders `null` once the graph answers empty; while the read is
    // in flight it renders the shape, so the panel is not absent while the
    // overview points at it.
    render(<EvidencePanel evidence={null} error={null} empty={false} loading={true} />)
    expect(screen.getByText(/Reading the evidence/i)).toBeInTheDocument()
    expect(document.querySelector('[data-skeleton="rows"]')).not.toBeNull()
  })

  it("gives way to the panel's own sentence once the read lands", () => {
    // The loading state is the workspace's, not the panel's forever: the flag
    // clears and the panel's real empty state is the sentence an analyst reads.
    render(<RunsPanel caseId="c" runs={[]} datasets={[]} loading={false} onChanged={() => {}} />)
    expect(screen.getByText(/No analysis has run yet/i)).toBeInTheDocument()
    expect(document.querySelector('[data-skeleton]')).toBeNull()
  })
})

describe('the surface and its gate', () => {
  it('is one rule reading the tokens, in both appearances', () => {
    const css = styles()
    // The bar is the muted surface the shell already uses, and the sweep is a
    // named overlay rather than a hex, so the appearance swap carries both the
    // way it carries every other surface.
    expect(/\.skeleton\s*\{[^}]*--color-surface-muted/s.test(css)).toBe(true)
    expect(/--color-skeleton-shimmer:\s*rgba\(/.test(css)).toBe(true)
    // The token is defined for dark too: a token that resolves only in light
    // is a light-only skeleton.
    const dark = css.indexOf("[data-theme='dark']")
    expect(css.indexOf('--color-skeleton-shimmer', dark)).toBeGreaterThan(dark)
  })

  it('is one animation, and the reduced-motion rule stops it', () => {
    const css = styles()
    const sweep = /@keyframes\s+skeleton-sweep\s*\{/
    expect(sweep.test(css), 'no skeleton-sweep keyframes').toBe(true)
    expect(/\.skeleton\s*\{[^}]*animation:\s*skeleton-sweep/.test(css)).toBe(true)
    // AT-30's budget is one animation for this whole task; a second keyframe
    // is a second animation and this rule stops only the first.
    const keyframes = css.match(/@keyframes\s+skeleton-\w+/g) ?? []
    expect(keyframes).toHaveLength(1)
    // The gate: reduced motion stops the sweep, and the muted bar alone still
    // reads as waiting. The rule is what keeps that promise when the animation
    // engine is absent.
    const reduced =
      /@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)\s*\{[^}]*\.skeleton\s*\{[^}]*animation:\s*none/s
    expect(reduced.test(css), 'no reduced-motion rule stops the sweep').toBe(true)
  })
})
