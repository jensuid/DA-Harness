import { useEffect, useState } from 'react'
import {
  type Case,
  type CaseProgress,
  type ClaimTrace,
  type ConversationTurn,
  type Dataset,
  type AgentRole,
  type AgentState,
  type AgentStep,
  type DraftFinding,
  type EdaOp,
  type EdaRequest,
  type EdaResult,
  type Evaluation,
  type EvidenceGraph,
  type EvidenceNode,
  type CaseHistory,
  type LearnWalk,
  type Finding,
  type GeneratedCode,
  type Interpretation,
  type Profile,
  type QualityIssue,
  type RunSummary,
  type ValidationResult,
  acceptFinding,
  attachDataset,
  draftFinding,
  approveAgentStep,
  approveRoleAgentStep,
  evaluateDataset,
  getEvidenceGraph,
  getCaseHistory,
  getLearnWalk,
  runEda,
  generateCode,
  getAgentState,
  getRoleAgentState,
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
  proposeRoleAgentStep,
  rejectAgentStep,
  rejectRoleAgentStep,
  runSql,
  validateFinding,
} from './api'
import { ApiError } from './api'
import { messageOf } from './CaseList'
import { ContextPanel } from './ContextPanel'
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
  // The reviewer is a second agent over the same case, with its own
  // pending step and its own audit trail. Both load read-only: a GET
  // never proposes, so opening a case commits nothing for either role.
  const [reviewer, setReviewer] = useState<AgentState | null>(null)
  const [evidence, setEvidence] = useState<EvidenceGraph | null>(null)
  const [evidenceError, setEvidenceError] = useState<string | null>(null)
  const [evidenceEmpty, setEvidenceEmpty] = useState(false)
  const [history, setHistory] = useState<CaseHistory | null>(null)
  const [historyError, setHistoryError] = useState<string | null>(null)
  const [historyMissing, setHistoryMissing] = useState(false)
  const [walk, setWalk] = useState<LearnWalk | null>(null)
  const [walkError, setWalkError] = useState<string | null>(null)
  const [walkMissing, setWalkMissing] = useState(false)
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
      // The evidence graph is a read-only projection; a 400 is the case having
      // nothing to graph, which is guidance for a young case rather than a
      // failure a reviewer caused.
      try {
        setEvidence(await getEvidenceGraph(caseId))
        setEvidenceError(null)
        setEvidenceEmpty(false)
      } catch (err) {
        setEvidence(null)
        setEvidenceEmpty(err instanceof ApiError && err.status === 400)
        setEvidenceError(messageOf(err))
      }
      // The timeline is a read-only projection; a 404 means the case is unknown,
      // and the workspace's own load reports that at the top - so this panel
      // says it once, as guidance rather than as a second alert.
      try {
        setHistory(await getCaseHistory(caseId))
        setHistoryError(null)
        setHistoryMissing(false)
      } catch (err) {
        setHistory(null)
        setHistoryMissing(err instanceof ApiError && err.status === 404)
        setHistoryError(messageOf(err))
      }
      // LEARN is a read-only projection too; a 404 means the case is unknown and
      // the workspace's own load reports that at the top, so it is guidance
      // here rather than a second alert.
      try {
        setWalk(await getLearnWalk(caseId))
        setWalkError(null)
        setWalkMissing(false)
      } catch (err) {
        setWalk(null)
        setWalkMissing(err instanceof ApiError && err.status === 404)
        setWalkError(messageOf(err))
      }
      // The agents' states are read-only here: a GET never proposes, so loading
      // a page commits nothing, no matter how many roles the case is open in.
      setAgent(await getAgentState(caseId))
      setReviewer(await getRoleAgentState(caseId, 'reviewer'))
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
      <ContextPanel caseId={caseId} onChanged={() => void load()} />
      <LearnPanel walk={walk} error={walkError} missing={walkMissing} />
      <AgentPanel
        caseId={caseId}
        role="analyst"
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
      <EdaPanel caseId={caseId} datasets={datasets} profiles={profiles} />
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
      <AgentPanel
        caseId={caseId}
        role="reviewer"
        agent={reviewer}
        onAgent={setReviewer}
        onChanged={() => void load()}
      />
      <EvidencePanel
        evidence={evidence}
        error={evidenceError}
        empty={evidenceEmpty}
      />
      <HistoryPanel
        history={history}
        error={historyError}
        missing={historyMissing}
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

// LEARN mode, as a surface (P7-SHELL-010). The workflow panel above says where
// the case stands; this says why each step of it exists and what a learner
// should be able to answer before leaving it - the spec's ladder, regrouped
// from the same artifact counts, as teaching rather than as a checklist.
//
// Read-only like the panels beside it: nothing here writes, and the work a
// learner does happens through the endpoints the stages name.
function LearnPanel({
  walk,
  error,
  missing,
}: {
  walk: LearnWalk | null
  error: string | null
  missing: boolean
}) {
  return (
    <div className="panel">
      <h2>Learn this case</h2>
      {missing ? (
        // A 404 means the case is unknown. The workspace loads its own case on
        // mount, so the header already reports it - this panel says so once,
        // as guidance, rather than reporting the same failure twice.
        <p className="muted">The walk could not be read: {error}</p>
      ) : !walk ? (
        <p className="muted">Loading the walk…</p>
      ) : (
        <WalkBody walk={walk} />
      )}
      {!missing && error && (
        <p role="alert">The walk could not be read: {error}</p>
      )}
    </div>
  )
}

function WalkBody({ walk }: { walk: LearnWalk }) {
  return (
    <>
      <p className="muted">
        A guided walk: why ask it, what the data says, how you test it, and
        whether it holds.
      </p>
      {walk.done ? (
        // The core's own discipline: a closed loop means the loop ran, not that
        // the answer is right - so the panel does not graduate the learner on a
        // stronger claim than the artifacts support.
        <p className="muted">
          The walk is complete: every phase is done and a finding has been
          validated. That says the trust loop ran, not that the answer is right.
        </p>
      ) : (
        // One thing to do next, never two - the core guarantees at most one
        // current phase, and the panel says which.
        <p>
          The phase to work on now is{' '}
          {PHASE_TITLES[walk.current ?? ''] ?? walk.current}: {walk.next_action}
          <br />
          <code>{walk.next_endpoint}</code>
        </p>
      )}
      <ul className="items">
        {walk.steps.map((step) => (
          <li key={step.name} aria-label={`phase ${step.name}: ${step.status}`}>
            <h3>{PHASE_TITLES[step.name] ?? step.name}</h3>
            <p className="muted">status: {step.status}</p>
            <p className="muted">{step.purpose}</p>
            <p>
              Can you answer: <strong>{step.prompt}</strong>
            </p>
            <ul className="stages">
              {step.stages.map((stage) => (
                <li
                  key={stage.name}
                  className={stage.completed ? 'stage done' : 'stage'}
                  aria-label={`${stage.action}: ${stage.completed ? 'done' : 'to do'}`}
                >
                  {stage.completed ? '✓' : '○'} {stage.action}
                  <span className="muted"> — {stage.hint}</span>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </>
  )
}

// The core's phase names, as a learner reads them.
const PHASE_TITLES: Record<string, string> = {
  why: 'Why',
  what: 'What',
  how: 'How',
  validate: 'Validate',
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

// What the data cannot support, before the analyst spends a question on it
// (AT-08/AT-09, UX 15). Each issue states what was measured and what it costs,
// at the Data stage rather than only after a finding exists; a dataset with no
// issues says so plainly, because "nothing rendered" is not the same signal as
// "this data is clean".
function QualityList({ quality }: { quality: QualityIssue[] }) {
  if (!quality || quality.length === 0) {
    return <p className="muted quality-clean">No data-quality issues detected.</p>
  }
  return (
    <ul className="quality-issues">
      {quality.map((issue, index) => (
        <li key={index} className={`quality-issue severity-${issue.severity}`}>
          <span className="quality-observed">{issue.observed}</span>
          {' '}
          <span className="quality-impact">Potential impact: {issue.impact}</span>
        </li>
      ))}
    </ul>
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
                {profile && <QualityList quality={profile.quality} />}
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
          {/* P8-CAUSAL-004: a guard refusal is the message, not a footnote on a
              pass. The verdict names the sentence to fix, so a finding that
              outruns its evidence is read as a refusal the analyst can act on
              rather than a warning beside a green tick. */}
          {verdict.status === 'insufficient_evidence' && (
            <p className="fail">
              The verdict refuses this finding rather than passing it with a
              caveat. A dimension the evidence cannot support failed, and its
              sentence above is what to change.
            </p>
          )}
          <ul className="items">
            {verdict.checks.map((check) => (
              <li
                key={check.name}
                className={check.passed ? 'muted' : check.hard ? 'fail' : 'warn'}
              >
                {/* A concern is not a failure: the numbers reproduce and the
                    claim is phrased within them, but the analysis carries a
                    stated limitation. The two read differently, so they render
                    differently (P8-VALID-003). */}
                {check.passed ? '✓' : check.hard ? '✗' : '⚠'} {check.dimension} —{' '}
                {check.detail}
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

// EDA: the "what should I look at first" steps (P7-SHELL-007). Each op
// compiles to read-only SQL under the same gate and row cap as a hand-written
// query and is deliberately not persisted - exploration is not evidence, and a
// finding has to anchor on a query the analyst wrote. The panel says so, so a
// promising segment leads to the runs panel rather than to a false finding.
function EdaPanel({
  caseId,
  datasets,
  profiles,
}: {
  caseId: string
  datasets: Dataset[]
  profiles: Record<string, Profile>
}) {
  const profiled = datasets.filter((d) => profiles[d.id] !== undefined)
  const [chosen, setChosen] = useState('')
  const [op, setOp] = useState<EdaOp>('distribution')
  // The picks are advisory: an effective value is resolved against the current
  // dataset's columns, so a stale pick from another dataset or another op can
  // never be submitted.
  const [by, setBy] = useState('')
  const [measure, setMeasure] = useState('')
  const [x, setX] = useState('')
  const [y, setY] = useState('')
  const [column, setColumn] = useState('')
  const [result, setResult] = useState<EdaResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (profiled.length === 0) {
    return (
      <div className="panel">
        <h2>Explore the data (EDA)</h2>
        <p className="muted">
          Profile a dataset first - the ops read its columns and their types.
        </p>
      </div>
    )
  }

  const dataset = profiled.find((d) => d.id === chosen) ?? profiled[0]
  const profile = profiles[dataset.id]
  const columns = profile.columns
  // A measure or a correlation axis is only meaningful over a numeric column,
  // so numerics are what those pickers offer when the dataset has any. A
  // dataset without one still offers every column, and the core's 400 is the
  // honest answer to the wrong choice.
  const numerics = columns.filter((c) => typeOf(profile, c) === 'numeric')
  const measurable = numerics.length > 0 ? numerics : columns

  const pick = (value: string, options: string[]) =>
    options.includes(value) ? value : options[0]

  const request: EdaRequest = { op }
  if (op === 'segment') {
    request.by = pick(by, columns)
    request.measure = pick(measure, measurable)
  } else if (op === 'correlate') {
    request.x = pick(x, measurable)
    request.y = pick(y, measurable)
  } else {
    request.column = pick(column, columns)
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      setResult(await runEda(caseId, dataset.id, request))
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="panel">
      <h2>Explore the data (EDA)</h2>
      <p className="muted">
        Segment a measure by a category, correlate two columns, or read a
        column's distribution. Each runs read-only like any query, and none is
        kept - an EDA result is exploration, not a finding.
      </p>
      {profiled.length > 1 && (
        <label>
          Explore
          <select
            aria-label="Dataset to explore"
            value={dataset.id}
            onChange={(e) => {
              setChosen(e.target.value)
              setResult(null)
              setError(null)
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
        <label>
          What to look at
          <select
            aria-label="Exploratory operation"
            value={op}
            onChange={(e) => {
              setOp(e.target.value as EdaOp)
              // A result from another op answers a question this one does not
              // ask, so it leaves with the picker that produced it.
              setResult(null)
              setError(null)
            }}
          >
            <option value="distribution">
              Distribution — a column's spread, or its most common values
            </option>
            <option value="segment">
              Segment — group a measure's stats by a category
            </option>
            <option value="correlate">
              Correlate — Pearson r between two numeric columns
            </option>
          </select>
        </label>
        {op === 'segment' && (
          <div className="row">
            <label>
              Group by
              <select
                aria-label="Column to group by"
                value={request.by}
                onChange={(e) => setBy(e.target.value)}
                disabled={busy}
              >
                {columns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Measure
              <select
                aria-label="Measure to summarise"
                value={request.measure}
                onChange={(e) => setMeasure(e.target.value)}
                disabled={busy}
              >
                {measurable.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {op === 'correlate' && (
          <div className="row">
            <label>
              X
              <select
                aria-label="X column"
                value={request.x}
                onChange={(e) => setX(e.target.value)}
                disabled={busy}
              >
                {measurable.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Y
              <select
                aria-label="Y column"
                value={request.y}
                onChange={(e) => setY(e.target.value)}
                disabled={busy}
              >
                {measurable.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {op === 'distribution' && (
          <label>
            Column
            <select
              aria-label="Column to describe"
              value={request.column}
              onChange={(e) => setColumn(e.target.value)}
              disabled={busy}
            >
              {columns.map((c) => (
                <option key={c} value={c}>
                  {c}
                  {typeOf(profile, c) === 'numeric' ? ' (numeric)' : ''}
                </option>
              ))}
            </select>
          </label>
        )}
        <button type="submit" disabled={busy}>
          {busy ? 'Running…' : 'Run the op'}
        </button>
      </form>
      {error && <p role="alert">The op could not run: {error}</p>}
      {result && <EdaResultTable result={result} />}
    </div>
  )
}

// The profile's per-column type family, or '' when the column has no recorded
// stat. It decides which summary a distribution yields and which columns a
// measure may honestly be taken over.
function typeOf(profile: Profile, column: string): string {
  const stats = (profile.stats ?? {}) as Record<string, { type?: string }>
  return stats[column]?.type ?? ''
}

// The columns the core returned are the table; a distribution over a numeric
// column has seven of them and over a category two, and the panel does not
// assume which.
function EdaResultTable({ result }: { result: EdaResult }) {
  return (
    <div className="proposal" data-testid="eda-result">
      <p className="muted">
        {result.row_count} row{result.row_count === 1 ? '' : 's'}
        {result.truncated && ' (truncated)'} — exploration, not evidence: run
        the equivalent query to make a finding of it.
      </p>
      <table className="eda">
        <thead>
          <tr>
            {result.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, i) => (
            <tr key={i}>
              {row.map((value, j) => (
                <td key={j}>{formatValue(value)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Four decimals is as precise as an average or a coefficient needs to be read;
// the full float is noise on the page and the stored value is untouched.
function formatValue(value: unknown): string {
  if (typeof value === 'number') {
    return String(Number(value.toFixed(4)))
  }
  if (value === null || value === undefined) {
    return ''
  }
  return String(value)
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
function EvidencePanel({
  evidence,
  error,
  empty,
}: {
  evidence: EvidenceGraph | null
  error: string | null
  empty: boolean
}) {
  return (
    <div className="panel">
      <h2>Evidence graph</h2>
      {empty ? (
        // A 400 is the case having no artifacts to graph. The core's sentence
        // names what would build one, and a young case is not a failed review.
        <p className="muted">{error}</p>
      ) : !evidence ? (
        <p className="muted">Loading the graph…</p>
      ) : (
        <GraphBody graph={evidence} />
      )}
      {!empty && error && (
        <p role="alert">The graph could not be read: {error}</p>
      )}
    </div>
  )
}

function GraphBody({ graph }: { graph: EvidenceGraph }) {
  const byId = new Map(graph.nodes.map((node) => [node.id, node]))
  // A node with no edge is still part of the case: an attached dataset nothing
  // has queried yet, a plan nothing has run. Leaving it out would make the
  // graph say the case has less than it does.
  const linked = new Set<string>()
  for (const edge of graph.edges) {
    linked.add(edge.source)
    linked.add(edge.target)
  }
  const isolated = graph.nodes.filter((node) => !linked.has(node.id))

  return (
    <>
      <p className="muted">
        {graph.counts.datasets} dataset{graph.counts.datasets === 1 ? '' : 's'},{' '}
        {graph.counts.runs} run{graph.counts.runs === 1 ? '' : 's'},{' '}
        {graph.counts.findings} finding{graph.counts.findings === 1 ? '' : 's'},{' '}
        {graph.counts.charts} chart{graph.counts.charts === 1 ? '' : 's'},{' '}
        {graph.counts.plans} plan{graph.counts.plans === 1 ? '' : 's'}
      </p>
      <h3>Claims and what they rest on</h3>
      {graph.traces.length === 0 ? (
        <p className="muted">No findings yet, so nothing to trace.</p>
      ) : (
        <ul className="items">
          {graph.traces.map((trace) => (
            <li key={trace.finding_id}>
              <ClaimTraceRow
                trace={trace}
                orphan={graph.orphan_findings.includes(trace.finding_id)}
              />
            </li>
          ))}
        </ul>
      )}
      <h3>How each artifact was derived</h3>
      {graph.edges.length === 0 ? (
        <p className="muted">No derivations yet.</p>
      ) : (
        <ul className="items">
          {graph.edges.map((edge, i) => (
            <li key={i} className="muted">
              {nodePhrase(byId.get(edge.source))}{' '}
              {RELATIONS[edge.relation] ?? edge.relation}{' '}
              {nodePhrase(byId.get(edge.target))}
            </li>
          ))}
        </ul>
      )}
      {isolated.length > 0 && (
        <>
          <h3>Attached but not used yet</h3>
          <ul className="items">
            {isolated.map((node) => (
              <li key={node.id} className="muted">
                {node.kind}: {node.label}
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  )
}

// One claim's path back to the data it stands on, as a chain of chips - the
// same shape the chat uses for a citation, so a reviewer reads it the same way.
function ClaimTraceRow({
  trace,
  orphan,
}: {
  trace: ClaimTrace
  orphan: boolean
}) {
  return (
    <div className="run">
      <p>
        <strong>{trace.statement}</strong>
      </p>
      <p className="muted">
        status: {trace.validation_status}
        {orphan && (
          <span className="warn"> — a claim with no source: its run is gone</span>
        )}
      </p>
      <ul className="grounds chain">
        {trace.hops.map((hop, i) => (
          <li key={`${hop.id}-${i}`} className="chip">
            {hop.kind}: {hop.label}
          </li>
        ))}
      </ul>
    </div>
  )
}

// A node as a readable phrase. An edge may name an artifact the case no longer
// has - a finding anchored on a deleted run - and that is worth saying plainly
// rather than rendering as an id.
function nodePhrase(node?: EvidenceNode): string {
  if (!node) return 'an artifact no longer in the case'
  return `${node.kind} “${node.label}”`
}

// The core's relations, as a reader would say them.
const RELATIONS: Record<string, string> = {
  anchored_on: 'anchored on',
  queries: 'queries',
  rendered_from: 'rendered from',
  planned_from: 'planned from',
}

// Case history, as a review surface (P7-SHELL-009). The evidence graph answers
// what backs each claim; this answers the simpler question an analyst asks on
// reopening a case: what did I do here, and when? One line per artifact, in the
// order it happened - the case's own shape, visible without opening every
// panel and comparing timestamps.
//
// Like the graph, it is a read-only projection over persisted rows: nothing
// here writes, and the only way to change the timeline is to change the case
// through the endpoints that own the artifacts.
function HistoryPanel({
  history,
  error,
  missing,
}: {
  history: CaseHistory | null
  error: string | null
  missing: boolean
}) {
  return (
    <div className="panel">
      <h2>Case history</h2>
      {missing ? (
        // A 404 means the case is unknown. The workspace loads its own case on
        // mount, so the header already reports it - this panel says so once, as
        // guidance, rather than reporting the same failure twice.
        <p className="muted">The timeline could not be read: {error}</p>
      ) : !history ? (
        <p className="muted">Loading the timeline…</p>
      ) : (
        <HistoryBody history={history} />
      )}
      {!missing && error && (
        <p role="alert">The timeline could not be read: {error}</p>
      )}
    </div>
  )
}

function HistoryBody({ history }: { history: CaseHistory }) {
  // Only the kinds the case actually has are named, so a young case is not
  // described by a row of zeroes it would have to explain away.
  const parts: string[] = []
  for (const [key, [noun, verb]] of Object.entries(COUNT_KINDS)) {
    const n = history.counts[key] ?? 0
    if (n > 0) parts.push(`${n} ${noun}${n === 1 ? '' : 's'} ${verb}`)
  }
  return (
    <>
      <p className="muted">
        {history.events.length} event{history.events.length === 1 ? '' : 's'} in
        this case{parts.length > 0 ? `, ${parts.join(', ')}` : ''} - oldest first
      </p>
      {history.events.length === 0 ? (
        // The core answers one event for a just-created case, so this is
        // defensive - but a projection that answered nothing would be a bug
        // worth seeing rather than an empty list worth hiding.
        <p className="muted">Nothing has happened in this case yet.</p>
      ) : (
        <ul className="items">
          {history.events.map((event, i) => (
            <li key={`${event.artifact_id ?? event.kind}-${i}`}>
              <p>
                <time className="muted" dateTime={event.timestamp}>
                  {event.timestamp}
                </time>{' '}
                — {EVENT_KINDS[event.kind] ?? event.kind}: {event.label}
              </p>
              {event.detail && <p className="muted">{event.detail}</p>}
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

// Which count key names which event kind, as a noun and a verb, so the summary
// sentence pluralises the noun where English does and still speaks the same
// phrases the timeline below does.
const COUNT_KINDS: Record<string, [string, string]> = {
  datasets: ['dataset', 'attached'],
  profiles: ['dataset', 'profiled'],
  plans: ['plan', 'created'],
  runs: ['run', 'executed'],
  charts: ['chart', 'rendered'],
  findings: ['finding', 'recorded'],
}

// The core's kind constants, as a reader would say them. An unknown kind is
// shown verbatim rather than dropped, so a newer core never makes the timeline
// quieter than it should be.
const EVENT_KINDS: Record<string, string> = {
  case_created: 'case created',
  dataset_attached: 'dataset attached',
  dataset_profiled: 'dataset profiled',
  plan_created: 'plan created',
  run_executed: 'run executed',
  chart_rendered: 'chart rendered',
  finding_recorded: 'finding recorded',
}

// The agents, as surfaces: the analyst (P7-SHELL-003) and the reviewer
// (P7-SHELL-011). Every other panel in this workspace is a step; these are the
// sequences. Each proposes from the case's own artifacts, and the human's yes
// or no is a button - the write never happens without it, and the write then
// runs through the endpoint that owns it, so an agent earns no privilege a
// hand-run case has.
//
// Two panels on one page would be ambiguous if they shared their wording, so
// each role carries its own: a reader and a matcher can tell the analysis loop
// from the audit loop at a glance. The roles never talk to each other - each
// addresses the case, and the case's rows are the shared state.
const AGENT_COPY: Record<AgentRole, {
  title: string
  blurb: string
  loading: string
  propose: string
  repropose: string
  idle: string
  stopped: string
  history: string
  error: string
}> = {
  analyst: {
    title: 'Agent',
    blurb:
      'A plan that executes itself one approved write at a time. It proposes ' +
      'the next step from what the case already has; nothing is written until ' +
      'you approve it, and every write goes through the same endpoint a ' +
      'hand-written call would.',
    loading: "Loading the agent's state\u2026",
    propose: 'Propose the next step',
    repropose: 'Re-derive the next step',
    idle: 'Nothing is pending. Propose a step, or work the panels below by hand.',
    stopped: 'The agent stopped:',
    history: 'What the agent has done',
    error: 'The agent could not proceed:',
  },
  reviewer: {
    title: 'Reviewer',
    blurb:
      "A second agent whose only method is EVALUATE: it takes each finding " +
      "this case recorded and proposes auditing the run that backs it - the " +
      "claim is the finding's own statement, the code the run's own query. " +
      "The verdict is recorded beside the finding and never changes the " +
      "finding's own validation status, because a rerun and an audit are two " +
      "different claims.",
    loading: "Loading the reviewer's state\u2026",
    propose: 'Propose the next audit',
    repropose: 'Re-derive the next audit',
    idle:
      'Nothing is pending review. Either the case has no findings yet, or ' +
      'every finding whose run still carries its code has been audited.',
    stopped: 'The reviewer stopped:',
    history: 'What the reviewer has done',
    error: 'The reviewer could not proceed:',
  },
}

function AgentPanel({
  caseId,
  role,
  agent,
  onAgent,
  onChanged,
}: {
  caseId: string
  role: AgentRole
  agent: AgentState | null
  onAgent: (state: AgentState) => void
  onChanged: () => void
}) {
  const copy = AGENT_COPY[role]
  const [busy, setBusy] = useState(false)
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  // The analyst is the legacy /agent family and the reviewer is the role
  // family; both answer the same four verbs. The analyst keeps calling the
  // functions it always did, so nothing about its behaviour changes.
  const calls =
    role === 'reviewer'
      ? {
          read: () => getRoleAgentState(caseId, role),
          propose: () => proposeRoleAgentStep(caseId, role),
          approve: (id: string) => approveRoleAgentStep(caseId, role, id),
          reject: (id: string, why: string) =>
            rejectRoleAgentStep(caseId, role, id, why),
        }
      : {
          read: () => getAgentState(caseId),
          propose: () => proposeAgentStep(caseId),
          approve: (id: string) => approveAgentStep(caseId, id),
          reject: (id: string, why: string) => rejectAgentStep(caseId, id, why),
        }

  async function refresh() {
    setError(null)
    try {
      onAgent(await calls.read())
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
      onAgent(await calls.propose())
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
        onAgent(await calls.approve(stepId))
      } else {
        onAgent(await calls.reject(stepId, reason))
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
        <h2>{copy.title}</h2>
        <p className="muted">{copy.loading}</p>
      </div>
    )
  }

  const pending = agent.pending
  const finished = !pending && agent.history.some((s) => s.kind === 'end')
  const end = finished ? agent.history[agent.history.length - 1] : null

  return (
    <div className="panel">
      <h2>{copy.title}</h2>
      <p className="muted">{copy.blurb}</p>
      <div className="row">
        <button
          type="button"
          onClick={propose}
          disabled={busy}
          className="small"
        >
          {busy ? 'Working…' : pending ? copy.repropose : copy.propose}
        </button>
      </div>
      {error && (
        <p role="alert">{copy.error} {error}</p>
      )}
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
          {copy.stopped}{' '}
          {end.note || 'no further step is derivable from the case as it stands'}
        </p>
      ) : (
        <p className="muted">{copy.idle}</p>
      )}
      {agent.history.length > 0 && (
        <div className="subpanel">
          <h3>{copy.history}</h3>
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
    case 'evaluate':
      // The reviewer's only step: the claim is the finding's own statement,
      // so the human approves an audit of something concrete.
      return str('claim')
        ? `Audit the finding: ${str('claim')}`
        : 'Audit the finding against the nine axes'
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
