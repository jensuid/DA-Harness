## Next action

**WALK-UX-004 is done: both W3X fixes held, and the walk-test found the one
thing no suite could.** The fourth walk-test ran the full loop on a new
domain (B2B SaaS renewals, 3,000 seeded rows) with the same slow provider W3
measured, and answered the two questions it existed for: the LLM plan
answered in 12.4 seconds with `source: llm` (W3: 120 seconds and a
deterministic fallback), and the Python panel's contract turned the naive
analyst's first interaction from three blind refusals into zero — the first
run used `dataset.rows` straight from the page and returned a 201.

The run's one finding was the regression the fix it validated had
introduced: W3X-003-PROMPT's shrunken prompt no longer asks for
`context_basis`, `validate_plan` treats the field as optional, and
`PlanPanel` read it unconditionally — so a case with an LLM plan could not
be reopened, the whole workspace blanking with a TypeError. W4X-001 guards
the field, marks it optional in the type, and adds one test; the prompt,
validator and deterministic planner are untouched, because the shrink is
what keeps the plan inside the budget and this is its cost, paid on the
client. Verified live: the case reopened and rendered `by llm for
saas_renewals_2026.csv`.

**Next: nothing is queued.** Every phase is delivered, all four walk-test 3
findings are closed, and their fixes are now validated in an analyst's
hands. W3X-001 (a filename accepted twice) stays an unmeasured observation;
the same Data panel accepted the same name four times in this run's failed
attach attempts, all from the harness's own file-synthesis path, so a human
selecting a file twice is still the only way to reach it. Two things
outside this repo's control, unchanged: GitHub Actions still refuses every
job (billing), and the packaged app is unsigned by DEC-006.

**v0.3.6 is the release the W3X fixes and this fix ship in.**

Gates now: web 285/285, tsc clean, build ok; server 793/793, trace 48/48,
e2e 28/28.

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **WALK-UX-004, the fourth walk-test** - a validation run on a new domain with the same slow provider: the plan answered in 12.4s as an LLM (W3: 120s timeout and fallback), and the Python surface's first interaction went from three blind refusals to zero. Its one finding was a regression W3X-003-PROMPT introduced: PlanPanel read the optional `context_basis` unconditionally, so a case with an LLM plan could not be reopened. Fixed as W4X-001, verified live in the same run. Findings, measurements and the honest harness limits (no multi-line typing, the chart step not observed) are in `walktest-w4/FINDINGS.md`.
- **W4X-001, the plan panel's optional field** - a two-line guard for a bug every test fixture inoculated against: each one supplies `context_basis`, so the suite could not see it, and only reopening a real case with a real LLM plan could. The join clause now disappears when the field is absent, which is what the field means; the type marks it optional so a future reader cannot assume it. Gates: web 285/285 (one test added), tsc clean, build ok; server unchanged.
- **v0.3.6, the release the W3X fixes ship in** - all three version files moved together, the sidecar repackaged so `/updates/latest` answers 0.3.6, and the DMG rebuilt from that bundle (sha256 63166707…69c280). Smoke-tested as a real launch: health ok, the case list and Templates render, the core exits with the shell. Gates: server 793/793, web 285/285 (five timing tests timed out under a parallel server run and re-ran green in isolation), tsc clean, build ok, trace 48/48, e2e 28/28.
- **W3X-003-PROMPT, the plan prompt's output size** - the walk-test measured a plan call that consumed the whole 120s budget and fell back deterministically, and the live measurement explained it: the prompt asked for the largest output of the six adapters and the provider runs at ~10-13 tok/s. `LLMPlanner.prompt` is now the text `plan` posts, on its own so a test can pin it, and it asks for at most 4 sub-questions / 3 hypotheses / 4 steps / 3 data requirements with one short clause per string. A live re-measurement answered 508 tokens in 52.3s (`finish_reason: stop`) instead of timing out. The validator's ceilings are untouched, so the request shrank the wait without shrinking what an engine may answer. Five tests pin it.
- **W3X-002, the fallback sentence glued to its label** - a panel that appends its own context to `sourceLabel` was gluing a lowercase fragment to a sentence that already ends with a period, and the substitution notice read as a typo. `sourceWith` capitalises the join; the sentences, the server's wording and the panels that render the label alone are untouched. Seven tests, one asserting the measured shape is absent.
- **W3X-004, the Python surface refuses and teaches nothing** - the sandbox's own contract now sits on the panel that runs against it: the handle (`dataset.rows`), the importable subset with pandas/csv/numpy named as refused and `statistics` as the alternative, no file path, and the `result` shape a run takes. The placeholder is the canonical use, not `# python`. Six tests, one comparing the panel's module list to `_SAFE_MODULES` in the Python source.
- **WALK-UX-003, the third walk-test** - a complete end-to-end run on a new domain (SaaS helpdesk, seeded, six planted anomalies) with a real LLM and a live Chromium on an isolated data dir. The loop closed through the UI alone. Four findings, none a blocker: the fallback sentence glued to its label (W3X-002), the Python surface refuses three times and teaches nothing (W3X-004), the plan call burns the whole 120s budget (W3X-003), and a filename accepted twice (W3X-001, a harness artifact). Nine W2X fixes confirmed still holding.
