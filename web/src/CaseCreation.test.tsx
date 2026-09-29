import { beforeEach, describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CaseCreation } from './CaseCreation'
import { createCase } from './api'

vi.mock('./api', async (importOriginal) => {
  const original = await importOriginal<typeof import('./api')>()
  return {
    ...original,
    getHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
    createCase: vi.fn().mockResolvedValue({
      id: 'case-1',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      created_at: '',
      updated_at: '',
    }),
  }
})

describe('CaseCreation', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders the creation form', async () => {
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)
    expect(screen.getByText(/new analysis case/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/question/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/dataset/i)).toBeInTheDocument()
  })

  it('reports the core as reachable when /health is ok', async () => {
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText(/core status: reachable/i)).toBeInTheDocument(),
    )
  })

  it('opens the created case in its workspace', async () => {
    const user = userEvent.setup()
    const onCreated = vi.fn()
    render(<CaseCreation onCreated={onCreated} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('case-1'))
  })

  // W2X-002: the walk-test's first wall. Submitting with the dataset empty was
  // total silence - no request, no alert, nothing changed - because only HTML5
  // native validation stood behind the submit, and its message is invisible
  // headlessly and undiscoverable for a first-time analyst. The field's own
  // sentence now answers, in the DOM and in a screen reader.
  it('says which fields are required instead of failing silently', async () => {
    const user = userEvent.setup()
    const onCreated = vi.fn()
    render(<CaseCreation onCreated={onCreated} onCancel={() => {}} />)

    await user.click(screen.getByRole('button', { name: /create case/i }))

    // No request left the page, and no case was created.
    expect(createCase).not.toHaveBeenCalled()
    expect(onCreated).not.toHaveBeenCalled()
    // Both required fields are named, as live regions a screen reader hears.
    expect(
      await screen.findByText(/a question is required/i),
    ).toBeInTheDocument()
    expect(screen.getByText(/a dataset filename is required/i)).toBeInTheDocument()
  })

  it('asks only for the field the analyst left blank', async () => {
    const user = userEvent.setup()
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    expect(screen.queryByText(/a question is required/i)).not.toBeInTheDocument()
    expect(
      await screen.findByText(/a dataset filename is required/i),
    ).toBeInTheDocument()
    expect(createCase).not.toHaveBeenCalled()
  })

  it('marks the blank fields as invalid for assistive technology', async () => {
    const user = userEvent.setup()
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)

    await user.click(screen.getByRole('button', { name: /create case/i }))

    expect(screen.getByLabelText(/question/i)).toHaveAttribute('aria-invalid', 'true')
    expect(screen.getByLabelText(/dataset/i)).toHaveAttribute('aria-invalid', 'true')
  })

  it('clears the message once the analyst fills the field', async () => {
    const user = userEvent.setup()
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)

    await user.click(screen.getByRole('button', { name: /create case/i }))
    expect(
      await screen.findByText(/a dataset filename is required/i),
    ).toBeInTheDocument()

    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')

    expect(screen.queryByText(/a dataset filename is required/i)).not.toBeInTheDocument()
  })

  // W2X-010: the second walk-test's last finding. The list showed two rows for
  // the same question and the same dataset with nothing to tell them apart but
  // a timestamp nobody reads, and the gap was that nobody said so. The core
  // answers with the case this one repeats, and the form says it back.
  it('says when a case already asks this question about this dataset', async () => {
    const user = userEvent.setup()
    const onCreated = vi.fn()
    vi.mocked(createCase).mockResolvedValue({
      id: 'case-2',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      duplicate_of: 'case-1',
      created_at: '',
      updated_at: '',
    })
    render(<CaseCreation onCreated={onCreated} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    // The case was made - the notice is what was missing, not a refusal - and
    // the sentence is announced as a status change a screen reader hears.
    await waitFor(() => expect(createCase).toHaveBeenCalled())
    expect(onCreated).not.toHaveBeenCalled()
    expect(
      screen.getByText(/a case already asks/i, { exact: false }),
    ).toBeInTheDocument()
    expect(screen.getByText(/sales.csv/)).toBeInTheDocument()
    expect(screen.getByText(/keep it if you meant to re-run the question/i)).toBeInTheDocument()
  })

  it('names the question and dataset the duplicate shares', async () => {
    const user = userEvent.setup()
    vi.mocked(createCase).mockResolvedValue({
      id: 'case-2',
      question: 'Why did churn rise?',
      dataset: 'users.csv',
      duplicate_of: 'case-1',
      created_at: '',
      updated_at: '',
    })
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did churn rise?')
    await user.type(screen.getByLabelText(/dataset/i), 'users.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    expect(
      await screen.findByText(/Why did churn rise\?/i, { exact: false }),
    ).toBeInTheDocument()
  })

  it('stays silent when the created case is no ones duplicate', async () => {
    const user = userEvent.setup()
    const onCreated = vi.fn()
    vi.mocked(createCase).mockResolvedValue({
      id: 'case-1',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      created_at: '',
      updated_at: '',
    })
    render(<CaseCreation onCreated={onCreated} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('case-1'))
    expect(screen.queryByText(/a case already asks/i)).not.toBeInTheDocument()
  })

  it('offers the existing case and opens it', async () => {
    const user = userEvent.setup()
    const onView = vi.fn()
    vi.mocked(createCase).mockResolvedValue({
      id: 'case-2',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      duplicate_of: 'case-1',
      created_at: '',
      updated_at: '',
    })
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} onView={onView} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    const link = await screen.findByRole('button', { name: /see the existing case/i })
    await user.click(link)

    expect(onView).toHaveBeenCalledWith('case-1')
  })

  it('renders no link when the parent cannot open a case', async () => {
    const user = userEvent.setup()
    vi.mocked(createCase).mockResolvedValue({
      id: 'case-2',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      duplicate_of: 'case-1',
      created_at: '',
      updated_at: '',
    })
    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    expect(
      await screen.findByText(/a case already asks/i, { exact: false }),
    ).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: /see the existing case/i }),
    ).not.toBeInTheDocument()
  })

  it('says nothing when the save itself fails', async () => {
    const user = userEvent.setup()
    vi.mocked(createCase).mockRejectedValue(new Error('core down'))

    render(<CaseCreation onCreated={() => {}} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    await screen.findByText(/failed: core down/i)
    expect(screen.queryByText(/a case already asks/i)).not.toBeInTheDocument()
  })

  it('clears a duplicate notice once the question changes and is saved again', async () => {
    const user = userEvent.setup()
    vi.mocked(createCase).mockResolvedValueOnce({
      id: 'case-2',
      question: 'Why did revenue decline?',
      dataset: 'sales.csv',
      duplicate_of: 'case-1',
      created_at: '',
      updated_at: '',
    })
    vi.mocked(createCase).mockResolvedValueOnce({
      id: 'case-3',
      question: 'Why did churn rise?',
      dataset: 'sales.csv',
      created_at: '',
      updated_at: '',
    })
    const onCreated = vi.fn()
    render(<CaseCreation onCreated={onCreated} onCancel={() => {}} />)

    await user.type(screen.getByLabelText(/question/i), 'Why did revenue decline?')
    await user.type(screen.getByLabelText(/dataset/i), 'sales.csv')
    await user.click(screen.getByRole('button', { name: /create case/i }))
    expect(
      await screen.findByText(/a case already asks/i, { exact: false }),
    ).toBeInTheDocument()

    await user.clear(screen.getByLabelText(/question/i))
    await user.type(screen.getByLabelText(/question/i), 'Why did churn rise?')
    await user.click(screen.getByRole('button', { name: /create case/i }))

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('case-3'))
    expect(screen.queryByText(/a case already asks/i)).not.toBeInTheDocument()
  })
})
