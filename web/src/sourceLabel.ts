// The sentence a panel renders next to an engine's answer (FIX-TIMEOUT-006).
//
// `by {source}` names the engine but never says it was not the one the analyst
// asked for. When the LLM fails the server falls back to a deterministic answer
// and records `deterministic fallback`, and that label is what tells the
// analyst the engine they configured did not answer and another one did - the
// sentence sits where the source label sits and reads as a sentence, so a
// fallback stops looking like a choice and starts looking like a substitution.
//
// The server owns the wording through SOURCE_FALLBACK_SENTENCE in each engine
// module; this is its web-side counterpart, kept in one place so the six panels
// that show a source cannot drift apart in how they announce one.
//
// W3X-002: a fallback sentence is a *complete* sentence, so a panel cannot
// append its own clause to one the way it can to `by {source}`. The walk-test
// measured the result: "The LLM was unavailable, so a deterministic plan
// answered in its place. for helpdesk_tickets_2026.csv" - a lowercase fragment
// glued to a period, reading as a typo rather than as the announcement the
// FIX-TIMEOUT-006 line intended. `sourceLabel` keeps returning the sentence,
// and panels that have their own context render it as a separate clause with
// `sourceWith`, which capitalises the context so both shapes stay grammatical -
// or as their own `<p>` alongside the sentence.

const FALLBACK_SOURCE = 'deterministic fallback'

const FALLBACK_SENTENCES: Record<string, string> = {
  // `source` is the engine that answered after the LLM failed; the noun is the
  // artifact kind the panel is showing.
  interpretation: 'The LLM was unavailable, so a deterministic reading answered in its place.',
  draft: 'The LLM was unavailable, so a deterministic draft answered in its place.',
  answer: 'The LLM was unavailable, so a deterministic answer answered in its place.',
  plan: 'The LLM was unavailable, so a deterministic plan answered in its place.',
  proposal: 'The LLM was unavailable, so a deterministic proposal answered in its place.',
}

/** The label a panel shows for an engine's source, announced when it fell back. */
export function sourceLabel(source: string, kind: keyof typeof FALLBACK_SENTENCES): string {
  if (source === FALLBACK_SOURCE) {
    return FALLBACK_SENTENCES[kind]
  }
  return `by ${source}`
}

/** The label and a context phrase the panel supplies, as one readable sentence.
 *
 * A `by {source}` label takes an appended clause ("by llm for sales.csv"); a
 * fallback sentence already ends with a period. Capitalising the context's
 * first letter keeps the fallback's announcement intact and the appended
 * clause grammatical, so the substitution stays an announcement instead of
 * looking like a broken label. */
export function sourceWith(
  source: string,
  kind: keyof typeof FALLBACK_SENTENCES,
  context: string,
): string {
  const label = sourceLabel(source, kind)
  if (source === FALLBACK_SOURCE) {
    return `${label} ${context[0].toUpperCase()}${context.slice(1)}`
  }
  return `${label} ${context}`
}
