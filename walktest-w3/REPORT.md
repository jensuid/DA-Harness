# WALK-UX-003 — Walk-test 3 report

A complete end-to-end walk-test of DAH on a domain the project has never
analysed, with a real LLM configured and a live Chromium, executed against the
v0.3.5 release tree. One session, one case, one dataset built for this run.

## Verdict

**The loop is end-to-end usable with no terminal.** A first-time analyst can
travel from an empty case list to a validated finding, an on-screen chart, a
reviewer-audited run, a written implication and a self-contained export
without ever leaving the UI or guessing an endpoint. Walk-test 2's density
problem is gone (19 panels, 3 collapsed disclosures, 1,715 words on the final
page — the validation block is the densest thing on it, by design).

Four new findings. None is a blocker, and none breaks the loop. Three are
polish on surfaces that already work (microcopy, the wait, the Python
surface's silence); one is an artifact of how this session drove the browser
and is recorded rather than fixed.

## The journey, as executed

| Step | What happened |
|---|---|
| Case list (empty) | "No cases yet - create one." + a Templates section that explains itself |
| New case, blank submit | Two `role="alert"` sentences, both fields `aria-invalid`, no navigation |
| Create | Stage `data`, "Next: Attach a dataset" |
| Guidance button | "Go to the Data panel" scrolled the page to the Data zone |
| Attach + profile | All six planted anomalies surfaced as quality findings |
| Generate plan | Elapsed clock + Cancel; LLM timed out at 120s, deterministic plan, substitution announced |
| SQL run | 4 rows (avg resolution / satisfaction by tier) |
| Python run | Sandbox's `dataset.rows` + `statistics` -> 3 rows, tier split repaired |
| Chart | Bar, `avg_resolution by tier`, drawn from the stored result |
| Interpret | LLM 429 -> deterministic reading in 441ms, announced |
| Draft finding | LLM draft schema-rejected (quoted absent values) -> deterministic draft, announced |
| Accept + validate | `partially_supported`, nine checks each with a mark and a sentence |
| Reviewer agent | Proposed an audit; approve -> "9 axes, 9 pass, 0 concern, 0 fail" |
| Ask the case | LLM answered in 66.8s, cited dataset/run/finding, and honestly said the case does not isolate Q2 Enterprise |
| Implication | Saved; `GET /decision` -> `loop_closed: true` |
| Back to list, reopen | Chart, rows, finding and implication all survived |
| Export | 24,877-byte self-contained package |

## New findings

| ID | Sev | One line | Fix shape |
|---|---|---|---|
| W3X-002 | MAJOR | The fallback sentence is glued to the label it replaces: *"…answered in its place. for helpdesk_tickets_2026.csv"* | Panel appends the filename after the sentence; make it its own clause |
| W3X-003 | MAJOR | The analyst waits the full 120s budget for a plan the deterministic engine writes in under a second | Bound the wait per engine — but check why the plan call took 120s when chat took 67s first |
| W3X-004 | MAJOR | The Python surface refuses three times (`pandas`, `csv`, `path`) and explains none of them on the page | Show the contract on the panel: `dataset.rows`, the importable subset, one example |
| W3X-001 | OBS | The Data panel accepted the same filename twice | Harness artifact; record only. A same-filename refusal would mirror W2X-010 |

Effort vs impact: W3X-002 is the cheapest (one line per call site's shape) and
lands on every LLM-backed panel. W3X-004 is the highest impact for an analyst
who reaches for Python first — three refusals with no on-page answer is the
first thing that engine ever says to them. W3X-003 needs a root cause before a
timeout change; the measured gap between the 120s plan call and the 67s chat
call on the same provider says the plan call is doing something different.

## Confirmations (nine previous fixes, measured live this run)

Recorded because a walk-test that only reports new findings cannot tell you
the old ones regressed: W2X-001 (the wait surface), W2X-002 (form answers),
W2X-003 (chart survives reopen), W2X-004 (no false unsaved-edits claim),
W2X-005 (guidance is an action), W2X-006 (editable code), W2X-008 + W2X-013
(density), W2X-009 (the outlier is named, not crowned), W2X-012 (the LLM
status surface). All nine still hold, each verified against the running core
rather than from the suite.

## Guardrails that fired correctly

- `POST /runs` with a `code` field -> 422 naming the missing `sql` field
- `import pandas`, `import csv` -> 400 naming the refused module
- An LLM draft quoting values absent from the result -> schema-rejected, deterministic draft answered, substitution announced
- The request log carries method, path and status only — no payload, no key

## Honest limitations

- **Agent != naive human.** This session measured surfaces, waits and refusals
  from evidence, but it did not experience real confusion. "Hard to
  understand" claims above are backed by measured refusal counts and elapsed
  time, not by a feeling.
- **W3X-001 is synthetic.** The harness cannot hand a real file to the input,
  so the second dataset came from a `DataTransfer`-built File. A human
  re-selecting the same file would reach the same state, but the finding's
  frequency is unmeasured.
- **One LLM provider, one session.** The 120s plan timeout is one observation
  on one provider while the provider was rate-limiting (a 429 landed on the
  interpret call minutes earlier). The timeout finding names the measured
  behaviour, not a general property.

## Pipeline status on this tree

- server pytest: 788 passed
- web vitest: 272 passed (one file's timing test timed out at 5s under load,
  re-ran green: 10/10)
- tsc -b: clean; vite build: ok
- gates: e2e, trace — see the logs in `walktest-w3/logs/`

## Material

- `walktest-w3/make_dataset.py` — the seeded dataset builder
- `walktest-w3/CAPTURE-SHEET.md` — the live sheet, no `to be recorded` left
- `walktest-w3/FINDINGS.md` — one block per finding, severity and evidence
- `walktest-w3/evidence/` — the SQL and Python runs, the export package, the
  final page's DOM text and screenshot
- `walktest-w3/logs/` — the core's request log, the suite and gate logs
