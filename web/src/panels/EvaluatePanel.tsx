/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useState } from 'react'
import { ApiError, type Dataset, type Evaluation, type Profile, evaluateDataset } from '../api'
import { messageOf } from '../CaseList'
import { Button, surfaces } from '../lib/ui'
import { Verdict } from './FindingsPanel'

// W-017: a 400 from the audit endpoint is the contract naming what to fix, but
// three different causes all answer 400 and the core's own sentence names the
// *artifact*, so an analyst who left a field empty read it as their SQL being
// refused. Each cause has its own sentence here, so the message the panel shows
// is about the field that is actually wrong. The key is the core's own detail
// string, so a core that rewords a refusal reads as an unknown 400 and is shown
// verbatim - the honesty budget is not paid by hiding a reason this map stops
// recognising.
export const EVALUATE_REFUSALS: Readonly<Record<string, string>> = {
  "the artifact's code is empty":
    "The artifact's code is empty - paste the work to audit.",
  'no claim was submitted to audit':
    'No claim was submitted - state what the work was offered to support.',
  "the artifact's kind must be 'sql' or 'python'":
    "The artifact's kind must be SQL or Python.",
  'the artifact is not a single read-only query':
    'The artifact is not a single read-only query, so it cannot be executed or audited.',
}

export function evaluateRefusal(error: unknown): string {
  if (error instanceof ApiError && error.status === 400) {
    for (const [key, sentence] of Object.entries(EVALUATE_REFUSALS)) {
      if (error.message.includes(key)) return sentence
    }
  }
  return messageOf(error)
}

export function EvaluatePanel({
  caseId,
  datasets,
  profiles,
  evaluations,
  onChanged,
}: {
  caseId: string
  datasets: Dataset[]
  profiles: Record<string, Profile>
  evaluations: Evaluation[]
  onChanged: () => void
}) {
  // An audit is meaningless without a profile: the Data and Quality axes judge
  // the code against profiled columns. The panel is absent rather than offering
  // a submission that cannot succeed.
  const profiled = datasets.filter((d) => profiles[d.id] !== undefined)
  const [chosen, setChosen] = useState('')
  const [kind, setKind] = useState<'sql' | 'python'>('sql')
  const [code, setCode] = useState('')
  const [claim, setClaim] = useState('')
  const [audit, setAudit] = useState<Evaluation | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  if (profiled.length === 0) {
    return (
      <div className={surfaces.panel}>
        <h2 className={surfaces.heading}>Audit submitted work (EVALUATE)</h2>
        <p className={surfaces.note}>
          Attach and profile a dataset first - an audit judges the work against
          the data it claims to read.
        </p>
      </div>
    )
  }

  const datasetId = chosen || profiled[0].id

  async function submit(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      setAudit(await evaluateDataset(caseId, datasetId, code, claim, kind))
      // The audit is persisted by the core, so the panel reloads the record
      // rather than trusting its own copy of it.
      onChanged()
    } catch (err) {
      // A 400 is part of the contract: a non-read-only artifact is refused
      // before anything executes. W-017: the three causes that answer 400 are
      // named separately rather than as one raw backend sentence, so an empty
      // field is not misread as the artifact being refused.
      setError(evaluateRefusal(err))
    } finally {
      setBusy(false)
    }
  }

  const prior = evaluations.filter((e) => e.dataset_id === datasetId)

  return (
    <div className={surfaces.panel}>
      <h2 className={surfaces.heading}>Audit submitted work (EVALUATE)</h2>
      <p className={surfaces.note}>
        Paste work that came from elsewhere and the claim it was offered to
        support. DAH runs it against the data and answers nine questions, each
        with a verdict and a sentence.
      </p>
      {profiled.length > 1 && (
        <label>
          Audit against
          <select
            aria-label="Dataset to audit against"
            value={datasetId}
            onChange={(e) => {
              setChosen(e.target.value)
              setAudit(null)
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
        <div className={surfaces.rowGap}>
          <label className="kind-toggle">
            <input
              type="radio"
              name="artifact-kind"
              value="sql"
              checked={kind === 'sql'}
              onChange={() => setKind('sql')}
            />{' '}
            SQL
          </label>
          <label className="kind-toggle">
            <input
              type="radio"
              name="artifact-kind"
              value="python"
              checked={kind === 'python'}
              onChange={() => setKind('python')}
            />{' '}
            Python
          </label>
        </div>
        <label>
          The artifact's code
          <textarea
            aria-label="The artifact's code"
            value={code}
            onChange={(e) => setCode(e.target.value)}
            placeholder={
              kind === 'sql'
                ? 'SELECT region, SUM(revenue) AS total FROM read_csv_auto(?) GROUP BY region'
                : "result = [{'total': sum(r['revenue'] for r in dataset.rows)}]"
            }
            rows={4}
            disabled={busy}
          />
        </label>
        <label>
          The claim it supports
          <input
            aria-label="The claim the code was offered to support"
            value={claim}
            onChange={(e) => setClaim(e.target.value)}
            placeholder="Revenue is higher in north than south"
            disabled={busy}
          />
        </label>
        <Button type="submit" disabled={busy || !code.trim() || !claim.trim()}>
          {busy ? 'Auditing…' : 'Audit this work'}
        </Button>
      </form>
      {error && <p role="alert">The audit could not run: {error}</p>}
      {audit && <Audit evaluation={audit} />}
      {prior.length > 0 && (
        <div className={surfaces.subpanel}>
          <h3 className={surfaces.subheading}>Recorded audits</h3>
          <ul className={surfaces.panelList}>
            {prior.map((evaluation) => (
              <li key={evaluation.id}>
                <RecordedAudit evaluation={evaluation} />
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// The nine axes in the spec's own order. The order is the order a reader asks
// them in, so the audit does not reorder it.
export const AXES = [
  'question', 'data', 'quality', 'method', 'calculation',
  'evidence', 'claim', 'visualization', 'limitations',
]

export function Audit({ evaluation }: { evaluation: Evaluation }) {
  const byAxis = new Map(evaluation.findings.map((f) => [f.axis, f]))
  return (
    <div className={surfaces.proposal} data-testid="audit">
      <p className={surfaces.note}>
        audited by {evaluation.source} — the artifact is stored as a run and can
        be re-read in the Runs panel
      </p>
      <ul className={surfaces.panelList}>
        {AXES.map((axis) => {
          const finding = byAxis.get(axis)
          if (!finding) return null
          return (
            <li key={axis}>
              <Verdict verdict={finding.verdict} axis={axis} detail={finding.detail} />
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// The verdict is the summary and the sentence is the substance, so neither is
// rendered without the other. Three states, not a score - the core's own
// decision, kept here rather than flattened into a number the axes cannot have.

export function RecordedAudit({ evaluation }: { evaluation: Evaluation }) {
  const summary = evaluation.findings
    .filter((f) => f.verdict !== 'pass')
    .map((f) => `${f.axis}: ${f.verdict}`)
  return (
    <div className={surfaces.row}>
      <p><strong>{evaluation.claim}</strong></p>
      <p className={surfaces.note}>
        {evaluation.artifact_kind} —{' '}
        {summary.length > 0 ? summary.join(', ') : 'every axis passed'}
      </p>
    </div>
  )
}

// One citation. A `case:` ground names a case the analyst can go and read, so
// it is a button; every other kind is a chip as it always was. The prior case's
// own question is the label because that is how the analyst recognises it - a
// uuid would not be.
