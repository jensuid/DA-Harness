import { useEffect, useState } from 'react'
import {
  type Case,
  type CaseProgress,
  type ConversationTurn,
  type Dataset,
  type AgentState,
  type AgentStep,
  type DraftFinding,
  type Evaluation,
  type Finding,
  type GeneratedCode,
  type Interpretation,
  type Profile,
  type RunSummary,
  type ValidationResult,
  acceptFinding,
  attachDataset,
  draftFinding,
  approveAgentStep,
  evaluateDataset,
  generateCode,
  getAgentState,
  getCase,
  getProgress,
  interpretRun,
  listChat,
  listDatasets,
  listEvaluations,
  listFindings,
  listRuns,
  postChat,
  profileDataset,
  proposeAgentStep,
  rejectAgentStep,
  runSql,
  validateFinding,
} from './api'
import { messageOf } from './CaseList'
import { PromoteTemplate } from './Templates'

// One case as the loop the core walks: attach and profile data, propose the
// computation that would answer the question, run it, read what it shows,
// draft the finding it supports, and validate that finding. Every assistant
// panel proposes; the buttons that write state post to the endpoints that own
// it - the runs endpoint for execution, the findings endpoint for a claim - so
// the split stays structural rather than becoming a UI flag.
export function CaseWorkspace({
  caseId,
  onBack,
  onOpenCase,
}: {
  caseId: string
  onBack: () => void
  // A prior case cited by an answer is opened as its own workspace (P7-SHELL-006).
  onOpenCase: (caseId: string) => void
}) {
  const [caseRow, setCaseRow] = useState<Case | null>(null)
  const [progress, setProgress] = useState<CaseProgress | null>(null)
  const [datasets, setDatasets] = useState<Dataset[]>([])
  const [profiles, setProfiles] = useState<Record<string, Profile>>({})
  const [runs, setRuns] = useState<RunSummary[]>([])
  const [findings, setFindings] = useState<Finding[]>([])
  const [turns, setTurns] = useState<ConversationTurn[]>([])
  const [evaluations, setEvaluations] = useState<Evaluation[]>([])
  const [agent, setAgent] = useState<AgentState | null>(null)
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
      // Audits belong to a dataset, not the case, so they load once the
      // datasets are known. A dataset without a profile cannot have been
      // audited usefully, so its audits are not shown.
      const audited = await Promise.all(
        ds.map((d) =>
          listEvaluations(caseId, d.id)
            .then((evaluations) => evaluations.map((evaluation) => [d.id, evaluation] as const))
            .catch(() => [] as const),
        ),
      )
      setEvaluations(audited.flat().map(([, evaluation]) => evaluation))
      // The agent's state is read-only here: a GET never proposes, so loading a
      // page commits nothing.
      setAgent(await getAgentState(caseId))
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
      <AgentPanel
        caseId={caseId}
        agent={agent}
        onAgent={setAgent}
        onChanged={() => void load()}
      />
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
      <EvaluatePanel
        caseId={caseId}
        datasets={datasets}
        profiles={profiles}
        evaluations={evaluations}
        onChanged={() => void load()}
      />
      <Chat
        caseId={caseId}
        turns={turns}
        onTurn={(turn) => setTurns((prior) => [...prior, turn])}
        onOpenCase={onOpenCase}
      />
      <PromoteTemplate caseId={caseId} question={caseRow?.question ?? ''} />
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
          </li>
        ))}
      </ul>
    </div>
  )
}

// EVALUATE mode: audit work that came from elsewhere (P7-SHELL-002). The
// ANALYZE loop above serves the analyst's own work; this panel points the same
// primitives at someone else's. The user pastes the artifact's code and the
// claim it was offered to support, and reads nine verdicts, each a sentence
// rather than a code.
//
// Every other panel's discipline applies unchanged: the submit posts to the
// evaluate endpoint and nothing else, and the endpoint - not the panel - runs
// the code under the read-only gate, the row cap and the hard sandbox. The
// panel never decides whether work is sound; it renders what the core found.
function EvaluatePanel({
  caseId,
  datasets,
  profiles,
  evaluations,
  onChanged,
}: {
  caseId: string
  datasets: Dataset[]
  profiles: Record<string, Profile>
  evaluations: Evaluation[]
  onChanged: () => void
}) {
  // An audit is meaningless without a profile: the Data and Quality axes judge
  // the code against profiled columns. The panel is absent rather than offering
  // a submission that cannot succeed.
  const profiled = datasets.filter((d) => profiles[d.id] !== undefined)
  const [chosen, setChosen] = useState('')
  const [kind, setKind] = useState<'sql' | 'python'>('sql')
  const [code, setCode] = useState('')
  const [claim, setClaim] = useState('')
  const [audit, setAudit] = useState<Evaluation | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (profiled.length === 0) {
    return (
      <div className="panel">
        <h2>Audit submitted work (EVALUATE)</h2>
        <p className="muted">
          Attach and profile a dataset first - an audit judges the work against
          the data it claims to read.
        </p>
      </div>
    )
  }

  const datasetId = chosen || profiled[0].id

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      setAudit(await evaluateDataset(caseId, datasetId, code, claim, kind))
      // The audit is persisted by the core, so the panel reloads the record
      // rather than trusting its own copy of it.
      onChanged()
    } catch (err) {
      // A 400 is part of the contract: a non-read-only artifact is refused
      // before anything executes, and its detail is the actionable thing. It
      // is shown as a sentence, not as a broken panel.
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  const prior = evaluations.filter((e) => e.dataset_id === datasetId)

  return (
    <div className="panel">
      <h2>Audit submitted work (EVALUATE)</h2>
      <p className="muted">
        Paste work that came from elsewhere and the claim it was offered to
        support. DAH runs it against the data and answers nine questions, each
        with a verdict and a sentence.
      </p>
      {profiled.length > 1 && (
        <label>
          Audit against
          <select
            aria-label="Dataset to audit against"
            value={datasetId}
            onChange={(e) => {
              setChosen(e.target.value)
              setAudit(null)
            }}
          >
            {profiled.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename}
              </option>
            ))}
          </select>
        </label>
      )}
      <form onSubmit={submit}>
        <div className="row">
          <label className="kind-toggle">
            <input
              type="radio"
              name="artifact-kind"
              value="sql"
              checked={kind === 'sql'}
              onChange={() => setKind('sql')}
            />{' '}
            SQL
          </label>
          <label className="kind-toggle">
            <input
              type="radio"
              name="artifact-kind"
              value="python"
              checked={kind === 'python'}
              onChange={() => setKind('python')}
            />{' '}
            Python
          </label>
        </div>
        <label>
          The artifact's code
          <textarea
            aria-label="The artifact's code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={
              kind === 'sql'
                ? 'SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region'
                : "result = [{'total': sum(r['revenue'] for r in dataset.rows)}]"
            }
            rows={4}
            disabled={busy}
          />
        </label>
        <label>
          The claim it supports
          <input
            aria-label="The claim the code was offered to support"
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="Revenue is higher in north than south"
            disabled={busy}
          />
        </label>
        <button type="submit" disabled={busy || !code.trim() || !claim.trim()}>
          {busy ? 'Auditing…' : 'Audit this work'}
        </button>
      </form>
      {error && <p role="alert">The audit could not run: {error}</p>}
      {audit && <Audit evaluation={audit} />}
      {prior.length > 0 && (
        <div className="subpanel">
          <h3>Recorded audits</h3>
          <ul className="items">
            {prior.map((evaluation) => (
              <li key={evaluation.id}>
                <RecordedAudit evaluation={evaluation} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// The nine axes in the spec's own order. The order is the order a reader asks
// them in, so the audit does not reorder it.
const AXES = [
  'question', 'data', 'quality', 'method', 'calculation',
  'evidence', 'claim', 'visualization', 'limitations',
]

function Audit({ evaluation }: { evaluation: Evaluation }) {
  const byAxis = new Map(evaluation.findings.map((f) => [f.axis, f]))
  return (
    <div className="proposal" data-testid="audit">
      <p className="muted">
        audited by {evaluation.source} — the artifact is stored as a run and can
        be re-read in the Runs panel
      </p>
      <ul className="items">
        {AXES.map((axis) => {
          const finding = byAxis.get(axis)
          if (!finding) return null
          return (
            <li key={axis}>
              <Verdict verdict={finding.verdict} axis={axis} detail={finding.detail} />
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// The verdict is the summary and the sentence is the substance, so neither is
// rendered without the other. Three states, not a score - the core's own
// decision, kept here rather than flattened into a number the axes cannot have.
function Verdict({
  verdict,
  axis,
  detail,
}: {
  verdict: string
  axis: string
  detail: string
}) {
  const mark = verdict === 'pass' ? '✓' : verdict === 'concern' ? '!' : '✗'
  return (
    <p>
      <span className={`verdict ${verdict}`}>{mark} {axis}</span>
      <span className="muted"> — {detail}</span>
    </p>
  )
}

function RecordedAudit({ evaluation }: { evaluation: Evaluation }) {
  const summary = evaluation.findings
    .filter((f) => f.verdict !== 'pass')
    .map((f) => `${f.axis}: ${f.verdict}`)
  return (
    <div className="run">
      <p><strong>{evaluation.claim}</strong></p>
      <p className="muted">
        {evaluation.artifact_kind} —{' '}
        {summary.length > 0 ? summary.join(', ') : 'every axis passed'}
      </p>
    </div>
  )
}

// One citation. A `case:` ground names a case the analyst can go and read, so
// it is a button; every other kind is a chip as it always was. The prior case's
// own question is the label because that is how the analyst recognises it - a
// uuid would not be.
function Ground({
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

// The agent: the loop's driver, as a surface (P7-SHELL-003). Every other panel
// in this workspace is a step; this one is the sequence. It proposes the next
// step from the case's own artifacts, and the human's yes or no is a button -
// the write never happens without it, and the write then runs through the
// endpoint that owns it, so the agent earns no privilege a hand-run case has.
function AgentPanel({
  caseId,
  agent,
  onAgent,
  onChanged,
}: {
  caseId: string
  agent: AgentState | null
  onAgent: (state: AgentState) => void
  onChanged: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)

  async function refresh() {
    setError(null)
    try {
      onAgent(await getAgentState(caseId))
    } catch (err) {
      setError(messageOf(err))
    }
  }

  async function propose() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      // Idempotent by contract: a pending step comes back unchanged, so an
      // impatient second click is a no-op rather than a second write.
      onAgent(await proposeAgentStep(caseId))
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function decide(approve: boolean) {
    const stepId = agent?.pending?.id
    if (busy || !stepId) return
    setBusy(true)
    setError(null)
    try {
      if (approve) {
        // Approving runs the step and the response carries the next proposal,
        // so there is no second call to see what comes next.
        onAgent(await approveAgentStep(caseId, stepId))
      } else {
        onAgent(await rejectAgentStep(caseId, stepId, reason))
        setReason('')
      }
      // The write changed the case's artifacts, so the whole workspace reloads -
      // a rejected draft leaves no finding behind, and an approved run appears
      // in the Runs panel.
      onChanged()
    } catch (err) {
      // A 409 means the step is no longer the case's pending one: another
      // approval moved the case on while this page sat open. Resync, then show
      // the sentence - refresh clears the error, so it runs first or the
      // message would vanish a tick after it appeared.
      await refresh()
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  if (!agent) {
    return (
      <div className="panel">
        <h2>Agent</h2>
        <p className="muted">Loading the agent's state…</p>
      </div>
    )
  }

  const pending = agent.pending
  const finished = !pending && agent.history.some((s) => s.kind === 'end')
  const end = finished ? agent.history[agent.history.length - 1] : null

  return (
    <div className="panel">
      <h2>Agent</h2>
      <p className="muted">
        A plan that executes itself one approved write at a time. It proposes
        the next step from what the case already has; nothing is written until
        you approve it, and every write goes through the same endpoint a
        hand-written call would.
      </p>
      <div className="row">
        <button
          type="button"
          onClick={propose}
          disabled={busy}
          className="small"
        >
          {busy ? 'Working…' : pending ? 'Re-derive the next step' : 'Propose the next step'}
        </button>
      </div>
      {error && <p role="alert">The agent could not proceed: {error}</p>}
      {pending ? (
        <div className="proposal">
          <p className="muted">
            proposed by {pending.source} — approve to run it, or reject with your
            reason
          </p>
          <p><strong>{stepSentence(pending)}</strong></p>
          <div className="row">
            <button
              type="button"
              onClick={() => void decide(true)}
              disabled={busy}
              className="small"
            >
              {busy ? 'Running…' : 'Approve and run'}
            </button>
            <button
              type="button"
              onClick={() => void decide(false)}
              disabled={busy}
              className="small"
            >
              {busy ? 'Recording…' : 'Reject'}
            </button>
          </div>
          <input
            aria-label="Reason for rejecting (optional)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why this step is wrong - recorded with it"
            disabled={busy}
          />
        </div>
      ) : end ? (
        <p className="muted">
          The agent stopped:{' '}
          {end.note || 'no further step is derivable from the case as it stands'}
        </p>
      ) : (
        <p className="muted">
          Nothing is pending. Propose a step, or work the panels below by hand.
        </p>
      )}
      {agent.history.length > 0 && (
        <div className="subpanel">
          <h3>What the agent has done</h3>
          <ul className="items">
            {agent.history
              .slice()
              .reverse()
              .map((step) => (
                <li key={step.id} className="run">
                  <StepStatus step={step} />
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// What a step will do, as a sentence built from the payload the core settled at
// proposal time. The human approves something concrete, not a promise - and
// the sentence is the same one the step's own write produced, so the proposal
// and the record cannot drift apart.
function stepSentence(step: AgentStep): string {
  const p = step.payload
  const str = (key: string) => String(p[key] ?? '')
  switch (step.kind) {
    case 'profile':
      return `Profile ${str('filename') || 'the attached dataset'}`
    case 'plan':
      return 'Plan the analysis from the profile'
    case 'analyze':
      return `Run ${str('kind') || 'the'} analysis${p.variant ? ` (variant ${p.variant})` : ''}`
    case 'interpret':
      return 'Interpret the last run'
    case 'accept':
      return `Accept the draft as a finding${str('statement') ? `: ${str('statement')}` : ''}`
    case 'chart':
      return `Render a ${str('kind') || 'bar'} chart of ${str('y')} by ${str('x')}`
    case 'validate':
      return 'Validate the finding'
    case 'end':
      return step.note || 'stop'
    default:
      return step.kind
  }
}

function StepStatus({ step }: { step: AgentStep }) {
  const mark = step.status === 'done' ? '✓' : step.status === 'rejected' ? '✗' : '○'
  return (
    <p>
      <span className={`verdict ${step.status === 'done' ? 'pass' : step.status === 'rejected' ? 'fail' : 'concern'}`}>
        {mark} {step.kind}
      </span>
      <span className="muted"> — {step.note || stepSentence(step)}</span>
      {step.status === 'rejected' && step.note && (
        <span className="muted"> (rejected: {step.note})</span>
      )}
    </p>
  )
}
