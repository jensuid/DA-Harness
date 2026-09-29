/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useState } from 'react'
import { type DraftFinding, acceptFinding } from '../api'
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'
import { Button, surfaces } from '../lib/ui'

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
    <div className={surfaces.proposal}>
      <p className={surfaces.note}>
        {sourceLabel(draft.source, 'draft')}
      </p>
      <p className={surfaces.note}>
        Accepting records a real finding, not_evaluated until validated
      </p>
      <p>{draft.statement}</p>
      <p className={surfaces.note}>{draft.interpretation}</p>
      {draft.caveat && <p className={surfaces.note}>caveat: {draft.caveat}</p>}
      {draft.grounds.length > 0 && (
        <ul className={surfaces.panelList}>
          {draft.grounds.map((ground) => (
            <li key={ground} className="chip">
              {ground}
            </li>
          ))}
        </ul>
      )}
      <Button type="button" onClick={accept} disabled={busy}>
        {busy ? 'Recording…' : 'Accept as a finding'}
      </Button>
      {error && <p role="alert">Could not record the finding: {error}</p>}
    </div>
  )
}
