## Next action
**P8-SHELL-006 is DONE**: the shell answers "where am I, what am I doing, what
can help me" as a layout rather than as a sentence. The persistent rail carries
UX 7's four marks - `✓` complete, `⚠` requires attention, `●` the current
stage, `○` not started - derived the same way the core derives the stage, from
`progress.completed` and `progress.stage`, so the rail cannot disagree with the
core. The one judgement is the warning, and it is measured: the data stage's
`⚠` is the profiler's own quality defect (P8-QUALITY-002), never a guess.
Beside the rail sits the case overview (UX 45) - objective, question, "N / M
stages complete", key findings, open issues, data sources, validation counts -
each an artifact count the core already computed, with the objective reading
the context's purpose and the question as the fallback. The workspace splits
into three landmark zones (orientation / work / intelligence), a
rearrangement of panels that already existed: no panel was rewritten, and the
tests that pinned them were not edited to fit the layout - only the assertion
that a stage the loop is on was "pending" now reads "current", the rail's own
sharper vocabulary.

The three render gaps the walkthrough found are closed over endpoints that
already existed: a run's result rows and the query that produced them reopen
on demand (with the truncation notice when the result was capped); the plan's
own contents - sub-questions, hypotheses with their rationale and check,
steps, data requirements, the basis it was planned from - render instead of
being written and never read back; and every column's measured null count
shows at the Data stage. The two adjacent near-identical input boxes are
separated by the zones themselves. One limitation recorded rather than papered
over: the overview's labels are unstyled text, because splitting a label into
its own element breaks the text matching a test and a screen reader both read.

**Gates:** 477 server (unchanged - this task touched only the shell), 99 web
(13 new), build green, 25/25 e2e.

### What is next, in priority order

- **P8-REFINE-007** - question refinement (AT-04): AI proposes a refinement,
  the original is preserved verbatim beside it, and accept / edit /
  keep-original are the only three paths. It edits the context object
  P8-CONTEXT-001 built.
- **P8-DECISION-008** - the decision view (UX 46, AT-43): the loop's exit,
  reading the validated findings and their residual uncertainty.
- **P8-MEASURE-009** - the measurement layer (AT-27..30/32/37/38/45/46):
  coverage, perf, a11y, deps, the data-size envelope.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each is
in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`; the reasoning and
the bugs found are in `ai/HANDOFF-ARCHIVE.md`.

- **P8-SHELL-006** - the orientation spine; the rail, the case overview and the
  three-zone workspace, and the three render gaps the walkthrough found.
- **P8-GOLDEN-005** - the analytical golden suite; AT-40's reference match rate
  and AT-01's workflow-completion rate are now measured numbers, not claims.
- **P8-CAUSAL-004** - the causal-language guard (AT-18); causality is a hard
  dimension, a 50-case corpus measures 100% on its three thresholds.
- **P8-VALID-003** - validation across the PRD's nine dimensions (AT-17).
- **P8-QUALITY-002** - quality detection beyond missingness (AT-08/AT-09).
- **P8-CONTEXT-001** - a case carries purpose, sub-questions, hypotheses and
  constraints (AT-03).
- **v0.2.0** - released and published (tag on `ec819fc`); CI's billing is
  suspended, so artifacts were built and uploaded locally.
