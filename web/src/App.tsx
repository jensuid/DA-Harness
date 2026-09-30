import { useState } from 'react'
import { CaseCreation } from './CaseCreation'
import { CaseList } from './CaseList'
import { CaseWorkspace } from './CaseWorkspace'
import { ReducedMotion } from './lib/motion'
import { NoticeLayer } from './NoticeLayer'
import { LlmStatusBanner } from './panels/LLMStatus'
import { LlmSettingsPanel } from './panels/LLMSettings'

// State-based navigation, no router: the bundle stays dependency-free as
// DEC-001 intends, and every screen reads its own data on mount.
type View =
  | { kind: 'list' }
  | { kind: 'workspace'; caseId: string }
  | { kind: 'create' }

export function App() {
  const [view, setView] = useState<View>({ kind: 'list' })

  // P9-F3: the motion gate is mounted once, at the root, so every motion
  // surface on every screen resolves `prefers-reduced-motion` through it
  // rather than each one reading the preference itself. A screen the gate
  // does not wrap is a screen the analyst's setting does not reach.
  return (
    <ReducedMotion>
      {/* UI-REDUX S1: the skip link is the standard accompaniment to the
          landmark below - a keyboard user's first tab reaches this instead of
          the sticky rail's controls, and it is invisible to the sighted layout
          until it has focus. */}
      <a className="skip-link" href="#content">
        Skip to content
      </a>
      {view.kind === 'workspace' ? (
        // The workspace spreads to three zones (UX 8); the list and the
        // creation form stay single-column narrow.
        <main className="wide" id="content">
          <NoticeLayer />
          <LlmStatusBanner />
          <LlmSettingsPanel />
          <CaseWorkspace
            caseId={view.caseId}
            onBack={() => setView({ kind: 'list' })}
            // A cited prior case opens as its own workspace rather than
            // landing back on the list (P7-SHELL-006).
            onOpenCase={(caseId) => setView({ kind: 'workspace', caseId })}
          />
        </main>
      ) : view.kind === 'create' ? (
        <main id="content">
          <NoticeLayer />
          <LlmStatusBanner />
          <LlmSettingsPanel />
          <CaseCreation
            onCreated={(caseId) => setView({ kind: 'workspace', caseId })}
            onCancel={() => setView({ kind: 'list' })}
            // W2X-010: the duplicate notice's own link reaches the case the
            // core named, and the workspace is the same view either way.
            onView={(caseId) => setView({ kind: 'workspace', caseId })}
          />
        </main>
      ) : (
        <main id="content">
          {/* FIX-UPDATES-009 (W-005): mounted on every screen because the
            native Check for Updates menu item can be pulled on any of them,
            and inert until a notice arrives - it is not a loading state. The
            browser host never receives one, because only the shell has a
            menu item to answer for. */}
          <NoticeLayer />
          <LlmStatusBanner />
          <LlmSettingsPanel />
          <CaseList
            onOpen={(caseId) => setView({ kind: 'workspace', caseId })}
            onCreate={() => setView({ kind: 'create' })}
          />
        </main>
      )}
    </ReducedMotion>
  )
}
