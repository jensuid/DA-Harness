/**
 * P9-F1-001: this panel moved out of CaseWorkspace.tsx verbatim.
 * The workspace holds the state; the panel is pure over its props.
 */

import { useEffect, useState } from 'react'
import { ApiError, type Dataset, type Plan, createPlan, getPlan } from '../api'
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'

export function PlanPanel({
  caseId,
  datasets,
  onChanged,
}: {
  caseId: string
  datasets: Dataset[]
  onChanged: () => void
}) {
  const [plan, setPlan] = useState<Plan | null>(null)
  const [missing, setMissing] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [generateError, setGenerateError] = useState<string | null>(null)
  const [generating, setGenerating] = useState(false)

  const datasetId = datasets.length > 0 ? datasets[0].id : null

  useEffect(() => {
    if (datasetId === null) {
      setPlan(null)
      setMissing(false)
      setError(null)
      return
    }
    let cancelled = false
    // The plan belongs to a dataset; the first attached one is the one the
    // workspace generates code against, so its plan is the one the analyst is
    // working from.
    getPlan(caseId, datasetId)
      .then((result) => {
        if (cancelled) return
        setPlan(result)
        setMissing(false)
        setError(null)
      })
      .catch((err) => {
        if (cancelled) return
        setPlan(null)
        // A 404 is a case that has not planned yet; anything else is a real
        // failure the panel reports rather than hiding behind the empty state.
        setMissing(err instanceof ApiError && err.status === 404)
        setError(messageOf(err))
      })
    return () => {
      cancelled = true
    }
  }, [caseId, datasetId])

  async function generate() {
    if (generating || datasetId === null) return
    setGenerating(true)
    setError(null)
    setGenerateError(null)
    try {
      const created = await createPlan(caseId, datasetId)
      setPlan(created)
      setMissing(false)
      // The plan is what makes the rail's next action legible, so the case's
      // stage and counts are re-read - the rail moves with the panel rather
      // than waiting for the next mount.
      onChanged()
    } catch (err) {
      // The endpoint refuses to plan an unprofiled dataset, and that refusal
      // is the sentence the analyst needs: it names the step before this one.
      // This is held separately from the read's error because the two are
      // never both live: the empty state the control lives in means the read
      // answered 404, and a 404 is not the reason a generation failed.
      setGenerateError(messageOf(err))
    } finally {
      setGenerating(false)
    }
  }

  if (datasets.length === 0) {
    return (
      <div className="panel">
        <h2>Plan</h2>
        <p className="muted">Attach a dataset before planning the analysis.</p>
      </div>
    )
  }

  if (!plan) {
    return (
      <div className="panel">
        <h2>Plan</h2>
        {missing ? (
          <>
            <p className="muted">
              No plan for {datasets[0].filename} yet - generate one to get
              sub-questions, hypotheses and the steps that answer them.
            </p>
            <div className="row">
              <button
                type="button"
                onClick={() => void generate()}
                disabled={generating}
              >
                {generating ? 'Generating the plan…' : 'Generate an analysis plan'}
              </button>
            </div>
            {generateError && (
              // The endpoint's own reason, as a sentence: a 400 is an
              // unprofiled dataset, so the refusal names the step before this
              // one rather than reading as a fault in the panel.
              <p role="alert">{generateError}</p>
            )}
          </>
        ) : error ? (
          <p role="alert">The plan could not be read: {error}</p>
        ) : (
          <p className="muted">Loading the plan…</p>
        )}
      </div>
    )
  }

  const body = plan.plan
  return (
    <div className="panel">
      <h2>Plan</h2>
      <p className="muted">
        {sourceLabel(plan.source, 'plan')} for {datasets[0].filename}
        {body.context_basis.length > 0 &&
          ` — read from ${body.context_basis.join(', ')}`}
      </p>
      <h3>Objective</h3>
      <p>Objective: {body.objective}</p>
      <h3>Sub-questions</h3>
      <ol className="items">
        {body.sub_questions.map((item, i) => (
          <li key={i}>{item}</li>
        ))}
      </ol>
      <h3>Hypotheses</h3>
      <ul className="items">
        {body.hypotheses.map((hypothesis, i) => (
          <li key={i} className="run">
            <p><strong>{hypothesis.statement}</strong></p>
            <p className="muted">why: {hypothesis.rationale}</p>
            <p className="muted">how to check: {hypothesis.check}</p>
          </li>
        ))}
      </ul>
      <h3>Steps</h3>
      <ol className="items">
        {body.analysis_steps.map((step, i) => (
          <li key={i}>
            <strong>{step.action}</strong>
            <span className="muted"> — {step.detail}</span>
          </li>
        ))}
      </ol>
      <h3>Data requirements</h3>
      <ul className="items">
        {body.data_requirements.map((requirement, i) => (
          <li key={i} className="muted">
            {requirement.requirement}: {requirement.detail}
          </li>
        ))}
      </ul>
    </div>
  )
}

// The profile's per-column null counts, as the profiler measured them. A
// column's null percentage is what the missing-data check and the planner both
// read, and rendering it at the Data stage means the analyst sees the hole
// before spending a question on it (UX 15).
