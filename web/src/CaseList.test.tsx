import { beforeEach, describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CaseList } from './CaseList'
import * as api from './api'

// Only the fetch functions are replaced; ApiError stays real so the failure
// paths can throw the class the client actually throws.
vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return {
    ...actual,
    listCases: vi.fn(),
    updateCase: vi.fn(),
    duplicateCase: vi.fn(),
    deleteCase: vi.fn(),
    listTemplates: vi.fn(),
  }
})

const cases = [
  { id: 'a', question: 'Why did revenue decline?', dataset: 'sales.csv', created_at: '', updated_at: '' },
  { id: 'b', question: 'Which region leads?', dataset: 'regions.csv', created_at: '', updated_at: '' },
]

describe('CaseList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // The list screen loads templates beside the cases now; an unresolved spy
    // would throw inside the section and put a second alert on the page.
    vi.mocked(api.listTemplates).mockResolvedValue([])
  })

  it('lists cases from the core', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    expect(screen.getByText('Which region leads?')).toBeInTheDocument()
  })

  it('searches through the core and opens a case', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    const onOpen = vi.fn()
    const user = userEvent.setup()
    render(<CaseList onOpen={onOpen} onCreate={() => {}} />)

    await user.type(screen.getByLabelText(/search cases/i), 'revenue')
    await waitFor(() =>
      expect(api.listCases).toHaveBeenLastCalledWith('revenue'),
    )
    await user.click(screen.getByText('Why did revenue decline?'))
    expect(onOpen).toHaveBeenCalledWith('a')
  })

  it('says the row is one open affordance, not a button beside text (W2X-011)', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)

    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    // The question and its dataset are the label of the open button: the
    // whole row is one button, not a button beside the text.
    expect(screen.getByText('Why did revenue decline?').closest('button')).toBe(
      screen.getByText('sales.csv').closest('button'),
    )
  })

  it('reaches for the case row height so any part of it opens the case (W2X-011)', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    const onOpen = vi.fn()
    const user = userEvent.setup()
    render(<CaseList onOpen={onOpen} onCreate={() => {}} />)

    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    const open = screen.getByText('Why did revenue decline?').closest('button')
    expect(open).not.toBeNull()
    // The button is the whole row: it carries the class that stretches it to
    // the row's height, so the blank part below the text is the button too.
    expect(open).toHaveClass('case-open')
    await user.click(open as HTMLElement)
    expect(onOpen).toHaveBeenCalledWith('a')
  })

  it('keeps the row clickable while it is not armed for deletion (W2X-011)', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    const onOpen = vi.fn()
    const user = userEvent.setup()
    render(<CaseList onOpen={onOpen} onCreate={() => {}} />)

    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    const open = screen.getByText('Why did revenue decline?').closest('button')
    expect(open).not.toBeDisabled()
    await user.click(open as HTMLElement)
    expect(onOpen).toHaveBeenCalledWith('a')
  })

  it('says so when the search matches nothing', async () => {
    vi.mocked(api.listCases).mockResolvedValue([])
    const user = userEvent.setup()
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await user.type(screen.getByLabelText(/search cases/i), 'revenue')
    await waitFor(() =>
      expect(screen.getByText(/no cases match that search/i)).toBeInTheDocument(),
    )
  })

  it('says so when there are no cases at all', async () => {
    vi.mocked(api.listCases).mockResolvedValue([])
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText(/no cases yet/i)).toBeInTheDocument(),
    )
  })

  // W2X-010: two rows with the same question and the same dataset differed
  // only in a timestamp nobody reads, so the row that repeats one names it.
  it('marks a row that repeats another case (W2X-010)', async () => {
    vi.mocked(api.listCases).mockResolvedValue([
      { ...cases[0] },
      { ...cases[1], duplicate_of: 'a' },
    ])
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    expect(
      await screen.findByText(/repeats case a/i),
    ).toBeInTheDocument()
  })

  it('names the case a duplicate repeats by its shortened id (W2X-010)', async () => {
    vi.mocked(api.listCases).mockResolvedValue([
      { id: 'f95acdc5', question: 'q', dataset: 'sales.csv',
        duplicate_of: '6a79a75b-1234-5678-9abc-def012345678',
        created_at: '', updated_at: '' },
    ])
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    expect(
      await screen.findByText(/repeats case 6a79a75b/i),
    ).toBeInTheDocument()
  })

  it('marks no row when no case repeats another (W2X-010)', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await waitFor(() =>
      expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument(),
    )
    expect(screen.queryByText(/repeats case/i)).not.toBeInTheDocument()
  })

  it('renders a failure as text rather than crashing', async () => {
    vi.mocked(api.listCases).mockRejectedValue(new api.ApiError(500, 'Internal Server Error'))
    vi.mocked(api.listTemplates).mockResolvedValue([])
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/internal server error/i),
    )
  })

  it('renames a case inline and the list shows the correction', async () => {
    const renamed = [
      { ...cases[0], question: 'Why did revenue double?' },
      cases[1],
    ]
    vi.mocked(api.listCases)
      .mockResolvedValueOnce(cases)
      .mockResolvedValue(renamed)
    vi.mocked(api.updateCase).mockResolvedValue({
      ...cases[0],
      question: 'Why did revenue double?',
    })

    const user = userEvent.setup()
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    await user.click(screen.getByRole('button', { name: /rename why did revenue decline/i }))
    const question = screen.getByLabelText(/case question/i)
    await user.clear(question)
    await user.type(question, 'Why did revenue double?')
    await user.click(screen.getByRole('button', { name: /save/i }))

    await waitFor(() =>
      expect(api.updateCase).toHaveBeenCalledWith('a', {
        question: 'Why did revenue double?',
        dataset: 'sales.csv',
      }),
    )
    expect(await screen.findByText('Why did revenue double?')).toBeInTheDocument()
    expect(screen.queryByText('Why did revenue decline?')).not.toBeInTheDocument()
  })

  it('duplicates a case and the copy appears', async () => {
    vi.mocked(api.listCases)
      .mockResolvedValueOnce(cases)
      .mockResolvedValueOnce([
        ...cases,
        { id: 'c', question: 'Why did revenue decline?', dataset: 'sales.csv', created_at: '', updated_at: '' },
      ])
    vi.mocked(api.duplicateCase).mockResolvedValue({ ...cases[0], id: 'c' })

    const user = userEvent.setup()
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    await user.click(screen.getByRole('button', { name: /duplicate why did revenue decline/i }))

    await waitFor(() => expect(api.duplicateCase).toHaveBeenCalledWith('a'))
    expect(await screen.findAllByText('Why did revenue decline?')).toHaveLength(2)
  })

  it('deletes only after a second click that names what it removes', async () => {
    vi.mocked(api.listCases).mockResolvedValueOnce(cases).mockResolvedValueOnce([cases[1]])
    vi.mocked(api.deleteCase).mockResolvedValue(undefined)

    const user = userEvent.setup()
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    // One click arms; nothing is removed yet.
    await user.click(screen.getByRole('button', { name: /^delete why did revenue decline/i }))
    expect(api.deleteCase).not.toHaveBeenCalled()
    const confirm = screen.getByRole('button', {
      name: /confirm deleting why did revenue decline/i,
    })
    expect(confirm).toBeInTheDocument()

    // The second click is the one that removes, and its label names the case.
    await user.click(confirm)
    await waitFor(() => expect(api.deleteCase).toHaveBeenCalledWith('a'))
    expect(await screen.findByText('Which region leads?')).toBeInTheDocument()
    expect(screen.queryByText('Why did revenue decline?')).not.toBeInTheDocument()
  })

  it('keeps every other case safe while one delete is armed', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    vi.mocked(api.deleteCase).mockResolvedValue(undefined)

    const user = userEvent.setup()
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    // Arm the first case's delete.
    await user.click(
      screen.getByRole('button', { name: /^delete why did revenue decline/i }),
    )
    expect(screen.getAllByRole('button', { name: /confirm deleting/i })).toHaveLength(1)

    // Arming the second case leaves the first armed but unconfirmed, and
    // neither is deleted.
    await user.click(screen.getByRole('button', { name: /^delete which region leads/i }))
    expect(screen.getAllByRole('button', { name: /confirm deleting/i })).toHaveLength(2)
    // Arming the second did not confirm the first.
    expect(api.deleteCase).not.toHaveBeenCalled()
  })

  it('shows the core refusal as a sentence and keeps the list usable', async () => {
    vi.mocked(api.listCases).mockResolvedValue(cases)
    vi.mocked(api.deleteCase).mockRejectedValue(new api.ApiError(409, 'the case is busy'))

    const user = userEvent.setup()
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await screen.findByText('Why did revenue decline?')

    await user.click(screen.getByRole('button', { name: /^delete why did revenue decline/i }))
    await user.click(
      screen.getByRole('button', { name: /confirm deleting why did revenue decline/i }),
    )

    const alert = await screen.findByRole('alert')
    expect(alert).toHaveTextContent(/the case is busy/i)
    // The case is still there: a failed delete removed nothing.
    expect(screen.getByText('Why did revenue decline?')).toBeInTheDocument()
  })
})
