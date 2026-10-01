/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useId, useState } from 'react'
import {
  type Dataset,
  type EdaOp,
  type EdaRequest,
  type EdaResult,
  type Profile,
  runEda,
} from "../api"
import { messageOf } from '../CaseList'
import { Button, Skeleton, surfaces } from '../lib/ui'
import { formatValue } from './RunsPanel'

export function EdaPanel({
  caseId,
  datasets,
  profiles,
  loading,
}: {
  caseId: string
  datasets: Dataset[]
  profiles: Record<string, Profile>
  loading: boolean
}) {
  const profiled = datasets.filter((d) => profiles[d.id] !== undefined)
  const headingId = useId()
  const [chosen, setChosen] = useState('')
  const [op, setOp] = useState<EdaOp>('distribution')
  // The picks are advisory: an effective value is resolved against the current
  // dataset's columns, so a stale pick from another dataset or another op can
  // never be submitted.
  const [by, setBy] = useState('')
  const [measure, setMeasure] = useState('')
  const [x, setX] = useState('')
  const [y, setY] = useState('')
  const [column, setColumn] = useState('')
  const [result, setResult] = useState<EdaResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (loading) {
    // SKEL: the profiles land last in the workspace's read, so "profile a
    // dataset first" would be guidance about a case the shell is still
    // reading. The shape is the op's own form.
    return (
      <section
        className={surfaces.panel}
        aria-labelledby={headingId}
      >
        <h2 className={surfaces.heading} id={headingId}>Explore the data (EDA)</h2>
        <p className={surfaces.note + ' visually-hidden'}>Reading the profiles…</p>
        <Skeleton shape="form" />
      </section>
    )
  }
  if (profiled.length === 0) {
    return (
      <section
        className={surfaces.panel}
        aria-labelledby={headingId}
      >
        <h2 className={surfaces.heading} id={headingId}>Explore the data (EDA)</h2>
        <p className={surfaces.note}>
          Profile a dataset first - the ops read its columns and their types.
        </p>
      </section>
    )
  }

  const dataset = profiled.find((d) => d.id === chosen) ?? profiled[0]
  const profile = profiles[dataset.id]
  const columns = profile.columns
  // A measure or a correlation axis is only meaningful over a numeric column,
  // so numerics are what those pickers offer when the dataset has any. A
  // dataset without one still offers every column, and the core's 400 is the
  // honest answer to the wrong choice.
  const numerics = columns.filter((c) => typeOf(profile, c) === 'numeric')
  const measurable = numerics.length > 0 ? numerics : columns

  const pick = (value: string, options: string[]) =>
    options.includes(value) ? value : options[0]

  const request: EdaRequest = { op }
  if (op === 'segment') {
    request.by = pick(by, columns)
    request.measure = pick(measure, measurable)
  } else if (op === 'correlate') {
    request.x = pick(x, measurable)
    request.y = pick(y, measurable)
  } else {
    request.column = pick(column, columns)
  }

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      setResult(await runEda(caseId, dataset.id, request))
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <section
      className={surfaces.panel}
      aria-labelledby={headingId}
    >
      <h2 className={surfaces.heading} id={headingId}>Explore the data (EDA)</h2>
      <p className={surfaces.note}>
        Segment a measure by a category, correlate two columns, or read a
        column's distribution. Each runs read-only like any query, and none is
        kept - an EDA result is exploration, not a finding.
      </p>
      {profiled.length > 1 && (
        <label>
          Explore
          <select
            aria-label="Dataset to explore"
            value={dataset.id}
            onChange={(e) => {
              setChosen(e.target.value)
              setResult(null)
              setError(null)
            }}
          >
            {profiled.map((d) => (
              <option key={d.id} value={d.id}>
                {d.filename}
              </option>
            ))}
          </select>
        </label>
      )}
      <form onSubmit={submit}>
        <label>
          What to look at
          <select
            aria-label="Exploratory operation"
            value={op}
            onChange={(e) => {
              setOp(e.target.value as EdaOp)
              // A result from another op answers a question this one does not
              // ask, so it leaves with the picker that produced it.
              setResult(null)
              setError(null)
            }}
          >
            <option value="distribution">
              Distribution — a column's spread, or its most common values
            </option>
            <option value="segment">
              Segment — group a measure's stats by a category
            </option>
            <option value="correlate">
              Correlate — Pearson r between two numeric columns
            </option>
          </select>
        </label>
        {op === 'segment' && (
          <div className={surfaces.rowGap}>
            <label>
              Group by
              <select
                aria-label="Column to group by"
                value={request.by}
                onChange={(e) => setBy(e.target.value)}
                disabled={busy}
              >
                {columns.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Measure
              <select
                aria-label="Measure to summarise"
                value={request.measure}
                onChange={(e) => setMeasure(e.target.value)}
                disabled={busy}
              >
                {measurable.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {op === 'correlate' && (
          <div className={surfaces.rowGap}>
            <label>
              X
              <select
                aria-label="X column"
                value={request.x}
                onChange={(e) => setX(e.target.value)}
                disabled={busy}
              >
                {measurable.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Y
              <select
                aria-label="Y column"
                value={request.y}
                onChange={(e) => setY(e.target.value)}
                disabled={busy}
              >
                {measurable.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </label>
          </div>
        )}
        {op === 'distribution' && (
          <label>
            Column
            <select
              aria-label="Column to describe"
              value={request.column}
              onChange={(e) => setColumn(e.target.value)}
              disabled={busy}
            >
              {columns.map((c) => (
                <option key={c} value={c}>
                  {c}
                  {typeOf(profile, c) === 'numeric' ? ' (numeric)' : ''}
                </option>
              ))}
            </select>
          </label>
        )}
        <Button type="submit" disabled={busy}>
          {busy ? 'Running…' : 'Run the op'}
        </Button>
      </form>
      {error && <p role="alert">The op could not run: {error}</p>}
      {result && <EdaResultTable result={result} />}
    </section>
  )
}

// The profile's per-column type family, or '' when the column has no recorded
// stat. It decides which summary a distribution yields and which columns a
// measure may honestly be taken over.
export function typeOf(profile: Profile, column: string): string {
  const stats = (profile.stats ?? {}) as Record<string, { type?: string }>
  return stats[column]?.type ?? ''
}

// The columns the core returned are the table; a distribution over a numeric
// column has seven of them and over a category two, and the panel does not
// assume which.
export function EdaResultTable({ result }: { result: EdaResult }) {
  return (
    <div className={surfaces.proposal} data-testid="eda-result">
      <p className={surfaces.note}>
        {result.row_count} row{result.row_count === 1 ? '' : 's'}
        {result.truncated && ' (truncated)'} — exploration, not evidence: run
        the equivalent query to make a finding of it.
      </p>
      <table className="eda">
        <thead>
          <tr>
            {result.columns.map((column) => (
              <th key={column}>{column}</th>
            ))}
          </tr>
        </thead>
        <tbody>
          {result.rows.map((row, i) => (
            <tr key={i}>
              {row.map((value, j) => (
                <td key={j}>{formatValue(value)}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

// Four decimals is as precise as an average or a coefficient needs to be read;
// the full float is noise on the page and the stored value is untouched.
