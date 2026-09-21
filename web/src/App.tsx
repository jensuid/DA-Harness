import { useState } from 'react'
import { CaseCreation } from './CaseCreation'
import { CaseList } from './CaseList'
import { CaseWorkspace } from './CaseWorkspace'

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
      <main>
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
        <CaseCreation
          onCreated={(caseId) => setView({ kind: 'workspace', caseId })}
          onCancel={() => setView({ kind: 'list' })}
        />
      </main>
    )
  }

  return (
    <main>
      <CaseList
        onOpen={(caseId) => setView({ kind: 'workspace', caseId })}
        onCreate={() => setView({ kind: 'create' })}
      />
    </main>
  )
}
