// FIX-UPDATES-009 (W-005): the menu item's three outcomes have to reach the
// window. These tests drive the layer the way the shell does - by dispatching
// the event its script builds - so what is asserted is what the analyst sees.

import { describe, it, expect, beforeEach } from 'vitest'
import { act, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NoticeLayer } from './NoticeLayer'
import { NOTICE_ATTR, NOTICE_EVENT } from './shell'

// The shell evaluates a script that posts this event with the core's own body
// as its detail; the Rust side builds the same name into that script. Wrapped
// in `act` because the listener is a native one - React schedules the state
// update rather than flushing it in line, and an unwrapped dispatch warns.
function postNotice(body: unknown) {
  act(() => {
    window.dispatchEvent(new CustomEvent(NOTICE_EVENT, { detail: body }))
  })
}

const UNREACHABLE = {
  status: 'unknown',
  current: '0.3.3',
  reason: 'the release feed is not reachable; the repository may be private',
}

describe('NoticeLayer', () => {
  beforeEach(() => {
    document.querySelectorAll(`[${NOTICE_ATTR}]`).forEach((node) => node.remove())
  })

  it('renders nothing until a notice arrives', () => {
    const { container } = render(<NoticeLayer />)
    expect(container).toBeEmptyDOMElement()
  })

  it('shows an unreachable feed with its reason', async () => {
    render(<NoticeLayer />)
    postNotice(UNREACHABLE)
    // The event is a native one, not a React handler, so React 18 schedules
    // the state update rather than flushing it in line - findByText awaits it.
    expect(
      await screen.findByText(/the repository may be private/i),
    ).toBeInTheDocument()
  })

  it('shows a newer build when one is available', async () => {
    render(<NoticeLayer />)
    postNotice({
      status: 'available',
      current: '0.3.3',
      latest: 'v0.4.0',
      page_url: 'https://github.com/jensuid/DA-Harness/releases/tag/v0.4.0',
    })
    expect(await screen.findByText(/v0\.4\.0 is available/i)).toBeInTheDocument()
  })

  it('shows that the installed build is the latest', async () => {
    render(<NoticeLayer />)
    postNotice({ status: 'current', current: '0.3.3', latest: 'v0.3.3' })
    expect(await screen.findByText(/up to date/i)).toBeInTheDocument()
  })

  it('carries a dismiss control the analyst can use', async () => {
    const user = userEvent.setup()
    render(<NoticeLayer />)
    postNotice(UNREACHABLE)
    const dismiss = await screen.findByRole('button', { name: /dismiss/i })
    await user.click(dismiss)
    await waitFor(() =>
      expect(screen.queryByText(/the repository may be private/i)).toBeNull(),
    )
  })

  it('replaces an earlier notice with the latest check', async () => {
    render(<NoticeLayer />)
    postNotice(UNREACHABLE)
    postNotice({ status: 'current', current: '0.3.3', latest: 'v0.3.3' })
    expect(await screen.findByText(/up to date/i)).toBeInTheDocument()
    await waitFor(() =>
      expect(screen.queryByText(/the repository may be private/i)).toBeNull(),
    )
  })

  it('reads a notice the shell wrote before the bundle mounted', () => {
    // The menu item can fire in the gap between the window showing and the
    // bundle finishing; the shell stashes the answer in the DOM for the layer
    // to pick up once, so the first check is not lost to a race.
    const stash = document.createElement('div')
    stash.setAttribute(NOTICE_ATTR, 'Could not check for updates: stashed')
    document.body.appendChild(stash)

    render(<NoticeLayer />)
    expect(screen.getByText(/stashed/i)).toBeInTheDocument()
    // Read once, never polled: the stash is cleared once the layer has it.
    expect(document.querySelector(`[${NOTICE_ATTR}]`)).toBeNull()
  })

  it('lands as a status region a screen reader announces', async () => {
    render(<NoticeLayer />)
    postNotice(UNREACHABLE)
    // The notice is the answer to something the analyst asked for; it should
    // be announced rather than appearing silently at the top of the page.
    expect(await screen.findByRole('status')).toBeInTheDocument()
  })
})
