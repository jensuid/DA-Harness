import { useEffect, useState } from 'react'
import {
  type Case,
  type CaseProgress,
  type ConversationTurn,
  type Dataset,
  type RunSummary,
  getCase,
  getProgress,
  listChat,
  listDatasets,
  listRuns,
  postChat,
} from './api'
import { messageOf } from './CaseList'

// One case: where it stands, what it holds, and the assistant it can be asked.
// Everything here is read on open - progress is derived by the core from the
// artifacts, so the stage the UI shows can never be one the data does not
// support.
export function CaseWorkspace({ caseId, onBack }: { caseId: string; onBack: () => void }) {
  const [caseRow, setCaseRow] = useState<Case | null>(null)
  const [progress, setProgress] = useState<CaseProgress | null>(null)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      const [c, p, ds, rs, chat] = await Promise.all([
        getCase(caseId),
        getProgress(caseId),
        listDatasets(caseId),
        listRuns(caseId),
        listChat(caseId),
      ])
      setCaseRow(c)
      setProgress(p)
      setDatasets(ds)
      setRuns(rs)
      setTurns(chat)
    } catch (err) {
      setError(messageOf(err))
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  if (error && !caseRow) {
    return (
      <section>
        <button type="button" onClick={onBack} className="link">
          ← Back to cases
        </button>
        <p role="alert">Failed to open the case: {error}</p>
      </section>
    )
  }

  return (
    <section>
      <button type="button" onClick={onBack} className="link">
        ← Back to cases
      </button>
      <h1>{caseRow?.question ?? '…'}</h1>
      {error && <p role="alert">Something went wrong: {error}</p>}

      <Workflow progress={progress} />
      <Artifacts datasets={datasets} runs={runs} />
      <Chat caseId={caseId} turns={turns} onTurn={(turn) => setTurns((prior) => [...prior, turn])} />
    </section>
  )
}

function Workflow({ progress }: { progress: CaseProgress | null }) {
  if (!progress) return <p>Loading workflow…</p>
  return (
    <div className="panel">
      <h2>Where this case stands</h2>
      {/* One text node: the sentence stays readable in the DOM and in a screen
          reader, and a test can assert on it without reaching across elements. */}
      <p>
        <strong>
          Stage: {progress.loop_closed ? 'validated' : progress.stage}
          {progress.loop_closed && ' — the trust loop has closed'}
        </strong>
      </p>
      {progress.next_action ? (
        <p>
          Next: <strong>{progress.next_action}</strong>
          <br />
          <code>{progress.next_endpoint}</code>
        </p>
      ) : (
        <p>Every stage has an artifact behind it.</p>
      )}
      <ul className="stages">
        {progress.stages.map((stage) => (
          <li
            key={stage.name}
            className={stage.completed ? 'stage done' : 'stage'}
            aria-label={`stage ${stage.name}: ${stage.completed ? 'complete' : 'pending'}`}
          >
            {stage.completed ? '✓' : '○'} {stage.name}
          </li>
        ))}
      </ul>
    </div>
  )
}

function Artifacts({
  datasets,
  runs,
}: {
  datasets: Dataset[]
  runs: RunSummary[]
}) {
  return (
    <div className="panel">
      <h2>What this case holds</h2>
      <h3>Datasets ({datasets.length})</h3>
      {datasets.length === 0 ? (
        <p className="muted">None attached yet.</p>
      ) : (
        <ul className="items">
          {datasets.map((d) => (
            <li key={d.id}>
              {d.filename} <span className="muted">({d.format})</span>
            </li>
          ))}
        </ul>
      )}
      <h3>Runs ({runs.length})</h3>
      {runs.length === 0 ? (
        <p className="muted">No analysis has run yet.</p>
      ) : (
        <ul className="items">
          {runs.map((r) => (
            <li key={r.id}>
              {r.kind} run — {r.row_count} row(r)
              {r.truncated && ' (truncated)'}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

// The assistant surface that needs nothing but a case. The citations are the
// point: each ground is rendered as a chip so a reviewer can check the answer
// against the artifact, and the badge says which engine spoke - a deterministic
// answer only ever cites what the case actually has.
function Chat({
  caseId,
  turns,
  onTurn,
}: {
  caseId: string
  turns: ConversationTurn[]
  onTurn: (turn: ConversationTurn) => void
}) {
  const [message, setMessage] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function send(event: React.FormEvent) {
    event.preventDefault()
    const text = message.trim()
    if (!text || busy) return
    setBusy(true)
    setError(null)
    try {
      const turn = await postChat(caseId, text)
      onTurn(turn)
      setMessage('')
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <h2>Ask this case</h2>
      <form onSubmit={send}>
        <input
          aria-label="Ask a question"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="How many datasets does this case have?"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !message.trim()}>
          {busy ? 'Asking…' : 'Ask'}
        </button>
      </form>
      {error && (
        <p role="alert">The assistant could not answer: {error}</p>
      )}
      <ul className="chat">
        {turns.map((turn) => (
          <li key={turn.id} className="turn">
            <p className="question">{turn.message}</p>
            <p>{turn.answer}</p>
            <p className="muted">answered by {turn.source}</p>
            {turn.grounds.length > 0 && (
              <ul className="grounds">
                {turn.grounds.map((ground) => (
                  <li key={ground} className="chip">
                    {ground}
                  </li>
                ))}
              </ul>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
