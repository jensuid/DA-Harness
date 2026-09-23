// Question refinement (P8-REFINE-007, AT-04, UX 12).
//
// The UX document's example shows the transformation explicitly:
//
//     YOUR QUESTION
//     Why are sales down?
//         ↓ AI suggestion
//     REFINED QUESTION
//     What factors explain the decline ... in Q2 vs Q1?
//         ↓
//     [Accept] [Edit] [Keep original]
//
// That is this panel. AI proposes and never silently rewrites: the original is
// shown beside the refinement, and accept / edit / keep original are the only
// three paths. The case's question moves only through the first two, and the
// original stays readable here after either of them.
//
// The panel sits in the orientation zone because it is about the question
// itself rather than about the work - it is the thing a case is organised
// around, and the overview beside it describes the case it organises.
import { useEffect, useState } from 'react'

import {
  acceptRefinement,
  editRefinement,
  getRefinement,
  type Refinement,
  proposeRefinement,
  rejectRefinement,
} from './api'
import { messageOf } from './CaseList'

// The two input boxes the walkthrough found near-identical are in different
// zones; this one is not a chat box, so its label says what it does.
const EDIT_LABEL = 'Refined question, edited'

export function RefinePanel({
  caseId,
  question,
  onChanged,
}: {
  caseId: string
  question: string
  onChanged: () => void
}) {
  const [proposal, setProposal] = useState<Refinement | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState('')

  async function load() {
    setError(null)
    try {
      const stored = await getRefinement(caseId)
      setProposal(stored)
      setEditing(false)
    } catch (err) {
      setError(messageOf(err))
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  async function propose() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const made = await proposeRefinement(caseId)
      setProposal(made)
      setDraft(made.refined_question)
      setEditing(false)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function decide(
    action: () => Promise<Refinement>,
    failure: string,
  ) {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const decided = await action()
      setProposal(decided)
      setEditing(false)
      // The case's own question may have moved; the workspace reloads it from
      // the same place it read the original.
      onChanged()
    } catch (err) {
      setError(`${failure}: ${messageOf(err)}`)
    } finally {
      setBusy(false)
    }
  }

  async function saveEdit() {
    const text = draft.trim()
    if (!text) return
    if (!proposal) return
    await decide(
      () => editRefinement(caseId, proposal.id, text),
      'Could not apply the edit',
    )
  }

  const pending = proposal?.status === 'pending'
  const declined = proposal?.status === 'declined'
  const decided =
    proposal && (proposal.status === 'accepted' || proposal.status === 'rejected' || proposal.status === 'edited')

  return (
    <div className="panel">
      <h2>Refine the question</h2>
      <p className="muted">
        A vague question is sharpened with what the profile measured - real
        columns, measured ranges - and nothing is changed until you decide.
      </p>

      {error && <p role="alert">Something went wrong: {error}</p>}

      {!proposal && (
        <div className="row">
          <button
            type="button"
            onClick={() => void propose()}
            disabled={busy || !question.trim()}
            aria-label="Propose a refinement of the question"
          >
            {busy ? 'Reading the profile…' : 'Propose a refinement'}
          </button>
          {!question.trim() && (
            <span className="muted">the case has no question yet</span>
          )}
        </div>
      )}

      {proposal && (
        <div>
          {/* UX 12: the transformation is shown, both halves of it. The
              original is never replaced in place, even after an accept that
              moved the case's question to the refined one. */}
          <h3>Your question</h3>
          <p className="question">{proposal.original_question}</p>

          {declined ? (
            <p className="muted">
              DAH looked at the question and the profiled data and had nothing
              to add: the question is already specific enough, or the data
              offers nothing that would make it more answerable.
            </p>
          ) : (
            <>
              <p className="muted" aria-label="AI suggestion">
                ↓ AI suggestion ({proposal.source})
              </p>
              <h3>Refined question</h3>
              {editing ? (
                <label className="subpanel">
                  <textarea
                    aria-label={EDIT_LABEL}
                    value={draft}
                    onChange={(e) => setDraft(e.target.value)}
                    disabled={busy}
                    rows={3}
                  />
                </label>
              ) : (
                <p className="question">
                  {proposal.status === 'edited'
                    ? proposal.edited_question
                    : proposal.refined_question}
                </p>
              )}

              {proposal.rationale && (
                <details>
                  <summary>Why these changes</summary>
                  <p>{proposal.rationale}</p>
                  {proposal.grounds.length > 0 && (
                    <ul className="items">
                      {proposal.grounds.map((ground, index) => (
                        <li key={index}>
                          <strong>{ground.name}</strong> - {ground.detail}
                        </li>
                      ))}
                    </ul>
                  )}
                </details>
              )}

              {pending && !editing && (
                // The three paths AT-04 names, and no fourth: there is no
                // button that rewrites the original without asking first.
                <div className="row">
                  <button
                    type="button"
                    onClick={() => void decide(
                      () => acceptRefinement(caseId, proposal.id),
                      'Could not accept the refinement',
                    )}
                    disabled={busy}
                  >
                    Accept
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      setDraft(proposal.refined_question)
                      setEditing(true)
                    }}
                    disabled={busy}
                  >
                    Edit
                  </button>
                  <button
                    type="button"
                    onClick={() => void decide(
                      () => rejectRefinement(caseId, proposal.id),
                      'Could not keep the original',
                    )}
                    disabled={busy}
                  >
                    Keep original
                  </button>
                </div>
              )}

              {pending && editing && (
                <div className="row">
                  <button
                    type="button"
                    onClick={() => void saveEdit()}
                    disabled={busy || !draft.trim()}
                  >
                    {busy ? 'Applying…' : 'Apply my edit'}
                  </button>
                  <button
                    type="button"
                    onClick={() => setEditing(false)}
                    disabled={busy}
                  >
                    Cancel
                  </button>
                </div>
              )}

              {decided && (
                <p className="muted">
                  {proposal.status === 'accepted' &&
                    'Accepted - the case now carries the refined question.'}
                  {proposal.status === 'edited' &&
                    'Edited - your wording replaced both the original and the proposal.'}
                  {proposal.status === 'rejected' &&
                    'Kept the original question.'}{' '}
                  The original above is still readable, and in the case's
                  history.
                </p>
              )}

              {decided && (
                <div className="row">
                  <button
                    type="button"
                    onClick={() => void propose()}
                    disabled={busy}
                  >
                    Propose again
                  </button>
                </div>
              )}
            </>
          )}
        </div>
      )}
    </div>
  )
}
