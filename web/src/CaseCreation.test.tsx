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
    createCase: vi.fn().mockResolvedValue({ id: 'case-1', question: 'q', dataset: 'd.csv' }),
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
})
