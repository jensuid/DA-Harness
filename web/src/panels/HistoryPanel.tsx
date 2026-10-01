/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 *
 * W2X-008: the timeline is a record, and a record is consulted rather than
 * kept open. A case with one event is still telling its beginning, so the
 * panel stays open; once the case has happened, the panel collapses to its
 * count and the detail is one click away.
 */

import { CaseHistory } from '../api'
import { Skeleton, surfaces } from '../lib/ui'

export function HistoryPanel({
  history,
  error,
  missing,
}: {
  history: CaseHistory | null
  error: string | null
  missing: boolean
}) {
  return (
    <div className={surfaces.panel}>
      <h2 className={surfaces.heading}>Case history</h2>
      {missing ? (
        // A 404 means the case is unknown. The workspace loads its own case on
        // mount, so the header already reports it - this panel says so once,
        // as guidance, rather than reporting the same failure twice.
        <p className={surfaces.note}>The timeline could not be read: {error}</p>
      ) : !history ? (
        <>
          <p className={surfaces.note + ' visually-hidden'}>Loading the timeline…</p>
          <Skeleton shape="rows" count={4} />
        </>
      ) : (
        <HistoryBody history={history} />
      )}
      {!missing && error && (
        <p role="alert">The timeline could not be read: {error}</p>
      )}
    </div>
  )
}

// W2X-008: the collapsed summary the record group shows: the panel's name, so
// the toggle is found by the name an analyst knows it by, and the count,
// plural the way the body's own sentence is - so the collapsed group and the
// open panel cannot disagree about how much case there is. A timeline that
// could not be read is named by the failure rather than by its absence: the
// panel's guidance is the one place the 404 is said once, and a collapsed
// group that hid it would report a missing case as a case with no history.
export function historySummary(history: CaseHistory | null, error: string | null): string {
  if (error) return 'Case history — could not be read'
  if (!history) return 'Case history'
  const n = history.events.length
  return `Case history — ${n} event${n === 1 ? '' : 's'} in this case`
}

export function HistoryBody({ history }: { history: CaseHistory }) {
  // Only the kinds the case actually has are named, so a young case is not
  // described by a row of zeroes it would have to explain away.
  const parts: string[] = []
  for (const [key, [noun, verb]] of Object.entries(COUNT_KINDS)) {
    const n = history.counts[key] ?? 0
    if (n > 0) parts.push(`${n} ${noun}${n === 1 ? '' : 's'} ${verb}`)
  }
  return (
    <>
      <p className={surfaces.note}>
        {history.events.length} event{history.events.length === 1 ? '' : 's'} in
        this case{parts.length > 0 ? `, ${parts.join(', ')}` : ''} - oldest first
      </p>
      {history.events.length === 0 ? (
        // The core answers one event for a just-created case, so this is
        // defensive - but a projection that answered nothing would be a bug
        // worth seeing rather than an empty list worth hiding.
        <p className={surfaces.note}>Nothing has happened in this case yet.</p>
      ) : (
        <ul className={surfaces.panelList}>
          {history.events.map((event, i) => (
            <li key={`${event.artifact_id ?? event.kind}-${i}`}>
              <p>
                <time className={surfaces.note} dateTime={event.timestamp}>
                  {event.timestamp}
                </time>{' '}
                — {EVENT_KINDS[event.kind] ?? event.kind}: {event.label}
              </p>
              {event.detail && <p className={surfaces.note}>{event.detail}</p>}
            </li>
          ))}
        </ul>
      )}
    </>
  )
}

// Which count key names which event kind, as a noun and a verb, so the summary
// sentence pluralises the noun where English does and still speaks the same
// phrases the timeline below does.
export const COUNT_KINDS: Record<string, [string, string]> = {
  datasets: ['dataset', 'attached'],
  profiles: ['dataset', 'profiled'],
  plans: ['plan', 'created'],
  runs: ['run', 'executed'],
  charts: ['chart', 'rendered'],
  findings: ['finding', 'recorded'],
}

// The core's kind constants, as a reader would say them. An unknown kind is
// shown verbatim rather than dropped, so a newer core never makes the timeline
// quieter than it should be.
export const EVENT_KINDS: Record<string, string> = {
  case_created: 'case created',
  dataset_attached: 'dataset attached',
  dataset_profiled: 'dataset profiled',
  plan_created: 'plan created',
  run_executed: 'run executed',
  chart_rendered: 'chart rendered',
  finding_recorded: 'finding recorded',
}

// The agents, as surfaces: the analyst (P7-SHELL-003) and the reviewer
// (P7-SHELL-011). Every other panel in this workspace is a step; these are the
// sequences. Each proposes from the case's own artifacts, and the human's yes
// or no is a button - the write never happens without it, and the write then
// runs through the endpoint that owns it, so an agent earns no privilege a
// hand-run case has.
//
// Two panels on one page would be ambiguous if they shared their wording, so
// each role carries its own: a reader and a matcher can tell the analysis loop
// from the audit loop at a glance. The roles never talk to each other - each
// addresses the case, and the case's rows are the shared state.
