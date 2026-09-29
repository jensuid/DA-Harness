# WALK-UX-003 capture sheet

Walk-test 3 end to end. Real dev core on 8123 (LLM configured:
`DAH_LLM_API_KEY` / Atria-Dawn-Preview), real Chromium over the Vite dev
bundle, fresh isolated data dir `walktest-w3/data`. New domain (SaaS helpdesk),
new planted anomalies. Recorded live; nothing reconstructed from memory.

## V — pre-flight

- `V1` port 8123 free before start (no listener). OK.
- `V2` core up: `GET /health` -> `{"status":"ok"}`. OK.
- `V3` `GET /llm/status` -> `configured: true`, provider `DAH_LLM_API_KEY`,
  model `Atria-Dawn-Preview`. LLM really configured. OK.
- `V4` dataset built by `walktest-w3/make_dataset.py` (seeded 20260929):
  89 rows, 10 columns, 1 duplicate `ticket_id`, 2 blank `product`, 1
  out-of-range `satisfaction` (0), 1 US-style `created_date`, 1
  `resolution_hours` outlier (962.5, 41.9x the next largest), `enterprise` vs
  `Enterprise`. OK.
- `V5` DB clean: `GET /cases` -> `[]`, "No cases yet - create one." OK.
- `V6` baseline page: 593px viewport, case list + Templates. OK.

## L — the walk, as executed

- `L1` landed on an empty case list. First thing the app says: "Analysis
  Cases / New case / No cases yet - create one." Templates section explains
  itself in 2 sentences. No dead end.
- `L2` New case form: `Question *` (placeholder "Why did revenue decline?") and
  `Dataset *` (placeholder "sales.csv"). Submitted blank on purpose: two
  `role="alert"` sentences appeared, both fields `aria-invalid`, page did not
  navigate. The dataset label says "the name of the CSV, Parquet or Excel file
  ... You attach the file itself inside the case." — clear.
- `L2c` created the case with the real question. Landed on the workspace at
  stage `data`, "Next: Attach a dataset".
- `L4` the "Go to the Data panel" button scrolled the page (0 -> 108px) and put
  the Data zone in view. Not a dead end.
- `L6` attached the CSV. **Incident W3X-001:** the panel accepted a
  `DataTransfer`-synthesised file and POSTed it; a second dataset row was
  created with the same filename.
- `L7` "Profile this dataset" -> profiled the real 89-row file. All six planted
  anomalies surfaced as quality findings (mixed type in `created_date`, 93.3%
  missing `reopened`, 1 duplicate, the 962.5 outlier at 41.9x, `tier` spelling
  split, 2 missing `product`). Quality gate works.
- `L8` "Generate an analysis plan": the elapsed clock ran ("Generating the
  plan… 106s elapsed" + Cancel). The LLM call **timed out at the 120s
  ceiling** and the deterministic plan answered with a visible fallback
  sentence. **Finding W3X-002 (the sentence itself) and W3X-003 (the 120s
  the analyst waits).**
- `L9` SQL run: `SELECT tier, COUNT(*) ... GROUP BY tier` -> 4 rows. First
  `POST /runs` attempt used `{code: ...}` and got a 422 naming the missing
  `sql` field; the correct shape `{sql: ...}` returned 201.
- `L9-PY` Python run: `import pandas` refused (400 "module 'pandas' is not
  allowed in analysis code"); `import csv` also refused; the sandbox's own
  `dataset.rows` handle + `statistics` worked (3 rows, median resolution by
  tier). **Finding W3X-004: the panel tells the analyst none of this.**
- `L10` run appears in Runs with Interpret / Draft a finding / Show the rows.
- `L11` chart rendered (bar, `avg_resolution by tier`) from the stored result.
- `L12` Interpret: LLM 429 -> deterministic fallback in 441ms, announced.
- `L13` Draft a finding: LLM produced a draft that **failed validation**
  ("quotes values absent from the result: 2.0, 2026.0"), deterministic draft
  answered, announced. Guard works.
- `L13b` accepted the draft -> finding recorded, evidence graph lists it.
- `L14` Validate -> `partially_supported`, nine checks each with a mark and a
  sentence (3 warnings: `data`, `method`, `alternative_explanations`).
- `L16c` wrote one implication through "Add implication" + the labelled input;
  "Save implications" persisted it ("1 saved"), confirmed by
  `GET /decision` (`loop_closed: true`).
- `L17` back to the list and reopened: chart still drawn, rows still shown,
  finding and implication present. State survives.
- `L18c` reviewer agent proposed an audit and it was approved: "9 axes, 9 pass,
  0 concern, 0 fail", recorded beside the finding.
- `L19e` asked the case a question. The LLM answered in 66.8s with grounds
  citing the dataset, the Python run and the finding — and honestly said the
  case does not isolate Q2 Enterprise. `by llm`, cited.
- `L20` "Export analysis case" triggered a download; `GET /export` is a
  24,877-byte self-contained package (runs 3, findings 1, charts 1,
  validations 1, agent_steps 1).

## F — measurements (facilitator)

- `F1` workspace height with one case fully worked: measured live.
- `F2` quality findings surfaced: 6, every one with a "Potential impact"
  sentence. No silent anomaly.
- `F3` LLM call outcomes this session: plan timed out at 120s (fallback),
  interpret 429 (fallback in 441ms), draft schema-rejected (fallback), chat
  200 in 66.8s. **1 of 4 LLM calls answered.**
- `F4` every fallback was announced on screen with a full sentence.
- `F5` stage rail advanced correctly: data -> profile -> plan -> evidence ->
  validated, and the reopen kept it.

## D — debrief

- `D1` The loop is end-to-end usable with no terminal. A naive analyst can go
  from an empty case to a validated finding, a chart, an audited run, a
  written implication and an export without leaving the UI.
- `D2` The dominant harm is no longer density (W2X-008/013 fixed that: 19
  panels, 3 disclosures, one page). It is the wait. The plan call consumed the
  whole 120s budget and produced a deterministic answer the analyst could have
  had instantly.
- `D3` The second harm is the Python surface's silence: three refusals, no
  guidance on the page, only a 400.
- `D4` The evidence/decision surfaces read clearly; the nine-check validation
  block is the most informative thing on the page.
- `D5` The guardrails that refused are all correct refusals (422 wrong field,
  pandas/csv refused, LLM draft schema-rejected). Their UX is what lags.
- `D6` No data leaked: the request log carries method/path/status only.
