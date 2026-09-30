## Next action

**WALK-UX-005 is done, and it upgraded one observation to a task.** The
fifth walk-test had one question — can a human reach W3X-001 (the Data
panel accepting the same filename twice), or is it only an artefact of the
harness synthesising a `File`? — and the answer is measured: **a human can
reach it, and it needs a fix.** A real file on disk, attached a second time
through the same file input a human re-selecting a file uses, was accepted
silently: `POST .../datasets -> 201 in 39ms` with no warning, "Data sources:
2", two dataset rows with the identical filename, and every panel that
labels by filename left ambiguous. W3 recorded this as an observation
because its second attach came from a synthesised `File`; W5 reproduced it
through the real input path, so the frequency is now "every time the same
file is attached twice to one case".

The queued task is **W5X-001** (contract in `ai/TASKS.md`): a same-filename
refusal with a full sentence naming the existing dataset, matching how
`POST /cases` answers a duplicate question+dataset. The endpoint keeps no
duplicate check for filename within a case today; only case creation does.
Cheapest guard, no dedupe, no silent behaviour change.

Everything else held, on a new retail-inventory domain with no terminal:
the LLM plan answered in **6.5 seconds** with `source: llm` (W4: 12.4s; W3:
120s timeout), the Python contract was used with zero refusals, the case
reopened after the loop and rendered its LLM plan (W4X-001 did not
regress), and the finding validated honestly as `insufficient_evidence` so
`loop_closed` stayed false — the contract behaving, not a failure.

**Next: W5X-001 is the only open task.** Its acceptance criteria are written;
the walk-test material is the measured record.

Gates now: web 286/286, tsc clean, build ok; server 793/793, trace 48/48,
e2e 28/28. No code changed this walk-test, so the gate numbers carried from
v0.3.6.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **WALK-UX-005, the fifth walk-test** - a focused validation of the one open observation: W3X-001 (the Data panel accepts the same filename twice). A real file on disk, attached a second time through the same file input, was accepted silently (201 in 39ms, no warning, "Data sources: 2"), so the observation is now a MAJOR finding with measured frequency - queued as W5X-001. Everything else held: the LLM plan answered in 6.5s with `source: llm`, the Python contract was used with zero refusals, and the case reopened with its LLM plan intact. The loop's own verdict was honest - the finding validated `insufficient_evidence`, so `loop_closed` stayed false. Material and the harness's honest limits (partial data-dir isolation, several steps driven via the API) are in `walktest-w5/FINDINGS.md`.
- **WALK-UX-004, the fourth walk-test** - a validation run on a new domain with the same slow provider: the plan answered in 12.4s as an LLM (W3: 120s timeout and fallback), and the Python surface's first interaction went from three blind refusals to zero. Its one finding was a regression W3X-003-PROMPT introduced: PlanPanel read the optional `context_basis` unconditionally, so a case with an LLM plan could not be reopened. Fixed as W4X-001, verified live in the same run.
- **W4X-001, the plan panel's optional field** - a two-line guard for a bug every test fixture inoculated against: each one supplies `context_basis`, so the suite could not see it, and only reopening a real case with a real LLM plan could. Gates: web 286/286 (one test added), tsc clean, build ok; server unchanged.
- **v0.3.6, the release the W3X fixes ship in** - all three version files moved together, the sidecar repackaged so `/updates/latest` answers 0.3.6, and the DMG rebuilt from that bundle. Smoke-tested as a real launch: health ok, the case list and Templates render, the core exits with the shell. Gates: server 793/793, web 286/285 (five timing tests timed out under a parallel server run and re-ran green in isolation), tsc clean, build ok, trace 48/48, e2e 28/28.
- **W3X-003-PROMPT, the plan prompt's output size** - the walk-test measured a plan call that consumed the whole 120s budget and fell back deterministically, and the live measurement explained it: the prompt asked for the largest output of the six adapters and the provider runs at ~10-13 tok/s. The fix moved the request, not the contract, and a live re-measurement answered 508 tokens in 52.3s with `finish_reason: stop`. Five tests pin it.
- **W3X-002, the fallback sentence glued to its label** - a panel that appends its own context to `sourceLabel` was gluing a lowercase fragment to a sentence that already ends with a period. `sourceWith` capitalises the join; the sentences and the server's wording are untouched. Seven tests.
- **W3X-004, the Python surface refuses and teaches nothing** - the sandbox's own contract now sits on the panel that runs against it: the handle, the importable subset with the refused modules named, no file path, and the `result` shape. Six tests.
- **WALK-UX-003, the third walk-test** - a complete end-to-end run on a new domain with a real LLM and a live Chromium. The loop closed through the UI alone. Four findings, none a blocker, all now closed except W3X-001 which this fifth walk-test just upgraded.
