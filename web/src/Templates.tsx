import { useEffect, useState } from 'react'
import {
  type Template,
  type TemplateShape,
  createCaseFromTemplate,
  deleteTemplate,
  listTemplates,
  promoteCaseToTemplate,
} from './api'
import { messageOf } from './CaseList'
import { Button, Skeleton, surfaces } from './lib/ui'

// Templates are the other thing a user comes to the front door for: the shape
// of an investigation that was worked out once, offered to the next one. They
// are not case children and outlive the case they came from, so they sit on
// the case-list screen rather than inside a workspace (P7-SHELL-005).
//
// Every write posts to its endpoint and the list reloads after it rather than
// mutating its own copy, so what it shows is what the core has - the same
// discipline the case list keeps.
export function Templates({ onOpen }: { onOpen: (caseId: string) => void }) {
  const [templates, setTemplates] = useState<Template[]>([])
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  async function reload() {
    setLoading(true)
    setError(null)
    try {
      setTemplates(await listTemplates())
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    void reload()
  }, [])

  return (
    <section className={surfaces.panel}>
      <h2 className={surfaces.heading}>Templates</h2>
      <p className={surfaces.note}>
        A saved case's plan, proposals and findings, offered to the next case
        that asks the same kind of question. Only the shape travels - no data,
        runs or findings - and every step it proposes is still yours to accept.
      </p>
      {error && <p role="alert">Failed to load templates: {error}</p>}
      {loading && (
        // SKEL: the template list's read is in flight; the shape is the same
        // three rows the case list waits on, the sentence still announced.
        <>
          <p className={surfaces.note + ' visually-hidden'}>Loading…</p>
          <Skeleton shape="rows" count={3} />
        </>
      )}
      {!loading && !error && templates.length === 0 && (
        <p className={surfaces.note}>No templates yet - save one from a case.</p>
      )}
      <ul className="case-list">
        {templates.map((template) => (
          <li key={template.id}>
            <TemplateRow template={template} onOpen={onOpen} onChanged={() => void reload()} />
          </li>
        ))}
      </ul>
    </section>
  )
}

// One template: what it seeds, and what kind of investigation it carries. The
// shape summary is the point - a name alone cannot say whether a template is a
// finished method or a question-only skeleton.
function TemplateRow({
  template,
  onOpen,
  onChanged,
}: {
  template: Template
  onOpen: (caseId: string) => void
  onChanged: () => void
}) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function start() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      // Only the question and the dataset label are copied; the seeded case
      // starts clean and offers the template's shape as proposals.
      const created = await createCaseFromTemplate(template.id)
      onOpen(created.id)
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function retire() {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await deleteTemplate(template.id)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="case">
      <p className="case-question">{template.name}</p>
      <p className="case-dataset">
        {template.question} — {template.dataset}
      </p>
      <ShapeSummary shape={template.shape} />
      <div className={surfaces.buttonRow}>
        <Button
          type="button"
          onClick={start}
          variant="small"
          disabled={busy}
          aria-label={`Start a case from ${template.name}`}
        >
          {busy ? 'Starting…' : 'Start a case from this'}
        </Button>
        <Button
          type="button"
          onClick={retire}
          variant="smallDanger"
          disabled={busy}
          aria-label={`Retire the template ${template.name}`}
        >
          Retire
        </Button>
      </div>
      {error && (
        <p role="alert" className="warn">
          The action failed: {error}
        </p>
      )}
    </div>
  )
}

// A shape says what the template carries. A template without one was promoted
// from a case that had nothing to capture (or before shapes existed), so it
// says so: showing zeroes would imply an empty investigation rather than an
// unrecorded one.
function ShapeSummary({ shape }: { shape: TemplateShape | null }) {
  if (!shape) {
    return <p className={surfaces.note}>A question-only skeleton - no shape was captured.</p>
  }
  const parts = [
    `${shape.proposals.length} proposal${shape.proposals.length === 1 ? '' : 's'}`,
  ]
  if (shape.findings.length > 0) {
    const verdicts = shape.findings
      .map((finding) => finding.validation_status)
      // A status is the finding's own verdict word; the summary counts each
      // kind so a reader sees how much of the shape survived validation.
      .reduce<Record<string, number>>((counts, status) => {
        counts[status] = (counts[status] ?? 0) + 1
        return counts
      }, {})
    parts.push(
      `${shape.findings.length} finding${
        shape.findings.length === 1 ? '' : 's'
      } (${Object.entries(verdicts)
        .map(([status, count]) => `${count} ${status}`)
        .join(', ')})`,
    )
  }
  return <p className={surfaces.note}>Carries {parts.join(', ')}</p>
}

// The workspace's promotion affordance (P7-SHELL-005). The name is optional -
// the core defaults it to the case's question - because the common gesture
// needs no second prompt, and a failure leaves the workspace usable.
export function PromoteTemplate({ caseId, question }: { caseId: string; question: string }) {
  const [name, setName] = useState('')
  const [busy, setBusy] = useState(false)
  const [saved, setSaved] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  async function save(event: React.FormEvent) {
    event.preventDefault()
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      const template = await promoteCaseToTemplate(caseId, name)
      setSaved(template.name)
      setName('')
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className={surfaces.panel}>
      <h2 className={surfaces.heading}>Save as a template</h2>
      <p className={surfaces.note}>
        Another case can start from this one's plan, proposals and findings.
        Nothing is copied but the shape - the next case still decides whether to
        accept each step.
      </p>
      <form onSubmit={save}>
        <label htmlFor={`template-name-${caseId}`}>
          Template name (optional - the case's question is used when blank)
        </label>
        <input
          id={`template-name-${caseId}`}
          aria-label="Template name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder={question}
          disabled={busy}
        />
        <Button type="submit" disabled={busy}>
          {busy ? 'Saving…' : 'Save as a template'}
        </Button>
      </form>
      {saved && (
        <p role="status">
          Saved as <strong>{saved}</strong> - it is on the case-list screen now.
        </p>
      )}
      {error && <p role="alert">Could not save the template: {error}</p>}
    </div>
  )
}
