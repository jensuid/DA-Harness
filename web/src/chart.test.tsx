/**
 * P9-F4-001: the on-screen chart.
 *
 * The artifact the case holds is the core's own SVG and PNG, rendered by
 * `server/app/charts.py`. The chart the analyst looks at is recharts, drawn
 * from the same stored result. These tests hold the two together: the
 * geometry the shell computes is the geometry the core's `ChartModel`
 * computes, so what the analyst sees and what the case holds answer the same
 * question the same way - and the difference between them is the tooltip,
 * the thing a static image cannot give.
 */

import { describe, expect, it } from 'vitest'
import { fireEvent, render, screen, within } from '@testing-library/react'
import type { Run } from './api'
import {
  CHART_PALETTE,
  ChartSurface,
  ChartTree,
  chartGeometry,
  hasPlottablePoints,
  isNumeric,
  labelOf,
  toNumber,
} from './lib/chart'

function runFixture(rows: unknown[][], columns = ['region', 'total']): Run {
  return {
    id: 'r1',
    case_id: 'c1',
    dataset_id: 'd1',
    kind: 'sql',
    sql: 'select region, sum(total) from orders group by region',
    code: null,
    dataset_ids: null,
    columns,
    rows,
    row_count: rows.length,
    truncated: false,
    executed_at: '',
  }
}

const REGIONS: unknown[][] = [
  ['north', 120],
  ['south', 80],
  ['east', 200],
  ['west', 60],
]

describe('the chart geometry', () => {
  it('reads the run result the way the core does', () => {
    const geometry = chartGeometry(runFixture(REGIONS), 'region', 'total', null)
    expect(geometry.categories).toEqual(['north', 'south', 'east', 'west'])
    // One series, named for the measure the way the core's `_series_of`
    // names it, at the palette's first colour.
    expect(geometry.plotted).toEqual([{ name: 'total', color: CHART_PALETTE[0] }])
    expect(geometry.data).toEqual([
      { region: 'north', total: 120 },
      { region: 'south', total: 80 },
      { region: 'east', total: 200 },
      { region: 'west', total: 60 },
    ])
  })

  it('splits the series the way the core does, first-appearance order', () => {
    const geometry = chartGeometry(
      runFixture(
        [
          ['north', 120, 'a'],
          ['north', 40, 'b'],
          ['south', 80, 'b'],
          ['east', 200, 'a'],
        ],
        ['region', 'total', 'channel'],
      ),
      'region',
      'total',
      'channel',
    )
    expect(geometry.series).toEqual(['a', 'b'])
    expect(geometry.categories).toEqual(['north', 'south', 'east'])
    // A category is the axis even when a series has no point at it, the way
    // the core's category list is `dict.fromkeys` over every point's x.
    expect(geometry.data).toEqual([
      { region: 'north', a: 120, b: 40 },
      { region: 'south', b: 80 },
      { region: 'east', a: 200 },
    ])
    expect(geometry.plotted.map((entry) => entry.name)).toEqual(['a', 'b'])
    expect(geometry.plotted.map((entry) => entry.color)).toEqual([
      CHART_PALETTE[0],
      CHART_PALETTE[1],
    ])
  })

  it('keeps a duplicated category as the two points the core draws', () => {
    // The core's single-series point list is one entry per result row, so a
    // category the result carries twice is two bars, not one merged bar.
    const geometry = chartGeometry(
      runFixture([
        ['north', 120],
        ['north', 40],
      ]),
      'region',
      'total',
      null,
    )
    expect(geometry.data).toEqual([
      { region: 'north', total: 120 },
      { region: 'north', total: 40 },
    ])
  })

  it('drops a measure the row does not actually carry', () => {
    const run = runFixture([
      ['north', 120],
      ['south', 'n/a'],
      ['east', 200],
    ])
    const geometry = chartGeometry(run, 'region', 'total', null)
    // A non-numeric measure is not plottable, the way the core's `_numeric`
    // filter drops it; the category it came with still has its axis slot.
    expect(geometry.data).toEqual([
      { region: 'north', total: 120 },
      { region: 'south' },
      { region: 'east', total: 200 },
    ])
    expect(hasPlottablePoints(geometry)).toBe(true)
  })

  it('answers nothing to plot when the measure has no numbers', () => {
    const geometry = chartGeometry(
      runFixture([
        ['north', 'n/a'],
        ['south', 'n/a'],
      ]),
      'region',
      'total',
      null,
    )
    expect(hasPlottablePoints(geometry)).toBe(false)
  })

  it('tells a number from a value that only looks like one', () => {
    expect(isNumeric(12)).toBe(true)
    expect(isNumeric(12.5)).toBe(true)
    expect(isNumeric(' 12 ')).toBe(true)
    // A boolean is not a magnitude, and the core's `_numeric` drops it too.
    expect(isNumeric(true)).toBe(false)
    expect(isNumeric(null)).toBe(false)
    expect(isNumeric(undefined)).toBe(false)
    expect(isNumeric('n/a')).toBe(false)
    expect(toNumber('n/a')).toBeNull()
    expect(toNumber(' 42 ')).toBe(42)
  })

  it('labels an integer without the decimal the run did not carry', () => {
    expect(labelOf(12)).toBe('12')
    expect(labelOf(12.5)).toBe('12.5')
    expect(labelOf('north')).toBe('north')
    expect(labelOf(null)).toBe('')
  })
})

describe('the on-screen chart', () => {
  it('renders a bar chart for the bar kind with its axes and bars', () => {
    const { container } = render(
      <ChartTree
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    const tree = screen.getByRole('img', { name: /bar chart of total by region/i })
    expect(tree.tagName).toBe('svg')
    // One bar per result row, in the palette's first colour.
    expect(container.querySelectorAll('.recharts-bar-rectangle')).toHaveLength(4)
    expect(container.querySelector('.recharts-line-curve')).toBeNull()
  })

  it('renders a line chart for the line kind with its points', () => {
    const { container } = render(
      <ChartTree
        kind="line"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    const tree = screen.getByRole('img', { name: /line chart of total by region/i })
    expect(tree.tagName).toBe('svg')
    expect(container.querySelector('.recharts-line-curve')).not.toBeNull()
    // A dot per point, the way the core's SVG draws a circle at each one.
    expect(container.querySelectorAll('.recharts-line-dot')).toHaveLength(4)
    expect(container.querySelector('.recharts-bar-rectangle')).toBeNull()
  })

  it('names the axes with the columns they plot', () => {
    render(
      <ChartTree
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    const axis = screen.getByRole('img', { name: /bar chart of total by region/i })
    // The categories the x axis draws, which is the axis's own label set.
    expect(within(axis).getByText('north')).toBeInTheDocument()
    expect(within(axis).getByText('east')).toBeInTheDocument()
  })

  it('anchors a bar at zero so its length reads as magnitude', () => {
    const { container } = render(
      <ChartTree
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    // The core anchors a bar's scale at zero (`anchor_at_zero`), so the screen
    // does too. jsdom has no SVG `getBBox`, so the axis's tick labels do not
    // measure; the bars do. A zero-anchored axis is what makes a bar's height
    // proportional to its value, so the smallest value's height is the same
    // fraction of the tallest one the values are of each other: 60 of 200.
    const heights = Array.from(container.querySelectorAll('.recharts-bar-rectangle'))
      .map((node) => node.querySelector('.recharts-rectangle'))
      .map((node) => Number(node?.getAttribute('height') ?? 0))
      .sort((a, b) => a - b)
    expect(heights[0] / heights[heights.length - 1]).toBeCloseTo(60 / 200, 2)
  })

  it('draws a legend only when there is more than one series', () => {
    const single = render(
      <ChartTree
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    expect(single.container.querySelector('.recharts-legend-wrapper')).toBeNull()

    const multi = render(
      <ChartTree
        kind="bar"
        run={runFixture(
          [
            ['north', 120, 'a'],
            ['south', 80, 'b'],
          ],
          ['region', 'total', 'channel'],
        )}
        x="region"
        y="total"
        series="channel"
        title=""
        width={760}
      />,
    )
    // Two series carry the legend, named for the series, not for the measure.
    expect(multi.container.querySelector('.recharts-default-legend')).not.toBeNull()
    expect(within(multi.container).getByText('a')).toBeInTheDocument()
    expect(within(multi.container).getByText('b')).toBeInTheDocument()
    expect(multi.container.querySelectorAll('.recharts-bar-rectangle')).toHaveLength(2)
  })

  it('carries a tooltip, which a static image cannot answer with', async () => {
    const { container } = render(
      <ChartTree
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    // The tooltip is part of the tree, so a point the analyst reaches has
    // its own values read back - the reason the screen is not the artifact.
    // recharts renders it as an assertive live region, which is what makes a
    // hovered point's values announced rather than only painted; a static
    // SVG has no element at all.
    const tooltip = container.querySelector('.recharts-tooltip-wrapper')
    expect(tooltip).not.toBeNull()
    // The inner surface is the live region a screen reader reaches.
    const live = container.querySelector('.recharts-default-tooltip')
    expect(live).not.toBeNull()
    expect(live!.getAttribute('role')).toBe('status')
    expect(live!.getAttribute('aria-live')).toBe('assertive')
    // And hovering a bar reaches the tooltip the tree already carries.
    const bar = container.querySelector('.recharts-bar-rectangle')!
    await fireEvent.mouseEnter(bar)
    await fireEvent.mouseMove(bar, { clientX: 100, clientY: 100 })
    expect(container.querySelector('.recharts-tooltip-wrapper')).not.toBeNull()
  })

  it('uses the palette the core\'s own SVG uses', () => {
    const { container } = render(
      <ChartTree
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    // The core paints its first series `#2563eb`; the screen agrees, so the
    // legend the analyst reads is the legend the artifact carries.
    const bars = container.querySelectorAll('.recharts-bar-rectangle')
    expect(bars).toHaveLength(4)
    const path = bars[0].querySelector('.recharts-rectangle')
    expect(path).not.toBeNull()
    expect(path!.getAttribute('fill')).toBe(CHART_PALETTE[0])
  })

  it('keeps the geometry the core computes when the result is truncated', () => {
    const run = runFixture(REGIONS)
    run.truncated = true
    run.row_count = 400
    const { container } = render(
      <ChartTree
        kind="bar"
        run={run}
        x="region"
        y="total"
        series={null}
        title=""
        width={760}
      />,
    )
    // The chart draws the rows the result carries, not the count the run
    // reports, the way the core renders the stored result alone.
    expect(container.querySelectorAll('.recharts-bar-rectangle')).toHaveLength(4)
  })
})

describe('the chart surface', () => {
  const svg = '<svg xmlns="http://www.w3.org/2000/svg"><text>the core drew this</text></svg>'

  it('draws the run on screen and names what it plots', () => {
    render(
      <ChartSurface
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        image={{ format: 'svg', svg }}
      />,
    )
    const surface = screen.getByTestId('chart-surface')
    expect(within(surface).getByText(/bar chart of total by region/i)).toBeInTheDocument()
    expect(within(surface).getByText(/drawn on screen/i)).toBeInTheDocument()
    expect(within(surface).getByTestId('chart-tree')).toBeInTheDocument()
    // The core's own drawing is the artifact, not what the shell shows here.
    expect(within(surface).queryByText(/the core drew this/i)).not.toBeInTheDocument()
  })

  it('carries the title the chart was rendered with', () => {
    render(
      <ChartSurface
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title="Revenue by region"
        image={{ format: 'svg', svg }}
      />,
    )
    expect(
      screen.getByText(/revenue by region \(bar: total by region\)/i),
    ).toBeInTheDocument()
  })

  it('falls back to the core\'s own image when nothing is plottable', () => {
    const run = runFixture([
      ['north', 'n/a'],
      ['south', 'n/a'],
    ])
    render(
      <ChartSurface
        kind="bar"
        run={run}
        x="region"
        y="total"
        series={null}
        title=""
        image={{ format: 'svg', svg }}
      />,
    )
    const surface = screen.getByTestId('chart-surface')
    // A geometry with nothing to plot is the core's image, because a chart
    // the analyst cannot see is worse than a chart the analyst cannot hover.
    expect(within(surface).getByTestId('chart-svg').querySelector('svg')).not.toBeNull()
    expect(within(surface).queryByTestId('chart-tree')).not.toBeInTheDocument()
    expect(within(surface).getByText(/the core drew this/i)).toBeInTheDocument()
  })

  it('keeps a PNG chart as the link to the core\'s artifact', () => {
    render(
      <ChartSurface
        kind="bar"
        run={runFixture(REGIONS)}
        x="region"
        y="total"
        series={null}
        title=""
        image={{ format: 'png', url: '/api/cases/c1/charts/c9/image' }}
      />,
    )
    const link = screen.getByRole('link', { name: /open the rendered chart/i })
    expect(link).toHaveAttribute('href', '/api/cases/c1/charts/c9/image')
    // A PNG is the core's bitmap, so no second renderer draws it on screen.
    expect(screen.queryByTestId('chart-tree')).not.toBeInTheDocument()
    expect(screen.getByTestId('chart-surface')).toBeInTheDocument()
  })
})
