// W2X-006: the one-token fix that used to cost another LLM call.
//
// The walk-test hit a 400 on a date the profile had already warned about, and
// the only copy of the code was a read-only <pre>. These tests hold the change:
// the proposal's code arrives in an editor, an edit is what the run posts, and
// a codegen that has become a form cannot silently run the old text.

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../api'
import { GeneratePanel } from './GeneratePanel'

vi.mock('../api', async (importOriginal) => {
  // `ApiError` is a value, not a type: a mock that returns only the functions
  // breaks messageOf's `instanceof ApiError` branch and the refusal it renders.
  const actual = await importOriginal<typeof import('../api')>()
  return {
    ...actual,
    generateCode: vi.fn(),
    runSql: vi.fn(),
    runPython: vi.fn(),
  }
})

const CASE_ID = 'c1'
const dataset = { id: 'd1', case_id: CASE_ID, filename: 'orders.csv', format: 'csv', created_at: '' }
const profile: api.Profile = {
  dataset_id: 'd1', rows: 10, columns: ['order_date'], stats: {},
  duplicate_rows: 0, quality: [], profiled_at: '',
}

const PROPOSED = "SELECT * FROM read_csv_auto(?) WHERE order_date > '2024-13-01'"
const EDITED = "SELECT * FROM read_csv_auto(?) WHERE order_date > '2024-01-01'"

/** The mock's calls array is the assertion's own evidence here, because the
 *  matcher over the mock's bare type is not in this file's typing context. */
function expectLastRun(sql: string) {
  const calls = vi.mocked(api.runSql).mock.calls
  expect(calls[calls.length - 1]).toEqual([CASE_ID, dataset.id, sql])
}

async function propose(user: ReturnType<typeof userEvent.setup>) {
  vi.mocked(api.generateCode).mockResolvedValue({
    dataset_id: 'd1', case_id: CASE_ID, kind: 'sql',
    code: PROPOSED, explanation: 'Revenue by month.', columns_used: ['order_date'],
    source: 'deterministic',
  })
  render(
    <GeneratePanel
      caseId={CASE_ID}
      dataset={dataset}
      profile={profile}
      onChanged={() => {}}
    />,
  )
  await user.type(screen.getByLabelText(/question for code generation/i), 'revenue by month')
  await user.click(screen.getByRole('button', { name: /generate code/i }))
  await screen.findByText('Revenue by month.')
}

describe('the editable proposal (W2X-006)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('shows the proposal in an editor, not a read-only pre', async () => {
    const user = userEvent.setup()
    await propose(user)

    const editor = screen.getByLabelText(/code to run/i) as HTMLTextAreaElement
    expect(editor.value).toBe(PROPOSED)
    expect(document.querySelector('pre')).toBeNull()
  })

  it('runs the edited code, so a one-token fix costs no second LLM call', async () => {
    const user = userEvent.setup()
    await propose(user)
    vi.mocked(api.runSql).mockResolvedValue({
      id: 'r1', case_id: CASE_ID, dataset_id: 'd1', kind: 'sql',
      sql: EDITED, code: null, row_count: 4, truncated: false, executed_at: '',
    })

    const editor = screen.getByLabelText(/code to run/i) as HTMLTextAreaElement
    await user.clear(editor)
    await user.type(editor, EDITED)
    await user.click(screen.getByRole('button', { name: /run this/i }))

    await waitFor(() => expect(vi.mocked(api.runSql)).toHaveBeenCalled())
    expectLastRun(EDITED)
  })

  it('does not run the proposed text once the analyst edited it', async () => {
    const user = userEvent.setup()
    await propose(user)
    vi.mocked(api.runSql).mockResolvedValue({
      id: 'r2', case_id: CASE_ID, dataset_id: 'd1', kind: 'sql',
      sql: EDITED, code: null, row_count: 4, truncated: false, executed_at: '',
    })

    const editor = screen.getByLabelText(/code to run/i) as HTMLTextAreaElement
    await user.clear(editor)
    await user.type(editor, EDITED)
    await user.click(screen.getByRole('button', { name: /run this/i }))

    await waitFor(() => expect(vi.mocked(api.runSql)).toHaveBeenCalled())
    const calls = vi.mocked(api.runSql).mock.calls
    // The run's argument never equals the invalid text the generator proposed.
    expect(calls.map((call) => call[2])).not.toContain(PROPOSED)
  })

  it('runs an untouched proposal unchanged', async () => {
    const user = userEvent.setup()
    await propose(user)
    vi.mocked(api.runSql).mockResolvedValue({
      id: 'r3', case_id: CASE_ID, dataset_id: 'd1', kind: 'sql',
      sql: PROPOSED, code: null, row_count: 0, truncated: false, executed_at: '',
    })

    await user.click(screen.getByRole('button', { name: /run this/i }))

    await waitFor(() => expect(vi.mocked(api.runSql)).toHaveBeenCalled())
    expectLastRun(PROPOSED)
  })
})
