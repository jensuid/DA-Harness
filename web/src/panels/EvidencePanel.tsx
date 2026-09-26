/**
 * P9-F1-001: this panel moved out of CaseWorkspace.tsx verbatim.
 * The workspace holds the state; the panel is pure over its props.
 */

import { type ClaimTrace, type EvidenceGraph, type EvidenceNode } from '../api'

export function EvidencePanel({
  evidence,
  error,
  empty,
}: {
  evidence: EvidenceGraph | null
  error: string | null
  empty: boolean
}) {
  return (
    <div className="panel">
      <h2>Evidence graph</h2>
      {empty ? (
        // A 400 is the case having no artifacts to graph. The core's sentence
        // names what would build one, and a young case is not a failed review.
        <p className="muted">{error}</p>
      ) : !evidence ? (
        <p className="muted">Loading the graph…</p>
      ) : (
        <GraphBody graph={evidence} />
      )}
      {!empty && error && (
        <p role="alert">The graph could not be read: {error}</p>
      )}
    </div>
  )
}

export function GraphBody({ graph }: { graph: EvidenceGraph }) {
  const byId = new Map(graph.nodes.map((node) => [node.id, node]))
  // A node with no edge is still part of the case: an attached dataset nothing
  // has queried yet, a plan nothing has run. Leaving it out would make the
  // graph say the case has less than it does.
  const linked = new Set<string>()
  for (const edge of graph.edges) {
    linked.add(edge.source)
    linked.add(edge.target)
  }
  const isolated = graph.nodes.filter((node) => !linked.has(node.id))

  return (
    <>
      <p className="muted">
        {graph.counts.datasets} dataset{graph.counts.datasets === 1 ? '' : 's'},{' '}
        {graph.counts.runs} run{graph.counts.runs === 1 ? '' : 's'},{' '}
        {graph.counts.findings} finding{graph.counts.findings === 1 ? '' : 's'},{' '}
        {graph.counts.charts} chart{graph.counts.charts === 1 ? '' : 's'},{' '}
        {graph.counts.plans} plan{graph.counts.plans === 1 ? '' : 's'}
      </p>
      <h3>Claims and what they rest on</h3>
      {graph.traces.length === 0 ? (
        <p className="muted">No findings yet, so nothing to trace.</p>
      ) : (
        <ul className="items">
          {graph.traces.map((trace) => (
            <li key={trace.finding_id}>
              <ClaimTraceRow
                trace={trace}
                orphan={graph.orphan_findings.includes(trace.finding_id)}
              />
            </li>
          ))}
        </ul>
      )}
      <h3>How each artifact was derived</h3>
      {graph.edges.length === 0 ? (
        <p className="muted">No derivations yet.</p>
      ) : (
        <ul className="items">
          {graph.edges.map((edge, i) => (
            <li key={i} className="muted">
              {nodePhrase(byId.get(edge.source))}{' '}
              {RELATIONS[edge.relation] ?? edge.relation}{' '}
              {nodePhrase(byId.get(edge.target))}
            </li>
          ))}
        </ul>
      )}
      {isolated.length > 0 && (
        <>
          <h3>Attached but not used yet</h3>
          <ul className="items">
            {isolated.map((node) => (
              <li key={node.id} className="muted">
                {node.kind}: {node.label}
              </li>
            ))}
          </ul>
        </>
      )}
    </>
  )
}

// One claim's path back to the data it stands on, as a chain of chips - the
// same shape the chat uses for a citation, so a reviewer reads it the same way.
export function ClaimTraceRow({
  trace,
  orphan,
}: {
  trace: ClaimTrace
  orphan: boolean
}) {
  return (
    <div className="run">
      <p>
        <strong>{trace.statement}</strong>
      </p>
      <p className="muted">
        status: {trace.validation_status}
        {orphan && (
          <span className="warn"> — a claim with no source: its run is gone</span>
        )}
      </p>
      <ul className="grounds chain">
        {trace.hops.map((hop, i) => (
          <li key={`${hop.id}-${i}`} className="chip">
            {hop.kind}: {hop.label}
          </li>
        ))}
      </ul>
    </div>
  )
}

// A node as a readable phrase. An edge may name an artifact the case no longer
// has - a finding anchored on a deleted run - and that is worth saying plainly
// rather than rendering as an id.
export function nodePhrase(node?: EvidenceNode): string {
  if (!node) return 'an artifact no longer in the case'
  return `${node.kind} “${node.label}”`
}

// The core's relations, as a reader would say them.
export const RELATIONS: Record<string, string> = {
  anchored_on: 'anchored on',
  queries: 'queries',
  rendered_from: 'rendered from',
  planned_from: 'planned from',
}

// Case history, as a review surface (P7-SHELL-009). The evidence graph answers
// what backs each claim; this answers the simpler question an analyst asks on
// reopening a case: what did I do here, and when? One line per artifact, in the
// order it happened - the case's own shape, visible without opening every
// panel and comparing timestamps.
//
// Like the graph, it is a read-only projection over persisted rows: nothing
// here writes, and the only way to change the timeline is to change the case
// through the endpoints that own the artifacts.
