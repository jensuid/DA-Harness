// Typed client for the DAH core. Every screen reads its own data on mount and
// nothing is cached, so the UI cannot go stale against the core.
const BASE = import.meta.env.VITE_API_URL ?? '/api'

export interface Health {
  status: string
}

export interface Case {
  id: string
  question: string
  dataset: string
  // Advisory: a template outlives its source case and may be deleted first, so
  // a missing template degrades to normal derivation rather than an error.
  template_id?: string
  created_at: string
  updated_at: string
}

export interface NewCase {
  question: string
  dataset: string
}

export interface Dataset {
  id: string
  case_id: string
  filename: string
  format: string
  created_at: string
}

export interface RunSummary {
  id: string
  case_id: string
  dataset_id: string
  kind: string
  sql: string | null
  code: string | null
  row_count: number
  truncated: boolean
  executed_at: string
}

export interface WorkflowStage {
  name: string
  completed: boolean
}

// A run reopened with its result rows (P8-SHELL-006): the summary tells you a
// run exists, the full run is what a finding actually rests on. The rows are
// JSON the core serialised, so a cell may be a number, a string or null.
export interface Run {
  id: string
  case_id: string
  dataset_id: string
  kind: string
  sql: string | null
  code: string | null
  dataset_ids: string[] | null
  columns: string[]
  rows: unknown[][]
  row_count: number
  truncated: boolean
  executed_at: string
}

// The plan's body, as the planner persisted it. Every entry references columns
// the profile actually has, so the plan is actionable rather than generic.
export interface PlanBody {
  objective: string
  primary_question: string
  sub_questions: string[]
  hypotheses: { statement: string; rationale: string; check: string }[]
  data_requirements: { requirement: string; detail: string }[]
  analysis_steps: { action: string; detail: string }[]
  context_basis: string[]
}

export interface Plan {
  id: string
  case_id: string
  dataset_id: string
  question: string
  plan: PlanBody
  source: string
  created_at: string
}

export interface CaseProgress {
  stage: string
  completed: string[]
  stages: WorkflowStage[]
  next_action: string | null
  next_hint: string | null
  next_endpoint: string | null
  loop_closed: boolean
  counts: Record<string, number>
}

export interface QualityIssue {
  /** One of the PRD's seven defect classes (AT-08). */
  kind: string
  /** The column, or null when the issue is dataset-wide (coverage). */
  column: string | null
  severity: 'high' | 'medium' | 'low'
  /** The measured fact. */
  observed: string
  /** What the issue does to an analysis built on this data (AT-09). */
  impact: string
}

export interface Profile {
  dataset_id: string
  rows: number
  columns: string[]
  stats: Record<string, unknown>
  duplicate_rows: number
  quality: QualityIssue[]
  profiled_at: string
}

export interface GeneratedCode {
  dataset_id: string
  case_id: string
  kind: string
  code: string
  explanation: string
  columns_used: string[]
  source: string
}

export interface Interpretation {
  id: string
  run_id: string
  case_id: string
  summary: string
  observations: string[]
  caveats: string[]
  source: string
  created_at: string
}

export interface DraftFinding {
  run_id: string
  case_id: string
  statement: string
  interpretation: string
  caveat: string
  grounds: string[]
  source: string
}

export interface Finding {
  id: string
  case_id: string
  run_id: string
  statement: string
  interpretation: string | null
  caveat: string | null
  validation_status: string
  created_at: string
}

export interface ValidationCheck {
  /** Legacy name, kept identical to `dimension` so an older client still finds
   * its check. */
  name: string
  /** One of the PRD's nine validation dimensions (AT-17). */
  dimension: string
  passed: boolean
  detail: string
  /** A hard failure blocks `supported`; a concern yields `partially_supported`. */
  hard: boolean
}

export interface ValidationResult {
  finding_id: string
  run_id: string
  status: string
  checks: ValidationCheck[]
  validated_at: string
}

// EVALUATE mode (P7-EVAL-001 / P7-SHELL-002): work that came from elsewhere,
// audited against the nine axes the specification names. The verdicts are
// pass / concern / fail - never a score, because a single number would imply a
// precision nine heterogenous axes do not have - and every verdict carries a
// sentence a reader can act on.
export interface AxisFinding {
  axis: string
  verdict: string
  detail: string
}

export interface Evaluation {
  id: string
  case_id: string
  dataset_id: string
  run_id: string | null
  artifact_kind: string
  code: string
  claim: string
  findings: AxisFinding[]
  source: string
  created_at: string
}

// The agent (P6-AGENT-002 / P7-SHELL-003): a driver over the loop the
// workspace's panels are steps of. It proposes; the human disposes. `payload`
// is exactly what the step will write, settled when it was proposed, so the
// human approves something concrete rather than a promise. `status` is pending
// until the human answers; `note` is what the write produced, or the reason it
// was refused.
export interface AgentStep {
  id: string
  case_id: string
  role: string
  kind: string
  payload: Record<string, unknown>
  source: string
  status: string
  note: string
  created_at: string
  decided_at: string | null
}

export interface AgentState {
  case_id: string
  role: string
  pending: AgentStep | null
  history: AgentStep[]
}

export interface ConversationTurn {
  id: string
  case_id: string
  message: string
  answer: string
  grounds: string[]
  source: string
  created_at: string
}

// A failure from the core. The body is parsed as JSON only when the core sent
// JSON, and it is now: a 4xx carries {"detail": ...} and a 500 carries
// {"detail": "internal error", "request_id": ...} (P5-RELIABILITY-003). The id
// is the key to that fault's traceback in the core's log, so it rides along for
// the UI to quote - "this is error <id>" is actionable in a way "request failed"
// is not.
//
// A 500 that is not JSON still works: the raw text becomes the message rather
// than throwing a second error inside the handler. That path is kept because the
// desktop shell's webview can meet a proxy, a timeout or an older core that
// never sent an envelope.
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public requestId?: string,
  ) {
    super(message)
    this.name = 'ApiError'
  }
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE}${path}`, init)
  if (!res.ok) {
    const text = await res.text()
    let message = text
    let requestId: string | undefined
    const contentType = res.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      try {
        const body = JSON.parse(text) as {
          detail?: string | { detail?: string }
          request_id?: string
        }
        if (body.detail) {
          // A nested detail is the agent's 409: it names the pending step the
          // approval should have carried, so the inner sentence is the
          // actionable one.
          message =
            typeof body.detail === 'string' ? body.detail : (body.detail.detail ?? '')
        }
        requestId = body.request_id
      } catch {
        // An unparseable JSON body keeps its raw text as the message.
      }
    }
    throw new ApiError(res.status, message || `request failed: ${res.status}`, requestId)
  }
  // A 204 (and any other empty body) has nothing to parse: the DELETEs the
  // shell makes - a case, a dataset, a template - answer 204 and succeed, and
  // parsing an empty body would throw a second error inside the handler after
  // the write had already landed. Nothing is the honest return for no body.
  if (res.status === 204 || (await res.clone().text()) === '') {
    return undefined as T
  }
  return (await res.json()) as T
}

export function getHealth(): Promise<Health> {
  return request<Health>('/health')
}

export function createCase(newCase: NewCase): Promise<Case> {
  return request<Case>('/cases', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(newCase),
  })
}

export function listCases(q?: string): Promise<Case[]> {
  const term = (q ?? '').trim()
  return request<Case[]>(term ? `/cases?q=${encodeURIComponent(term)}` : '/cases')
}

export function getCase(id: string): Promise<Case> {
  return request<Case>(`/cases/${id}`)
}

// --- the case's stated intent (P8-CONTEXT-001) -----------------------------

// The primary question stays on the case row; this is what a question alone
// cannot carry. Lists, because the analyst adds and removes entries as the
// investigation moves, and the whole object is replaced on save so a retry
// after a failure cannot merge two drafts.
export interface CaseContext {
  case_id: string
  purpose: string
  sub_questions: string[]
  hypotheses: string[]
  constraints: string[]
  updated_at: string | null
}

export function getContext(caseId: string): Promise<CaseContext> {
  return request<CaseContext>(`/cases/${caseId}/context`)
}

// Whole-object replace: the stored context is identical to what the form held,
// never a merge of the form and what was on the server a moment ago.
export function putContext(
  caseId: string,
  context: { purpose: string; sub_questions: string[]; hypotheses: string[]; constraints: string[] },
): Promise<CaseContext> {
  return request<CaseContext>(`/cases/${caseId}/context`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(context),
  })
}

// --- question refinement (P8-REFINE-007 / AT-04) ---------------------------

// A proposed sharpening of the case's question, and what the analyst decided.
// The original is carried beside the proposal and is never overwritten by it:
// accepting moves the refined question onto the case, but the row keeps what
// was there before, so the transformation stays recoverable.
export interface RefinementGround {
  kind: string
  name: string
  detail: string
}

export interface Refinement {
  id: string
  case_id: string
  original_question: string
  refined_question: string
  rationale: string
  grounds: RefinementGround[]
  source: string
  status: 'pending' | 'declined' | 'accepted' | 'rejected' | 'edited'
  edited_question: string | null
  created_at: string
  decided_at: string | null
}

// Proposing writes nothing: the question moves only through accept or edit.
// Read-only on a GET, so opening a case never proposes.
export function proposeRefinement(caseId: string): Promise<Refinement> {
  return request<Refinement>(`/cases/${caseId}/refine`, { method: 'POST' })
}

export function getRefinement(caseId: string): Promise<Refinement | null> {
  return request<Refinement | null>(`/cases/${caseId}/refine`)
}

export function acceptRefinement(
  caseId: string,
  proposalId: string,
): Promise<Refinement> {
  return request<Refinement>(
    `/cases/${caseId}/refine/${proposalId}/accept`,
    { method: 'POST' },
  )
}

// Keep original: the no is recorded, nothing is written.
export function rejectRefinement(
  caseId: string,
  proposalId: string,
): Promise<Refinement> {
  return request<Refinement>(
    `/cases/${caseId}/refine/${proposalId}/reject`,
    { method: 'POST' },
  )
}

// The third path: neither the original nor the proposal, but the analyst's own
// wording, which becomes the case's question.
export function editRefinement(
  caseId: string,
  proposalId: string,
  question: string,
): Promise<Refinement> {
  return request<Refinement>(
    `/cases/${caseId}/refine/${proposalId}/edit`,
    { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ question }) },
  )
}

// --- case management (P2-CASE-010 / P7-SHELL-004) --------------------------

// Omitted fields are left as they are, and updated_at moves so a rename shows
// up as case activity.
export function updateCase(
  caseId: string,
  changes: { question?: string; dataset?: string },
): Promise<Case> {
  return request<Case>(`/cases/${caseId}`, {
    method: 'PATCH',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(changes),
  })
}

// A copy is a self-contained case: its datasets, profiles, runs and findings
// arrive with fresh ids, so it may be mutated without touching the original.
export function duplicateCase(caseId: string): Promise<Case> {
  return request<Case>(`/cases/${caseId}/duplicate`, { method: 'POST' })
}

// Irreversible: the case row, every child and the case's on-disk directory go
// together. The caller asks twice.
export function deleteCase(caseId: string): Promise<void> {
  return request<void>(`/cases/${caseId}`, { method: 'DELETE' })
}

// --- templates: the shape of a finished case (P6-TEMPLATE-003 / P7-SHELL-005) -

// A template is a skeleton plus what the case it came from learned. The
// proposals travel with the columns they read, because the schema they were
// written against does not - a later case may have to refuse one.
export interface TemplateProposal {
  kind: string
  code: string
  explanation: string
  columns_used: string[]
}

export interface TemplateFindingSummary {
  statement: string
  validation_status: string
}

export interface TemplateShape {
  plan: Record<string, unknown> | null
  plan_source: string | null
  proposals: TemplateProposal[]
  findings: TemplateFindingSummary[]
}

// A template outlives the case it came from, so `shape` is nullable: a case
// with nothing to carry promotes the question-only skeleton, and a template
// promoted before shapes existed has none.
export interface Template {
  id: string
  name: string
  question: string
  dataset: string
  shape: TemplateShape | null
  created_at: string
}

// The name is optional - the core defaults it to the case's question - so the
// common "save this as a template" gesture needs no second prompt. An empty
// name is sent as an omission rather than a blank string, because a blank
// string is the one shape the core refuses with a 400.
export function promoteCaseToTemplate(
  caseId: string,
  name = '',
): Promise<Template> {
  const trimmed = name.trim()
  return request<Template>(`/cases/${caseId}/template`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(trimmed ? { name: trimmed } : {}),
  })
}

export function listTemplates(): Promise<Template[]> {
  return request<Template[]>('/templates')
}

// Only the skeleton is copied: no data, runs or findings. Either field may be
// overridden inline, and the seeded case records which template it came from.
export function createCaseFromTemplate(
  templateId: string,
  overrides: { question?: string; dataset?: string } = {},
): Promise<Case> {
  return request<Case>('/cases/from-template', {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ template_id: templateId, ...overrides }),
  })
}

// A template carries no data of its own, and the core's contract is that cases
// created from it keep working without it - they degrade to normal derivation
// - so retiring a template loses nothing the way deleting a case does.
export function deleteTemplate(templateId: string): Promise<void> {
  return request<void>(`/templates/${templateId}`, { method: 'DELETE' })
}

export function getProgress(id: string): Promise<CaseProgress> {
  return request<CaseProgress>(`/cases/${id}/progress`)
}

export function listDatasets(id: string): Promise<Dataset[]> {
  return request<Dataset[]>(`/cases/${id}/datasets`)
}

export function listRuns(id: string): Promise<RunSummary[]> {
  return request<RunSummary[]>(`/cases/${id}/runs`)
}

// A run's own rows, reopened (P8-SHELL-006): the result a finding rests on is
// readable without re-running it.
export function getRun(caseId: string, runId: string): Promise<Run> {
  return request<Run>(`/cases/${caseId}/runs/${runId}`)
}

export function postChat(id: string, message: string): Promise<ConversationTurn> {
  return request<ConversationTurn>(`/cases/${id}/chat`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ message }),
  })
}

export function listChat(id: string): Promise<ConversationTurn[]> {
  return request<ConversationTurn[]>(`/cases/${id}/chat`)
}

// --- the loop the workspace walks -------------------------------------------

export function attachDataset(caseId: string, file: File): Promise<Dataset> {
  const form = new FormData()
  form.append('file', file)
  return request<Dataset>(`/cases/${caseId}/datasets`, {
    method: 'POST',
    body: form,
  })
}

export function profileDataset(caseId: string, datasetId: string): Promise<Profile> {
  return request<Profile>(`/cases/${caseId}/datasets/${datasetId}/profile`, {
    method: 'POST',
  })
}

// W-008 (FIX-PROFILE-008): reading a profile is a GET. Opening a case used to
// POST the profile endpoint per attached dataset on every mount - twice, under
// strict mode's double render - so a visit recomputed and rewrote a profile
// that already existed, and the panel's "profiling…" was the shell completing
// a step the rail names as the analyst's. Reading is read-only now; the POST
// is the analyst's explicit ask.
export function getProfile(caseId: string, datasetId: string): Promise<Profile> {
  return request<Profile>(`/cases/${caseId}/datasets/${datasetId}/profile`)
}

export function runSql(
  caseId: string,
  datasetId: string,
  sql: string,
): Promise<RunSummary> {
  return request<RunSummary>(`/cases/${caseId}/datasets/${datasetId}/runs`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ sql }),
  })
}

// The three assistant slices. Each returns a proposal and writes nothing
// except interpret, which persists a reading of an already-persisted result.
// The latest plan for a dataset (P8-SHELL-006): the loop's plan stage is a
// persisted artifact, and rendering it is what tells the analyst what to run.
export function getPlan(caseId: string, datasetId: string): Promise<Plan> {
  return request<Plan>(`/cases/${caseId}/datasets/${datasetId}/plan`)
}

// W-011 (FIX-PLAN-003): generating the plan is a POST, the planner's own
// write. The panel reads the latest plan and, when there is none, offers this
// - the rail names "Generate an analysis plan" and before this control the
// shell never called the endpoint that performs it, so the stage was only
// finishable from a terminal.
export function createPlan(caseId: string, datasetId: string): Promise<Plan> {
  return request<Plan>(`/cases/${caseId}/datasets/${datasetId}/plan`, {
    method: 'POST',
  })
}

export function generateCode(
  caseId: string,
  datasetId: string,
  question: string,
  kind = 'sql',
): Promise<GeneratedCode> {
  return request<GeneratedCode>(
    `/cases/${caseId}/datasets/${datasetId}/generate-code`,
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ question, kind }),
    },
  )
}

export function interpretRun(caseId: string, runId: string): Promise<Interpretation> {
  return request<Interpretation>(`/cases/${caseId}/runs/${runId}/interpret`, {
    method: 'POST',
  })
}

export function draftFinding(
  caseId: string,
  runId: string,
): Promise<DraftFinding> {
  return request<DraftFinding>(`/cases/${caseId}/runs/${runId}/draft-finding`, {
    method: 'POST',
  })
}

// The two ways a proposal becomes real. Both stay the analyst's call: the
// findings endpoint is the only path that writes a finding, and validation
// reruns the stored computation rather than trusting the claim.
export function acceptFinding(
  caseId: string,
  runId: string,
  draft: DraftFinding,
): Promise<Finding> {
  return request<Finding>(`/cases/${caseId}/findings`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({
      run_id: runId,
      statement: draft.statement,
      interpretation: draft.interpretation,
      caveat: draft.caveat,
    }),
  })
}

export function validateFinding(caseId: string, findingId: string): Promise<ValidationResult> {
  return request<ValidationResult>(`/cases/${caseId}/findings/${findingId}/validate`, {
    method: 'POST',
  })
}

export function listFindings(caseId: string): Promise<Finding[]> {
  return request<Finding[]>(`/cases/${caseId}/findings`)
}

// --- EDA: what to look at first (P3-ANALYSIS-005 / P7-SHELL-007) ------------

// Each op compiles to read-only SQL under the same gate and row cap as a
// hand-written query, and each takes only its own inputs:
//   segment - `by` and `measure`; correlation needs two numerics.
//   correlate - `x` and `y`.
//   distribution - one `column`; numeric yields a spread, a category its
//   most common values.
export type EdaOp = 'segment' | 'correlate' | 'distribution'

export interface EdaRequest {
  op: EdaOp
  by?: string
  measure?: string
  x?: string
  y?: string
  column?: string
}

export interface EdaResult {
  op: string
  columns: string[]
  rows: unknown[][]
  row_count: number
  truncated: boolean
}

// Exploration, not evidence: the result is returned and never persisted, so a
// finding still has to anchor on a query the analyst wrote. A 400 is part of
// the contract rather than a failure - a column the dataset lacks, or a
// correlation over a column with no paired numerics - and its sentence is what
// teaches the correction.
export function runEda(
  caseId: string,
  datasetId: string,
  payload: EdaRequest,
): Promise<EdaResult> {
  return request<EdaResult>(`/cases/${caseId}/datasets/${datasetId}/eda`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

// --- EVALUATE: audit work that came from elsewhere -------------------------

// The submission executes through the same engine the runs endpoints use, so
// the read-only gate, the row cap and the hard sandbox are the ones every other
// run answers to. A 400 is part of the contract rather than a failure: a
// non-read-only artifact is refused before anything executes, and the detail
// says what to change.
export function evaluateDataset(
  caseId: string,
  datasetId: string,
  code: string,
  claim: string,
  kind = 'sql',
): Promise<Evaluation> {
  return request<Evaluation>(
    `/cases/${caseId}/datasets/${datasetId}/evaluate`,
    {
      method: 'POST',
      headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ code, claim, kind }),
    },
  )
}

export function listEvaluations(
  caseId: string,
  datasetId: string,
): Promise<Evaluation[]> {
  return request<Evaluation[]>(
    `/cases/${caseId}/datasets/${datasetId}/evaluations`,
  )
}

// --- the evidence graph: what each claim rests on (P3-EVIDENCE-006 / P7-SHELL-008)

// The graph is projected from the persisted rows, never stored, so it cannot
// drift from what is on disk. Nodes are the case's artifacts; edges say how
// one was derived from another.
export interface EvidenceNode {
  id: string
  kind: string
  label: string
  detail?: string | null
  created_at?: string | null
}

export interface EvidenceEdge {
  source: string
  target: string
  relation: string
}

// One claim's path back to the data it stands on. `reaches_source` is false
// when the finding's run is gone - a claim with no source, which is what the
// graph exists to surface rather than to hide.
export interface ClaimTrace {
  finding_id: string
  statement: string
  validation_status: string
  hops: EvidenceNode[]
  reaches_source: boolean
}

export interface EvidenceGraph {
  case_id: string
  nodes: EvidenceNode[]
  edges: EvidenceEdge[]
  traces: ClaimTrace[]
  orphan_findings: string[]
  counts: Record<string, number>
}

// Read-only: the graph answers what is, and nothing a reviewer does here
// changes the case. A 400 is the case having no artifacts to graph, which is
// guidance rather than a failure.
export function getEvidenceGraph(caseId: string): Promise<EvidenceGraph> {
  return request<EvidenceGraph>(`/cases/${caseId}/evidence-graph`)
}

// --- LEARN mode: the analytical process as a guided walk (P7-LEARN-001 / P7-SHELL-010)

// The walk regroups the ANALYZE workflow into the spec's four phases - why,
// what, how, validate - and each phase carries what it teaches and the question
// a learner should be able to answer before leaving it. Like the evidence graph
// and the case history it is a read-side projection, so it cannot drift from
// the case and nothing here writes.
export interface LearnStage {
  name: string
  completed: boolean
  // What closes the stage, from the workflow's own table - one source of truth.
  action: string
  hint: string
}

export interface LearnStep {
  name: string
  purpose: string
  prompt: string
  stages: LearnStage[]
  status: string // complete | current | pending
}

export interface LearnWalk {
  case_id: string
  question: string
  steps: LearnStep[]
  current: string | null
  next_action: string | null
  next_hint: string | null
  next_endpoint: string | null
  done: boolean
}

// Read-only: the walk answers what the learner should do and understand, and
// nothing a learner does here changes the case. A 404 means the case is
// unknown, and the workspace loads its own case on mount, so that answer is
// already reported at the top.
export function getLearnWalk(caseId: string): Promise<LearnWalk> {
  return request<LearnWalk>(`/cases/${caseId}/learn`)
}

// --- case history: what happened in this case, and when (P3-CASE-007 / P7-SHELL-009)

// The timeline is projected from each artifact's own timestamp, never stored,
// so it cannot drift from the persisted rows. One event per artifact, in the
// order the loop usually produces them; a finding's validation status rides
// along as its event's detail, because validation keeps no timestamp of its own.
export interface HistoryEvent {
  timestamp: string
  kind: string
  artifact_id: string | null
  label: string
  detail: string | null
}

export interface CaseHistory {
  case_id: string
  question: string
  events: HistoryEvent[]
  counts: Record<string, number>
}

// Read-only: the timeline answers what happened, and nothing a reviewer does
// here changes the case. A 404 means the case is unknown - the workspace loads
// its own case on mount, so that answer is already reported at the top.
export function getCaseHistory(caseId: string): Promise<CaseHistory> {
  return request<CaseHistory>(`/cases/${caseId}/history`)
}

// --- the agent: the loop's driver -----------------------------------------

// The GET is read-only and never proposes, so a page refresh commits nothing.
export function getAgentState(caseId: string): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agent`)
}

// Idempotent: a pending step is returned unchanged, so two calls never yield
// two writes.
export function proposeAgentStep(caseId: string): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agent`, { method: 'POST' })
}

// The approval must name the case's CURRENT pending step; an id from a stale
// page is a 409, never a second write. Approving runs the step's write through
// the endpoint that owns it and returns the next proposal with it, so the
// human needs no second call to see what comes next.
export function approveAgentStep(caseId: string, stepId: string): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agent/approve`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ step_id: stepId }),
  })
}

// Rejection never writes case state: the proposal is marked rejected with the
// analyst's reason, and the next step is derived.
export function rejectAgentStep(
  caseId: string,
  stepId: string,
  reason = '',
): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agent/reject`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ step_id: stepId, reason }),
  })
}

// --- the agents: roles over one case --------------------------------------
// P7-AGENT-001. A case can be worked by more than one agent, each with a role
// of its own: the analyst drives the analysis loop, the reviewer audits what
// the case claims. They share one approval gate and never talk to each other -
// each addresses the case, and the case's rows are the shared state.

// The roles the core knows. An unknown role is a 400 naming the ones that
// exist, so the shell names the roles it uses rather than sending a free
// string.
export type AgentRole = 'analyst' | 'reviewer'

// The GET is read-only and never proposes, so two open panels commit nothing
// on a refresh.
export function getRoleAgentState(
  caseId: string,
  role: AgentRole,
): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agents/${role}`)
}

// Idempotent: a role's pending step comes back unchanged. Each role derives
// from the same artifacts independently, so the two panels' proposals are two
// derivations, not one shared one.
export function proposeRoleAgentStep(
  caseId: string,
  role: AgentRole,
): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agents/${role}`, { method: 'POST' })
}

// The approval must name THIS role's current pending step. An id from the
// other role's panel is a 409, because one role's write is never authorised
// by another role's approval - and the 409's sentence names that role's own
// pending step, which is the actionable thing. The response carries the next
// proposal with it.
export function approveRoleAgentStep(
  caseId: string,
  role: AgentRole,
  stepId: string,
): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agents/${role}/approve`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ step_id: stepId }),
  })
}

export function rejectRoleAgentStep(
  caseId: string,
  role: AgentRole,
  stepId: string,
  reason = '',
): Promise<AgentState> {
  return request<AgentState>(`/cases/${caseId}/agents/${role}/reject`, {
    method: 'POST',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ step_id: stepId, reason }),
  })
}

// --- the loop's exit (P8-DECISION-008 / UX 46) ----------------------------

// The case's decision view: the findings validation stood behind, the
// uncertainty that survived them (the checks that did not pass, never a
// score), the claims still open, and the implications the analyst wrote. DAH
// informs decisions and does not make them, so nothing here recommends
// anything and no number summarises a finding's trust.
export interface DecisionCheck {
  dimension: string
  detail: string
  hard: boolean
}

export interface DecisionFinding {
  id: string
  statement: string
  validation_status: string
  interpretation: string | null
  caveat: string | null
  uncertainty: DecisionCheck[]
  validated_at: string | null
}

export interface DecisionOpenItem {
  id: string
  statement: string
  validation_status: string
  reasons: string[]
}

export interface DecisionView {
  case_id: string
  question: string
  purpose: string
  loop_closed: boolean
  findings: DecisionFinding[]
  open_items: DecisionOpenItem[]
  implications: string[]
  updated_at: string | null
  counts: Record<string, number>
}

// Read-only, deterministic, executes nothing: every field is a stored row or a
// count of stored rows, so opening a case renders a decision without running a
// query and without moving a verdict.
export function getDecision(caseId: string): Promise<DecisionView> {
  return request<DecisionView>(`/cases/${caseId}/decision`)
}

// The view's only write: the implications, in the analyst's own words. Nothing
// proposes them and nothing derives them, because a tool that drafts the
// action to take is a tool making the decision.
export function putDecision(
  caseId: string,
  implications: string[],
): Promise<DecisionView> {
  return request<DecisionView>(`/cases/${caseId}/decision`, {
    method: 'PUT',
    headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ implications }),
  })
}

// The case's package, as the decision's export (UX 46/47). The browser saves
// it rather than rendering it, so this returns the raw response instead of
// parsed JSON.
export async function exportCasePackage(caseId: string): Promise<Blob> {
  const res = await fetch(`${BASE}/cases/${caseId}/export`)
  if (!res.ok) {
    const text = await res.text()
    throw new ApiError(res.status, text || `export failed: ${res.status}`)
  }
  return res.blob()
}
