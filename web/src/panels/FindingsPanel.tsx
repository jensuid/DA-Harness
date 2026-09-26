/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useState } from 'react'
import { type Finding, type ValidationResult, validateFinding } from '../api'
import { messageOf } from '../CaseList'
import { Button, surfaces } from '../lib/ui'
import { MotionSurface } from '../lib/motion'

export function FindingsPanel({
  caseId,
  findings,
  onChanged,
}: {
  caseId: string
  findings: Finding[]
  onChanged: () => void
}) {
  if (findings.length === 0) {
    return (
      <div className={surfaces.panel}>
        <h2 className={surfaces.heading}>Findings</h2>
        <p className={surfaces.note}>No findings yet - a run can draft one.</p>
      </div>
    )
  }
  return (
    <div className={surfaces.panel}>
      <h2 className={surfaces.heading}>Findings</h2>
      <ul className={surfaces.panelList}>
        {findings.map((finding) => (
          <li key={finding.id}>
            <FindingRow caseId={caseId} finding={finding} onChanged={onChanged} />
          </li>
        ))}
      </ul>
    </div>
  )
}

export function FindingRow({
  caseId,
  finding,
  onChanged,
}: {
  caseId: string
  finding: Finding
  onChanged: () => void
}) {
  const [verdict, setVerdict] = useState<ValidationResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function validate() {
    setBusy(true)
    setError(null)
    try {
      setVerdict(await validateFinding(caseId, finding.id))
      // The verdict persists on the finding, so the panel reloads rather than
      // showing a stale not_evaluated next time.
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={surfaces.row}>
      <p>{finding.statement}</p>
      <p className={surfaces.note}>status: {finding.validation_status}</p>
      {verdict && (
        <MotionSurface variant="arrive" className={surfaces.proposal}>
          <p><strong>Verdict: {verdict.status}</strong></p>
          {/* P8-CAUSAL-004: a guard refusal is the message, not a footnote on a
              pass. The verdict names the sentence to fix, so a finding that
              outruns its evidence is read as a refusal the analyst can act on
              rather than a warning beside a green tick. */}
          {verdict.status === 'insufficient_evidence' && (
            <p className="fail">
              The verdict refuses this finding rather than passing it with a
              caveat. A dimension the evidence cannot support failed, and its
              sentence above is what to change.
            </p>
          )}
          <ul className={surfaces.panelList}>
            {verdict.checks.map((check) => (
              <li
                key={check.name}
                className={check.passed ? surfaces.note : check.hard ? 'fail' : 'warn'}
              >
                {/* A concern is not a failure: the numbers reproduce and the
                    claim is phrased within them, but the analysis carries a
                    stated limitation. The two read differently, so they render
                    differently (P8-VALID-003). */}
                {check.passed ? '✓' : check.hard ? '✗' : '⚠'} {check.dimension} —{' '}
                {check.detail}
              </li>
            ))}
          </ul>
        </MotionSurface>
      )}
      <Button type="button" onClick={validate} disabled={busy} variant="small">
        {busy ? 'Validating…' : 'Validate'}
      </Button>
      {error && <p role="alert">Validation failed: {error}</p>}
    </div>
  )
}

// The assistant surface that needs nothing but a case. The citations are the
// point: each ground is rendered as a chip so a reviewer can check the answer
// against the artifact, and the badge says which engine spoke - a deterministic
// answer only ever cites what the case actually has.

export function Verdict({
  verdict,
  axis,
  detail,
}: {
  verdict: string
  axis: string
  detail: string
}) {
  const mark = verdict === 'pass' ? '✓' : verdict === 'concern' ? '!' : '✗'
  return (
    <p>
      <span className={`verdict ${verdict}`}>{mark} {axis}</span>
      <span className={surfaces.note}> — {detail}</span>
    </p>
  )
}
