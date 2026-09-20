import { useEffect, useState } from 'react'
import { ApiError, type Case, listCases } from './api'

// The list is the front door: find a case again, or start a new one. The search
// box is the API's q parameter - a literal substring over question and dataset.
export function CaseList({
  onOpen,
  onCreate,
}: {
  onOpen: (id: string) => void
  onCreate: () => void
}) {
  const [term, setTerm] = useState('')
  const [cases, setCases] = useState<Case[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setError(null)
    listCases(term)
      .then(setCases)
      .catch((err) => setError(messageOf(err)))
      .finally(() => setLoading(false))
  }, [term])

  return (
    <section>
      <h1>Analysis Cases</h1>
      <div className="row">
        <input
          aria-label="Search cases"
          value={term}
          onChange={(e) => setTerm(e.target.value)}
          placeholder="Search by question or dataset…"
        />
        <button type="button" onClick={onCreate}>
          New case
        </button>
      </div>
      {error && <p role="alert">Failed to load cases: {error}</p>}
      {loading && <p>Loading…</p>}
      {!loading && !error && cases.length === 0 && (
        <p>{term ? 'No cases match that search.' : 'No cases yet - create one.'}</p>
      )}
      <ul className="case-list">
        {cases.map((item) => (
          <li key={item.id}>
            <button type="button" onClick={() => onOpen(item.id)} className="case">
              <span className="case-question">{item.question}</span>
              <span className="case-dataset">{item.dataset}</span>
            </button>
          </li>
        ))}
      </ul>
    </section>
  )
}

export function messageOf(err: unknown): string {
  if (err instanceof ApiError) {
    // The id finds this fault's traceback in the core's log, so it is worth
    // showing: "error abc12345" is something someone can look up, and "HTTP
    // 500" alone is not.
    const id = err.requestId ? ` error ${err.requestId.slice(0, 8)}` : ''
    return `${err.message} (HTTP ${err.status}${id})`
  }
  return err instanceof Error ? err.message : 'unknown error'
}
