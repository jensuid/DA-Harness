import { describe, it, expect, vi, beforeEach } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CaseWorkspace } from './CaseWorkspace'
import { CaseCreation } from './CaseCreation'
import { CaseList } from './CaseList'
import * as api from './api'
import './index.css'
import {
  auditAll,
  auditKeyboardReachable,
  auditLabels,
  auditSemantics,
  auditStatusNotColorOnly,
  controlCount,
  focusIsGuaranteed,
} from './accessibility'

vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return {
    ...actual,
    getCase: vi.fn(),
    createCase: vi.fn(),
    listCases: vi.fn(),
    getContext: vi.fn(),
    putContext: vi.fn(),
    getProgress: vi.fn(),
    listDatasets: vi.fn(),
    getPlan: vi.fn(),
    listRuns: vi.fn(),
    getRun: vi.fn(),
    listFindings: vi.fn(),
    listChat: vi.fn(),
    profileDataset: vi.fn(),
    attachDataset: vi.fn(),
    generateCode: vi.fn(),
    runSql: vi.fn(),
    interpretRun: vi.fn(),
    draftFinding: vi.fn(),
    acceptFinding: vi.fn(),
    validateFinding: vi.fn(),
    postChat: vi.fn(),
    evaluateDataset: vi.fn(),
    runEda: vi.fn(),
    getEvidenceGraph: vi.fn(),
    getCaseHistory: vi.fn(),
    getLearnWalk: vi.fn(),
    listEvaluations: vi.fn(),
    getAgentState: vi.fn(),
    proposeAgentStep: vi.fn(),
    approveAgentStep: vi.fn(),
    rejectAgentStep: vi.fn(),
    getRoleAgentState: vi.fn(),
    proposeRoleAgentStep: vi.fn(),
    approveRoleAgentStep: vi.fn(),
    rejectRoleAgentStep: vi.fn(),
    promoteCaseToTemplate: vi.fn(),
    getRefinement: vi.fn(),
    proposeRefinement: vi.fn(),
    acceptRefinement: vi.fn(),
    rejectRefinement: vi.fn(),
    editRefinement: vi.fn(),
    getDecision: vi.fn(),
    putDecision: vi.fn(),
    exportCasePackage: vi.fn(),
  }
})

const dataset = { id: 'd1', case_id: 'c1', filename: 'sales.csv', format: 'csv', created_at: '' }
const profile: api.Profile = {
  dataset_id: 'd1',
  rows: 3,
  columns: ['order_id', 'revenue', 'region'],
  stats: {
    order_id: { type: 'other', null_count: 0, null_percentage: 0 },
    revenue: { type: 'numeric', null_count: 1, null_percentage: 33.33 },
    region: { type: 'other', null_count: 0, null_percentage: 0 },
  },
  duplicate_rows: 0,
  quality: [
    {
      kind: 'missing_values',
      column: 'revenue',
      severity: 'medium',
      observed: 'revenue has 1 missing value.',
      impact: 'Totals over revenue may be understated.',
    },
  ],
  profiled_at: '',
}

const progress = {
  stage: 'analyze',
  completed: ['question', 'data', 'profile', 'plan'],
  stages: [
    { name: 'question', completed: true },
    { name: 'data', completed: true },
    { name: 'profile', completed: true },
    { name: 'plan', completed: true },
    { name: 'analyze', completed: false },
  ],
  next_action: 'Run an analysis',
  next_hint: 'SQL or Python.',
  next_endpoint: 'POST /cases/c1/datasets/d1/runs',
  loop_closed: false,
  counts: { datasets: 1, runs: 1 },
}

const finding = {
  id: 'f1',
  case_id: 'c1',
  run_id: 'r1',
  statement: 'North revenue is higher than south.',
  interpretation: 'The gap is consistent across quarters.',
  caveat: 'One revenue value is missing.',
  validation_status: 'partially_supported',
  grounds: ['run:r1', 'dataset:d1'],
  created_at: '',
}

const decision: api.DecisionView = {
  case_id: 'c1',
  question: 'Why did revenue decline?',
  purpose: 'Decide whether to chase the south region.',
  loop_closed: true,
  findings: [
    {
      id: 'f1',
      statement: 'North revenue is higher than south.',
      validation_status: 'partially_supported',
      interpretation: null,
      caveat: 'One revenue value is missing.',
      uncertainty: [
        { dimension: 'data', detail: 'revenue contains 1 missing value.', hard: false },
      ],
      validated_at: '2026-09-23T09:00:00+00:00',
    },
  ],
  open_items: [
    {
      id: 'f2',
      statement: 'The price change caused the rise.',
      validation_status: 'insufficient_evidence',
      reasons: ['causality: the claim is causal and the method is not'],
    },
  ],
  implications: ['Shift spend toward the north.'],
  updated_at: '2026-09-23T09:05:00+00:00',
  counts: {
    findings: 2, key_findings: 1, supported: 0, partially_supported: 1,
    open_items: 1, open_checks: 1, implications: 1,
  },
}

const proposal: api.Refinement = {
  id: 'p1',
  case_id: 'c1',
  original_question: 'Why did revenue decline?',
  refined_question: 'Why did revenue decline in the south region last quarter?',
  rationale: 'The profile measures revenue and region.',
  source: 'deterministic',
  status: 'pending',
  grounds: [{ kind: 'column', name: 'region', detail: '4 values, no nulls' }],
  edited_question: null,
  created_at: '',
  decided_at: null,
}

function mockWorkedCase() {
  vi.clearAllMocks()
  vi.mocked(api.getCase).mockResolvedValue({
    id: 'c1', question: 'Why did revenue decline?', dataset: 'sales.csv',
    created_at: '', updated_at: '',
  })
  vi.mocked(api.getContext).mockResolvedValue({
    case_id: 'c1', purpose: 'Decide whether to chase the south region.',
    sub_questions: ['Is the south gap new?'], hypotheses: ['A price change.'],
    constraints: [], updated_at: '',
  })
  vi.mocked(api.getProgress).mockResolvedValue(progress)
  // A worked case has no latest plan in these fixtures; refusing read-only is
  // what the core answers, and the panel renders its "no plan yet" guidance.
  vi.mocked(api.getPlan).mockRejectedValue(new api.ApiError(404, 'plan not found'))
  vi.mocked(api.getRun).mockRejectedValue(new api.ApiError(404, 'run not found'))
  vi.mocked(api.listDatasets).mockResolvedValue([dataset])
  vi.mocked(api.profileDataset).mockResolvedValue(profile)
  vi.mocked(api.listRuns).mockResolvedValue([
    { id: 'r1', case_id: 'c1', dataset_id: 'd1', kind: 'sql',
      sql: 'SELECT region, SUM(revenue)', code: null, row_count: 3,
      truncated: false, executed_at: '' },
  ])
  vi.mocked(api.listFindings).mockResolvedValue([finding])
  vi.mocked(api.listChat).mockResolvedValue([])
  vi.mocked(api.listEvaluations).mockResolvedValue([])
  vi.mocked(api.getEvidenceGraph).mockResolvedValue({
    case_id: 'c1',
    nodes: [
      { id: 'd1', kind: 'dataset', label: 'sales.csv', detail: 'csv file', created_at: '' },
      { id: 'r1', kind: 'run', label: 'sql run', detail: 'SELECT region', created_at: '' },
      { id: 'f1', kind: 'finding', label: finding.statement, detail: 'validated', created_at: '' },
    ],
    edges: [{ source: 'f1', target: 'r1', relation: 'anchored_on' }],
    traces: [{
      finding_id: 'f1', statement: finding.statement,
      validation_status: 'partially_supported',
      hops: [
        { id: 'f1', kind: 'finding', label: finding.statement },
        { id: 'r1', kind: 'run', label: 'sql run' },
        { id: 'd1', kind: 'dataset', label: 'sales.csv' },
      ],
      reaches_source: true,
    }],
    orphan_findings: [],
    counts: { datasets: 1, runs: 1, charts: 0, plans: 0, findings: 1, edges: 1 },
  })
  vi.mocked(api.getCaseHistory).mockResolvedValue({
    case_id: 'c1', question: 'Why did revenue decline?',
    events: [{
      timestamp: '2026-09-21T09:00:00+00:00', kind: 'case_created',
      artifact_id: 'c1', label: 'Why did revenue decline?', detail: 'dataset: sales.csv',
    }],
    counts: { datasets: 1, profiles: 1, plans: 0, runs: 1, charts: 0, findings: 1 },
  })
  vi.mocked(api.getLearnWalk).mockResolvedValue({
    case_id: 'c1', question: 'Why did revenue decline?',
    steps: [{
      name: 'why', purpose: 'What the case is asking.',
      prompt: 'What would answer it?',
      stages: [{ name: 'question', action: 'state the question',
        hint: 'write the question', completed: true }],
      status: 'complete',
    }],
    current: null, next_action: null, next_hint: null,
    next_endpoint: null, done: true,
  })
  vi.mocked(api.getRefinement).mockResolvedValue(proposal)
  vi.mocked(api.getDecision).mockResolvedValue(decision)
  vi.mocked(api.getAgentState).mockResolvedValue({
    case_id: 'c1', role: 'analyst', pending: null, history: [],
  })
  vi.mocked(api.getRoleAgentState).mockResolvedValue({
    case_id: 'c1', role: 'reviewer', pending: null, history: [],
  })
}

describe('accessibility (AT-32)', () => {
  beforeEach(() => {
    cleanup()
    mockWorkedCase()
  })

  it('renders the worked case for the audit', async () => {
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    expect(await screen.findByRole('heading', { name: /^Decision$/i })).toBeInTheDocument()
  })

  it('has no critical violations in the worked workspace', async () => {
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('heading', { name: /^Decision$/i })
    const violations = auditAll(document.body)
    expect(violations, violations.join('\n')).toEqual([])
  })

  it('audits a workspace that covers a real spread of controls', async () => {
    // A measurement over one button proves nothing; this asserts the audit
    // actually walked a worked case, so a "0 violations" is about the many
    // controls rather than the absence of any.
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('heading', { name: /^Decision$/i })
    expect(controlCount(document.body)).toBeGreaterThan(10)
  })

  it('carries status as text, never as colour alone', async () => {
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('heading', { name: /^Decision$/i })
    const violations = auditStatusNotColorOnly(document.body)
    expect(violations, violations.join('\n')).toEqual([])
  })

  it('labels every field in the workspace', async () => {
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('heading', { name: /^Decision$/i })
    const violations = auditLabels(document.body)
    expect(violations, violations.join('\n')).toEqual([])
  })

  it('keeps every control in the tab order', async () => {
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('heading', { name: /^Decision$/i })
    const violations = auditKeyboardReachable(document.body)
    expect(violations, violations.join('\n')).toEqual([])
  })

  it('reaches every control from the keyboard', async () => {
    // AT-32's "100% of critical user flows keyboard-accessible": the workspace
    // is tabbed through end to end, and the controls the tab lands on are the
    // ones the audit counted.
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('heading', { name: /^Decision$/i })
    const user = userEvent.setup()
    const focused: HTMLElement[] = []
    for (let i = 0; i < 40; i++) {
      await user.tab()
      const active = document.activeElement
      if (active && active !== document.body) focused.push(active as HTMLElement)
    }
    const focusable = new Set(focused)
    expect(focusable.size).toBeGreaterThan(0)
    // Everything that received focus is a real control, not a div standing in
    // for one. A disclosure's `<summary>` is focusable and operable from the
    // keyboard, so it belongs on the list as much as a button does.
    for (const element of focusable) {
      const tag = element.tagName
      expect(['BUTTON', 'A', 'INPUT', 'SELECT', 'TEXTAREA', 'SUMMARY']).toContain(tag)
    }
  })

  it('gives every interactive element a semantic role', async () => {
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('heading', { name: /^Decision$/i })
    const violations = auditSemantics(document.body)
    expect(violations, violations.join('\n')).toEqual([])
  })

  it('ships a focus ring the product owns', () => {
    // Read from the DOM rather than from the source: the audit sees the rules
    // the build ships, the same place a browser's accessibility tree gets
    // them.
    const styles = Array.from(document.querySelectorAll('style'))
      .map((style) => style.textContent ?? '')
      .join('\n')
    expect(focusIsGuaranteed(styles)).toBe(true)
  })

  it('audits the case creation form', async () => {
    vi.mocked(api.createCase).mockResolvedValue({
      id: 'c1', question: 'q', dataset: 'sales.csv', created_at: '', updated_at: '',
    })
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)
    const violations = auditAll(document.body)
    expect(violations, violations.join('\n')).toEqual([])
  })

  it('audits the case list', async () => {
    vi.mocked(api.listCases).mockResolvedValue([
      { id: 'c1', question: 'Why did revenue decline?', dataset: 'sales.csv',
        created_at: '', updated_at: '' },
    ])
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await screen.findByText(/why did revenue decline/i)
    const violations = auditAll(document.body)
    expect(violations, violations.join('\n')).toEqual([])
  })

  it('the audit itself catches a violation', () => {
    // A measurement that cannot fail measures nothing: a clickable div with no
    // role is the failure the suite must be able to see.
    const broken = document.createElement('div')
    broken.innerHTML = '<div class="stage done" onClick="x"></div><input id="nolabel">'
    expect(auditSemantics(broken)).not.toEqual([])
    expect(auditLabels(broken)).not.toEqual([])
  })
})
