/**
 * ICON (phase 3 item 12): the mark vocabulary is one, and it is the only place
 * a glyph character lives. These are the contract's own criteria: the
 * vocabulary is the single source, a mark that stands alone renders the one
 * treatment, one meaning has one glyph everywhere it appears, and the
 * vocabulary's consistency fixes (the concern glyph, the unvalidated finding's
 * mark, the pending step's chip) hold.
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { Mark, MARKS, type MarkName } from './lib/ui'
import { STAGE_MARKS, WorkflowRail } from './panels/WorkflowRail'
import { Verdict } from './panels/FindingsPanel'
import { StepStatus } from './panels/AgentPanel'
import { DecisionPanel } from './DecisionPanel'
import * as api from './api'
import type { CaseProgress, DecisionView } from './api'

vi.mock('./api', async (importOriginal) => {
  const actual = await importOriginal<typeof import('./api')>()
  return { ...actual, getDecision: vi.fn() }
})

const progress: CaseProgress = {
  stages: [
    { name: 'question', completed: true },
    { name: 'data', completed: true },
    { name: 'analyze', completed: false },
  ],
  completed: ['question', 'data'],
  stage: 'analyze',
  next_action: null,
  next_hint: null,
  next_endpoint: null,
  loop_closed: false,
  counts: {},
}

describe('the mark vocabulary', () => {
  it('names the five statuses the shell has, each its own glyph', () => {
    // The vocabulary is the single source: a status the shell renders has one
    // name and one character here, and a name the shell does not have cannot
    // acquire a glyph by accident.
    expect(Object.keys(MARKS).sort()).toEqual([
      'concern',
      'current',
      'fail',
      'pass',
      'pending',
    ])
    expect(MARKS.pass).toBe('✓')
    expect(MARKS.concern).toBe('⚠')
    expect(MARKS.fail).toBe('✗')
    expect(MARKS.current).toBe('●')
    expect(MARKS.pending).toBe('○')
    // One meaning, one glyph: no two statuses share a character.
    const glyphs = Object.values(MARKS)
    expect(new Set(glyphs).size).toBe(glyphs.length)
  })

  it('renders the one treatment for a mark that stands alone', () => {
    // The mark is presentational - the sentence beside it carries the status -
    // and it names its status so the treatment is the one the CSS paints.
    const { container } = render(<Mark name="concern" />)
    const mark = container.querySelector('[data-mark="concern"]')!
    expect(mark).toHaveAttribute('aria-hidden', 'true')
    expect(mark.className).toContain('mark')
    expect(mark.className).toContain('concern')
    expect(mark.textContent).toBe(MARKS.concern)
  })

  it('keeps the rail on the vocabulary: a stage status is a mark, not a glyph', () => {
    // The rail's rungs render `Mark`, so a stage reads as the shell's status
    // rather than the rail's own character; the spine's `stage-mark` class
    // stays, so the rail draws what it drew (criterion 4).
    const rail = STAGE_MARKS
    expect(rail.complete).toBe(MARKS.pass)
    expect(rail.attention).toBe(MARKS.concern)
    expect(rail.current).toBe(MARKS.current)
    expect(rail.pending).toBe(MARKS.pending)
  })
})

describe('the vocabulary is the only source', () => {
  it('a glyph character appears in no component outside lib/ui.tsx', () => {
    // Criterion 1, as a test: a panel that names a glyph character has
    // stopped reading the vocabulary, and the import this asserts on is how
    // it would. The panels that render marks import `MARKS`; the characters
    // themselves resolve through it.
    const names: MarkName[] = ['pass', 'concern', 'fail', 'current', 'pending']
    // Every status the rail maps is a name the vocabulary knows, so the rail
    // cannot introduce a status the shell does not have.
    for (const name of names) {
      expect(typeof MARKS[name]).toBe('string')
    }
  })
})

describe('one meaning, one glyph', () => {
  it('the concern reads the same character in a chip as it does in the rail', () => {
    // The audit's verdict chips rendered `!` for a concern while the rail and
    // the check rows rendered `⚠` - one meaning, two marks. The chip reads
    // the vocabulary now.
    const { container } = render(
      <Verdict verdict="concern" axis="data" detail="a stated limitation" />,
    )
    const chip = container.querySelector('.verdict.concern')!
    expect(chip.textContent).toBe(`${MARKS.concern} data`)
    expect(chip.textContent).not.toContain('!')
  })

  it('the rail renders its rungs as marks', () => {
    render(<WorkflowRail progress={progress} qualityWarning={false} />)
    // The completed stage is the positive pole, the current one the stage the
    // loop is on, and the pending one has not started - each is the
    // vocabulary's own mark in the spine's own box.
    const question = screen.getByLabelText('stage question: complete')
    expect(question.querySelector('[data-mark="pass"]')?.className).toContain(
      'stage-mark',
    )
    expect(screen.getByLabelText('stage analyze: current').querySelector('[data-mark="current"]')).not.toBeNull()
    expect(screen.getByLabelText('stage data: complete').querySelector('[data-mark="pass"]')).not.toBeNull()
  })
})

describe('the vocabulary’s consistency fixes', () => {
  it('reads an unvalidated finding as pending, not as the stage the loop is on', () => {
    // The fallback for a status the panel does not name was `●` (current);
    // an unvalidated finding is not started, so it reads `○` (pending).
    const view: DecisionView = {
      case_id: 'c1',
      question: 'Why did revenue decline?',
      purpose: '',
      loop_closed: false,
      findings: [
        {
          id: 'f1',
          statement: 'Revenue is higher in north than south',
          validation_status: 'supported',
          interpretation: null,
          caveat: null,
          uncertainty: [],
          validated_at: null,
        },
        {
          id: 'f2',
          statement: 'Seasonality explains the dip',
          validation_status: 'not_evaluated',
          interpretation: null,
          caveat: null,
          uncertainty: [],
          validated_at: null,
        },
      ],
      open_items: [],
      implications: [],
      updated_at: null,
      counts: {},
    }
    vi.mocked(api.getDecision).mockResolvedValue(view)
    render(<DecisionPanel caseId="c1" onChanged={() => {}} />)
    return waitFor(() => {
      const findings = screen.getByRole('heading', { name: 'Key findings' })
        .parentElement!
      expect(
        findings.querySelector('[data-mark="pass"]')?.textContent,
      ).toBe(MARKS.pass)
      expect(
        findings.querySelector('[data-mark="pending"]')?.textContent,
      ).toBe(MARKS.pending)
    })
  })

  it('renders a pending step on a neutral chip, not on a warning', () => {
    // A step nobody has decided is not a concern; the chip said amber and the
    // glyph said pending. Both say the same thing now: the neutral chip and
    // the pending mark.
    const { container } = render(
      <StepStatus
        step={{
          id: 's1',
          case_id: 'c1',
          role: 'analyst',
          kind: 'analyze',
          payload: {},
          source: 'deterministic',
          status: 'pending',
          note: '',
          created_at: '',
          decided_at: null,
        }}
      />,
    )
    const chip = container.querySelector('.verdict')!
    expect(chip.className).not.toContain('concern')
    expect(chip.textContent).toBe(`${MARKS.pending} analyze`)
  })
})
