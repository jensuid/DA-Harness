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

export interface Profile {
  dataset_id: string
  rows: number
  columns: string[]
  stats: Record<string, unknown>
  duplicate_rows: number
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

export interface ValidationResult {
  finding_id: string
  run_id: string
  status: string
  checks: { name: string; passed: boolean; detail: string }[]
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

export function getProgress(id: string): Promise<CaseProgress> {
  return request<CaseProgress>(`/cases/${id}/progress`)
}

export function listDatasets(id: string): Promise<Dataset[]> {
  return request<Dataset[]>(`/cases/${id}/datasets`)
}

export function listRuns(id: string): Promise<RunSummary[]> {
  return request<RunSummary[]>(`/cases/${id}/runs`)
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
