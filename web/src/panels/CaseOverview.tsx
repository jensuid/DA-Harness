/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { CaseProgress, QualityIssue } from '../api'
import { surfaces } from '../lib/ui'

export function CaseOverview({
  question,
  purpose,
  progress,
  datasets,
  findings,
  openIssues,
  pendingValidation,
}: {
  question: string
  purpose: string
  progress: CaseProgress | null
  datasets: number
  findings: number
  openIssues: number
  pendingValidation: number
}) {
  // The analyst's stated purpose outranks the question when both exist; a case
  // that never stated one is described by the question it was created with, so
  // the objective is never blank.
  const objective = purpose.trim() || question
  const total = progress ? progress.stages.length : 0
  const done = progress ? progress.completed.length : 0
  const validated = progress ? progress.counts['validated_findings'] ?? 0 : 0

  return (
    <div className={surfaces.panel + ' case-overview'}>
      <h2 className={surfaces.heading}>Case overview</h2>
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
      </ul>
    </div>
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
