// FIX-UPDATES-009 (W-005): the surface that answers the native Check for
// Updates menu item.
//
// The shell owns the menu bar and the core owns the check; this component is
// the delivery, and it is the delivery because it is the surface the window
// already has. The browser host never sees a notice: the shell is the only
// host that dispatches `dah-notice`, because it is the only host with a menu
// item to answer for.
//
// This is the shell's only always-mounted surface, and it stays inert until a
// notice arrives - the layer is not a loading state, and it renders nothing
// until there is something to say.
//
// The notice carries its own Dismiss button rather than vanishing on a timer:
// a sentence like "the release feed is not reachable; the repository may be
// private" is the answer the analyst asked for, and an answer that disappears
// before it is read is no better than stderr.

import { useEffect, useState } from 'react'
import { describeUpdate, NOTICE_ATTR, NOTICE_EVENT } from './shell'
import { Button } from './lib/ui'

export function NoticeLayer() {
  const [notice, setNotice] = useState<string | null>(null)

  useEffect(() => {
    // A notice the shell wrote before this bundle mounted - the menu item can
    // fire in the gap between the window showing and the bundle finishing.
    // Read once, never polled: the attribute is a stash, not a channel.
    const pending = document.querySelector(`[${NOTICE_ATTR}]`)
    if (pending) {
      const text = pending.getAttribute(NOTICE_ATTR)
      if (text) setNotice(text)
      pending.remove()
    }

    const onNotice = (event: Event) => {
      const detail = (event as CustomEvent<unknown>).detail
      setNotice(describeUpdate(detail))
    }
    window.addEventListener(NOTICE_EVENT, onNotice)
    return () => window.removeEventListener(NOTICE_EVENT, onNotice)
  }, [])

  if (!notice) return null

  return (
    <div className="shell-notice" role="status" aria-live="polite">
      <span>{notice}</span>
      <Button
        type="button"
        variant="small"
        onClick={() => setNotice(null)}
        aria-label="Dismiss the update notice"
      >
        Dismiss
      </Button>
    </div>
  )
}
