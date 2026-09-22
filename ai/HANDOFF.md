## Next action
**P8-VALID-003 is DONE**: a finding's verdict now covers the PRD's nine
dimensions (AT-17), not three. New `server/app/validation.py` - nine pure
checks reading objects already on disk, never raising; a check that cannot
decide *passes* with a "skipped -" sentence rather than punishing a finding for
the validator's blindness. The three existing checks survive as three of the
nine; the verdict stays three-valued (hard failure -> `insufficient_evidence`,
concern -> `partially_supported`, clean -> `supported`). **A validation costs
one rerun, not nine** - pinned by a counter test, proven to fail when a second
execution was injected. The schema stays at v11; a check is derived, never
stored.

Two lessons worth carrying:
- The web suite's 5000ms timeouts were **CPU starvation under parallel file
  execution, not flaky code** - every CaseWorkspace test passes in under 2s in
  isolation. Now serial (`fileParallelism: false` in `web/vite.config.ts`): no
  wall-clock cost, and a red signal means code again.
- Renaming the check keys broke the **P2 and P3 phase gates** in
  `verification/`, not just the tests. `verification/` is a consumer of the
  API; a contract-key rename must grep it too.

**Gates:** 452 server tests, 85 web, build green, all 25 real-server e2e steps
green. Committed as `086daf2` and pushed.

### What is next, in priority order

- **P8-CAUSAL-004** - the causal-language guard (AT-18, 50 cases, 95%
  thresholds). This task shipped its weakest deliberate form: a *check* that
  says the claim outruns the method. The guard is a policy with thresholds and
  an evaluation corpus.
- **P8-GOLDEN-005** - the analytical golden suite (AT-40/AT-01). This is what
  *measures* the >= 95% detection rate AT-17 names and the 95%/5% AT-08 names;
  this task and P8-QUALITY-002 shipped the checks, neither the measurement.
- **P8-SHELL-006** - the orientation spine (AT-33/34/35).

## Recent completions

The last tasks to land, newest first. The contract and done-record for each is
in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`; the reasoning and
the bugs found are in `ai/HANDOFF-ARCHIVE.md`.

- **P8-VALID-003** - validation across the PRD's nine dimensions (AT-17);
  nine pure checks, one rerun, concern vs failure distinguished in the shell.
- **P8-QUALITY-002** - quality detection beyond missingness (AT-08/AT-09);
  seven defect classes, each with an impact sentence, shown at the Data stage.
- **P8-CONTEXT-001** - a case carries purpose, sub-questions, hypotheses and
  constraints (AT-03), read by the planner and the assistant.
- **v0.2.0** - released and published (tag on `ec819fc`); CI's billing is
  suspended, so artifacts were built and uploaded locally.
- **P7-CSV-002 / P7-CORS-001** - a stray trailing comma no longer collapses a
  CSV to one column; the packaged app's webview can reach its own core.

