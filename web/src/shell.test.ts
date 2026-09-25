// FIX-UPDATES-009 (W-005): the core distinguishes three statuses and the shell
// delivered none of them. These tests pin the sentence each one becomes in the
// window - including the unreachable feed, which is what this repository
// actually answers and what the menu item used to say nothing about.

import { describe, it, expect } from 'vitest'
import { describeUpdate, NOTICE_ATTR, NOTICE_EVENT } from './shell'

const UNREACHABLE = {
  status: 'unknown',
  current: '0.3.3',
  reason: 'the release feed is not reachable; the repository may be private',
}

describe('describeUpdate', () => {
  it('reports an unreachable feed with its reason rather than silence', () => {
    const text = describeUpdate(UNREACHABLE)
    expect(text).toContain('Could not check for updates')
    // The core's own reason rides along, not reworded into "up to date".
    expect(text).toContain('the repository may be private')
  })

  it('names the installed and the newer build when one is available', () => {
    const text = describeUpdate({
      status: 'available',
      current: '0.3.3',
      latest: 'v0.4.0',
      page_url: 'https://github.com/jensuid/DA-Harness/releases/tag/v0.4.0',
    })
    expect(text).toContain('0.3.3')
    expect(text).toContain('v0.4.0')
    expect(text).toContain(
      'https://github.com/jensuid/DA-Harness/releases/tag/v0.4.0',
    )
  })

  it('says the installed build is the latest when nothing newer exists', () => {
    const text = describeUpdate({
      status: 'current',
      current: '0.3.3',
      latest: 'v0.3.3',
    })
    expect(text).toContain('up to date')
    expect(text).toContain('0.3.3')
    // A check that reached the feed does not read as a failure.
    expect(text).not.toContain('Could not check')
  })

  it('reports a status it has never heard of as could-not-tell', () => {
    expect(
      describeUpdate({ status: 'whatever', current: '0.3.3' }),
    ).toContain('Could not check for updates')
  })

  it('reports a missing reason rather than inventing one', () => {
    const text = describeUpdate({ status: 'unknown', current: '0.3.3' })
    expect(text).toContain('Could not check for updates')
    expect(text).toContain('could not determine')
  })

  it('reports an available build that named no download page', () => {
    const text = describeUpdate({
      status: 'available',
      current: '0.3.3',
      latest: 'v0.4.0',
    })
    expect(text).toContain('v0.4.0')
    expect(text).toContain('did not name a download page')
  })

  it('degrades a body that is not the shape expected', () => {
    expect(describeUpdate(null)).toContain('Could not check for updates')
    expect(describeUpdate('nope')).toContain('Could not check for updates')
    expect(describeUpdate({ status: 42 })).toContain('Could not check for updates')
  })

  it('agrees with the shell event and attribute names', () => {
    // The Rust side builds these into the script it evaluates; a rename here
    // without one there makes the menu item silent again (W-005).
    expect(NOTICE_EVENT).toBe('dah-notice')
    expect(NOTICE_ATTR).toBe('data-dah-notice')
  })
})
