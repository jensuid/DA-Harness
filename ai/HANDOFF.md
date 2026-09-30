## Next action

**W5X-001 is done: the Data panel no longer accepts the same filename twice.**
The fifth walk-test measured a real file, attached a second time through the
same file input a human re-selecting a file uses, being accepted silently —
two dataset rows with the identical filename, no warning, and every panel
that labels by filename left ambiguous. The attach endpoint now checks for a
same-filename dataset in the case **before it writes the file**, and answers
409 with a sentence the analyst can act on: "sales.csv is already attached to
this case as dataset d1; delete it first if you want to replace it."

The refusal follows the W2X-010 pattern the contract named: a full sentence
identifying the collision, not a bare error. The `Attach failed:` surface the
DataPanel already owned renders it, so no UI code changed — the sentence is
the answer, and the panel was already built to show sentences. Three server
tests pin the behaviour (same filename refused with the sentence and nothing
written; two different filenames both accepted; the same filename still
allowed in a *different* case, because its dataset is never this case's
label), and one web test asserts the refusal renders.

The check happens after the format guard and before the content read, so it
refuses before touching disk. Non-goals held: no silent dedupe, and case
creation's duplicate handling is untouched.

**Next: nothing is queued.** All five walk-tests' findings are closed. Two
things outside this repo's control, unchanged: GitHub Actions still refuses
every job (billing suspended), and the packaged app is unsigned by DEC-006.

Gates now: server 796/796 (three tests added), web 287/287, tsc clean, build
ok, trace 48/48, e2e ALL PASS.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **W5X-001, the Data panel's duplicate filename** - the attach endpoint refuses a filename already attached to the case before it writes the file, answering 409 with a sentence naming the existing dataset and how to replace it. The check is per-case, so another case may still attach the same filename, and case creation's duplicate handling is untouched. The panel's existing `Attach failed:` surface renders the sentence, so no UI changed. Three server tests and one web test pin it. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **WALK-UX-005, the fifth walk-test** - a focused validation of the one open observation: W3X-001 (the Data panel accepts the same filename twice). A real file on disk, attached a second time through the same file input, was accepted silently (201 in 39ms, no warning, "Data sources: 2"), so the observation became a MAJOR finding with measured frequency - queued as W5X-001, now closed. Everything else held: the LLM plan answered in 6.5s with `source: llm`, the Python contract was used with zero refusals, and the case reopened with its LLM plan intact. Material and the harness's honest limits (partial data-dir isolation, several steps driven via the API) are in `walktest-w5/FINDINGS.md`.
- **WALK-UX-004, the fourth walk-test** - a validation run on a new domain with the same slow provider: the plan answered in 12.4s as an LLM (W3: 120s timeout and fallback), and the Python surface's first interaction went from three blind refusals to zero. Its one finding was a regression W3X-003-PROMPT introduced: PlanPanel read the optional `context_basis` unconditionally, so a case with an LLM plan could not be reopened. Fixed as W4X-001, verified live in the same run.
- **W4X-001, the plan panel's optional field** - a two-line guard for a bug every test fixture inoculated against: each one supplies `context_basis`, so the suite could not see it, and only reopening a real case with a real LLM plan could. Gates: web 286/286 (one test added), tsc clean, build ok; server unchanged.
- **v0.3.6, the release the W3X fixes ship in** - all three version files moved together, the sidecar repackaged so `/updates/latest` answers 0.3.6, and the DMG rebuilt from that bundle. Smoke-tested as a real launch: health ok, the case list and Templates render, the core exits with the shell. Gates: server 793/793, web 286/285 (five timing tests timed out under a parallel server run and re-ran green in isolation), tsc clean, build ok, trace 48/48, e2e 28/28.
- **W3X-003-PROMPT, the plan prompt's output size** - the walk-test measured a plan call that consumed the whole 120s budget and fell back deterministically, and the live measurement explained it: the prompt asked for the largest output of the six adapters and the provider runs at ~10-13 tok/s. The fix moved the request, not the contract, and a live re-measurement answered 508 tokens in 52.3s with `finish_reason: stop`. Five tests pin it.
- **W3X-002, the fallback sentence glued to its label** - a panel that appends its own context to `sourceLabel` was gluing a lowercase fragment to a sentence that already ends with a period. `sourceWith` capitalises the join; the sentences and the server's wording are untouched. Seven tests.
- **W3X-004, the Python surface refuses and teaches nothing** - the sandbox's own contract now sits on the panel that runs against it: the handle, the importable subset with the refused modules named, no file path, and the `result` shape. Six tests.
