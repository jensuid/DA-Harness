/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useEffect, useState } from 'react'
import {
  type ChartImage,
  type ChartKind,
  type ChartSummary,
  type Chart,
  type Dataset,
  type DraftFinding,
  type Interpretation,
  type Run,
  type RunSummary,
  createChart,
  draftFinding,
  getChart,
  getChartImage,
  getRun,
  interpretRun,
  listCharts,
} from "../api"
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'
import { Button, Skeleton, surfaces } from '../lib/ui'
import { CallProgress, useCallProgress } from '../lib/progress'
import { MotionSurface } from '../lib/motion'
import { ChartSurface } from '../lib/chart'
import { DraftPanel } from './DraftPanel'

export function RunsPanel({
  caseId,
  runs,
  datasets,
  onChanged,
  loading,
}: {
  caseId: string
  runs: RunSummary[]
  datasets: Dataset[]
  loading: boolean
  onChanged: () => void
}) {
  if (loading) {
    // SKEL: the workspace's read is in flight, so "no analysis has run yet"
    // would describe a case the shell has not read. The shape is the run
    // rows the panel renders once a run exists.
    return (
      <div className={surfaces.panel}>
        <h2 className={surfaces.heading}>Runs</h2>
        <p className={surfaces.note + ' visually-hidden'}>Reading the runs…</p>
        <Skeleton shape="rows" count={Math.max(runs.length, 3)} />
      </div>
    )
  }
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
  // W2X-001: the run's three actions are three separate requests, so a shared
  // "busy" meant every button read "Working…" for whichever one was in flight
  // - the walk saw three at once, and a slow LLM-backed interpret made the
  // rows toggle read the same thing as the call it was not making. Each action
  // owns its own flag, and each slow one owns its own elapsed row.
  const [busy, setBusy] = useState<'' | 'rows' | 'read' | 'draft'>('')
  const progress = useCallProgress()
  const [error, setError] = useState<string | null>(null)
  // W2X-003: a run whose chart the core already holds opens with its rows
  // already read. The chart sits below the rows table, so the drawing the
  // analyst left behind stays invisible until the rows are shown - and the
  // walk found exactly that, a case that had one chart by the evidence graph
  // and none on screen. The rows the chart needs are the same rows the table
  // shows, so this is the read "Show the rows" makes, only automatic.
  const [hasChart, setHasChart] = useState<ChartSummary | null>(null)
  // W2X-003: the chart the core already holds, read back so the case opens
  // with the drawing it closed with. Handed down to the chart panel, which
  // would otherwise only ever show a chart it rendered in this session.
  const [restored, setRestored] = useState<{ chart: Chart; image: ChartImage } | null>(null)

  useEffect(() => {
    let cancelled = false
    void (async () => {
      try {
        const charts = await listCharts(caseId, run.id)
        if (cancelled || charts.length === 0) return
        setHasChart(charts[0])
        // W2X-003: the chart the analyst left behind. The image endpoint sniffs
        // its format from the bytes the core stored, so the metadata is read
        // first - the restore cannot guess inline-SVG from a bitmap link, and
        // the pickers open on the axes the stored chart used.
        const stored = await getChart(caseId, charts[0].id)
        if (cancelled) return
        const img = await getChartImage(caseId, stored)
        if (cancelled) return
        setRestored({ chart: stored, image: img })
      } catch {
        // A chart whose image is gone from disk is still a chart the case has:
        // the rows open so the control is where it always was, and the analyst
        // can render it again. The restore does not report this as a failure.
      }
    })()
    return () => {
      cancelled = true
    }
  }, [caseId, run.id])

  useEffect(() => {
    if (!hasChart || rows || busy) return
    void showRows()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hasChart])

  async function showRows() {
    if (busy) return
    setBusy('rows')
    setError(null)
    try {
      setRows(await getRun(caseId, run.id))
      setReading(null)
      setDraft(null)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy('')
    }
  }

  async function read() {
    if (busy) return
    setBusy('read')
    setError(null)
    const signal = progress.start()
    try {
      setReading(await interpretRun(caseId, run.id, signal))
      setDraft(null)
    } catch (err) {
      // A cancel is the analyst's stop, and the reading simply did not happen -
      // reported as a sentence rather than as an assistant that failed.
      setError(
        err instanceof DOMException && err.name === 'AbortError'
          ? 'Cancelled - no interpretation was made.'
          : messageOf(err),
      )
    } finally {
      progress.done()
      setBusy('')
    }
  }

  async function draftIt() {
    if (busy) return
    setBusy('draft')
    setError(null)
    const signal = progress.start()
    try {
      setDraft(await draftFinding(caseId, run.id, signal))
      setReading(null)
    } catch (err) {
      setError(
        err instanceof DOMException && err.name === 'AbortError'
          ? 'Cancelled - no draft was made.'
          : messageOf(err),
      )
    } finally {
      progress.done()
      setBusy('')
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
        <Button type="button" onClick={read} disabled={busy !== ''} variant="small">
          {busy === 'read' ? 'Working…' : 'Interpret'}
        </Button>
        <Button type="button" onClick={draftIt} disabled={busy !== ''} variant="small">
          {busy === 'draft' ? 'Working…' : 'Draft a finding'}
        </Button>
        <Button
          type="button"
          onClick={() => (rows ? setRows(null) : void showRows())}
          disabled={busy !== ''}
          variant="small"
          aria-expanded={rows !== null}
        >
          {busy === 'rows' ? 'Working…' : rows ? 'Hide the rows' : 'Show the rows'}
        </Button>
      </div>
      <CallProgress
        kind={busy === 'draft' ? 'draft finding' : 'interpretation'}
        elapsed={progress.elapsed}
        active={progress.active}
        onCancel={progress.cancel}
      />
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
      <ChartPanel
        caseId={caseId}
        run={run}
        rows={rows}
        restored={restored}
        onChanged={onChanged}
      />
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
  restored,
  onChanged,
}: {
  caseId: string
  run: RunSummary
  rows: Run | null
  // W2X-003: a chart the case held before it was closed, read back by the row
  // above and handed down. The panel would otherwise only ever show a chart it
  // rendered in this session.
  restored: { chart: Chart; image: ChartImage } | null
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

  // W2X-003: the chart this case already has is the one to draw, so the
  // restored pair wins over an empty local state and falls behind a chart the
  // analyst rendered here - a new render is the analyst's latest answer.
  const shownChart = chart ?? restored?.chart ?? null
  const shownImage = image ?? restored?.image ?? null

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
      {shownImage && shownChart && rows && (
        // The surface reads the run's own result, so the on-screen chart and
        // the stored artifact answer the same question from the same numbers;
        // the chart's metadata carries the axes the analyst picked.
        <ChartSurface
          kind={shownChart.kind as ChartKind}
          run={rows}
          x={shownChart.x}
          y={shownChart.y}
          series={shownChart.series}
          title={shownChart.title}
          image={shownImage}
        />
      )}
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

// The drawn chart: on screen it is recharts drawing the same stored result
// the core drew its artifact from (P9-F4-001), because a static image cannot
// answer "what is this point"; the artifact the case holds is still the
// core's own SVG, and a chart with nothing plottable falls back to it. A PNG
// chart is the core's bitmap, so it stays the link it always was.
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
