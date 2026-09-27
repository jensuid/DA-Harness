// W2X-012: the banner that says what the LLM features are actually doing.
//
// The walk-test's BLOCKER was a silence: the packaged app carries no LLM
// credentials, every LLM feature falls back to the deterministic engine, and
// the analyst is told nothing. `source: template` carried the truth and a
// developer is who reads it. These tests drive the surface the analyst reads.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { LlmStatusBanner } from './LLMStatus'
import * as api from '../api'
import { SETTINGS_EVENT, LLM_CHANGED_EVENT } from '../shell'

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

  it('refetches when the settings panel says a save landed', async () => {
    // The banner reads once, so a key the analyst saves in the panel would
    // leave a stale concern on screen until the next mount. The panel posts
    // a changed event; this is the one thing besides the mount that can move
    // the state, so it is the one thing the banner refetches for.
    const get = vi.spyOn(api, 'getLlmStatus').mockResolvedValue(UNCONFIGURED)
    render(<LlmStatusBanner />)
    await screen.findByText(/not configured/i)
    expect(get).toHaveBeenCalledTimes(1)

    window.dispatchEvent(new CustomEvent(LLM_CHANGED_EVENT))

    // One refetch per event - not a poll that has to be torn down.
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2))
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

  it('offers a Configure button that opens the settings panel', async () => {
    // Phase A's sentence ended in an env var name - a developer's answer to
    // an analyst's problem. Phase B gives it a door, and this is the seam:
    // the button and the DAH Settings menu item dispatch the same event, so
    // the panel is one surface whichever path opened it.
    vi.spyOn(api, 'getLlmStatus').mockResolvedValue(UNCONFIGURED)
    render(<LlmStatusBanner />)
    // The label is the accessible name, so the button is found by it rather
    // than by the visible glyph - "Configure…" is what the analyst reads, and
    // the ellipsis is a character a regex has to opt into.
    const button = await screen.findByRole('button', { name: /configure the llm/i })

    expect(button).toBeInTheDocument()

    const dispatched: CustomEvent[] = []
    const listener = (event: Event) => dispatched.push(event as CustomEvent)
    window.addEventListener(SETTINGS_EVENT, listener)
    await userEvent.click(button)
    window.removeEventListener(SETTINGS_EVENT, listener)

    expect(dispatched).toHaveLength(1)
    expect(dispatched[0].type).toBe(SETTINGS_EVENT)
  })

  it('renders no Configure button when the LLM is configured', async () => {
    // The button belongs to the concern state only. A door on the happy path
    // is the same noise phase A refused to make of the banner itself.
    vi.spyOn(api, 'getLlmStatus').mockResolvedValue(CONFIGURED)
    const { container } = render(<LlmStatusBanner />)

    await waitFor(() => expect(api.getLlmStatus).toHaveBeenCalled())
    expect(container).toBeEmptyDOMElement()
  })
})
