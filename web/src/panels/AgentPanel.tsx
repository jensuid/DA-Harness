/**
 * P9-F1-001: this panel moved out of CaseWorkspace.tsx verbatim.
 * The workspace holds the state; the panel is pure over its props.
 */

import { useState } from 'react'
import {
  type AgentRole,
  type AgentState,
  type AgentStep,
  approveAgentStep,
  approveRoleAgentStep,
  getAgentState,
  getRoleAgentState,
  proposeAgentStep,
  proposeRoleAgentStep,
  rejectAgentStep,
  rejectRoleAgentStep,
} from "../api"
import { sourceLabel } from '../sourceLabel'
import { messageOf } from '../CaseList'

export const AGENT_COPY: Record<AgentRole, {
  title: string
  blurb: string
  loading: string
  propose: string
  repropose: string
  idle: string
  stopped: string
  history: string
  error: string
}> = {
  analyst: {
    title: 'Agent',
    blurb:
      'A plan that executes itself one approved write at a time. It proposes ' +
      'the next step from what the case already has; nothing is written until ' +
      'you approve it, and every write goes through the same endpoint a ' +
      'hand-written call would.',
    loading: "Loading the agent's state\u2026",
    propose: 'Propose the next step',
    repropose: 'Re-derive the next step',
    idle: 'Nothing is pending. Propose a step, or work the panels below by hand.',
    stopped: 'The agent stopped:',
    history: 'What the agent has done',
    error: 'The agent could not proceed:',
  },
  reviewer: {
    title: 'Reviewer',
    blurb:
      "A second agent whose only method is EVALUATE: it takes each finding " +
      "this case recorded and proposes auditing the run that backs it - the " +
      "claim is the finding's own statement, the code the run's own query. " +
      "The verdict is recorded beside the finding and never changes the " +
      "finding's own validation status, because a rerun and an audit are two " +
      "different claims.",
    loading: "Loading the reviewer's state\u2026",
    propose: 'Propose the next audit',
    repropose: 'Re-derive the next audit',
    idle:
      'Nothing is pending review. Either the case has no findings yet, or ' +
      'every finding whose run still carries its code has been audited.',
    stopped: 'The reviewer stopped:',
    history: 'What the reviewer has done',
    error: 'The reviewer could not proceed:',
  },
}

export function AgentPanel({
  caseId,
  role,
  agent,
  onAgent,
  onChanged,
}: {
  caseId: string
  role: AgentRole
  agent: AgentState | null
  onAgent: (state: AgentState) => void
  onChanged: () => void
}) {
  const copy = AGENT_COPY[role]
  const [busy, setBusy] = useState(false)
  const [reason, setReason] = useState('')
  const [error, setError] = useState<string | null>(null)
  // The analyst is the legacy /agent family and the reviewer is the role
  // family; both answer the same four verbs. The analyst keeps calling the
  // functions it always did, so nothing about its behaviour changes.
  const calls =
    role === 'reviewer'
      ? {
          read: () => getRoleAgentState(caseId, role),
          propose: () => proposeRoleAgentStep(caseId, role),
          approve: (id: string) => approveRoleAgentStep(caseId, role, id),
          reject: (id: string, why: string) =>
            rejectRoleAgentStep(caseId, role, id, why),
        }
      : {
          read: () => getAgentState(caseId),
          propose: () => proposeAgentStep(caseId),
          approve: (id: string) => approveAgentStep(caseId, id),
          reject: (id: string, why: string) => rejectAgentStep(caseId, id, why),
        }

  async function refresh() {
    setError(null)
    try {
      onAgent(await calls.read())
    } catch (err) {
      setError(messageOf(err))
    }
  }

  async function propose() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      // Idempotent by contract: a pending step comes back unchanged, so an
      // impatient second click is a no-op rather than a second write.
      onAgent(await calls.propose())
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function decide(approve: boolean) {
    const stepId = agent?.pending?.id
    if (busy || !stepId) return
    setBusy(true)
    setError(null)
    try {
      if (approve) {
        // Approving runs the step and the response carries the next proposal,
        // so there is no second call to see what comes next.
        onAgent(await calls.approve(stepId))
      } else {
        onAgent(await calls.reject(stepId, reason))
        setReason('')
      }
      // The write changed the case's artifacts, so the whole workspace reloads -
      // a rejected draft leaves no finding behind, and an approved run appears
      // in the Runs panel.
      onChanged()
    } catch (err) {
      // A 409 means the step is no longer the case's pending one: another
      // approval moved the case on while this page sat open. Resync, then show
      // the sentence - refresh clears the error, so it runs first or the
      // message would vanish a tick after it appeared.
      await refresh()
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  if (!agent) {
    return (
      <div className="panel">
        <h2>{copy.title}</h2>
        <p className="muted">{copy.loading}</p>
      </div>
    )
  }

  const pending = agent.pending
  const finished = !pending && agent.history.some((s) => s.kind === 'end')
  const end = finished ? agent.history[agent.history.length - 1] : null

  return (
    <div className="panel">
      <h2>{copy.title}</h2>
      <p className="muted">{copy.blurb}</p>
      <div className="row">
        <button
          type="button"
          onClick={propose}
          disabled={busy}
          className="small"
        >
          {busy ? 'Working…' : pending ? copy.repropose : copy.propose}
        </button>
      </div>
      {error && (
        <p role="alert">{copy.error} {error}</p>
      )}
      {pending ? (
        <div className="proposal">
          <p className="muted">
            {sourceLabel(pending.source, 'proposal')} — approve to run it, or
            reject with your reason
          </p>
          <p><strong>{stepSentence(pending)}</strong></p>
          <div className="row">
            <button
              type="button"
              onClick={() => void decide(true)}
              disabled={busy}
              className="small"
            >
              {busy ? 'Running…' : 'Approve and run'}
            </button>
            <button
              type="button"
              onClick={() => void decide(false)}
              disabled={busy}
              className="small"
            >
              {busy ? 'Recording…' : 'Reject'}
            </button>
          </div>
          <input
            aria-label="Reason for rejecting (optional)"
            value={reason}
            onChange={(e) => setReason(e.target.value)}
            placeholder="Why this step is wrong - recorded with it"
            disabled={busy}
          />
        </div>
      ) : end ? (
        <p className="muted">
          {copy.stopped}{' '}
          {end.note || 'no further step is derivable from the case as it stands'}
        </p>
      ) : (
        <p className="muted">{copy.idle}</p>
      )}
      {agent.history.length > 0 && (
        <div className="subpanel">
          <h3>{copy.history}</h3>
          <ul className="items">
            {agent.history
              .slice()
              .reverse()
              .map((step) => (
                <li key={step.id} className="run">
                  <StepStatus step={step} />
                </li>
              ))}
          </ul>
        </div>
      )}
    </div>
  )
}

// What a step will do, as a sentence built from the payload the core settled at
// proposal time. The human approves something concrete, not a promise - and
// the sentence is the same one the step's own write produced, so the proposal
// and the record cannot drift apart.
export function stepSentence(step: AgentStep): string {
  const p = step.payload
  const str = (key: string) => String(p[key] ?? '')
  switch (step.kind) {
    case 'profile':
      return `Profile ${str('filename') || 'the attached dataset'}`
    case 'plan':
      return 'Plan the analysis from the profile'
    case 'analyze':
      return `Run ${str('kind') || 'the'} analysis${p.variant ? ` (variant ${p.variant})` : ''}`
    case 'interpret':
      return 'Interpret the last run'
    case 'accept':
      return `Accept the draft as a finding${str('statement') ? `: ${str('statement')}` : ''}`
    case 'chart':
      return `Render a ${str('kind') || 'bar'} chart of ${str('y')} by ${str('x')}`
    case 'validate':
      return 'Validate the finding'
    case 'evaluate':
      // The reviewer's only step: the claim is the finding's own statement,
      // so the human approves an audit of something concrete.
      return str('claim')
        ? `Audit the finding: ${str('claim')}`
        : 'Audit the finding against the nine axes'
    case 'end':
      return step.note || 'stop'
    default:
      return step.kind
  }
}

export function StepStatus({ step }: { step: AgentStep }) {
  const mark = step.status === 'done' ? '✓' : step.status === 'rejected' ? '✗' : '○'
  return (
    <p>
      <span className={`verdict ${step.status === 'done' ? 'pass' : step.status === 'rejected' ? 'fail' : 'concern'}`}>
        {mark} {step.kind}
      </span>
      <span className="muted"> — {step.note || stepSentence(step)}</span>
      {step.status === 'rejected' && step.note && (
        <span className="muted"> (rejected: {step.note})</span>
      )}
    </p>
  )
}
