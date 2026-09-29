# DAH - Task Backlog

## P0 Foundation - PASSED

| Task ID | Status | Verification |
|---------|--------|--------------|
| P0-INFRA-001 | DONE | pytest passes; live `GET /health` returns 200 |
| P0-WEB-002 | DONE | Vitest 2/2 pass; build succeeds; `/api` proxy reaches backend |
| P0-DATA-003 | DONE | 5/5 pytest pass; case survives restart; DuckDB profiles CSV |

## P1 Vertical Slice - PASSED

| Task ID | Status | Verification |
|---------|--------|--------------|
| P1-DATA-001 | DONE | CSV attaches, file on disk, survives reopen |
| P1-DATA-002 | DONE | profile (rows/columns/null counts) stored against dataset |
| P1-ANALYSIS-003 | DONE | read-only SQL runs persisted with results |
| P1-EVIDENCE-004 | DONE | evidence chain finding -> run -> dataset |
| P1-VALID-005 | DONE | rerun reproduces or demotes the finding |

## P2 MVP

Goal: turn the vertical slice into a genuinely usable analytical application.
The loop is proven; P2 broadens it. AI joins last, only after the deterministic
surface is complete (roadmap section 5).

```
Parquet/Excel + richer profiling + Python execution + charts
+ case management + AI planning (structured) + export
```

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P2-DATA-006 | Data Layer (breadth) | M | DONE | P1 done | Parquet and Excel attach alongside CSV |
| P2-DATA-007 | Data Layer (depth) | M | DONE | P2-DATA-006 | Profile covers duplicates, types, basic stats |
| P2-ANALYSIS-008 | Analysis Workspace | M | DONE | P2-DATA-006 | Read-only Python executes against a dataset, result persisted |
| P2-ANALYSIS-009 | Analysis Workspace | M | DONE | P2-ANALYSIS-008 | Chart image persisted from a run result |
| P2-CASE-010 | Analysis Case | M | DONE | P1 done | Rename, duplicate, delete cases |
| P2-AI-011 | AI Planning | M | DONE | P2-ANALYSIS-008 | Structured plan (sub-questions, hypotheses) from a question + profile |
| P2-CASE-012 | Export | M | DONE | P2-AI-011 | Case exports as a self-contained JSON package |

## P3 V1

Goal: make the MVP substantially better for repeated real-world use (roadmap
section 6). Entry order follows ai/ROADMAP.md; hardening first because the P3
AI code-generation work multiplies the risk of the P2 soft sandbox.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P3-SEC-001 | Analysis Workspace (hardening) | M | DONE | P2-ANALYSIS-008 | Python runs in a separate process under an OS sandbox; writes outside scratch, network, and runaway CPU are bounded and reported as 400 |
| P3-CHART-002 | Analysis Workspace (raster charts) | M | DONE | P3-SEC-001 | PNG rendering behind the same interface; bar geometry and export round trip verified |
| P3-DATA-003 | Data Layer (multi-dataset) | M | DONE | P2 done | Join runs across attached files; validation, duplicate, export all carry the dataset list |
| P3-FLOW-004 | Analysis workflow (guided) | M | DONE | P3-DATA-003 | Derived stage and single next action from the case's artifacts |
| P3-ANALYSIS-005 | Analysis Workspace (richer EDA) | M | DONE | P3-FLOW-004 | Segment / correlate / distribution compile to read-only SQL |
| P3-EVIDENCE-006 | Evidence (richer lineage) | M | DONE | P3-ANALYSIS-005 | Case-wide evidence graph with claim-to-source tracing |
| P3-CASE-007 | Analysis Case (reuse) | M | DONE | P3-EVIDENCE-006 | Case search, case history timeline, and case templates |

## P4 Production Candidate

Goal: make DAH reliable, secure, usable and observable enough for controlled
external users (roadmap section 7). Entry order follows ai/ROADMAP.md's
checklist; the gate comes first because a phase is done when a gate says so.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P4-VERIFY-001 | Verification (P3 gate) | M | DONE | P3 complete | One journey exercises multi-dataset joins, the hard sandbox and all four assistant slices end to end |
| P4-RELIABILITY-002 | Reliability | M | DONE | P4-VERIFY-001 | Input errors answer 400 with the engine's message; a harness fault answers 500 instead of a 400 that blamed the analyst |
| P4-UX-003 | UX (case workspace + chat) | M | DONE | P4-RELIABILITY-002 | Cases can be searched and opened; the workspace shows the derived stage, datasets and runs, and the case answers questions with visible citations |
| P4-UX-004 | UX (run-scoped assistant surfaces) | M | DONE | P4-UX-003 | The workspace walks the loop one panel per step - attach+profile, generate code, run, interpret, draft, accept, validate - and every write posts to the endpoint that owns it |
| P4-VALID-005 | Validation (rerun determinism) | M | DONE | P4-UX-004 | Reproduction compares SQL rows as a multiset, so an unordered GROUP BY answering in a different order is a match, not a drift |
| P4-PERF-006 | Performance (large datasets) | M | DONE | P4-VALID-005 | Profiling no longer materialises every row to read a description; the result cap and profile correctness are pinned at scale |
| P4-CI-007 | Distribution (CI + signing decision) | M | DONE | P4-PERF-006 | macOS CI runs the server suite and both gates, the web suite and build, the desktop lifecycle tests against a live core, and a sidecar packaging build; signing deferred to P5 by DEC-004 |

## P5 Production Grade

Goal: make DAH tested, hardened, distributable, maintainable, observable and
supportable (roadmap section 8). Entry order follows ai/ROADMAP.md's checklist;
the gate comes first because a phase is done when a gate says so.

| Task ID | Capability | Priority | Status | Dependencies | Verification |
|---------|-----------|----------|--------|--------------|--------------|
| P5-VERIFY-001 | Verification (P4 gate) | M | DONE | P4 complete | One journey walks the edges: the error taxonomy, rerun determinism, the result cap, graceful degradation |
| P5-OBSERVE-002 | Observability | M | DONE | P5-VERIFY-001 | The core writes a size-capped rotating log into the user's data dir, `GET /logs` tails it read-only, and nothing the analyst typed ever lands in it |
| P5-RELIABILITY-003 | Error contract | M | DONE | P5-OBSERVE-002 | A 500 answers a JSON envelope with a request id that maps to the traceback in the log, and the id is surfaced to the user |
| P5-CI-004 | CI floor | S | DONE | P5-RELIABILITY-003 | Every job runs on macos-13 (Ventura), the minimum supported macOS, and the packaged-core smoke now asserts file logging lands in the data dir |
| P5-RELEASE-005 | Release automation | M | DONE | P5-CI-004 | A tag matching server/pyproject.toml's version builds, smokes and publishes an unsigned .app as a flagged pre-release with its checksum |
| P5-UX-006 | Shell UX | S | DONE | P5-RELEASE-005 | A Reveal DAH Logs menu item asks the core where its log is and opens the folder in Finder with it selected |

### W2X-012-A contract (phase A: the status surface)

```
TASK ID: W2X-012-A
MILESTONE: post-walk-test fixes (the second walk-test's BLOCKER, half one)
CAPABILITY: Distribution / feature availability (the LLM status surface)
GOAL: the LLM's silent degradation becomes a stated one. W2X-012's actual harm
      was not that the packaged app falls back - a deterministic answer is a
      working answer - but that it fell back and told nobody: `source:
      template` is a field a developer reads, and the analyst reads no part of
      it. So the core learns to answer the question "will I get an LLM answer",
      and the shell learns to render the answer. The credential itself still
      does not reach the bundle; that is phase B, and this is the floor it
      builds on - without a way to ask, phase B's own UI cannot say whether it
      worked.
CONTEXT: three sites carry the silence. `server/dah-core.spec` bundles only
         the version stamp (`.env` is gitignored, by the repo's own rule that
         no secret is committed); `server/app/main.py:28` loads `.env`
         relative to source, a path that does not exist inside a one-file
         PyInstaller bundle; `core_server.rs:88-93` injects only DATA_DIR,
         DB_PATH and PARENT_PID into the child. Six adapters - planner,
         generator, drafter, interpreter, assistant, refine - each read the
         same three env vars through their own `_configured_llm()`, so the
         truth was duplicated six times and surfaced zero. `/health` answers
         `{"status":"ok"}` either way, so the shell could not ask.
INPUTS: the six adapters' env reads (DAH_LLM_API_KEY with an OPENAI_API_KEY
        fallback, DAH_LLM_BASE_URL, DAH_LLM_MODEL), the response-model
        conventions in `server/app/models.py`, the notice/banner conventions
        in `web/src/index.css`, and `web/src/NoticeLayer.tsx` as the existing
        shell-to-window channel (deliberately untouched: that one answers the
        native menu bar through a custom event the browser host never
        receives; this is an ordinary GET both hosts make).
RELEVANT FILES: server/app/llm.py (new - the one read, the status builder,
                the boot log line), server/app/models.py (+LlmStatus),
                server/app/main.py (+the endpoint, +the boot log call),
                server/tests/test_llm_status.py (new, 13 tests),
                web/src/api.ts (+getLlmStatus, +LlmStatus),
                web/src/panels/LLMStatus.tsx (new - the banner),
                web/src/panels/LLMStatus.test.tsx (new, 7 tests),
                web/src/App.tsx (mounted on all three screens),
                web/src/index.css (+.llm-status, +its reduced-motion rule),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - The core answers. `GET /llm/status`, read-only by construction - a GET
    with no body and no path parameters - returning {configured, provider,
    model, base_url}. `configured` is the field the banner branches on.
    `provider` names the env var that supplied the key, never its value: the
    name tells the analyst which setting to change and a value would be a
    credential the CORS-permitted webview can read and a log line can
    capture. `model` and `base_url` are the public defaults a configured
    deployment overrode.
  - One place reads the environment, not seven. `llm.py` exists so the answer
    is asked in one place; the six adapters keep their own `_configured_llm`
    (a deduplication is a separate task, and it touches trust-bearing paths).
    The two must *agree*: a blank value is treated as absent in both, and
    the same two var names in the same order.
  - One boot line, `llm configured: model X at Y` or `llm not configured;
    LLM features will use deterministic engines`, written to `dah.core`
    after `configure_logging()`. Once, not per request: the configuration is
    a property of this deployment, and the request log line still records
    only method, path and status, so the privacy property the walk-test
    verified (no payload in the log, ever) holds.
  - The banner renders on all three screens, reads once on mount, never
    polls, and renders nothing while the fetch is in flight, nothing when the
    LLM is configured, nothing if the endpoint fails (the health surface owns
    "the core is down"), and the concern banner otherwise - naming the
    deterministic engines and the var to set. A green banner on every screen
    is noise the analyst learns to dismiss; only the broken state shows. The
    unmount's cancellation flag is what keeps a late resolution from updating
    state after the analyst left the screen.
  - The CSS mirrors `.shell-notice` - fixed, concern-toned, token-backed -
    with its own `prefers-reduced-motion` rule in the same block.
NON-GOALS: delivering the credential (phase B - a first-run prompt and a
           settings surface, or build-time injection), refactoring the six
           adapters onto this reader, changing any timeout, any new
           dependency, and a UI state where the banner can be dismissed - a
           condition that persists cannot be dismissed away.
CONSTRAINTS: green only. No new dependency (DEC-001). No key value in any
             response body, log line or test assertion. Read-only endpoint.
             Deterministic and offline: the endpoint reads the environment
             and touches nothing else. The desktop capability set stays
             `core:default` - no Tauri command is added; that is phase B.
ACCEPTANCE CRITERIA:
- [x] the core answers `/llm/status` with all four fields, and `configured`
      is the one the banner branches on
- [x] no response body, log line or test assertion contains any part of a key
      value; the provider is the variable's name
- [x] the same two variables in the same order as the six adapters read them,
      so the endpoint and the adapters cannot disagree about whether a key
      exists
- [x] a blank key is no key, in both places
- [x] the banner renders nothing when configured, nothing while loading,
      nothing on an endpoint failure, and the concern banner otherwise
- [x] the fetch happens exactly once per mount and a late resolution after
      unmount updates nothing
- [x] the server-side test pins every field the client branches on - the web
      suite mocks the api module and a fixture would supply `configured`
      whether the server emits it or not (the P9-F4 `format` failure)
- [x] both states verified in a real browser against a real core started both
      ways, not only in jsdom
TESTS: server 13 in test_llm_status.py - the unconfigured answer with its
       public defaults, configured with the provider name, the OpenAI var
       fallback, three shapes of blank key, a blank key not shadowing the
       fallback, the field set the client branches on, the whole body free of
       the key, the two boot lines (and free of the key), read-only-ness, and
       the helper agreeing with the endpoint.
       Web 7 in LLMStatus.test.tsx - the banner and its sentence when
       unconfigured, nothing when configured, nothing while loading, one
       fetch only, nothing when the core is unreachable, no state update
       after unmount, and the read going through the api client.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL=
              DAH_LLM_MODEL= OPENAI_API_KEY= .venv/bin/python -m pytest -q`
              green (741); `cd web && npm test && npx tsc -b && npm run
              build` green (223, build ok); `server/.venv/bin/python
              verification/trace/verify_trace.py` green (48/48);
              verification/e2e/verify_e2e.py green (28/28);
              verification/golden/verify_golden.py green (21/21);
              verification/refine/verify_refine.py green (AT-04);
              verification/measure/verify_measure.py green (9/9);
              and a real browser against a core started with and without a
              key: the banner absent in one state and present with its
              sentence in the other.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the W2X-012 carried item
              becomes phase A closed and phase B open. No schema change.
```

TASK: W2X-012-A - the LLM status surface
ID: W2X-012-A
PRIORITY: high
STATUS: DONE
SUMMARY: the walk-test's BLOCKER had two halves, and this closed the one that
         was the analyst's to bear. `GET /llm/status` answers the question
         the shell could not ask, `server/app/llm.py` is the one place it is
         read (six adapters each had their own copy of the same read), and
         the banner renders on every screen - nothing when an LLM is there,
         because a green banner on every screen is noise the analyst learns
         to dismiss, and a concern sentence naming the deterministic engines
         when one is not. One boot line says which engine is in play, so
         `Reveal DAH Logs` shows it too. The property that makes this safe
         rather than convenient is that the key is never anywhere in the
         answer: the provider is the variable's *name*, and the whole body is
         asserted free of any key value on both the response and the log
         line. The credential still does not reach the packaged app; phase B
         is the settings surface that puts it there, and this is the floor it
         stands on.

### W2X-012-B contract (phase B: the settings surface)

```
TASK ID: W2X-012-B
MILESTONE: post-walk-test fixes (the second walk-test's BLOCKER, half two)
CAPABILITY: Distribution / feature availability (the LLM settings surface)
GOAL: phase A named the state; this delivers the fix. The packaged app carried
      no LLM credentials and there was no way to put one in it: `.env` is
      gitignored and does not exist inside a one-file PyInstaller bundle, and
      the shell injects only the data dir. So the analyst's only path to an
      LLM answer was a terminal and a restart, which is nobody's path. The
      credential now arrives as a file the shell's own data dir already
      owns, and a panel in the bundle writes it - three fields, no restart,
      no new dependency, and no capability change to the shell.
CONTEXT: `core_server.rs` injects `DAH_DATA_DIR` into the child (the same dir
         the cases and `dah-core.log` live in), the six adapters read the env
         at call time rather than import time (planner.py:390,
         generator.py:493, interpreter.py:266, assistant.py:600,
         drafter.py:336, refine.py:622), `updates.rs` had already proven the
         shell-to-webview channel - a `window.eval()` dispatching a DOM
         CustomEvent needs no ACL permission - and the webview is already
         CORS-permitted by `main.py`'s allowlist. The capability file grants
         only `core:default` and declares that no Tauri JS APIs are used;
         adding a command would have made that a lie.
INPUTS: phase A's `GET /llm/status` (the answer this surface's own save
        returns, so the panel never asserts a state the core did not confirm),
        `LlmStatus` and the banner conventions, `shell.ts`'s
        `NOTICE_EVENT`/`describeUpdate` pattern, `updates.rs`'s
        `notice_script`/`json_string` pair, and `main.rs`'s menu builder.
RELEVANT FILES: server/app/llm.py (+settings_path, +read_settings_file,
                +load_settings, +apply_config, +write_settings),
                server/app/main.py (+GET/PUT /llm/config, +the boot load),
                server/app/models.py (+LlmConfig),
                server/tests/test_llm_config.py (new, 18 tests),
                desktop/src-tauri/src/settings.rs (new - the menu's handler
                and its eval),
                desktop/src-tauri/src/main.rs (+SETTINGS_ID, +the menu item,
                +the handler),
                web/src/api.ts (+getLlmConfig, +putLlmConfig, +LlmConfig),
                web/src/shell.ts (+SETTINGS_EVENT, +LLM_CHANGED_EVENT),
                web/src/panels/LLMSettings.tsx (new - the panel),
                web/src/panels/LLMSettings.test.tsx (new, 6 tests),
                web/src/panels/LLMStatus.tsx (+the Configure button, +the
                changed-event refetch),
                web/src/panels/LLMStatus.test.tsx (+2 tests),
                web/src/App.tsx (the panel mounted on all three screens),
                web/src/index.css (+.llm-settings, +its reduced-motion rule),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - The credential's home is a file, not the environment and not the bundle.
    `dah-llm.json` sits in the data dir the shell already injects, is read
    into `os.environ` once at boot (after `configure_logging()`, before phase
    A's boot line so that line is true), and is written mode `0o600` via an
    atomic `.tmp` + `os.replace` (DEC-001: no new dependency, so no Keychain
    binding; a build-time injection would burn the key into a reversible
    binary, which was rejected). The file is outside the repo, the bundle and
    git, and the analyst can edit or delete it directly.
  - The load yields and the save does not. `load_settings` will not overwrite
    a non-blank exported or injected variable - a deployment's own key is
    authoritative and the file is advisory. `apply_config` is the write path,
    and it overwrites and *unsets* rather than yielding: the form is the thing
    that just wrote it, so a blank save must clear the key, not blank a
    variable the previous save set. Only `DAH_LLM_API_KEY` is ever touched;
    the `OPENAI_API_KEY` fallback is never written to.
  - `GET /llm/config` reads the file, never the environment, and never echoes
    a key: an exported key the shell cannot overwrite would otherwise reach
    the CORS-permitted webview. The three fields are present as blanks when
    nothing is stored. Unknown keys in the file are ignored; an unreadable or
    invalid file warns and yields nothing - a settings surface that raised
    could not be opened to fix itself.
  - `PUT /llm/config` writes, applies, and answers phase A's `LlmStatus`:
    the panel shows the core's own verdict, not its own write, and the
    banner can be driven from the same answer.
  - No restart. The adapters read the environment at call time, so a boot
    load plus a save-time apply is enough; the six adapters, the spec and
    the capability file are untouched.
  - The shell's menu gains "DAH Settings…" beside the existing items. The
    handler asks the core for the status and evaluates a script that
    dispatches a DOM CustomEvent the panel listens for - the same channel
    `updates.rs` uses, needs no permission, and is a no-op in a browser
    host. The panel is the bundle's own surface, so no native window is
    built.
  - The panel renders nothing until the event arrives (the browser host
    never receives it), offers the three fields, and on a save answers with
    the sentence "no restart needed" - the property the whole design exists
    to deliver. A failure names the error and keeps the panel open, because
    dismissing a failed write is how a credential gets lost.
  - The banner gains the Configure button and a refetch on the panel's
    changed event. The banner reads once per mount and is not polled; the
    changed event is the one other thing that can move the state, so it is
    the one other thing the banner refetches for - an analyst who just
    resolved the concern should not have to reload to see it go.
NON-GOALS: refactoring the six adapters onto the single reader, a first-run
           prompt, keyring/Keychain support (DEC-001), an obscured/masked
           reveal of the stored key, per-feature LLM toggles, and any change
           to the capability set, `core_server.rs`, `dah-core.spec` or the
           six adapters.
CONSTRAINTS: green only. No new dependency (DEC-001). No key value in any
             response body, log line or test assertion - the GET answers
             blanks, the boot line names the engine, and the request log
             keeps its method/path/status-only property. The write handler
             must not raise while holding the payload. The desktop capability
             set stays `core:default`; no Tauri command is added.
ACCEPTANCE CRITERIA:
- [x] the credential reaches a packaged core: a settings file in the shell's
      data dir, read at boot, applied on save
- [x] saving a key makes the LLM features use it with no restart, verified
      against a live core (the adapter saw the key immediately after the PUT)
- [x] clearing the key unsets the variable, not blanks it, and the status
      answers unconfigured
- [x] no response body, log line or test assertion contains any part of a key
      value; the GET never echoes one
- [x] an exported or injected key is not overwritten by the file at boot, and
      is not shadowed by the fallback when the form supplies one
- [x] an unreadable or invalid settings file yields no configuration and does
      not stop the core from starting
- [x] the file is mode 0o600, written atomically, outside the repo, bundle and
      git
- [x] the menu item opens the panel through a channel needing no new
      permission, and the panel is a no-show in a browser host
- [x] the panel writes the three fields and answers with the core's own
      status shape; a failed write keeps the panel open with the error
- [x] the banner's Configure button opens the same panel, and the banner
      refetches once when a save lands - still no poll
- [x] both states and the full save loop verified in a real browser against a
      real core
TESTS: server 18 in test_llm_config.py - the unconfigured answer and its
       blanks, unknown keys ignored, an unreadable file, a malformed file,
       the boot load's precedence (env wins), the write path's precedence
       (form wins, and unsets), a blank save clearing, the variable unset
       rather than blanked, the fallback not shadowed, the atomic write and
       its mode, no key in any body or line, and the read-only-ness of the
       GET. Rust 4 in settings.rs - every shape of a body that is not a
       boolean `configured` answers not-configured, and the event name the
       script builds is the one `shell.ts` exports. Web 6 in
       LLMSettings.test.tsx - nothing rendered until the event, the three
       fields from the stored config, the write and its "no restart needed"
       sentence, a failure keeping the panel open with the error, the
       changed event posted without a payload, and the close. Plus 2 in
       LLMStatus.test.tsx - the Configure button opens the panel, and the
       banner refetches once on the changed event.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL=
              DAH_LLM_MODEL= OPENAI_API_KEY= .venv/bin/python -m pytest -q`
              green (772 = 741 + 31); `cd desktop/src-tauri && cargo test`
              green (30 = 26 + 4); `cd web && npm test && npx tsc -b &&
              npm run build` green (235 = 223 + 12, build ok);
              `server/.venv/bin/python verification/trace/verify_trace.py`
              green (48/48);
              verification/measure/verify_measure.py green (9/9);
              and a real browser against a live core: the banner's concern,
              the Configure button opening the panel, a save answering
              "no restart needed", and the banner leaving the screen without
              a reload - then clearing the key and seeing it return.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the W2X-012 carried item
              closes (both halves done). No schema change.
```

TASK: W2X-012-B - the LLM settings surface
ID: W2X-012-B
PRIORITY: high
STATUS: DONE
SUMMARY: the walk-test's BLOCKER is closed on both halves. Phase A made the
         degradation sayable; this made it fixable from inside the app. The
         credential lives in `dah-llm.json` in the data dir the shell already
         injects - mode 0o600, atomic, outside the repo and the bundle, so it
         can be edited or deleted without a rebuild - read into the
         environment once at boot and applied on every save, which works
         because the six adapters read the environment at call time and so
         need no restart. The panel is three fields in the bundle itself,
         opened from a menu item the shell already had the channel for: a
         `window.eval()` dispatching a DOM CustomEvent, the same thing
         `updates.rs` does, needing no permission and no capability change,
         and a no-op in a browser host. The save answers with phase A's own
         `LlmStatus`, so the panel reports the core's verdict instead of its
         own write, and the banner refetches once on the panel's changed
         event - still not polled - so a concern the analyst just resolved
         leaves the screen instead of lingering until the next mount. The
         property that makes this safe rather than convenient is that the key
         is nowhere it can be read back: the GET answers blanks and never the
         environment, the boot line names the engine, and the write handler
         does not raise while holding the payload.

### WALK-UX-003 contract (the third walk-test)

```
TASK ID: WALK-UX-003
MILESTONE: the third walk-test (a new domain, a real LLM, a live browser)
CAPABILITY: Verification / UX (the shipped app, used end to end)
GOAL: prove the loop a first-time analyst can walk without a terminal, on a
      domain the project had never analysed, and find what still harms them.
      WALK-UX-002 found density; with that closed, the hypothesis was that
      the remaining harm is the wait and the surfaces that refuse without
      teaching. This run tested that, and measured both.
CONTEXT: the v0.3.5 tree - all thirteen W2X fixes released, WALK-UX-002
         closed. The walk-test's own protocol (walktest-w2/PLAN.md) is the
         one followed: naive analyst plus facilitator, no coaching mid-run,
         every density claim backed by a number, no code changed during the
         run. The Tauri WKWebView has no CDP, so the authoritative surface
         is the web bundle in a real Chromium, which is the same React code
         the shell renders.
INPUTS: a fresh core on an isolated data dir (DAH_DATA_DIR / DAH_DB_PATH under
        walktest-w3/data), port 8123, DAH_LLM_API_KEY configured
        (Atria-Dawn-Preview) so the LLM paths are really exercised - a
        walk-test that never calls the LLM cannot find what the wait costs.
        The Vite dev server on 5273 serving the master bundle.
RELEVANT FILES: walktest-w3/make_dataset.py (new - the seeded dataset),
                walktest-w3/CAPTURE-SHEET.md (new - the live sheet),
                walktest-w3/FINDINGS.md (new - the four findings and the
                nine confirmations), walktest-w3/REPORT.md (new - summary,
                journey table, priority), walktest-w3/evidence/ (the two
                runs, the export package, the final page's DOM text and
                screenshot), walktest-w3/logs/ (the core request log, the
                suite and gate logs), .gitignore (+walktest-w3/data and
                /logs, mirroring the walktest-w2 rule),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE: none. This task produces findings, not changes; each W3X
                fix is a separate task with its own contract and gate.
                The only files that move are the walk-test's own material
                and the ai/ state that records it.
ACCEPTANCE CRITERIA:
- [x] the walk runs against a real core with a real LLM configured, not a
      mocked or deterministic-only environment
- [x] the dataset is new (not a reuse of walktest/ or walktest-w2/) and
      carries planted anomalies the profiler must find
- [x] every surface the shell owns is reached through the UI, and the loop
      closes: attach, profile, plan, SQL run, Python run, chart, interpret,
      draft, accept, validate, reviewer audit, chat, implications, export
- [x] state survives a leave and a reopen
- [x] no code was changed during the run
- [x] the capture sheet has no `to be recorded` left
- [x] every finding carries a measured observation, not an impression
- [x] each previous walk-test fix the run exercised is recorded as holding
      or as regressed, with the measurement
- [x] the verification pipeline runs green on the same tree: server 788/788,
      web 272/272, tsc clean, build ok, e2e 28/28, trace 48/48
TESTS: none new - this is a walk-test. The suites were re-run on the same
       tree as the run's own exit gate.
VERIFICATION: server 788/788 passed; web vitest 271/272 with one timing test
              (AT-27, measure.test.tsx) timing out at 5s under load and
              re-running green 10/10; `npx tsc -b` clean; `vite build` ok;
              `verification/e2e/verify_e2e.py` 28/28 PASS;
              `verification/trace/verify_trace.py` 48/48 PASS.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the three MAJOR findings
              become carried follow-ups. No schema change.
```

TASK: WALK-UX-003 - the third walk-test
ID: WALK-UX-003
PRIORITY: high
STATUS: DONE
SUMMARY: the loop a first-time analyst walks without a terminal, proven on
         a domain the project had never analysed. One seeded helpdesk dataset
         with six planted anomalies, one case, every surface the shell owns -
         and the anomalies the profiler was supposed to find were all six
         found, each with its own "potential impact" sentence. `loop_closed`
         read true and the export round-tripped. Four findings: the fallback
         sentence is glued to the label it replaces (W3X-002), the Python
         surface refuses three times and teaches nothing (W3X-004), the plan
         call burns the whole 120s budget for an answer the deterministic
         engine writes in under a second (W3X-003), and a filename accepted
         twice (W3X-001, an artifact of how the harness drives the file
         input). Nine W2X fixes were measured holding against the running
         core - recorded because a walk-test that only reports new findings
         cannot tell you the old ones regressed.

### Carried follow-ups from the third walk-test (WALK-UX-003 - closed)

None remain open. The three MAJOR findings are closed (W3X-002 and W3X-004
with code; W3X-003 root-caused as a property of the provider rather than the
harness, and its follow-up W3X-003-PROMPT now shrinks the prompt) and W3X-001
is recorded as an observation. The material is in `walktest-w3/FINDINGS.md`.

**MAJOR**

- **W3X-002 — CLOSED.** The fallback sentence was glued to the label it
  replaces: `sourceLabel` returns the substitution sentence and the panel
  appended ` for {filename}`, so it rendered "...answered in its place. for
  helpdesk_tickets_2026.csv" - a lowercase fragment that read as a typo
  rather than as the announcement W2X-001's FIX-TIMEOUT-006 line intended.
  The fix moved only the join: `sourceLabel` and its five sentences are
  byte-identical, and the three panels that append their own context go
  through `sourceWith`, which capitalises the context so a sentence ending
  in a period takes a grammatical clause. Contract and tests below, in the
  rolling window.
- **W3X-004 — CLOSED.** The Python surface refuses three times and teaches
  nothing. A Python-fluent analyst's first three interactions with the engine
  were refusals (`import pandas`, `import csv`, the `path` variable the SQL
  placeholder implies exists), and the page put none of the answers on it: the
  handle is `dataset.rows` and only a stdlib subset imports. The sandbox was
  right to refuse - refusing is the security property - so the fix was not the
  wall but the sign on it: the panel shows the contract before the first run
  (contract, done-record and tests below, in the rolling window).
- **W3X-003 — CLOSED as root-caused, no code change.** The plan call consumed
  the whole `LLM_TIMEOUT_SECONDS` budget (`POST .../plan -> 201 in 120552ms`,
  `The read operation timed out`) and the live measurement against the same
  provider explains it: the plan prompt is the only one of the six adapters
  that asks for a large structured object (6 sub-questions, 5 hypotheses, 6
  steps), the provider generates at ~13 completion tokens per second, and
  1785 tokens at that rate is ~137s - the 120s timeout missed it by minutes.
  Temperature is not the variable; `max_tokens` truncates the JSON mid-object,
  which the schema validator refuses, so a cap buys a faster fallback, not a
  faster answer. This is a property of the provider, not the harness: the
  fallback was announced, deterministic and correct, which is the trust model
  the timeout was designed around. The measurement is recorded in
  `walktest-w3/FINDINGS.md` for the next session that asks why the plan is
  slow - the answer is the prompt's output size, not `timeouts.py`.

**OBS (recorded, not to fix)**

- **W3X-001 — the Data panel accepted the same filename twice.** The
  walk-test synthesised a `File` through `DataTransfer` because the harness
  cannot hand the input a real one; a human re-selecting the same file would
  reach the same state. `POST /datasets` has no filename check - only
  `POST /cases` checks for a duplicate (W2X-010). The cheapest guard is a
  same-filename refusal naming the existing dataset, but the frequency is
  unmeasured, so it is recorded rather than queued.

### W3X-003-PROMPT contract (the plan prompt asks for less than the validator accepts)

```
TASK ID: W3X-003-PROMPT
MILESTONE: post-walk-test fixes (the third walk-test's measured wait)
CAPABILITY: AI planning (the LLM prompt's requested output size)
GOAL: a complete LLM plan arrives inside the 120s budget on a ~13 tok/s
      provider. The walk-test measured the wait (POST .../plan -> 201 in
      120552ms, then the timeout's deterministic fallback) and a live
      measurement against the same provider explained it: the plan prompt is
      the only one of the six adapters that asks for a large structured object,
      1785 completion tokens at ~13 tok/s is ~137s, so the 120s timeout missed
      it by minutes. The timeout is not the variable (a slow endpoint is not
      made faster by giving up on it, and the fallback it produced was
      announced, deterministic and correct - the trust model the timeout was
      designed around); `max_tokens` is not either (measured: it truncates the
      JSON mid-object, `finish_reason: length`, and the schema validator
      refuses it - a cap buys a faster fallback, not a faster answer); and
      temperature is not (141s with, 103s without, the difference is only the
      output length). The one lever left is the output the prompt requests.
CONTEXT: `server/app/planner.py`'s `LLMPlanner.plan` built the prompt inline,
         so the text a measurement has to hold was not reachable without
         posting it. `_MAX_SUB_QUESTIONS = 6`, `_MAX_HYPOTHESES = 5` and
         `_MAX_STEPS = 6` are the validator's ceilings - the deterministic
         planner produces up to those counts, and `validate_plan` accepts
         them - so a smaller request must not shrink what the deterministic
         path or the validator accepts. The provider in the walk-test measured
         ~9.7-13 tok/s; nothing in the harness sets that rate.
INPUTS: the walk-test's measurement (`walktest-w3/FINDINGS.md`, W3X-003's
        block with the four timings: chat 6.1s, plan 141s / 103s, capped
        49.3s truncated), the live re-measurement this task ran
        (`walktest-w3/logs/measure-plan-prompt.log`: the shipped prompt
        answered 508 tokens in 52.3s, finish=stop, rate 9.7 tok/s), and the
        validator's own ceilings in `server/app/planner.py`.
RELEVANT FILES: server/app/planner.py (+`LLMPlanner.prompt`, `plan` now calls
                it), server/tests/test_llm_adapters.py (+5 tests, 793 server
                total),
                walktest-w3/measure_plan_prompt.py (new - the live
                re-measurement, offline by construction: no key, no run),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - The prompt is reachable without posting it. `LLMPlanner.prompt` holds the
    text `plan` posts, so a measurement or a test can hold the prompt the
    adapter actually sends. `plan` is byte-for-byte the same request.
  - The prompt asks for less: at most 4 sub_questions, 3 hypotheses, 4
    analysis_steps and 3 data_requirements, and every string "one short
    clause - a sentence at most, never a paragraph". This is a request, not
    a constraint the validator enforces - the word is "at most", and an
    engine that answers with five hypotheses is still a valid plan, only a
    slower one.
  - The validator's ceilings are untouched. `_MAX_SUB_QUESTIONS = 6`,
    `_MAX_HYPOTHESES = 5` and `_MAX_STEPS = 6` stay, the deterministic
    planner still produces up to them, and `validate_plan` still accepts
    them. Nothing about what an engine may answer changed; only what the
    LLM is asked for.
NON-GOALS: any change to `server/app/timeouts.py` (measured as not the
           variable - a shorter timeout is a faster *fallback*), a
           `max_tokens` cap (measured: it truncates the JSON mid-object and
           the validator refuses it), a temperature change (measured: only
           the output length moved), shrinking what the deterministic
           planner produces or the validator accepts, any change to the
           other five adapters (their outputs are small already - the chat
           shape measured 6.1s), and any new dependency.
CONSTRAINTS: green only. No new dependency. Deterministic and offline for
             the tests: every new test builds the prompt directly or reads
             it out of the patched `httpx.post` recorder, so no packet
             leaves the process and no key is real. The prompt's caps are
             pinned by test so a drift back to asking for the validator's
             ceilings is a named failure rather than a slow regression.
ACCEPTANCE CRITERIA:
- [x] the prompt is reachable without a network call, so a test pins the
      text the adapter actually posts
- [x] the prompt requests at most 4 sub_questions, 3 hypotheses, 4
      analysis_steps and 3 data_requirements, and asks for one short clause
      per string
- [x] each requested cap is strictly below the validator's ceiling, so the
      request is smaller than the contract
- [x] the contract is unchanged: a plan answering with the validator's full
      ceilings still passes `validate_plan`, and the deterministic planner
      still produces up to them
- [x] `plan` posts exactly the prompt `prompt` builds - the pinned text is
      the text sent
- [x] the prompt still carries the question, the truncated profile and the
      stated intent when there is one
- [x] a live re-measurement against the configured provider answers inside
      the 120s budget with `finish_reason: stop` (508 tokens, 52.3s), not a
      truncated object
- [x] all gates green: server 793 (788 + 5), web 285/285 unchanged, tsc
      clean, build ok, trace 48/48, e2e 28/28
TESTS: 5 in test_llm_adapters.py - the caps read out of the prompt's own
       sentence and each below the validator's ceiling, a plan at the
       validator's full ceilings still passing `validate_plan`, `plan`
       posting exactly the prompt `prompt` builds, the prompt carrying the
       stated intent, and the profile truncation holding.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              OPENAI_API_KEY= .venv/bin/python -m pytest -q` green (793);
              `cd web && npm test && npx tsc -b && npm run build` green
              (285, build ok); `server/.venv/bin/python
              verification/trace/verify_trace.py` green (48/48);
              `server/.venv/bin/python verification/e2e/verify_e2e.py`
              green (28/28); and the live re-measurement
              (`server/.venv/bin/python walktest-w3/measure_plan_prompt.py`,
              log at walktest-w3/logs/measure-plan-prompt.log) answering
              inside the budget.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; W3X-003-PROMPT closes (the
              last walk-test follow-up). No schema change.
```

TASK: W3X-003-PROMPT - the LLM plan prompt asks for less than the validator
ID: W3X-003-PROMPT
PRIORITY: high
STATUS: DONE
SUMMARY: the plan prompt's output size was the cost, and the cost is now
         asked down. A live measurement this task ran against the same
         provider shows the shipped prompt answering 508 tokens in 52.3s
         (`finish_reason: stop`) where the walk-test's unshrunk prompt took
         137s and timed out - still slow in absolute terms, because the
         provider generates at ~10-13 tok/s and that rate is the provider's,
         not the harness's, but inside the 120s budget rather than past it.
         The prompt is now reachable without posting it (`LLMPlanner.prompt`,
         with `plan` calling it, byte-for-byte the same request), asks for at
         most 4 sub-questions / 3 hypotheses / 4 steps / 3 data requirements
         with one short clause per string, and the validator's ceilings are
         untouched - an engine that answers with the full contract still
         passes, and the deterministic planner still produces up to it. The
         acceptance is honest about what did not change: a provider at this
         rate is never fast; the fix moved the plan from "times out and falls
         back" to "answers inside the budget".


### Carried follow-ups from the second walk-test (WALK-UX-002 - closed)

All thirteen findings closed. The walk-test's own material is in
`walktest-w2/` - REPORT.md (summary, measured density, priority table),
FINDINGS.md (one block per finding with severity and code location),
PHASE2.md (the real-app verification), CAPTURE-SHEET.md. Each was a separate
task with its own contract and one commit per fix.

**BLOCKER**

- **W2X-012 (the second walk-test's BLOCKER) — CLOSED, both halves.** Phase A
  made the degradation sayable; phase B made it fixable from inside the app.
  The credential lives in `dah-llm.json` in the data dir the shell already
  injects (mode 0o600, atomic, outside the repo and the bundle), read into the
  environment once at boot and applied on save - no restart, because the six
  adapters read the environment at call time. `GET/PUT /llm/config` are the
  read and the write (the GET answers blanks and never the environment, so no
  key is ever echoed into the CORS-permitted webview), and a three-field panel
  in the bundle writes it, opened from a "DAH Settings…" menu item through
  the same `window.eval()` DOM CustomEvent channel `updates.rs` already used -
  no permission, no capability change, a no-op in a browser host. The save
  answers phase A's own `LlmStatus` and the banner refetches once on it, so a
  concern the analyst just resolved leaves the screen instead of lingering.

**MAJOR**

- **W2X-001 — CLOSED.** The timeout surface. Three of four LLM calls timed out
  at the 120s ceiling while the UI showed one static word - and in the runs
  panel three "Working…" at once, because one shared `busy` flag served three
  unrelated requests. `web/src/lib/progress.tsx` is a hook that owns one call's
  `AbortController` and elapsed clock, plus the row a panel renders from it
  ("Generating the plan… 12s elapsed" + a Cancel button). Every LLM-backed call
  in the shell carries the signal now - plan, code, interpret, draft, refine,
  chat, agent proposal - and each panel's busy state is per action, so the
  button that is in flight is the only one that says so. A cancel is reported
  as a sentence ("Cancelled - the plan was not generated"), never as a failure.
  The shell does not shorten the core's timeout or retry: cancelling aborts the
  browser's request, and a fallback that arrives after a cancel is the core's
  business. The deterministic fallback banner was already shipped
  (`sourceLabel` reads `deterministic fallback` and announces the substitution);
  this task is the wait itself.
- **W2X-002 — CLOSED.** The form answers instead of going quiet: submitting
  "New Analysis Case" with a blank field now names the fields it still needs
  in `role="alert"` live regions, marks them `aria-invalid`, clears a message
  once the field is filled, and never leaves the page - the browser's native
  validation was the only thing behind the submit, and its message is
  invisible headlessly and undiscoverable for a first-time analyst. Both
  labels now carry the `*` and the dataset's says what to put there.
  `web/src/CaseCreation.tsx`; 4 tests in `web/src/CaseCreation.test.tsx`.
- **W2X-005 — CLOSED.** The stage guidance shows an action, not an endpoint:
  "Next: Attach a dataset" with a "Go to the Data panel" button that
  scrollIntoViews the panel that performs it, and the raw path moved behind a
  "developer info" disclosure where it still answers the reader who wanted
  it. The core side of the same fix fills `{dataset_id}` with the first
  attached dataset and drops the placeholder when no dataset exists yet, so
  the path the disclosure quotes is a path that runs instead of a literal
  that 404s. `web/src/panels/WorkflowRail.tsx` (7 tests) +
  `web/src/CaseWorkspace.tsx` (panel anchors) + `server/app/workflow.py`
  (2 tests in `server/tests/test_workflow.py`).
- **W2X-006 — CLOSED.** The generated code is editable: `GeneratePanel`'s
  `<pre>` is a `textarea` holding a `draft` that starts as the proposal and is
  what the run posts, so an untouched proposal runs unchanged and a one-token
  fix for a 400 costs no second LLM call. `web/src/panels/GeneratePanel.tsx`;
  4 tests in `web/src/panels/GeneratePanel.test.tsx`.
- **W2X-007 — CLOSED.** The capability has a surface of its own: a
  `RunCodePanel` in the work zone with an engine selector (SQL default,
  Python the analyst's choice), a blank editor, and the two run endpoints
  the codegen panel already posted to. `web/src/panels/RunCodePanel.tsx`
  mounted in `DataPanel.tsx`; 7 tests in
  `web/src/panels/RunCodePanel.test.tsx`.
- **W2X-008 — CLOSED.** The density was measured, and the fix hides what has
  nothing to say and collapses what the case has already finished. `web/src/lib/
  disclosure.tsx` is a `<button>` + `role="region"` pair (native `<details>` was
  rejected: its open state is the browser's, so it cannot be seeded from the
  case's artifacts and a test cannot read what it chose). The record group -
  Learn, History, Save as a template - is one collapsed container; Findings and
  the Evidence graph stay mounted only once the case has them, and the
  overview's "Still to come" names the ones still waiting. The guidance a 404
  used to give is not lost: the summaries name the failure ("Case history —
  could not be read"), so a missing case still reads as missing.
- **W2X-013 — CLOSED.** The orientation column's fixed 15rem wrapped a long
  question into a 101pt block. `minmax(15rem, 17rem)` lets it breathe; the work
  and intelligence zones keep the rest.
- **W2X-009 — CLOSED.** The deterministic drafter promoted the planted outlier
  (revenue 99,589, 758.6x the next-largest value the profile already
  flagged) as the case's finding, and the validator then blamed the wrong
  column. The trust loop closed on a false number wearing a
  `partially_supported` badge. `server/app/drafter.py` + `server/app/main.py`.

**MINOR**

- **W2X-003 — CLOSED.** The on-screen chart is gone after a reopen (0 svgs)
  though the artifact is stored and the evidence graph records it. The chart
  lived in local state that a remount resets, and the panel it sat in only
  mounted once the analyst showed the rows. `RunsPanel` + `api.getChart`.
- **W2X-004 — CLOSED.** The Context panel showed "unsaved edits" from the moment
  the case opens, though nothing was touched. The false dirty state was in the
  Decision panel's implications editor, not the Context panel: `dirty` was
  derived from a join comparison, so a parent reload handing the panel a fresh
  view object read as an edit. `web/src/DecisionPanel.tsx`.
- **W2X-010 — CLOSED.** The case list showed two rows for the same question
  and the same dataset with nothing to tell them apart but a timestamp nobody
  reads. The core now answers the question itself: `POST /cases` carries a
  `duplicate_of` when another case asks this exact question about this exact
  dataset (migration 14, `cases.duplicate_of`, advisory like `template_id`).
  The pair is not a constraint - a duplicate is a case in its own right, and
  re-running an old question is a normal thing to do - so the case is made and
  the form says it: a warn-toned sentence under the form naming the question
  and dataset, with a link to the case it repeats, and the list row itself
  carries `repeats case <id>`. `server/app/main.py` + `server/app/db.py` +
  `server/app/models.py`; 10 in `server/tests/test_cases.py`; 8 in
  `web/src/CaseCreation.test.tsx` + 3 in `web/src/CaseList.test.tsx`.
- **W2X-011 — CLOSED.** Clicking a case row's text did nothing; only the Open
  button opened it. The button was already the whole width of the row but was
  only as tall as its own text, so the blank part of the row was not the
  button. `flex: 1 0 auto` stretches the button to the row's height, so any
  part of the row opens the case (`web/src/CaseList.tsx`, `web/src/index.css`).
- **W2X-013 — CLOSED.** The orientation column's fixed 15rem wrapped a long
  question into a 101pt-tall block; `minmax(15rem, 17rem)` lets it breathe and
  the work zone keeps the rest (`web/src/index.css`).

### Carried decisions (not code, unchanged)

- The packaged app is unsigned: macOS gatekeeps the first launch (right-click,
  Open). Signing and notarization are deferred indefinitely by DEC-006 (DAH is
  single-user) - not blocked, and worth revisiting if the user count moves
  beyond one.
- GitHub Actions refuses every job with "recent account payments have failed";
  nothing pushed since `c73118c` has run in CI, and v0.2.0-v0.3.4 were built
  locally from the same steps `release.yml` runs. Fix at Settings > Billing &
  plans; no code change.

### Closed follow-ups (resolved by the v0.3.4 close-out)

- **DMG bundling** — closed. The non-determinism was the vendored
  `create-dmg`'s Finder-prettifying AppleScript, which fails when the build is
  invoked without a GUI session (an npm-run subprocess, CI) and succeeds when
  it has one, with no code change between. Its own `--sandbox-safe` flag skips
  the AppleScript; `desktop/bundle_dmg.sh` passes that flag, verifies the
  image and prints its hash. The image's bytes are then identical run to run
  (the container-level hash still moves, because `hdiutil` stamps the image's
  creation time - the mounted contents are byte-identical, which is the
  property a build is reproducible by).
- **The icon's blind-chosen proportion** — closed, and it was not a defect.
  Measured rather than guessed: the artwork covers 51.4% of the 1024 canvas,
  is dead-centre (x offset 0, y offset -2), carries the correct macOS squircle
  (full canvas, corner radius 66) and reads as an ascending bar chart in cyan
  with the tallest bar in amber. Apple's own guidance is that "you don't need
  to fill the entire icon canvas with content," so the 52% the blind guess
  landed on was right; the follow-up was the guess, not the proportion.
- **The fragile question-refinement test layout** — closed. The describe sat
  outside the `CaseWorkspace` describe and inherited the previous test's
  persisted plan and run reads, because its `beforeEach` cleared the mocks but
  did not re-set the 404 refusals the parent describe sets. Its `beforeEach`
  now sets the same refusals the decision describe already set for the same
  reason (P8-DECISION-008). 116 tests in the file still pass.

## P6 Post-Launch Evolution

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P6-MEMORY-001 | Analysis memory (cross-case recall) | DONE | 11 tests in test_memory.py; P2/P3/P4 gates PASS |
| P6-AGENT-002 | Agentic analysis | DONE | 24 tests in test_agent.py; P2/P3/P4 gates PASS |
| P6-TEMPLATE-003 | Case reuse (templates carry the shape) | DONE | +11 tests in test_case_templates.py; P2/P3/P4 gates PASS |
| P6-MIGRATE-004 | Maintainability (versioned migration path) | DONE | 13 tests in test_migrations.py; P2/P3/P4 gates PASS |
| P6-UPDATE-005 | Distribution (update check) | DONE | 21 tests in test_updates.py + 7 Rust tests; P2/P3/P4 gates PASS |

## Walk-test (selesai, bukan phase)

Tugas evaluasi flow/UI/UX yang TIDAK tercatat di `ai/HANDOFF.md` saat mulai
(tugas tambahan dari user). Bukan lulus gate, bukan membuka phase; tujuannya
menemukan bahan perbaikan. State mesin live: `walktest/HANDOFF.md` (dibaca
pertama oleh session lanjutan). Mekanisme akses + rencana: `walktest/PLAN.md`.
Temuan: `walktest/FINDINGS.md` (append-only, 19 blok). Laporan akhir:
`walktest/REPORT.md`.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| WALK-E2E-001 | Walk-test end-to-end (flow, UI, UX) | DONE | 19 temuan (8 MAJOR, 8 MINOR, 3 OBS); laporan `walktest/REPORT.md`; trust loop case B2B 484-baris tertutup (`loop_closed: true`) |
| WALK-UX-002 | Walk-test round 2 (post-redesign, junior analyst) | DONE - 13 findings, all fixed and released | 13 temuan (1 BLOCKER, 7 MAJOR, 5 MINOR) di `walktest-w2/FINDINGS.md`; fase 2 (app riil `/Applications/DAH.app`) selesai; kepadatan terukur 13,1x viewport browser / 5,8x app riil, 18 panel flat, 0 disclosure. Ketigabelas fixnya (W2X-001..W2X-013) dirilis di v0.3.5 - tag v0.3.4 kosong, hanya menunjuk bump versi, jadi tidak ada satu fix walk-test pun pernah masuk release sebelumnya |

Konfigurasi target: core master diluncurkan via `.app` v0.3.2 dengan
`DAH_DEV_CORE=1` (venv checkout, fix version aktif), LLM dari `server/.env`;
deep DOM walk via Chromium di `:5273` (bundle yang sama dengan Tauri);
permukaan Tauri (menu) diverifikasi via Accessibility.

## P7 Product Modes

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P7-EVAL-001 | EVALUATE mode (audit existing work) | DONE | 22 tests in test_evaluator.py; P2/P3/P4 gates PASS |
| P7-SHELL-002 | UX (EVALUATE in the web shell) | DONE | +6 tests in CaseWorkspace.test.tsx; web build PASS |
| P7-SHELL-003 | UX (the agent in the web shell) | DONE | +7 tests; web build PASS |
| P7-SHELL-004 | UX (rename, duplicate, delete a case) | DONE | +5 tests; web build PASS |
| P7-SHELL-005 | UX (templates in the web shell) | DONE | +11 tests; web build PASS |
| P7-SHELL-006 | UX (cross-case memory actionable in the shell) | DONE | +4 tests; web build PASS |
| P7-SHELL-007 | UX (EDA in the web shell) | DONE | +6 tests; web build PASS |
| P7-SHELL-008 | UX (the evidence graph in the web shell) | DONE | +4 tests; web build PASS |
| P7-SHELL-009 | UX (case history in the web shell) | DONE | +3 tests; web build PASS |
| P7-LEARN-001 | LEARN mode (the guided walk, core) | DONE | +9 tests; P2/P3/P4 gates PASS |
| P7-SHELL-010 | UX (LEARN mode in the web shell) | DONE | +6 tests; web build PASS |
| P7-AGENT-001 | Multi-agent workflows (roles, core) | DONE | +13 tests; P2/P3/P4 gates PASS |
| P7-SHELL-011 | UX (the multi-agent surface) | DONE | +5 web tests; web build PASS |
| P7-E2E-001 | Verification (real-server e2e) | DONE | 25 steps over real HTTP; 3 runs green |
| P7-WALK-001 | Verification (manual shell walkthrough) | DONE | walked the shipped shell by hand; 1 bug fixed, 380 tests + e2e green |
| P7-CORS-001 | Reliability (the packaged app's webview) | DONE | CORS for the shell's origins; 4 tests, +4 (384), e2e green |
| P7-CSV-002 | Data Layer (a stray trailing comma) | DONE | 4 tests, +4 (388), e2e green |


## P8 Analytical Contract

Goal: close the PRD's Level 1 breadth gaps and make "done" measurable. DAH
implements its trust model narrowly (validation 3 of 9 dimensions, quality
detection 2 of 7 defect classes, question capture one text field) and measures
nothing; this phase widens the trust machinery first - the PRD's own rule is
that convenience is sacrificed before analytical trust - and then measures it.
See `docs/PRD & UX Conformance Evaluation.md` for the gap analysis this phase
answers.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P8-RELEASE | Distribution (the phase's releases) | DONE | tags v0.2.0 (ec819fc, 409 tests), v0.3.0 (ab56541, 686 tests) v0.3.1 (19cefc1, the squircle icon) and v0.3.2 (2ff1bca,
  the icon's artwork scaled to 52% of the canvas); artifacts built locally - CI's billing is suspended - and published as flagged pre-releases with checksums |
| P8-CONTEXT-001 | Data Layer (the case's context object) | DONE | 21 tests added (409 server, 82 web); schema v10; e2e green |
| P8-QUALITY-002 | Data Layer (quality beyond missingness) | DONE | 26 tests added (435 server, 84 web); schema v11; e2e green |
| P8-VALID-003 | Validation (3 checks to 9 dimensions) | DONE | 16 tests added (451 server, 85 web); e2e green; schema v11 |
| P8-CAUSAL-004 | Validation (the causal-language guard) | DONE | 16 tests added (468 server, 86 web); 50-case corpus measures 100% on AT-18's three thresholds; e2e green; schema v11 |
| P8-GOLDEN-005 | Verification (the analytical golden suite) | DONE | 21 reference calculations match at 100% (AT-40); 21/21 scripted runs complete the loop at 100% over 3 datasets (AT-01); 477 server, 86 web; e2e green |
| P8-SHELL-006 | UX (the orientation spine) | DONE | 13 tests added (477 server, 99 web); AT-33's seven questions answerable from the rendered workspace; e2e green |
| P8-REFINE-007 | AI (question refinement) | DONE | 41 tests added (518 server, 106 web); schema v12; AT-04's four thresholds measured over 50 cases at 100%/100%/0/0; e2e green |
| P8-DECISION-008 | UX (the decision view) | DONE | 30 tests added (548 server, 116 web); schema v13; 28/28 e2e; the verdict persists, the export carries it |
| P8-MEASURE-009 | Verification (the measurement layer) | DONE | 644 server, 138 web, e2e 28/28; every measured AT holds - AT-38 core 93.9% / analytical 92.9% / evidence 92.4%, AT-37 0/0, AT-28 p95 223ms, AT-29 p95 1.5s, AT-46 at the envelope |
| P8-TRACE-010 | Verification (the traceability matrix) | DONE | 48/48 rows resolve; P0 15/15 (100%), P1 33/33 (target >= 95%); 686 server, 138 web; e2e 28/28 |

### P8-TRACE-010 contract

```
TASK ID: P8-TRACE-010
MILESTONE: P8 Analytical Contract
CAPABILITY: Verification (the requirement-traceability matrix)
GOAL: AT-48, the PRD's section 59 control artifact. The PRD asks for a matrix
      that carries each requirement from the PRD through the UX surface, the
      implementation and the test to the threshold that says it holds - and
      until now that matrix was the PRD's own table, nine rows of checkmarks a
      human keeps up to date. This task makes it code: 48 rows, one per
      acceptance threshold, each cell naming a real thing in the repository,
      and one runner that resolves every cell against the repository as it
      actually stands. A matrix someone types drifts the moment a symbol is
      renamed; a matrix the gate resolves does not.
CONTEXT: last in the phase because it traces what the first nine delivered,
         and every AT now has a measured number for it to point at - the
         golden suite (AT-40/AT-01), the refinement runner (AT-04) and the
         measurement layer (AT-27..30/32/37/38/45/46) each wrote a committed
         report the matrix cites as evidence, and the suites hold the rest.
INPUTS: the PRD (its 48 AT headers and its section 53 release-blocking list),
        the UX architecture document (its numbered sections), the source of
        every module and component the matrix names, the test modules it
        cites, and the committed reports the measured rows point at.
RELEVANT FILES: verification/trace/matrix.py (new - the 48 rows, the cell
                types, the release-blocking categories), verification/trace/
                verify_trace.py (new - the resolver, the requirement-set check,
                the AT-48 fold, the report), verification/trace/REPORT.md
                (written by the runner), server/tests/test_trace.py (new, 42
                tests), ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The matrix is data, not prose. Each row carries the AT id and title, the
    PRD header line quoted exactly, whether the requirement is
    release-blocking and which of the PRD's section 53 categories it guards,
    the UX surface (a shipped component, a section of the UX document, or an
    explicit "no surface, and here is why"), the implementation (a file and a
    name defined in it), the tests (a file and the tests defined in it), the
    threshold in the PRD's own words, and where the measured number lives.
  - The runner resolves every cell: the PRD header must appear in the PRD, a
    component must ship and define the component named, a UX section must
    still carry its number and its title, a Python implementation or test must
    define the name at module level (an AST check), a cited runner must exist
    and the report it wrote must be committed, mention the AT and carry its
    own green sentence. A report carrying a failure marker is a red gate,
    because a measurement that stopped holding is not evidence.
  - The requirement set is checked against the PRD itself: the matrix's ids
    must be exactly the PRD's ids, so a requirement the PRD adds is a red gate
    until a row exists for it, and a row the PRD no longer states is a phantom
    the gate rejects.
  - Fifteen rows are P0, each naming one of the PRD's eight section 53
    categories: data loss, fabricated evidence, fabricated execution, an
    incorrect validated finding, a broken evidence chain, a critical security
    vulnerability, a critical analytical calculation error, and an
    unrecoverable case. AT-48's two thresholds compute from the resolved rows
    - 100% of P0 and >= 95% of P1 - rather than being asserted.
  - The report is the PRD's own table shape (requirement, UX, implementation,
    test, verification, threshold, verdict) plus the two AT-48 numbers, so a
    release gate can read it.
NON-GOALS: re-measuring anything - the matrix cites the runners and reports
           that already measure (golden, refine, measure) and points at the
           suites that assert, it does not run them; a browser-side
           measurement; a product surface for the matrix (section 59 calls it
           an engineering control artifact, not a user feature).
CONSTRAINTS: green only. No new dependency (DEC-001 - the resolver is ast and
             re). Deterministic and offline: the runner reads files that are
             committed and never touches the network. Read-only: it resolves,
             it does not execute the product.
ACCEPTANCE CRITERIA:
- [x] every one of AT-01..AT-48 has a row, and the row's ids are exactly the
      PRD's ids - no requirement untraced, no phantom row
- [x] every cell resolves: a missing file, a renamed symbol, a deleted test, a
      moved UX section, an uncommitted report or a red one is a named failure
- [x] the PRD header each row quotes is the PRD's own line, so a drift in the
      PRD is caught rather than silently mirrored
- [x] every P0 row guards a category the PRD's section 53 actually names
- [x] AT-48's thresholds are computed: 100% of P0 (15/15) and >= 95% of P1
      (33/33), and a single broken P0 row turns them red
- [x] the matrix can fail: a deliberately broken row is caught for each of the
      six ways a row can break, and the failure names the requirement
- [x] every cited measurement is real: the runner exists, the report is
      committed, it mentions the AT, and it carries its green sentence
- [x] the report renders the PRD's control-artifact table with a verdict per
      requirement, and is written to verification/trace/REPORT.md
TESTS: test_trace.py (42) - the 48 ids are the PRD's 48 in order, no
       requirement untraced or phantom, a requirement the PRD adds is an
       untraced red gate and a row it does not state is a phantom one, no AT
       traced twice, every row states a threshold and names an implementation,
       tests and evidence, the P0/P1 split is real and the section 53
       categories are the PRD's, an invented category fails, one broken P0 row
       fails the 100% threshold, and the six ways a row breaks - a missing
       file, a renamed symbol, a deleted test, a renumbered and a renamed UX
       section, a component that no longer ships and one that changed name, a
       no-surface cell without a reason, an uncommitted report, a missing
       runner, a report that went red, one that lost its marker, one that no
       longer mentions the requirement, and a missing suite - each fail and
       name what broke. Plus the gate itself green, the report written and
       readable, and AT-48's own row tracing to the matrix and these tests.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (686);
              `server/.venv/bin/python verification/trace/verify_trace.py`
              green (48/48 rows, AT-48 PASS);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (28/28); `server/.venv/bin/python
              verification/golden/verify_golden.py` green;
              `server/.venv/bin/python verification/refine/verify_refine.py`
              green; `server/.venv/bin/python verification/measure/
              verify_measure.py` green (9/9); `cd web && npm test && npm run
              build` green (138, build ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the P8 table closes at 10 of
              10. No schema change.
```

TASK: P8-TRACE-010 - the requirement-traceability matrix
ID: P8-TRACE-010
PRIORITY: high
STATUS: DONE
SUMMARY: the PRD's control artifact is code. Forty-eight rows carry every
         acceptance threshold from the PRD through the UX surface, the
         implementation and the test to the threshold that says it holds, and
         one runner resolves every cell against the repository as it stands.
         What makes it a control artifact rather than a document is that a
         renamed symbol, a deleted test, a renumbered UX section, an uncommitted
         report or a red one is a named failure - the matrix cannot quietly
         disagree with the thing it traces. The requirement set is checked
         against the PRD's own headers, so an acceptance threshold the PRD adds
         is a red gate until a row exists for it. Fifteen rows are
         release-blocking by the PRD's section 53, each naming the category it
         guards, and AT-48's thresholds compute from the resolved rows: 15/15
         (100%) and 33/33 against a >= 95% target. The matrix's own measurement
         is honest about which rows are measured and which asserted: the
         measured ones cite a runner and its committed report, and the asserted
         ones name the suite that pins them. One thing the resolution made
         visible and fixed: the AST check for a module-level name missed
         annotated constants (`INPUT_ERROR_TYPES: tuple[...] = ...`), so an
         implementation cell citing one read as undefined until the check
         learned `AnnAssign` - the kind of gap a matrix that only listed paths
         would never have found.

## Post-phase fixes

Fixes worked off the carried follow-up list after P8 closed - each is one
defect the shipped product still carried, taken in priority order. A phase is
not reopened for these; the fix's own contract and verification are below.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| FIX-VERSION-001 | Distribution (the packaged core's own version) | DONE | 8 tests added (694 server, 138 web); the packaged binary answers `current: 0.3.2` at `/updates/latest`; both packaged-core smokes now assert it |
| FIX-EVIDENCE-002 | Validation (the evidence check's number regex, W-015) | DONE | +5 tests (699 server, 138 web); golden 21/21, e2e all pass, refine AT-04, measure 9/9, trace 48/48 |
| FIX-PLAN-003 | UX (the plan stage's missing button, W-011) | DONE | 4 tests added (727 server, 167 web); the empty state's own sentence finally has the control that performs it - a POST to the plan endpoint, the plan rendered in place, the rail and the counts reloaded with it, and an existing plan offers nothing |
| FIX-CHART-004 | UX (a chart surface, W-016) | DONE | 6 tests added (727 server, 173 web); a run with a result can render a chart and see it inline as the core's own SVG, the pickers offer only the run's columns, a refusal shows the renderer's sentence, and the evidence count moves |
| FIX-PYTHON-005 | UX (a python run surface, W-016) | DONE | 4 tests added (727 server, 177 web); a python run can be generated and executed from the shell - the panel offers SQL and Python, the proposal matches the kind, and the run posts to the sandbox's own endpoint |
| FIX-TIMEOUT-006 | Reliability (the interpret/draft LLM timeout, W-014) | DONE | +24 tests (723 server, 140 web); every adapter posts one configured 120s timeout; a fallback source renders as a sentence; e2e all pass, golden 21/21, refine AT-04, measure 9/9, trace 48/48 |
| FIX-REFINE-007 | UX (the refinement's rationale, W-009) | DONE | +3 web tests (143 web total); "Why these changes" renders the rationale and grounds the API returns, shown rather than disclosed, and stays readable after an accept |
| FIX-PROFILE-008 | Reliability (the automatic re-profiling, W-008) | DONE | +4 web tests (147 web total); the mount GETs the profile and the analyst's POST is on request - no write on open, an offer when there is none, a re-profile when there is |
| FIX-UPDATES-009 | Distribution (the silent update check, W-005) | DONE | web 163 (+16), Rust 25 (+6); the three statuses reach the window as the shell's own notice, the log line still writes, the browser still opens an available build |
| FIX-VERSION-010 | Distribution (the dev checkout's stale version, W-001) | DONE | 4 tests added (727 server, 163 web); a dev checkout answers `current: 0.3.3` at `/updates/latest`, the source's number, with a stale metadata's drift logged rather than silently believed |

Prioritas adalah urutan tabel di atas (WALK-E2E-001's report menetapkannya:
W-015, W-011, W-016, W-014, lalu W-009, W-008, W-005, W-001). Satu commit per
fix. W-016 pecah jadi dua task (chart, python) karena keduanya tidak berbagi
kode selain panel tempatnya mendarat. Contract masing-masing di bawah.

Urutan eksekusi untuk session baru: FIX-EVIDENCE-002 dulu (paling terlokalisir,
hanya `server/app/evaluator.py`, tidak butuh infrastruktur walk-test yang
masih hidup). Lalu FIX-PLAN-003, FIX-CHART-004, FIX-PYTHON-005 (web), dan
baru FIX-TIMEOUT-006 (server + web). Empat terakhir (FIX-REFINE-007,
FIX-PROFILE-008 web; FIX-UPDATES-009 Rust; FIX-VERSION-010 server) bebas
urutan, dan ketiganya selain FIX-VERSION-010 sudah selesai; FIX-VERSION-010
selesai juga sekarang - urutan resolusinya menjadi stamp > pyproject >
metadata. Setiap fix: baca contractnya di file ini, implementasi, tes, full
gate (server pytest + e2e + golden + refine + measure + trace, web test +
build), lalu commit + push. Walk-test infra (core :8123 pid 84940, web :5273,
Tauri dah-shell 84919) masih hidup bila perlu memverifikasi ulang; cara
menjalankannya di `walktest/HANDOFF.md`.


## P9 UI/UX Redesign

Goal: the shell is functionally complete - every walk-test finding closed and
48/48 requirements traced - but the surfaces are the hand-written CSS and
hand-rolled markup of an MVP that grew. P9 makes them a designed system. The
stack, decided with the user: npm stays (CI hardcodes `npm ci`, Tauri's
beforeDevCommand uses `npm --prefix`), the theme is light first, and recharts
draws the on-screen chart because the server's chart SVG bakes a white
background into the image and is static - while its layout engine and PNG
export stay for the export path. Four phases, green at each: F1 the foundation,
F2 the surfaces, F3 motion, F4 the chart surface and a re-walk.

| Task ID | Capability | Status | Verification |
|---------|-----------|--------|--------------|
| P9-F1-001 | Foundation (tooling, tokens, structure) | DONE | web 181 (177 + 4 panels tests), build ok, tsc clean, server 727, e2e 28/28, golden 21/21, refine AT-04, measure 9/9, trace 48/48 |
| P9-F2-001 | Surfaces (the walk-test's last three findings) | DONE | web 184 (+3), build ok, tsc clean, trace 48/48; W-013/W-017/W-018 closed |
| P9-F2-002 | Surfaces (the restyle onto the tokens) | DONE | web 185 (+1), tsc clean, build ok (CSS 14.44 kB), trace 48/48; 109 lines of hand-written CSS retired |
| P9-F3-001 | Motion (the motion layer and its gate) | DONE | web 197 (+12), tsc clean, build ok (CSS 15.11 kB, JS 347 kB), trace 48/48; framer-motion used, `prefers-reduced-motion` honoured by the JS-driven motion too |
| P9-F4-001 | Charts (the on-screen chart and a re-walk) | DONE | web 216 (+19), server 728 (+1), tsc clean, build ok (CSS 16.46 kB, JS 744 kB), trace 48/48, e2e 28/28; recharts used, the re-walk found the missing `format` field and the tooltip is verified in a browser |

### P9-F3-001 contract

```
TASK ID: P9-F3-001
MILESTONE: P9 UI/UX Redesign (phase F3, motion)
CAPABILITY: Motion (the motion layer and its gate)
GOAL: framer-motion@13 was installed in F1 and imported nowhere - the same
      debt shape F2 just paid, one phase earlier. This is the motion: a
      panel's content appearing as the case loads, a run row opening, a
      verdict landing. The constraint is `prefers-reduced-motion`, which the
      CSS already honours for the shell notice (`index.css`'s explicit
      `animation: none` rule); F3 makes the JS-driven motion honour it too
      rather than only the CSS-driven kind. A motion budget is the
      discipline: an animation that costs a frame the measurement layer
      (AT-27/AT-30) counts is a regression, not a polish.
CONTEXT: F1 shipped the toolchain and the tokens; F2 moved every surface onto
         them. The surfaces are the wrappers the panels already render - a
         run row is `surfaces.row`, a verdict is `surfaces.proposal` - so the
         motion attaches to those wrappers rather than to new elements, and a
         motion surface is the `div` the panel was already drawing. The
         measurement layer pins AT-27's interaction response at 200ms p95 and
         AT-30's visible state at 100% of long-running operations, and both
         are asserted in `measure.test.tsx` against the disclosure this layer
         animates - so the budget is measured, not asserted in prose.
INPUTS: framer-motion@13 (installed, unused), `web/src/index.css`'s existing
        reduced-motion rule for the shell notice, the panels' surface
        wrappers, and the measurement suite that pins the budget.
RELEVANT FILES: web/src/lib/motion.tsx (new - the variants, the transitions,
                the `ReducedMotion` gate, the `MotionSurface` component),
                web/src/motion.test.tsx (new, 12 tests),
                web/src/setup-tests.ts (the matchMedia shim),
                web/src/App.tsx (the gate mounted at the root),
                web/src/CaseWorkspace.tsx, web/src/CaseList.tsx,
                web/src/panels/RunsPanel.tsx, web/src/panels/FindingsPanel.tsx,
                web/src/panels/Chat.tsx, web/src/index.css (the CSS gate),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - The vocabulary: `transitions` names three - `surface` (0.18s, what a
    click opens), `enter` (0.28s, what a case loads) and `arrive` (a spring,
    what a verdict does) - and `variants` names the same three, each a
    `hidden` state and a `shown` one with the transition riding inside the
    target so the gate's collapse to `shown` is the end of the motion. The
    movement is 4-6px and never an element's own height, because layout
    shift is the cost AT-27 counts; the arrival scales by 2% rather than
    sliding, because it is the loop's exit and the weight reads.
  - The gate: `ReducedMotion` mounts `MotionConfig reducedMotion="user"`
    once at the root in `App.tsx`, so every screen resolves the analyst's
    OS preference through it. The collapse is this layer's own, not the
    library's: framer-motion makes positional keys instant under reduced
    motion but still fades opacity, and a reduced-motion setting that still
    moves the surface is a setting the surface is not honouring, so
    `MotionSurface` reads `useReducedMotionConfig()` and sets
    `initial={false}` - the surface renders its shown state with no
    animation at all, the same result the CSS gives the shell notice.
  - The CSS gate, `index.css`'s second `prefers-reduced-motion` rule, holds
    a `[data-motion-surface]` at opacity 1 and transform none. It is the belt
    to the JS braces: a surface that starts hidden and is never animated to
    shown - because the engine was absent, or a frame was dropped on a slow
    machine - is invisible content, and this rule is what keeps the content
    present when the motion does not run.
  - The matchMedia shim in `setup-tests.ts`: jsdom has no `matchMedia`, and
    the library's preference resolution reads through it, so the shim is what
    makes the gate behave in the suite the way it behaves in a browser. It is
    stubbed in `beforeEach` and unstubbed in `afterEach`, so a test that
    changes the preference does not leak into the accessibility audit or the
    measurement layer.
  - The surfaces that moved: the workspace's three zones (the panels appear
    as the case loads), a run row and its rows table, the chart surface, a
    verdict, a chat answer, and a case row on the list. Every one is the
    wrapper the panel already rendered, now a `MotionSurface` carrying the
    same `className`; no markup was added and no surface was restyled.
NON-GOALS: restyling anything (F2's parity stands; a new look is a later pass
           that decides on purpose what changes), the on-screen chart (F4 -
           recharts is installed and still unused, and the chart this phase
           animates is the core's own SVG, unchanged), a dark theme, touching
           the server, and changing any test's assertion rather than the
           element it reads.
CONSTRAINTS: green only. No new dependency (framer-motion is F1's, now used).
             Deterministic and offline. The accessibility audit's
             STATUS_CLASSES contract is unchanged, and the audit is
             structural - it does not read opacity, so a surface that starts
             hidden passes it; the CSS gate is what protects the analyst the
             audit cannot see. Web-only: no line outside `web/` moves.
ACCEPTANCE CRITERIA:
- [x] framer-motion is imported and the motion is the surfaces' own: a panel
      arriving, a row opening, a verdict landing, a case row on the list
- [x] every variant is inside the budget: 0.18s for a click's surface, 0.28s
      for a case load, and a spring whose settle (4 * mass / damping) is
      under 0.3s
- [x] a surface slides a little and never its own height - 6px or less, so
      no motion this layer adds moves another panel
- [x] the gate closes: `reducedMotion="always"` renders the shown state with
      no animation, and the surface's opacity is not the hidden one
- [x] the CSS gate holds a motion surface visible when the motion does not
      run, and the shell notice's own rule is still there beside it
- [x] the gate is mounted once at the root, so a screen it does not wrap is
      a screen the analyst's setting does not reach
- [x] no other behaviour moved: the existing 185 assertions pass unchanged,
      the emitted stylesheet still resolves the focus rule the accessibility
      audit reads, and the disclosure the measurement layer times is inside
      its budget with the motion in the tree
TESTS: `motion.test.tsx` (12) - the three variants each carry the state the
       gate collapses and come to rest visible, the movement is bounded, the
       transitions are inside the 200ms budget numerically and the
       disclosure's open is measured with the motion mounted, the gate
       renders visible content when open and its end state when closed, the
       helper reads the preference the same way, the CSS rules resolve from
       the shipped stylesheet, and the root wraps every screen.
VERIFICATION: `cd web && npm test && npm run build` green (197 = 185 + 12,
               tsc clean, build ok - the emitted CSS is 15.11 kB and still
               resolves the focus rule, the JS 347 kB);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48 rows, AT-48 PASS - the symbols the matrix cites
               still resolve). Web-only, so the server suite (727), the e2e
               (28/28), golden (21/21), refine (AT-04) and measure (9/9) are
               not re-run: no line outside `web/` moved (verified by
               `git status`), and their last runs are green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the task; the P9 table closes
              at F3-001. No schema change, no version bump.
```

TASK: P9-F3-001 - the motion layer and its gate
ID: P9-F3-001
PRIORITY: high
STATUS: DONE
SUMMARY: the motion the surfaces were missing, and the one gate that decides
         whether any of it runs. `web/src/lib/motion.tsx` names three
         transitions - a click's surface at 0.18s, a case load at 0.28s, a
         verdict's spring - and three variants to match, each a hidden state
         and a shown one with the transition riding inside the target. The
         movement is 4-6px and never an element's own height, because layout
         shift is the frame AT-27 counts; the verdict scales by 2% because
         the loop's exit carries weight. `ReducedMotion` mounts
         `MotionConfig reducedMotion="user"` once at the root, and the
         collapse is this layer's own rather than the library's:
         framer-motion makes positional keys instant under reduced motion but
         still fades opacity, so `MotionSurface` reads
         `useReducedMotionConfig()` and sets `initial={false}`, rendering the
         shown state with no animation at all - the same result the CSS gives
         the shell notice. A second `prefers-reduced-motion` rule holds a
         `[data-motion-surface]` visible, because a surface that starts
         hidden and is never animated to shown is invisible content, and that
         is the failure mode the JS gate cannot see itself out of. The lesson
         the gate earned: `useReducedMotion()` caches the OS preference in
         `useState` at first read, so a probe that reads it outside the
         `MotionConfig` provider always answers the default - the preference
         is a context, not a global, and the two are not interchangeable.


### P9-F4-001 contract

```
TASK ID: P9-F4-001
MILESTONE: P9 UI/UX Redesign (phase F4, charts)
CAPABILITY: Charts (the on-screen chart, and a re-walk)
GOAL: recharts@3 is the last of F1's three dependencies still at zero
      imports. The chart the shell shows is the core's own static SVG -
      white background baked in, no tooltip, no hover - because the shell
      draws what the core already drew rather than drawing a second time.
      This phase changes the renderer of what the analyst *looks at*, not
      of what the case *holds*: recharts draws the on-screen chart from the
      run's stored result, and the core's SVG and PNG stay the persisted
      artifact, the exported package and the evidence. What the new
      renderer adds is what a static image cannot: a tooltip that reads a
      point's own values, and a hover state that names what is under the
      cursor. What it must not add is a second source of truth for the
      numbers.
CONTEXT: F1 shipped the toolchain and the tokens, F2 the surfaces, F3 the
         motion. The chart surface this phase replaces is `ChartSurface` in
         `web/src/panels/RunsPanel.tsx`, which draws the core's SVG inline
         through `dangerouslySetInnerHTML` for an SVG chart and a link for a
         PNG one. The renderer the shell uses reads the same run result the
         core's renderer reads - `GET /cases/{id}/runs/{id}` gives the
         columns and the rows, which is what the chart controls already
         offer - so the geometry comes from the same stored numbers the
         finding rests on. F3's motion layer wraps the surface, and the
         surface keeps its `arrive` variant.
INPUTS: recharts@3 (installed, unused), the run result the chart controls
        read (`Run` in `web/src/api.ts`: `columns`, `rows`, `truncated`),
        `ChartModel`'s own rules in `server/app/charts.py` (the series
        split, the plottable-points filter, the palette, the
        zero-anchored bar scale), and the measurement suite that pins
        AT-27's 200ms budget.
RELEVANT FILES: web/src/lib/chart.tsx (new - the recharts surface, the
                shared geometry: series splitting, plottable points, the
                palette), web/src/panels/RunsPanel.tsx (ChartSurface
                replaced; the pickers, the refusal path and the PNG link
                stay), web/src/chart.test.tsx (new), web/src/index.css (a
                rule that holds the chart readable when recharts does not
                run - the CSS-side of the same failure F3's gate covers),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - One geometry, two renderers. The series split, the plottable-points
    filter and the palette are the core's own rules, so they live in one
    module the shell and the tests read, and a divergence between what the
    analyst sees and what the core drew is a named failure rather than a
    drift. The module exports the shape recharts takes - one record per x
    category, one key per series - and nothing else.
  - The surface: `bar` is a `BarChart` with `BarChart`'s bars at the
    palette's colours; `line` is a `LineChart` with `Line` and its points.
    Both carry `XAxis`, `YAxis`, `CartesianGrid`, `Tooltip` and `Legend`
    when there is more than one series. The axes name themselves with the
    columns they plot, and the y axis is zero-anchored for a bar, because
    bar length reads as magnitude. The chart's own title and its source
    line stay where the static surface had them, and the surface keeps
    F3's motion wrapper and its `data-testid`.
  - What a chart must never do here: invent a series, drop a category the
    result had, or plot a point the measure column did not have. The
    transformation is the core's `_series_of`, not recharts' own
    grouping, so the on-screen chart and the stored SVG answer the same
    question the same way.
  - The fallback: the recharts surface is a React tree, and a React tree
    can fail to render - a measure column with no plottable points, a
    category list that came back empty, a shape recharts rejected. A
    surface that renders nothing is the static-SVG failure mode without
    the static SVG's saving grace, so the surface falls back to the
    core's own image the moment its own geometry is empty, and a CSS
    rule holds the container's height so the panel does not collapse.
  - The artifact is untouched: the PNG chart stays a link to the artifact
    the core wrote, the SVG chart is still stored by the core, and the
    export package and the evidence graph still carry the core's own
    image. No new endpoint, no new persistence, no server line moves.
NON-GOALS: new chart kinds (the PRD's `bar` and `line` are what the core
           renders; a third kind is a change to the core's contract, not
           to the shell), the export path (the core's SVG and PNG are the
           exported artifact and stay so - a chart that changes shape
           between the screen and the export is not evidence), touching
           the server, restyling anything outside the chart surface, and
           any measurement that is not the AT-27 budget the suite already
           asserts.
CONSTRAINTS: green only. No new dependency (recharts is F1's, now used).
             Deterministic and offline: the chart is drawn from a stored
             result, not from a live query, so a re-render is the same
             chart. Web-only: no line outside `web/` moves, so the server
             suite (727), e2e (28/28), golden (21/21), refine (AT-04) and
             measure (9/9) gates are not re-run. The accessibility audit
             is structural and does not read pixels; the tooltip is a
             keyboard-reachable element or it is not shipped.
ACCEPTANCE CRITERIA:
- [x] recharts is imported and the on-screen chart is its tree: a bar
      chart for `bar`, a line chart for `line`, with axes, gridlines, a
      tooltip and a legend when there is more than one series
- [x] the geometry is the core's own rules: the same result renders the
      same series, the same categories and the same points the core's SVG
      does, and a divergence is a test that names it
- [x] the tooltip reads a point's own values and the hover state names
      what is under the cursor - the thing the static SVG could not give
- [x] the axes name themselves with the columns they plot, and a bar's y
      axis is anchored at zero
- [x] the surface falls back to the core's own image when its geometry is
      empty, and the container's height is held by CSS when the tree does
      not render
- [x] the PNG chart is still a link to the core's artifact, and nothing
      about the stored chart, the export or the evidence graph changed
- [x] the disclosure the measurement layer times is inside its budget
      with the recharts tree mounted, and no existing assertion moved
TESTS: `web/src/chart.test.tsx` (19) - the two kinds each render their
       recharts tree from a fixture result, the geometry matches the
       core's own series split and point set for single- and multi-series
       results, a duplicated category keeps both points, a non-plottable
       measure drops a point but keeps its category, the tooltip is the
       live region a hovered point reaches, the axes carry the column
       names and a bar's height is proportional to its value (the
       zero-anchor, measured as a ratio because jsdom has no SVG getBBox),
       the legend appears only with more than one series and names the
       series, the palette agrees with the core's own, the fallback shows
       the core's image when there is nothing plottable, the CSS rule
       resolves from the shipped stylesheet, the PNG path is still a link,
       and a truncated result draws the rows it carries. Plus the existing
       chart assertions in `CaseWorkspace.test.tsx` pass (one updated: the
       source sentence and the testid, both changed by the renderer swap).
VERIFICATION: `cd web && npm test && npm run build` green (216 = 197 + 19,
               tsc clean, build ok - the emitted CSS is 16.46 kB and still
               resolves the focus rule, the JS 744 kB carrying recharts);
               `cd server && .venv/bin/python -m pytest -q` green (728 =
               727 + 1 - the `format` regression);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48); `verification/e2e/verify_e2e.py` green
               (28/28). F4 is not web-only as contracted: the re-walk
               found the core's `Chart` response missing `format`, which
               is why the recharts tree rendered in jsdom and nowhere
               else, so the server moved one field and one test.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the P9 table closes at
              F4, and the phase closes with a re-walk. No schema change.
```

TASK: P9-F4-001 - the on-screen chart, and a re-walk
ID: P9-F4-001
PRIORITY: high
STATUS: DONE
SUMMARY: recharts@3, the last of F1's three dependencies, draws the chart
         the analyst looks at, and the core's own SVG and PNG stay the
         chart the case holds. `web/src/lib/chart.tsx` is both halves: a
         geometry that is the core's `_series_of`/`_numeric`/palette copied
         into the shell, so the screen and the artifact cannot drift, and a
         recharts surface that carries axes naming their own columns, a
         zero-anchored bar, a legend only when there is more than one
         series, and a tooltip that is a live region. The fallback is the
         discipline: a geometry with nothing plottable shows the core's own
         image, because a chart the analyst cannot see is worse than a
         chart the analyst cannot hover, and a CSS rule holds the
         container's height when the tree does not render.
         The re-walk is what the task will be remembered for. The shell
         rendered every chart as a link - the recharts tree appeared in the
         suite and nowhere else, because the core's `Chart` model never
         returned `format` and the shell read `undefined` straight into the
         PNG branch. A jsdom fixture had supplied the field, which is why
         185 tests said green while the feature was dark. One field
         (`format: str = "svg"`, the default the image endpoint already
         sniffs), one regression test, and a browser confirmation: hovering
         a bar answers its own values, "north" and "total_total : 270".
         The lesson: a contract tested only against a fixture the test
         itself builds is a contract the fixture keeps, not the server.


### P9-F2-002 contract

```
TASK ID: P9-F2-002
MILESTONE: P9 UI/UX Redesign (phase F2, the surfaces)
CAPABILITY: Surfaces (the restyle onto the tokens)
GOAL: the debt F1 and F2-001 took on, paid. The token layer shipped in
      `lib/ui.tsx` and nothing imported it; the panels rendered class names
      the hand-written CSS defined. This moves every surface onto the tokens
      and deletes the CSS rules that only existed to name them, so the palette
      is one set of names in one file and a panel reads one surface name
      instead of a string of properties. The restyle is conservative by
      contract: nothing is restyled and nothing is invented, because the
      surfaces are the CSS rules they replace, as utility classes, with the
      same values. The theme is the existing one named, not a new one drawn.
CONTEXT: F1 shipped the tokens and the primitives and used them nowhere, by
         the same rule that let it install dependencies it did not import
         yet. F2-001 added the `surfaces` strings. The workspace is 15 panels
         in `web/src/panels/` plus five screens that are not panels
         (`CaseList`, `CaseCreation`, `Templates`, `ContextPanel`,
         `RefinePanel`, `DecisionPanel`, `NoticeLayer`), and each carried its
         own `className="panel"` / `"subpanel"` / `"proposal"` / `"run"` /
         `"turn"` / `"muted"` / `"row"`. The accessibility audit reads the
         emitted stylesheet (`accessibility.test.tsx`'s `focusIsGuaranteed`),
         so a rule the audit resolves must survive as a literal declaration.
INPUTS: `web/src/lib/ui.tsx` (the tokens and the `surfaces` strings), the 15
        panel files, the five non-panel screens, `web/src/index.css`, and the
        existing test suites, which are the behaviour contract.
RELEVANT FILES: every file above, `web/src/panels/panels.test.tsx` (+1 test -
                the debt-paid assertion), `ai/HANDOFF.md`, `ai/TASKS.md`,
                `ai/CURRENT_STATE.md`.
REQUIRED CHANGE:
  - Every panel and screen swaps its literal `className="panel"` /
    `"subpanel"` / `"proposal"` / `"run"` / `"turn"` / `"muted"` / `"row"` /
    `"stages"` / `"items"` / `"grounds"` / `"rationale"` for the `surfaces`
    string that holds the same values as utility classes. A panel keeps the
    `panel` word in its class because it is a structural landmark the
    workspace's own tests reach with `heading.closest('.panel')` and the zone
    CSS scopes to `.zone .panel`.
  - `lib/ui.tsx` gains the surfaces the restyle needed and F2-001 did not
    name: `labelheading` (the `.panel h4` size), `turn` (a chat turn's own
    padding), `rowGap` and `buttonRow` (a form's control row and the case
    list's action row), and `smallDanger` as a fifth button variant, because
    a variant that is both small and danger was a class string two panels
    composed by hand. `buttonVariants`'s default carries the base button
    rule's own properties, so a bare `<Button>` is the button the CSS drew.
  - The CSS rules those class names defined are deleted in the same pass:
    `.row` and `.row input` / `.row label`, `.panel h2` / `h3` / `h4`,
    `.muted`, `.stages` / `.items` / `.chat` / `.grounds`, `.stage.done`,
    `.turn`, `.turn .question`, `.subpanel`, `.rationale` and `.rationale p`,
    `.proposal` and `.proposal pre`, `.run`, and `.case-actions`. The rules
    that stay are the ones no token can own: the three-zone layout, the
    sticky rail, the verdict and chip shapes the status vocabulary renders
    as text-plus-chip, the quality-issue and shell-notice surfaces, and the
    literal `:focus-visible` rule the accessibility audit resolves.
  - One regression class, found by auditing the rules the deletion removed
    against the source that still used them, and fixed before any commit:
    `LearnPanel` rendered `className="stage done"` and `FindingsPanel`
    rendered `className="muted"`, both of which lost their rules. `.stage.done`
    stays in the CSS (a completed stage is the one green status, and it is
    the rail's and the ladder's shared vocabulary) and the muted check row
    moves to `surfaces.note`, which carries the size and the colour together.
NON-GOALS: restyling anything beyond parity (a new look is a later pass that
           decides on purpose what changes), motion (F3), the on-screen chart
           (F4), a dark theme, touching the server, changing any test's
           assertion rather than the class it reads, and deleting a rule a
           status chip or the audit resolves.
CONSTRAINTS: green only. No new dependency (DEC-001). The accessibility
             audit's STATUS_CLASSES contract is unchanged: no status class is
             added or removed, and nothing new carries a status by colour
             alone. Web-only: no line outside `web/` moves.
ACCEPTANCE CRITERIA:
- [x] every panel and screen renders its surfaces through the token layer,
      and no source file uses a literal `className` the deleted rules defined
- [x] the CSS the build emits no longer carries the retired rules, and the
      emitted stylesheet still resolves the focus rule the audit reads
- [x] the surfaces are the rules they replaced: same values, same specificity
      behaviour, so a panel on a token renders what the CSS rule rendered
- [x] no class that a surviving rule styles lost its rule - every literal
      className still in the source has its CSS (audited rule by rule, which
      is how the `stage done` / `muted` regressions were caught)
- [x] a test asserts the debt stays paid: a panel that goes back to a literal
      `className="panel"` fails by name
- [x] no other behaviour moved: the existing 184 assertions pass unchanged
TESTS: `panels/panels.test.tsx` (+1) - reads every panel's and screen's source
       through Vite's `?raw` and asserts none of the retired class names
       appears as a literal `className`, naming the file and the class. The
       suite's unchanged assertions are the rest of the contract.
VERIFICATION: `cd web && npm test && npm run build` green (185 = 184 + 1,
               tsc clean, build ok, the emitted CSS 14.44 kB and still
               resolving the focus rule);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48 rows, AT-48 PASS - the symbols the matrix cites
               still resolve). Web-only, so the server suite (727), the e2e
               (28/28), golden (21/21), refine (AT-04) and measure (9/9) are
               not re-run: no line outside `web/` moved (verified by
               `git status`), and their last runs are green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the task; the P9 table closes
              at F2-002. No schema change, no version bump.
```

TASK: P9-F2-002 - the restyle onto the tokens
ID: P9-F2-002
PRIORITY: high
STATUS: DONE
SUMMARY: the token layer is the vocabulary the panels use, and the
         hand-written CSS that named those surfaces is gone. Every panel and
         every screen renders through `surfaces` in `lib/ui.tsx`, and 109
         lines of CSS retired with them - `.panel h2/h3/h4`, `.muted`,
         `.stages`/`.items`/`.chat`/`.grounds`, `.turn`, `.subpanel`,
         `.rationale`, `.proposal`, `.run`, `.row` and `.case-actions`. What
         stays is the layout no token can own: the three-zone grid, the
         sticky rail, the verdict and chip shapes the status vocabulary
         renders as text-plus-chip, the quality and notice surfaces, and the
         literal `:focus-visible` the accessibility audit resolves. The
         restyle is parity by contract - a surface is the rule it replaced,
         as utility classes, with the same values, so nothing looks
         different and the palette is one set of names in one file.
         The lesson the audit earned: deleting the retired rules was only
         safe once the rules were checked against the source that used them,
         not against the list of rules the restyle touched. Two literals
         survived the move and lost their rules - `LearnPanel`'s
         `className="stage done"` and `FindingsPanel`'s `className="muted"`.
         The first keeps its rule, because a completed stage is the one
         green status and the word is the rail's and the ladder's shared
         vocabulary; the second moves to `surfaces.note`, which carries the
         size with the colour. The panels test now asserts the debt stays
         paid, reading every source file raw and naming the file and the
         class if a literal comes back.
```

### FIX-CHART-004 contract

```
TASK ID: FIX-CHART-004
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (a chart surface, W-016)
GOAL: a chart is an evidence artifact the core renders, stores and exports,
      and the shell cannot produce one. The runs panel runs a query and the
      evidence graph counts the charts, but between them there is no control
      that asks for a chart, and no surface that shows the one the core drew.
      Every chart is only reachable through its file path. This closes that
      gap for the run that produced the numbers.
CONTEXT: WALK-E2E-001 Fase C created a chart by curl to verify the renderer,
         and the evidence graph, the history and the export all carried it -
         only the shell could not. `grep -c chart web/src/api.ts` is zero.
         The endpoint validates its columns against the run's own result, so
         the control's pickers can only offer what the run produced.
INPUTS: the chart endpoint's payload and response (main.py:2884), the chart
        kinds and formats the renderer supports, the run row's columns, and
        the stored path the response returns.
RELEVANT FILES: web/src/api.ts (a chart helper), web/src/CaseWorkspace.tsx
                (RunRow gains the control and the surface), the renderer and
                the endpoint (unchanged), web/src/CaseWorkspace.test.tsx,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - A run row offers "Render a chart" once it has a result, with pickers for
    the x and y columns the run actually produced and the kind the renderer
    supports, and the control posts to the endpoint that owns the write.
  - The response's chart is shown in the shell - as an inline SVG for the
    default format, and as a link for the others - so a chart is evidence
    the analyst can see, not a path on disk.
  - A chart that fails to render shows the endpoint's own reason as a
    sentence, because the renderer's refusal is the analyst's input.
NON-GOALS: a chart gallery or a chart history view (the evidence graph
           counts them and the export carries them); editing a chart; new
           chart kinds (the renderer's vocabulary is what it is).
CONSTRAINTS: green only. No new dependency. The POST goes to the endpoint
             that owns the write and renders from the stored result.
ACCEPTANCE CRITERIA:
- [x] a run with a result can render a chart, and the chart appears in the
      shell without leaving the case
- [x] the pickers offer only the columns the run produced
- [x] an unsupported choice is refused with the endpoint's own sentence
- [x] the SVG the response carries is what the shell displays
- [x] the evidence graph's chart count moves when a chart is rendered
TESTS: CaseWorkspace.test.tsx (+6) - the control appears only once the run's
       rows are open, the SVG shows inline and the payload carries the run's
       own columns, the measure picker defaults to the numeric column, the
       case reloads so the evidence count moves, a refusal surfaces the
       renderer's sentence with the control standing, and a bitmap is a link
       to the persisted artifact.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (727);
              `cd web && npm test && npm run build` green (173, build ok);
              `verify_e2e.py` green (28/28); `verify_trace.py` green (48/48).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the chart half of
              W-016 closes.
```
TASK: FIX-CHART-004 - the chart surface
ID: FIX-CHART-004
PRIORITY: high
STATUS: DONE
SUMMARY: a chart is now evidence the analyst can produce and see. The run row
         holds a "Render a chart" control that appears once the run's rows are
         open - those columns are the renderer's input and are exactly what
         the pickers offer, with the measure defaulting to a numeric column -
         and it POSTs the endpoint that owns the write. On success the shell
         fetches the SVG the core drew and renders it inline, because drawing
         it a second time would make the shell a second source of truth for
         what the chart looks like; a PNG is a link to the persisted artifact
         instead. The workspace reloads with a chart, so the evidence graph's
         count moves with the panel, and a refusal shows the renderer's own
         sentence with the control standing. Two things the first test run
         caught: the control was offered before the rows were read, which is
         before there is anything to draw from, so it now waits on the result;
         and the surface was asserted as an img role, which jsdom does not
         give an inline SVG - the assertion reads the element instead.

### FIX-PYTHON-005 contract

```
TASK ID: FIX-PYTHON-005
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (a python run surface, W-016)
GOAL: the sandbox executes user Python against an attached dataset and
      persists the result exactly like a SQL run, and the shell has no way to
      ask for one. The codegen panel generates SQL only, and the runs
      endpoint it posts to is the SQL one. A python run is only reachable by
      curl, so the hardening the sandbox exists to prove is untested by
      anyone using the app.
CONTEXT: WALK-E2E-001 Fase C ran python through the endpoint: the seatbelt
         refused a bad script with a 400 and an honest reason, and a correct
         one produced a run that the evidence graph, the history and the
         export all carried. `grep -rn "runs/python" web/src` is empty. The
         generator already supports kind 'python' and the endpoint and its
         model already exist; only the shell's request is missing.
INPUTS: the python run endpoint (main.py:1778), its `PythonRunCreate` model,
        the generator's kind parameter and its python output, the sandbox's
        contract (a `dataset` handle, a `result` the run tabulates), and the
        codegen panel's existing propose-and-run shape.
RELEVANT FILES: web/src/api.ts (a python run helper), web/src/CaseWorkspace.tsx
                (the codegen panel gains a kind, the run posts to the python
                endpoint), web/src/CaseWorkspace.test.tsx, the endpoint and
                the sandbox (unchanged), ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The codegen panel offers SQL and Python, and the proposal it generates
    matches the kind chosen, so a python question is answered with python.
  - Running a python proposal posts to the python endpoint, and the run it
    persists is a run like any other - the same runs panel, the same
    evidence chain, the same validation.
  - A sandbox refusal is the analyst's input: its detail is the sentence the
    panel shows, not a broken panel.
NON-GOALS: a python editor with a console; a package installer; changing the
           sandbox (its allowlist, its seatbelt profile and its row cap are
           the contract the surface now exposes).
CONSTRAINTS: green only. No new dependency. The POST goes to the endpoint
             that owns the write; the panel does not execute code itself.
ACCEPTANCE CRITERIA:
- [x] the panel generates python for a python question and the code it
      proposes is what the sandbox accepts
- [x] running a python proposal creates a run the runs panel and the
      evidence graph carry
- [x] a script the sandbox refuses answers a 400 whose detail the panel
      shows as a sentence
- [x] the kind persists across proposals in the same panel
- [x] the SQL path is unchanged in behaviour and in its tests
TESTS: CaseWorkspace.test.tsx (+4) - python generation and its run, the
       engine persisting across proposals, the refusal surfaced, SQL
       unaffected (its own test still asserts the run posts to the SQL
       endpoint and never the python one).
VERIFICATION: `cd server && ... pytest -q` green (727);
              `cd web && npm test && npm run build` green (177, build ok);
              verification/e2e, golden, refine (AT-04), measure (9/9) and
              trace (48/48) all green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the python half of
              W-016 closes and W-016 is done.
```

### FIX-PYTHON-005 done-record

```
TASK: FIX-PYTHON-005 - a python run surface
ID: FIX-PYTHON-005
PRIORITY: high
STATUS: DONE
SUMMARY: the codegen panel now offers two engines where it offered one. A
         kind selector (SQL, the default, and Python) picks the code the
         generator is asked for and persists across proposals in the same
         panel, and the run posts to the endpoint matching the proposal's own
         kind rather than the selector's current value - the code the analyst
         read is the code that executes. `runPython` posts to the sandbox's
         own endpoint, which was reachable only by curl before, so the hard
         sandbox P3-SEC-001 exists to prove is now exercised by someone using
         the app. A persisted python run is a run like any other: the same
         runs panel, the same evidence chain, the same validation. The
         seatbelt's 400 detail renders as a sentence and the proposal stands
         to be fixed and retried. Two things the first test run caught: two
         radios named python/sql on the same page (the EVAL panel's own
         kind-toggle) matched every /python/i query, so the codegen radios
         carry their own aria-label and the audit test now scopes its click to
         its panel; and a multi-line script does not survive getByText's
         whitespace normalisation, so the pre's own textContent is what the
         assertion reads.
```

### FIX-TIMEOUT-006 contract

```
TASK ID: FIX-TIMEOUT-006
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: Reliability (the interpret/draft LLM timeout, W-014)
GOAL: two of the three assistant slices never use the LLM in practice: the
      interpret and draft endpoints wait exactly thirty seconds, time out,
      and fall back to deterministic, and the shell shows "Working…" for the
      whole thirty seconds with no indication that an engine failed and
      another answered. The planner and refine endpoints, at sixty seconds,
      finish. The analyst reads a deterministic reading believing it was the
      LLM's, because the only tell is a small source label.
CONTEXT: WALK-E2E-001 Fase C reproduced this on every interpret and draft
         call: the log line is `llm read failed; falling back to
         deterministic: The read operation timed out` at 30133ms and
         30184ms, while the generator at 30s and refine at 60s succeeded.
         The timeouts are interpreter.py:239, drafter.py:312 and
         assistant.py:576 at 30.0; planner.py:366 and refine.py:595 at 60.0.
INPUTS: the five LLM call sites and their timeouts, the fallback contract
        (any failure degrades, the source field records which engine
        answered), and the panels that render the source label.
RELEVANT FILES: server/app/interpreter.py, server/app/drafter.py,
                server/app/assistant.py (the timeouts), the web panels that
                render `by <source>` (the announcement), the tests for both,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The timeouts are one configured value the environment can raise, default
    high enough that a slow endpoint answers before the harness gives up on
    it, so the engine a case configured is the engine that answers.
  - A fallback is announced rather than labelled: the panel says the LLM was
    unavailable and a deterministic reading was used in its place, in the
    same place the source label sits, so the analyst knows which engine
    spoke and that it was not the one asked.
  - The contract that any failure degrades is untouched: a plan, a reading
    and a draft are still always returned, and the source still records
    which engine produced them.
NON-GOALS: changing the fallback itself (the contract is the point);
           retrying (a second thirty seconds is not a better answer);
           streaming (the endpoints answer once, whole).
CONSTRAINTS: green only. No new dependency. The default is a number, not a
             behaviour; the tests inject the failure rather than waiting for
             it, so no test is slower for the change.
ACCEPTANCE CRITERIA:
- [ ] the three 30s call sites read the same configured value, and the
      planner's 60s is the same value's neighbour
- [ ] a slow endpoint that would have timed out answers before the timeout
- [ ] the source the response carries still records which engine answered
- [ ] a panel showing a deterministic answer after an LLM failure says so in
      a sentence the analyst reads
- [ ] no test waits the timeout to reach its failure
TESTS: test_interpreter.py / test_drafter.py (+~4, the timeout is read from
       the value and a slow engine still answers), the web panel's
       announcement (+~2).
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-014 closes.
```

### FIX-REFINE-007 contract

```
TASK ID: FIX-REFINE-007
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (the refinement's rationale, W-009)
GOAL: accepting a refinement is a black box. The API returns a rationale and
      the grounds it rests on, and the panel renders neither, so the analyst
      approves a change to their own question without being told why the
      change was proposed or what in the profile supports it. "Why these
      changes" is the panel's own heading and it sits empty.
CONTEXT: WALK-E2E-001 Fase B accepted a deterministic refinement and the
         heading stayed blank; the response carries the fields the panel
         does not read.
INPUTS: the refinement response's rationale and grounds fields, the panel's
        heading and its accepted state.
RELEVANT FILES: web/src/RefinePanel.tsx, web/src/CaseWorkspace.test.tsx,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The proposal renders its rationale as the answer to the heading that
    asks, and the grounds it names - the profile's own columns and measures,
    which is what makes the suggestion honest - are listed where the analyst
    can see what the suggestion rests on.
  - The accepted state keeps the proposal readable, so the change the
    analyst accepted stays explained after it is applied.
NON-GOALS: changing the refinement engines or their output; editing a
           rationale; re-proposing automatically.
CONSTRAINTS: green only. No new dependency. The fields are already in the
             response; this is rendering what the API returns.
ACCEPTANCE CRITERIA:
- [x] a proposal shows its rationale under its own heading
- [x] the grounds the proposal names are listed, and they are the response's
- [x] an accepted refinement keeps its rationale and grounds readable
- [x] a proposal without grounds renders nothing rather than an empty list
TESTS: CaseWorkspace.test.tsx / RefinePanel (+~3).
VERIFICATION: `cd server && ... pytest -q` green; `cd web && npm test && npm
              run build` green.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-009 closes.
```

TASK: FIX-REFINE-007 - the refinement's rationale is rendered
ID: FIX-REFINE-007
PRIORITY: high
STATUS: DONE
SUMMARY: accepting a refinement was a black box. The API returned a
         `rationale` and the `grounds` it rests on - the profile's own
         columns and measured ranges, which is what makes a suggestion
         honest - and `RefinePanel` had both inside a `<details>` that
         renders collapsed, so "Why these changes" read as inert text and
         the analyst approved a change to their own question without being
         told why it was proposed or what supports it. The disclosure is
         gone: the rationale sits under a real `<h4>` heading of its own,
         the grounds list below it, both always visible, and both still
         rendered after an accept so a change the analyst made stays
         explained. `.rationale` carries the proposals' left rule and
         ground so the block reads as support rather than another paragraph,
         and `.panel h4` exists because no panel had used a fourth-level
         heading. Three tests cover it: the proposal shows its rationale and
         both grounds under the heading, an accepted proposal keeps them
         readable, and a proposal without grounds renders no empty list.

### W3X-002 contract (the fallback sentence is not glued to the label it replaces)

```
TASK ID: W3X-002
MILESTONE: post-phase (the third walk-test's findings, WALK-UX-003)
CAPABILITY: UX (the engine-source announcement, shared by seven panels)
GOAL: the substitution announcement - the analyst's only signal that the
      engine they configured did not answer - must read as a sentence, not as
      a label with a typo glued to it. W2X-001/FIX-TIMEOUT-006 made the
      fallback visible; this keeps it legible.
CONTEXT: `web/src/sourceLabel.ts` returns one of five full sentences when
         `source` is `deterministic fallback` (each engine module owns the
         server-side wording through SOURCE_FALLBACK_SENTENCE). Seven panels
         render that label; three of them append their own context directly
         after it in JSX: PlanPanel (" for {filename}"), GeneratePanel
         (" — reads {columns}"), AgentPanel (" — approve to run it, or reject
         with your reason"). DraftPanel's sentence stood
         beside "— accepting records a real finding". The measured rendering
         was "...answered in its place. for helpdesk_tickets_2026.csv" -
         a period followed by a lowercase fragment.
INPUTS: `web/src/sourceLabel.ts` (the shared label), the three call sites that
        append context, the two surfaces that render the sentence beside a
        second thought, and `web/src/CaseWorkspace.test.tsx` (regex
        assertions on the fallback sentences, which must keep matching).
RELEVANT FILES: web/src/sourceLabel.ts (+sourceWith), web/src/sourceLabel.test.ts
                (new, 7 tests), web/src/panels/PlanPanel.tsx,
                web/src/panels/GeneratePanel.tsx,
                web/src/panels/AgentPanel.tsx (sourceWith at the three call
                sites that append context),
                web/src/panels/DraftPanel.tsx (the sentence as its own <p>),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md.
REQUIRED CHANGE:
  - Nothing about the sentences themselves. `sourceLabel` is unchanged; the
    server's wording (the owner, per FIX-TIMEOUT-006) is untouched, and the
    panels that render the label with no context of their own
    (RunsPanel, Chat, RefinePanel) are untouched too.
  - One new helper next to it: `sourceWith(source, kind, context)` returns
    `by {source} {context}` for a plain label, and for a fallback takes the
    sentence as it stands and capitalises the context's first letter, so the
    period is followed by a grammatical clause instead of a fragment. The
    context stays the panel's own; the helper owns only the join.
  - The three call sites that appended context now go through it.
    DraftPanel renders the sentence as its own `<p>` and its "accepting
    records a real finding" note as the sibling it always read as.
NON-GOALS: changing any fallback sentence's wording (the server's), changing
           the engine-side `SOURCE_FALLBACK_SENTENCE`, touching the panels
           that render the label alone, and any change to the endpoints, the
           sandbox or the capability set.
CONSTRAINTS: green only. Shell-only, no new dependency (DEC-001), no LLM
             call. The existing regex assertions in CaseWorkspace.test.tsx
             continue to match because the sentences are unchanged.
ACCEPTANCE CRITERIA:
- [x] no panel renders a period followed by a lowercase fragment as its
      engine-source line
- [x] the five fallback sentences themselves are byte-identical to before
- [x] a plain `by {source}` label still takes its appended context unchanged
- [x] the panels that rendered the label with no context are untouched
- [x] CaseWorkspace.test.tsx's regex assertions on the sentences still match
- [x] a unit test pins the join: fallback + context is the sentence, then a
      capitalised clause; and the two shapes never disagree about which
      engine answered
TESTS: web 7 in sourceLabel.test.ts - the plain label, the fallback sentence,
       the join for a plain label, the measured typo shape asserted absent,
       the join for a fallback, a context already carrying its own dash, and
       the two shapes naming the same engine.
VERIFICATION: `cd web && npx vitest run` green (285 = 278 + 7);
              `npx tsc -b` clean; `npm run build` ok.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W3X-002 closes and
              the carried list drops to one (W3X-003). No schema change.
```

TASK: W3X-002 - the fallback sentence is not glued to the label it replaces
ID: W3X-002
PRIORITY: high
STATUS: DONE
SUMMARY: the announcement W2X-001 made visible now reads as a sentence. The
         fix kept the sentences, the server's wording and the panels that
         render the label alone completely untouched, and moved only the
         join: the three panels that append their own context go through
         `sourceWith`, which capitalises the context so a sentence that ends
         with a period takes a grammatical clause instead of the lowercase
         fragment the walk-test measured. DraftPanel's "accepting records a
         real finding" became the sibling paragraph it always read as.

### W3X-004 contract (the Python surface's own contract)

```
TASK ID: W3X-004
MILESTONE: post-phase (the third walk-test's findings, WALK-UX-003)
CAPABILITY: Analysis Workspace (the Python run surface, microcopy + UX)
GOAL: a first-time analyst's first three interactions with the Python engine
      are not three blind refusals. The three the walk measured were
      `import pandas`, `import csv` and the `path` variable the SQL
      placeholder implies exists; the answers - `dataset.rows`, the stdlib
      subset, the shape a run takes - were nowhere on the page, and the
      analyst's only teacher was the 400. The sandbox keeps refusing exactly
      as it did: refusing is the security property, and this task changes
      none of it. What changes is the page.
CONTEXT: walktest-w3/FINDINGS.md (W3X-004, MAJOR) - three 400s in
         walktest-w3/logs/core-stdout.log and the 201 that followed once
         `dataset.rows` and `statistics` were guessed; the placeholder was
         `# python`. The handle is `_DatasetHandle` in
         server/app/python_exec.py (`.rows`, `.columns`, `.query(sql)`), the
         import wall is `_SAFE_MODULES` in the same file, and the canonical
         use is server/tests/test_python_runs.py:40-73.
INPUTS: the sandbox's own allowlist and handle, the panel's existing surface,
        and the codegen panel's placeholder as the style the SQL engine
        already carries (`read_csv_auto(?)`).
RELEVANT FILES: web/src/panels/RunCodePanel.tsx (the contract surface and the
                placeholder), web/src/panels/DataPanel.tsx (passes the
                profiled columns), web/src/index.css (the contract's surface,
                with its own reduced-motion rule), RunCodePanel.test.tsx,
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The panel shows the contract while the Python engine is chosen: the
    handle (`dataset.rows`, `dataset.columns`, `dataset.query`), that there
    is no file path, the importable modules as one sentence naming pandas,
    csv and numpy as the refused ones with statistics as the alternative, and
    the shape a run takes (a list of dicts left in `result`).
  - The placeholder stops being `# python` and becomes the canonical use -
    read the handle, accumulate, leave the table in `result` - so an
    analyst who runs it as it stands gets a run, not a refusal. The SQL
    placeholder names `read_csv_auto(?)` and a column the dataset has.
  - The contract is the Python engine's own: it appears when Python is
    chosen and is absent on SQL, which carries its own contract in its
    placeholder.
  - The module list the panel shows is the sandbox's `_SAFE_MODULES`, and a
    test reads the frozenset from the Python source to prove the two are one
    set - the page does not get to claim a door the wall refuses.
NON-GOALS: weakening or widening the sandbox; changing `_SAFE_MODULES`,
           the handle, the endpoints or the capability set; adding a
           dependency or a Tauri command; touching the refusal messages,
           which stay exactly as they are; an endpoint that publishes the
           allowlist (the page carries the sentence, not the wall).
CONSTRAINTS: green only. Shell-only. No new dependency (DEC-001). The
             surface follows the token layer and the CSS conventions
             (`.duplicate-notice`'s warn-toned left rule, an explicit
             `prefers-reduced-motion` entry, text carrying the whole
             meaning so colour is never the signal - AT-32).
ACCEPTANCE CRITERIA:
- [x] with Python chosen, the page names `dataset.rows` before any run
- [x] the page names the refused modules (pandas, csv, numpy) and the
      alternative (statistics) - the answers to refusal 1 and 2
- [x] the page says there is no file path - the answer to refusal 3
- [x] the page shows the shape a run takes, and the placeholder is a
      runnable script rather than `# python`
- [x] the module list the panel shows equals `_SAFE_MODULES`, verified
      against the Python source
- [x] the contract is present only for the Python engine; SQL is unchanged
- [x] the sandbox, the endpoints, the capability set and the refusal
      messages are untouched; the server suite is unchanged and green
TESTS: RunCodePanel.test.tsx (+6) - the handle/columns/query sentence, the
       three refusals' answers, the allowlist-equals-`_SAFE_MODULES` drift
       test, the placeholder's shape, generic terms for an unprofiled
       dataset, and SQL/Python contract parity on engine switching.
VERIFICATION: `cd web && npm test` green (278/278); `npx tsc -b` clean;
              `npm run build` ok; `cd server && .venv/bin/python -m pytest`
              788/788; verification/trace 48/48; verification/e2e 28/28.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W3X-004 closes.
```

TASK: W3X-004 - the Python run surface teaches its own contract
ID: W3X-004
PRIORITY: high
STATUS: DONE
SUMMARY: the Python engine is the one a Python-fluent analyst reaches for
         first, and its first three interactions were refusals whose answers
         were not on the page - `import pandas`, `import csv`, and the
         `path` variable the SQL placeholder implies exists, answered only
         by a 400. The sandbox was correct to refuse, so the fix is the sign
         on the wall rather than the wall: the panel shows the contract
         while Python is chosen - the handle `dataset.rows` / `.columns` /
         `.query(sql)` and that there is no file path, the importable subset
         as one sentence that names pandas, csv and numpy as refused with
         `statistics` as the alternative, and the list-of-dicts-in-`result`
         shape a run takes. The placeholder stopped being `# python` and
         became the canonical use the core's own tests write, so an analyst
         who runs it as it stands gets a run. The contract is the engine's
         own: it appears on Python and is absent on SQL, whose placeholder
         carries its own contract (`read_csv_auto(?)`). The allowlist the
         page shows is read out of `_SAFE_MODULES` by a test, so the two
         cannot drift. Nothing in the sandbox, the endpoints, the capability
         set or the refusal messages moved.

Contracts for the rolling window (the two most recent: W3X-003-PROMPT and
W3X-004). Older blocks are in `ai/TASKS-ARCHIVE.md`.
