import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CaseList } from './CaseList'
import * as api from './api'

// Only the fetch functions are replaced; ApiError stays real so the failure
// paths can throw the class the client actually throws.
vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return { ...actual, listCases: vi.fn() }
})

const cases = [
  { id: 'a', question: 'Why did revenue decline?', dataset: 'sales.csv', created_at: '', updated_at: '' },
  { id: 'b', question: 'Which region leads?', dataset: 'regions.csv', created_at: '', updated_at: '' },
]

describe('CaseList', () => {
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

  it('renders a failure as text rather than crashing', async () => {
    vi.mocked(api.listCases).mockRejectedValue(new api.ApiError(500, 'Internal Server Error'))
    render(<CaseList onOpen={() => {}} onCreate={() => {}} />)
    await waitFor(() =>
      expect(screen.getByRole('alert')).toHaveTextContent(/internal server error/i),
    )
  })
})
