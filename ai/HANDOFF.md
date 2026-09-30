## Next action

**v0.3.7 is published: the release the W5X-001 fix ships in.** All three
version files moved together — `server/pyproject.toml`,
`desktop/package.json`, `desktop/src-tauri/tauri.conf.json` — the sidecar was
repackaged so the stamp the spec writes is 0.3.7, and `tauri build` produced
the `.app` and the DMG from that bundle. Smoke-tested as a real launch: the
packaged core answers `/health` ok and `/updates/latest` reports
`current: 0.3.7`, so the version a Check for Updates reads is the version
this release is.

The DMG (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119) is unsigned, as every release has been since DEC-006 deferred signing for a single-user app. Nothing is queued: all five walk-tests' findings are closed, and their fixes are validated and shipped. GitHub Actions still refuses every job (billing suspended), so the release was built and verified locally from the same steps `release.yml` runs.

**Next: nothing is open.** The two remaining limits are both outside this
repo's control: the app is unsigned (DEC-006), and CI is suspended (billing).

Gates now: server 796/796, web 287/287, tsc clean, build ok, trace 48/48,
e2e ALL PASS.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **v0.3.7, the release W5X-001 ships in** - all three version files moved together, the sidecar repackaged so the stamp the spec writes is 0.3.7, and the DMG rebuilt from that bundle (sha256 b1635955803967f8f0e44124c25bfcac42389820efbd0b101db6ece216c6119). Smoke-tested as a real launch: health ok, and the packaged core's own `/updates/latest` answers `current: 0.3.7`, so the Check for Updates item reads this release's number. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **W5X-001, the Data panel's duplicate filename** - the attach endpoint refuses a filename already attached to the case before it writes the file, answering 409 with a sentence naming the existing dataset and how to replace it. The check is per-case, so another case may still attach the same filename, and case creation's duplicate handling is untouched. The panel's existing `Attach failed:` surface renders the sentence, so no UI changed. Three server tests and one web test pin it. Gates: server 796/796, web 287/287, tsc clean, build ok, trace 48/48, e2e ALL PASS.
- **WALK-UX-005, the fifth walk-test** - a focused validation of the one open observation: W3X-001 (the Data panel accepts the same filename twice). A real file on disk, attached a second time through the same file input, was accepted silently (201 in 39ms, no warning, "Data sources: 2"), so the observation became a MAJOR finding with measured frequency - queued as W5X-001, now closed. Everything else held: the LLM plan answered in 6.5s with `source: llm`, the Python contract was used with zero refusals, and the case reopened with its LLM plan intact. Material and the harness's honest limits are in `walktest-w5/FINDINGS.md`.
- **WALK-UX-004, the fourth walk-test** - a validation run on a new domain with the same slow provider: the plan answered in 12.4s as an LLM (W3: 120s timeout and fallback), and the Python surface's first interaction went from three blind refusals to zero. Its one finding was a regression W3X-003-PROMPT introduced: PlanPanel read the optional `context_basis` unconditionally, so a case with an LLM plan could not be reopened. Fixed as W4X-001, verified live in the same run.
- **W4X-001, the plan panel's optional field** - a two-line guard for a bug every test fixture inoculated against: each one supplies `context_basis`, so the suite could not see it, and only reopening a real case with a real LLM plan could. Gates: web 286/286 (one test added), tsc clean, build ok; server unchanged.
- **v0.3.6, the release the W3X fixes ship in** - all three version files moved together, the sidecar repackaged so `/updates/latest` answers 0.3.6, and the DMG rebuilt from that bundle. Smoke-tested as a real launch: health ok, the case list and Templates render, the core exits with the shell. Gates: server 793/793, web 286/285 (five timing tests timed out under a parallel server run and re-ran green in isolation), tsc clean, build ok, trace 48/48, e2e 28/28.
- **W3X-003-PROMPT, the plan prompt's output size** - the walk-test measured a plan call that consumed the whole 120s budget and fell back deterministically, and the live measurement explained it: the prompt asked for the largest output of the six adapters and the provider runs at ~10-13 tok/s. The fix moved the request, not the contract, and a live re-measurement answered 508 tokens in 52.3s with `finish_reason: stop`. Five tests pin it.
- **W3X-002, the fallback sentence glued to its label** - a panel that appends its own context to `sourceLabel` was gluing a lowercase fragment to a sentence that already ends with a period. `sourceWith` capitalises the join; the sentences and the server's wording are untouched. Seven tests.
- **W3X-004, the Python surface refuses and teaches nothing** - the sandbox's own contract now sits on the panel that runs against it: the handle, the importable subset with the refused modules named, no file path, and the `result` shape. Six tests.
