/**
 * P9-F1-001: the workspace is a composition root. The state lives here;
 * every surface it renders moved into `web/src/panels/` and is pure over
 * its props. The three-zone layout (UX 8) is unchanged, as is every
 * panel's contract - the split is structural, and the tests that assert
 * the rendered output are the contract that it changed nothing.
 */
import { useEffect, useId, useState } from 'react'
import {
  type Case,
  type CaseContext,
  type CaseProgress,
  type CaseHistory,
  type ConversationTurn,
  type Dataset,
  type Evaluation,
  type EvidenceGraph,
  type Finding,
  type LearnWalk,
  type Profile,
  type RunSummary,
  type AgentState,
} from './api'
import {
  getAgentState,
  getCase,
  getCaseHistory,
  getContext,
  getEvidenceGraph,
  getLearnWalk,
  getProfile,
  getProgress,
  getRoleAgentState,
  listChat,
  listDatasets,
  listEvaluations,
  listFindings,
  listRuns,
} from './api'
import { ApiError } from './api'
import { messageOf } from './CaseList'
import { Button, surfaces } from './lib/ui'
import { MotionSurface } from './lib/motion'
import { AgentPanel } from './panels/AgentPanel'
import { CaseOverview } from './panels/CaseOverview'
import { Chat } from './panels/Chat'
import { ContextPanel } from './ContextPanel'
import { DataPanel } from './panels/DataPanel'
import { DecisionPanel } from './DecisionPanel'
import { EdaPanel } from './panels/EdaPanel'
import { EvaluatePanel } from './panels/EvaluatePanel'
import { EvidencePanel } from './panels/EvidencePanel'
import { FindingsPanel } from './panels/FindingsPanel'
import { HistoryPanel } from './panels/HistoryPanel'
import { LearnPanel } from './panels/LearnPanel'
import { PlanPanel } from './panels/PlanPanel'
import { PromoteTemplate } from './Templates'
import { Disclosure } from './lib/disclosure'
import { historySummary } from './panels/HistoryPanel'
import { walkSummary } from './panels/LearnPanel'

/**
 * W2X-008: the case's own record.
 *
 * Learn, history and the template promotion are orientation rather than work -
 * they describe what the case has rather than doing a step in it - but the
 * walk measured them occupying the first screen alongside six other panels,
 * four of them relevant only late in the loop. They are one group here, a
 * single collapsed container the analyst opens when they want the record, so
 * the orientation zone is the rail, the overview and the question - the three
 * things that orient - and the record is a click away rather than three panels
 * of scroll.
 *
 * The group stays in the orientation zone: a case's record is what the zone is
 * for, and moving a panel between zones is a bigger change than the density
 * asks for. The group's own open state starts closed, because the surfaces
 * inside it carry their own disclosures and each says its own count.
 */
export function CaseRecord({
  caseId,
  question,
  walk,
  walkError,
  walkMissing,
  history,
  historyError,
  historyMissing,
}: {
  caseId: string
  question: string
  walk: LearnWalk | null
  walkError: string | null
  walkMissing: boolean
  history: CaseHistory | null
  historyError: string | null
  historyMissing: boolean
}) {
  const headingId = useId()
  return (
    <section
      className={surfaces.panel + ' zone-record'}
      aria-labelledby={headingId}
    >
      <h2 className={surfaces.heading} id={headingId}>Case record</h2>
      <p className={surfaces.note}>
        The walk, the timeline and this case's template. Each opens to its own
        detail.
      </p>
      <div className="record-group">
        <Disclosure
          id="record-learn"
          summary={walkSummary(walk, walkError)}
        >
          <LearnPanel walk={walk} error={walkError} missing={walkMissing} />
        </Disclosure>
        <Disclosure
          id="record-history"
          summary={historySummary(history, historyError)}
        >
          <HistoryPanel history={history} error={historyError} missing={historyMissing} />
        </Disclosure>
        <Disclosure id="record-template" summary="Save as a template">
          <PromoteTemplate caseId={caseId} question={question} />
        </Disclosure>
      </div>
    </section>
  )
}

// The surfaces the case is still waiting on, as one sentence. A hidden panel's
// empty state is not gone - it is here, named, so the analyst can see the
// shape of the case they have not built yet without scrolling past it.
//
// Each line reads a count the workspace already loads, so the sentence and the
// panels cannot disagree. The evidence graph is the one projection: it is read
// through a projection that can answer 400 for a young case, so its own loaded
// state is the signal, not the count.
export function pendingPanels(state: {
  runs: number
  findings: number
  evidence: boolean
  evaluations: number
}): string[] {
  const pending: string[] = []
  if (state.findings === 0) pending.push('a finding')
  if (!state.evidence) pending.push('the evidence graph')
  if (state.evaluations === 0) pending.push('an audit')
  return pending
}

import { RefinePanel } from './RefinePanel'
import { RunsPanel } from './panels/RunsPanel'
import { WorkflowRail } from './panels/WorkflowRail'

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
  // The case's stated intent. The overview's OBJECTIVE reads its purpose, and
  // a case that never stated one falls back to the question it was created
  // with - so the overview always answers "what is this case for".
  const [context, setContext] = useState<CaseContext | null>(null)
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
  // SKEL: the workspace's own read is in flight. This is true only until the
  // first `load()` completes - a reload after a write leaves it false, so a
  // panel keeps rendering the data it has while the refetch happens rather
  // than flashing its skeleton at every save. The panels that read
  // workspace-owned state cannot tell "the fetch has not landed" from "the
  // case has nothing" on their own, so this is the one signal that separates
  // a young case from a case the shell has not read yet.
  const [loading, setLoading] = useState(true)

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
      // The context is read-only here: the ContextPanel owns editing it, and
      // this copy is only the overview's objective. A case that has none is
      // not an error, so a failure degrades to the question rather than
      // failing the workspace.
      try {
        setContext(await getContext(caseId))
      } catch {
        setContext(null)
      }
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
      // W-008: the read is a GET. A mount used to POST here, so opening a
      // case recomputed a profile that already existed - twice, under strict
      // mode - and silently completed the step the rail calls the analyst's.
      // A dataset without a profile stays unprofiled until the analyst asks;
      // the panel says so rather than writing on a read.
      const profiled = await Promise.all(
        ds.map((d) =>
          getProfile(caseId, d.id)
            .then((profile) => [d.id, profile] as const)
            .catch(() => [d.id, null] as const),
        ),
      )
      setProfiles(
        Object.fromEntries(profiled.filter(([, p]) => p !== null)) as Record<string, Profile>,
      )
    } catch (err) {
      setError(messageOf(err))
    } finally {
      // SKEL: the first read is over; every panel that was waiting on the
      // workspace's own state renders its real shape now.
      setLoading(false)
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  if (error && !caseRow) {
    return (
      <section>
        <Button type="button" onClick={onBack} variant="link">
          ← Back to cases
        </Button>
        <p role="alert">Failed to open the case: {error}</p>
      </section>
    )
  }

  // The quality issues the profiler found, across every profiled dataset. The
  // rail's warning mark and the overview's open-issue count both read this -
  // a stage's warning is a measured defect (P8-QUALITY-002), never a guess.
  const qualityIssues = datasets.flatMap((d) => profiles[d.id]?.quality ?? [])
  // A finding recorded but never validated: the loop's last step is still
  // waiting, and the overview counts it as an open issue rather than as a
  // result.
  const pendingFindings = findings.filter(
    (f) => f.validation_status === 'not_evaluated',
  ).length

  return (
    <section>
      {/* ZONE-A: the page's masthead - the way back and the case's own
          question, which is the page's name. `<header>` is the element for
          the block that names the page, and the h1 inside it is the heading
          the landmark structure already rests on. */}
      <header>
        <Button type="button" onClick={onBack} variant="link">
          ← Back to cases
        </Button>
        <h1>{caseRow?.question ?? '…'}</h1>
        {error && <p role="alert">Something went wrong: {error}</p>}
      </header>

      {/* UX 8: three zones - where am I, what am I doing, what can help me.
          Every panel here already existed with its own contract; the layout
          arranges them rather than replacing them. The rail stays visible in
          the left zone while the work scrolls (UX 5: "the workflow indicator
          should remain visible"), so orientation does not depend on the panel
          the analyst happens to be reading. The work zone ends on the decision
          (UX 46), which is the loop's exit rather than another step in it. */}
      <div className="workspace">
        <section className="zone orientation" aria-label="orientation">
          <MotionSurface variant="enter" className="contents">
            <WorkflowRail
              progress={progress}
              qualityWarning={qualityIssues.length > 0}
            />
            <CaseOverview
              question={caseRow?.question ?? ''}
              purpose={context?.purpose ?? ''}
              progress={progress}
              datasets={datasets.length}
              findings={findings.length}
              openIssues={qualityIssues.length + pendingFindings}
              pendingValidation={pendingFindings}
              pending={pendingPanels({
                runs: runs.length,
                findings: findings.length,
                // The graph is a projection that can answer 400 for a young
                // case; its own loaded state says it exists, not the error
                // that answered instead.
                evidence: !!evidence,
                evaluations: evaluations.length,
              })}
            />
            <div id="refine">
            <RefinePanel
              caseId={caseId}
              question={caseRow?.question ?? ''}
              onChanged={() => void load()}
            />
            </div>
            {/* W2X-008: the case's own record. Learn, history and the template
                promotion are orientation - they describe the case rather than
                doing work in it - but they are the later part of orientation,
                the part an analyst consults once the loop has produced
                something. One collapsed group instead of three flat panels,
                open when the case has a record to read. */}
            <CaseRecord
              caseId={caseId}
              question={caseRow?.question ?? ''}
              walk={walk}
              walkError={walkError}
              walkMissing={walkMissing}
              history={history}
              historyError={historyError}
              historyMissing={historyMissing}
            />
          </MotionSurface>
        </section>
        <section className="zone work" aria-label="work">
          <MotionSurface variant="enter" className="contents">
            <div id="data">
            <DataPanel
              caseId={caseId}
              datasets={datasets}
              profiles={profiles}
              loading={loading}
              onChanged={() => void load()}
            />
            </div>
            {/* ZONE-B (L3): the two "what to look at" surfaces over the profile
                are one block - the plan says what to examine and the EDA ops
                examine it, so the pair reads as the explore step rather than as
                two of the zone's seven equal cards. */}
            <div className="zone-group">
              <div id="plan">
              <PlanPanel
                caseId={caseId}
                datasets={datasets}
                loading={loading}
                onChanged={() => void load()}
              />
              </div>
              <EdaPanel caseId={caseId} datasets={datasets} profiles={profiles} loading={loading} />
            </div>
            {/* W2X-008: Runs stays mounted on a young case. Hiding a panel that
                carries no artifact is right only when the panel carries no
                control either - this one holds "Draft a finding", the only
                surface that creates one, so a case with no runs still needs it
                and its empty state is the next action's own sentence. The
                rail's "Go to the Runs panel" points here, and the anchor has to
                resolve. */}
            <div id="runs">
            <RunsPanel
              caseId={caseId}
              runs={runs}
              datasets={datasets}
              loading={loading}
              onChanged={() => void load()}
            />
            </div>
            {findings.length > 0 ? (
              <div id="findings">
                <FindingsPanel
                  caseId={caseId}
                  findings={findings}
                  onChanged={() => void load()}
                />
              </div>
            ) : null}
            {/* ZONE-B (L3): the two review surfaces are one block - the audit
                and the evidence graph both answer "what backs this case's
                claims", so they read as the validate step rather than as two
                more cards in the stack. */}
            <div className="zone-group">
              <div id="evaluate">
              <EvaluatePanel
                caseId={caseId}
                datasets={datasets}
                profiles={profiles}
                evaluations={evaluations}
                loading={loading}
                onChanged={() => void load()}
              />
              </div>
              <EvidencePanel
                evidence={evidence}
                error={evidenceError}
                empty={evidenceEmpty}
                loading={loading}
              />
            </div>
            {/* UX 46: the loop's exit, last in the work zone - after the
                evidence graph, because a decision is what the evidence is
                for. */}
            <DecisionPanel
              caseId={caseId}
              onChanged={() => void load()}
            />
          </MotionSurface>
        </section>
        <section className="zone intelligence" aria-label="intelligence">
          <MotionSurface variant="enter" className="contents">
            {/* ZONE-B (L4): the copilot is first in this zone. The mental model
                puts it there - `docs/UX-UI Architecture.md` sec. 2's diagram has
                no copilot node, because it is not a stage in the loop: it is
                the per-stage support that answers "What should I do next?", one
                of the three questions sec. 2 says the analyst must always
                understand, and a surface answering an always-question cannot
                sit below the fold of the zone that exists to answer it. Sec. 8
                lists the zone's contents with "AI assistance" first, before
                "context" and before "suggestions". Sec. 22 constrains the form,
                not the rank - "The AI should not dominate the application" - so
                this is a reorder and never an enlargement: the panel keeps its
                size, its contract and its region, and the turns grow downward
                as they did when it was last. */}
            <Chat
              caseId={caseId}
              turns={turns}
              onTurn={(turn) => setTurns((prior) => [...prior, turn])}
              onOpenCase={onOpenCase}
            />
            <ContextPanel caseId={caseId} loading={loading} onChanged={() => void load()} />
            {/* ZONE-B (L3): the two agents are one mechanism in two roles - the
                same component mounted twice over the same case - so they read
                as one block rather than two equal cards beside the copilot.
                Sec. 22's copilot is contextual, and a grouped pair is not a
                dominating one. */}
            <div className="zone-group">
              <AgentPanel
                caseId={caseId}
                role="analyst"
                agent={agent}
                onAgent={setAgent}
                onChanged={() => void load()}
              />
              <AgentPanel
                caseId={caseId}
                role="reviewer"
                agent={reviewer}
                onAgent={setReviewer}
                onChanged={() => void load()}
              />
            </div>
          </MotionSurface>
        </section>
      </div>
    </section>
  )
}
