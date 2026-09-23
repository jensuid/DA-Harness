// The loop's exit (P8-DECISION-008, UX 46): the case's decision view.
//
// Until this panel existed, a validated finding was the end of the road - the
// verdict was computed, shown, and discarded, and nothing closed over what the
// loop had established. This is that close: the question the case asked, the
// findings validation stood behind, the uncertainty that survived them, the
// claims still open, the implications the analyst writes, and the case's
// export - which had no surface in the shell at all, and whose natural home is
// the decision it sits beside (UX 48's flow ends at Decision Support -> Export).
//
// What this panel is *not* is as important as what it is. DAH informs
// decisions; it does not make them. Nothing here scores, ranks or recommends
// anything: uncertainty is the checks that did not pass, each carried with its
// own sentence (UX 44's rule - structured signals, not confidence), and the
// implications are the analyst's own words, written by the analyst. No engine
// drafts them, because a tool that drafts the action to take is a tool making
// the decision.
import { useEffect, useState } from 'react'

import {
  type DecisionView,
  exportCasePackage,
  getDecision,
  putDecision,
} from './api'
import { messageOf } from './CaseList'

const STATUS_MARKS: Record<string, string> = {
  supported: '✓',
  partially_supported: '⚠',
}

export function DecisionPanel({
  caseId,
  onChanged,
}: {
  caseId: string
  onChanged: () => void
}) {
  const [view, setView] = useState<DecisionView | null>(null)
  const [missing, setMissing] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function load() {
    setError(null)
    try {
      setView(await getDecision(caseId))
      setMissing(false)
    } catch (err) {
      // A case that never produced a decision view answers 404; the panel says
      // so rather than rendering an empty decision.
      setMissing(true)
      setError(messageOf(err))
    }
  }

  useEffect(() => {
    void load()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [caseId])

  if (missing) {
    return (
      <div className="panel">
        <h2>Decision</h2>
        <p className="muted">
          The decision view could not be read: {error ?? 'the case has no decision yet'}
        </p>
      </div>
    )
  }
  if (!view) {
    return (
      <div className="panel">
        <h2>Decision</h2>
        <p className="muted">Reading the case's decision…</p>
      </div>
    )
  }

  const keyFindings = view.findings
  const unresolved = keyFindings.reduce(
    (total, finding) => total + finding.uncertainty.length,
    0,
  )

  return (
    <div className="panel">
      <h2>Decision</h2>
      <p className="muted">
        What this case established, and what it did not. DAH informs decisions;
        it does not make them.
      </p>

      <div className="subpanel">
        <h3>Question</h3>
        <p>{view.question}</p>
        {view.purpose && <p className="muted">Purpose: {view.purpose}</p>}
      </div>

      <div className="subpanel">
        <h3>Key findings</h3>
        {keyFindings.length === 0 ? (
          <p className="muted">
            No finding validation has stood behind yet. {guidance(view)}
          </p>
        ) : (
          <ol className="items">
            {keyFindings.map((finding) => (
              <li key={finding.id} className="run">
                <p>
                  <strong>{STATUS_MARKS[finding.validation_status] ?? '●'}</strong>{' '}
                  {finding.statement}
                </p>
                <p className="muted">validation: {finding.validation_status}</p>
                {finding.caveat && (
                  <p className="warn">caveat: {finding.caveat}</p>
                )}
              </li>
            ))}
          </ol>
        )}
      </div>

      <div className="subpanel">
        <h3>Uncertainty</h3>
        {unresolved === 0 ? (
          <p className="muted">
            Every check validation measured passed. Nothing here is a score -
            it is the checks that did not pass, and there are none.
          </p>
        ) : (
          <ul className="items">
            {keyFindings
              .flatMap((finding) =>
                finding.uncertainty.map((check) => ({ finding, check })),
              )
              .map(({ finding, check }) => (
                <li
                  key={finding.id + check.dimension + check.detail}
                  className={check.hard ? 'fail' : 'warn'}
                >
                  {check.hard ? '✗' : '⚠'} {check.dimension} — {check.detail}
                  <span className="muted"> (from “{finding.statement}”)</span>
                </li>
              ))}
          </ul>
        )}
        {view.open_items.length > 0 && (
          <>
            <h3>Still open</h3>
            <ul className="items">
              {view.open_items.map((item) => (
                <li key={item.id} className="run">
                  <p>{item.statement}</p>
                  <p className="muted">validation: {item.validation_status}</p>
                  <ul className="items">
                    {item.reasons.map((reason, index) => (
                      <li key={index} className="warn">
                        ⚠ {reason}
                      </li>
                    ))}
                  </ul>
                </li>
              ))}
            </ul>
          </>
        )}
      </div>

      <Implications caseId={caseId} view={view} onChanged={onChanged} />

      <Export caseId={caseId} question={view.question} />
    </div>
  )
}

function guidance(view: DecisionView): string {
  if (view.open_items.length === 0) {
    return 'A finding recorded and validated is what this section closes over.'
  }
  const awaiting = view.open_items.filter(
    (item) => item.validation_status === 'not_evaluated',
  )
  if (awaiting.length === view.open_items.length) {
    return 'Validate the finding - the loop’s last step has not run.'
  }
  return 'A claim was refused by validation; its reasons are listed under Still open.'
}

// The only write the decision accepts, and the only thing in the panel a human
// authors. Nothing proposes these and nothing derives them.
function Implications({
  caseId,
  view,
  onChanged,
}: {
  caseId: string
  view: DecisionView
  onChanged: () => void
}) {
  const [draft, setDraft] = useState<string[]>(view.implications)
  const [saved, setSaved] = useState<string[] | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // The server is the source of truth: a decision written elsewhere (the API,
  // a restored export) shows up on reload rather than being overwritten by a
  // stale draft.
  useEffect(() => {
    setDraft(view.implications)
    setSaved(view.implications)
  }, [view.implications])

  const dirty = draft.join('\n') !== (saved ?? view.implications).join('\n')

  async function save() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const trimmed = draft.map((entry) => entry.trim()).filter((entry) => entry.length > 0)
      const written = await putDecision(caseId, trimmed)
      setDraft(written.implications)
      setSaved(written.implications)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="subpanel">
      <h3>Potential implications</h3>
      <p className="muted">
        Yours to write - the analysis informs them, it does not draft them.
      </p>
      <ul className="items">
        {draft.map((entry, index) => (
          <li key={index} className="row">
            <input
              aria-label={`Implication ${index + 1}`}
              value={entry}
              onChange={(event) =>
                setDraft(draft.map((value, at) => (at === index ? event.target.value : value)))
              }
              disabled={busy}
            />
            <button
              type="button"
              onClick={() => setDraft(draft.filter((_, at) => at !== index))}
              disabled={busy}
              className="small"
              aria-label={`Remove implication ${index + 1}`}
            >
              Remove
            </button>
          </li>
        ))}
      </ul>
      <button
        type="button"
        onClick={() => setDraft([...draft, ''])}
        disabled={busy}
        className="small"
      >
        Add implication
      </button>
      {error && <p role="alert">Could not save the implications: {error}</p>}
      <div className="row">
        <button type="button" onClick={save} disabled={busy || !dirty}>
          {busy ? 'Saving…' : 'Save implications'}
        </button>
        {dirty && <span className="muted">unsaved edits</span>}
        {saved && saved.length > 0 && !dirty && (
          <span className="muted">{saved.length} saved</span>
        )}
      </div>
    </div>
  )
}

// UX 46 closes on the export, and UX 47 wants the package to carry the
// analytical structure. The shell had no export surface at all before this
// panel - the endpoint existed, but nothing reached it.
function Export({ caseId, question }: { caseId: string; question: string }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function download() {
    setBusy(true)
    setError(null)
    try {
      const blob = await exportCasePackage(caseId)
      const url = URL.createObjectURL(blob)
      const anchor = document.createElement('a')
      anchor.href = url
      anchor.download = `${slug(question) || 'analysis-case'}.json`
      document.body.appendChild(anchor)
      anchor.click()
      anchor.remove()
      URL.revokeObjectURL(url)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="subpanel">
      <h3>Export</h3>
      <p className="muted">
        A self-contained package: the findings, their validation, the evidence
        and the decision - restorable anywhere with fresh IDs.
      </p>
      <button type="button" onClick={download} disabled={busy}>
        {busy ? 'Exporting…' : 'Export analysis case'}
      </button>
      {error && <p role="alert">Export failed: {error}</p>}
    </div>
  )
}

function slug(text: string): string {
  return text
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
    .slice(0, 60)
}
