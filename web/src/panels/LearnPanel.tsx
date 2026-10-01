/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { type LearnWalk } from '../api'
import { Skeleton, surfaces } from '../lib/ui'

// W2X-008: the panel renders its body directly. The collapse is the Case
// record group's own disclosure, which carries this panel's derived summary -
// a disclosure nested in a disclosure is two clicks to read one thing, and
// the group's summary is the one the analyst scans.
export function LearnPanel({
  walk,
  error,
  missing,
}: {
  walk: LearnWalk | null
  error: string | null
  missing: boolean
}) {
  return (
    <div className={surfaces.panel}>
      <h2 className={surfaces.heading}>Learn this case</h2>
      {missing ? (
        // A 404 means the case is unknown. The workspace loads its own case on
        // mount, so the header already reports it - this panel says so once,
        // as guidance, rather than reporting the same failure twice.
        <p className={surfaces.note}>The walk could not be read: {error}</p>
      ) : !walk ? (
        <>
          <p className={surfaces.note + ' visually-hidden'}>Loading the walk…</p>
          <Skeleton shape="rows" count={4} />
        </>
      ) : (
        <WalkBody walk={walk} />
      )}
      {!missing && error && (
        <p role="alert">The walk could not be read: {error}</p>
      )}
    </div>
  )
}

// W2X-008: the collapsed summary the record group shows. It carries the
// panel's name - so the toggle is found by the name an analyst knows it by -
// and the state, so a finished walk says it finished rather than merely
// sitting closed. A walk that could not be read is named by the failure
// itself rather than by its absence: the panel's guidance is the one place
// the 404 is said once, and a collapsed group that hid it would report a
// missing case as a case with nothing to learn. The workspace sets the error
// and a null walk together, so the error branch is read before the null one
// - a load still in flight has neither.
export function walkSummary(walk: LearnWalk | null, error: string | null): string {
  if (error) return 'Learn this case — could not be read'
  if (!walk) return 'Learn this case'
  if (walk.done) {
    return 'Learn this case — complete, every phase done'
  }
  const phase = PHASE_TITLES[walk.current ?? ''] ?? walk.current
  return walk.current
    ? `Learn this case — ${phase} is the phase to work on`
    : 'Learn this case'
}

export function WalkBody({ walk }: { walk: LearnWalk }) {
  return (
    <>
      <p className={surfaces.note}>
        A guided walk: why ask it, what the data says, how you test it, and
        whether it holds.
      </p>
      {walk.done ? (
        // The core's own discipline: a closed loop means the loop ran, not that
        // the answer is right - so the panel does not graduate the learner on a
        // stronger claim than the artifacts support.
        <p className={surfaces.note}>
          The walk is complete: every phase is done and a finding has been
          validated. That says the trust loop ran, not that the answer is right.
        </p>
      ) : (
        // One thing to do next, never two - the core guarantees at most one
        // current phase, and the panel says which.
        <p>
          The phase to work on now is{' '}
          {PHASE_TITLES[walk.current ?? ''] ?? walk.current}: {walk.next_action}
          <br />
          <code>{walk.next_endpoint}</code>
        </p>
      )}
      <ul className={surfaces.panelList}>
        {walk.steps.map((step) => (
          <li key={step.name} aria-label={`phase ${step.name}: ${step.status}`}>
            <h3 className={surfaces.subheading}>{PHASE_TITLES[step.name] ?? step.name}</h3>
            <p className={surfaces.note}>status: {step.status}</p>
            <p className={surfaces.note}>{step.purpose}</p>
            <p>
              Can you answer: <strong>{step.prompt}</strong>
            </p>
            <ul className={surfaces.panelList}>
              {step.stages.map((stage) => (
                <li
                  key={stage.name}
                  className={stage.completed ? 'stage done' : 'stage'}
                  aria-label={`${stage.action}: ${stage.completed ? 'done' : 'to do'}`}
                >
                  {stage.completed ? '✓' : '○'} {stage.action}
                  <span className={surfaces.note}> — {stage.hint}</span>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </>
  )
}

// The core's phase names, as a learner reads them.
export const PHASE_TITLES: Record<string, string> = {
  why: 'Why',
  what: 'What',
  how: 'How',
  validate: 'Validate',
}

// The orientation spine (UX 5/7, AT-33): a persistent rail that answers
// "where am I in this loop and what is next" from the artifact counts the core
// derives, so the rail cannot disagree with the core's own stage. The four
// marks are the UX document's status vocabulary:
//
//   ✓  complete      - the stage has an artifact behind it
//   ⚠  attention     - complete, but a measured defect degrades it (a
//                      data-quality issue the profiler found, P8-QUALITY-002)
//   ●  current       - the core's derived stage: the first one with nothing
//                      behind it, which is where the next action lands
//   ○  not started
//
// The warning is data rather than a guess: it reads the same quality issues the
// Data panel renders, so the mark and the panel can never disagree.
