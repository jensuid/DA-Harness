/**
 * P9-F1-001: this panel moved out of CaseWorkspace.tsx verbatim.
 * The workspace holds the state; the panel is pure over its props.
 */

import { CaseHistory } from '../api'

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
    <div className="panel">
      <h2>Case history</h2>
      {missing ? (
        // A 404 means the case is unknown. The workspace loads its own case on
        // mount, so the header already reports it - this panel says so once, as
        // guidance, rather than reporting the same failure twice.
        <p className="muted">The timeline could not be read: {error}</p>
      ) : !history ? (
        <p className="muted">Loading the timeline…</p>
      ) : (
        <HistoryBody history={history} />
      )}
      {!missing && error && (
        <p role="alert">The timeline could not be read: {error}</p>
      )}
    </div>
  )
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
      <p className="muted">
        {history.events.length} event{history.events.length === 1 ? '' : 's'} in
        this case{parts.length > 0 ? `, ${parts.join(', ')}` : ''} - oldest first
      </p>
      {history.events.length === 0 ? (
        // The core answers one event for a just-created case, so this is
        // defensive - but a projection that answered nothing would be a bug
        // worth seeing rather than an empty list worth hiding.
        <p className="muted">Nothing has happened in this case yet.</p>
      ) : (
        <ul className="items">
          {history.events.map((event, i) => (
            <li key={`${event.artifact_id ?? event.kind}-${i}`}>
              <p>
                <time className="muted" dateTime={event.timestamp}>
                  {event.timestamp}
                </time>{' '}
                — {EVENT_KINDS[event.kind] ?? event.kind}: {event.label}
              </p>
              {event.detail && <p className="muted">{event.detail}</p>}
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
