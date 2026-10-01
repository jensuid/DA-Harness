/**
 * P9-F2-002: this panel is built on the token layer, not on the class names
 * the hand-written CSS defined. The workspace still holds the state; the
 * panel is still pure over its props.
 */

import { useId, useState } from 'react'
import { type Dataset, type Profile, attachDataset, profileDataset } from '../api'
import { messageOf } from '../CaseList'
import { Button, Skeleton, surfaces } from '../lib/ui'
import { QualityList } from './CaseOverview'
import { GeneratePanel } from './GeneratePanel'
import { RunCodePanel } from './RunCodePanel'

export function DataPanel({
  caseId,
  datasets,
  profiles,
  loading,
  onChanged,
}: {
  caseId: string
  datasets: Dataset[]
  profiles: Record<string, Profile>
  loading: boolean
  onChanged: () => void
}) {
  const headingId = useId()
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // W-008: re-profiling is the analyst's, on request. A dataset that has a
  // stored profile shows it; one without shows an offer to profile it, so the
  // profile stage is a step the shell takes when asked rather than on every
  // visit.
  async function profileDatasetNow(datasetId: string) {
    if (busy) return
    setBusy(true)
    setError(null)
    try {
      await profileDataset(caseId, datasetId)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
    }
  }

  async function attach(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setBusy(true)
    setError(null)
    try {
      const dataset = await attachDataset(caseId, file)
      // Profiling is the step the generator reads, so the UI performs it
      // immediately rather than leaving an unprofiled dataset to guess from.
      await profileDataset(caseId, dataset.id)
      onChanged()
    } catch (err) {
      setError(messageOf(err))
    } finally {
      setBusy(false)
      event.target.value = ''
    }
  }

  return (
    <section
      className={surfaces.panel}
      aria-labelledby={headingId}
    >
      <h2 className={surfaces.heading} id={headingId}>Data</h2>
      <label className="file-button">
        {busy ? 'Attaching…' : 'Attach a CSV, Parquet or Excel file'}
        <input
          type="file"
          accept=".csv,.parquet,.xlsx"
          onChange={attach}
          disabled={busy}
          aria-label="Attach a dataset"
        />
      </label>
      {error && <p role="alert">Attach failed: {error}</p>}
      {loading ? (
        // SKEL: the workspace's read is in flight, so "no data attached yet"
        // would be a sentence about a case the shell has not read. The shape
        // is the overview-plus-table the profile fills in; the sentence stays
        // for assistive tech, visually hidden.
        <>
          <p className={surfaces.note + ' visually-hidden'}>Reading the data…</p>
          <Skeleton shape="table" count={Math.max(datasets.length, 1)} />
        </>
      ) : datasets.length === 0 ? (
        <p className={surfaces.note}>No data attached yet - this is where the loop starts.</p>
      ) : (
        <ul className={surfaces.panelList}>
          {datasets.map((d) => {
            const profile = profiles[d.id]
            return (
              <li key={d.id}>
                <strong>{d.filename}</strong> <span className={surfaces.note}>({d.format})</span>
                {profile ? (
                  <>
                    <span className={surfaces.note}>
                      {' '}— {profile.rows} rows, {profile.columns.length} columns,{' '}
                      {profile.duplicate_rows} duplicate
                    </span>
                    <div className={surfaces.buttonRow}>
                      <Button
                        type="button"
                        onClick={() => void profileDatasetNow(d.id)}
                        disabled={busy}
                        aria-label={`Re-profile ${d.filename}`}
                      >
                        {busy ? 'Profiling…' : 'Re-profile'}
                      </Button>
                    </div>
                  </>
                ) : (
                  // W-008: an unprofiled dataset is offered a profile rather
                  // than silently profiled on open. The rail's profile stage
                  // is the analyst's step; the shell takes it when asked.
                  <div className={surfaces.buttonRow}>
                    <Button
                      type="button"
                      onClick={() => void profileDatasetNow(d.id)}
                      disabled={busy}
                      aria-label={`Profile ${d.filename}`}
                    >
                      {busy ? 'Profiling…' : 'Profile this dataset'}
                    </Button>
                    <span className={surfaces.note}>unprofiled - the generator and the planner read this</span>
                  </div>
                )}
                {profile && <QualityList quality={profile.quality} />}
                {profile && <ColumnNulls profile={profile} />}
              </li>
            )
          })}
        </ul>
      )}
      {datasets.length > 0 && (
        <GeneratePanel
          caseId={caseId}
          dataset={datasets[0]}
          profile={profiles[datasets[0].id]}
          onChanged={onChanged}
        />
      )}
      {datasets.length > 0 && (
        <RunCodePanel
          caseId={caseId}
          datasetId={datasets[0].id}
          datasetName={datasets[0].filename}
          // W3X-004: the contract names the columns the dataset actually has,
          // so its example reads against the file the analyst attached. A
          // dataset the profile has not reached yet still gets the contract,
          // in the generic terms the codegen panel's placeholder uses.
          columns={profiles[datasets[0].id]?.columns}
          onChanged={onChanged}
        />
      )}
    </section>
  )
}

// A question yields the read-only computation that would answer it. The
// proposal writes nothing; Run is the analyst's explicit decision and posts to
// the only endpoint that persists a run.
//
// W-016 (FIX-PYTHON-005): the panel offers SQL and Python, and the kind it
// carries picks both the code the generator proposes and the endpoint the run
// posts to. A python run is the hard sandbox's own surface (P3-SEC-001) - it
// persists exactly like a SQL one, so the runs panel, the evidence graph and
// the validation are all shared, and the only thing that changes is who
// executed the code. The kind persists across proposals in the same panel, so
// a sequence of python questions stays python.

export function ColumnNulls({ profile }: { profile: Profile }) {
  const stats = (profile.stats ?? {}) as Record<string, {
    null_count?: number
    null_percentage?: number
  }>
  const rows = profile.columns
    .map((column) => ({ column, stat: stats[column] }))
    .filter((entry): entry is { column: string; stat: { null_count: number; null_percentage: number } } =>
      entry.stat !== undefined &&
      typeof entry.stat.null_count === 'number' &&
      typeof entry.stat.null_percentage === 'number',
    )
  if (rows.length === 0) return null
  return (
    <ul className={surfaces.panelList + ' column-nulls'}>
      {rows.map(({ column, stat }) => (
        <li
          key={column}
          className={stat.null_count > 0 ? 'warn' : surfaces.note}
          aria-label={`${column}: ${stat.null_count} null (${stat.null_percentage}%)`}
        >
          {column}: {stat.null_count} null{stat.null_count === 1 ? '' : 's'} ({stat.null_percentage}%)
        </li>
      ))}
    </ul>
  )
}
