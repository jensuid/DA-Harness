// The sentence a panel shows next to an engine's answer, and how a panel's own
// context joins it (W3X-002: the sentence used to be glued to the label it
// replaces).
import { describe, expect, it } from 'vitest'

import { sourceLabel, sourceWith } from './sourceLabel'

describe('sourceLabel', () => {
  it('names the engine when it did not fall back', () => {
    expect(sourceLabel('llm', 'plan')).toBe('by llm')
  })

  it('announces a fallback as a complete sentence, not a label', () => {
    // FIX-TIMEOUT-006: a deterministic answer has to read as a substitution,
    // not as a choice, or the analyst mistakes it for the LLM's.
    expect(sourceLabel('deterministic fallback', 'plan')).toBe(
      'The LLM was unavailable, so a deterministic plan answered in its place.',
    )
    expect(sourceLabel('deterministic fallback', 'interpretation')).toBe(
      'The LLM was unavailable, so a deterministic reading answered in its place.',
    )
  })
})

describe('sourceWith', () => {
  it('appends a context phrase to a plain engine label', () => {
    expect(sourceWith('llm', 'plan', 'for sales.csv')).toBe(
      'by llm for sales.csv',
    )
  })

  it('does not glue a lowercase fragment to a fallback sentence', () => {
    // The walk-test measured this rendering and read it as a typo:
    //   "...answered in its place. for helpdesk_tickets_2026.csv"
    // A sentence that ends with a period cannot take a lowercase fragment.
    const rendered = sourceWith(
      'deterministic fallback',
      'plan',
      'for helpdesk_tickets_2026.csv',
    )
    expect(rendered).not.toMatch(/ in its place\. for /)
  })

  it('keeps the fallback sentence intact and grammatical with context', () => {
    expect(
      sourceWith('deterministic fallback', 'plan', 'for sales.csv'),
    ).toBe(
      'The LLM was unavailable, so a deterministic plan answered in its place. For sales.csv',
    )
  })

  it('carries a context that is already a clause with its own dash', () => {
    expect(
      sourceWith('deterministic fallback', 'proposal', '— reads revenue'),
    ).toBe(
      'The LLM was unavailable, so a deterministic proposal answered in its place. — reads revenue',
    )
  })

  it('names the same engine the fallback announcement does', () => {
    // The two shapes must not disagree about which engine answered.
    const label = sourceWith('deterministic fallback', 'draft', '— read it')
    expect(label).toContain('deterministic draft answered in its place')
    expect(sourceWith('llm', 'draft', '— read it')).toContain('by llm')
  })
})
