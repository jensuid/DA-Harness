/**
 * P9-F4-001: the on-screen chart.
 *
 * The core (`server/app/charts.py`) renders the chart the case *holds*: the
 * persisted SVG, the PNG, the exported package, the evidence. This module
 * renders the chart the analyst *looks at*, from the same stored result, and
 * the difference is deliberate - a static image cannot answer "what is this
 * point", and a trust chain cannot be an interactive widget. So the artifact
 * stays the core's, and the screen becomes recharts'.
 *
 * One geometry, two renderers. The series split, the plottable-points filter
 * and the palette are the core's own rules, copied here rather than
 * re-derived by recharts, so what the analyst sees and what the case holds
 * answer the same question the same way. `chartGeometry` is that copy, and a
 * divergence between it and `ChartModel` is a test that names it.
 */

import type { ReactElement } from 'react'
import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'
import type { ChartKind, Run } from '../api'
import { MotionSurface } from './motion'
import { surfaces } from './ui'

// The core's palette (`charts.py`'s `_PALETTE`), in the core's order: the
// on-screen chart and the stored SVG must agree on which series is which
// colour, or the legend is not the legend the artifact carries.
export const CHART_PALETTE = [
  '#2563eb',
  '#dc2626',
  '#059669',
  '#d97706',
  '#7c3aed',
  '#db2777',
] as const

// A category on the x axis, carrying one value per series that has a point
// there. This is the shape recharts takes; the single-series shape is one
// record per result row, which is the shape the core's `_series_of` builds
// its point list from.
export interface ChartPoint {
  [key: string]: string | number | null
}

export interface ChartGeometry {
  /** The x axis's categories, in the result's first-appearance order. */
  categories: string[]
  /** One series name per series, in the core's own order. */
  series: string[]
  /** One record per category (multi-series) or per row (single-series). */
  data: ChartPoint[]
  /** The series that carry at least one point, with their palette colour. */
  plotted: { name: string; color: string }[]
}

export function isNumeric(value: unknown): boolean {
  if (value === null || value === undefined || typeof value === 'boolean') {
    return false
  }
  if (typeof value === 'number') {
    return Number.isFinite(value)
  }
  return Number.isFinite(Number(String(value).trim()))
}

export function toNumber(value: unknown): number | null {
  if (!isNumeric(value)) return null
  return Number(String(value).trim())
}

export function labelOf(value: unknown): string {
  if (value === null || value === undefined) return ''
  if (typeof value === 'number' && Number.isInteger(value)) {
    return String(value)
  }
  return String(value)
}

/**
 * The transformation the core's `_series_of` performs, in the core's order.
 *
 * Without a series column there is one series named after the measure, and
 * one record per result row kept in row order - the core's own point list,
 * duplicated categories included, because a category the result had twice is
 * two points the core draws. With a series column, series keep
 * first-appearance order so the legend is stable and independent of the
 * engine's grouping order, and the categories are the axis. A point is kept
 * only when its measure is plottable, the way the core's `_numeric` filter
 * keeps it.
 */
export function chartGeometry(
  run: { columns: string[]; rows: unknown[][] },
  x: string,
  y: string,
  series: string | null,
): ChartGeometry {
  const indexOf = (column: string): number => run.columns.indexOf(column)

  if (series === null || series === '') {
    const data: ChartPoint[] = []
    const categories: string[] = []
    const xi = indexOf(x)
    const yi = indexOf(y)
    for (const row of run.rows) {
      const category = labelOf(row[xi])
      const record: ChartPoint = { [x]: category }
      const value = toNumber(row[yi])
      if (value !== null) {
        record[y] = value
      }
      data.push(record)
      if (!categories.includes(category)) {
        categories.push(category)
      }
    }
    return {
      categories,
      series: [y],
      data,
      plotted: [{ name: y, color: CHART_PALETTE[0] }],
    }
  }

  const xi = indexOf(x)
  const yi = indexOf(y)
  const si = indexOf(series)
  const order: string[] = []
  const bySeries = new Map<string, Map<string, number>>()
  const categories: string[] = []
  for (const row of run.rows) {
    const category = labelOf(row[xi])
    const name = labelOf(row[si])
    if (!categories.includes(category)) {
      categories.push(category)
    }
    if (!order.includes(name)) {
      order.push(name)
      bySeries.set(name, new Map())
    }
    const value = toNumber(row[yi])
    if (value !== null) {
      bySeries.get(name)!.set(category, value)
    }
  }

  const data: ChartPoint[] = categories.map(
    (category) => ({ [x]: category }) as ChartPoint,
  )
  for (const name of order) {
    const points = bySeries.get(name)!
    for (let i = 0; i < categories.length; i++) {
      const category = categories[i]
      if (points.has(category)) {
        data[i][name] = points.get(category) as number
      }
    }
  }

  return {
    categories,
    series: order,
    data,
    plotted: order.map((name, i) => ({
      name,
      color: CHART_PALETTE[i % CHART_PALETTE.length],
    })),
  }
}

/** A chart with nothing to plot is the core's image, not an empty tree. */
export function hasPlottablePoints(geometry: ChartGeometry): boolean {
  if (geometry.plotted.length === 0) return false
  if (geometry.data.length === 0) return false
  return geometry.data.some((record) =>
    geometry.plotted.some((series) => record[series.name] !== undefined),
  )
}

export interface ChartSurfaceProps {
  kind: ChartKind
  run: Run
  x: string
  y: string
  series: string | null
  title: string
  /**
   * The room the chart draws in. A browser's ResponsiveContainer measures its
   * parent; jsdom has no layout, so a percentage answers zero and recharts
   * renders a wrapper with no surface in it. The surface gives the tree a
   * real size and the container keeps its own minimum, so a browser uses the
   * width it has and the suite sees the same chart.
   */
  width?: number
  height?: number
}

/**
 * The recharts tree. The axes name themselves with the columns they plot, a
 * bar's y axis is anchored at zero because bar length reads as magnitude,
 * and the legend appears when there is more than one series - the same rules
 * the core's own SVG draws by.
 */
export function ChartTree({
  kind,
  run,
  x,
  y,
  series,
  title,
  width,
  height,
}: ChartSurfaceProps): ReactElement {
  const geometry = chartGeometry(run, x, y, series)
  const Chart = kind === 'line' ? LineChart : BarChart
  const crowded = geometry.categories.length > 6
  return (
    <Chart
      data={geometry.data}
      // recharts' ResponsiveContainer measures its parent; a percentage here
      // answers zero without a layout engine, and the tree renders nothing.
      width={width ?? '100%'}
      height={height ?? 300}
      margin={{ top: 16, right: 24, left: 8, bottom: 8 }}
      role="img"
      aria-label={title || `${kind} chart of ${y} by ${x}`}
    >
      <CartesianGrid strokeDasharray="3 3" />
      <XAxis
        dataKey={x}
        name={x}
        angle={crowded ? -35 : 0}
        textAnchor={crowded ? 'end' : 'middle'}
        interval={0}
        height={crowded ? 60 : 30}
      />
      <YAxis
        name={y}
        // A bar's length reads as magnitude, so its axis starts where the
        // core's own `anchor_at_zero` does; a line may start above zero to
        // use the plot area, the way the core's scale lets it.
        domain={kind === 'bar' ? [0, 'auto'] : ['auto', 'auto']}
      />
      <Tooltip />
      {geometry.plotted.length > 1 && <Legend />}
      {kind === 'line'
        ? geometry.plotted.map((entry) => (
            <Line
              key={entry.name}
              dataKey={entry.name}
              name={entry.name}
              stroke={entry.color}
              strokeWidth={2}
              dot={{ r: 3, fill: entry.color }}
              activeDot={{ r: 5 }}
              connectNulls
              // The chart is an evidence surface, not a performance: no
              // animation means the geometry is on the page when it mounts,
              // which is also what makes it deterministic to test.
              isAnimationActive={false}
            />
          ))
        : geometry.plotted.map((entry) => (
            <Bar
              key={entry.name}
              dataKey={entry.name}
              name={entry.name}
              fill={entry.color}
              isAnimationActive={false}
            />
          ))}
    </Chart>
  )
}

/**
 * The surface a run row opens. The geometry comes from the same stored result
 * the core's chart came from; the renderer is recharts where the core's is
 * SVG, and the artifact - the persisted chart the evidence graph counts and
 * the export carries - is still the core's own.
 *
 * A PNG chart is the core's bitmap, so it stays the link it was. A geometry
 * with nothing plottable is the one case where the new renderer has nothing
 * honest to draw, and the core's own image is what the surface falls back to,
 * because a chart the analyst cannot see is worse than a chart the analyst
 * cannot hover.
 */
export function ChartSurface({
  kind,
  run,
  x,
  y,
  series,
  title,
  image,
}: ChartSurfaceProps & {
  image: { format: 'svg'; svg: string } | { format: 'png'; url: string }
}): ReactElement {
  const geometry = chartGeometry(run, x, y, series)
  if (image.format === 'png' || !hasPlottablePoints(geometry)) {
    return (
      <MotionSurface
        variant="arrive"
        className={surfaces.proposal}
        data-testid="chart-surface"
      >
        <p className={surfaces.note}>{chartLabel(title, kind, x, y)}</p>
        {image.format === 'png' ? (
          <p>
            <a href={image.url}>Open the rendered chart</a>
          </p>
        ) : (
          // The geometry had nothing plottable, so the core's own drawing is
          // what the analyst sees: the artifact, rather than an empty tree.
          <div
            className="chart"
            data-testid="chart-svg"
            dangerouslySetInnerHTML={{ __html: image.svg }}
          />
        )}
      </MotionSurface>
    )
  }
  return (
    <MotionSurface
      variant="arrive"
      className={surfaces.proposal}
      data-testid="chart-surface"
    >
      <p className={surfaces.note}>
        {chartLabel(title, kind, x, y)} — drawn on screen from the run&apos;s
        stored result
      </p>
      <div className="chart" data-testid="chart-tree">
        <ChartTree
          kind={kind}
          run={run}
          x={x}
          y={y}
          series={series}
          title={title}
          width={760}
          height={300}
        />
      </div>
    </MotionSurface>
  )
}

export function chartLabel(
  title: string,
  kind: ChartKind,
  x: string,
  y: string,
): string {
  return title.trim()
    ? `${title} (${kind}: ${y} by ${x})`
    : `${kind} chart of ${y} by ${x}`
}
