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

import { AgentPanel, AGENT_COPY, stepSentence, StepStatus } from './AgentPanel'
import { CaseOverview, QualityList } from './CaseOverview'
import { Chat, Ground } from './Chat'
import { ColumnNulls, DataPanel } from './DataPanel'
import { DraftPanel } from './DraftPanel'
import { EdaPanel, EdaResultTable, typeOf } from './EdaPanel'
import { Audit, AXES, EvaluatePanel, RecordedAudit } from './EvaluatePanel'
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
  ChartSurface,
  RunRow,
  RunRowsTable,
  RunsPanel,
  chartLabel,
  formatValue,
  measureChoices,
  pickOf,
} from './RunsPanel'
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
  EvaluatePanel: [EvaluatePanel, Audit, AXES, RecordedAudit],
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
})
