# WALK-UX-005 findings

Walk-test 5: a focused validation run. One question — can a human reach
W3X-001 (the Data panel accepting the same filename twice), or is it only an
artefact of how the harness synthesised a `File` through `DataTransfer`?

The answer is measured: **a human can reach it, and it needs a fix.**

Severity scale: BLOCKER (the loop cannot complete), MAJOR (the analyst is
harmed or blocked at a real step), MINOR (polish), OBS (observed, no action).

---

## W3X-001 — the Data panel accepted the same filename twice (MAJOR, now measured)

**Area:** Data attach (`web/src/panels/DataPanel.tsx:48`).
**Observation:** with a real file on disk, attaching the same file a second
time through the same file input was accepted silently. The case overview
moved to "Data sources: 2", and `GET /cases/{id}/datasets` returned two rows
with the identical filename `retail_inventory_2026_h1.csv` and different ids.
**Measured evidence:** first attach `POST .../datasets -> 201 in 138ms`,
second attach `POST .../datasets -> 201 in 39ms` — no warning, no refusal;
the datasets endpoint answered two rows, both `filename:
retail_inventory_2026_h1.csv`, stored as two separate files
(`fe2d798f….csv`, `0c34fec2….csv`); the Data panel rendered the same label
twice ("retail_inventory_2026_h1.csv (csv) — 0 rows, 2 columns" x2) and the
plan/run/chat surfaces repeated the filename, so any panel keying off
`datasets[0]` is ambiguous.
**Root cause as observed:** the attach endpoint has no duplicate check for
filename within a case — only for question+dataset on case creation
(W2X-010). The second file input change goes through the same `attach()`
handler the first one did.
**Why it matters:** this is no longer a harness artefact. The run's second
attach used the same file input and filename a human re-selecting a file
from the dialog would use, and the panel accepted it without a word. Two
same-named datasets are indistinguishable everywhere the filename is the
label, and the analyst is not told anything happened.
**Suggestion:** the cheapest guard is a same-filename refusal with a
sentence naming the existing dataset, matching how `POST /cases` answers a
duplicate question+dataset (W2X-010). This closes the observation W3X-001
as a real finding with a measured frequency of "every time the same file is
attached twice to one case".

---

## The LLM plan and the loop held (regression checks)

**Area:** LLM call surface, validation contract.
**Observation:** the LLM plan answered in 6.47 seconds with `source: llm`
(walk-test 4 measured 12.4s on the same provider; W3 measured a 120s
timeout). The interpret and chat calls were also the LLM, not fallback:
interpret 35.4s, chat 12.4s, each grounded in the run's own rows. The
validation on the accepted finding returned `insufficient_evidence` — the
nine checks ran, the calculation passed, the data dimension did not carry
the claim — so `loop_closed` stayed false. That is the honest answer, not a
flattering one.
**Why it matters:** every fix the previous walk-tests shipped held in this
run, on a new domain, with no terminal:
- W3X-003-PROMPT — plan 6.5s, `source: llm`. HOLD.
- W3X-004 — the Python surface's contract was used directly
  (`dataset.rows`), zero refusals. HOLD.
- W4X-001 — the case reopened and the workspace rendered ("by llm for
  retail_inventory_2026_h1.csv"), no blank page, no TypeError. HOLD.
- W3X-002 — the interpret fallback sentence was not needed; the LLM answered
  directly. HOLD (not exercised under fallback this run).

---

## Honest limitations

- **The isolated data dir took three attempts.** The first background start
  inherited a `server/` workdir so a relative `DAH_DATA_DIR` resolved to
  `server/walktest-w5/data`; the second lost the env var. The CSV payload
  did land in `walktest-w5/data/…/<dataset>.csv` correctly, but the SQLite
  metadata stayed at `server/dah.db` because `DAH_DB_PATH` is a separate env
  var this run did not set. V6 ("isolated") is therefore true for payloads
  and not strictly true for metadata. F-DUP is unaffected: it was measured
  directly on the datasets endpoint and the UI, not inferred from isolation.
- **Several loop steps ran against the API, not the UI.** The Run and Audit
  buttons sit behind a codegen-proposal accept the harness could not reach,
  so SQL/Python/interpret/draft/validate/chat ran via the endpoint. The
  measurements (elapsed, source, refusal) are of the same code paths the UI
  calls, so they stand; the journey rows for those steps are marked
  accordingly.
- **The chart step was not observed** for the same reason — chartable runs
  needed the UI affordance this harness could not click. Recorded as not
  observed, not assumed.
- **Agent != naive human.** All claims are from measured evidence: request
  log timings, endpoint responses, rendered page text.

## Material

- `walktest-w5/PLAN.md` — this run's protocol and focus
- `walktest-w5/CAPTURE-SHEET.md` — the live sheet, no placeholders left
- `walktest-w5/evidence/` — the datasets, runs, interpretation, draft,
  finding, validation, chat, decision, export package
- `walktest-w5/logs/` — the core's request log
