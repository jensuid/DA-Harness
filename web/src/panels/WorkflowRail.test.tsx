// W2X-005: the stage guidance answered a developer's question, not an
// analyst's. The rail's "Next" is the first thing the screen says, and it said
// `POST /cases/6a79…/datasets` - an endpoint no button performs, with a
// `{dataset_id}` placeholder the walk-test read as a bug. These tests hold the
// answer the analyst gets: a sentence naming the panel, one click to it, and
// the path still there for the reader who wanted it.

import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { type CaseProgress } from '../api'
import { WorkflowRail } from './WorkflowRail'

function progress(over: Partial<CaseProgress> = {}): CaseProgress {
  return {
    stage: 'data',
    completed: ['question'],
    stages: [
      { name: 'question', completed: true },
      { name: 'data', completed: false },
      { name: 'profile', completed: false },
    ],
    next_action: 'Attach a dataset',
    next_hint: 'CSV, Parquet or Excel - the engine reads all three.',
    next_endpoint: 'POST /cases/c1/datasets',
    loop_closed: false,
    counts: { datasets: 0, profiles: 0, plans: 0, runs: 0, findings: 0, charts: 0, validated_findings: 0, supported_findings: 0 },
    ...over,
  }
}

describe('the workflow rail (W2X-005)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // jsdom has no layout, so scrollIntoView is undefined here; the panel's own
    // guard reads the element first and only scrolls when one exists.
    vi.spyOn(window, 'scrollTo').mockImplementation(() => {})
  })

  it('shows the action as a sentence, not as a raw endpoint', () => {
    render(<WorkflowRail progress={progress()} qualityWarning={false} />)

    // The sentence reads "Next: Attach a dataset" across a strong tag; the
    // container's own text is the sentence the screen reader speaks.
    const next = screen.getByText(/attach a dataset/i)
    expect(next.closest('.next-action')?.textContent).toMatch(
      /next: attach a dataset/i,
    )
    // The path is not the headline. jsdom renders `<details>` open - it has
    // no content-visibility - so the assertion that holds in a browser is
    // that the endpoint is inside the disclosure rather than in the sentence.
    const endpoint = screen.getByText('POST /cases/c1/datasets')
    expect(endpoint.closest('details')).not.toBeNull()
    expect(endpoint.closest('.next-action')?.querySelector('summary'))
      .toHaveTextContent(/developer info/i)
  })

  it('keeps the endpoint reachable for the reader who wanted it', () => {
    render(<WorkflowRail progress={progress()} qualityWarning={false} />)

    // The disclosure is the path's home, and its summary is the affordance.
    const details = screen.getByText('POST /cases/c1/datasets').closest('details')
    expect(details?.querySelector('summary')).toHaveTextContent(/developer info/i)
  })

  it('carries the hint the core already sent', () => {
    render(<WorkflowRail progress={progress()} qualityWarning={false} />)

    expect(
      screen.getByText(/CSV, Parquet or Excel - the engine reads all three./i),
    ).toBeInTheDocument()
  })

  it('offers a button to the panel that performs the action', () => {
    render(<WorkflowRail progress={progress()} qualityWarning={false} />)

    expect(
      screen.getByRole('button', { name: /go to the data panel/i }),
    ).toBeInTheDocument()
  })

  it('scrolls to that panel when the button is clicked', async () => {
    const user = userEvent.setup()
    render(
      <div>
        <WorkflowRail progress={progress()} qualityWarning={false} />
        {/* The anchor the workspace puts on the Data panel. */}
        <div id="data" data-testid="data-panel" />
      </div>,
    )

    const scrollIntoView = vi.fn()
    // jsdom has no layout; hand the anchor the method the browser would have.
    const anchor = screen.getByTestId('data-panel')
    anchor.scrollIntoView = scrollIntoView

    await user.click(screen.getByRole('button', { name: /go to the data panel/i }))

    expect(scrollIntoView).toHaveBeenCalledOnce()
  })

  it('points at a different panel for a later stage', () => {
    render(
      <WorkflowRail
        progress={progress({
          stage: 'analyze',
          next_action: 'Run an analysis',
          next_hint: 'SQL or Python, single- or multi-dataset.',
          next_endpoint: 'POST /cases/c1/datasets/d1/runs',
        })}
        qualityWarning={false}
      />,
    )

    expect(
      screen.getByRole('button', { name: /go to the runs panel/i }),
    ).toBeInTheDocument()
  })

  it('still names the stage and its completion', () => {
    render(<WorkflowRail progress={progress()} qualityWarning={false} />)

    expect(screen.getByText(/stage: data/i)).toBeInTheDocument()
  })
})
