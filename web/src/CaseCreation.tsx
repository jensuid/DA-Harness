import { useEffect, useState } from 'react'
import { createCase, getHealth } from './api'
import { messageOf } from './CaseList'
import { Button } from './lib/ui'

export function CaseCreation({
  onCreated,
  onCancel,
}: {
  onCreated: (caseId: string) => void
  onCancel: () => void
}) {
  const [question, setQuestion] = useState('')
  const [dataset, setDataset] = useState('')
  const [coreStatus, setCoreStatus] = useState('checking…')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
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
    try {
      const created = await createCase({ question, dataset })
      // The core returns the persisted case; open it straight into its
      // workspace rather than dumping the analyst back on an empty form.
      onCreated(created.id)
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
        <Button type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Create case'}
        </Button>
        {error && <p role="alert">Failed: {error}</p>}
      </form>
    </section>
  )
}
