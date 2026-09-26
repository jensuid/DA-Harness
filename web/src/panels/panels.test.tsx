/**
 * The split itself (P9-F1-001).
 *
 * The contract this file pins is not behaviour - CaseWorkspace.test.tsx's 177
 * assertions already hold the panels to that, unchanged - but the structure:
 * every panel the composition root renders is exported by a file in this
 * directory, and no file recreates the 2,900-line component it replaced. A
 * panel that grows past the ceiling is a file that needs splitting again,
 * and this is the test that says so before someone opens it.
 *
 * The files are imported rather than read: the suite has no node typings
 * (the build's tsc -b compiles these sources, and `node:fs` is not in it),
 * and an import is the reachability check the split is about - a name the
 * root imports that does not resolve is a broken link, not a missing file.
 */
import { describe, expect, it } from 'vitest'

import { CaseWorkspace } from '../CaseWorkspace'

// The source text of every panel the workspace renders, read through Vite's
// `?raw` so the debt-paid test below asserts over the file as it stands rather
// than over a module's evaluated shape.
import { default as agentSource } from './AgentPanel.tsx?raw'
import { default as chatSource } from './Chat.tsx?raw'
import { default as contextSource } from '../ContextPanel.tsx?raw'
import { default as dataPanelSource } from './DataPanel.tsx?raw'
import { default as decisionSource } from '../DecisionPanel.tsx?raw'
import { default as draftPanelSource } from './DraftPanel.tsx?raw'
import { default as edaPanelSource } from './EdaPanel.tsx?raw'
import { default as evaluatePanelSource } from './EvaluatePanel.tsx?raw'
import { default as evidencePanelSource } from './EvidencePanel.tsx?raw'
import { default as findingsPanelSource } from './FindingsPanel.tsx?raw'
import { default as generatePanelSource } from './GeneratePanel.tsx?raw'
import { default as historyPanelSource } from './HistoryPanel.tsx?raw'
import { default as learnPanelSource } from './LearnPanel.tsx?raw'
import { default as planPanelSource } from './PlanPanel.tsx?raw'
import { default as refinePanelSource } from '../RefinePanel.tsx?raw'
import { default as runsPanelSource } from './RunsPanel.tsx?raw'
import { default as templatesSource } from '../Templates.tsx?raw'
import { default as caseListSource } from '../CaseList.tsx?raw'

const sources: Record<string, string> = {
  'AgentPanel.tsx': agentSource,
  'Chat.tsx': chatSource,
  'ContextPanel.tsx': contextSource,
  'DataPanel.tsx': dataPanelSource,
  'DecisionPanel.tsx': decisionSource,
  'DraftPanel.tsx': draftPanelSource,
  'EdaPanel.tsx': edaPanelSource,
  'EvaluatePanel.tsx': evaluatePanelSource,
  'EvidencePanel.tsx': evidencePanelSource,
  'FindingsPanel.tsx': findingsPanelSource,
  'GeneratePanel.tsx': generatePanelSource,
  'HistoryPanel.tsx': historyPanelSource,
  'LearnPanel.tsx': learnPanelSource,
  'PlanPanel.tsx': planPanelSource,
  'RefinePanel.tsx': refinePanelSource,
  'RunsPanel.tsx': runsPanelSource,
  'Templates.tsx': templatesSource,
  'CaseList.tsx': caseListSource,
}

import { AgentPanel, AGENT_COPY, stepSentence, StepStatus } from './AgentPanel'
import { CaseOverview, QualityList } from './CaseOverview'
import { Chat, Ground } from './Chat'
import { ColumnNulls, DataPanel } from './DataPanel'
import { DraftPanel } from './DraftPanel'
import { EdaPanel, EdaResultTable, typeOf } from './EdaPanel'
import { Audit, AXES, EVALUATE_REFUSALS, EvaluatePanel, evaluateRefusal, RecordedAudit } from './EvaluatePanel'
import {
  ClaimTraceRow,
  EvidencePanel,
  GraphBody,
  RELATIONS,
  nodePhrase,
} from './EvidencePanel'
import { FindingRow, FindingsPanel, Verdict } from './FindingsPanel'
import {
  GENERATE_KINDS,
  GENERATE_KIND_LABELS,
  GeneratePanel,
} from './GeneratePanel'
import { COUNT_KINDS, EVENT_KINDS, HistoryBody, HistoryPanel } from './HistoryPanel'
import { LearnPanel, PHASE_TITLES, WalkBody } from './LearnPanel'
import { PlanPanel } from './PlanPanel'
import {
  ChartPanel,
  RunRow,
  RunRowsTable,
  RunsPanel,
  chartLabel,
  formatValue,
  measureChoices,
  pickOf,
} from './RunsPanel'
// P9-F4-001: the chart surface moved to `lib/chart.tsx`, where the geometry
// the core's own renderer uses lives with the tree that draws it.
import { ChartSurface } from '../lib/chart'
import { STAGE_MARKS, WorkflowRail, stageStatus } from './WorkflowRail'

/** The panels this directory ships, keyed by file: each entry's value is the
 * names that file exports, so a panel added without an entry here fails the
 * completeness check rather than shipping untraced. */
const PANELS: Record<string, unknown[]> = {
  AgentPanel: [AgentPanel, AGENT_COPY, stepSentence, StepStatus],
  CaseOverview: [CaseOverview, QualityList],
  Chat: [Chat, Ground],
  DataPanel: [DataPanel, ColumnNulls],
  DraftPanel: [DraftPanel],
  EdaPanel: [EdaPanel, EdaResultTable, typeOf],
  EvaluatePanel: [EvaluatePanel, Audit, AXES, RecordedAudit, EVALUATE_REFUSALS, evaluateRefusal],
  EvidencePanel: [EvidencePanel, GraphBody, ClaimTraceRow, nodePhrase, RELATIONS],
  FindingsPanel: [FindingsPanel, FindingRow, Verdict],
  GeneratePanel: [GeneratePanel, GENERATE_KINDS, GENERATE_KIND_LABELS],
  HistoryPanel: [HistoryPanel, HistoryBody, COUNT_KINDS, EVENT_KINDS],
  LearnPanel: [LearnPanel, WalkBody, PHASE_TITLES],
  PlanPanel: [PlanPanel],
  RunsPanel: [
    RunsPanel,
    RunRow,
    RunRowsTable,
    ChartPanel,
    ChartSurface,
    chartLabel,
    formatValue,
    measureChoices,
    pickOf,
  ],
  WorkflowRail: [WorkflowRail, stageStatus, STAGE_MARKS],
}

describe('the panel split', () => {
  it('every panel the workspace renders is one this directory exports', () => {
    // The root imports its panels by name; a name that resolves here is a
    // link the split kept, and one that does not is a panel left behind in
    // the old file. The root renders each of these exactly once.
    expect(Object.keys(PANELS).sort()).toEqual(
      [
        'AgentPanel',
        'CaseOverview',
        'Chat',
        'DataPanel',
        'DraftPanel',
        'EdaPanel',
        'EvaluatePanel',
        'EvidencePanel',
        'FindingsPanel',
        'GeneratePanel',
        'HistoryPanel',
        'LearnPanel',
        'PlanPanel',
        'RunsPanel',
        'WorkflowRail',
      ].sort(),
    )
  })

  it('a panel is a function or a component, never undefined', () => {
    for (const [stem, exports] of Object.entries(PANELS)) {
      for (const name of exports) {
        expect(name, `${stem} exported a name that resolves to undefined`)
          .toBeDefined()
      }
    }
  })

  it('the workspace is the composition root: a panel is not a file here', () => {
    expect(Object.keys(PANELS)).not.toContain('CaseWorkspace')
    // The root renders each panel exactly once; a panel that renders its
    // peers has taken the root's job, and a panel that renders the root has
    // made the loop a cycle.
    expect(typeof CaseWorkspace).toBe('function')
  })

  it('every exported name is a distinct symbol, not a re-export twice', () => {
    const seen = new Set<unknown>()
    for (const exports of Object.values(PANELS)) {
      for (const name of exports) {
        expect(seen.has(name), 'the same symbol is exported by two panels')
          .toBe(false)
        seen.add(name)
      }
    }
  })

  it('F2-002: the token layer is the vocabulary the panels use, not the CSS', () => {
    // A panel that goes back to `className="panel"` reinstates the debt F2-002
    // paid, and this is the test that says so. The old CSS rules those names
    // defined are gone, so a literal className would render unstyled rather
    // than merely old-styled - the failure it catches is visible.
    const dead = ['panel', 'subpanel', 'proposal', 'run', 'items', 'grounds',
                  'stages', 'chat', 'muted', 'turn', 'rationale']
    for (const [file, source] of Object.entries(sources)) {
      for (const name of dead) {
        expect(
          source,
          `${file} still uses className="${name}" - the token layer owns that surface`,
        ).not.toMatch(`className="${name}"`)
      }
    }
  })
})
