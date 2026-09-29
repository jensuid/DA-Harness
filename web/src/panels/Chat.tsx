/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useEffect, useState } from 'react'
import { type ConversationTurn, getCase, postChat } from '../api'
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'
import { Button, surfaces } from '../lib/ui'
import { CallProgress, useCallProgress } from '../lib/progress'
import { MotionSurface } from '../lib/motion'

export function Chat({
  caseId,
  turns,
  onTurn,
  onOpenCase,
}: {
  caseId: string
  turns: ConversationTurn[]
  onTurn: (turn: ConversationTurn) => void
  onOpenCase: (caseId: string) => void
}) {
  // A previous case cited by an answer is looked up once, however many turns
  // cite it, and only for `case:` grounds - the other kinds are not
  // case-scoped. The lookup is a read-only GET and writes nothing.
  const [priorQuestions, setPriorQuestions] = useState<Record<string, string | null>>({})
  useEffect(() => {
    const cited = turns
      .flatMap((turn) => turn.grounds)
      .filter((ground) => ground.startsWith('case:'))
      .map((ground) => ground.slice('case:'.length))
    const missing = [...new Set(cited)].filter((id) => !(id in priorQuestions))
    if (missing.length === 0) return
    let cancelled = false
    void Promise.all(
      missing.map((id) =>
        getCase(id)
          .then((prior) => [id, prior.question] as const)
          // A deleted case, or a core that could not answer, is recorded as
          // absent rather than refetched on every render.
          .catch(() => [id, null] as const),
      ),
    ).then((entries) => {
      if (cancelled) return
      setPriorQuestions((prior) => {
        let changed = false
        const next = { ...prior }
        for (const [id, question] of entries) {
          if (!(id in next)) {
            next[id] = question
            changed = true
          }
        }
        // Returning the same object keeps a failed lookup from re-fetching on
        // every render: the effect's own state change would otherwise loop.
        return changed ? next : prior
      })
    })
    return () => {
      cancelled = true
    }
  }, [turns, priorQuestions])
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  // W2X-001: the chat's answer is the call the analyst waits on most often,
  // and its wait is the same one-word sentence as the rest. The elapsed row
  // and its stop button sit under the question the analyst asked.
  const progress = useCallProgress()

  async function send(event: React.FormEvent) {
    event.preventDefault()
    const text = message.trim()
    if (!text || busy) return
    setBusy(true)
    setError(null)
    const signal = progress.start()
    try {
      const turn = await postChat(caseId, text, signal)
      onTurn(turn)
      setMessage('')
    } catch (err) {
      // A cancel leaves the question where the analyst wrote it, so the wait
      // can stop without losing what was asked.
      setError(
        err instanceof DOMException && err.name === 'AbortError'
          ? 'Cancelled - the question is still here.'
          : messageOf(err),
      )
    } finally {
      progress.done()
      setBusy(false)
    }
  }

  return (
    <div className={surfaces.panel}>
      <h2 className={surfaces.heading}>Ask this case</h2>
      <p className={surfaces.note}>
        Answers come from this case's artifacts. The memory is cross-case: it
        may recall findings from your other cases, and it says when it cannot
        compare across them.
      </p>
      <form onSubmit={send}>
        <input
          aria-label="Ask a question"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="How many datasets does this case have?"
          disabled={busy}
        />
        <Button type="submit" disabled={busy || !message.trim()}>
          {busy ? 'Asking…' : 'Ask'}
        </Button>
      </form>
      <CallProgress
        kind="answer"
        elapsed={progress.elapsed}
        active={progress.active}
        onCancel={progress.cancel}
      />
      {error && <p role="alert">The assistant could not answer: {error}</p>}
      <ul className={surfaces.panelList}>
        {turns.map((turn) => (
          <li key={turn.id} className={surfaces.turn}>
            <p className="question">{turn.message}</p>
            <MotionSurface variant="open">
              <p>{turn.answer}</p>
              <p className={surfaces.note}>{sourceLabel(turn.source, 'answer')}</p>
              {turn.grounds.length > 0 && (
                <ul className={surfaces.panelList}>
                  {turn.grounds.map((ground) => (
                    <li key={ground}>
                      <Ground
                        ground={ground}
                        priorQuestions={priorQuestions}
                        onOpenCase={onOpenCase}
                      />
                    </li>
                  ))}
                </ul>
              )}
            </MotionSurface>
          </li>
        ))}
      </ul>
    </div>
  )
}

// EDA: the "what should I look at first" steps (P7-SHELL-007). Each op
// compiles to read-only SQL under the same gate and row cap as a hand-written
// query and is deliberately not persisted - exploration is not evidence, and a
// finding has to anchor on a query the analyst wrote. The panel says so, so a
// promising segment leads to the runs panel rather than to a false finding.

export function Ground({
  ground,
  priorQuestions,
  onOpenCase,
}: {
  ground: string
  priorQuestions: Record<string, string | null>
  onOpenCase: (caseId: string) => void
}) {
  if (!ground.startsWith('case:')) {
    return <span className="chip">{ground}</span>
  }
  const caseId = ground.slice('case:'.length)
  if (!(caseId in priorQuestions)) {
    return <span className="chip">previous case…</span>
  }
  const question = priorQuestions[caseId]
  if (!question) {
    // The cited case may have been deleted - a citation outlives its source
    // the way a template does. The answer stays readable; nothing throws.
    return <span className="chip">a previous case that is no longer available</span>
  }
  return (
    <button
      type="button"
      className="chip"
      onClick={() => onOpenCase(caseId)}
      aria-label={`Open the previous case: ${question}`}
    >
      previous case: {question}
    </button>
  )
}

// The evidence graph, as a review surface (P7-SHELL-008). The workspace's other
// panels serve the analyst working the loop; this one serves the person reading
// the result, answering the case-level question: what backs each claim, and
// does every one of them reach the data?
//
// The graph is a read-only projection over persisted rows - nothing here writes,
// and nothing a reviewer does changes the case. The shapes are the core's own,
// rendered as text: an SVG layout is a library's job and DEC-001 keeps the
// bundle dependency-free, and a sentence carries the same information a reader
// can act on.
