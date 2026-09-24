/**
 * Interaction timing (AT-27), for jsdom.
 *
 * The PRD's target is a 95th-percentile interaction response of 200ms on
 * benchmark hardware - a browser target, measured against the browser's own
 * clock. jsdom is not a browser: it has no compositor and runs no layout, so
 * a millisecond here is not a millisecond there. What it *can* measure is the
 * React layer's own response cost - the state update and re-render an
 * interaction causes - which is the part the product controls and the part a
 * regression in this code makes worse.
 *
 * The p95 helper is the percentile itself, implemented once so the suite and
 * any report compute the same number from the same samples.
 */

/**
 * The 95th percentile of a sample of durations, in milliseconds.
 *
 * Interpolated the way a benchmark percentile usually is: the sample's own
 * values are the population we have, and the 95th percentile is the value
 * 95% of the way through the sorted samples. An empty sample answers zero
 * rather than crashing, because a measurement that ran no samples is a
 * measurement that should say so, not one that should fail a test with a
 * division by nothing.
 */
export function p95(samples: number[]): number {
  if (samples.length === 0) return 0
  const sorted = [...samples].sort((a, b) => a - b)
  const rank = 0.95 * (sorted.length - 1)
  const lower = Math.floor(rank)
  const upper = Math.ceil(rank)
  if (lower === upper) return sorted[lower]
  const share = rank - lower
  return sorted[lower] + (sorted[upper] - sorted[lower]) * share
}
