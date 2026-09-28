/**
 * W2X-007: the capability the core has always had, given a surface of its own.
 *
 * The stage guidance says "Run an analysis", but the only doors into `/runs`
 * were the non-editable codegen and the EDA presets. The core's own engine
 * - arbitrary SQL or Python against the attached dataset - had no way in.
 * This is that way in: a textarea, the engine the code is for, and the run
 * endpoints the codegen panel already posts to.
 *
 * W2X-006's editor lives in GeneratePanel for the loop it serves; this one is
 * the analyst's own code from nothing. They share the wire, not the surface.
 */

import { useState } from 'react'
import {
  runPython,
  runSql,
} from '../api'
import { messageOf } from '../CaseList'
import { Button, surfaces } from '../lib/ui'

type RunKind = 'sql' | 'python'
export const RUN_KINDS: RunKind[] = ['sql', 'python']
export const RUN_KIND_LABELS: Record<RunKind, string> = {
  sql: 'SQL',
  python: 'Python',
}

export function RunCodePanel({
  caseId,
  datasetId,
  datasetName,
  onChanged,
}: {
  caseId: string
  datasetId: string
  datasetName: string
  onChanged: () => void
}) {
  const [kind, setKind] = useState<RunKind>('sql')
  const [code, setCode] = useState('')
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function run(event: React.FormEvent) {
    event.preventDefault()
    const text = code.trim()
    if (!text || running) return
    setRunning(true)
    setError(null)
    try {
      if (kind === 'python') {
        await runPython(caseId, datasetId, code)
      } else {
        await runSql(caseId, datasetId, code)
      }
      // The run persisted before this line, so the runs panel and the rail
      // read the case again and pick it up now (W-013).
      onChanged()
      setCode('')
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setRunning(false)
    }
  }

  return (
    <div className={surfaces.subpanel}>
      <h3 className={surfaces.subheading}>Run code on {datasetName}</h3>
      <fieldset>
        <legend className={surfaces.note}>Engine</legend>
        {RUN_KINDS.map((option) => (
          <label key={option}>
            <input
              type="radio"
              name="run-kind"
              aria-label={`${RUN_KIND_LABELS[option]} for a manual run`}
              value={option}
              checked={kind === option}
              onChange={() => setKind(option)}
              disabled={running}
            />{' '}
            {RUN_KIND_LABELS[option]}
          </label>
        ))}
      </fieldset>
      <form onSubmit={run}>
        <textarea
          aria-label={`${RUN_KIND_LABELS[kind]} to run`}
          value={code}
          onChange={(e) => setCode(e.target.value)}
          spellCheck={false}
          placeholder={kind === 'sql' ? 'SELECT …' : '# python'}
          disabled={running}
        />
        <Button type="submit" disabled={running || !code.trim()}>
          {running ? 'Running…' : 'Run'}
        </Button>
      </form>
      {error && <p role="alert">{`Run failed: ${error}`}</p>}
    </div>
  )
}
