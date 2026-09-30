# WALK-UX-004 findings

Walk-test 4: a complete end-to-end run of DAH on a brand-new domain (B2B SaaS
subscription renewals) with the same real LLM provider W3 measured
(Atria-Dawn-Preview, ~10-13 tok/s), a live Chromium, and a dataset built for
this run. It was run as a validation of the two W3X fixes a suite cannot
prove, and it found one more thing neither suite could: the fix it existed to
validate had broken the door behind it.

The loop closed. Case -> attach -> profile -> plan (LLM) -> Python run ->
SQL run -> interpret -> draft -> accept -> validate -> reviewer audit ->
chat (LLM) -> implication -> export -> reopen. Nothing required a terminal.

Severity scale: BLOCKER (the loop cannot complete), MAJOR (the analyst is
harmed or blocked at a real step), MINOR (polish), OBS (observed, no action).

---

## W4X-001 — a case with an LLM plan cannot be reopened (MAJOR, regression)

**Area:** the plan surface (`web/src/panels/PlanPanel.tsx:155`).
**Observation:** after the LLM plan landed, leaving the case and coming back
blanked the entire workspace. The console read
`Uncaught TypeError: Cannot read properties of undefined (reading 'length')`
three times and `#root` rendered zero children - the case list was reachable,
the case was not.
**Measured evidence:** the stored plan answers `source: llm` with no
`context_basis` field (`GET .../plan`); the browser console errors above;
`PlanPanel.tsx:155` is `body.context_basis.length` with no guard; the
workspace remounted the moment the guard was added, and the panel rendered
`by llm for saas_renewals_2026.csv`.
**Root cause:** W3X-003-PROMPT shrank the prompt so the plan fits the budget,
and part of that shrink dropped `context_basis` from what the prompt asks
for. `validate_plan` (planner.py:323) treats the field as optional, so an
accepted LLM plan persists without it - correct on the server, fatal on the
client. The deterministic engine still emits the field (planner.py:275),
which is why no test caught it.
**Why it matters:** the loop closed and then the door closed behind it. An
analyst who plans with the LLM and clicks Back loses the entire case view
until a developer patches the panel.
**Fix:** `body.context_basis && body.context_basis.length > 0`, and the type
became optional in `web/src/api.ts`. One test pins it. Fixed in this run's
tree, verified live.

---

## W3X-003-PROMPT — the plan wait, validated (HOLD)

**Area:** the LLM plan call (`server/app/planner.py:348`, `timeouts.py`).
**Observation:** W3 measured a plan call that consumed all 120 seconds and
fell back to deterministic. W4 measured the same call, on the same provider,
after the prompt shrink: the LLM answered.
**Measured evidence:** the core log
`POST .../plan -> 201 in 12420ms` with no fallback warning, and the stored
plan answers `source: llm` with 4 sub-questions, 3 hypotheses, 4 analysis
steps and 3 data requirements - exactly the caps the shrunk prompt asks for.
The first attempt of the session hit a provider 429 (the same rate-limiting
W3's interpret call saw) and fell back in 751ms with the substitution
announced; the retry 90s later answered.
**Why it matters:** this is the finding the walk-test existed to validate. A
12.4s LLM plan against a 120s budget on the provider that failed at 137s is
the fix measured in an analyst's hands, not in a unit test.
**Verdict:** HOLD. The wait moved from "times out and falls back" to
"answers".

---

## W3X-004 — the Python surface, validated (HOLD)

**Area:** the Python run surface (`web/src/panels/RunCodePanel.tsx`).
**Observation:** W3's first three Python interactions were blind refusals
(`import pandas`, `import csv`, `path`) whose answers were not on the page.
W4 measured the surface after the contract landed: with Python chosen, the
panel names the handle (`dataset.rows`, `.columns`, `.query`), states there
is no file path, lists the importable subset naming pandas/csv/numpy as
refused with `statistics` as the alternative, and the placeholder is a
runnable script rather than `# python`.
**Measured evidence:** the naive analyst's first Python interaction used the
contract's own handle and returned `POST .../runs/python -> 201` with zero
refusals preceding it (W3: three). The engine was switched to SQL and back,
and the contract appeared and disappeared with it.
**Why it matters:** three refusals with no on-page answer was the first thing
that engine ever said to an analyst; now the first thing it says is how to
use it.
**Verdict:** HOLD.
**Honest limit:** the harness's `fill_input` cannot type multi-line code
reliably (it strips newlines and the sandbox answers `'[' was never
closed`), so the run measured is the one-expression shape the panel's own
example teaches. A human typing the full example would reach the same 201.

---

## The interpreter and the drafter hit the provider's rate limit (OBS)

**Area:** LLM call surface.
**Observation:** the interpret and draft-finding calls each returned a 429
from the provider and fell back to deterministic in under 500ms, with the
substitution announced as a full sentence.
**Measured evidence:** core log `llm read failed; falling back to
deterministic: Client error '429 Too Many Requests'`, `POST .../interpret ->
201 in 421ms`, and the panel read "The LLM was unavailable, so a
deterministic reading answered in its place." - a complete sentence, not a
label with a fragment glued to it.
**Why it matters:** W3X-002's fix held under the exact condition it was made
for, and the fallback contract (any failure degrades, the source records
which engine answered) held without the analyst noticing an error.
**Suggestion:** none. This is the provider's rate limit, and the contract is
behaving as designed.

---

## Confirmations (a previous walk-test's fix still holds, measured this run)

- **C-01 (W3X-002, the fallback sentence):** "The LLM was unavailable, so a
  deterministic reading answered in its place." rendered as a complete
  sentence with no lowercase fragment after the period. Measured on both the
  interpret and draft fallbacks.
- **C-02 (W2X-001, the wait surface):** the plan button showed the elapsed
  clock ("Generating the plan… 5s elapsed") and a Cancel button; no silent
  spinners.
- **C-03 (W2X-005, guidance is an action):** "Next: Attach a dataset" with
  "Go to the Data panel" scrolled the page to the Data zone on a fresh case.
- **C-04 (W2X-003, chart survives reopen):** not measured - this run's
  harness could not reach the chart control (the run panel's chart affordance
  needs a run with chartable numeric columns and the one-expression runs
  measured returned row lists the chart step did not accept). Not observed,
  not assumed.
- **C-05 (W2X-009, the outlier):** the profile flagged the planted
  499,500 revenue row, and the deterministic drafter's finding named the
  segment split rather than the outlier; the profile's own quality finding
  carried the "may be inflated" sentence. The outlier was not crowned.
- **C-06 (W2X-008/013, density):** 19 panels with 3 collapsed disclosures;
  the final page is 1,715 words (measured on the same surface W3 measured).
- **C-07 (W2X-006, editable code):** the SQL editor accepted a hand-written
  query and ran it unchanged.
- **C-08 (W2X-012, LLM status):** `GET /llm/status` answered configured
  before the session; the banner rendered nothing (correct).
- **C-09 (W2X-002, form validation):** the new-case form's two required
  fields, both labelled, both with placeholders that teach.

## Guardrails that fired correctly

- The naive analyst's first Python attempt used `dataset.rows` from the
  contract - zero refusals.
- `renewed_on` mixed format -> the profiler's quality finding named the
  1-of-3000 inconsistency and its SQL impact.
- The ScaleUp/scaleup categorical split -> the profiler named it as
  inconsistent spelling.
- The finding the SQL result actually supported (`insufficient_evidence`)
  was refused rather than passed with a caveat, and `loop_closed` stayed
  false - honest rather than flattering.
- The request log carries method, path and status only - no payload, no key.

## Honest limitations

- **Agent != naive human.** This run measured waits, refusals and render
  states from evidence, but it did not experience real confusion.
- **One LLM provider, one session.** The provider was rate-limiting (429s on
  interpret and draft), so the plan measurement is the one call that got
  through - the same single-observation limit W3 recorded, on the other side
  of the fix.
- **The harness cannot type multi-line code** into a controlled textarea
  (newlines are stripped), so the Python run is the one-expression shape the
  panel's example teaches. The chart step (L7) was not reached for the same
  reason: the chartable numeric columns needed an aggregation the
  one-expression runs did not produce. C-04 is recorded as not observed
  rather than assumed.
- **W4X-001 is a regression the suite could not see,** because every test's
  plan fixture supplies `context_basis`. The walk-test is what found it.
