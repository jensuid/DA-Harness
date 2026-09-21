# DAH — PRD & UX/UI Conformance Evaluation

**Evaluated against:**
- `docs/Product Requirements Specification (PRD).md` (v1.1, Artifact 04) — 48
  acceptance thresholds AT-01…AT-48
- `docs/UX- UI Architecture.md` (v1.0, Artifact 06) — the UX contract

**Method:** each requirement was checked against the running app's endpoints,
its SQLite schema, its workflow derivation in `server/app/workflow.py`, and the
rendered shell in `web/src/`. No claim below rests on the documents alone.

---

## 1. Verdict

The PRD and the UX architecture are **not describing a different product**.
They are the master specification of the product DAH already is, written at the
level of *measurable thresholds* rather than *capabilities*. The gap is not one
of vision — it is that DAH implements the trust model **narrowly** and measures
**nothing**.

Concretely:

- The PRD's Level 0 and Level 1 core (no fabricated evidence, no fabricated
  execution, valid evidence chains, reproducible computation, human control of
  every AI write) is **genuinely built and genuinely enforced** — not claimed,
  enforced by construction.
- The PRD's *breadth* requirements are not: validation covers **3 of 9**
  dimensions, data-quality detection covers **2 of 7** defect classes, and
  question capture is **one text field** rather than the structured
  purpose/question/sub-question/hypothesis object the PRD requires.
- The PRD's central demand — *"what 'done' quantitatively means"* — is entirely
  unmet: there is no golden analytical dataset suite, no coverage measurement,
  no performance benchmark, no accessibility suite, no requirement-traceability
  matrix. DAH measures that its contracts pass; it does not measure that they
  meet thresholds.
- The UX architecture's **orientation spine** — the persistent workflow rail
  with per-stage status, the three-zone adaptive workspace, the case overview,
  the decision view — is absent. The shell is a capable but flat vertical stack
  of thirteen panels.

One thing to be clear about: **the UX document's own MVP scope (§50) is largely
satisfied.** What it calls P0 and P1 (shell, case list, creation, navigation,
workflow indicator, persistence, purpose, question, data, quality, explore,
analysis, evidence, finding, validation, case overview) is mostly built —
except **purpose/context**, **the quality gate before analysis**, and **the case
overview**. The three-zone layout, command palette and Analysis Canvas are its
own later-stage items.

---

## 2. Where DAH already satisfies the contract

Mapped to the PRD's threshold hierarchy, with the evidence that proves it.

### Level 0 — Safety / Trust (0 tolerance): **MET**

| Threshold | What the PRD requires | DAH's state |
|---|---|---|
| AT-19 | 0 fabricated execution or evidence claims | The honesty budgets: a proposal (code, interpretation, draft) **writes nothing**; every citation must resolve to a real artifact or the answer is rejected; an invented column or number is refused, not rendered. `source` records which engine spoke. |
| AT-22 | 100% of state-changing AI actions authorized | The single approval gate. Both agent roles propose; only a human **Approve and run** performs the write, through the endpoint that owns it. A GET never proposes. |
| AT-15 | 100% valid evidence chains | A finding cannot exist without a `run_id` (schema-level NOT NULL); the evidence graph traces claim → run → dataset; a dataset with a bound run cannot be deleted (400). |
| AT-41/42 | No validated finding with missing evidence; no invalid transitions | A finding is created `not_evaluated` with evidence already attached; validation is the only path to a verdict. There is no Draft→Validated shortcut, because there is no shortcut at all. |

### Level 1 — Correctness (≈100%): **MOSTLY MET**

| Threshold | State |
|---|---|
| AT-07 profiling | **Fully met.** Missingness, uniqueness, duplicates, numeric summaries (min/max/avg), temporal ranges, categorical cardinality — all in the deep profile, deterministic. |
| AT-11 SQL / AT-12 Python | Met. Read-only gate rejects non-SELECT before execution; Python runs under an OS-level sandbox with bounded CPU and no network. Failed executions return readable errors, never a crash. |
| AT-13 result integrity | Met. Every run records dataset, kind, code, columns, rows, row count, truncation and execution time. |
| AT-14 visualization | Met. Charts render from the run's own persisted result rows, not from a separate hand-entered series. |
| AT-23 reproducibility | Met. Validation reruns the stored computation and compares rows **as a multiset**, so an unordered `GROUP BY` matches rather than drifting. |
| AT-02 / AT-24 persistence | Met. SQLite with a forward-only versioned migration path; 50 save→reopen cycles would pass today. |
| AT-43 / AT-47 export | Met. Self-contained JSON package with an import round trip, fresh IDs. |
| AT-44 auditability | Met. The case-history timeline records one event per artifact; agent steps record approval *and rejection reasons*. |

### Level 2 — Reliability: **MET**

AT-26 error recovery and the P5 500-envelope: a harness fault answers 500 with a
request id mapping to a log traceback; an analyst error answers 400 with the
engine's own message. Input failure never costs the case.

### The UX contract's fifteen rules (§58): **largely honoured in spirit**

Case-first not dashboard-first (✓ — there is no dashboard at all); computation
inspectable (✓); guided not forced (✓ — the stage is *derived*, and deleting an
artifact moves the case back, so nothing forces an order); human in control
(✓); uncertainty communicated honestly (✓ — `partially_supported` exists and is
rendered, and LEARN says the loop ran, not that the answer is right).

---

## 3. The gaps, in the PRD's own priority order

### Level 1 correctness gaps — the real trust debt

**G1. Validation covers 3 of 9 dimensions (AT-17).** This is the single most
important gap, and the PRD makes it release-blocking for a reason. Today
`validate_finding` runs three checks: reproducibility, missing data, evidence
integrity. The PRD requires nine — Calculation, Data, Population, Timeframe,
Method, Evidence, Assumptions, Causality, Alternative explanations. Six are
uncomputed. Notably the **EVALUATE engine already computes a nine-axis audit**
(question, data, quality, method, calculation, evidence, claim, visualization,
limitations) — but only over *imported external work*, never over the case's own
findings. The machinery exists; it is pointed at the wrong object.

**G2. Data-quality detection covers 2 of 7 defect classes (AT-08).** The profile
finds missing values and duplicate rows. It does not detect invalid types,
inconsistent categories, date gaps, extreme values, or insufficient coverage —
and these are the defects that make a *correct* calculation answer the *wrong*
question.

**G3. No quality impact communication (AT-09).** The validation check reports
"1 null value(s) across profiled columns." The PRD wants "Revenue contains 4.8%
missing values; revenue comparisons may be understated." The number is
available; the *consequence* is not derived. And per the UX document (§15) this
belongs at the **Data stage, before analysis** — today it surfaces only at
validation, after the finding exists.

**G4. Question capture is one text field (AT-03).** A case is `question +
dataset`. There is no purpose, no sub-questions, no hypotheses as editable
first-class objects — yet these are exactly what AT-03 requires to persist and
reopen, what AT-10 requires the plan to contain, what the planner should reason
over, and what the UX document's Context section (§13) treats as a first-class
analytical object. The *generated plan* carries sub-questions and hypotheses,
but P7-WALK-001 recorded that **they are persisted and never rendered**, and they
are not editable.

**G5. No causal-language guard on the case's own findings (AT-18).** The
EVALUATE `claim` axis flags unsupported causal language in submitted work. A
finding drafted inside DAH gets no such check — it can be accepted as
"marketing spend drives signups" from six correlating rows, and nothing says
otherwise. The validation that runs answers *reproducibility*, not *causality*.

### Level 3 detection-quality gaps

**G6. No AI evaluation suite (AT-04, AT-20, AT-21).** The honesty *mechanisms*
are built and tested, but the 50-/100-case evaluation suites that would measure
the thresholds do not exist. DAH cannot currently state a number for its own
most important claims.

### Level 4 performance and Level 5 UX gaps

**G7. Nothing is measured (AT-01, AT-27…AT-30, AT-32, AT-37, AT-38, AT-45,
AT-46, AT-48).** No golden analytical dataset suite with reference values
(AT-40); no scripted-workflow completion rate; no profiling/case-load
benchmarks; no accessibility suite; no dependency scanning; no declared
data-size envelope (a 50M-row CSV is attempted today, not refused); no
requirement-traceability matrix — which the PRD (§59) calls "an engineering
control artifact" and is the one artifact that would make every other gap
visible.

**G8. The orientation spine is missing (AT-33, AT-34, AT-35; UX §5, §7, §8,
§45, §46).** Specifically absent:

- **The persistent workflow rail** (UX §7) with per-stage `✓ / ⚠ / ● / ○`. The
  shell has a text sentence ("Where this case stands") and no continuous
  status map. This is the UX document's central orientation mechanism.
- **The three-zone adaptive workspace** (UX §8): left = orientation, center =
  work, right = intelligence. Today the workspace is a single vertical column
  of thirteen panels in a fixed order.
- **The case overview** (UX §45) — objective, status, key findings, open
  issues, validation counts. The natural home for AT-33's "current stage /
  next useful action."
- **The decision view** (UX §46) — the loop's exit: findings, their validation,
  residual uncertainty, implications. Today a validated finding is the end of
  the road; the PRD's own flow (§48) ends at Decision Support → Export.
- **Context as an object** (UX §13) — same root cause as G4.
- **The work-launcher home** (UX §10) — the case list is a flat searchable
  list, not "continue where you left off."

**G9. Small render gaps the walkthrough already found.** A run's result rows
are not rendered; the plan's contents are not rendered; the profile's
per-column null count is not rendered; the chat and generate-code inputs are
adjacent near-identical boxes. Each is a panel over an existing contract, and
each becomes more visible once the three-zone layout exists.

---

## 4. Proposed plan — phase P8: *Analytical Contract*

The PRD's own rule governs the ordering: *"DAH should sacrifice convenience
before it sacrifices analytical trust."* So Level 1 trust breadth comes before
Level 5 UX, even though the UX work is more visible.

One dependency shapes the sequence: **the context object (P8-01) unblocks more
than anything else** — the planner reads it, question refinement edits it, the
case overview summarizes it, the decision view closes over it. It goes first.

### Entry checklist

| # | Task | Closes | Why this order |
|---|------|--------|----------------|
| 1 | **P8-CONTEXT-001** — the case's context object | AT-03, AT-10, UX §13 | Everything downstream reads from it; schema migration v10 |
| 2 | **P8-QUALITY-002** — quality detection beyond missingness | AT-08, AT-09 | Extends the profiler's own scan; feeds the quality gate |
| 3 | **P8-VALID-003** — validation from 3 checks to 9 dimensions | AT-17 | The largest single trust gap; reuses EVALUATE's machinery |
| 4 | **P8-CAUSAL-004** — the causal-language guard | AT-18 | Sits on the verdict vocabulary P8-03 formalises |
| 5 | **P8-GOLDEN-005** — the analytical golden suite + workflow rate | AT-40, AT-01 | Turns G1–G4 into measured numbers |
| 6 | **P8-SHELL-006** — the orientation spine | AT-33/34/35, UX §5/7/8/45 | Layout, after the objects it presents exist |
| 7 | **P8-REFINE-007** — question refinement | AT-04, UX §12 | Edits the context object; needs P8-01 |
| 8 | **P8-DECISION-008** — the decision view | UX §46, AT-43 | The loop's exit; reads validated findings |
| 9 | **P8-MEASURE-009** — coverage, perf, a11y, deps, envelope | AT-27…30, 32, 37, 38, 45, 46 | Mechanical once the golden suite exists |
| 10 | **P8-TRACE-010** — the requirement-traceability matrix | AT-48 | Last, because it traces what 1–9 delivered |

### Task shapes

**P8-CONTEXT-001 — the case's context object.**
A case gains structured, editable context: purpose, primary question,
sub-questions, hypotheses, known constraints. Persisted in a new `context`
table (migration v10), editable through `PATCH /cases/{id}/context`, read by
the planner (so a plan is generated *from* intent rather than from a question
string plus a profile) and by the chat's grounding budget. The UX document's
"business objective / time period / relevant changes / known constraints"
shape is the model. Acceptance: entered text persists across reopen; edited
text persists; the plan records which context fields it read; 3 sub-questions
and 2 hypotheses survive a round trip through export.

**P8-QUALITY-002 — quality detection beyond missingness.**
Five new defect classes computed in the profiling pass, reusing the one-scan
aggregate design: invalid types (values DuckDB coerced against the column's
declared family), inconsistent categories (a categorical with outlier-high
cardinality or off-pattern values), date gaps (missing periods in an ordered
temporal column), extreme values (z-score or IQR outliers on numerics), and
insufficient coverage (a categorical dominated by one value). Each produces
the AT-09 *impact* sentence from the profile's own numbers — which column is
affected, which comparisons it understates. Surfaced at the Data stage, before
analysis, as the UX document demands — not only at validation. Acceptance:
≥95% detection and ≤5% false positives on an injected-defect suite; every
material issue carries an impact sentence.

**P8-VALID-003 — validation from 3 checks to 9 dimensions.**
Extend `validate_finding` to the PRD's nine: Calculation (reproducibility,
already), Data (missingness, already, extended by P8-002's defect classes),
Population (does the claim's scope match the rows the query filtered?),
Timeframe (does the claim name a period the data covers?), Method (is the
aggregate appropriate to the claim — a mean over a skewed distribution, a
total over a null-bearing column), Evidence (already), Assumptions (does the
claim rest on a column the query never read?), Causality (P8-004),
Alternative explanations (is there another grouping that reverses the
result?). Each is a check with a pass/fail and a sentence, in the vocabulary
EVALUATE already uses. Acceptance: the nine are computed and rendered; ≥95% of
introduced analytical problems are detected; a finding with a failing
Calculation cannot report `supported`.

**P8-CAUSAL-004 — the causal-language guard.**
A deterministic check, not a judgement: causal verbs and construction patterns
(drives, causes, leads to, because of, due to, impact on) in a finding's
statement, combined with a run that establishes association only (no
intervention, no time-ordering, no confounder control) produce a `CONCERN` at
validation, and the rendered caveat names the distinction. The EVALUATE `claim`
axis already implements the vocabulary this needs. Acceptance: ≥95% flag rate
on 50 causal-language cases; **0** cases where an association-only basis
becomes a validated causal finding — the PRD makes that P0.

**P8-GOLDEN-005 — the analytical golden suite.**
Deterministic datasets designed to exercise aggregation, filtering, joins,
missingness, duplicates, dates, percentages, segmentation, statistical
calculation and validation, each with *expected reference values*, not just
expected success. This is AT-40 and it is the foundation the PRD's whole
measurement argument rests on. Alongside it: the scripted-workflow harness that
reports the AT-01 completion rate across 20 runs and 3 datasets. Acceptance:
100% of reference calculations match within tolerance; a workflow-completion
number exists and is reported.

**P8-SHELL-006 — the orientation spine.**
The persistent workflow rail with per-stage status, derived from the artifact
counts `workflow.py` already computes — so a stage's `⚠` is a quality defect
from P8-002, not a guess. The three-zone layout (orientation / work /
intelligence), which is a *rearrangement of panels that already exist*, not a
new application: the right rail becomes the chat and the agent panels, the left
rail becomes stages, datasets, findings and history, and the center becomes
data, runs, findings and the evidence graph. Includes rendering the three
numbers the walkthrough found unrendered (result rows, plan contents,
per-column nulls) and separating the two adjacent input boxes. Acceptance:
AT-33's seven questions are answerable from the rendered workspace alone; the
rail's status agrees with the core's derived stage.

**P8-REFINE-007 — question refinement.** AI proposes a refinement; the original
is preserved verbatim and shown beside it; accept / edit / keep-original are
the only three paths. Zero silent overwrites is a Level 0 requirement.
Acceptance: AT-04's thresholds on a 50-case suite; the original question is
recoverable after any path.

**P8-DECISION-008 — the decision view.** The loop's exit: the case's validated
findings, their residual uncertainty (the failing checks, not a score), the
implications the analyst writes, and the export. DAH informs decisions; it does
not make them. Acceptance: a case's decision view lists every validated finding
with its open caveats; export carries it.

**P8-MEASURE-009 — the measurement layer.** Line coverage against the PRD's
targets (≥80% core, ≥90% critical), the AT-27…30 performance benchmarks
including the 95th-percentile interaction target, an accessibility pass
(keyboard, focus, contrast, non-color-only status — the shell already uses ✓/✗
text, which is a head start), dependency scanning, and the declared data-size
envelope with honest refusal beyond it (AT-45: a 6M-row CSV is processed or
rejected, never silently hung). Acceptance: each AT has a number attached.

**P8-TRACE-010 — the requirement-traceability matrix.** The PRD's own control
artifact (§59): every AT number → the UX surface → the implementation → the
test → the measured threshold → PASS/FAIL. Built last, because it traces what
the phase delivered, and maintained thereafter as the release gate's input.

### Sequencing and the release

The release (v0.2.0) should **not** wait for P8. Everything P7 promised is
built, verified against a real server, walked through by hand, and now carries
the CSV fix. P8 is a *contract-conformance* phase, and its value is measured
work that lands as v0.3.0. If a release is wanted first, tag it now; the
pipeline is ready and the checklist is complete.

Within P8, tasks 1–5 are core-only and independently shippable; 6–8 are the
shell and depend on 1; 9–10 are mechanical and depend on 5. Tasks 1 and 2 can
run concurrently; 3 depends on 2's defect vocabulary; 4 depends on 3's verdict
shape.

### What I would deliberately not build

- **The Analysis Canvas** (UX §18). The document itself labels it "a later-stage
  feature rather than an MVP requirement." The evidence graph already renders
  the reasoning chain; a free canvas is a different product.
- **The command palette** (UX §28) — the document's own P3 item. Cheap later,
  no dependency, and it does not close a threshold.
- **The Knowledge nav item** (UX §4). Cross-case recall already exists as
  cited memory; a separate knowledge surface would duplicate it.
- **AI confidence scores** (UX §44). The document rejects them explicitly —
  structured evidence quality signals instead, which is what validation already
  renders. P8 keeps that.
- **Any dashboard.** The thesis is explicit and DAH currently honours it.

### The one risk worth naming

**P8-SHELL-006 is the only task that restructures a working surface**, and it
will touch every web test. The mitigation is that it is a *rearrangement*:
every panel it places already exists and already has a contract, and the
existing jsdom suite pins each one's rendered content. The layout changes; the
assertions should not have to. If the restructure proves to destabilise, it can
be deferred behind a feature flag and P8 still ships 1–5 and 7–10.
