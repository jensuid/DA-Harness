import { useEffect, useState } from 'react'
import { createCase, getHealth } from './api'
import { messageOf } from './CaseList'

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

  useEffect(() => {
    getHealth()
      .then((h) => setCoreStatus(h.status === 'ok' ? 'reachable' : `unexpected: ${h.status}`))
      .catch(() => setCoreStatus('unreachable'))
  }, [])

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault()
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
      <button type="button" onClick={onCancel} className="link">
        ← Back to cases
      </button>
      <h1>New Analysis Case</h1>
      <p>Core status: {coreStatus}</p>
      <form onSubmit={handleSubmit}>
        <label htmlFor="question">Question</label>
        <input
          id="question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Why did revenue decline?"
          required
        />
        <label htmlFor="dataset">Dataset</label>
        <input
          id="dataset"
          value={dataset}
          onChange={(e) => setDataset(e.target.value)}
          placeholder="sales.csv"
          required
        />
        <button type="submit" disabled={saving}>
          {saving ? 'Saving…' : 'Create case'}
        </button>
        {error && <p role="alert">Failed: {error}</p>}
      </form>
    </section>
  )
}
