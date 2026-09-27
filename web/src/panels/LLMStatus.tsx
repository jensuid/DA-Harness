// W2X-012 (the walk-test's BLOCKER): the surface that says what the analyst
// is actually getting.
//
// The packaged app carries no LLM credentials, so every LLM feature silently
// degrades to the deterministic engine - plan, draft, refine, chat and agent
// all answer, and the one field that carried the truth was `source:
// template`, which is a developer's field. The analyst reads no part of it.
// This asks the core once, on mount, and says the thing out loud.
//
// It renders nothing when the LLM is configured. A green banner on every
// screen is noise the analyst learns to dismiss, and a notice that fires on
// every mount is the boy who cried wolf - the one time it has something to
// say is the one time it is not read. Only the broken state shows.
//
// The shell's NoticeLayer is a different channel and stays untouched: that
// one answers the native menu bar through a custom event the browser host
// never receives. This is an ordinary GET the shell and the browser both
// make, so a developer running the core without a key sees the same sentence
// a user of the packaged app does.

import { useEffect, useState } from 'react'
import { getLlmStatus, type LlmStatus } from '../api'

export function LlmStatusBanner() {
  const [status, setStatus] = useState<LlmStatus | null>(null)

  useEffect(() => {
    let cancelled = false
    // Read once, never polled: the configuration is a property of this
    // deployment, and a poll would re-render the banner on every interval.
    void getLlmStatus()
      .then((value) => {
        if (!cancelled) setStatus(value)
      })
      .catch(() => {
        // A core that cannot answer this is a core that cannot answer the
        // LLM either, but saying so from here would be a guess - the health
        // surface is what owns "the core is down". Render nothing and let
        // that surface say it.
      })
    return () => {
      cancelled = true
    }
  }, [])

  if (!status || status.configured) return null

  return (
    <div className="llm-status" role="status" aria-live="polite">
      <span>
        The LLM is not configured, so plan, draft, refine, chat and the agent
        answer from DAH's deterministic engines instead. Add a key to
        DAH_LLM_API_KEY to use them.
      </span>
    </div>
  )
}
