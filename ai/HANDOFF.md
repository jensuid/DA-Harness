## Next action
**P8-CAUSAL-004 is DONE**: the causality check stopped commenting and started
guarding. An unsupported causal claim now gates the verdict - causality is the
fourth hard dimension, so "spend drives signups" over a correlation reaches
`insufficient_evidence`, not `supported`. New `server/app/causality.py` makes
three judgements: unhedged causal language over an observational comparison is
unsupported; a hedge ("may drive") or negation ("does not cause") is the author
naming the limit and passes; an intervention the context records *and the SQL
compares across* earns causation. The branch AT-18 turns on: an intervention
merely mentioned but never compared across still fails - mentioning is not
using.

**The 50-case corpus is data, and the measurement runs in the suite**: 100%
detection, 100% discrimination, 0 conversions against AT-18's 95%/95%/0. The
corpus found two real bugs the eyeball missed - normalisation strips the slash
("a/b test" arrives as "a b test"), and the negation window needed 5 words, not
3.

**Gates:** 468 server, 86 web, build green, 25/25 e2e.

### What is next, in priority order

- **P8-GOLDEN-005** - the analytical golden suite (AT-40/AT-01). This is what
  *measures* the workflow-completion rate; the causal corpus above can fold
  into it.
- **P8-SHELL-006** - the orientation spine (AT-33/34/35).
- **P8-REFINE-007** - question refinement (AT-04), editing the context object.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each is
in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`; the reasoning and
the bugs found are in `ai/HANDOFF-ARCHIVE.md`.

- **P8-CAUSAL-004** - the causal-language guard (AT-18); causality is now a
  hard dimension, a 50-case corpus measures 100% on AT-18's thresholds.
- **P8-VALID-003** - validation across the PRD's nine dimensions (AT-17);
  nine pure checks, one rerun, concern vs failure distinguished in the shell.
- **P8-QUALITY-002** - quality detection beyond missingness (AT-08/AT-09);
  seven defect classes, each with an impact sentence, shown at the Data stage.
- **P8-CONTEXT-001** - a case carries purpose, sub-questions, hypotheses and
  constraints (AT-03), read by the planner and the assistant.
- **v0.2.0** - released and published (tag on `ec819fc`); CI's billing is
  suspended, so artifacts were built and uploaded locally.
- **P7-CSV-002 / P7-CORS-001** - a stray trailing comma no longer collapses a
  CSV to one column; the packaged app's webview can reach its own core.

