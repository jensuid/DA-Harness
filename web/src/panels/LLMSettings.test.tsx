// W2X-012 phase B: the settings surface that puts the credential where the
// packaged core can read it.
//
// Phase A's tests pin the banner's sentence. These pin the door the sentence
// now ends in: the panel the Configure button and the DAH Settings menu item
// open, the three fields it carries, and the state it answers once saved. The
// browser host never receives the shell's event, but the panel itself is an
// ordinary form, so it is driven the way the shell drives it and the way a
// browser would if it ever needed to.

import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

import { LlmSettingsPanel } from './LLMSettings'
import * as api from '../api'
import { SETTINGS_EVENT, LLM_CHANGED_EVENT } from '../shell'

const STORED: api.LlmConfig = {
  api_key: 'stored-key',
  model: 'stored-model',
  base_url: 'https://example.invalid/v1',
}

describe('LlmSettingsPanel', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
  })

  it('renders nothing until the shell opens it', () => {
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    const { container } = render(<LlmSettingsPanel />)

    // The panel is not a banner. An empty form on every screen is the same
    // noise phase A refused to make, so closed is the resting state.
    expect(container).toBeEmptyDOMElement()
    // ...and it does not fetch anything it would have no reason to show.
    expect(api.getLlmConfig).not.toHaveBeenCalled()
  })

  it('opens on the shell event and pre-fills from the stored settings', async () => {
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    render(<LlmSettingsPanel />)

    // The menu item dispatches this; the panel listens. A browser host never
    // receives it, so the panel stays closed there.
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))

    expect(await screen.findByText(/DAH Settings/i)).toBeInTheDocument()
    expect(api.getLlmConfig).toHaveBeenCalledTimes(1)
    expect(screen.getByPlaceholderText('sk-…')).toHaveValue('stored-key')
    expect(screen.getByPlaceholderText('gpt-4o-mini')).toHaveValue('stored-model')
    expect(
      screen.getByPlaceholderText('https://api.openai.com/v1'),
    ).toHaveValue('https://example.invalid/v1')
  })

  it('opens with blanks when the settings cannot be read', async () => {
    // A corrupt or unreadable file is a state the analyst can write over, not
    // a reason for the panel to refuse to appear - a save is how they fix it.
    vi.spyOn(api, 'getLlmConfig').mockRejectedValue(new Error('boom'))
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))

    expect(await screen.findByText(/DAH Settings/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-…')).toHaveValue('')
  })

  it('writes the three fields and says the features will use them', async () => {
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    const put = vi
      .spyOn(api, 'putLlmConfig')
      .mockResolvedValue({ ...STORED, configured: true, provider: 'DAH_LLM_API_KEY' })
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    const key = await screen.findByPlaceholderText('sk-…')
    await userEvent.clear(key)
    await userEvent.type(key, 'new-key')
    await userEvent.click(screen.getByText('Save'))

    // The write is the whole point: the credential reaches the file the core
    // reads, and the answer is the status surface's own shape.
    await waitFor(() =>
      expect(put).toHaveBeenCalledWith({
        api_key: 'new-key',
        model: 'stored-model',
        base_url: 'https://example.invalid/v1',
      }),
    )
    expect(
      await screen.findByText(/no restart needed/i),
    ).toBeInTheDocument()
  })

  it('tells the banner a save landed, without asserting what it changed', async () => {
    // The banner reads once on mount; without this the concern it was showing
    // lingers after the analyst fixed it. The event carries no payload, so the
    // banner refetches and the two surfaces agree on the core's own answer
    // rather than on a value this panel asserted.
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue({ api_key: '', model: '', base_url: '' })
    vi.spyOn(api, 'putLlmConfig').mockResolvedValue({
      configured: true,
      provider: 'DAH_LLM_API_KEY',
      model: 'gpt-4o-mini',
      base_url: 'https://api.openai.com/v1',
    })
    const posted: CustomEvent[] = []
    const listener = (event: Event) => posted.push(event as CustomEvent)
    window.addEventListener(LLM_CHANGED_EVENT, listener)
    try {
      render(<LlmSettingsPanel />)
      window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
      await screen.findByPlaceholderText('sk-…')
      await userEvent.click(screen.getByText('Save'))
      await waitFor(() => expect(posted).toHaveLength(1))
      expect(posted[0].type).toBe(LLM_CHANGED_EVENT)
    } finally {
      window.removeEventListener(LLM_CHANGED_EVENT, listener)
    }
  })

  it('says it when a save leaves the LLM still unconfigured', async () => {
    // A cleared key, or a key the core could not read, lands as a save that
    // did not change the state - and that is a sentence rather than a green
    // tick, because "saved" and "configured" are different claims.
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    vi.spyOn(api, 'putLlmConfig').mockResolvedValue({
      configured: false,
      provider: null,
      model: 'gpt-4o-mini',
      base_url: 'https://api.openai.com/v1',
    })
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    await screen.findByPlaceholderText('sk-…')
    await userEvent.click(screen.getByText('Save'))

    expect(
      await screen.findByText(/still reports the LLM is not configured/i),
    ).toBeInTheDocument()
  })

  it('keeps the entered values when a save fails', async () => {
    // A network blip should not cost the analyst the key they typed, so the
    // failure goes back to ready - the form keeps its contents - rather than
    // to closed.
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue({ api_key: '', model: '', base_url: '' })
    vi.spyOn(api, 'putLlmConfig').mockRejectedValue(new Error('boom'))
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    const key = await screen.findByPlaceholderText('sk-…')
    await userEvent.type(key, 'typed-key')
    await userEvent.click(screen.getByText('Save'))

    expect(await screen.findByText(/boom/i)).toBeInTheDocument()
    expect(screen.getByPlaceholderText('sk-…')).toHaveValue('typed-key')
  })

  it('closes on the Close button and reopens on the next event', async () => {
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    await screen.findByText(/DAH Settings/i)
    await userEvent.click(screen.getByText('Close'))

    expect(screen.queryByText(/DAH Settings/i)).not.toBeInTheDocument()

    // The listener survives the close, so the menu item works again - and a
    // panel that could only open once would be a panel the analyst has to
    // relaunch the app to reach.
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    expect(await screen.findByText(/DAH Settings/i)).toBeInTheDocument()
    expect(api.getLlmConfig).toHaveBeenCalledTimes(2)
  })

  it('reads the config through the api client', async () => {
    // The client is the one seam these tests replace; a panel that bypassed
    // it would be a panel talking to a core the fixtures do not control.
    const get = vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))

    await waitFor(() => expect(get).toHaveBeenCalled())
  })
})

// DMDARK: the appearance row. The three states are a window preference, so the
// row applies on change - the dialog saves on change - and there is nothing to
// fetch and no save to wait for. What is under test is the control reaching the
// resolver: the row is the only surface that moves the attribute, and a row
// that rendered without wiring it would be a row the analyst cannot use.
describe('LlmSettingsPanel appearance row', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
    document.documentElement.removeAttribute('data-theme')
  })

  it('shows the three states with the current one selected', async () => {
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))

    expect(await screen.findByText('Appearance')).toBeInTheDocument()
    // System is the zero-config default, so it is the one checked on a fresh
    // store.
    expect(screen.getByRole('radio', { name: 'System' })).toBeChecked()
    expect(screen.getByRole('radio', { name: 'Light' })).not.toBeChecked()
    expect(screen.getByRole('radio', { name: 'Dark' })).not.toBeChecked()
  })

  it('reflects a choice the previous launch persisted', async () => {
    localStorage.setItem('dah-theme', 'dark')
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))

    expect(await screen.findByRole('radio', { name: 'Dark' })).toBeChecked()
  })

  it('applies Dark on change and keeps it, with no save', async () => {
    // The row is not part of the LLM form's submit: an appearance moves the
    // attribute the moment it is chosen, because there is nothing to wait for.
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    await screen.findByText('Appearance')

    await userEvent.click(screen.getByRole('radio', { name: 'Dark' }))

    expect(document.documentElement.getAttribute('data-theme')).toBe('dark')
    expect(localStorage.getItem('dah-theme')).toBe('dark')
  })

  it('moves back to Light when Light is chosen', async () => {
    localStorage.setItem('dah-theme', 'dark')
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    await screen.findByText('Appearance')

    await userEvent.click(screen.getByRole('radio', { name: 'Light' }))

    expect(document.documentElement.getAttribute('data-theme')).toBe('light')
    expect(localStorage.getItem('dah-theme')).toBe('light')
  })

  it('does not post the appearance to the core', async () => {
    // The credential is the core's business; the appearance is the window's.
    // A row that smuggled its choice into the LLM save would send a field the
    // core has no use for.
    vi.spyOn(api, 'getLlmConfig').mockResolvedValue(STORED)
    const put = vi
      .spyOn(api, 'putLlmConfig')
      .mockResolvedValue({ ...STORED, configured: true, provider: 'DAH_LLM_API_KEY' })
    render(<LlmSettingsPanel />)
    window.dispatchEvent(new CustomEvent(SETTINGS_EVENT))
    await screen.findByText('Appearance')
    await userEvent.click(screen.getByRole('radio', { name: 'Dark' }))

    expect(put).not.toHaveBeenCalled()
  })
})
