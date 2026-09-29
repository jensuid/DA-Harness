# WALK-UX-003 findings

Walk-test 3: a complete end-to-end run of DAH on a brand-new domain (SaaS
helpdesk tickets) with a real LLM configured and a live Chromium, executed on
the v0.3.5 release tree. Thirteen findings; three are real product findings,
nine are confirmations that a previous walk-test's fix still holds, and one is
an artifact of how this session drove the browser (recorded, not a defect).

The loop closed. Case -> attach -> profile -> plan -> SQL run -> Python run ->
chart -> finding -> validation -> reviewer audit -> decision implication ->
export all executed through the app's own surfaces. Nothing required a
terminal.

Severity scale: BLOCKER (the loop cannot complete), MAJOR (the analyst is
harmed or blocked at a real step), MINOR (polish), OBS (observed, no action).

---

## W3X-001 — the Data panel accepted the same filename twice (OBS, harness artifact)

**Area:** Data attach (`web/src/panels/DataPanel.tsx:48`).
**Observation:** the panel accepted two files with the identical name
`helpdesk_tickets_2026.csv` and created two dataset rows. The evidence graph
read "2 datasets", the run/code/chart surfaces all listed the filename twice,
and `datasets[0]` pointed at whichever row sorted first.
**Measured evidence:** `GET /cases/{id}/datasets` returned two rows, both
`filename: helpdesk_tickets_2026.csv`, different `id`s. The duplicate was
deleted (`DELETE .../datasets/{id}` -> 204) and the run continued.
**Why it matters:** two same-named datasets are indistinguishable everywhere
the filename is the label, and the panels that key off `datasets[0]` become
ambiguous.
**Root cause as observed:** the walk-test synthesised a `File` object through
`DataTransfer` because the harness cannot hand a real file to the input. A
human selecting the same file twice from the dialog would do the same thing;
the endpoint has no duplicate check for filename, only for question+dataset on
case creation (W2X-010).
**Suggestion:** worth a real finding only if a human can reach it. The cheapest
guard is a same-filename refusal with a sentence naming the existing dataset,
matching how `POST /cases` answers a duplicate. Recorded as OBS because this
session created it synthetically.

---

## W3X-002 — the fallback sentence is glued to the label it replaces (MAJOR, microcopy)

**Area:** engine-source announcement (`web/src/sourceLabel.ts:16-24`,
rendered by `PlanPanel.tsx:154`).
**Observation:** when the plan LLM timed out, the panel rendered:

    The LLM was unavailable, so a deterministic plan answered in its place. for helpdesk_tickets_2026.csv

The sentence is correct and visible — the fix this replaces (a bare
`deterministic fallback` label that only a developer reads) is clearly still
working. But the trailing " for {filename}" is appended by the panel after the
sentence, so the substitution notice ends with a lowercase fragment that reads
as a punctuation error rather than a sentence.
**Measured evidence:** the exact rendered string is in
`walktest-w3/evidence/final-page.txt`; the same shape appears for the
interpret and draft fallbacks.
**Why it matters:** the sentence is the analyst's only signal that the engine
they configured did not answer. If it reads as a typo, the signal is weaker
than the fix intended.
**Suggestion:** the panel appends ` for {filename}` to whatever `sourceLabel`
returns. Either the sentence ends with a colon and the filename follows as its
own clause, or the panel renders the sentence, then the filename as a separate
note. One-line change in each of the seven call sites' shared shape.

---

## W3X-003 — the analyst waits 120 seconds for a deterministic plan (MAJOR, the wait)

**Area:** LLM timeout surface (`server/app/timeouts.py:33`, the 120s default).
**Observation:** "Generate an analysis plan" showed the elapsed clock and a
Cancel button (W2X-001's fix, working exactly as designed) and then consumed
the entire 120-second budget before the endpoint's read timed out and the
deterministic plan answered. That is two minutes of a spinning button for an
answer the deterministic engine produces in under a second.
**Measured evidence:** the core log —
`POST .../plan -> 201 in 120552ms`, with
`WARNING app.planner llm plan failed; falling back to deterministic: The read
operation timed out`. The same session's interpret call failed in 441ms with a
429 and the chat call succeeded in 66.8s, so the plan call was the outlier.
**Why it matters:** the wait is now honest (it says how long it has been and
can be cancelled), but it is still two minutes. W2X-001 fixed the *silence*;
the *duration* is what remains. An analyst who hits this on every plan learns
to click and walk away.
**Suggestion (offered, not assumed):** the timeout is one global number for
every engine. A per-engine budget, or a shorter plan/generate-code budget
(plan is the most-schema-constrained call and the cheapest to fall back from),
would bound the wait to something a human tolerates. Root cause worth checking
first: why the plan endpoint takes 120s when the chat endpoint answers in
67s on the same provider — the call that timed out may be a prompt-size or
streaming issue rather than a slow model.

---

## W3X-004 — the Python surface refuses three times and explains none of them (MAJOR, microcopy + UX)

**Area:** the Python run surface (`web/src/panels/RunCodePanel.tsx:94`,
`server/app/python_exec.py:64-85`).
**Observation:** a first-time analyst writing Python against the dataset hit
three refusals in a row, and the panel told them nothing about any of them
until the 400 came back:

1. `import pandas` -> 400 "module 'pandas' is not allowed in analysis code"
2. `import csv` -> 400 "module 'csv' is not allowed in analysis code"
3. `path` (the variable the SQL placeholder suggests exists) -> not the
   sandbox's handle; the correct surface is `dataset.rows`, which the page
   never shows.

Only after guessing `dataset.rows` + the allowed stdlib (`statistics`) did the
run succeed. The sandbox is correct to refuse — refusing is the security
property — but the analyst's only teacher is the error.
**Measured evidence:** three 400s in `walktest-w3/logs/core-stdout.log` and
the successful 201 that followed; the panel's placeholder is `# python` with no
mention of `dataset.rows` or the module allowlist.
**Why it matters:** the Python engine is the one a Python-fluent analyst
reaches for first, and its first three interactions are all refusals whose
answer is not on the page. The SQL surface has the same problem in a milder
form (the `read_csv_auto(?)` placeholder is shown in the codegen panel, not
this one).
**Suggestion:** show the contract on the panel — one note naming the dataset
handle (`dataset.rows`), that only the stdlib subset is importable, and a
one-line example. The allowlist already exists as a frozenset; the refusals
could name a suggested alternative (`statistics` instead of `pandas`) the way
the profile's quality findings name an action.

---

## Confirmations (a previous walk-test's fix still holds, measured this run)

These are recorded because a walk-test that only reports new findings cannot
tell you the old ones regressed. All nine were exercised against a real core.

- **C-01 (W2X-002, form validation):** blank submit -> two `role="alert"`
  sentences, both fields `aria-invalid`, no page navigation. Measured live.
- **C-02 (W2X-005, guidance is an action):** "Next: Attach a dataset" + "Go to
  the Data panel" scrolled the page to the Data zone (scrollY 0 -> 108). Not a
  dead end.
- **C-03 (W2X-001, the wait surface):** every LLM-backed button showed an
  elapsed clock and a Cancel button ("Generating the plan… 106s elapsed").
  No silent spinners, no shared busy flag across panels.
- **C-04 (W2X-003, chart survives reopen):** after back-to-list and reopen the
  bar chart was still drawn and the run rows still shown.
- **C-05 (W2X-004, false unsaved-edits):** the implications editor never
  claimed unsaved edits on open; "unsaved edits" appeared only on the Context
  panel, which had genuinely been touched. Save cleared to "1 saved".
- **C-06 (W2X-008/013, density):** 19 panels with 3 collapsed disclosures;
  the final page is 1,715 words, and the validation block is the densest thing
  on it by design. The measured density problem of walk-test 2 is gone.
- **C-07 (W2X-006, editable code):** the SQL editor accepted a hand-written
  query and ran it unchanged.
- **C-08 (W2X-009, the outlier):** the deterministic drafter named the
  profile-flagged outlier (`resolution_hours` 962.5, 41.9x) rather than
  crowning it; the validation's `method` check separately warned that an
  average over that column "describes the outlier more than the typical value".
- **C-09 (W2X-012, LLM status):** `GET /llm/status` answered configured before
  the session; the banner rendered nothing (correct — a green banner on every
  screen is noise).

## Guardrails that fired correctly

- `POST /runs` with `{code: ...}` -> 422 naming the missing `sql` field.
- `import pandas` / `import csv` -> 400 naming the refused module.
- The LLM draft that quoted values absent from the result (2.0, 2026.0) was
  schema-rejected, and the deterministic draft answered in its place with the
  substitution announced.
- The request log carries method, path and status only — no payload, no key.
