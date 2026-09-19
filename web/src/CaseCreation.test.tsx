import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { CaseCreation } from './CaseCreation'

vi.mock('./api', () => ({
  getHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
  createCase: vi.fn().mockResolvedValue({ id: 'case-1', question: 'q', dataset: 'd.csv' }),
}))

describe('CaseCreation', () => {
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
})
