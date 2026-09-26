/**
 * P9-F1-001: this panel moved out of CaseWorkspace.tsx verbatim.
 * The workspace holds the state; the panel is pure over its props.
 */

import { useState } from 'react'
import { type DraftFinding, acceptFinding } from '../api'
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'

export function DraftPanel({
  caseId,
  runId,
  draft,
  onAccepted,
}: {
  caseId: string
  runId: string
  draft: DraftFinding
  onAccepted: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function accept() {
    setBusy(true)
    setError(null)
    try {
      await acceptFinding(caseId, runId, draft)
      onAccepted()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="proposal">
      <p className="muted">
        {sourceLabel(draft.source, 'draft')} — accepting records a real finding,
        not_evaluated until validated
      </p>
      <p>{draft.statement}</p>
      <p className="muted">{draft.interpretation}</p>
      {draft.caveat && <p className="muted">caveat: {draft.caveat}</p>}
      {draft.grounds.length > 0 && (
        <ul className="grounds">
          {draft.grounds.map((ground) => (
            <li key={ground} className="chip">
              {ground}
            </li>
          ))}
        </ul>
      )}
      <button type="button" onClick={accept} disabled={busy}>
        {busy ? 'Recording…' : 'Accept as a finding'}
      </button>
      {error && <p role="alert">Could not record the finding: {error}</p>}
    </div>
  )
}
