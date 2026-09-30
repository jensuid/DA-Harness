import { useEffect, useState } from 'react'
import { type Case, createCase, getHealth } from './api'
import { messageOf } from './CaseList'
import { Button } from './lib/ui'

export function CaseCreation({
  onCreated,
  onCancel,
  onView,
}: {
  onCreated: (caseId: string) => void
  onCancel: () => void
  // W2X-010: the notice that a duplicate exists is only useful if the case it
  // names can be reached from it, so the form asks its parent to show the one
  // it found rather than knowing how navigation works.
  onView?: (caseId: string) => void
}) {
  const [question, setQuestion] = useState('')
  const [dataset, setDataset] = useState('')
  const [coreStatus, setCoreStatus] = useState('checking…')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [duplicate, setDuplicate] = useState<Case | null>(null)
  // W2X-002: the required fields are enforced here rather than by the browser.
  // Native HTML5 validation refuses the submit with no visible message in a
  // headless context, and a first-time analyst only learns a field is required
  // by guessing. This carries the sentence the browser would have shown.
  const [missing, setMissing] = useState<string[]>([])
  const REQUIRED = [
    { name: 'question', label: 'Question' },
    { name: 'dataset', label: 'Dataset' },
  ] as const

  function missingFields() {
    return REQUIRED.filter((f) => {
      if (f.name === 'question') return question.trim() === ''
      return dataset.trim() === ''
    }).map((f) => f.label)
  }

  function showInlineValidation() {
    const blanks = missingFields()
    setMissing(blanks)
    return blanks.length === 0
  }

  useEffect(() => {
    getHealth()
      .then((h) => setCoreStatus(h.status === 'ok' ? 'reachable' : `unexpected: ${h.status}`))
      .catch(() => setCoreStatus('unreachable'))
  }, [])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
    if (!showInlineValidation()) return
    setSaving(true)
    setError(null)
    setDuplicate(null)
    try {
      const created = await createCase({ question, dataset })
      // W2X-010: the core answers with the case this one repeats when its
      // question and dataset match an existing one exactly, so the form says
      // it rather than letting an identical row appear later with no way to
      // tell the two apart but their timestamps. The pair is not refused - a
      // duplicate is a case in its own right, and re-running an old question
      // is a normal thing to do - so the case is made and the notice stays.
      if (created.duplicate_of) {
        setDuplicate(created)
      } else {
        // The core returns the persisted case; open it straight into its
        // workspace rather than dumping the analyst back on an empty form.
        onCreated(created.id)
      }
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setSaving(false)
    }
  }

  return (
    <section>
      <Button type="button" onClick={onCancel} variant="link">
        ← Cancel
      </Button>
      <h1>New Analysis Case</h1>
      <p>Core status: {coreStatus}</p>
      <form onSubmit={handleSubmit}>
        <label htmlFor="question">Question *</label>
        <input
          id="question"
          value={question}
          onChange={(e) => {
            setQuestion(e.target.value)
            if (e.target.value.trim() !== '') {
              setMissing((m) => m.filter((f) => f !== 'Question'))
            }
          }}
          placeholder="Why did revenue decline?"
          aria-invalid={missing.includes('Question')}
        />
        {missing.includes('Question') && (
          <p className="field-error" role="alert">
            A question is required - state what you want to know.
          </p>
        )}
        <label htmlFor="dataset">Dataset *</label>
        <input
          id="dataset"
          value={dataset}
          onChange={(e) => {
            setDataset(e.target.value)
            if (e.target.value.trim() !== '') {
              setMissing((m) => m.filter((f) => f !== 'Dataset'))
            }
          }}
          placeholder="sales.csv"
          aria-invalid={missing.includes('Dataset')}
        />
        {missing.includes('Dataset') && (
          <p className="field-error" role="alert">
            A dataset filename is required - the name of the CSV, Parquet or
            Excel file, e.g. sales.csv. You attach the file itself inside the
            case.
          </p>
        )}
        <Button type="submit" disabled={saving} variant="primary">
          {saving ? 'Saving…' : 'Create case'}
        </Button>
        {error && <p role="alert">Failed: {error}</p>}
      </form>
      {duplicate && (
        <p className="duplicate-notice" role="status">
          Created - but a case already asks “{duplicate.question}” about{' '}
          {duplicate.dataset}. This one is separate; keep it if you meant to
          re-run the question.
          {onView && (
            <Button
              type="button"
              variant="link"
              onClick={() => onView(duplicate.duplicate_of ?? '')}
            >
              See the existing case
            </Button>
          )}
        </p>
      )}
    </section>
  )
}
