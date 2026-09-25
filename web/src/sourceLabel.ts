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
