// The case's stated intent (P8-CONTEXT-001): what the analysis is for, what it
// would answer in pieces, what it would test, and what it is assuming.
//
// The primary question is deliberately not here - it already lives on the case
// row and is editable in the list. This is what a question alone cannot carry.
//
// Whole-object save: the PUT replaces the stored context, so a retry after a
// failed save leaves the server identical to the form rather than merging the
// two. Nothing is written until Save; closing the panel discards the edits,
// which is why the panel says when there are unsaved ones.
import { useEffect, useId, useState } from 'react'

import { type CaseContext, getContext, putContext } from './api'
import { messageOf } from './CaseList'
import { Button, Skeleton, surfaces } from './lib/ui'

type Lists = 'sub_questions' | 'hypotheses' | 'constraints'

const FIELDS: { key: Lists; label: string; noun: string }[] = [
  { key: 'sub_questions', label: 'Sub-questions', noun: 'sub-question' },
  { key: 'hypotheses', label: 'Hypotheses to test', noun: 'hypothesis' },
  { key: 'constraints', label: 'Known constraints', noun: 'constraint' },
]

function empty(): CaseContext {
  return { case_id: '', purpose: '', sub_questions: [], hypotheses: [], constraints: [], updated_at: null }
}

export function ContextPanel({
  caseId,
  loading,
  onChanged,
}: {
  caseId: string
  loading: boolean
  onChanged: () => void
}) {
  const headingId = useId()
  const [context, setContext] = useState<CaseContext>(empty())
  const [dirty, setDirty] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      const stored = await getContext(caseId)
      setContext(stored)
      setDirty(false)
    } catch (err) {
      setError(messageOf(err))
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  function setPurpose(text: string) {
    setContext((prior) => ({ ...prior, purpose: text }))
    setDirty(true)
  }

  function setList(key: Lists, entries: string[]) {
    setContext((prior) => ({ ...prior, [key]: entries }))
    setDirty(true)
  }

  async function save() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      // Trimmed on the way in, so an entry of spaces is not saved as a blank
      // the server would have to reject.
      const trimmed = {
        purpose: context.purpose.trim(),
        sub_questions: context.sub_questions.map((s) => s.trim()).filter((s) => s.length > 0),
        hypotheses: context.hypotheses.map((s) => s.trim()).filter((s) => s.length > 0),
        constraints: context.constraints.map((s) => s.trim()).filter((s) => s.length > 0),
      }
      const stored = await putContext(caseId, trimmed)
      setContext(stored)
      setDirty(false)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  if (loading) {
    // SKEL: the panel's read is in flight and its empty state is an editable
    // form - a young case and a case the shell has not read yet look the same
    // shape. The skeleton is that shape: the purpose field and the three
    // lists, in the same subpanels the real form fills in.
    return (
      <section
        className={surfaces.panel}
        aria-labelledby={headingId}
      >
        <h2 className={surfaces.heading} id={headingId}>Context</h2>
        <p className={surfaces.note + ' visually-hidden'}>Reading the context…</p>
        <Skeleton shape="form" count={3} />
      </section>
    )
  }

  return (
    <section
      className={surfaces.panel}
      aria-labelledby={headingId}
    >
      <h2 className={surfaces.heading} id={headingId}>Context</h2>
      <p className={surfaces.note}>
        What this case is for. The planner reads it, so a plan is built from
        stated intent rather than from a question string alone.
      </p>

      <label className={surfaces.subpanel}>
        <h3 className={surfaces.subheading}>Purpose</h3>
        <textarea
          aria-label="Purpose"
          value={context.purpose}
          onChange={(e) => setPurpose(e.target.value)}
          placeholder="What are you trying to understand, and why does it matter?"
          disabled={busy}
          rows={3}
        />
      </label>

      {FIELDS.map((field) => (
        <div className={surfaces.subpanel} key={field.key}>
          <h3 className={surfaces.subheading}>{field.label}</h3>
          <ul className={surfaces.panelList}>
            {context[field.key].map((entry, index) => (
              <li key={index} className={surfaces.rowGap}>
                <input
                  aria-label={`${field.noun} ${index + 1}`}
                  value={entry}
                  onChange={(e) =>
                    setList(field.key, context[field.key].map((v, i) => (i === index ? e.target.value : v)))
                  }
                  disabled={busy}
                />
                <Button
                  type="button"
                  onClick={() => setList(field.key, context[field.key].filter((_, i) => i !== index))}
                  disabled={busy}
                  variant="small"
                  aria-label={`Remove ${field.noun} ${index + 1}`}
                >
                  Remove
                </Button>
              </li>
            ))}
          </ul>
          <Button
            type="button"
            onClick={() => setList(field.key, [...context[field.key], ''])}
            disabled={busy}
            variant="small"
          >
            Add {field.noun}
          </Button>
        </div>
      ))}

      {error && <p role="alert">Could not save the context: {error}</p>}
      <div className={surfaces.rowGap}>
        <Button type="button" onClick={save} disabled={busy || !dirty}>
          {busy ? 'Saving…' : 'Save context'}
        </Button>
        {dirty && <span className={surfaces.note}>unsaved edits</span>}
        {context.updated_at && !dirty && (
          <span className={surfaces.note}>saved</span>
        )}
      </div>
    </section>
  )
}
