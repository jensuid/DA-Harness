/**
 * P9-F1-001: this panel moved out of CaseWorkspace.tsx verbatim.
 * The workspace holds the state; the panel is pure over its props.
 */

import { useState } from 'react'
import {
  type Dataset,
  type GeneratedCode,
  type Profile,
  generateCode,
  runPython,
  runSql,
} from "../api"
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'

type GenerateKind = 'sql' | 'python'
export const GENERATE_KINDS: GenerateKind[] = ['sql', 'python']
export const GENERATE_KIND_LABELS: Record<GenerateKind, string> = {
  sql: 'SQL',
  python: 'Python',
}

// One case as the loop the core walks: attach and profile data, propose the
// computation that would answer the question, run it, read what it shows,
// draft the finding it supports, and validate that finding. Every assistant
// panel proposes; the buttons that write state post to the endpoints that own
// it - the runs endpoint for execution, the findings endpoint for a claim - so
// the split stays structural rather than becoming a UI flag.

export function GeneratePanel({
  caseId,
  dataset,
  profile,
  onChanged,
}: {
  caseId: string
  dataset: Dataset
  profile: Profile | undefined
  // W-013: a run the panel posts lands in the runs list the workspace owns, so
  // the panel reports it the way every other writing panel does - otherwise the
  // analyst re-runs a computation that already succeeded, and the history the
  // core holds and the list the shell shows disagree.
  onChanged: () => void
}) {
  const [question, setQuestion] = useState('')
  const [proposal, setProposal] = useState<GeneratedCode | null>(null)
  const [kind, setKind] = useState<GenerateKind>('sql')
  const [busy, setBusy] = useState(false)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function propose(event: React.FormEvent) {
    event.preventDefault()
    const text = question.trim()
    if (!text || busy) return
    setBusy(true)
    setError(null)
    try {
      setProposal(await generateCode(caseId, dataset.id, text, kind))
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function run() {
    if (!proposal || running) return
    setRunning(true)
    setError(null)
    try {
      // The proposal's own kind decides the endpoint, not the selector's
      // current value: a proposal is generated once and the code in it is
      // for one engine, so the run always matches what the analyst read.
      if (proposal.kind === 'python') {
        await runPython(caseId, dataset.id, proposal.code)
      } else {
        await runSql(caseId, dataset.id, proposal.code)
      }
      // W-013: the run persisted before this line, so the runs panel, the rail
      // and the evidence graph read the case again and pick it up now - the
      // analyst sees the run land rather than having to reopen the case.
      onChanged()
      setProposal(null)
      setQuestion('')
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setRunning(false)
    }
  }

  if (!profile) {
    return <p className="muted">Profile the dataset before generating code.</p>
  }

  return (
    <div className="subpanel">
      <h3>Ask for the computation</h3>
      <fieldset>
        <legend className="muted">Engine</legend>
        {GENERATE_KINDS.map((option) => (
          <label key={option}>
            <input
              type="radio"
              name="generate-kind"
              aria-label={`${GENERATE_KIND_LABELS[option]} for code generation`}
              value={option}
              checked={kind === option}
              onChange={() => setKind(option)}
              disabled={busy}
            />{' '}
            {GENERATE_KIND_LABELS[option]}
          </label>
        ))}
      </fieldset>
      <form onSubmit={propose}>
        <input
          aria-label="Question for code generation"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="What would you like to know?"
          disabled={busy}
        />
        <button type="submit" disabled={busy || !question.trim()}>
          {busy ? 'Generating…' : 'Generate code'}
        </button>
      </form>
      {error && <p role="alert">Generation failed: {error}</p>}
      {proposal && (
        <div className="proposal">
          <p className="muted">
            {sourceLabel(proposal.source, 'proposal')} — reads{' '}
            {proposal.columns_used.join(', ')}
          </p>
          <p>{proposal.explanation}</p>
          <pre>{proposal.code}</pre>
          <button type="button" onClick={run} disabled={running}>
            {running ? 'Running…' : 'Run this'}
          </button>
        </div>
      )}
    </div>
  )
}

// The plan's own contents (UX 17, AT-33's "current task"): the planner
// persists sub-questions, hypotheses and steps, and rendering them is what
// tells the analyst what to run next - the plan is the loop's to-do list, and
// until it was rendered here it was written but never read back.
//
// W-011 (FIX-PLAN-003): a case with no plan was told to "generate one" by a
// panel that offered no control, so the plan stage was only finishable from a
// terminal. The POST is the panel's own now - busy while the planner works,
// the endpoint's own reason as a sentence on a refusal (a 400 is an
// unprofiled dataset, the step before this one), and a success that reloads
// the plan and the case so the rail and the panel move together.
