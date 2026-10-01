/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useId } from 'react'
import { CaseProgress, QualityIssue } from '../api'
import { Skeleton, surfaces } from '../lib/ui'

export function CaseOverview({
  question,
  purpose,
  progress,
  datasets,
  findings,
  openIssues,
  pendingValidation,
  pending,
}: {
  question: string
  purpose: string
  progress: CaseProgress | null
  datasets: number
  findings: number
  openIssues: number
  pendingValidation: number
  // W2X-008: the surfaces the case is still waiting on. A panel whose empty
  // state carries no control is hidden until it has data, so the overview
  // names them here instead - one sentence, where an analyst scans the case's
  // shape, rather than twelve panels each saying the same nothing.
  pending: string[]
}) {
  const headingId = useId()
  // The analyst's stated purpose outranks the question when both exist; a case
  // that never stated one is described by the question it was created with, so
  // the objective is never blank.
  const objective = purpose.trim() || question
  // SKEL: `progress` lands with the workspace's first batch, so its absence is
  // the in-flight signal - and until it lands every count below would read as
  // a case that has nothing, which is a different sentence from a case the
  // shell has not read yet.
  if (!progress) {
    return (
      <section
        className={surfaces.panel + ' case-overview'}
        aria-labelledby={headingId}
      >
        <h2 className={surfaces.heading} id={headingId}>Case overview</h2>
        <p className={surfaces.note + ' visually-hidden'}>Reading the case…</p>
        <Skeleton shape="facts" />
      </section>
    )
  }
  const total = progress.stages.length
  const done = progress.completed.length
  const validated = progress.counts['validated_findings'] ?? 0

  return (
    <section
      className={surfaces.panel + ' case-overview'}
      aria-labelledby={headingId}
    >
      <h2 className={surfaces.heading} id={headingId}>Case overview</h2>
      {/* One text node per fact: the label and its value stay in the same
          element, so each sentence reads whole in the DOM and in a screen
          reader, and nothing has to reach across elements to match one. */}
      <ul className="overview">
        <li>Objective: {objective}</li>
        <li>Question: {question}</li>
        <li>
          Status: {done} / {total} stages complete
          {progress?.loop_closed && ' — the trust loop has closed'}
        </li>
        <li>Key findings: {findings}</li>
        <li>Open issues: {openIssues}</li>
        <li>Data sources: {datasets}</li>
        <li>
          Validation: {validated} finding{validated === 1 ? '' : 's'} validated
          {pendingValidation > 0
            ? `, ${pendingValidation} pending`
            : findings > 0
              ? ''
              : ' — none recorded yet'}
        </li>
        {pending.length > 0 && (
          // W2X-008: the hidden panels' empty states, named in one sentence.
          // A young case is told what it does not have yet, by the panel that
          // already answers "what does this case have", rather than by a
          // screen of surfaces each saying nothing.
          <li>
            Still to come: {pending.join(', ')}
          </li>
        )}
      </ul>
    </section>
  )
}

// What the data cannot support, before the analyst spends a question on it
// (AT-08/AT-09, UX 15). Each issue states what was measured and what it costs,
// at the Data stage rather than only after a finding exists; a dataset with no
// issues says so plainly, because "nothing rendered" is not the same signal as
// "this data is clean".
export function QualityList({ quality }: { quality: QualityIssue[] }) {
  if (!quality || quality.length === 0) {
    return <p className={surfaces.note + ' quality-clean'}>No data-quality issues detected.</p>
  }
  return (
    <ul className="quality-issues">
      {quality.map((issue, index) => (
        <li key={index} className={`quality-issue severity-${issue.severity}`}>
          <span className="quality-observed">{issue.observed}</span>
          {' '}
          <span className="quality-impact">Potential impact: {issue.impact}</span>
        </li>
      ))}
    </ul>
  )
}
