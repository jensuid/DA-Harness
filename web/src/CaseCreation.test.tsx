import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { CaseCreation } from './CaseCreation'

vi.mock('./api', () => ({
  getHealth: vi.fn().mockResolvedValue({ status: 'ok' }),
  createCase: vi.fn().mockResolvedValue(undefined),
}))

describe('CaseCreation', () => {
  it('renders the creation form', async () => {
    render(<CaseCreation />)
    expect(screen.getByText(/new analysis case/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/question/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/dataset/i)).toBeInTheDocument()
  })

  it('reports the core as reachable when /health is ok', async () => {
    render(<CaseCreation />)
    await waitFor(() =>
      expect(screen.getByText(/core status: reachable/i)).toBeInTheDocument(),
    )
  })
})
