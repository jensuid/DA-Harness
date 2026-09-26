/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { type CaseProgress } from '../api'
import { surfaces } from '../lib/ui'

export function WorkflowRail({
  progress,
  qualityWarning,
}: {
  progress: CaseProgress | null
  qualityWarning: boolean
}) {
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
        <p>
          Next: <strong>{progress.next_action}</strong>
          <br />
          <code>{progress.next_endpoint}</code>
        </p>
      ) : (
        <p>Every stage has an artifact behind it.</p>
      )}
      <ul className={surfaces.panelList}>
        {progress.stages.map((stage) => {
          const status = stageStatus(stage.name, progress, qualityWarning)
          return (
            <li
              key={stage.name}
              className={`stage ${status}`}
              aria-label={`stage ${stage.name}: ${status}`}
            >
              {STAGE_MARKS[status]} {stage.name}
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
