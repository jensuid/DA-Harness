// W2X-007: the capability the core already had, given a door of its own.
//
// The walk-test's complaint was structural: the stage guidance said "Run an
// analysis" while the only paths into /runs were the non-editable codegen and
// the EDA presets. These tests hold the door in place - the engine the analyst
// picks is the endpoint the run posts to, a run the analyst owns lands in the
// case's history, and a refusal is a sentence rather than a silent failure.
//
// W3X-004 adds the door's own sign: the Python sandbox's contract is on the
// page before the first run, so the three refusals the walk measured (pandas,
// csv and the `path` variable the SQL placeholder implies) are answered by
// the surface rather than by the error that follows.

import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import * as api from '../api'
import { PYTHON_ALLOWED_MODULES, RunCodePanel } from './RunCodePanel'

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

// The allowlist the sandbox's import wall admits, read from the module the
// wall lives in. The panel carries its own copy so the page can render it
// without a fetch; this is the test that keeps the two the same set.
import pythonExec from '../../../server/app/python_exec.py?raw'

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

  // ------------------------------------------------------- W3X-004: the sign on the wall

  describe('the python sandbox\'s contract (W3X-004)', () => {
    it('names the handle, the columns and the query door', async () => {
      const user = userEvent.setup()
      render(
        <RunCodePanel
          caseId={CASE_ID}
          datasetId={DATASET_ID}
          datasetName={DATASET_NAME}
          onChanged={() => {}}
        />,
      )
      await user.click(screen.getByRole('radio', { name: /python for a manual run/i }))

      // The third refusal the walk measured was a `path` variable the SQL
      // placeholder implies exists; the handle is what the sandbox actually
      // hands the code, and it is named on the page before the first run.
      const contract = screen.getByRole('note')
      expect(contract).toHaveTextContent('dataset.rows')
      expect(contract).toHaveTextContent('dataset.columns')
      expect(contract).toHaveTextContent('dataset.query')
      expect(contract).toHaveTextContent('no path variable')
    })

    it('answers each of the three refusals the walk measured', async () => {
      const user = userEvent.setup()
      render(
        <RunCodePanel
          caseId={CASE_ID}
          datasetId={DATASET_ID}
          datasetName={DATASET_NAME}
          onChanged={() => {}}
        />,
      )
      await user.click(screen.getByRole('radio', { name: /python for a manual run/i }))

      const contract = screen.getByRole('note')
      // import pandas -> the stdlib subset is the answer, and statistics is
      // named as the alternative a sum or a mean actually needs.
      expect(contract).toHaveTextContent(/pandas, csv and numpy are refused/i)
      expect(contract).toHaveTextContent(/statistics covers a mean or a sum/i)
      // import csv -> the same sentence names it, so the second refusal is
      // not a second mystery.
      expect(contract).toHaveTextContent(/\bcsv\b/)
      // `result` -> the shape a run takes, which is what the 400 for a
      // missing `result` was asking for.
      expect(contract).toHaveTextContent(/leave the answer in result/i)
      expect(contract).toHaveTextContent('dataset.rows')
    })

    it('lists every module the import wall admits, and no others', async () => {
      // The panel's list and the sandbox's `_SAFE_MODULES` are two copies of
      // one security decision, and a module that moves on one side and not
      // the other is either a door the page claims and the wall refuses, or a
      // door the wall admits and the page forgets to name. This reads the
      // wall's own frozenset and compares the sets, so the drift is a named
      // failure rather than a slow disagreement.
      const source = pythonExec as string
      const wall = /_SAFE_MODULES\s*=\s*frozenset\(\s*{([^}]*)}/s.exec(source)
      expect(wall, 'the sandbox\'s _SAFE_MODULES frozenset moved').not.toBeNull()
      const allowed = (wall![1].match(/"([a-z_]+)"/g) ?? [])
        .map((quoted) => quoted.slice(1, -1))
        .sort()
      expect(PYTHON_ALLOWED_MODULES.slice().sort()).toEqual(allowed)
    })

    it('shows the shape a run takes before the analyst writes anything', async () => {
      const user = userEvent.setup()
      render(
        <RunCodePanel
          caseId={CASE_ID}
          datasetId={DATASET_ID}
          datasetName={DATASET_NAME}
          columns={['region', 'revenue']}
          onChanged={() => {}}
        />,
      )
      await user.click(screen.getByRole('radio', { name: /python for a manual run/i }))

      const editor = screen.getByLabelText(/python to run/i) as HTMLTextAreaElement
      // The placeholder is the canonical use the core's own tests write: read
      // the handle, accumulate, leave the table in `result`. An analyst who
      // runs it as it stands gets a run, not a refusal.
      expect(editor.placeholder).toMatch(/for row in dataset\.rows/)
      expect(editor.placeholder).toMatch(/result = /)
      // The contract's one-line example points at a column the dataset has,
      // so the first line an analyst copies names something real.
      expect(screen.getByRole('note')).toHaveTextContent("'region'")
    })

    it('answers in generic terms for an unprofiled dataset', async () => {
      const user = userEvent.setup()
      render(
        <RunCodePanel
          caseId={CASE_ID}
          datasetId={DATASET_ID}
          datasetName={DATASET_NAME}
          onChanged={() => {}}
        />,
      )
      await user.click(screen.getByRole('radio', { name: /python for a manual run/i }))

      const editor = screen.getByLabelText(/python to run/i) as HTMLTextAreaElement
      expect(editor.placeholder).toMatch(/for row in dataset\.rows/)
      // No columns were named, so the example still reads as an example and
      // never as a claim about the file.
      expect(editor.placeholder).toMatch(/'region'/)
    })

    it('hides the contract on SQL, which has its own', async () => {
      const user = userEvent.setup()
      render(
        <RunCodePanel
          caseId={CASE_ID}
          datasetId={DATASET_ID}
          datasetName={DATASET_NAME}
          columns={['region', 'revenue']}
          onChanged={() => {}}
        />,
      )

      expect(screen.queryByRole('note')).toBeNull()
      const editor = screen.getByLabelText(/sql to run/i) as HTMLTextAreaElement
      // SQL's contract is the file itself, and `read_csv_auto(?)` is the
      // door; the placeholder carries it, the way the codegen panel's does.
      expect(editor.placeholder).toMatch(/read_csv_auto\(\?\)/)

      // Switching to Python puts the contract on the page and changes the
      // placeholder to the handle's shape - the two engines' contracts are
      // not one paragraph applied to both.
      await user.click(screen.getByRole('radio', { name: /python for a manual run/i }))
      expect(screen.getByRole('note')).toBeInTheDocument()
      expect(
        (screen.getByLabelText(/python to run/i) as HTMLTextAreaElement).placeholder,
      ).toMatch(/dataset\.rows/)

      // Switching back takes it off again, so the SQL surface is not left
      // carrying the Python engine's contract.
      await user.click(screen.getByRole('radio', { name: /sql for a manual run/i }))
      expect(screen.queryByRole('note')).toBeNull()
    })
  })
})
