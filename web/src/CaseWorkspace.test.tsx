import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CaseWorkspace } from './CaseWorkspace'
import * as api from './api'

// Only the fetch functions are replaced; ApiError stays real.
vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return {
    ...actual,
    getCase: vi.fn(),
    getProgress: vi.fn(),
    listDatasets: vi.fn(),
    listRuns: vi.fn(),
    listChat: vi.fn(),
    postChat: vi.fn(),
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

function mockCase() {
  vi.mocked(api.getCase).mockResolvedValue({
    id: 'c1', question: 'Why did revenue decline?', dataset: 'sales.csv',
    created_at: '', updated_at: '',
  })
  vi.mocked(api.getProgress).mockResolvedValue(progress)
  vi.mocked(api.listDatasets).mockResolvedValue([
    { id: 'd1', case_id: 'c1', filename: 'sales.csv', format: 'csv', created_at: '' },
  ])
  vi.mocked(api.listRuns).mockResolvedValue([])
  vi.mocked(api.listChat).mockResolvedValue([])
}

describe('CaseWorkspace', () => {
  it('shows the question, the derived stage, the next action and the artifacts', async () => {
    mockCase()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    expect(screen.getByText(/stage: analyze/i)).toBeInTheDocument()
    expect(screen.getByText('Run an analysis')).toBeInTheDocument()
    expect(screen.getByText('sales.csv')).toBeInTheDocument()
    expect(screen.getByText(/no analysis has run yet/i)).toBeInTheDocument()
  })

  it('marks the completed stages', async () => {
    mockCase()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    expect(screen.getByLabelText('stage question: complete')).toBeInTheDocument()
    expect(screen.getByLabelText('stage analyze: pending')).toBeInTheDocument()
  })

  it('loads prior turns oldest-first', async () => {
    mockCase()
    vi.mocked(api.listChat).mockResolvedValue([
      {
        id: 't1', case_id: 'c1', message: 'How many datasets?',
        answer: 'One.', grounds: ['dataset:sales.csv'], source: 'deterministic',
        created_at: '',
      },
    ])
    render(<CaseWorkspace caseId="c1" onBack={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('How many datasets?')).toBeInTheDocument(),
    )
    expect(screen.getByText('One.')).toBeInTheDocument()
    expect(screen.getByText('dataset:sales.csv')).toBeInTheDocument()
    expect(screen.getByText(/answered by deterministic/i)).toBeInTheDocument()
  })

  it('asks the case and shows the answer with its citations', async () => {
    mockCase()
    vi.mocked(api.postChat).mockResolvedValue({
      id: 't2', case_id: 'c1', message: 'How many runs?',
      answer: 'None yet.', grounds: ['dataset:sales.csv'], source: 'llm',
      created_at: '',
    })
    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    await user.type(screen.getByLabelText(/ask a question/i), 'How many runs?')
    await user.click(screen.getByRole('button', { name: 'Ask' }))

    await waitFor(() => expect(api.postChat).toHaveBeenCalledWith('c1', 'How many runs?'))
    expect(await screen.findByText('None yet.')).toBeInTheDocument()
    expect(screen.getByText('dataset:sales.csv')).toBeInTheDocument()
    expect(screen.getByText(/answered by llm/i)).toBeInTheDocument()
  })

  it('renders an assistant failure rather than crashing', async () => {
    mockCase()
    vi.mocked(api.postChat).mockRejectedValue(new api.ApiError(500, 'Internal Server Error'))
    const user = userEvent.setup()
    render(<CaseWorkspace caseId="c1" onBack={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    await user.type(screen.getByLabelText(/ask a question/i), 'anything')
    await user.click(screen.getByRole('button', { name: 'Ask' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(/could not answer/i)
  })
})
