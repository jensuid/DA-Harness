import { useEffect, useState } from 'react'
import {
  type Case,
  type CaseProgress,
  type ConversationTurn,
  type Dataset,
  type DraftFinding,
  type Finding,
  type GeneratedCode,
  type Interpretation,
  type Profile,
  type RunSummary,
  type ValidationResult,
  acceptFinding,
  attachDataset,
  draftFinding,
  generateCode,
  getCase,
  getProgress,
  interpretRun,
  listChat,
  listDatasets,
  listFindings,
  listRuns,
  postChat,
  profileDataset,
  runSql,
  validateFinding,
} from './api'
import { messageOf } from './CaseList'

// One case as the loop the core walks: attach and profile data, propose the
// computation that would answer the question, run it, read what it shows,
// draft the finding it supports, and validate that finding. Every assistant
// panel proposes; the buttons that write state post to the endpoints that own
// it - the runs endpoint for execution, the findings endpoint for a claim - so
// the split stays structural rather than becoming a UI flag.
export function CaseWorkspace({ caseId, onBack }: { caseId: string; onBack: () => void }) {
  const [caseRow, setCaseRow] = useState<Case | null>(null)
  const [progress, setProgress] = useState<CaseProgress | null>(null)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [profiles, setProfiles] = useState<Record<string, Profile>>({})
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [findings, setFindings] = useState<Finding[]>([])
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      const [c, p, ds, rs, fs, chat] = await Promise.all([
        getCase(caseId),
        getProgress(caseId),
        listDatasets(caseId),
        listRuns(caseId),
        listFindings(caseId),
        listChat(caseId),
      ])
      setCaseRow(c)
      setProgress(p)
      setDatasets(ds)
      setRuns(rs)
      setFindings(fs)
      setTurns(chat)
      // Profiles are read-only context for the generator; a dataset without
      // one is unprofiled, and the UI says so rather than guessing.
      const profiled = await Promise.all(
        ds.map((d) =>
          profileDataset(caseId, d.id)
            .then((profile) => [d.id, profile] as const)
            .catch(() => [d.id, null] as const),
        ),
      )
      setProfiles(
        Object.fromEntries(profiled.filter(([, p]) => p !== null)) as Record<string, Profile>,
      )
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
      <DataPanel
        caseId={caseId}
        datasets={datasets}
        profiles={profiles}
        onChanged={() => void load()}
      />
      <RunsPanel
        caseId={caseId}
        runs={runs}
        datasets={datasets}
        onChanged={() => void load()}
      />
      <FindingsPanel
        caseId={caseId}
        findings={findings}
        onChanged={() => void load()}
      />
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

function DataPanel({
  caseId,
  datasets,
  profiles,
  onChanged,
}: {
  caseId: string
  datasets: Dataset[]
  profiles: Record<string, Profile>
  onChanged: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function attach(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setBusy(true)
    setError(null)
    try {
      const dataset = await attachDataset(caseId, file)
      // Profiling is the step the generator reads, so the UI performs it
      // immediately rather than leaving an unprofiled dataset to guess from.
      await profileDataset(caseId, dataset.id)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
      event.target.value = ''
    }
  }

  return (
    <div className="panel">
      <h2>Data</h2>
      <label className="file-button">
        {busy ? 'Attaching…' : 'Attach a CSV, Parquet or Excel file'}
        <input
          type="file"
          accept=".csv,.parquet,.xlsx"
          onChange={attach}
          disabled={busy}
          aria-label="Attach a dataset"
        />
      </label>
      {error && <p role="alert">Attach failed: {error}</p>}
      {datasets.length === 0 ? (
        <p className="muted">No data attached yet - this is where the loop starts.</p>
      ) : (
        <ul className="items">
          {datasets.map((d) => {
            const profile = profiles[d.id]
            return (
              <li key={d.id}>
                <strong>{d.filename}</strong> <span className="muted">({d.format})</span>
                {profile ? (
                  <span className="muted">
                    {' '}— {profile.rows} rows, {profile.columns.length} columns,{' '}
                    {profile.duplicate_rows} duplicate
                  </span>
                ) : (
                  <span className="muted"> — profiling…</span>
                )}
              </li>
            )
          })}
        </ul>
      )}
      {datasets.length > 0 && (
        <GeneratePanel caseId={caseId} dataset={datasets[0]} profile={profiles[datasets[0].id]} />
      )}
    </div>
  )
}

// A question yields the read-only computation that would answer it. The
// proposal writes nothing; Run is the analyst's explicit decision and posts to
// the only endpoint that persists a run.
function GeneratePanel({
  caseId,
  dataset,
  profile,
}: {
  caseId: string
  dataset: Dataset
  profile: Profile | undefined
}) {
  const [question, setQuestion] = useState('')
  const [proposal, setProposal] = useState<GeneratedCode | null>(null)
  const [busy, setBusy] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function propose(event: React.FormEvent) {
    event.preventDefault()
    const text = question.trim()
    if (!text || busy) return
    setBusy(true)
    setError(null)
    try {
      setProposal(await generateCode(caseId, dataset.id, text))
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function run() {
    if (!proposal || running) return
    setRunning(true)
    setError(null)
    try {
      await runSql(caseId, dataset.id, proposal.code)
      setProposal(null)
      setQuestion('')
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setRunning(false)
    }
  }

  if (!profile) {
    return <p className="muted">Profile the dataset before generating code.</p>
  }

  return (
    <div className="subpanel">
      <h3>Ask for the computation</h3>
      <form onSubmit={propose}>
        <input
          aria-label="Question for code generation"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What would you like to know?"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !question.trim()}>
          {busy ? 'Generating…' : 'Generate code'}
        </button>
      </form>
      {error && <p role="alert">Generation failed: {error}</p>}
      {proposal && (
        <div className="proposal">
          // One text node, so the sentence is matchable and screen-reader friendly.
          <p className="muted">
            proposed by {proposal.source} — reads {proposal.columns_used.join(', ')}
          </p>
          <p>{proposal.explanation}</p>
          <pre>{proposal.code}</pre>
          <button type="button" onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run this'}
          </button>
        </div>
      )}
    </div>
  )
}

function RunsPanel({
  caseId,
  runs,
  datasets,
  onChanged,
}: {
  caseId: string
  runs: RunSummary[]
  datasets: Dataset[]
  onChanged: () => void
}) {
  if (runs.length === 0) {
    return (
      <div className="panel">
        <h2>Runs</h2>
        <p className="muted">No analysis has run yet.</p>
      </div>
    )
  }
  return (
    <div className="panel">
      <h2>Runs</h2>
      <ul className="items">
        {runs.map((run) => (
          <li key={run.id}>
            <RunRow
              caseId={caseId}
              run={run}
              datasetLabel={datasets.find((d) => d.id === run.dataset_id)?.filename ?? 'data'}
              onChanged={onChanged}
            />
          </li>
        ))}
      </ul>
    </div>
  )
}

function RunRow({
  caseId,
  run,
  datasetLabel,
  onChanged,
}: {
  caseId: string
  run: RunSummary
  datasetLabel: string
  onChanged: () => void
}) {
  const [reading, setReading] = useState<Interpretation | null>(null)
  const [draft, setDraft] = useState<DraftFinding | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function read() {
    setBusy(true)
    setError(null)
    try {
      setReading(await interpretRun(caseId, run.id))
      setDraft(null)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function draftIt() {
    setBusy(true)
    setError(null)
    try {
      setDraft(await draftFinding(caseId, run.id))
      setReading(null)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="run">
      <p>
        <strong>{run.kind}</strong> over {datasetLabel} — {run.row_count} row
        {run.row_count === 1 ? '' : 's'}
        {run.truncated && ' (truncated)'}
      </p>
      <div className="row">
        <button type="button" onClick={read} disabled={busy} className="small">
          {busy ? 'Working…' : 'Interpret'}
        </button>
        <button type="button" onClick={draftIt} disabled={busy} className="small">
          {busy ? 'Working…' : 'Draft a finding'}
        </button>
      </div>
      {error && <p role="alert">The assistant failed: {error}</p>}
      {reading && (
        <div className="proposal">
          <p className="muted">read by {reading.source}</p>
          <p>{reading.summary}</p>
          {reading.observations.length > 0 && (
            <ul className="items">
              {reading.observations.map((observation, i) => (
                <li key={i}>{observation}</li>
              ))}
            </ul>
          )}
          {reading.caveats.length > 0 && (
            <ul className="items">
              {reading.caveats.map((caveat, i) => (
                <li key={i} className="muted">
                  caveat: {caveat}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {draft && (
        <DraftPanel
          caseId={caseId}
          runId={run.id}
          draft={draft}
          onAccepted={() => {
            setDraft(null)
            onChanged()
          }}
        />
      )}
    </div>
  )
}

// A draft proposes a finding and creates nothing. Accept posts the statement
// to the findings endpoint - the only path that writes one - so the analyst,
// not the assistant, decides what becomes evidence.
function DraftPanel({
  caseId,
  runId,
  draft,
  onAccepted,
}: {
  caseId: string
  runId: string
  draft: DraftFinding
  onAccepted: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function accept() {
    setBusy(true)
    setError(null)
    try {
      await acceptFinding(caseId, runId, draft)
      onAccepted()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="proposal">
      <p className="muted">
        drafted by {draft.source} — accepting records a real finding,
        not_evaluated until validated
      </p>
      <p>{draft.statement}</p>
      <p className="muted">{draft.interpretation}</p>
      {draft.caveat && <p className="muted">caveat: {draft.caveat}</p>}
      {draft.grounds.length > 0 && (
        <ul className="grounds">
          {draft.grounds.map((ground) => (
            <li key={ground} className="chip">
              {ground}
            </li>
          ))}
        </ul>
      )}
      <button type="button" onClick={accept} disabled={busy}>
        {busy ? 'Recording…' : 'Accept as a finding'}
      </button>
      {error && <p role="alert">Could not record the finding: {error}</p>}
    </div>
  )
}

function FindingsPanel({
  caseId,
  findings,
  onChanged,
}: {
  caseId: string
  findings: Finding[]
  onChanged: () => void
}) {
  if (findings.length === 0) {
    return (
      <div className="panel">
        <h2>Findings</h2>
        <p className="muted">No findings yet - a run can draft one.</p>
      </div>
    )
  }
  return (
    <div className="panel">
      <h2>Findings</h2>
      <ul className="items">
        {findings.map((finding) => (
          <li key={finding.id}>
            <FindingRow caseId={caseId} finding={finding} onChanged={onChanged} />
          </li>
        ))}
      </ul>
    </div>
  )
}

function FindingRow({
  caseId,
  finding,
  onChanged,
}: {
  caseId: string
  finding: Finding
  onChanged: () => void
}) {
  const [verdict, setVerdict] = useState<ValidationResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function validate() {
    setBusy(true)
    setError(null)
    try {
      setVerdict(await validateFinding(caseId, finding.id))
      // The verdict persists on the finding, so the panel reloads rather than
      // showing a stale not_evaluated next time.
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="run">
      <p>{finding.statement}</p>
      <p className="muted">status: {finding.validation_status}</p>
      {verdict && (
        <div className="proposal">
          <p><strong>Verdict: {verdict.status}</strong></p>
          <ul className="items">
            {verdict.checks.map((check) => (
              <li key={check.name} className={check.passed ? 'muted' : 'warn'}>
                {check.passed ? '✓' : '✗'} {check.name} — {check.detail}
              </li>
            ))}
          </ul>
        </div>
      )}
      <button type="button" onClick={validate} disabled={busy} className="small">
        {busy ? 'Validating…' : 'Validate'}
      </button>
      {error && <p role="alert">Validation failed: {error}</p>}
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
      {error && <p role="alert">The assistant could not answer: {error}</p>}
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
