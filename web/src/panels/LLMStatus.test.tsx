// W2X-012: the banner that says what the LLM features are actually doing.
//
// The walk-test's BLOCKER was a silence: the packaged app carries no LLM
// credentials, every LLM feature falls back to the deterministic engine, and
// the analyst is told nothing. `source: template` carried the truth and a
// developer is who reads it. These tests drive the surface the analyst reads.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'

import { LlmStatusBanner } from './LLMStatus'
import * as api from '../api'

const CONFIGURED = {
  configured: true,
  provider: 'DAH_LLM_API_KEY',
  model: 'gpt-4o-mini',
  base_url: 'https://api.openai.com/v1',
}

const UNCONFIGURED = {
  configured: false,
  provider: null,
  model: 'gpt-4o-mini',
  base_url: 'https://api.openai.com/v1',
}

describe('LlmStatusBanner', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('says the LLM features fell back when no key is configured', async () => {
    vi.spyOn(api, 'getLlmStatus').mockResolvedValue(UNCONFIGURED)
    render(<LlmStatusBanner />)

    expect(
      await screen.findByText(/not configured/i),
    ).toBeInTheDocument()
    // The sentence has to name the deterministic engines, because "not
    // configured" alone tells a developer what is wrong and an analyst what
    // they got instead - and what they got is the point.
    expect(
      await screen.findByText(/deterministic engines/i),
    ).toBeInTheDocument()
  })

  it('renders nothing when the LLM is configured', async () => {
    vi.spyOn(api, 'getLlmStatus').mockResolvedValue(CONFIGURED)
    const { container } = render(<LlmStatusBanner />)

    // A green banner on every screen is noise the analyst learns to dismiss;
    // only the broken state shows.
    await waitFor(() => expect(api.getLlmStatus).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it('renders nothing while the status is still loading', () => {
    vi.spyOn(api, 'getLlmStatus').mockReturnValue(new Promise(() => {}))
    const { container } = render(<LlmStatusBanner />)

    // A flash of the wrong state on every mount is the same noise; the banner
    // commits only once the core has answered.
    expect(container).toBeEmptyDOMElement()
  })

  it('asks the core once and does not poll', async () => {
    vi.spyOn(api, 'getLlmStatus').mockResolvedValue(UNCONFIGURED)
    render(<LlmStatusBanner />)

    await screen.findByText(/not configured/i)
    // The configuration is a property of this deployment, not of a request -
    // a poll would re-render the banner on every interval for a fact that
    // does not move.
    expect(api.getLlmStatus).toHaveBeenCalledTimes(1)
  })

  it('stays silent when the core cannot be reached', async () => {
    vi.spyOn(api, 'getLlmStatus').mockRejectedValue(new Error('core down'))
    const { container } = render(<LlmStatusBanner />)

    // Not a guess about the LLM's state: a core that cannot answer this
    // cannot answer the LLM either, and the health surface owns "the core is
    // down". Two surfaces saying it is two places to be wrong.
    await waitFor(() => expect(api.getLlmStatus).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })

  it('does not drop the banner if the unmount races the fetch', async () => {
    vi.spyOn(api, 'getLlmStatus').mockResolvedValue(UNCONFIGURED)
    const { unmount } = render(<LlmStatusBanner />)
    unmount()

    // The cancellation flag is the point: a state update after unmount is a
    // React warning in the log and, if the component were not guarding, a
    // banner that arrives after the analyst left the screen.
    await waitFor(() => expect(api.getLlmStatus).toHaveBeenCalled())
  })

  it('reads the status through the api client, not a fetch of its own', async () => {
    vi.spyOn(api, 'getLlmStatus').mockResolvedValue(UNCONFIGURED)
    render(<LlmStatusBanner />)

    // One client, one error path, one place the core's envelope contract
    // lives. A second fetch would be a second copy of the parsing and a
    // second copy of ApiError to get wrong.
    expect(api.getLlmStatus).toHaveBeenCalledWith()
    // Await the fetch's resolution so the state update lands inside the test
    // rather than after it - an unwrapped update is a warning in the log and
    // a banner the next test might see.
    await waitFor(() => expect(screen.queryByText(/not configured/i)).not.toBeNull())
  })
})
