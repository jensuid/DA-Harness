# WALK-UX-004 — Walk-test 4 report

A validation walk-test: the fourth end-to-end run of DAH, on a domain the
project had never analysed (B2B SaaS subscription renewals), with the same
slow LLM provider the third walk-test measured, a live Chromium, and a fresh
seeded dataset. It existed to answer two questions a suite cannot, and it
answered both.

## Verdict

**Both W3X fixes hold in a naive analyst's hands, and the walk-test found
the one thing no suite could.**

- **W3X-003-PROMPT: HOLD.** The LLM plan answered in **12.4 seconds**
  (`source: llm`) where W3 measured 120 seconds and a deterministic
  fallback - on the same provider, the same key, the same model. The stored
  plan carries 4 sub-questions / 3 hypotheses / 4 steps / 3 data
  requirements, exactly the shrunk prompt's caps.
- **W3X-004: HOLD.** The Python panel's contract turned the naive analyst's
  first interaction from three blind refusals into **zero refusals**: the
  first run used `dataset.rows` straight from the page and returned a 201.
- **W4X-001 (MAJOR, regression):** the W3X-003-PROMPT shrink dropped
  `context_basis` from the plan, the validator treats it as optional, and
  PlanPanel read it unconditionally - so **a case with an LLM plan could not
  be reopened**. Fixed and verified live in this run, committed as its own
  task.

The loop closed end to end with no terminal: attach, profile, plan, Python
run, SQL run, interpret, draft, accept, validate, reviewer audit, chat
(LLM), implication, export, reopen - and the reopen is what caught W4X-001.

## The journey, as executed

| Step | What happened |
|---|---|
| Case list (empty) | "No cases yet - create one." + a Templates section that explains itself |
| New case | Two labelled fields, both placeholders teach; stage `data` |
| Attach + profile | 3,000 rows, 10 columns; the planted mixed-date, categorical-split, missing-value and outlier anomalies all surfaced with "potential impact" sentences |
| Generate plan | **LLM answered in 12.4s** (after one provider 429 fell back in 751ms, announced); 4/3/4/3 fields |
| Python run | The contract on the page; first attempt used `dataset.rows` -> 201, **zero refusals** (W3: three) |
| SQL run | Segment/status counts, grouped, hand-written query accepted |
| Interpret | Provider 429 -> deterministic reading in 421ms, announced as a full sentence |
| Draft finding | Provider 429 -> deterministic draft, announced; accept recorded a finding |
| Validate | Nine checks; the verdict honestly refused the finding as `insufficient_evidence` |
| Reviewer audit | Proposed an audit; approve -> nine-axes EVALUATE verdict with per-axis sentences |
| Ask the case | LLM answered in 20s, grounded in the run's own rows: "Low active_users-to-seats utilisation predicts churned status" |
| Implication | Saved; `GET /decision` carries it |
| Export | 337KB self-contained package |
| Reopen | All state survived - and this is where W4X-001 was caught, fixed, and re-verified |

## Findings

| ID | Sev | One line | Fix shape |
|---|---|---|---|
| W4X-001 | MAJOR | A case with an LLM plan cannot be reopened - the plan panel reads a field the shrunk prompt no longer asks for | Guard the optional field; make the type optional. Done and verified live |
| W3X-003-PROMPT | HOLD | 12.4s LLM plan against a 120s budget on the provider that failed | Validated, no action |
| W3X-004 | HOLD | First Python interaction: zero refusals, `dataset.rows` used from the page | Validated, no action |

Effort vs impact: W4X-001 is the whole reason walk-tests run - a two-line
guard for a bug every test fixture inoculated against, found only by
reopening a real case with a real LLM plan.

## Honest limitations

- **Agent != naive human.** Waits, refusals and render states were measured
  from evidence, not experienced.
- **One provider, one session, rate-limited.** The plan measurement is the
  one call that got through; interpret and draft both hit 429s and fell back
  correctly.
- **The harness cannot type multi-line code** (a controlled-textarea
  limitation), so the Python run is the one-expression shape the panel's own
  example teaches - and the chart step (L7) was never reached for the same
  reason: chartable numeric columns needed an aggregation the one-expression
  runs did not produce. C-04 (chart survives reopen) is recorded as **not
  observed**, not assumed.

## Pipeline status on this tree

- server pytest: 793 passed (run for the v0.3.6 gate)
- web vitest: 285 passed (the five timing tests that timed out under load
  re-ran green in isolation - the same host-load pattern W3 recorded)
- tsc -b: clean; vite build: ok
- gates: trace 48/48, e2e 28/28

## Material

- `walktest-w4/make_dataset.py` — the seeded dataset builder
- `walktest-w4/PLAN.md` — this run's protocol and focus
- `walktest-w4/CAPTURE-SHEET.md` — the live sheet
- `walktest-w4/FINDINGS.md` — one block per finding, with the measurements
- `walktest-w4/evidence/` — the runs, the chat, the decision, the export package
- `walktest-w4/logs/` — the core's request log
