import { beforeEach, describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { Templates } from './Templates'
import * as api from './api'

// Only the fetch functions are replaced; ApiError stays real so a failure path
// throws the class the client actually throws.
vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return {
    ...actual,
    listTemplates: vi.fn(),
    createCaseFromTemplate: vi.fn(),
    deleteTemplate: vi.fn(),
  }
})

const shaped = {
  id: 't1',
  name: 'Revenue decline playbook',
  question: 'Why did revenue decline?',
  dataset: 'sales.csv',
  shape: {
    plan: { steps: [] },
    plan_source: 'deterministic',
    proposals: [
      {
        kind: 'sql',
        code: 'SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region',
        explanation: 'Total revenue per region',
        columns_used: ['region', 'revenue'],
      },
    ],
    findings: [
      { statement: 'North leads revenue', validation_status: 'validated' },
      { statement: 'South is flat', validation_status: 'not_evaluated' },
    ],
  },
  created_at: '',
}

const shapeless = {
  id: 't2',
  name: 'Weather and sales',
  question: 'Does weather move sales?',
  dataset: 'weather.csv',
  shape: null,
  created_at: '',
}

describe('Templates', () => {
  beforeEach(() => {
    // The spies are module-level and accumulate, so the record is cleared per
    // test - a "not called" assertion otherwise answers for every prior test.
    vi.clearAllMocks()
  })

  it('lists templates with the shape each one carries', async () => {
    vi.mocked(api.listTemplates).mockResolvedValue([shaped])
    render(<Templates onOpen={() => {}} />)

    expect(await screen.findByText('Revenue decline playbook')).toBeInTheDocument()
    expect(screen.getByText(/why did revenue decline/i)).toBeInTheDocument()
    expect(screen.getByText(/— sales\.csv/)).toBeInTheDocument()
    // The summary is the point: a name alone cannot say what kind of
    // investigation a template is.
    expect(screen.getByText(/carries 1 proposal/i)).toHaveTextContent(
      '2 findings (1 validated, 1 not_evaluated)',
    )
  })

  it('says so when a template carries no shape', async () => {
    vi.mocked(api.listTemplates).mockResolvedValue([shapeless])
    render(<Templates onOpen={() => {}} />)

    expect(await screen.findByText('Weather and sales')).toBeInTheDocument()
    // Zeroes would imply an empty investigation; this one was never recorded.
    expect(screen.getByText(/question-only skeleton/i)).toBeInTheDocument()
    expect(screen.queryByText(/carries/i)).not.toBeInTheDocument()
  })

  it('says so when there are no templates at all', async () => {
    vi.mocked(api.listTemplates).mockResolvedValue([])
    render(<Templates onOpen={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText(/no templates yet/i)).toBeInTheDocument(),
    )
  })

  it('starts a case from a template and opens it', async () => {
    vi.mocked(api.listTemplates).mockResolvedValue([shaped])
    vi.mocked(api.createCaseFromTemplate).mockResolvedValue({
      id: 'c9',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      created_at: '',
      updated_at: '',
    })
    const onOpen = vi.fn()
    const user = userEvent.setup()
    render(<Templates onOpen={onOpen} />)

    await screen.findByText('Revenue decline playbook')
    await user.click(
      screen.getByRole('button', { name: /start a case from revenue decline playbook/i }),
    )

    await waitFor(() =>
      expect(api.createCaseFromTemplate).toHaveBeenCalledWith('t1'),
    )
    expect(onOpen).toHaveBeenCalledWith('c9')
  })

  it('retires a template and the list shows the rest', async () => {
    vi.mocked(api.listTemplates)
      .mockResolvedValueOnce([shaped, shapeless])
      .mockResolvedValue([shapeless])
    vi.mocked(api.deleteTemplate).mockResolvedValue(undefined)

    const user = userEvent.setup()
    render(<Templates onOpen={() => {}} />)
    await screen.findByText('Revenue decline playbook')

    await user.click(
      screen.getByRole('button', { name: /retire the template revenue decline playbook/i }),
    )

    await waitFor(() => expect(api.deleteTemplate).toHaveBeenCalledWith('t1'))
    expect(await screen.findByText('Weather and sales')).toBeInTheDocument()
    expect(screen.queryByText('Revenue decline playbook')).not.toBeInTheDocument()
  })

  it('shows the core refusal as a sentence and keeps the template usable', async () => {
    vi.mocked(api.listTemplates).mockResolvedValue([shaped])
    vi.mocked(api.createCaseFromTemplate).mockRejectedValue(
      new api.ApiError(404, 'template not found'),
    )

    const user = userEvent.setup()
    render(<Templates onOpen={() => {}} />)
    await screen.findByText('Revenue decline playbook')

    await user.click(
      screen.getByRole('button', { name: /start a case from revenue decline playbook/i }),
    )

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/template not found/i)
    // The template is still there: a failed start changed nothing.
    expect(screen.getByText('Revenue decline playbook')).toBeInTheDocument()
  })

  it('renders a failed load as text rather than crashing', async () => {
    vi.mocked(api.listTemplates).mockRejectedValue(
      new api.ApiError(500, 'internal error'),
    )
    render(<Templates onOpen={() => {}} />)
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/internal error/i),
    )
  })
})
