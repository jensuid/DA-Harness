// W2X-007: the capability the core already had, given a door of its own.
//
// The walk-test's complaint was structural: the stage guidance said "Run an
// analysis" while the only paths into /runs were the non-editable codegen and
// the EDA presets. These tests hold the door in place - the engine the analyst
// picks is the endpoint the run posts to, a run the analyst owns lands in the
// case's history, and a refusal is a sentence rather than a silent failure.

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../api'
import { RunCodePanel } from './RunCodePanel'

vi.mock('../api', async (importOriginal) => {
  // The module's own types are not values; `ApiError` is. A mock that returns
  // only the functions breaks messageOf's `instanceof ApiError` branch, and the
  // refusal the panel shows is the thing a broken mock hides.
  const actual = await importOriginal<typeof import('../api')>()
  return {
    ...actual,
    runSql: vi.fn(),
    runPython: vi.fn(),
  }
})

const CASE_ID = 'c1'
const DATASET_ID = 'd1'
const DATASET_NAME = 'orders.csv'

describe('the standalone run-code panel (W2X-007)', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('renders for a named dataset and offers both engines', () => {
    render(
      <RunCodePanel
        caseId={CASE_ID}
        datasetId={DATASET_ID}
        datasetName={DATASET_NAME}
        onChanged={() => {}}
      />,
    )

    expect(
      screen.getByText(`Run code on ${DATASET_NAME}`),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('radio', { name: /sql for a manual run/i }),
    ).toBeInTheDocument()
    expect(
      screen.getByRole('radio', { name: /python for a manual run/i }),
    ).toBeInTheDocument()
  })

  it('sql is the default engine, and python is the analyst\'s choice', async () => {
    const user = userEvent.setup()
    render(
      <RunCodePanel
        caseId={CASE_ID}
        datasetId={DATASET_ID}
        datasetName={DATASET_NAME}
        onChanged={() => {}}
      />,
    )

    expect(screen.getByRole('radio', { name: /sql/i })).toBeChecked()

    await user.click(screen.getByRole('radio', { name: /python for a manual run/i }))

    expect(screen.getByRole('radio', { name: /python/i })).toBeChecked()
  })

  it('runs the sql the analyst wrote against the runs endpoint', async () => {
    const user = userEvent.setup()
    const sql = 'SELECT channel, SUM(revenue) FROM read_csv_auto(?)'
    vi.mocked(api.runSql).mockResolvedValue({
      id: 'r1', case_id: CASE_ID, dataset_id: DATASET_ID, kind: 'sql',
      sql, code: null, row_count: 3, truncated: false, executed_at: '',
    })
    const onChanged = vi.fn()

    render(
      <RunCodePanel
        caseId={CASE_ID}
        datasetId={DATASET_ID}
        datasetName={DATASET_NAME}
        onChanged={onChanged}
      />,
    )
    await user.type(screen.getByLabelText(/sql to run/i), sql)
    await user.click(screen.getByRole('button', { name: /^run$/i }))

    await waitFor(() =>
      expect(api.runSql).toHaveBeenCalledWith(CASE_ID, DATASET_ID, sql),
    )
    expect(api.runPython).not.toHaveBeenCalled()
    // A run that persisted tells the workspace to read the case again.
    expect(onChanged).toHaveBeenCalled()
  })

  it('switching to python posts to the sandbox\'s own endpoint', async () => {
    const user = userEvent.setup()
    const code = 'result = sum(row.revenue for row in dataset.rows)'
    vi.mocked(api.runPython).mockResolvedValue({
      id: 'r2', case_id: CASE_ID, dataset_id: DATASET_ID, kind: 'python',
      sql: null, code, row_count: 1, truncated: false, executed_at: '',
    })

    render(
      <RunCodePanel
        caseId={CASE_ID}
        datasetId={DATASET_ID}
        datasetName={DATASET_NAME}
        onChanged={() => {}}
      />,
    )
    await user.click(screen.getByRole('radio', { name: /python for a manual run/i }))
    await user.type(screen.getByLabelText(/python to run/i), code)
    await user.click(screen.getByRole('button', { name: /^run$/i }))

    await waitFor(() =>
      expect(api.runPython).toHaveBeenCalledWith(CASE_ID, DATASET_ID, code),
    )
    expect(api.runSql).not.toHaveBeenCalled()
  })

  it('clears the editor after a run so the code is not run twice', async () => {
    const user = userEvent.setup()
    vi.mocked(api.runSql).mockResolvedValue({
      id: 'r3', case_id: CASE_ID, dataset_id: DATASET_ID, kind: 'sql',
      sql: 'SELECT 1', code: null, row_count: 1, truncated: false,
      executed_at: '',
    })

    render(
      <RunCodePanel
        caseId={CASE_ID}
        datasetId={DATASET_ID}
        datasetName={DATASET_NAME}
        onChanged={() => {}}
      />,
    )
    await user.type(screen.getByLabelText(/sql to run/i), 'SELECT 1')
    await user.click(screen.getByRole('button', { name: /^run$/i }))

    await waitFor(() =>
      expect((screen.getByLabelText(/sql to run/i) as HTMLTextAreaElement).value).toBe(''),
    )
  })

  it('a refusal answers with a sentence, not a silent failure', async () => {
    const user = userEvent.setup()
    vi.mocked(api.runSql).mockRejectedValue(new Error('unknown table nope'))

    render(
      <RunCodePanel
        caseId={CASE_ID}
        datasetId={DATASET_ID}
        datasetName={DATASET_NAME}
        onChanged={() => {}}
      />,
    )
    await user.type(screen.getByLabelText(/sql to run/i), 'SELECT * FROM nope')
    await user.click(screen.getByRole('button', { name: /^run$/i }))

    expect(await screen.findByText(/run failed: unknown table nope/i)).toBeInTheDocument()
  })

  it('leaves run disabled until there is code to run', () => {
    render(
      <RunCodePanel
        caseId={CASE_ID}
        datasetId={DATASET_ID}
        datasetName={DATASET_NAME}
        onChanged={() => {}}
      />,
    )

    expect(screen.getByRole('button', { name: /^run$/i })).toBeDisabled()
  })
})
