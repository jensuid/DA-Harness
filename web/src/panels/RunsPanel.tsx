/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useState } from 'react'
import {
  type ChartImage,
  type ChartKind,
  type ChartSummary,
  type Dataset,
  type DraftFinding,
  type Interpretation,
  type Run,
  type RunSummary,
  createChart,
  draftFinding,
  getChartImage,
  getRun,
  interpretRun,
} from "../api"
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'
import { Button, surfaces } from '../lib/ui'
import { MotionSurface } from '../lib/motion'
import { DraftPanel } from './DraftPanel'

export function RunsPanel({
  caseId,
  runs,
  datasets,
  onChanged,
}: {
  caseId: string
  runs: RunSummary[]
  datasets: Dataset[]
  onChanged: () => void
}) {
  if (runs.length === 0) {
    return (
      <div className={surfaces.panel}>
        <h2 className={surfaces.heading}>Runs</h2>
        <p className={surfaces.note}>No analysis has run yet.</p>
      </div>
    )
  }
  return (
    <div className={surfaces.panel}>
      <h2 className={surfaces.heading}>Runs</h2>
      <ul className={surfaces.panelList}>
        {runs.map((run) => (
          <li key={run.id}>
            <RunRow
              caseId={caseId}
              run={run}
              datasetLabel={datasets.find((d) => d.id === run.dataset_id)?.filename ?? 'data'}
              onChanged={onChanged}
            />
          </li>
        ))}
      </ul>
    </div>
  )
}

export function RunRow({
  caseId,
  run,
  datasetLabel,
  onChanged,
}: {
  caseId: string
  run: RunSummary
  datasetLabel: string
  onChanged: () => void
}) {
  const [reading, setReading] = useState<Interpretation | null>(null)
  const [draft, setDraft] = useState<DraftFinding | null>(null)
  // A run's own rows, reopened on demand: the summary says a run exists, the
  // rows are what a finding rests on, and AT-34 asks a reader to trace a claim
  // back to them without leaving the workspace.
  const [rows, setRows] = useState<Run | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function showRows() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      setRows(await getRun(caseId, run.id))
      setReading(null)
      setDraft(null)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function read() {
    setBusy(true)
    setError(null)
    try {
      setReading(await interpretRun(caseId, run.id))
      setDraft(null)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function draftIt() {
    setBusy(true)
    setError(null)
    try {
      setDraft(await draftFinding(caseId, run.id))
      setReading(null)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <MotionSurface variant="open" className={surfaces.row}>
      <p>
        <strong>{run.kind}</strong> over {datasetLabel} — {run.row_count} row
        {run.row_count === 1 ? '' : 's'}
        {run.truncated && ' (truncated)'}
      </p>
      <div className={surfaces.buttonRow}>
        <Button type="button" onClick={read} disabled={busy} variant="small">
          {busy ? 'Working…' : 'Interpret'}
        </Button>
        <Button type="button" onClick={draftIt} disabled={busy} variant="small">
          {busy ? 'Working…' : 'Draft a finding'}
        </Button>
        <Button
          type="button"
          onClick={() => (rows ? setRows(null) : void showRows())}
          disabled={busy}
          variant="small"
          aria-expanded={rows !== null}
        >
          {busy ? 'Working…' : rows ? 'Hide the rows' : 'Show the rows'}
        </Button>
      </div>
      {error && <p role="alert">The assistant failed: {error}</p>}
      {reading && (
        <div className={surfaces.proposal}>
          <p className={surfaces.note}>{sourceLabel(reading.source, 'interpretation')}</p>
          <p>{reading.summary}</p>
          {reading.observations.length > 0 && (
            <ul className={surfaces.panelList}>
              {reading.observations.map((observation, i) => (
                <li key={i}>{observation}</li>
              ))}
            </ul>
          )}
          {reading.caveats.length > 0 && (
            <ul className={surfaces.panelList}>
              {reading.caveats.map((caveat, i) => (
                <li key={i} className={surfaces.note}>
                  caveat: {caveat}
                </li>
              ))}
            </ul>
          )}
        </div>
      )}
      {draft && (
        <DraftPanel
          caseId={caseId}
          runId={run.id}
          draft={draft}
          onAccepted={() => {
            setDraft(null)
            onChanged()
          }}
        />
      )}
      {rows && <RunRowsTable run={rows} />}
      <ChartPanel caseId={caseId} run={run} rows={rows} onChanged={onChanged} />
    </MotionSurface>
  )
}

// A chart is evidence the core draws from a run's stored result, and until
// this panel the shell could only reach one by its file path. The control
// asks for one (W-016): pickers offer the columns the run produced - the
// renderer validates against that result, so the offer cannot name a column
// the chart cannot have - and the surface shows what came back, inline for
// the SVG the core already drew and as a link for a bitmap.
//
// The pickers are advisory the way EDA's are: an effective value resolves
// against the run's own columns, so a pick from another run can never be
// submitted, and a measure defaults to a numeric column when there is one.
export function ChartPanel({
  caseId,
  run,
  rows,
  onChanged,
}: {
  caseId: string
  run: RunSummary
  rows: Run | null
  onChanged: () => void
}) {
  const [open, setOpen] = useState(false)
  const [kind, setKind] = useState<ChartKind>('bar')
  const [x, setX] = useState('')
  const [y, setY] = useState('')
  const [series, setSeries] = useState('')
  const [chart, setChart] = useState<ChartSummary | null>(null)
  const [image, setImage] = useState<ChartImage | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canOffer = rows !== null && rows.columns.length > 0

  async function render() {
    if (!rows || busy) return
    setBusy(true)
    setError(null)
    try {
      const created = await createChart(caseId, run.id, {
        kind,
        x: pickOf(x, rows.columns),
        y: pickOf(y, measureChoices(rows)),
        series: series ? pickOf(series, rows.columns) : null,
        format: 'svg',
      })
      setChart(created)
      // The SVG the response's image endpoint carries is what the shell draws;
      // a bitmap would be a second renderer, so it is a link to the artifact.
      setImage(await getChartImage(caseId, created))
      // A chart moves the evidence graph's count, so the case is re-read and
      // the rail moves with the panel rather than waiting for a remount.
      onChanged()
    } catch (err) {
      setChart(null)
      setImage(null)
      // The renderer's refusal is the analyst's input: its detail names the
      // column, the kind or the measure that is not drawable, and the panel
      // shows that sentence rather than reading as a fault in itself.
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  if (!canOffer) {
    return null
  }

  const columns = rows.columns
  const measures = measureChoices(rows)
  const xValue = pickOf(x, columns)
  const yValue = pickOf(y, measures)

  return (
    <div className={surfaces.subpanel}>
      <div className={surfaces.buttonRow}>
        <Button
          type="button"
          onClick={() => setOpen((prior) => !prior)}
          aria-expanded={open}
          disabled={busy}
          variant="small"
        >
          {open ? 'Hide the chart controls' : 'Render a chart'}
        </Button>
      </div>
      {open && (
        <form
          onSubmit={(event) => {
            event.preventDefault()
            void render()
          }}
        >
          <div className={surfaces.rowGap}>
            <label>
              Kind
              <select
                aria-label="Chart kind"
                value={kind}
                onChange={(e) => setKind(e.target.value as ChartKind)}
                disabled={busy}
              >
                <option value="bar">Bar — length reads as magnitude</option>
                <option value="line">Line — a series over the axis</option>
              </select>
            </label>
            <label>
              X axis
              <select
                aria-label="Column for the x axis"
                value={xValue}
                onChange={(e) => setX(e.target.value)}
                disabled={busy}
              >
                {columns.map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Y axis
              <select
                aria-label="Column for the y axis"
                value={yValue}
                onChange={(e) => setY(e.target.value)}
                disabled={busy}
              >
                {measures.map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
              </select>
            </label>
            <label>
              Series
              <select
                aria-label="Column to split into series"
                value={series ? pickOf(series, columns) : ''}
                onChange={(e) => setSeries(e.target.value)}
                disabled={busy}
              >
                <option value="">none — one series</option>
                {columns.map((column) => (
                  <option key={column} value={column}>
                    {column}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <Button type="submit" disabled={busy}>
            {busy ? 'Rendering…' : 'Render the chart'}
          </Button>
        </form>
      )}
      {error && (
        <p role="alert">The chart could not be rendered: {error}</p>
      )}
      {image && <ChartSurface chart={chart} image={image} />}
    </div>
  )
}

// A measure is only meaningful over a numeric column, so numerics are what the
// y picker offers when the run has any. A result without one still offers
// every column, and the renderer's 400 is the honest answer to a column whose
// values are not plottable.
export function measureChoices(run: Run): string[] {
  const columns = run.columns
  const numerics = columns.filter((column) =>
    run.rows.some(
      (row) => typeof row[columns.indexOf(column)] === 'number',
    ),
  )
  return numerics.length > 0 ? numerics : columns
}

// An effective pick resolves against the choices, so a stale pick from another
// run can never be submitted.
export function pickOf(value: string, choices: string[]): string {
  return choices.includes(value) ? value : (choices[0] ?? '')
}

// The drawn chart: the core's own SVG inline, because an <img> over it would
// be the shell drawing a second time from a renderer it does not have; or a
// link to the persisted bitmap, which is the artifact the core wrote.
export function ChartSurface({
  chart,
  image,
}: {
  chart: ChartSummary | null
  image: ChartImage
}) {
  const label = chart ? chartLabel(chart) : 'the chart'
  if (image.format === 'svg') {
    return (
      <MotionSurface
        variant="arrive"
        className={surfaces.proposal}
        data-testid="chart-surface"
      >
        <p className={surfaces.note}>
          {label} — drawn by the core from the run's stored result
        </p>
        <div
          className="chart"
          data-testid="chart-svg"
          // The SVG is the core's own output, rendered from the same stored
          // result the finding rests on; the shell draws it as-is rather than
          // re-deriving the geometry.
          dangerouslySetInnerHTML={{ __html: image.svg }}
        />
      </MotionSurface>
    )
  }
  return (
    <MotionSurface
      variant="arrive"
      className={surfaces.proposal}
      data-testid="chart-surface"
    >
      <p className={surfaces.note}>{label}</p>
      <p>
        <a href={image.url}>Open the rendered chart</a>
      </p>
    </MotionSurface>
  )
}

export function chartLabel(chart: ChartSummary): string {
  const title = chart.title.trim()
  return title
    ? `${title} (${chart.kind}: ${chart.y} by ${chart.x})`
    : `${chart.kind} chart of ${chart.y} by ${chart.x}`
}

// A run's result, as the table it always was on the wire: the core persisted
// the columns and the rows, so the finding a run supports can be checked
// against the numbers it quotes without re-running anything. The query that
// produced them sits above the table, because a claim is judged by what it
// computed and not only by what came back.
export function RunRowsTable({ run }: { run: Run }) {
  const query = run.sql ?? run.code
  return (
    <MotionSurface variant="open" className={surfaces.proposal} data-testid="run-rows">
      {query && <pre>{query}</pre>}
      {run.rows.length === 0 ? (
        <p className={surfaces.note}>The run produced no rows.</p>
      ) : (
        <table className="eda">
          <thead>
            <tr>
              {run.columns.map((column) => (
                <th key={column}>{column}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {run.rows.map((row, i) => (
              <tr key={i}>
                {row.map((value, j) => (
                  <td key={j}>{formatValue(value)}</td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      )}
      {run.truncated && (
        <p className={surfaces.note}>
          The result was capped at the row limit; the stored count is{' '}
          {run.row_count}.
        </p>
      )}
    </MotionSurface>
  )
}

// A draft proposes a finding and creates nothing. Accept posts the statement
// to the findings endpoint - the only path that writes one - so the analyst,
// not the assistant, decides what becomes evidence.

export function formatValue(value: unknown): string {
  if (typeof value === 'number') {
    return String(Number(value.toFixed(4)))
  }
  if (value === null || value === undefined) {
    return ''
  }
  return String(value)
}

// EVALUATE mode: audit work that came from elsewhere (P7-SHELL-002). The
// ANALYZE loop above serves the analyst's own work; this panel points the same
// primitives at someone else's. The user pastes the artifact's code and the
// claim it was offered to support, and reads nine verdicts, each a sentence
// rather than a code.
//
// Every other panel's discipline applies unchanged: the submit posts to the
// evaluate endpoint and nothing else, and the endpoint - not the panel - runs
// the code under the read-only gate, the row cap and the hard sandbox. The
// panel never decides whether work is sound; it renders what the core found.
