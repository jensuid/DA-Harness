/**
 * W2X-001: the timeout surface.
 *
 * The walk measured three of four LLM calls timing out at the harness's 120s
 * ceiling while the UI showed one static word ("Generating…", "Working…", and
 * in the runs panel three "Working…" at once) - no elapsed time, no way to
 * stop a call the analyst had given up on, and then a deterministic answer
 * arriving as if nothing had happened. Waiting two minutes on one word cannot
 * be distinguished from a dead page by the person looking at it.
 *
 * The fix is three primitives, and this file holds the shared two: a hook that
 * owns one call's abort controller and elapsed timer, and the row a panel
 * renders from it. A call that is LLM-backed is the point; a fast deterministic
 * one shows the same row for a moment and clears, which is harmless and is
 * better than two surfaces. The shell cannot know which engine the core will
 * pick before it answers, so it does not pretend to.
 *
 * What this is NOT: the shell does not shorten the core's own timeout, and it
 * does not retry. Cancelling aborts the request the browser made; the core may
 * still finish it, and a fallback that arrives after a cancel is the core's own
 * business. The analyst's contract is the local one - the wait became legible
 * and stoppable.
 */

import { useEffect, useRef, useState } from 'react'
import { Button, surfaces } from './ui'

/**
 * One in-flight call: its elapsed seconds and its stop button.
 *
 * `kind` names the thing the analyst is waiting for ("plan", "interpretation",
 * "draft"), because the static word the walk replaced named the verb and not
 * the object, and a reader does not know what "Working…" is producing.
 */
export function useCallProgress() {
  const [elapsed, setElapsed] = useState(0)
  const [active, setActive] = useState(false)
  const controller = useRef<AbortController | null>(null)
  const timer = useRef<ReturnType<typeof setInterval> | null>(null)

  // The elapsed clock is a one-second interval, and it clears with the call:
  // the interval is the whole cost of this surface, and a leaked one would
  // keep ticking after the panel unmounted.
  function stop() {
    if (timer.current !== null) {
      clearInterval(timer.current)
      timer.current = null
    }
    controller.current = null
    setActive(false)
  }

  useEffect(() => stop, [])

  /** Starts the clock and answers the signal a request carries. */
  function start(): AbortSignal {
    controller.current = new AbortController()
    setElapsed(0)
    setActive(true)
    if (timer.current !== null) clearInterval(timer.current)
    timer.current = setInterval(() => {
      setElapsed((prior) => prior + 1)
    }, 1000)
    return controller.current.signal
  }

  /** Ends the call without cancelling: the response arrived. */
  function done() {
    stop()
  }

  /** Cancels the in-flight request. Idempotent: ending is the same either way. */
  function cancel() {
    controller.current?.abort()
    stop()
  }

  return { elapsed, active, start, done, cancel }
}

export function CallProgress({
  kind,
  elapsed,
  active,
  onCancel,
}: {
  kind: string
  elapsed: number
  active: boolean
  onCancel: () => void
}) {
  if (!active) return null
  // One text node, so the sentence reads whole in the DOM and in a screen
  // reader and the elapsed count is not a fragment a test has to reassemble.
  return (
    <div className={surfaces.buttonRow + ' call-progress'} role="status" aria-live="polite">
      <p className={surfaces.note}>
        Generating the {kind}… {elapsed}s elapsed
      </p>
      <Button type="button" variant="small" onClick={onCancel}>
        Cancel
      </Button>
    </div>
  )
}
