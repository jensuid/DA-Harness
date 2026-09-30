/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { type CaseProgress } from '../api'
import { surfaces } from '../lib/ui'

// W2X-005: the stage's action is an action in the product, not an endpoint.
// The rail's "Next" is the first thing an analyst reads, and a raw HTTP path
// answers the developer's question, not theirs. Each stage names the panel
// that performs it; the button scrolls there, and the endpoint stays available
// behind "developer info" for the reader who wanted it.
const STAGE_PANEL: Record<string, { panel: string; label: string }> = {
  question: { panel: 'refine', label: 'the question panel' },
  data: { panel: 'data', label: 'the Data panel' },
  profile: { panel: 'data', label: 'the Data panel' },
  plan: { panel: 'plan', label: 'the Plan panel' },
  analyze: { panel: 'runs', label: 'the Runs panel' },
  evidence: { panel: 'findings', label: 'the Findings panel' },
  validate: { panel: 'evaluate', label: 'the Evaluate panel' },
}

export function WorkflowRail({
  progress,
  qualityWarning,
}: {
  progress: CaseProgress | null
  qualityWarning: boolean
}) {
  const target =
    progress?.stage && progress.stage in STAGE_PANEL
      ? STAGE_PANEL[progress.stage]
      : null
  if (!progress) return <p className={surfaces.note}>Loading workflow…</p>
  return (
    <div className={surfaces.panel + ' workflow-rail'}>
      <h2 className={surfaces.heading}>Where this case stands</h2>
      {/* One text node: the sentence stays readable in the DOM and in a screen
          reader, and a test can assert on it without reaching across elements. */}
      <p>
        <strong>
          Stage: {progress.loop_closed ? 'validated' : progress.stage}
          {progress.loop_closed && ' — the trust loop has closed'}
        </strong>
      </p>
      {progress.next_action ? (
        <div className="next-action">
          <p>
            Next: <strong>{progress.next_action}</strong>
          </p>
          {progress.next_hint && (
            <p className={surfaces.note}>{progress.next_hint}</p>
          )}
          {target && (
            <p>
              <button
                type="button"
                className="next-action-link"
                onClick={() => {
                  const el = document.getElementById(target.panel)
                  if (el) el.scrollIntoView({ behavior: 'smooth', block: 'start' })
                }}
              >
                Go to {target.label}
              </button>
            </p>
          )}
          <details>
            <summary>developer info</summary>
            <code>{progress.next_endpoint}</code>
          </details>
        </div>
      ) : (
        <p>Every stage has an artifact behind it.</p>
      )}
      <ul className={surfaces.panelList + ' stage-list'}>
        {progress.stages.map((stage) => {
          const status = stageStatus(stage.name, progress, qualityWarning)
          return (
            <li
              key={stage.name}
              className={`stage ${status}`}
              aria-label={`stage ${stage.name}: ${status}`}
            >
              {/* L2: the glyph stays the status the audit pins it as; the
                  fixed-width span is what the rule through the stages aligns
                  on, so a stage reads as a rung rather than a bullet. */}
              <span className="stage-mark" aria-hidden="true">
                {STAGE_MARKS[status]}
              </span>{' '}
              {stage.name}
            </li>
          )
        })}
      </ul>
    </div>
  )
}

// One stage's status, derived the same way the core derives the stage itself:
// a stage is complete when `progress.completed` names it, current when it is
// the first stage that does not, and not started otherwise. The warning is the
// only judgement here, and it is a measured one - the data stage's artifact
// exists but the profiler found something in it.
export function stageStatus(
  name: string,
  progress: CaseProgress,
  qualityWarning: boolean,
): 'complete' | 'attention' | 'current' | 'pending' {
  if (progress.completed.includes(name)) {
    // A stage reached but degraded warns rather than passing silently; every
    // other completed stage is clean.
    if (name === 'data' && qualityWarning) return 'attention'
    return 'complete'
  }
  // The core's stage is the first incomplete one, so this is where the loop is.
  if (name === progress.stage) return 'current'
  return 'pending'
}

export const STAGE_MARKS: Record<string, string> = {
  complete: '✓',
  attention: '⚠',
  current: '●',
  pending: '○',
}

// The case's control center (UX 45, AT-33): the seven things an analyst needs
// to answer "what is this case, and where does it stand" without scrolling
// through panels. Every number is an artifact count the core already computed,
// so the overview is a reading of the case rather than a second opinion about
// it - and it cannot drift from the rail beside it.
