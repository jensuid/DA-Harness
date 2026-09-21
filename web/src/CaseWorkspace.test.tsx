import { beforeEach, describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CaseWorkspace } from './CaseWorkspace'
import * as api from './api'

vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return {
    ...actual,
    getCase: vi.fn(),
    getProgress: vi.fn(),
    listDatasets: vi.fn(),
    listRuns: vi.fn(),
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
    listEvaluations: vi.fn(),
    getAgentState: vi.fn(),
    proposeAgentStep: vi.fn(),
    approveAgentStep: vi.fn(),
    rejectAgentStep: vi.fn(),
    promoteCaseToTemplate: vi.fn(),
  }
})

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
  counts: { datasets: 1, runs: 0 },
}

const dataset = { id: 'd1', case_id: 'c1', filename: 'sales.csv', format: 'csv', created_at: '' }
const profile = {
  dataset_id: 'd1',
  rows: 3,
  columns: ['order_id', 'revenue', 'region'],
  stats: {},
  duplicate_rows: 0,
  profiled_at: '',
}

function runFixture(): api.RunSummary {
  return {
    id: 'r1', case_id: 'c1', dataset_id: 'd1', kind: 'sql', sql: 'q', code: null,
    row_count: 2, truncated: false, executed_at: '',
  }
}

function mockEmptyCase() {
  vi.mocked(api.getCase).mockResolvedValue({
    id: 'c1', question: 'Why did revenue decline?', dataset: 'sales.csv',
    created_at: '', updated_at: '',
  })
  vi.mocked(api.getProgress).mockResolvedValue(progress)
  vi.mocked(api.listDatasets).mockResolvedValue([dataset])
  vi.mocked(api.listRuns).mockResolvedValue([])
  vi.mocked(api.listFindings).mockResolvedValue([])
  vi.mocked(api.listChat).mockResolvedValue([])
  vi.mocked(api.profileDataset).mockResolvedValue(profile)
  vi.mocked(api.listEvaluations).mockResolvedValue([])
  vi.mocked(api.getAgentState).mockResolvedValue(agentIdle())
}

function agentStep(overrides: object = {}): api.AgentStep {
  return {
    id: 's1',
    case_id: 'c1',
    kind: 'analyze',
    payload: { kind: 'sql', code: 'SELECT 1', variant: 0 },
    source: 'deterministic',
    status: 'pending',
    note: '',
    created_at: '',
    decided_at: null,
    ...overrides,
  }
}

function agentIdle(state: object = {}): api.AgentState {
  return { case_id: 'c1', pending: null, history: [], ...state }
}

function finding(axis: string, verdict: string, detail: string) {
  return { axis, verdict, detail }
}

function cleanFindings() {
  return [
    finding('question', 'pass', 'the claim states a position over 3 profiled column(s)'),
    finding('data', 'pass', 'the artifact reads 2 column(s) present in the profile: region, revenue'),
    finding('quality', 'pass', 'no material null or duplicate load'),
    finding('method', 'pass', 'the artifact is read-only, bounded, and reproducible'),
    finding('calculation', 'pass', 'a second execution produced the same result'),
    finding('evidence', 'pass', 'every magnitude the claim quotes appears in the result'),
    finding('claim', 'pass', 'the claim states a direction, so the data can disagree'),
    finding('visualization', 'pass', 'no chart exists and none is required'),
    finding('limitations', 'pass', 'no material limitations: every axis passed'),
  ]
}

function evaluation(overrides: object = {}): api.Evaluation {
  return {
    id: 'e1',
    case_id: 'c1',
    dataset_id: 'd1',
    run_id: 'r9',
    artifact_kind: 'sql',
    code: 'SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region',
    claim: 'Revenue is higher in north than south',
    findings: cleanFindings(),
    source: 'deterministic',
    created_at: '',
    ...overrides,
  }
}

async function submitAudit(user: Awaited<ReturnType<typeof userEvent.setup>>) {
  await user.type(
    screen.getByLabelText(/artifact's code/i),
    'SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region',
  )
  await user.type(
    screen.getByLabelText(/the claim it supports/i),
    'Revenue is higher in north than south',
  )
  await user.click(screen.getByRole('button', { name: /audit this work/i }))
}

describe('CaseWorkspace', () => {
  beforeEach(() => {
    // The api spies are module-level and persist, so the call record is cleared
    // per test - otherwise a "not called" assertion answers for every test that
    // ran before it.
    vi.clearAllMocks()
  })
  it('shows the question, the derived stage, the next action and the artifacts', async () => {
    mockEmptyCase()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    expect(screen.getByText(/stage: analyze/i)).toBeInTheDocument()
    expect(screen.getByText('Run an analysis')).toBeInTheDocument()
    expect(screen.getByText('sales.csv')).toBeInTheDocument()
    expect(screen.getByText(/no analysis has run yet/i)).toBeInTheDocument()
  })

  it('marks the completed stages', async () => {
    mockEmptyCase()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    expect(screen.getByLabelText('stage question: complete')).toBeInTheDocument()
    expect(screen.getByLabelText('stage analyze: pending')).toBeInTheDocument()
  })

  it('reports the profile once the data is attached', async () => {
    mockEmptyCase()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    expect(await screen.findByText(/3 rows, 3 columns, 0 duplicate/i)).toBeInTheDocument()
  })

  it('attaches a file and profiles it', async () => {
    vi.mocked(api.getCase).mockResolvedValue({
      id: 'c1', question: 'Q?', dataset: 'sales.csv', created_at: '', updated_at: '',
    })
    vi.mocked(api.getProgress).mockResolvedValue(progress)
    const attached = { ...dataset, id: 'd2', filename: 'new.csv' }
    vi.mocked(api.listDatasets)
      .mockResolvedValueOnce([])
      .mockResolvedValueOnce([attached])
    vi.mocked(api.listRuns).mockResolvedValue([])
    vi.mocked(api.listFindings).mockResolvedValue([])
    vi.mocked(api.listChat).mockResolvedValue([])
    vi.mocked(api.profileDataset).mockResolvedValue(profile)
    vi.mocked(api.attachDataset).mockResolvedValue(attached)

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText(/no data attached yet/i)

    const input = screen.getByLabelText(/attach a dataset/i)
    await user.upload(input, new File(['a,b\n1,2\n'], 'new.csv', { type: 'text/csv' }))

    await waitFor(() => expect(api.attachDataset).toHaveBeenCalled())
    expect(api.profileDataset).toHaveBeenCalledWith('c1', 'd2')
    expect(await screen.findByText('new.csv')).toBeInTheDocument()
  })

  it('generates code from a question and runs it when the analyst chooses', async () => {
    mockEmptyCase()
    vi.mocked(api.generateCode).mockResolvedValue({
      dataset_id: 'd1', case_id: 'c1', kind: 'sql',
      code: 'SELECT region, SUM(revenue) FROM read_csv_auto(?) GROUP BY region',
      explanation: 'Sums revenue per region.',
      columns_used: ['region', 'revenue'],
      source: 'deterministic',
    })
    vi.mocked(api.runSql).mockResolvedValue({
      id: 'r1', case_id: 'c1', dataset_id: 'd1', kind: 'sql', sql: 'q',
      code: null, row_count: 2, truncated: false, executed_at: '',
    })

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText(/ask for the computation/i)

    await user.type(screen.getByLabelText(/question for code generation/i), 'revenue per region')
    await user.click(screen.getByRole('button', { name: /generate code/i }))

    expect(await screen.findByText('Sums revenue per region.')).toBeInTheDocument()
    expect(screen.getByText(/proposed by deterministic/i)).toBeInTheDocument()
    expect(screen.getByText(/region, revenue/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /run this/i }))
    await waitFor(() => expect(api.runSql).toHaveBeenCalledWith('c1', 'd1',
      'SELECT region, SUM(revenue) FROM read_csv_auto(?) GROUP BY region'))
  })

  it('interprets a run and shows what it says', async () => {
    mockEmptyCase()
    vi.mocked(api.listRuns).mockResolvedValue([runFixture()])
    vi.mocked(api.interpretRun).mockResolvedValue({
      id: 'i1', run_id: 'r1', case_id: 'c1',
      summary: 'North leads on revenue.',
      observations: ['north: 325.0', 'south: 161.0'],
      caveats: ['two rows only'],
      source: 'llm',
      created_at: '',
    })

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    const interpret = await screen.findByRole('button', { name: /interpret/i })
    await user.click(interpret)

    expect(await screen.findByText('North leads on revenue.')).toBeInTheDocument()
    expect(screen.getByText('north: 325.0')).toBeInTheDocument()
    expect(screen.getByText(/caveat: two rows only/i)).toBeInTheDocument()
    expect(screen.getByText(/read by llm/i)).toBeInTheDocument()
  })

  it('drafts a finding and accepts it through the findings endpoint', async () => {
    mockEmptyCase()
    vi.mocked(api.listRuns).mockResolvedValue([runFixture()])
    const draft = {
      run_id: 'r1', case_id: 'c1',
      statement: 'North leads revenue at 325.0.',
      interpretation: 'The north region has the highest total.',
      caveat: 'Only two rows were compared.',
      grounds: ['north: 325.0'],
      source: 'deterministic',
    }
    vi.mocked(api.draftFinding).mockResolvedValue(draft)
    const recorded = {
      id: 'f1', case_id: 'c1', run_id: 'r1', statement: draft.statement,
      interpretation: draft.interpretation, caveat: draft.caveat,
      validation_status: 'not_evaluated', created_at: '',
    }
    vi.mocked(api.acceptFinding).mockResolvedValue(recorded)
    const findingsSoFar: api.Finding[] = []
    vi.mocked(api.listFindings).mockImplementation(async () => [...findingsSoFar])
    vi.mocked(api.acceptFinding).mockImplementation(async () => {
      findingsSoFar.push(recorded)
      return recorded
    })

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await user.click(await screen.findByRole('button', { name: /draft a finding/i }))

    expect(await screen.findByText('North leads revenue at 325.0.')).toBeInTheDocument()
    expect(screen.getByText('north: 325.0')).toBeInTheDocument()
    expect(screen.getByText(/not_evaluated until validated/i)).toBeInTheDocument()

    await user.click(screen.getByRole('button', { name: /accept as a finding/i }))
    await waitFor(() => expect(api.acceptFinding).toHaveBeenCalledWith('c1', 'r1', draft))

    // The draft panel clears and the recorded finding renders.
    await screen.findByText(/status: not_evaluated/i)
  })

  it('validates a recorded finding and shows the verdict', async () => {
    mockEmptyCase()
    vi.mocked(api.listFindings).mockResolvedValue([
      { id: 'f1', case_id: 'c1', run_id: 'r1', statement: 'North leads revenue.',
        interpretation: null, caveat: null, validation_status: 'not_evaluated',
        created_at: '' },
    ])
    vi.mocked(api.validateFinding).mockResolvedValue({
      finding_id: 'f1', run_id: 'r1', status: 'supported',
      checks: [
        { name: 'reproducibility', passed: true, detail: 'rerun matches stored result' },
        { name: 'missing_data', passed: true, detail: '0 null value(s)' },
      ],
      validated_at: '',
    })

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await user.click(await screen.findByRole('button', { name: /validate/i }))

    expect(await screen.findByText(/verdict: supported/i)).toBeInTheDocument()
    expect(screen.getByText(/rerun matches stored result/i)).toBeInTheDocument()
  })

  it('renders an assistant failure rather than crashing', async () => {
    mockEmptyCase()
    vi.mocked(api.postChat).mockRejectedValue(new api.ApiError(500, 'Internal Server Error'))
    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    await user.type(screen.getByLabelText(/ask a question/i), 'anything')
    await user.click(screen.getByRole('button', { name: 'Ask' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not answer/i)
  })

  it('audits submitted work and shows all nine axes with their sentences', async () => {
    mockEmptyCase()
    vi.mocked(api.evaluateDataset).mockResolvedValue(evaluation())

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText(/audit submitted work/i)
    await submitAudit(user)

    // Scoped to the audit: the workflow's stage list also renders a checkmark
    // and an axis name, so the badge must be found inside the audit it belongs to.
    const audit = await screen.findByTestId('audit')
    // Nine axes in the spec's own order, each with its verdict and its sentence.
    for (const [mark, axis] of [
      ['✓', 'question'], ['✓', 'data'], ['✓', 'quality'], ['✓', 'method'],
      ['✓', 'calculation'], ['✓', 'evidence'], ['✓', 'claim'],
      ['✓', 'visualization'], ['✓', 'limitations'],
    ] as const) {
      expect(within(audit).getByText(`${mark} ${axis}`)).toBeInTheDocument()
    }
    expect(within(audit).getByText(/every magnitude the claim quotes appears/i)).toBeInTheDocument()
    expect(api.evaluateDataset).toHaveBeenCalledWith(
      'c1', 'd1',
      'SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region',
      'Revenue is higher in north than south',
      'sql',
    )
  })

  it('shows a failing axis with its value, not only its name', async () => {
    mockEmptyCase()
    vi.mocked(api.evaluateDataset).mockResolvedValue(
      evaluation({
        findings: cleanFindings().map((f) =>
          f.axis === 'evidence'
            ? finding('evidence', 'fail', 'the claim quotes values absent from the result: 999')
            : f,
        ),
      }),
    )

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText(/audit submitted work/i)
    await submitAudit(user)

    const audit = await screen.findByTestId('audit')
    expect(within(audit).getByText(/✗ evidence/i)).toBeInTheDocument()
    expect(within(audit).getByText(/absent from the result: 999/i)).toBeInTheDocument()
  })

  it('shows the core refusal as a sentence and records nothing', async () => {
    mockEmptyCase()
    vi.mocked(api.evaluateDataset).mockRejectedValue(
      new api.ApiError(400, 'the artifact is not a single read-only query'),
    )

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText(/audit submitted work/i)
    await submitAudit(user)

    expect(await screen.findByRole('alert')).toHaveTextContent(
      /not a single read-only query/i,
    )
    // The panel is still there, ready for corrected work.
    expect(screen.getByRole('button', { name: /audit this work/i })).toBeInTheDocument()
  })

  it('lists the audits already recorded over the dataset, newest first', async () => {
    mockEmptyCase()
    vi.mocked(api.listEvaluations).mockResolvedValue([
      evaluation({
        id: 'e2',
        claim: 'North totals 999.0, more than south',
        findings: [
          ...cleanFindings().slice(0, 5),
          finding('evidence', 'fail', 'the claim quotes values absent from the result: 999'),
          ...cleanFindings().slice(6),
        ],
      }),
      evaluation({ id: 'e1', claim: 'Revenue is higher in north than south' }),
    ])

    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    const recorded = await screen.findByText(/recorded audits/i)
    const claims = within(recorded.parentElement!)
      .getAllByRole('listitem')
      .map((item) => item.textContent ?? '')
    // Newest first, as the core's listing orders them.
    expect(claims[0]).toContain('North totals 999.0')
    expect(claims[0]).toContain('evidence: fail')
    expect(claims[1]).toContain('Revenue is higher in north than south')
    expect(claims[1]).toContain('every axis passed')
  })

  it('switches the submission between SQL and Python', async () => {
    mockEmptyCase()
    vi.mocked(api.evaluateDataset).mockResolvedValue(evaluation({ artifact_kind: 'python' }))

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText(/audit submitted work/i)

    await user.click(screen.getByLabelText(/python/i))
    await user.type(screen.getByLabelText(/artifact's code/i), 'result = 42')
    await user.type(screen.getByLabelText(/the claim it supports/i), 'A python claim')
    await user.click(screen.getByRole('button', { name: /audit this work/i }))

    await waitFor(() => expect(api.evaluateDataset).toHaveBeenCalled())
    expect(api.evaluateDataset).toHaveBeenCalledWith(
      'c1', 'd1', 'result = 42', 'A python claim', 'python',
    )
  })

  it('waits for a profile before offering an audit', async () => {
    vi.mocked(api.getCase).mockResolvedValue({
      id: 'c1', question: 'Q?', dataset: 'sales.csv', created_at: '', updated_at: '',
    })
    vi.mocked(api.getProgress).mockResolvedValue(progress)
    vi.mocked(api.listDatasets).mockResolvedValue([dataset])
    vi.mocked(api.listRuns).mockResolvedValue([])
    vi.mocked(api.listFindings).mockResolvedValue([])
    vi.mocked(api.listChat).mockResolvedValue([])
    // No profile yet, so the dataset is not auditable.
    vi.mocked(api.profileDataset).mockRejectedValue(new api.ApiError(404, 'no profile'))

    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    expect(await screen.findByText(/attach and profile a dataset first/i)).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /audit this work/i })).not.toBeInTheDocument()
  })

  it('shows the agent state and a pending proposal as a sentence', async () => {
    mockEmptyCase()
    vi.mocked(api.getAgentState).mockResolvedValue(
      agentIdle({
        pending: agentStep({
          id: 's7',
          kind: 'accept',
          payload: { run_id: 'r1', statement: 'North leads revenue' },
        }),
      }),
    )

    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    expect(await screen.findByText(/north leads revenue/i)).toBeInTheDocument()
    expect(screen.getByText(/proposed by deterministic/i)).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /approve and run/i })).toBeInTheDocument()
  })

  it('proposes idempotently and a second call writes nothing more', async () => {
    mockEmptyCase()
    const proposed = agentIdle({ pending: agentStep({ id: 's7' }) })
    vi.mocked(api.proposeAgentStep).mockResolvedValue(proposed)

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByText(/nothing is pending/i)

    await user.click(screen.getByRole('button', { name: /propose the next step/i }))
    await waitFor(() => expect(api.proposeAgentStep).toHaveBeenCalledTimes(1))

    // The same button again: the contract returns the same pending step, and
    // the panel still holds exactly one proposal.
    await user.click(screen.getByRole('button', { name: /re-derive the next step/i }))
    await waitFor(() => expect(api.proposeAgentStep).toHaveBeenCalledTimes(2))
    expect(await screen.findByText(/approve to run it/i)).toBeInTheDocument()
  })

  it('approves a step and the next proposal arrives with it', async () => {
    mockEmptyCase()
    // The workspace reloads the state after the write, so the second read must
    // show the world the approval produced, not the one it replaced.
    vi.mocked(api.getAgentState)
      .mockResolvedValueOnce(agentIdle({ pending: agentStep({ id: 's7' }) }))
      .mockResolvedValue(
        agentIdle({
          pending: agentStep({ id: 's8', kind: 'interpret' }),
          history: [
            agentStep({
              id: 's7',
              kind: 'analyze',
              status: 'done',
              note: 'ran sql variant 0: 2 row(s)',
            }),
          ],
        }),
      )
    vi.mocked(api.approveAgentStep).mockResolvedValue(
      agentIdle({
        pending: agentStep({ id: 's8', kind: 'interpret' }),
        history: [
          agentStep({
            id: 's7',
            kind: 'analyze',
            status: 'done',
            note: 'ran sql variant 0: 2 row(s)',
          }),
        ],
      }),
    )

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await user.click(await screen.findByRole('button', { name: /approve and run/i }))

    expect(await waitFor(() => expect(api.approveAgentStep).toHaveBeenCalledWith('c1', 's7')))
    // The response carried the next proposal, so no second call is needed.
    expect(api.proposeAgentStep).not.toHaveBeenCalled()
    expect(await screen.findByText(/interpret the last run/i)).toBeInTheDocument()
    expect(screen.getByText(/ran sql variant 0: 2 row\(s\)/i)).toBeInTheDocument()
  })

  it('rejects with a reason and writes nothing', async () => {
    mockEmptyCase()
    vi.mocked(api.getAgentState)
      .mockResolvedValueOnce(agentIdle({ pending: agentStep({ id: 's7' }) }))
      .mockResolvedValue(
        agentIdle({
          history: [
            agentStep({
              id: 's7',
              status: 'rejected',
              note: 'wrong direction',
            }),
          ],
        }),
      )
    vi.mocked(api.rejectAgentStep).mockResolvedValue(
      agentIdle({
        history: [
          agentStep({
            id: 's7',
            status: 'rejected',
            note: 'wrong direction',
          }),
        ],
      }),
    )

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await screen.findByRole('button', { name: /reject/i })

    await user.type(screen.getByLabelText(/reason for rejecting/i), 'wrong direction')
    await user.click(screen.getByRole('button', { name: /reject/i }))

    await waitFor(() =>
      expect(api.rejectAgentStep).toHaveBeenCalledWith('c1', 's7', 'wrong direction'),
    )
    // No write of case state: the workspace reloaded, but no approval ran.
    expect(api.approveAgentStep).not.toHaveBeenCalled()
    expect(await screen.findByText(/✗ analyze/i)).toBeInTheDocument()
  })

  it('shows a stale approval as a sentence, never "[object Object]"', async () => {
    mockEmptyCase()
    vi.mocked(api.getAgentState)
      .mockResolvedValueOnce(agentIdle({ pending: agentStep({ id: 's7' }) }))
      .mockResolvedValue(agentIdle({ pending: null, history: [] }))
    // The core answers 409 with an object as the detail.
    vi.mocked(api.approveAgentStep).mockRejectedValue(
      new api.ApiError(409, "the step id is not this case's pending step"),
    )

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await user.click(await screen.findByRole('button', { name: /approve and run/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/not this case's pending step/i)
    expect(alert.textContent).not.toContain('[object Object]')
  })

  it('shows a cited previous case as a button that opens it', async () => {
    // Recall is only useful if the analyst can go and read what was concluded
    // last time (P7-SHELL-006). The core cites the prior case in grounds as
    // `case:<id>`; the chip carries a uuid and goes nowhere without this.
    mockEmptyCase()
    vi.mocked(api.listChat).mockResolvedValue([
      {
        id: 'm1',
        case_id: 'c1',
        message: 'What did I find before about revenue?',
        answer:
          'Before this case, a previous case, "Why did revenue decline?", ' +
          'which found North leads revenue. It shares revenue with your question.',
        grounds: ['case:prior', 'finding:f9'],
        source: 'deterministic',
        created_at: '',
      },
    ])
    vi.mocked(api.getCase).mockImplementation(async (id: string) => {
      if (id === 'prior') {
        return {
          id, question: 'Why did revenue decline?', dataset: 'sales.csv',
          created_at: '', updated_at: '',
        }
      }
      return {
        id: 'c1', question: 'Why did revenue decline?', dataset: 'sales.csv',
        created_at: '', updated_at: '',
      }
    })

    const onOpenCase = vi.fn()
    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={onOpenCase} />)
    const button = await screen.findByRole('button', {
      name: /open the previous case: why did revenue decline/i,
    })
    expect(button).toBeInTheDocument()

    await user.click(button)
    expect(onOpenCase).toHaveBeenCalledWith('prior')
  })

  it('looks a cited case up once however many turns cite it', async () => {
    mockEmptyCase()
    vi.mocked(api.listChat).mockResolvedValue([
      {
        id: 'm1', case_id: 'c1', message: 'before?', answer: 'one',
        grounds: ['case:prior'], source: 'deterministic', created_at: '',
      },
      {
        id: 'm2', case_id: 'c1', message: 'earlier?', answer: 'two',
        grounds: ['case:prior'], source: 'deterministic', created_at: '',
      },
    ])
    vi.mocked(api.getCase).mockResolvedValue({
      id: 'prior', question: 'Why did revenue decline?', dataset: 'sales.csv',
      created_at: '', updated_at: '',
    })

    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await waitFor(() =>
      expect(screen.getAllByRole('button', { name: /open the previous case/i })).toHaveLength(2),
    )
    // Two citations, one lookup: the question does not change between turns.
    // (The workspace's own load accounts for the other call.)
    const lookups = vi.mocked(api.getCase).mock.calls.filter(
      ([id]) => id === 'prior',
    )
    expect(lookups).toHaveLength(1)
  })

  it('degrades to a chip when a cited case can no longer be read', async () => {
    // A citation outlives the case it names - the case may have been deleted.
    // The answer stays readable and nothing throws.
    mockEmptyCase()
    vi.mocked(api.listChat).mockResolvedValue([
      {
        id: 'm1', case_id: 'c1', message: 'before?', answer: 'North leads revenue.',
        grounds: ['case:gone'], source: 'deterministic', created_at: '',
      },
    ])
    vi.mocked(api.getCase).mockImplementation(async (id: string) => {
      if (id === 'gone') {
        throw new api.ApiError(404, 'case not found')
      }
      return {
        id: 'c1', question: 'Why did revenue decline?', dataset: 'sales.csv',
        created_at: '', updated_at: '',
      }
    })

    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    expect(await screen.findByText(/no longer available/i)).toBeInTheDocument()
    expect(screen.getByText('North leads revenue.')).toBeInTheDocument()
    expect(screen.queryByRole('button', { name: /open the previous case/i })).not.toBeInTheDocument()
  })

  it('renders grounds of other kinds as the chips they always were', async () => {
    mockEmptyCase()
    vi.mocked(api.listChat).mockResolvedValue([
      {
        id: 'm1', case_id: 'c1', message: 'How many in north?',
        answer: 'north: 325.0, in sales.csv.',
        grounds: ['column:north', 'dataset:sales.csv'],
        source: 'deterministic', created_at: '',
      },
    ])

    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    expect(await screen.findByText(/north: 325\.0/)).toBeInTheDocument()
    expect(screen.getByText('column:north')).toBeInTheDocument()
    expect(screen.getByText('dataset:sales.csv')).toBeInTheDocument()
  })

  it('saves the case as a template, named for the question when no name is given', async () => {
    mockEmptyCase()
    vi.mocked(api.promoteCaseToTemplate).mockResolvedValue({
      id: 't1',
      name: 'Why did revenue decline?',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      shape: null,
      created_at: '',
    })

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )

    // No name typed: the core defaults it to the case's question.
    await user.click(screen.getByRole('button', { name: /save as a template/i }))
    await waitFor(() =>
      expect(api.promoteCaseToTemplate).toHaveBeenCalledWith('c1', ''),
    )
    expect(await screen.findByText(/saved as/i)).toHaveTextContent(
      'Why did revenue decline?',
    )
  })

  it('sends the chosen name when the case is promoted', async () => {
    mockEmptyCase()
    vi.mocked(api.promoteCaseToTemplate).mockResolvedValue({
      id: 't2',
      name: 'Revenue decline playbook',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      shape: null,
      created_at: '',
    })

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )

    await user.type(screen.getByLabelText(/template name/i), 'Revenue decline playbook')
    await user.click(screen.getByRole('button', { name: /save as a template/i }))

    await waitFor(() =>
      expect(api.promoteCaseToTemplate).toHaveBeenCalledWith(
        'c1',
        'Revenue decline playbook',
      ),
    )
    expect(await screen.findByText('Revenue decline playbook')).toBeInTheDocument()
  })

  it('shows the core refusal when a promotion fails', async () => {
    mockEmptyCase()
    vi.mocked(api.promoteCaseToTemplate).mockRejectedValue(
      new api.ApiError(400, 'name must not be empty'),
    )

    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )

    await user.click(screen.getByRole('button', { name: /save as a template/i }))

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/name must not be empty/i)
    // The panel is still ready for a corrected attempt.
    expect(screen.getByRole('button', { name: /save as a template/i })).toBeEnabled()
  })

  it('states why the agent stopped when nothing is pending', async () => {
    mockEmptyCase()
    vi.mocked(api.getAgentState).mockResolvedValue(
      agentIdle({
        history: [
          agentStep({
            id: 's9',
            kind: 'end',
            status: 'done',
            note: 'the budget is exhausted: 12 steps',
          }),
        ],
      }),
    )

    render(<CaseWorkspace caseId="c1" onBack={() => {}} onOpenCase={() => {}} />)
    // The note rides in both the stopped sentence and the history's last step,
    // so the sentence is the unique thing to assert on.
    expect(
      await screen.findByText(/the agent stopped: the budget is exhausted/i),
    ).toBeInTheDocument()
  })
})
