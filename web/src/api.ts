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
// JSON: a 4xx carries {"detail": ...}, but a 500 answers plain text
// (P4-RELIABILITY-002) and res.json() on it would throw a second, hiding
// failure - so the raw text is the message there.
export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
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
    const contentType = res.headers.get('content-type') ?? ''
    if (contentType.includes('application/json')) {
      try {
        const body = JSON.parse(text) as { detail?: string }
        if (body.detail) message = body.detail
      } catch {
        // An unparseable JSON body keeps its raw text as the message.
      }
    }
    throw new ApiError(res.status, message || `request failed: ${res.status}`)
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
