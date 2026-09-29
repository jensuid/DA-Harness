/**
 * W2X-007: the capability the core has always had, given a surface of its own.
 *
 * The stage guidance says "Run an analysis", but the only doors into `/runs`
 * were the non-editable codegen and the EDA presets. The core's own engine
 * - arbitrary SQL or Python against the attached dataset - had no way in.
 * This is that way in: a textarea, the engine the code is for, and the run
 * endpoints the codegen panel already posts to.
 *
 * W2X-006's editor lives in GeneratePanel for the loop it serves; this one is
 * the analyst's own code from nothing. They share the wire, not the surface.
 *
 * W3X-004: the Python engine is the one a Python-fluent analyst reaches for
 * first, and its first three interactions used to be three refusals whose
 * answers were not on the page - `import pandas`, `import csv`, and the
 * `path` variable the SQL surface's own placeholder implies exists. The
 * sandbox is right to refuse, so the fix is not the wall but the sign on it:
 * the panel shows the contract before the first run. `dataset.rows` is the
 * handle, the module allowlist is the importable set, and the example is the
 * shape a run takes. The SQL engine needs none of it - `read_csv_auto(?)` is
 * its own contract, and its placeholder carries it.
 */

import { useState } from 'react'
import {
  runPython,
  runSql,
} from '../api'
import { messageOf } from '../CaseList'
import { Button, surfaces } from '../lib/ui'

type RunKind = 'sql' | 'python'
export const RUN_KINDS: RunKind[] = ['sql', 'python']
export const RUN_KIND_LABELS: Record<RunKind, string> = {
  sql: 'SQL',
  python: 'Python',
}

// The module allowlist the sandbox's import wall admits (`_SAFE_MODULES` in
// server/app/python_exec.py). Everything else - pandas, csv, numpy, os,
// subprocess - is refused, and the refusal is the security property. The two
// lists are the same set by hand: the sandbox publishes no endpoint for its
// allowlist, and a panel that fetched one would be a second source of truth
// for a list that changes with the security review, not with the UI. The
// drift test in RunCodePanel.test keeps the two honest.
export const PYTHON_ALLOWED_MODULES: readonly string[] = [
  'math', 'statistics', 'json', 're', 'collections', 'itertools',
  'functools', 'operator', 'string', 'unicodedata', 'datetime',
  'decimal', 'fractions', 'html', 'textwrap', 'openpyxl', 'pyarrow',
]

// The three refusals the walk-test measured, and the answer to each. Naming
// the alternative is what makes a refusal teach: `statistics` is the stdlib's
// own pandas for the sum and the mean the analyst was reaching for.
const PYTHON_CONTRACT = [
  'Read the dataset through the handle, not a file path: dataset.rows is the ' +
    'table as a list of dicts, dataset.columns its names, and ' +
    'dataset.query(sql) a read-only SQL query. There is no path variable and ' +
    'no open().',
  'Only these modules import: ' +
    PYTHON_ALLOWED_MODULES.slice(0, -1).join(', ') +
    ` and ${PYTHON_ALLOWED_MODULES[PYTHON_ALLOWED_MODULES.length - 1]}. ` +
    'pandas, csv and numpy are refused - statistics covers a mean or a sum.',
  'Leave the answer in result as a list of dicts and it becomes the run\'s ' +
    'columns and rows, the same shape a SQL run produces.',
] as const

// The shape a run takes, as the placeholder the empty editor shows: read the
// handle, accumulate, leave the table in `result`. This is the canonical use
// the core's own tests write (server/tests/test_python_runs.py).
const PYTHON_EXAMPLE = [
  "totals = {}",
  "for row in dataset.rows:",
  "    totals[row['region']] = totals.get(row['region'], 0) + row['revenue']",
  "result = [{'region': k, 'total': v} for k, v in sorted(totals.items())]",
].join('\n')

export function RunCodePanel({
  caseId,
  datasetId,
  datasetName,
  columns,
  onChanged,
}: {
  caseId: string
  datasetId: string
  datasetName: string
  /** The profiled column names, so the contract's one-line example points at
   * columns the dataset actually has. Unprofiled datasets answer in generic
   * terms rather than inventing a name. */
  columns?: string[]
  onChanged: () => void
}) {
  const [kind, setKind] = useState<RunKind>('sql')
  const [code, setCode] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(event: React.FormEvent) {
    event.preventDefault()
    const text = code.trim()
    if (!text || running) return
    setRunning(true)
    setError(null)
    try {
      if (kind === 'python') {
        await runPython(caseId, datasetId, code)
      } else {
        await runSql(caseId, datasetId, code)
      }
      // The run persisted before this line, so the runs panel and the rail
      // read the case again and pick it up now (W-013).
      onChanged()
      setCode('')
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setRunning(false)
    }
  }

  // A column the dataset really has, or the generic term the codegen panel's
  // own placeholder uses. The SQL example groups by it and the Python example
  // names it, so the first thing an unprofiled dataset shows is still valid.
  const key = columns && columns.length > 0 ? columns[0] : 'region'

  return (
    <div className={surfaces.subpanel}>
      <h3 className={surfaces.subheading}>Run code on {datasetName}</h3>
      <fieldset>
        <legend className={surfaces.note}>Engine</legend>
        {RUN_KINDS.map((option) => (
          <label key={option}>
            <input
              type="radio"
              name="run-kind"
              aria-label={`${RUN_KIND_LABELS[option]} for a manual run`}
              value={option}
              checked={kind === option}
              onChange={() => setKind(option)}
              disabled={running}
            />{' '}
            {RUN_KIND_LABELS[option]}
          </label>
        ))}
      </fieldset>
      {kind === 'python' && (
        <div className="engine-contract" role="note">
          <p className={surfaces.note}>{PYTHON_CONTRACT[0]}</p>
          <p className={surfaces.note}>{PYTHON_CONTRACT[1]}</p>
          <p className={surfaces.note}>
            {PYTHON_CONTRACT[2]}{' '}
            <code>
              {`result = [{'${key}': row['${key}']} for row in dataset.rows]`}
            </code>
          </p>
        </div>
      )}
      <form onSubmit={run}>
        <textarea
          aria-label={`${RUN_KIND_LABELS[kind]} to run`}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          placeholder={
            kind === 'sql'
              ? `SELECT ${key}, COUNT(*) FROM read_csv_auto(?) GROUP BY ${key}`
              : PYTHON_EXAMPLE
          }
          disabled={running}
        />
        <Button type="submit" disabled={running || !code.trim()}>
          {running ? 'Running…' : 'Run'}
        </Button>
      </form>
      {error && <p role="alert">{`Run failed: ${error}`}</p>}
    </div>
  )
}
