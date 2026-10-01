import { useEffect, useState } from 'react'
import {
  ApiError,
  type Case,
  deleteCase,
  duplicateCase,
  listCases,
  updateCase,
} from './api'
import { Templates } from './Templates'
import { Button, Skeleton, surfaces } from './lib/ui'
import { MotionSurface } from './lib/motion'

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

  async function reload() {
    setLoading(true)
    setError(null)
    try {
      setCases(await listCases(term))
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void reload()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [term])

  return (
    <section>
      {/* ZONE-A: the page's masthead - its name and the controls that open a
          new case. Same element the workspace's own top uses, so the two
          screens name themselves the same way. */}
      <header>
        <h1>Analysis Cases</h1>
        <div className={surfaces.rowGap}>
          <input
            aria-label="Search cases"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="Search by question or dataset…"
          />
          <Button type="button" onClick={onCreate} variant="primary">
            New case
          </Button>
        </div>
        {error && <p role="alert">Failed to load cases: {error}</p>}
      </header>
      {loading && (
        <>
          <p className="visually-hidden">Loading…</p>
          <Skeleton shape="rows" count={3} />
        </>
      )}
      {!loading && !error && cases.length === 0 && (
        <p>{term ? 'No cases match that search.' : 'No cases yet - create one.'}</p>
      )}
      <ul className="case-list">
        {cases.map((item) => (
          <li key={item.id}>
            <CaseRow
              caseRow={item}
              onOpen={() => onOpen(item.id)}
              onChanged={() => void reload()}
            />
          </li>
        ))}
      </ul>
      {/* Templates are not case children and outlive the case they came from,
          so they live on the front door beside the list rather than inside a
          workspace (P7-SHELL-005). */}
      <Templates onOpen={onOpen} />
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

// One case: opening it is the primary affordance, and the three everyday
// operations sit beside it. Rename is inline - a correction should not need a
// second screen - and delete asks twice, because the core's deletion is final
// and takes the case's on-disk data with it.
function CaseRow({
  caseRow,
  onOpen,
  onChanged,
}: {
  caseRow: Case
  onOpen: () => void
  onChanged: () => void
}) {
  const [editing, setEditing] = useState(false)
  const [armed, setArmed] = useState(false)
  const [question, setQuestion] = useState(caseRow.question)
  const [dataset, setDataset] = useState(caseRow.dataset)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await updateCase(caseRow.id, { question: question.trim(), dataset: dataset.trim() })
      setEditing(false)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function duplicate() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await duplicateCase(caseRow.id)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await deleteCase(caseRow.id)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
      setArmed(false)
    } finally {
      setBusy(false)
    }
  }

  function cancelEdit() {
    setQuestion(caseRow.question)
    setDataset(caseRow.dataset)
    setError(null)
    setEditing(false)
  }

  if (editing) {
    return (
      <form className="case case-editing" onSubmit={save}>
        <label className="visually-hidden" htmlFor={`question-${caseRow.id}`}>
          Question
        </label>
        <input
          id={`question-${caseRow.id}`}
          aria-label="Case question"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          disabled={busy}
        />
        <label className="visually-hidden" htmlFor={`dataset-${caseRow.id}`}>
          Dataset label
        </label>
        <input
          id={`dataset-${caseRow.id}`}
          aria-label="Dataset label"
          value={dataset}
          onChange={(e) => setDataset(e.target.value)}
          disabled={busy}
        />
        <div className={surfaces.buttonRow}>
          <Button type="submit" variant="small" disabled={busy || !question.trim() || !dataset.trim()}>
            {busy ? 'Saving…' : 'Save'}
          </Button>
          <Button type="button" variant="small" onClick={cancelEdit} disabled={busy}>
            Cancel
          </Button>
        </div>
        {error && (
          <p role="alert" className="warn">
            Could not save: {error}
          </p>
        )}
      </form>
    )
  }

  return (
    <MotionSurface variant="enter" className="case">
      {caseRow.duplicate_of && (
        // W2X-010: the only thing separating two rows with the same question
        // and dataset is a timestamp nobody reads, so the row names the case
        // it repeats. The pair was never refused - the notice is what was
        // missing - and the marker points at a case that may since have been
        // deleted, so it degrades to nothing rather than to an error.
        <span className="case-duplicate">
          repeats case {caseRow.duplicate_of.slice(0, 8)}
        </span>
      )}
      <button
        type="button"
        onClick={onOpen}
        // It is the whole row, so it reaches for the case's height: clicking
        // anywhere in the blank part of the row opens the case (W2X-011).
        className="case-open"
        disabled={armed}
      >
        <span className="case-question">{caseRow.question}</span>
        <span className="case-dataset">{caseRow.dataset}</span>
      </button>
      {armed ? (
        // The second click names what it removes: the question is the thing the
        // user would be sorry to lose, so it is the confirmation's subject.
        <div className={surfaces.buttonRow}>
          <Button
            type="button"
            onClick={() => void remove()}
            variant="smallDanger"
            disabled={busy}
            aria-label={`Confirm deleting ${caseRow.question}`}
          >
            {busy ? 'Deleting…' : `Delete “${caseRow.question}” for good`}
          </Button>
          <Button
            type="button"
            onClick={() => setArmed(false)}
            variant="small"
            disabled={busy}
          >
            Keep it
          </Button>
        </div>
      ) : (
        <div className={surfaces.buttonRow}>
          <Button
            type="button"
            onClick={() => {
              setEditing(true)
              setArmed(false)
            }}
            variant="small"
            disabled={busy}
            aria-label={`Rename ${caseRow.question}`}
          >
            Rename
          </Button>
          <Button
            type="button"
            onClick={() => void duplicate()}
            variant="small"
            disabled={busy}
            aria-label={`Duplicate ${caseRow.question}`}
          >
            {busy ? 'Copying…' : 'Duplicate'}
          </Button>
          <Button
            type="button"
            onClick={() => {
              setArmed(true)
              setError(null)
            }}
            variant="smallDanger"
            disabled={busy}
            aria-label={`Delete ${caseRow.question}`}
          >
            Delete
          </Button>
        </div>
      )}
      {error && (
        <p role="alert" className="warn">
          The action failed: {error}
        </p>
      )}
    </MotionSurface>
  )
}
