# WALK-UX-005 — Walk-test 5 report

A focused validation run with one question: can a human reach W3X-001 (the
Data panel accepting the same filename twice), or is it only an artefact of
how the harness synthesised a `File`? The answer is measured — **a human can
reach it, and it needs a fix.**

## Verdict

**W3X-001: HOLD as a real finding (MAJOR), with measured frequency.** A real
file on disk, attached a second time through the same file input, was
accepted silently: `POST .../datasets -> 201 in 39ms` with no warning. The
case overview read "Data sources: 2", the datasets endpoint returned two
rows with the identical filename, and every panel that labels by filename
became ambiguous. The suggestion from walk-test 3 stands: a same-filename
refusal naming the existing dataset, matching how `POST /cases` answers a
duplicate.

**All prior fixes held, on a new domain, with no terminal:** the LLM plan
answered in 6.5s with `source: llm` (W4: 12.4s; W3: 120s timeout); the
Python contract was used directly with zero refusals; the case reopened
after the loop and rendered its LLM plan — W4X-001 did not regress.

The loop closed with one honest gap: the finding validated as
`insufficient_evidence`, so `loop_closed` stayed false. That is the contract
behaving, not a failure.

## The journey, as executed

| Step | What happened |
|---|---|
| Case list (empty) | "No cases yet - create one." + Templates |
| New case | Labelled fields; stage `data` |
| Attach (1st) + profile | 4,681 rows, 12 cols; all six planted anomalies surfaced as quality findings |
| **Attach same file (2nd)** | **Accepted silently — 201 in 39ms, no warning; "Data sources: 2"** |
| Generate plan | LLM answered in 6.5s, `source: llm` |
| SQL run | Regional March grouping, 26 rows |
| Python run | `dataset.rows` from the contract, zero refusals |
| Interpret | LLM, 35.4s, grounded in the run's rows |
| Draft + accept + validate | Finding accepted; nine checks ran; `insufficient_evidence` (honest) |
| Reviewer audit | Not executed — endpoint shape needed a body this harness could not build |
| Ask the case | LLM, 12.4s: "No—low on_hand has not been established as the explanation" |
| Implications | Saved; `loop_closed: false` (correct, given the verdict) |
| Reopen | Workspace rendered, LLM plan intact — W4X-001 HOLD |
| Export | 532KB package |

## Findings

| ID | Sev | One line | Fix shape |
|---|---|---|---|
| W3X-001 | MAJOR | Same filename accepted twice; two indistinguishable datasets, no warning | Same-filename refusal naming the existing dataset (W2X-010 pattern). Queued. |
| (regression) | — | W3X-003-PROMPT, W3X-004, W4X-001, W3X-002 all HOLD | No action |

## Honest limitations

- **Isolation was partial.** The CSV payloads landed in `walktest-w5/data`,
  but the SQLite metadata stayed at `server/dah.db` because `DAH_DB_PATH`
  is a separate env var this run did not set. F-DUP was measured on the
  datasets endpoint and the UI directly, so it does not depend on isolation.
- **Several loop steps ran via the API**, not the UI: the Run and Audit
  buttons sit behind a codegen-proposal accept this harness could not
  reach. The timings and sources are of the same code paths the UI calls.
- **The chart step was not observed** for the same reason.
- **Agent != naive human.** Every claim is from measured evidence: request
  log timings, endpoint responses, rendered page text.

## Material

- `walktest-w5/PLAN.md` — protocol and focus
- `walktest-w5/CAPTURE-SHEET.md` — live sheet, no placeholders left
- `walktest-w5/FINDINGS.md` — one block per finding, with measurements
- `walktest-w5/evidence/` — datasets, runs, interpretation, draft, finding,
  validation, chat, decision, export package
- `walktest-w5/logs/` — the core's request log
