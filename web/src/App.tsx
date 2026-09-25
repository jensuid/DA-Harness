import { useState } from 'react'
import { CaseCreation } from './CaseCreation'
import { CaseList } from './CaseList'
import { CaseWorkspace } from './CaseWorkspace'
import { NoticeLayer } from './NoticeLayer'

// State-based navigation, no router: the bundle stays dependency-free as
// DEC-001 intends, and every screen reads its own data on mount.
type View =
  | { kind: 'list' }
  | { kind: 'workspace'; caseId: string }
  | { kind: 'create' }

export function App() {
  const [view, setView] = useState<View>({ kind: 'list' })

  if (view.kind === 'workspace') {
    return (
      // The workspace spreads to three zones (UX 8); the list and the creation
      // form stay single-column narrow.
      <main className="wide">
        <NoticeLayer />
        <CaseWorkspace
          caseId={view.caseId}
          onBack={() => setView({ kind: 'list' })}
          // A cited prior case opens as its own workspace rather than landing
          // back on the list (P7-SHELL-006).
          onOpenCase={(caseId) => setView({ kind: 'workspace', caseId })}
        />
      </main>
    )
  }

  if (view.kind === 'create') {
    return (
      <main>
        <NoticeLayer />
        <CaseCreation
          onCreated={(caseId) => setView({ kind: 'workspace', caseId })}
          onCancel={() => setView({ kind: 'list' })}
        />
      </main>
    )
  }

  return (
    <main>
      {/* FIX-UPDATES-009 (W-005): mounted on every screen because the native
        Check for Updates menu item can be pulled on any of them, and inert
        until a notice arrives - it is not a loading state. The browser host
        never receives one, because only the shell has a menu item to answer
        for. */}
      <NoticeLayer />
      <CaseList
        onOpen={(caseId) => setView({ kind: 'workspace', caseId })}
        onCreate={() => setView({ kind: 'create' })}
      />
    </main>
  )
}
