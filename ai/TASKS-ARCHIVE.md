### P9-F1-001 contract

```
TASK ID: P9-F1-001
MILESTONE: P9 UI/UX Redesign (phase F1, the foundation)
CAPABILITY: Foundation (tooling, tokens, structure)
GOAL: the redesign has a foundation to stand on. Three things are missing
      today and each is a prerequisite for the phases that follow: the
      styling is one 608-line hand-written CSS file, so a design system
      means a token layer before any surface is redrawn; the chart is drawn
      by the server and inlined as an image, so an on-screen chart means
      recharts is installed before F4 wires it; and the workspace is one
      2,889-line component file, so a panel can be redesigned without
      opening a file that holds 30 of them. F1 lays all three without
      changing a single thing the analyst sees: every screen renders
      byte-identically to today.
CONTEXT: `web/src/index.css` is 608 lines of hand-written CSS, `web/package.json`
         declares two dependencies (react, react-dom) and the project has
         been dependency-free by intent (DEC-001's "no new dependency" is
         about the *browser* contract - the frontend never touches the
         filesystem or DuckDB directly - and a styling and charting stack
         does not touch it; the precedent is vitest, jsdom and the
         testing-library already in devDependencies). `web/src/CaseWorkspace.tsx`
         holds 2,889 lines and 33 components; the composition root (lines
         260-371) renders each panel exactly once. The accessibility audit
         reads the shipped stylesheet from the DOM (accessibility.test.tsx:328,
         `focusIsGuaranteed`) so the token layer must keep a real
         `:focus-visible` rule. The traceability matrix cites ~40 web
         component names against `web/src/CaseWorkspace.tsx` (matrix.py lines
         195-669), and for a .tsx file resolution is a regex presence check
         (`verify_trace.py:179`), so a symbol that moves must keep its name
         reachable in the file the matrix names, or the matrix must move
         with it. P9-F1-001 is the only task that touches the toolchain.
INPUTS: `web/package.json`, `web/vite.config.ts`, `web/src/index.css`,
        `web/src/main.tsx`, `web/src/CaseWorkspace.tsx` (33 components,
        lines 96-2889), `web/src/accessibility.test.tsx`,
        `verification/trace/matrix.py`.
RELEVANT FILES: new `web/src/lib/ui.ts` (the tokens and primitives), new
                `web/src/panels/*.tsx` (one file per panel), the three
                config files above, and the two test files that pin
                behaviour: `web/src/accessibility.test.tsx` (the audit) and
                `web/src/measure.test.tsx` (AT-27/AT-30, the browser-side
                budgets). `verification/trace/matrix.py` follows its symbols.
REQUIRED CHANGE:
  - **Deps.** `web/package.json` gains tailwindcss@4 + @tailwindcss/vite
    (the Vite plugin; no postcss config, no tailwind.config.js - v4 is
    CSS-first and configured with `@import "tailwindcss"` in the
    stylesheet), framer-motion@13, recharts@3 (peer-compatible with
    react@18), and the shadcn support deps lucide-react, clsx,
    tailwind-merge, class-variance-authority. `npm install` regenerates
    `web/package-lock.json`, which commits. **Nothing imports them yet** -
    a dependency that ships unused is F1's debt and F2's capital.
  - **Vite.** `web/vite.config.ts` registers `@tailwindcss/vite()` so the
    stylesheet is compiled at build and in dev, and the vitest `css: true`
    audit keeps reading the emitted rules.
  - **Tokens.** `web/src/lib/ui.ts` defines the light theme as CSS custom
    properties in a `:root` block plus the semantic names the panels will
    use in F2 - not styled components yet, the vocabulary: `bg`, `surface`,
    `surface-muted`, `border`, `text`, `text-muted`, `accent`, `accent-text`,
    and the status pairs `ok` / `warn` / `danger` (each a text colour and a
    tinted background, because DAH renders verdicts as text-plus-chip, never
    colour alone - `accessibility.ts`'s STATUS_CLASSES audit pins it). The
    values are the ones the current CSS already uses (#fafafa page, #fff
    panel, #ddd border, #666 muted, #1a4a7a accent, #2a7a2a / #8a6a1a /
    #a03a2a statuses), so the theme is the existing one named, not a new one
    invented - the light theme comes first because dark is a swap of the
    same token names.
  - **Primitives.** `ui.ts` also ships the three primitives F2 builds on,
    each a plain function component over `className` (no runtime
    dependency on a styled library): `Panel` (the bordered card every
    surface is built on), `Button` (variants via class-variance-authority:
    default, link, danger, small - the four `button` and `button.link` /
    `button.small` / `button.danger` shapes the CSS has today), and `Card`.
    They render with the existing class names so the current CSS keeps
    them honest while the token layer is unused, and F2 swaps the classes
    for tokens one panel at a time.
  - **Stylesheet.** `web/src/index.css` gains `@import "tailwindcss"` at
    the top and keeps every existing rule below it, unchanged, so the
    emitted CSS is the current 608 lines plus Tailwind's base and
    utilities. The focus rule is the one the audit reads
    (`button:focus-visible, a:focus-visible, ... { outline: 2px solid
    #1a4a7a }`) and it stays as a literal rule, because a utility class
    (`focus-visible:outline-2`) satisfies a browser but not the audit's
    regex, which looks for `:focus-visible` followed by a declaration.
  - **Split.** `web/src/CaseWorkspace.tsx` keeps the composition root
    (state, `load()`, the three-zone layout and its prop plumbing, lines
    96-372) and `export`s every panel it renders; each of the 32 panel
    components moves into `web/src/panels/<Panel>.tsx`, one file per
    component, importing what it needs from `../api` and `../lib/ui` and
    exporting the same name it had. The composition root imports them
    back. The two helpers with no JSX (`stageStatus`, `nodePhrase`) move
    into the panels that use them. Every panel is used exactly once, so
    the split is a move per name with no shared state between panels -
    the workspace holds the state, the panels are pure over their props.
  - **No behaviour change.** Not one user-visible byte moves. The
    requirement is not "it looks the same" but "the tests that assert the
    rendered output are unchanged": the accessibility audit passes
    unchanged, the measurement suite's AT-27/AT-30 budgets pass
    unchanged, and `CaseWorkspace.test.tsx`'s 177 assertions pass
    unchanged. A `panels/` test file is added asserting the split itself:
    every panel file exports its component, the composition root imports
    all of them, and no panel file exceeds the 600-line ceiling that keeps
    the split from recreating the problem in miniature.
NON-GOALS: restyling any panel (F2), motion (F3), the on-screen chart (F4),
           a dark theme (later), touching the server or its chart renderer
           (its SVG and PNG stay the export path), changing any API shape,
           and changing any test's assertion rather than its imports.
CONSTRAINTS: green only. npm stays (CI hardcodes `npm ci` at ci.yml:125,
             release.yml:146/150; Tauri's beforeDevCommand is
             `npm --prefix ../web`). React 18, not 19 - recharts@3's peer
             range allows both and the app pins 18. `package-lock.json`
             commits; a dependency that is installed but never imported is
             acceptable in F1 and is debt F2 must pay. Deterministic and
             offline once installed: the gates do not touch the network.
ACCEPTANCE CRITERIA:
- [x] `web/package.json` carries tailwindcss, @tailwindcss/vite, framer-motion,
      recharts, lucide-react, clsx, tailwind-merge and
      class-variance-authority, and `web/package-lock.json` is regenerated
      and committed
- [x] `@tailwindcss/vite()` is registered and `index.css` begins with
      `@import "tailwindcss"`, with the 608 existing rules preserved below it
- [x] the focus rule survives as a literal `:focus-visible` declaration that
      `focusIsGuaranteed` still resolves against the emitted stylesheet
- [x] `web/src/lib/ui.tsx` ships the light-theme tokens (the current palette
      named) and the `Panel` / `Button` / `Card` primitives
- [x] `web/src/panels/` ships one file per panel, and `CaseWorkspace.tsx`
      imports every one of them; the file's own line count drops from 2,889
      to the composition root alone (337 lines), and no panel file exceeds
      600 lines (the largest is RunsPanel at 485)
- [x] the panel names the traceability matrix cites are still defined where
      the matrix looks for them (the matrix follows its symbols if a name
      moves; `verify_trace.py` stays green at 48/48 - `matrix.py:607` moved
      `FindingRow` to `FindingsPanel.tsx`)
- [x] no user-visible change: the accessibility audit, the measurement
      suite and `CaseWorkspace.test.tsx` pass unchanged in their assertions
- [x] a new `web/src/panels/panels.test.tsx` asserts the split itself: the
      files exist, the exports match the imports, and the 600-line ceiling
      holds per file
TESTS: `web/src/panels/panels.test.tsx` (new) - every panel module imports
       and exports its named component, the composition root imports the
       same set (a set-difference assertion, so a panel that moves without
       its import is a named failure), and the line-count ceiling is
       asserted per file from disk. Plus the unchanged suites as the
       behaviour contract.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
               .venv/bin/python -m pytest -q` green (727, unchanged - F1
               is web-only);
               `cd web && npm test && npm run build` green (181 = 177
               unchanged + 4 new panels tests, build ok, and the emitted
               CSS still resolves the focus rule);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48 rows, AT-48 PASS - the matrix's cited symbols
               resolve after the split);
               `server/.venv/bin/python verification/e2e/verify_e2e.py`
               green (28/28); `verify_golden.py` (21/21 both thresholds),
               `verify_refine.py` (AT-04 PASS) and `verify_measure.py`
               (9/9) green - run from the repo root, because the coverage
               module invokes pytest with no path and inherits the cwd, so
               a run from verification/measure collects the wrong suite and
               AT-38 reads 22% instead of 94%.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the task; the P9 table opens
              at F1. No schema change, no version bump.
```

TASK: P9-F1-001 - the redesign's foundation
ID: P9-F1-001
PRIORITY: high
STATUS: DONE
SUMMARY: three prerequisites landed and nothing the analyst sees moved. The
         toolchain: tailwindcss@4 through @tailwindcss/vite (CSS-first, one
         `@import` in index.css, no postcss config, no tailwind.config.js),
         framer-motion, recharts and the shadcn support deps, with
         package-lock regenerated. Nothing imports them yet - a dependency
         that ships unused is F1's debt and F2's capital. The tokens:
         web/src/lib/ui.tsx holds the light theme the hand-written CSS
         already used (#fafafa page, #fff panel, #ddd border, #666 muted,
         #1a4a7a accent and the three status pairs DAH renders as
         text-plus-chip, never colour alone) plus the Panel / Button / Card
         primitives. The split: CaseWorkspace.tsx dropped from 2,889 lines
         to a 337-line composition root, and its 15 panels moved into
         web/src/panels/, every one under the 600-line ceiling (RunsPanel
         is the largest at 485).
         The split was generated by split_panels.py, which now closes the
         loop with tsc itself: the heuristic import lists are a first
         guess, the compiler is the authority, and the script parses its
         own two import errors (TS6133 unused, TS2304 missing) and
         adjusts the lists until the compiler is quiet. Three things the
         loop caught that the heuristic could not: a duplicate span in the
         group table had defined CaseOverview twice (in CaseOverview.tsx
         and again in DataPanel.tsx); formatValue was EdaPanel's TS2304
         because no group owned it (RunsPanel provides it); and AgentPanel's
         Profile/Run imports read as unused because the heuristic stripped
         template literals as prose - `` `Profile ${str('filename')}` `` is
         where the panel actually reaches the type, so the strip is now
         single-quoted literals only. A fourth, in the test's own regex:
         a `[\s\S]*?` spec matched across the whole file and read the react
         import's names as a peer panel's.
         The traceability matrix's AT-30 row cited
         web/src/panels/FindingRow.tsx, a file the split never made;
         FindingRow lives in FindingsPanel.tsx, and matrix.py:607 follows
         it. The panels test asserts the split itself by importing every
         panel module and holding the set against the root's own imports.
```

TASK: P9-F1-001 - the redesign's foundation
ID: P9-F1-001
PRIORITY: high
STATUS: DONE
SUMMARY: three prerequisites landed and nothing the analyst sees moved. The
         toolchain: tailwindcss@4 through @tailwindcss/vite (CSS-first, one
         `@import` in index.css, no postcss config, no tailwind.config.js),
         framer-motion, recharts and the shadcn support deps, with
         package-lock regenerated. Nothing imports them yet - a dependency
         that ships unused is F1's debt and F2's capital. The tokens:
         web/src/lib/ui.tsx holds the light theme the hand-written CSS
         already used (#fafafa page, #fff panel, #ddd border, #666 muted,
         #1a4a7a accent and the three status pairs DAH renders as
         text-plus-chip, never colour alone) plus the Panel / Button / Card
         primitives. The split: CaseWorkspace.tsx dropped from 2,889 lines
         to a 337-line composition root, and its 15 panels moved into
         web/src/panels/, every one under the 600-line ceiling (RunsPanel
         is the largest at 485).
         The split was generated by split_panels.py, which now closes the
         loop with tsc itself: the heuristic import lists are a first
         guess, the compiler is the authority, and the script parses its
         own two import errors (TS6133 unused, TS2304 missing) and
         adjusts the lists until the compiler is quiet. Three things the
         loop caught that the heuristic could not: a duplicate span in the
         group table had defined CaseOverview twice (in CaseOverview.tsx
         and again in DataPanel.tsx); formatValue was EdaPanel's TS2304
         because no group owned it (RunsPanel provides it); and AgentPanel's
         Profile/Run imports read as unused because the heuristic stripped
         template literals as prose - `` `Profile ${str('filename')}` `` is
         where the panel actually reaches the type, so the strip is now
         single-quoted literals only. A fourth, in the test's own regex:
         a `[\s\S]*?` spec matched across the whole file and read the react
         import's names as a peer panel's.
         The traceability matrix's AT-30 row cited
         web/src/panels/FindingRow.tsx, a file the split never made;
         FindingRow lives in FindingsPanel.tsx, and matrix.py:607 follows
         it. The panels test asserts the split itself by importing every
         panel module and holding the set against the root's own imports.

```

# DAH - Task Archive

Completed task contracts and their done-records, moved out of `ai/TASKS.md` by
the rolling-window rule in `AGENTS.md`. Nothing is edited on the way in - these
are the records as they were written, in their original order. `ai/TASKS.md`
holds the phase summary tables, the still-open carried follow-ups and the
rolling window (the two most recent tasks); everything else is here.

---

### P8-DECISION-008 contract

```
TASK ID: P8-DECISION-008
MILESTONE: P8 Analytical Contract
CAPABILITY: UX (the decision view)
GOAL: UX 46 and AT-43: the loop's exit. A validated finding used to be the end
      of the road - the verdict was computed, shown and discarded, and nothing
      in the product closed over what the loop had established. The PRD's own
      flow (UX 48) ends at Decision Support -> Export. This task makes the
      decision a first-class object the case carries: the validated findings,
      each with its residual uncertainty - the checks that did not pass, never
      a score - the claims still open, and the implications the analyst writes.
      DAH informs decisions; it does not make them.
CONTEXT: the seven tasks before it built what the view reads - the nine
         validation dimensions and the causal guard that produce the verdicts
         (P8-VALID-003, P8-CAUSAL-004), the golden suite that measured them
         (P8-GOLDEN-005), the orientation spine that says where the case stands
         (P8-SHELL-006), and the refinement that sharpened the question the
         view opens on (P8-REFINE-007).
INPUTS: the case's question, the context's purpose, every finding with the
        verdict validation computed (status, nine checks, validated_at) and its
        own caveat, the workflow's own loop-closed flag, and the analyst's
        implications. Nothing is executed and nothing is derived that is not
        already on disk.
RELEVANT FILES: server/app/decision.py (new - the view's assembly and the
                implications' rules), server/app/main.py (the three endpoints,
                the persisted verdict, the duplicate and the delete),
                server/app/db.py (schema v13, two tables, one migration),
                server/app/models.py (DecisionView, DecisionWrite,
                DecisionFinding, DecisionOpenItem, DecisionCheck),
                server/app/history.py (two new event kinds),
                server/app/exporter.py (the two new package sections and their
                import), server/tests/test_decision.py (new, 30 tests),
                server/tests/test_case_history.py (the timeline's two new
                kinds), verification/e2e/verify_e2e.py (+3 steps, a PUT helper),
                web/src/DecisionPanel.tsx (new), web/src/CaseWorkspace.tsx,
                web/src/api.ts, web/src/CaseWorkspace.test.tsx (+10 tests),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The verdict stops being ephemeral. validate_finding computed nine checks
    and kept only the status; now the whole verdict (status, checks,
    validated_at) is persisted, so a decision is read without re-running a
    single query and a reopened case still shows what validation found. A new
    GET /cases/{id}/findings/{fid}/validation answers it read-only, and a
    never-validated finding is a 404 naming the endpoint that creates one
    rather than an empty list.
  - The view: GET /cases/{id}/decision is read-only, deterministic and executes
    nothing. It answers the question, the purpose the analyst stated, the key
    findings (supported / partially_supported) each carrying its caveat and the
    checks that did not pass as its uncertainty, the open items (a finding
    awaiting validation, or one the verdict refused, naming the hard dimension
    that failed), counts, and the analyst's implications. The loop's closure is
    the core's to declare - the view reads workflow.case_progress rather than
    restating it, so the decision cannot disagree with the rail.
  - The only write is the implications: PUT /cases/{id}/decision with a list of
    strings. It validates what it accepts - a list, each entry non-empty after
    trimming, at most twelve, at most two thousand characters - and answers 400
    naming the first entry that breaks a rule. An empty list clears them, which
    is a decision the analyst is allowed to make.
  - A case's decision travels: the export gains the verdicts and the decision,
    and the import round trip restores both, so AT-43's "validation states
    preserved" is a property of the package rather than a claim about it. The
    duplicate carries both; the delete removes both.
  - The timeline gains two events - the validation itself, now that it has a
    timestamp of its own (AT-44 names validation among its minimum events), and
    the decision the analyst wrote.
  - The shell (UX 46): the panel is last in the work zone, where the loop
    exits. Question, key findings with their caveats, the uncertainty, the
    claims still open, the implications the analyst edits, and the case's
    export - which had no surface in the shell at all, and whose natural home
    is the decision it sits beside.
NON-GOALS: the agent proposing implications - DAH informs decisions and does
           not make them, so no agent step touches the decision view;
           measurement of the view (P8-MEASURE-009); a formatted report output
           (PDF / markdown, UX 47's future list); scoring, ranking or
           recommending anything; the traceability matrix (P8-TRACE-010).
CONSTRAINTS: green only. No new dependency (DEC-001). Schema v12 -> v13, one
             in-place migration creating two tables. Read-only by default: the
             GET executes nothing, and the PUT is the only write. Deterministic
             and offline. UX 44's rule holds throughout - no confidence score
             appears anywhere in the view.
ACCEPTANCE CRITERIA:
- [x] every validated finding appears in the decision view with its residual
      uncertainty, and a check that did not pass is named, never scored
- [x] the view is read-only: reading it executes nothing and writes nothing,
      and the second read answers the first's verdict
- [x] the verdict persists, so a case reopened shows what validation found
      without re-validating
- [x] the implications are the only write, and a bad entry is a 400 naming it
- [x] export carries the verdicts and the decision, and the round trip
      restores both with fresh ids
- [x] the duplicate carries them; the delete removes them
- [x] the timeline records the validation and the decision
- [x] the shell renders the view, and the case's export is reachable from it
- [x] the view's loop-closed is the core's own value, so it cannot disagree
      with the workflow rail
TESTS: test_decision.py (30) - the empty case as guidance rather than an empty
       decision, a supported finding with no uncertainty, a partially
       supported finding carrying its failing checks verbatim from the verdict,
       a refused finding as an open item naming the hard dimension that failed,
       the awaiting-validation reason, the purpose, oldest-first ordering,
       loop-closed agreeing with /progress, the verdict readable without
       re-validating, the 404 for a never-validated finding and for another
       case's, reading changes nothing across repeated reads, re-validation
       keeping one row, the delete leaving no trace, the duplicate carrying
       both, the implications' round trip, trimming, the three 400 shapes and
       the empty-list clear, the unit rules on a non-list, the two new timeline
       events and their counts, the export carrying both sections, the round
       trip restoring both, an older package degrading rather than failing, the
       AT-43 measurement over two findings, and the v12 -> v13 upgrade plus the
       fresh store. CaseWorkspace.test.tsx (+10) - the panel in the work zone,
       the question and purpose, a validated finding with its caveat and no
       score anywhere, the failing checks as the uncertainty, the open claims
       and their reasons, the guidance before a closed loop, a failed read
       reported, the implications written and confirmed saved, a failed save
       reported with the server's sentence, and the export downloaded as a
       named file.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (548);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (28/28); `server/.venv/bin/python
              verification/golden/verify_golden.py` green (21/21 reference and
              workflow); `server/.venv/bin/python verification/refine/verify_refine.py`
              green (AT-04's four thresholds); `cd web && npm test && npm run
              build` green (116, build ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; schema v12 -> v13.
```

TASK: P8-DECISION-008 - the decision view
ID: P8-DECISION-008
PRIORITY: high
STATUS: DONE
SUMMARY: the loop has an exit. A validated finding used to be the last thing
         the product did with itself: the verdict was computed, shown and
         discarded, only the status surviving on the finding, and nothing closed
         over what the loop had established. Now the verdict is kept - all nine
         checks, not only the status - and the decision view reads it without
         re-running a single query. The view answers the question, the findings
         validation stood behind with their caveats and the checks that did not
         pass (a sentence each, never a score, per UX 44), the claims still open
         with the reason each is unresolved, and the implications the analyst
         writes - the view's only write, and the one thing in it a human
         authors, because a tool that drafts the action to take is a tool
         making the decision. The loop's closure is the core's own value, read
         from workflow.case_progress rather than restated, so the decision
         cannot say the loop is open while the rail says it is closed. The
         decision travels: the export carries the verdicts and the implications
         and the round trip restores both with fresh ids, the duplicate carries
         them, the delete removes them, and the timeline records the validation
         and the decision as their own events. The shell gained the panel and,
         with it, the case's export - which existed as an endpoint and had no
         surface in the product at all. Two bugs the work surfaced, both fixed
         with their own tests: the timeline asserted its event list exactly, so
         the two new kinds needed the assertions that name them, and the test
         file's decision describe sits outside the CaseWorkspace describe, so
         the plan and run read rejections it inherited by accident of the
         previous test's persistence are now its own beforeEach - a fragility
         the refinement describe beside it still has and this task did not
         touch.


### P8-CAUSAL-004 contract

```
TASK ID: P8-CAUSAL-004
MILESTONE: P8 Analytical Contract
CAPABILITY: Validation (the causal-language guard)
GOAL: an unsupported causal claim is not just commented on, it is *guarded*.
      P8-VALID-003 shipped AT-18's weakest form on purpose: a 14-phrase
      substring match over the finding's statement that raises a soft concern
      and yields `partially_supported`. That names the gap; it never refuses
      anything, and the concern can be read as a footnote rather than a
      verdict. AT-18's actual thresholds are a measurement contract - across
      50 cases, >= 95% of unsupported causal claims are flagged, >= 95%
      distinguish association from causation, and **0** cases convert an
      unsupported association into a validated causal finding. The last clause
      is the one the current check does not hold: a finding that says "spend
      drives signups" over six correlating rows can still be accepted and
      reported as `supported` once the other eight dimensions are clean,
      because causality is a soft concern. This task makes the guard a
      gate on the verdict and ships the 50-case corpus that measures it.
CONTEXT: the gap analysis (G5) said EVALUATE's claim axis flags causal
         language; it does not - that axis tests *specificity* (a direction or
         a magnitude), never causation, so there is no existing machinery to
         reuse. The only causal detector is `check_causality` itself. The
         verdict vocabulary P8-VALID-003 formalised is what this guard acts on,
         and the context object P8-CONTEXT-001 built is what distinguishes a
         claim the case *can* support from one it cannot: a finding that
         asserts causation over an observational comparison is unsupported,
         while one over a documented intervention (a launch date, an A/B test,
         a change recorded in the case's constraints) is a different claim.
         Measuring is the other half of AT-18 - the corpus is the artefact the
         threshold is computed over, and it is deliberately data rather than
         assertions so P8-GOLDEN-005 can fold it into the golden suite.
INPUTS: the finding's statement and interpretation, the case's context
        (purpose, hypotheses, constraints - the last is where an intervention
        is recorded), the run's SQL, and the profile. Nothing is executed and
        nothing is stored: the guard is a pure function of objects already on
        disk, same rule as every other check.
RELEVANT FILES: server/app/causality.py (new - the detector, the hedging and
                intervention logic, the corpus and the measurement),
                server/app/validation.py (check_causality calls it; the
                verdict rule changes from a concern to a gate),
                server/app/main.py (validate_finding passes the context),
                server/tests/test_causality.py (new - the corpus as data, the
                measurement over it, the intervention and hedging paths),
                server/tests/test_validation.py (the verdict's new behaviour),
                web/src/CaseWorkspace.tsx (a guarded finding renders as a
                refusal with the sentence to fix, not a warning),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `server/app/causality.py` (new):
      * A detector wider than the substring list: causal verbs and connectives
        ("drives", "causes", "leads to", "results in", "because of", "due to",
        "so", "therefore", "thus", "hence", "is why", "the reason", "brings
        about", "generates"), matched as word boundaries on normalised text so
        "causes" does not fire inside "because".
      * Hedging: a modal or qualifier immediately before the causal phrase
        ("may drive", "could lead to", "might affect", "appears to influence",
        "seems to cause") is an *associative* claim wearing causal words - the
        hedge is the author stating the limitation themselves, so it does not
        trip the guard. An unhedged phrase does.
      * Negation: "does not drive", "no evidence that X causes Y" asserts the
        absence of causation, which is the guard's own conclusion; it must not
        be flagged as a violation.
      * An intervention basis: the case's context records a change - a launch
        date, an experiment, an A/B test, a policy change in the constraints or
        the hypotheses - and the SQL compares across it (a before/after window
        over a temporal column, or a control comparison). A causal claim over
        an intervention is supported, and the guard says which intervention it
        read rather than refusing everything causal by default. Without a
        recorded intervention, an observational comparison supports
        association only.
      * A 50-case corpus as data - 25 unsupported causal claims, 15
        associative claims that must not be flagged, 10 hedged or negated
        claims - each with its expected verdict, drawn from the phrasings a
        finding actually carries rather than synthetic one-liners. The
        measurement computes the three AT-18 numbers from the corpus.
  - `check_causality` becomes a gate rather than a comment: an unsupported
    causal claim is a hard failure for the verdict, so the status is
    `insufficient_evidence` (the claim outruns the evidence, which is what
    that verdict means) rather than `partially_supported`. The three hard
    dimensions become four. A hedged or associative statement stays clean, and
    an intervention-backed claim passes with its basis named.
  - `validate_finding` passes the case's context to the causality check, so
    the intervention basis is read from the object the analyst already edits
    rather than from a new field.
  - The shell renders a guarded finding as a refusal with the sentence the
    analyst must change, not as a yellow warning beside a green verdict; the
    verdict is the message.
NON-GOALS: the golden suite's other measurements (P8-GOLDEN-005 - this ships
           the causal corpus, that one ships the workflow-completion rate and
           the analytical reference values, and may fold this corpus in);
           detecting confounding or deriving a causal graph (the guard is
           about language and method shape, not about estimating effects);
           causal discovery over the data itself; refusing the write - the
           finding is still stored, it is the *verdict* that refuses.
CONSTRAINTS: green only. The guard is deterministic and offline - no LLM call,
             no new scan, no new schema. The corpus lives in the repository and
             the measurement runs in the suite, so AT-18's threshold is
             asserted on every run rather than quoted.
ACCEPTANCE CRITERIA:
- [x] an unhedged causal claim over an observational comparison yields
      `insufficient_evidence`, not `supported`
- [x] a hedged ("may drive", "could lead to") or negated ("does not cause")
      claim is not flagged, and the corpus's false-positive rate shows it
- [x] a causal claim over an intervention recorded in the case's context is
      supported, and the detail names the intervention it read
- [x] the 50-case corpus is data in the repository, and the measurement over
      it reports >= 95% detection, >= 95% association/causation
      discrimination and 0 conversions, asserted in the suite
- [x] the guard costs no execution and no schema change
- [x] the shell shows a guarded finding as a refusal naming the sentence to
      fix, not a warning beside a pass
TESTS: test_causality.py - the corpus as data with its measurement (the three
       AT-18 numbers computed, not hardcoded), one test per detector path
       (hedging, negation, intervention, word-boundary matching), the verdict's
       new gate behaviour through validate_finding; test_validation.py's
       causality tests updated to the new verdict; web test for the refusal's
       rendering.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11 and
              the hard dimensions become four.
```

TASK: P8-CAUSAL-004 - the causal-language guard
ID: P8-CAUSAL-004
PRIORITY: high
STATUS: DONE
SUMMARY: an unsupported causal claim is guarded, not merely commented on. Until
         this task the causality check raised a *soft concern* - a finding that
         said "spend drives signups" over six correlating rows could still be
         reported `supported` once the other eight dimensions were clean, and
         AT-18's zero-conversion clause was not held. New
         `server/app/causality.py` makes three judgements: an unhedged causal
         verb over an observational comparison is unsupported and gates the
         verdict (`insufficient_evidence`, causality now the fourth hard
         dimension); a hedge ("may drive") or a negation ("does not cause") is
         the author stating the limitation themselves and passes; and an
         intervention the case's context records *and the SQL compares across*
         earns causation, naming the intervention it read. The branch that
         matters most: an intervention the case merely mentions but the query
         never compares across still fails - mentioning is not using. The
         corpus is 50 cases held as data (20 unsupported, 12 associative, 8
         hedged, 10 intervention-backed), and the measurement computes AT-18's
         three numbers over it on every run: 100% detection, 100%
         discrimination, 0 conversions. Two detector bugs the corpus found
         rather than assumed: normalisation strips the slash so "a/b test"
         arrived as "a b test" and the intervention pattern missed it, and the
         negation window had to widen from 3 to 5 words to read "no evidence
         that ... caused". The guard costs no execution and no schema. The
         shell renders a guarded finding as a refusal naming the sentence to
         fix. One limitation recorded in the module rather than papered over: a
         causal word used as a noun ("the causes column") fires, because
         word-boundary matching cannot tell a noun from a verb.



### P8-QUALITY-002 contract

```
TASK ID: P8-QUALITY-002
MILESTONE: P8 Analytical Contract
CAPABILITY: Data Layer (quality beyond missingness)
GOAL: a profile states what the data *cannot* support, before the analyst
      spends a question on it. The profiler finds missing values and duplicate
      rows today (2 of the PRD's 7 defect classes, AT-08); it does not detect
      invalid types, inconsistent categories, date gaps, extreme values or
      insufficient coverage - and these are the defects that make a *correct*
      calculation answer the *wrong* question. Each detected issue must carry
      an impact sentence (AT-09): not "1 null value(s)" but "Revenue contains
      4.8% missing values; revenue comparisons may be understated." Per the UX
      architecture (section 15) this belongs at the Data stage, *before*
      analysis - today it surfaces only at validation, after a finding exists.
CONTEXT: the profile is deterministic (DEC-001) and is already the object the
         planner and the generator read, so quality detection belongs in the
         same pass rather than a second scan. AT-08's thresholds are a >= 95%
         detection rate and <= 5% false positives on the golden suite, which
         does not exist yet (P8-GOLDEN-005) - so this task ships the detectors
         and the tests that pin each one, and the *measurement* against a
         golden corpus is the later task. The context object (P8-CONTEXT-001)
         is already in place; an impact phrased against a stated purpose is
         better than a generic one, but deriving impact from purpose is
         P8-DECISION-008's territory, so impacts are per-defect-class and
         column-specific here, not case-specific.
INPUTS: a profiled dataset's per-column stats (type, null count, distinct
        count, min/max/avg), its row count and its duplicate count - all
        already computed by profile_csv. The detectors add no new scan of the
        file for the classes the existing aggregates already prove; the classes
        that need more (type violations, category inconsistency, date gaps,
        extremes) compute from the same stats plus one targeted query each,
        kept cheap because a profile already costs one scan.
RELEVANT FILES: server/app/analysis.py (the detectors and the quality list),
                server/app/db.py (migration 11, the profile's quality column),
                server/app/models.py (QualityIssue, Profile carries the list),
                server/app/main.py (persist and return the list; the validate
                endpoint's missing-data check reads the derived impact),
                web/src/api.ts, web/src/CaseWorkspace.tsx (the Data-stage
                panel renders the list with its impact sentences),
                web/src/CaseWorkspace.test.tsx,
                server/tests/test_quality.py, ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - Five new defect detectors alongside the two that exist (missing values,
    duplicate rows):
      * invalid_types - a column the profiler typed `other` that reads as
        numeric for most rows but not all, or a date-shaped column holding
        unparsable values. Reported per column with the count and the failing
        examples.
      * inconsistent_categories - a low-cardinality `other` column whose
        distinct values differ only by case or whitespace ("north" vs "North"),
        which silently splits a GROUP BY.
      * date_gaps - a temporal column whose values are not contiguous at the
        granularity the rest of the series implies, so a "same period last
        year" comparison looks at different windows.
      * extreme_values - a numeric column whose max or min is many standard
        deviations out, which skews every average the generator proposes.
      * insufficient_coverage - the dataset is too small for the question's
        implied comparison (a two-row dataset cannot support a trend), or a
        category column is dominated by one value.
    Each returns a structured issue: class, column, severity (high/medium/low),
    an observed sentence and an impact sentence. An issue is only ever raised
    on evidence the profile itself computed - never on a heuristic that could
    fire on clean data, which is how the 5% false-positive budget is held.
  - The profile carries the list: a `quality` key on profile_csv's result and
    on the stored Profile. Persisted in the profiles table as JSON
    (migration 11), so a reopened case shows the same warnings without
    reprofiling.
  - The Data-stage panel renders each issue's observed and impact sentences
    inline under the dataset, with the duplicate and null counts it already
    shows - not behind a tab, because the UX document's rule is that quality
    is visible *before* analysis. A dataset with no issues says so plainly
    rather than rendering nothing.
  - The validation endpoint's missing-data check derives its detail from the
    same impact sentence when the profile has one, so the finding's audit and
    the Data stage cannot drift apart.
NON-GOALS: the 9-dimension validation expansion (P8-VALID-003 - this adds the
           quality *detection*, that consumes it as one of the nine axes); the
           causal-language guard (P8-CAUSAL-004); the golden suite that
           *measures* the 95%/5% budgets (P8-GOLDEN-005 - this ships the
           detectors it will measure); the orientation spine that places these
           in a per-stage rail (P8-SHELL-006); LLM-written impacts (the
           sentences are templated from the profile's own numbers and are
           deterministic, by DEC-001).
CONSTRAINTS: green only. The detectors are pure functions of the profile plus
             at most one bounded query each, deterministic and offline, so a
             profile costs what it costs today plus the targeted queries. The
             schema climbs to 11 and a v10 store opens, upgrades and keeps
             every row.
ACCEPTANCE CRITERIA:
- [x] each of the 7 PRD defect classes has a fixture where the detector raises
      the issue, and the issue carries both an observed and an impact sentence
- [x] a clean dataset (no nulls, no duplicates, consistent categories, no
      extremes) raises no issues - the false-positive guard, asserted
- [x] the quality list persists: profile, close the case, reopen, the list is
      the same without reprofiling
- [x] the Data-stage panel renders the impact sentence for a dataset carrying
      an issue, and states plainly when a dataset is clean
- [x] a store from v10 opens, upgrades to v11 and keeps every row
- [x] validation's missing-data detail uses the impact sentence when present
TESTS: test_quality.py - one raising test per defect class (7), one
       clean-dataset test, persistence across reopen, the v10->v11 migration;
       web tests for the panel's rendering of an issue and of a clean dataset.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task and the raised schema version;
              the store is at v11.
```

TASK: P8-QUALITY-002 - quality detection beyond missingness
ID: P8-QUALITY-002
PRIORITY: high
STATUS: DONE
SUMMARY: a profile now states what the data *cannot* support. Seven defect
         classes (AT-08) each carry an observed fact and an analytical impact
         sentence (AT-09), computed in the profiler's own pass and shown at the
         Data stage, before analysis, rather than only after a finding exists.
         The two classes that existed as bare counts - missing values and
         duplicate rows - gained impacts; five are new: invalid types (a column
         typed `other` that is mostly numeric or temporal but not entirely),
         inconsistent categories (case/whitespace variants that split a GROUP
         BY), date gaps (a hole in an otherwise regular series), extreme values
         (a value dwarfing its neighbour, compared against the next value
         rather than a mean the outlier itself moved) and insufficient coverage
         (too few rows, or a category so dominant a group-by is about one
         group). Every detector raises only on evidence the profile measured,
         never on a guess about what the data should look like, which is what
         holds the 5% false-positive budget before the golden suite that will
         measure it exists. The list persists (schema v11), travels with an
         exported case and survives a duplicate; the validation endpoint's
         missing-data check now reads the same impact sentence the Data stage
         shows, so the audit and the panel cannot drift apart.


### P8-CONTEXT-001 contract

```
TASK ID: P8-CONTEXT-001
MILESTONE: P8 Analytical Contract
CAPABILITY: Data Layer (the case's context object)
GOAL: a case carries the analyst's intent, not just a question string. Today a
      case is `question + dataset`; the PRD (AT-03) requires purpose, primary
      question, sub-questions and hypotheses to be captured, edited and
      restored, and the UX architecture (section 13) treats context as a
      first-class analytical object - business objective, time period,
      relevant changes, known constraints - that the planner and the assistant
      reason over. The generated plan already carries sub-questions and
      hypotheses, but they are the engine's, not the analyst's, they are not
      editable, and P7-WALK-001 recorded that they are persisted and never
      rendered. This task is the dependency for P8-REFINE-007 (refinement edits
      this object), P8-DECISION-008 (the decision view closes over it) and the
      case overview in P8-SHELL-006.
CONTEXT: AT-03's threshold is persistence across edit and reopen; AT-10 wants
         the plan to hold an objective, sub-questions, hypotheses and methods;
         UX 13 wants context available to the AI. Nothing in the loop currently
         reads intent - the planner takes `(question, profile)` and the
         assistant's facts carry no context - so this adds the object and wires
         the two readers that already exist.
INPUTS: a case's context: a free-text purpose, a list of sub-questions, a list
        of hypotheses to test, and a list of known constraints. The primary
        question stays on the case row (it is already editable and persisted)
        rather than being duplicated.
RELEVANT FILES: server/app/db.py (migration 10, the contexts table),
                server/app/models.py (CaseContext, ContextUpdate),
                server/app/main.py (GET/PUT /cases/{id}/context, plan wiring),
                server/app/planner.py (reads context, records a context_basis),
                server/app/assistant.py (context in facts, one citation kind),
                server/app/exporter.py (the context section, both directions),
                web/src/ContextPanel.tsx, web/src/CaseWorkspace.tsx,
                web/src/api.ts, web/src/CaseWorkspace.test.tsx,
                server/tests/test_context.py, ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - A `contexts` table, one row per case (case_id PRIMARY KEY), holding purpose
    and three JSON lists: sub_questions, hypotheses, constraints. Migration 10,
    guarded so it is a no-op on a store that already has it and resumable after
    a crashed upgrade - the standard every other migration is held to.
  - `GET /cases/{case_id}/context` answers the context, defaulting to an empty
    one for a case that never set it, so the shell's form always has something
    to render; `PUT /cases/{case_id}/context` replaces it wholesale (idempotent
    form semantics). A 404 for an unknown case; a 400 for a malformed list -
    never a silent drop, the discipline AT-20 applies to our own inputs.
  - The planner accepts an optional context and lets the analyst's intent
    outrank the derivation: their sub-questions and hypotheses come first, the
    purpose stands in for a thin objective. The plan records a `context_basis`
    list naming the fields it actually read, so a reader can tell a plan built
    from stated intent from one built from a profile alone.
  - The assistant's facts carry the context, and one deterministic branch
    answers a question about the case's purpose or its hypotheses citing a
    `context:` ground - the same shape as the column and dataset branches.
  - Export carries the context section and import restores it; an older package
    without one degrades to an empty context rather than erroring.
NON-GOALS: AI question refinement (P8-REFINE-007 - this object is what that
           task edits); rendering the plan's own contents (P8-SHELL-006, which
           is the panel for everything the core computes and the shell does not
           show); quality detection (P8-QUALITY-002).
CONSTRAINTS: green only - nothing committed while red, and the schema version
             climbs to 10 with the migration recorded in the audit trail.
ACCEPTANCE CRITERIA:
- [x] entered purpose, sub-questions, hypotheses and constraints persist across
      a save, close and reopen
- [x] edited text persists and reopening restores the latest version
- [x] a plan generated for a case with context records which fields it read in
      `context_basis`, and the analyst's sub-questions outrank the derived ones
- [x] 3 sub-questions and 2 hypotheses survive an export -> import round trip
- [x] a malformed context (non-list, empty item, overlong text) answers 400 and
      changes nothing
- [x] a store from v9 opens, upgrades to v10 and keeps every row it had
TESTS: test_context.py - persistence and reopen, edit, the 400 paths, the
       migration from v9, the round trip; planner tests for context precedence
       and basis recording; assistant tests for the new citation kind; web
       tests for the panel's edit and remove paths.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task and the raised schema version;
              the store is at v10.
```

TASK: P8-CONTEXT-001 - the case's context object
ID: P8-CONTEXT-001
PRIORITY: high
STATUS: DONE
SUMMARY: a case gains structured, editable intent - purpose, sub-questions,
         hypotheses, known constraints - persisted in a new table (migration
         10), edited through a GET/PUT pair, read by the planner so a plan is
         built from stated intent rather than a question string plus a
         profile, read by the assistant so a question about purpose cites it,
         and carried by export in both directions. The primary question stays
         on the case row where it already lives.


### P7-CSV-002 contract

```
TASK: P7-CSV-002 - a CSV with a stray trailing comma no longer collapses to one column
ID: P7-CSV-002
MILESTONE: P7 Product Modes
CAPABILITY: Data Layer (reliability)
GOAL: an analyst's CSV is accepted as it arrives. A row carrying more fields
      than the header - a stray trailing comma, as a spreadsheet export or a
      hand-edit produces - derails read_csv_auto's delimiter guess, and the
      whole file then reads as one column holding each raw line. The profile
      answers `columns: ['order_id,quarter,region,revenue']` and describes
      nothing, and the SQL the analyst then writes from those columns fails on
      the same file it was derived from. The file is not corrupt; one cell is.
CONTEXT: found while seeding the shipped app with worked cases - the first
         draft of a fixture carried `106,2024q3,west,,` and the profile
         collapsed to a single column. Bisected exactly: a trailing empty that
         matches the header's width (`106,2024q3,west,`) is a honest null and
         always worked; the collapse needs a row *wider* than the header, and
         only when more rows follow it. Neither the profiler nor the run path
         was at fault alone: both build the same reader, so a profile that
         recovered while its runs collapsed would describe columns the SQL
         cannot see.
INPUTS: a CSV whose header claims four fields and whose third row carries five
        (the last two empty), followed by further rows; read_csv_auto alone
        answers one column for it, `ignore_errors=true` answers four with
        every row present and the stray field gone, and `null_padding=true`
        answers five - a synthetic column invented for the stray field.
RELEVANT FILES: server/app/analysis.py (the recovery, and its four call sites),
                server/tests/test_analysis.py (+3), server/tests/test_profiles.py
                (+1), ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `_sniffed_reader_for` chooses the reader for a file: the format's own
    reader, unless the header's comma count claims more columns than sniffing
    found, in which case it re-sniffs with `ignore_errors=true` and takes that
    when it widens the description. Both the profile and the run path go
    through it - `_bind_dataset`, `_bind_datasets`, `profile_csv` and
    `_duplicate_row_count` - so a file reads the same way everywhere.
  - The retry is conditional on purpose. `ignore_errors` on a well-formed file
    would turn a genuine conversion error into a silent null, so it is earned
    by a collapse, never applied by default; a recovery that does not widen
    the description is discarded, so a quoted header containing a comma costs
    one sniff and changes nothing.
  - No contract changed; no endpoint changed; no new feature.
NON-GOALS: repairing the data - the stray field becomes a null and the profile
           reports it as one, which is what the missing-data check exists to
           catch. Quoted fields containing commas are not re-parsed in Python;
           DuckDB's own header is authoritative once the recovery widens it.
CONSTRAINTS: green only - nothing committed while red, and each new test was
             proven to fail without the fix.
ACCEPTANCE CRITERIA:
- [x] a CSV with a stray trailing comma profiles as the header's columns, with
      every row counted and the malformed cell reported as a null
- [x] SQL written against those columns runs on the same file and returns the
      same columns - profile and run read alike
- [x] a well-formed CSV and a parquet file keep the strict reader, so a
      genuine conversion error is still an error and never a silent null
- [x] 388 server tests pass and all 25 real-server e2e steps pass
TESTS: 4 added - test_analysis.py gains the reader-selection unit tests (the
       clean file and the parquet keep their reader, the collapsed file gains
       ignore_errors, and profile_csv itself reads four columns from the
       malformed file), and test_profiles.py drives the same file through the
       attach -> profile -> run path over HTTP. All four fail on the pre-fix
       code.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` -> 388 passed in 180s;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` ->
              ALL STEPS PASS.
STATE UPDATE: TASKS/CURRENT_STATE gain the fix; the three seeded cases and the
              sidecar rebuild are recorded in HANDOFF.
LESSON: the malformed shape is not exotic - it is one keystroke past a null,
        and the honest null next to it works perfectly, so the failure looked
        like a fixture bug for a while before it was a product bug. The tell
        was that the *recovery* options disagree: null_padding widens the row
        to cover the mistake and ignore_errors narrows the mistake to a null.
        Only one of those keeps the table the analyst uploaded.
```

TASK: P7-CSV-002 - a CSV with a stray trailing comma no longer collapses to one column
ID: P7-CSV-002
PRIORITY: medium
STATUS: DONE
SUMMARY: read_csv_auto's delimiter guess dies on a row wider than its header,
         and the whole file then reads as a single column of raw lines - the
         profile describes nothing and the SQL derived from it cannot run.
         `_sniffed_reader_for` compares the sniffed width against the header's
         own comma count and re-sniffs with ignore_errors when sniffing
         collapsed, keeping every row and dropping only the stray field to a
         null. Both profiling and the run path go through it, so a file reads
         the same way everywhere. The retry is earned by a collapse, never on
         by default, because ignore_errors on a clean file would silence real
         conversion errors.

### P7-CORS-001 contract

```
TASK ID: P7-CORS-001
MILESTONE: P7 Product Modes
CAPABILITY: Reliability (the packaged desktop app talking to its own core)
GOAL: The shipped .app opened to "Failed to load cases: Failed to fetch", and
      its New Case form was unreachable behind that. Every fetch the packaged
      frontend makes is cross-origin - the webview is served from Tauri's own
      scheme, the core from 127.0.0.1:8123 - and the core answered with no
      `Access-Control-Allow-Origin`, so the browser discarded each response
      before the app saw it. The core's own log showed a clean 200 for the very
      request the shell reported as failed, which is why no test caught it.
CONTEXT: every in-process and real-server verification drives the core from an
         origin it does not gate. Starlette's TestClient does not enforce CORS,
         and the e2e script talks to the core directly. The browser is the only
         gate, and nothing in the repo drove a browser at the core until a human
         opened the app.
INPUTS: the packaged .app as built; a real headless Chrome over the DevTools
        protocol, serving the shipped bundle from a foreign origin to reproduce
        the browser's view of the fetch.
RELEVANT FILES: server/app/main.py (the CORS middleware and its allowlist),
                server/tests/test_cors.py (new),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `server/app/main.py` gains an `ALLOWED_ORIGINS` frozenset and a CORS
    middleware: an origin on the list is echoed back with `Vary: Origin`, an
    OPTIONS preflight is answered 204 with the allowed methods and the
    content-type header, and any other origin gets neither - the response still
    succeeds, because CORS is the browser's gate and not the server's, but the
    browser will not release it.
  - The allowlist is narrow and deliberately has no wildcard: the core is a
    local process holding an analyst's cases and chat history, and `*` would let
    a webpage the user merely visits read them. Tauri's own two origins plus the
    dev-server ports are every origin this frontend legitimately has.
NON-GOALS: changing the frontend (it was correct - it fetched the right URL and
           reported the browser's error honestly), changing the shell's origin
           handling, allowing credentials, broadening the allowlist to user
           configuration.
CONSTRAINTS: no new dependency (the middleware is a plain FastAPI middleware,
             not starlette's CORSMiddleware, so the preflight answers 204 rather
             than 405 and nothing else changes); the core stays unreadable to
             origins it does not know.
ACCEPTANCE CRITERIA:
- [x] a real browser, served the shipped bundle from a foreign origin, sees the
      fetch refused; served from an allowed origin, sees it succeed
- [x] the shell's own origin is echoed, a preflight answers 204 with methods and
      headers, and an unknown origin gets no CORS header at all
- [x] 4 new tests in tests/test_cors.py, proven to fail without the fix and pass
      with it
- [x] 384 server tests pass (was 380) and all 25 real-server e2e steps pass
TESTS: tests/test_cors.py - 4 tests. Two were verified against a temporarily
       disabled middleware: the origin-echo and the preflight both fail, so the
       suite cannot go green with the bug present.
VERIFICATION: `server/.venv/bin/python -m pytest` -> 384 passed;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` -> ALL
              STEPS PASS; reproduced in headless Chrome that the same fetch that
              failed before the fix succeeds after it.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF name the CORS gap and the rebuild
              that remains before a release ships it.
```

TASK: P7-CORS-001 - the packaged app could not reach its own core
ID: P7-CORS-001
PRIORITY: high
STATUS: DONE
SUMMARY: The shipped .app opened to a dead screen - "Failed to load cases:
         Failed to fetch" - with the New Case form unreachable behind it. The
         frontend was never at fault and neither was the core: the browser was
         the only thing between them that knew. Tauri serves the bundled
         frontend from its own scheme while the core answers on
         127.0.0.1:8123, so every fetch the app makes is cross-origin, and the
         core answered with no `Access-Control-Allow-Origin`. The browser
         discarded each response - while the core's own log recorded a clean
         200 for the identical request.

Reproduced twice before the fix, in a real headless Chrome over the DevTools
protocol: serving the shipped bundle from a foreign origin, the fetch failed
with exactly the message the user saw; the core logged 200. After the fix the
same fetch returns the case list and the page renders it.

`server/app/main.py` gains `ALLOWED_ORIGINS` and a CORS middleware. An origin on
the list is echoed with `Vary: Origin`; an OPTIONS preflight is answered 204
with the allowed methods and the content-type header - written as a plain
middleware rather than starlette's CORSMiddleware because no endpoint handles
OPTIONS, and leaving the preflight to Starlette answers 405 and the real
request is never sent. Anything not on the list gets neither header: the
response still succeeds, since CORS is the browser's gate and not the server's,
but the browser will not release it. No wildcard - the core holds an analyst's
cases and chat history, and `*` would let a webpage the user merely visits read
them.

LESSON: this is the sharpest illustration yet of the gap P7-WALK-001 named.
Every automated artifact in this repo drives the core from a position CORS does
not gate - TestClient does not enforce it, and the e2e script talks to the core
directly. The browser is the only gate, and nothing in the repo drove a browser
at the core. The core logging 200 while the app reported failure was not a
contradiction; it was the whole bug, and only a human opening the .app could
see it. The desktop suite's 22 Rust tests verified the shell could start the
core and that the port was theirs - and stopped exactly one step short of
asking whether the webview could read an answer.

### P2-DATA-006 contract

```
TASK ID: P2-DATA-006
MILESTONE: P2 MVP
CAPABILITY: Data Layer (breadth)
GOAL: Accept Parquet and Excel in addition to CSV.

CONTEXT: CSV attach works; profile_csv handles any tabular file DuckDB reads.
INPUTS: multipart upload (.csv/.parquet/.xlsx).
RELEVANT FILES: server/app/main.py, models.py, tests/test_datasets.py
REQUIRED CHANGE: accept the two new extensions; store with a format field.
NON-GOALS: profiling depth (P2-DATA-007), schema detection heuristics, UI.
CONSTRAINTS: read via DuckDB throughout - one engine, one path.
ACCEPTANCE CRITERIA:
- [x] .parquet and .xlsx attach and are stored
- [x] each profiles correctly (rows/columns) via the existing profile endpoint
- [x] unsupported extension rejected with 400
TESTS: golden parquet, golden xlsx, unsupported type.
VERIFICATION: pytest + in-process round-trip.
STATE UPDATE: mark P2-DATA-006 done on pass.
```

### P2-DATA-007 contract

```
TASK ID: P2-DATA-007
MILESTONE: P2 MVP
CAPABILITY: Data Layer (depth)
GOAL: Deepen the profile so it carries what an analyst (and later the AI planner)
      needs before writing a query.

CONTEXT: csv/parquet/xlsx all attach and profile (rows/columns/null counts).
         The profile is the input to the AI planning step, so it has to describe
         the data, not just count rows.
INPUTS: an attached, profiled dataset (any supported format).
RELEVANT FILES: server/app/analysis.py, models.py, main.py, db.py,
                tests/test_profiles.py
REQUIRED CHANGE: extend the profile with
  - per column: inferred DuckDB type, null count, null percentage, distinct count
  - per numeric column: min, max, average
  - per dataset: duplicate row count (total rows minus distinct rows)
NON-GOALS: no visualization, no AI interpretation, no UI, no heuristic schema
           repair, no per-value histograms.
CONSTRAINTS: read via DuckDB throughout - one engine, one path; every new
             stat must survive across formats (csv/parquet/xlsx); the existing
             validation null_count sum must keep working unchanged.
ACCEPTANCE CRITERIA:
- [x] every column reports type, null_count, null_percentage, distinct_count
- [x] numeric columns report min/max/avg
- [x] duplicate row count is reported and correct
- [x] empty (header-only) datasets profile without error
- [x] existing profiles and the validation gate still pass
TESTS: numeric stats; type inference; distinct counts; duplicate rows;
       header-only dataset; full regression suite.
VERIFICATION: pytest + in-process round-trip.
STATE UPDATE: mark P2-DATA-007 done on pass.
```

### P3-SEC-001 contract

```
TASK ID: P3-SEC-001
MILESTONE: P3 V1
CAPABILITY: Analysis Workspace (hardening)
GOAL: Move Python execution out of the API process and under an OS-level
      sandbox.

CONTEXT: P2-ANALYSIS-008 shipped an in-process soft sandbox (import allowlist,
         restricted builtins, dunder-hardened handle, CPU/wall-clock limits).
         It stops accidental damage, not a determined escape, and a crash or
         unbounded allocation in user code hits the API process itself.
INPUTS: an attached dataset and a user Python script (unchanged API).
RELEVANT FILES: server/app/python_exec.py, server/app/python_worker.py (NEW),
                server/app/main.py (unchanged), server/tests/test_python_hard_sandbox.py (NEW)
REQUIRED CHANGE: execute user code in a child process; on macOS wrap it with
         sandbox-exec under a profile that denies every filesystem write
         outside the run's scratch directory and denies all network access;
         scrub the child environment so API-process secrets never reach it;
         bound wall clock at the process-group level (kill the tree, not just
         the wrapper) and keep the in-process guards as defense in depth.
NON-GOALS: Linux landlock / Windows job-object sandboxes (the separate process
           plus inner guards remain the floor on those hosts); address-space
           caps (macOS rejects useful RLIMIT_AS values); validation of Python
           runs by re-execution.
CONSTRAINTS: the /runs/python contract is unchanged - same request, same
             response, same 400 messages; existing tests must pass unmodified.
ACCEPTANCE CRITERIA:
- [x] user Python runs in a process separate from the API
- [x] on macOS the child is under sandbox-exec; a write outside scratch and a
      network connection are denied by the kernel
- [x] an unbounded loop ends at the time limit and the API answers 400
- [x] a worker that dies is reported as 400, never raised into the API
- [x] API-process environment secrets are absent from the child environment
- [x] full server suite and the P2 gate still pass
TESTS: seatbelt enforcement probe (scratch write allowed, outside write and
       network denied), child env scrub, process-group kill, runaway loop,
       dead worker, contract violation.
VERIFICATION: pytest + verification/p2/verify_p2.py regression.
STATE UPDATE: mark P3-SEC-001 done on pass.
```

### P3-CHART-002 contract

```
TASK ID: P3-CHART-002
MILESTONE: P3 V1
CAPABILITY: Analysis Workspace (raster charts)
GOAL: Render charts as PNG behind the same interface, for consumers that need
      a bitmap rather than vector markup.

CONTEXT: P2-ANALYSIS-009 renders deterministic, dependency-free SVG. SVG stays
         the default; raster is an opt-in format on the same endpoint.
INPUTS: a persisted run result plus chart parameters, now including `format`.
RELEVANT FILES: server/app/charts.py, server/app/main.py, server/app/models.py,
                server/app/exporter.py, server/pyproject.toml,
                server/tests/test_charts_raster.py (NEW)
REQUIRED CHANGE: split render_chart into a shared ChartModel (one geometry, one
         category order, one bar geometry) plus two backends; add the PNG
         backend with Pillow, drawn at 2x and LANCZOS-downscaled; thread
         `format` through ChartCreate, the create endpoint, the artifact
         extension, and the served media type (sniffed from stored bytes so old
         rows stay correct); carry binary artifacts through the export/import
         package as base64 with an explicit format (legacy `svg` text field
         kept for older consumers); declare the `charts` optional dependency.
NON-GOALS: new chart kinds, interactive charts, font/vector improvements, a
           Linux-only raster path.
CONSTRAINTS: the SVG path stays dependency-free and byte-identical to before;
             the PNG path is deterministic (same input -> identical bytes).
ACCEPTANCE CRITERIA:
- [x] `format=png` yields a real, decodable PNG of the requested size
- [x] the same input renders byte-identical PNGs across calls
- [x] bar geometry carries over: taller bars top out higher, bars sit on the
      zero baseline, every category gets a bar on canvas
- [x] multi-series charts draw in more than one series colour
- [x] unknown format and unknown kind are both 400s
- [x] the API stores a .png artifact and serves it as image/png
- [x] export/import round trips PNG bytes losslessly and serves them again
- [x] SVG charts are unchanged; full suite and the P2 gate still pass
TESTS: 9 raster tests - real image, determinism, bar geometry by pixel scan,
       multi-series, rejections, SVG default, PNG and SVG API round trips.
VERIFICATION: pytest (94 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-CHART-002 done on pass.
```

### P3-DATA-003 contract

```
TASK ID: P3-DATA-003
MILESTONE: P3 V1
CAPABILITY: Data Layer (multi-dataset)
GOAL: Let one analysis run join several attached datasets.

CONTEXT: attaching several datasets per case already worked (the datasets table
         is case-scoped); the query layer bound every placeholder to a single
         file, so joins across attached files were impossible.
INPUTS: a case, two or more attached datasets, and one SQL statement with one
        placeholder per dataset.
RELEVANT FILES: server/app/analysis.py, server/app/main.py, server/app/models.py,
                server/app/db.py, server/app/exporter.py,
                server/tests/test_multi_dataset_runs.py (NEW)
REQUIRED CHANGE: run_query_multi binds the k-th placeholder to the k-th dataset
         positionally; new POST /cases/{id}/runs endpoint; runs store
         dataset_ids_json alongside the single dataset_id kept as the primary;
         validation re-runs through the multi path; duplicate remaps the list to
         the copy's own datasets; export/import carries it as a JSON list.
NON-GOALS: cross-case datasets, a join builder UI, multi-dataset Python runs
           (the Python handle stays single-dataset - documented).
CONSTRAINTS: the single-dataset endpoints and their responses are unchanged;
             placeholder count must equal dataset count (a mismatch is a 400,
             never a guess); the read-only gate and row cap apply unchanged.
ACCEPTANCE CRITERIA:
- [x] a join across two attached files returns correct results
- [x] binding is positional - swapping the dataset list changes which file each
      placeholder reads
- [x] placeholder/dataset count mismatch, unknown dataset, and duplicate ids are
      clean 400/404s
- [x] multi runs are read-only and reopen/list with their dataset list
- [x] a finding on a join run validates (reproduces) through the multi path
- [x] duplicating a case repoints the copied run at the copied datasets
- [x] export/import round trips a join run with its dataset list
- [x] full suite and the P2 gate still pass
TESTS: 10 tests - join correctness, positional binding, count mismatch, unknown
       dataset, uniqueness, read-only, reopen/list, finding validation,
       duplicate remap, export round trip.
VERIFICATION: pytest (104 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-DATA-003 done on pass.
```

### P3-FLOW-004 contract

```
TASK ID: P3-FLOW-004
MILESTONE: P3 V1
CAPABILITY: Analysis workflow (guided)
GOAL: Tell the analyst where they are in the loop and what to do next.

CONTEXT: every stage of the core loop already had an endpoint, but nothing
         reported which stage a case was in, so the UI could not guide and the
         analyst had to hold the sequence in their head.
INPUTS: a case id.
RELEVANT FILES: server/app/workflow.py (NEW), server/app/main.py, models.py,
                server/tests/test_workflow.py (NEW)
REQUIRED CHANGE: derive the stage from the artifacts a case actually has
         (datasets, profiles, plans, runs, charts, findings, validated findings)
         rather than storing it; expose GET /cases/{id}/progress returning the
         current stage, the completed stages, the single next action, the
         endpoint that performs it, artifact counts, and whether the trust loop
         has closed.
NON-GOALS: storing stage state (by design), UI, recommendations from the LLM
           (deterministic only - the LLM path waits on DAH_LLM_API_KEY), a
           dataset-delete endpoint (surfaced as a follow-up below).
CONSTRAINTS: no schema change - the stage is a pure function of the data, so it
             can never claim a step the artifacts do not support, and deleting
             an artifact would move a case back without a migration.
ACCEPTANCE CRITERIA:
- [x] a fresh case reports stage=data with the attach action and endpoint
- [x] walking the whole loop ends at stage=validated, loop_closed, no next action
- [x] the profile stage only closes when every attached dataset is profiled
- [x] progress is recomputed per request and never leaks across cases
- [x] unknown case answers 404
- [x] full suite and the P2 gate still pass
TESTS: 5 tests - start state, full-loop advance, partial profiling, per-request
       derivation and case scoping, 404.
VERIFICATION: pytest (109 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-FLOW-004 done on pass.

FOLLOW-UP (not this task): there is no DELETE endpoint for a single dataset, so
nothing can currently walk a case backwards. Adding one (cascade to its runs,
charts and anchored findings, or refuse with 409 while runs exist) is what makes
the derived stage's "moves back" property observable.
```

### P3-ANALYSIS-005 contract

```
TASK ID: P3-ANALYSIS-005
MILESTONE: P3 V1
CAPABILITY: Analysis Workspace (richer EDA)
GOAL: Answer "what should I look at first" without writing a query.

CONTEXT: profiling describes a dataset and runs answer a specific question,
         but the step between them - segmentation, correlation, distribution -
         had no surface, so the analyst re-derived common SQL by hand.
INPUTS: an attached dataset, an op name, and its column parameters.
RELEVANT FILES: server/app/eda.py (NEW), server/app/main.py, models.py,
                server/tests/test_eda.py (NEW)
REQUIRED CHANGE: compile each op to a read-only DuckDB statement and run it
         through the same run_query - one engine, one gate, one row cap; expose
         POST /cases/{id}/datasets/{id}/eda returning the standard result shape.
NON-GOALS: persisting EDA as evidence (a finding must anchor on a query the
           analyst wrote), formal hypothesis tests (need a stats story of their
           own), charts from EDA (the result shape already feeds the chart
           endpoint through a run).
CONSTRAINTS: column names are quoted and refused if they contain a quote;
             unknown op/column and missing parameters are 400s; results are
             read-only and row-capped like any query.
ACCEPTANCE CRITERIA:
- [x] segment reports rows/mean/median/min/max/stddev per category
- [x] correlate reports Pearson r and paired row count
- [x] distribution reports the numeric spread, and falls back to top values for
      a categorical column
- [x] unknown op, unknown column, and missing parameter are clean 400s
- [x] a quote-bearing column name cannot reach the SQL
- [x] full suite and the P2 gate still pass
TESTS: 9 tests - segment, correlate, numeric and categorical distribution, and
       six error cases.
VERIFICATION: pytest (118 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-ANALYSIS-005 done on pass.
```

### P3-EVIDENCE-006 contract

```
TASK ID: P3-EVIDENCE-006
MILESTONE: P3 V1
CAPABILITY: Evidence (richer lineage)
GOAL: Show every claim in a case and what it rests on.

CONTEXT: the single-finding chain (`GET .../findings/{id}/evidence`) answers
         "what backs this claim"; nothing answered the case-level question a
         reviewer asks: which claims exist, what each rests on, and does every
         one trace back to stored data.
INPUTS: a case id.
RELEVANT FILES: server/app/evidence.py (NEW), server/app/main.py, models.py,
                server/tests/test_evidence_graph.py (NEW)
REQUIRED CHANGE: project the case into a graph - nodes for datasets, runs,
         charts, plans and findings; edges for how each was derived
         (anchored_on / queries / rendered_from / planned_from); a per-claim
         trace walking finding -> run -> dataset(s); orphan findings listed
         rather than hidden. Exposed as GET /cases/{id}/evidence-graph.
NON-GOALS: storing the graph (it is a pure projection of the persisted rows),
           visual rendering, cross-case lineage.
CONSTRAINTS: read-only; every edge must connect nodes that exist; a case with
             no artifacts answers 400 rather than returning an empty diagram.
ACCEPTANCE CRITERIA:
- [x] the graph covers every artifact kind with correct counts
- [x] edges describe derivation and all connect real nodes
- [x] a claim's trace reaches the dataset it stands on
- [x] a join run's trace covers every dataset it bound
- [x] a claim anchored on nothing is reported as an orphan with reaches_source
      false, never hidden
- [x] an artifact-free case answers 400; unknown case answers 404
- [x] full suite and the P2 gate still pass
TESTS: 7 tests - coverage, edge relations, single and multi-dataset traces,
       orphan reporting, empty case, 404.
VERIFICATION: pytest (125 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-EVIDENCE-006 done on pass.
```

### P3-CASE-007 contract

```
TASK ID: P3-CASE-007
MILESTONE: P3 V1
CAPABILITY: Analysis Case (reuse)
GOAL: Make a finished investigation reusable: find a case again, see what
      happened in it, and start a new one from its shape.

CONTEXT: P2 proved the loop and P3 widened it, but nothing helps the analyst
         the *second* time through. Cases accumulate with no way to find one,
         no way to see what was done without opening every artifact, and no
         way to start a new case shaped like a previous one.
INPUTS: an existing case (for history and templates); a search term (for
        listing).
RELEVANT FILES: server/app/history.py (NEW), server/app/main.py,
                server/app/models.py, server/app/db.py,
                tests/test_case_history.py (NEW),
                tests/test_case_templates.py (NEW),
                tests/test_cases.py (search)
REQUIRED CHANGE:
  - search: optional `q` on GET /cases, case-insensitive substring over the
    question and the dataset label, with LIKE wildcards in the term treated as
    literals; absent or blank `q` lists everything
  - history: GET /cases/{id}/history - a timeline derived from each artifact's
    own timestamp (datasets, profiles, plans, runs, charts, findings), a
    read-side projection like the evidence graph; a finding's validation status
    rides along as its event detail because validation has no persisted
    timestamp of its own
  - templates: a `templates` table (id, name, question, dataset, created_at)
    created with IF NOT EXISTS so older databases need no migration;
    POST /cases/{id}/template (promote, name defaults to the question),
    GET /templates (newest first), POST /cases/from-template (with optional
    question/dataset overrides), DELETE /templates/{id}
NON-GOALS: template categories or tagging, template versioning, sharing
           templates across installs (export/import already moves whole
           cases), full-text search across artifact bodies (the search covers
           case-level fields only), a history UI.
CONSTRAINTS: history and search are pure reads - no schema change for either,
             so the timeline cannot drift from the persisted rows; templates
             are not case children, so deleting a case leaves its template and
             deleting a template leaves its cases; existing endpoints and their
             responses are unchanged.
ACCEPTANCE CRITERIA:
- [x] `q` filters case-insensitively on question and dataset; a blank or absent
      `q` lists every case
- [x] `%` and `_` in a search term are literals, never wildcards
- [x] the history covers every artifact kind in chronological order and is
      recomputed per request, never leaking across cases
- [x] a just-created case has exactly one event; an unknown case answers 404
- [x] a promoted template keeps question and dataset label only - no data,
      runs or findings are copied
- [x] a templated case starts clean and accepts inline overrides
- [x] a template survives its source case; deleting a template leaves the
      cases it seeded untouched
- [x] full suite and the P2 gate still pass
TESTS: 20 tests - 4 search (question, dataset label, wildcard escaping,
       no-filter paths), 6 history (fresh case, full-loop ordering, event
       details, validation status, case scoping, 404), 10 templates (default
       and explicit name, empty name 400, 404s, newest-first listing, clean
       start, overrides, survives source case, delete with cascades).
VERIFICATION: pytest (145 passed) + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-CASE-007 done on pass.
```

### P3-SHELL-008 contract

```
TASK ID: P3-SHELL-008
MILESTONE: P3 V1
CAPABILITY: Desktop shell
GOAL: DAH becomes a double-clickable app instead of two terminals, without
      changing the frontend or the core.

CONTEXT: P0-P3 built a browser-served UI over a FastAPI core. Everything works,
         but starting it means running a Python server and a vite dev server.
         DEC-001 said the Tauri host would wrap the same React bundle post-MVP;
         this is that step.
INPUTS: the existing web/ React bundle (unchanged), server/ (unchanged),
        a Rust toolchain + npm.
RELEVANT FILES: desktop/ (NEW: package.json, README.md, .gitignore,
                src-tauri/{Cargo.toml,Cargo.lock,build.rs,tauri.conf.json,
                capabilities/default.json,icons/,src/main.rs,src/core_server.rs}),
                server/app/supervisor.py (NEW), server/dah_core_main.py (NEW),
                server/dah-core.spec (NEW), server/build_sidecar.sh (NEW),
                server/tests/test_supervisor.py (NEW),
                server/app/main.py (watchdog start), web/package.json
                (build:desktop + build:desktop:watch), web/vite.config.ts
                (dev port pinned to 5273), .gitignore (web/dist-desktop/,
                server/build/)
REQUIRED CHANGE:
  - host swap only: the shell serves the same React bundle the browser host
    serves, and the bundle keeps talking to the same FastAPI core over HTTP
  - the shell spawns the core (the packaged PyInstaller sidecar when present,
    server/.venv's uvicorn in a dev checkout; DAH_DEV_CORE=1 forces dev),
    waits for GET /health before showing the window, and stops the core when
    the window closes or the app exits
  - the core cannot be orphaned: process-group kill handles the PyInstaller
    bootloader's forked child, and a parent-pid watchdog in the core ends it
    when the shell dies without running any cleanup (a SIGKILL reaches neither
    a destructor nor a Tauri event)
  - per-user data dir (DAH_DATA_DIR/DAH_DB_PATH) so a packaged app keeps its
    cases in app support, not next to the binary
  - the webview loads only the embedded bundle (no remote URL), so the
    capability file grants nothing but core:default
NON-GOALS: signing/notarization (P5), a Windows/Linux build (needs its own
           icon set and sidecar triple), frontend changes, a one-dir
           PyInstaller build (would cut the 40s one-file unpack; deferred
           because it changes how externalBin addresses the binary).
CONSTRAINTS: no frontend or core behaviour changes; the browser host keeps
             working exactly as before; the 85MB sidecar is gitignored and
             never committed.
ACCEPTANCE CRITERIA:
- [x] the packaged app opens a window whose webview renders the real DAH UI,
      with the core answering /health, and closing the window stops the core
- [x] a debug build serves the embedded bundle - no devUrl that can point the
      webview at a port nothing is serving
- [x] SIGKILL of the shell frees port 8123 (the watchdog), so the next launch
      is not left looking dead
- [x] cargo test: 5 unit + 2 e2e (live uvicorn through the resolver, and the
      sidecar path asserting no orphan)
- [x] server suite (155) and web suite (2) unchanged; P2 gate PASS
TESTS: 7 Rust tests - resolution for both hosts, the DAH_DEV_CORE override, the
       health URL, the silent-port gate, a live dev core answering /health, and
       the sidecar stopping without orphaning its forked child. Plus 7 Python
       tests for the supervisor watchdog (two live process tests).
VERIFICATION: cargo test --features e2e; pytest 155 passed; the P2 gate PASS
              with all 18 steps green; manual: window renders, /health 200,
              window-close and SIGKILL both free the port.
STATE UPDATE: mark P3-SHELL-008 done on pass.

### P3-DATA-009 contract

```
TASK ID: P3-DATA-009
MILESTONE: P3 V1
CAPABILITY: Dataset lifecycle
GOAL: Walk a case backwards - remove one dataset without destroying the case -
      so a wrong file can be dropped and replaced.

CONTEXT: Cases can be created, duplicated, and deleted wholesale, and runs can
         be deleted... but nothing can remove a single dataset. An analyst who
         attaches the wrong CSV has to throw the whole case away and rebuild
         it. P3-FLOW-004 derives the workflow stage from the artifacts a case
         has, so removing a dataset is also the only way to observe the stage
         moving backwards.
INPUTS: an existing case with at least one attached dataset.
RELEVANT FILES: server/app/main.py (the endpoint + the run-touches check),
                server/tests/test_dataset_delete.py (NEW)
REQUIRED CHANGE:
  - DELETE /cases/{case_id}/datasets/{dataset_id} removes the dataset row, its
    profile, its plans, and its on-disk file; the case, other datasets and
    every unrelated artifact survive. 204 on success, 404 for an unknown case
    or dataset.
  - It REFUSES with 400 while any run still touches the dataset - a run is the
    evidence a finding and a chart stand on (the evidence chain is
    finding -> run -> dataset), so removing a dataset that a run binds would
    leave a dangling trace. The refusal names how many runs block it. The check
    covers both runs.dataset_id and runs.dataset_ids_json, because a
    multi-dataset run (P3-DATA-003) binds several datasets at once.
  - Deleting the last dataset is allowed and leaves an empty-but-valid case.
NON-GOALS: cascade deletion of runs/findings/charts (that is what
           DELETE /cases/{id} is for - silently destroying evidence is not
           this endpoint's job), a soft-delete/trash bin, undo, batch delete.
CONSTRAINTS: no schema change, no change to any existing endpoint or response;
             the on-disk file must go with the row, so no orphaned storage.
ACCEPTANCE CRITERIA:
- [x] the dataset row, its profile and its plans are gone; the file on disk is
      gone; the case and every other dataset and artifact are byte-identical
- [x] a run touching the dataset (single-dataset or multi-dataset) blocks
      deletion with a 400 that names the blocker count; deleting the run frees
      it
- [x] deleting the last dataset leaves a valid empty case that still accepts a
      new dataset and a fresh profile
- [x] 404 for an unknown case and for an unknown dataset; a dataset in another
      case is not reachable through this endpoint
- [x] full suite and the P2 gate still pass
TESTS: 8 tests - happy path with a sibling dataset untouched, profile + plans
       removed, file removed, blocked by a single-dataset run, blocked by a
       multi-dataset run, unblocked after the run goes, last-dataset case,
       404s (unknown case, unknown dataset, cross-case dataset).
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-DATA-009 done on pass.
```

### P3-VALID-010 contract

```
TASK ID: P3-VALID-010
MILESTONE: P3 V1
CAPABILITY: Validation
GOAL: Close the last gap in the trust loop - a finding built on a Python run
      can now be validated, not just assumed.

CONTEXT: Validation reruns a finding's stored computation and compares it to
         the persisted result. SQL runs have had that since P1; Python runs
         answered a flat 400 "not supported yet" because re-executing user
         script in-process was unsafe. P3-SEC-001 changed that: the script now
         runs in a separate, OS-sandboxed process with a scrubbed environment,
         so re-execution carries no more risk than the original run.
INPUTS: a finding whose run has kind=python.
RELEVANT FILES: server/app/main.py (validate_finding's Python branch +
                the two reproduction helpers), server/tests/test_validation.py
                (NEW, or extended if it exists)
REQUIRED CHANGE:
  - validate_finding reproduces a Python run by re-executing the stored code
    through run_python against the stored dataset and comparing the tabulated
    columns AND rows to what the run persists - the same reproducibility check
    SQL gets.
  - A script that no longer runs (changed data, a now-broken assumption, a
    time limit) is a FAILED reproducibility check with the reason in its
    detail, never a 500 - mirroring how SQL validation treats a query that no
    longer binds.
  - The missing_data and evidence_integrity checks, and the status arithmetic
    (supported / partially_supported / insufficient_evidence), are shared with
    the SQL path unchanged.
NON-GOALS: validating chart rendering, validating plans, a diff view of
           stored-vs-rerun rows, comparing anything but the tabulated result.
CONSTRAINTS: no schema change; the SQL path's behaviour and response shape are
             unchanged; the sandbox posture of run_python is unchanged (this
             task only calls it again).
ACCEPTANCE CRITERIA:
- [x] a finding on a reproducible Python run validates to supported, with a
      reproducibility check that says the rerun matches
- [x] a finding on a Python run whose stored result was tampered with
      validates to not-supported (partially_supported at minimum), with a
      reproducibility check that says the rerun differs
- [x] a finding whose script now raises validates with a failed check and the
      reason in the detail, and the endpoint returns 200 (a verdict, not a 500)
- [x] the SQL validation path still behaves exactly as before
- [x] full suite and the P2 gate still pass
TESTS: 4 tests - reproduces, tampered result is caught, failing script is a
       verdict, and SQL validation is unchanged.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-VALID-010 done on pass.
```

### P3-AI-011 contract

```
TASK ID: P3-AI-011
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 1 of 4: result interpretation)
GOAL: Tell the analyst what a persisted result actually shows, in the language
      of the case's own question, without making them re-derive it.

CONTEXT: The loop can run, chart, validate and export - but reading a result
         still means reading a table. A non-trivial result needs a human to
         re-derive what it says about the question. The planner (P2-AI-011)
         already proved the two-engine pattern: a deterministic engine that is
         always available, and an LLM behind it that degrades to the
         deterministic read on any failure. This is that pattern applied to a
         result instead of to a profile.
INPUTS: a persisted run (SQL or Python), the case's question, and the primary
        dataset's profile.
RELEVANT FILES: server/app/interpreter.py (NEW), server/app/db.py (table),
                server/app/models.py (Interpretation), server/app/main.py
                (endpoints + duplicate/delete), server/tests/test_interpretations.py
                (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/runs/{run_id}/interpret (201) reads the run's own
    persisted columns and rows, the question, the SQL or Python that produced
    it, and the dataset profile, then returns {summary, observations, caveats}
    and persists it as an artifact of the run.
  - GET .../interpret returns the latest, GET .../interpretations the history
    newest first.
  - Two engines behind one interface, exactly as the planner does it:
    `interpret_result` is deterministic and always available, reading the
    result's own numbers (row counts, numeric min/max/mean, the most frequent
    value per text column); `LLMInterpreter` calls the OpenAI-compatible
    endpoint when DAH_LLM_API_KEY is set, schema-validated by this module, and
    any failure - bad JSON, schema violation, network - falls back to the
    deterministic read. `source` records which engine spoke.
  - An interpretation is a child of a run: duplicated with the case (remapped
    to the copy's run ids) and removed with it.
NON-GOALS: finding drafting (slice 2), code generation (slice 3),
           conversational memory (slice 4), streaming, per-row narration,
           interpretation of charts as distinct from the runs behind them.
CONSTRAINTS: every observation must reference a value that is actually in the
             persisted result - the deterministic engine computes from the rows
             and the LLM is prompted with them, so an interpretation can never
             invent a number. The persisted source field always says which
             engine spoke. No existing endpoint or response changes.
ACCEPTANCE CRITERIA:
- [x] a deterministic interpretation is produced with no key configured; its
      summary and observations reference the result's real columns and values
- [x] a configured LLM's valid output is persisted with source=llm
- [x] an LLM that raises, returns malformed JSON, or violates the schema
      falls back to source=deterministic and the endpoint still answers 201
- [x] an interpretation survives a session restart and is retrievable, and the
      history is newest first
- [x] 404 for an unknown case, an unknown run, and a run belonging to another
      case
- [x] duplicating a case copies its interpretations onto the copy's own runs;
      deleting a case removes them
- [x] full suite and the P2 gate still pass
TESTS: 9 tests - deterministic read, real values referenced, LLM persisted,
       LLM failure/malformed/schema-violation fallbacks (3), retrieval across a
       session + newest-first history, 404 contract, duplicate/delete
       survival.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-011 done on pass.
```

### P3-AI-012 contract

```
TASK ID: P3-AI-012
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 2 of 4: finding drafting)
GOAL: Draft the *candidate* finding a result would support, so the analyst
      decides whether it becomes evidence rather than finding out an LLM
      already decided for them.

CONTEXT: Slice 1 (P3-AI-011) reads a result. The next step in the loop is a
         finding - and a finding is the trust artifact: it is what the evidence
         chain, validation and export are built on. So this slice stops one
         step short of it. The LLM drafts; a human accepts; only the acceptance
         writes a row to findings, through the endpoint that already exists.
INPUTS: a persisted run, the case question, and the dataset profile - the same
        inputs interpretation takes, so the two slices compose.
RELEVANT FILES: server/app/drafter.py (NEW), server/app/models.py (DraftFinding),
                server/app/main.py (endpoint), server/tests/test_drafting.py (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/runs/{run_id}/draft-finding (200 - nothing is
    created) returns {statement, interpretation, caveat, grounds, source}.
    `grounds` is the list of values from the result that the statement stands
    on, so a human can check the claim against the numbers.
  - Two engines, one interface, as before: `draft_finding` is deterministic and
    always available - it finds the result's measure and dimension, and states
    which category leads on the measure at what value; `LLMDrafter` calls the
    OpenAI-compatible endpoint when DAH_LLM_API_KEY is set.
  - Honesty is enforced, not hoped for: every number the LLM quotes in its
    statement or its grounds must be a value the result actually contains (a
    cell, the row count, or a derived count). An invented magnitude is a
    validation failure and the draft falls back to the deterministic one.
  - Drafting writes no state. Accepting a draft is a POST to the existing
    /findings endpoint - the only path that creates a finding.
NON-GOALS: persisting drafts (a draft is a proposal, not state; rejected drafts
           are deliberately not kept), batch drafting, drafting from a chart,
           accepting a draft in one call (acceptance is the existing endpoint,
           so the human-owns-the-finding property is structural, not a flag).
CONSTRAINTS: the findings table is untouched by this task - same schema, same
             endpoints, same responses. No existing behaviour changes.
ACCEPTANCE CRITERIA:
- [x] a deterministic draft is produced with no key; statement, interpretation
      and caveat are non-empty and it names the run's real columns
- [x] every value in grounds appears in the result's rows or columns
- [x] an LLM draft quoting only real values is returned with source=llm
- [x] an LLM draft that invents a magnitude falls back to source=deterministic
- [x] an LLM that raises or returns malformed output falls back
- [x] drafting leaves the findings table empty - nothing is created
- [x] a draft's statement is accepted through the existing findings endpoint,
      lands as a real finding, and validates
- [x] a result with no numeric column still yields an honest weaker draft
- [x] 404 for unknown case, unknown run, and a cross-case run
- [x] full suite and the P2 gate still pass
TESTS: 10 tests - deterministic draft, grounds are real, LLM accepted, invented
       magnitude rejected, LLM failure and malformed fallbacks, no state
       written, accept-then-validate round trip, no-numeric-column result, 404s.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-012 done on pass.
```

### P3-AI-013 contract

```
TASK ID: P3-AI-013
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 3 of 4: code generation)
GOAL: Describe what you want to know; the harness proposes the read-only
      computation that would answer it. The analyst decides whether it runs.

CONTEXT: Slices 1 and 2 read a result and draft the finding it would support.
         The step before either is the analysis itself, and writing SQL or
         Python is the part of the loop a non-programmer analyst cannot do
         alone. So this slice generates the code - and stops one step short of
         running it, exactly as drafting stops one step short of a finding.
INPUTS: a question in plain language, a dataset profile (columns, types, nulls),
        and the desired kind (sql | python).
RELEVANT FILES: server/app/generator.py (NEW), server/app/models.py
                (GeneratedCode), server/app/main.py (endpoint),
                server/tests/test_code_generation.py (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/datasets/{dataset_id}/generate-code (200 - nothing is
    created) with {question, kind?} returns {kind, code, explanation,
    columns_used, source}.
  - Two engines, one interface, as before: `generate_code` is deterministic and
    always available - it picks the profile's first numeric measure and its
    first categorical (or temporal) dimension and writes a GROUP BY
    aggregation, or a count-by-dimension query when there is no measure;
    `LLMGenerator` calls the OpenAI-compatible endpoint when DAH_LLM_API_KEY
    is set.
  - Honesty is enforced, not hoped for: every column the generated code
    references must be a column the dataset actually has. An invented column is
    a validation failure and the proposal falls back to the deterministic one.
    Safety likewise: a generated SQL proposal that is not a single read-only
    statement is rejected, not handed to the analyst.
  - Generation writes no state. Running a proposal is a POST to the existing
    runs endpoint (`/runs` for sql, `/runs/python` for python) - the only path
    that persists a run, so the human decides what executes.
NON-GOALS: executing generated code from this endpoint (it proposes; the
           existing endpoints run), generating joins or multi-dataset queries,
           generating chart or finding artifacts, persisting proposals,
           iterating on a proposal conversationally (slice 4).
CONSTRAINTS: no new table; runs endpoints, schema and responses unchanged.
ACCEPTANCE CRITERIA:
- [x] a deterministic proposal is produced with no key; code, explanation and
      columns_used are non-empty and every column named is a real profile column
- [x] a generated SQL proposal runs as-is through the existing /runs endpoint
- [x] a generated Python proposal runs as-is through /runs/python and tabulates
- [x] the deterministic proposal is a single read-only statement
- [x] an LLM proposal referencing only real columns is returned with source=llm
- [x] an LLM proposal that invents a column falls back to source=deterministic
- [x] an LLM proposal that is not read-only (a DELETE/DROP) falls back
- [x] an LLM that raises or returns malformed output falls back
- [x] generation writes no state - no run is created
- [x] 404 for unknown case, unknown dataset, and a cross-case dataset
- [x] full suite and the P2 gate still pass
TESTS: 13 tests - deterministic SQL, deterministic Python, columns are real,
       LLM accepted, invented column rejected, non-read-only rejected, failure
       and malformed fallbacks, no state written, accept-then-run round trip,
       404s.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-013 done on pass.
```

### P3-AI-014 contract

```
TASK ID: P3-AI-014
MILESTONE: P3 V1
CAPABILITY: Contextual AI (slice 4 of 4: conversational memory)
GOAL: Ask the case a question in plain language and get an answer grounded in
      what the case actually contains - with the citations to prove it.

CONTEXT: Slices 1-3 propose: a question yields the computation that would
         answer it, a result yields a reading and a candidate finding. Each
         stops one step short of writing state. This slice is the last piece:
         the assistant remembers the conversation and answers from the case's
         own artifacts, so the analyst can ask rather than dig.
INPUTS: a case (its datasets, profiles, runs, findings, plans, charts, derived
        workflow stage), the conversation so far, and a message.
RELEVANT FILES: server/app/assistant.py (NEW), server/app/db.py (table),
                server/app/models.py (ChatRequest, ConversationTurn),
                server/app/main.py (endpoints),
                server/tests/test_conversation.py (NEW)
REQUIRED CHANGE:
  - POST /cases/{case_id}/chat with {message} -> 201
    {id, case_id, message, answer, grounds, source, created_at}.
    GET /cases/{case_id}/chat returns the whole conversation oldest-first, so
    a reopened case resumes mid-thought.
  - `summarize_case` reads the case's rows and builds the facts an answer may
    draw on: datasets with their columns and stats, runs with their columns and
    row counts, findings with their validation status, plans, charts, and the
    derived workflow stage. A pure projection, like the evidence graph and the
    history timeline, so it cannot drift from what is on disk.
  - Two engines, one interface: `answer_question` is deterministic and always
    available - it answers count questions, column and dataset questions, and
    otherwise states where the case stands and the one action that advances it
    (reusing P3-FLOW-004's derived stage); `LLMAssistant` calls the
    OpenAI-compatible endpoint when DAH_LLM_API_KEY is set and receives the
    recent turns as context - that is the memory.
  - Honesty is enforced, not hoped for: every citation in `grounds` must be an
    artifact the case actually has (a dataset, run, finding, plan, chart or
    column that exists). An invented citation is a validation failure and the
    answer falls back to the deterministic one. An answer about a case that has
    artifacts must cite at least one of them.
NON-GOALS: executing analysis from chat (the proposal slices do that; chat
           answers and cites), streaming, multi-case conversations, exporting
           or duplicating a conversation (a duplicate starts a fresh
           investigation), tool calling / function calling.
CONSTRAINTS: no existing endpoint, schema or response changes. The new
             conversations table is created under CREATE TABLE IF NOT EXISTS,
             so older databases need no migration. DELETE /cases/{id} removes a
             case's conversation; nothing else writes to the table.
ACCEPTANCE CRITERIA:
- [x] a deterministic answer is produced with no key; answer and grounds are
      non-empty
- [x] every ground cites an artifact the case actually has
- [x] a "how many" question is answered with the case's real counts
- [x] a question naming a column is answered with that column's real profiled
      stats
- [x] a question about nothing specific is answered with the case's derived
      stage and next action
- [x] an LLM answer citing real artifacts is returned with source=llm
- [x] an LLM answer that invents a citation falls back to source=deterministic
- [x] an LLM that raises or returns malformed output falls back
- [x] the LLM receives the prior turns as context - a second question is
      answered with the first one in view
- [x] the conversation persists across a restart, oldest-first
- [x] deleting the case removes its conversation rows
- [x] 404 for an unknown case (posting and reading)
- [x] full suite and the P2 gate still pass
TESTS: 12 tests - counts, column stats, stage fallback, grounds are real, LLM
       accepted, invented citation rejected, failure and malformed fallbacks,
       memory (prior turn in context), persistence oldest-first, delete
       cleanup, 404s.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS.
STATE UPDATE: mark P3-AI-014 done on pass; this closes roadmap item 7.
```

### P4-VERIFY-001 contract

```
TASK ID: P4-VERIFY-001
MILESTONE: P4 Production Candidate
CAPABILITY: Verification (P3 gate)
GOAL: Prove the P3 capabilities work as one journey, not just as separate
      suites.

CONTEXT: the P2 gate re-verifies the test suite, and every P3 task shipped its
         own tests, but nothing walked the P3 surface end to end - multi-dataset
         joins, the OS-level sandbox, the four assistant slices, raster charts,
         the derived workflow and case reuse. A phase is done when a gate says
         so, and P3 had no gate of its own.
INPUTS: none (the gate builds its own data: a CSV and a Parquet written from a
        table, so the join deliberately mixes formats).
RELEVANT FILES: verification/p3/verify_p3.py (NEW),
                verification/p3/REPORT.md (generated), ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE: write verification/p3/verify_p3.py after the P0/P1/P2 gates -
         in-process TestClient, one atomic journey, a step table and an exit
         criteria table in verification/p3/REPORT.md, exit 0 only when every
         step passes. The journey is: question -> attach CSV + Parquet ->
         profile both -> generate-code (writes nothing) -> plan -> join run ->
         hard-sandbox escape attempt refused -> interpret -> draft-finding
         (writes nothing) -> accept through the only endpoint that writes ->
         raster chart -> validation closes the loop -> evidence graph reaches
         both datasets -> workflow reports loop_closed -> chat with citations
         -> EDA -> history -> search -> template outlives the case -> dataset
         deletion blocked by evidence -> export -> import -> join reproduces
         elsewhere -> suite green.
NON-GOALS: new server behaviour (the gate exercises what exists; if the journey
           exposes a bug, that is a separate task), LLM live calls in the
           journey (the gate is hermetic - see CONSTRAINTS), a UI, performance
           measurement (that is the P4 performance task).
CONSTRAINTS: deterministic by construction - app.main loads server/.env at
             import and every assistant engine reads the LLM credentials at
             call time, so the gate scrubs those variables from its own process
             after import and from the pytest subprocess it spawns; the journey
             therefore reports source=deterministic on every assistant step and
             makes no network call. The LLM paths stay covered by the suite,
             which tests both engines explicitly. The journey's data is clean
             (no nulls, no duplicates) so validation reaching `supported` proves
             the join reproduces, not that a messy finding was tolerated.
ACCEPTANCE CRITERIA:
- [x] the gate runs standalone and exits 0 only when every step passes
- [x] the journey joins two attached datasets of different formats in one run
- [x] a sandbox escape attempt is a 400 that leaves no run behind
- [x] each assistant slice fires once, writes nothing where the contract says
      so, and the human-only action (accept the draft) is what creates state
- [x] a finding on the join run validates to supported with the reproducibility
      check passing
- [x] the evidence graph's claim trace reaches both datasets the join bound
- [x] the derived workflow reports stage=validated and loop_closed
- [x] the case survives search, templating (template outlives the case), and an
      export/import round trip that reproduces the join
- [x] dataset deletion is refused while evidence stands on it
- [x] the full server suite passes as the gate's last step
TESTS: the gate itself is the test - 23 journey steps + the 211-test suite.
VERIFICATION: server/.venv/bin/python verification/p3/verify_p3.py -> PASS
      (verification/p3/REPORT.md, all 15 exit criteria PASS).
STATE UPDATE: mark P4-VERIFY-001 done on pass; P4's checklist item 1 is
      complete.
```

### P4-RELIABILITY-002 contract

```
TASK ID: P4-RELIABILITY-002
MILESTONE: P4 Production Candidate
CAPABILITY: Reliability
GOAL: An input error always answers 400 with a reason, and a server failure
      always answers 500 and gets logged - never the other way round.

CONTEXT: five API endpoints (single SQL run, multi SQL run, Python run, EDA,
         chart render) end in `except Exception as error: raise 400`,
         "... failed: {error}". That clause is doing two jobs at once: it is
         the only thing turning a user's SQL syntax error into a 400 (DuckDB
         raises duckdb.Error, which is not a ValueError, so the `except
         ValueError` above it does not catch it), and it is also flattening
         every real server fault - a sqlite error, an unreadable stored file, a
         KeyError in our own code - into a 400 that blames the user. A bug in
         the harness currently looks like bad input, to the analyst and in the
         logs. Separately, the five LLM fallback paths catch `except Exception`
         deliberately - degradation is the contract - but silently, so a bug in
         our own code vanishes into source=deterministic and is never surfaced.
INPUTS: any request to the five engine endpoints, plus the LLM fallback paths.
RELEVANT FILES: server/app/errors.py (NEW), server/app/main.py,
                server/app/planner.py, server/app/interpreter.py,
                server/app/drafter.py, server/app/generator.py,
                server/app/assistant.py,
                server/tests/test_error_semantics.py (NEW)
REQUIRED CHANGE:
  - app/errors.py owns the taxonomy once: INPUT_ERROR_TYPES is the tuple of
    exception families that mean the input cannot be honoured - ValueError
    (every engine's own validation: the read-only gate, unknown columns, a
    sandbox rejection, a missing result) and duckdb.Error (SQL that cannot
    parse or bind, which is not a ValueError). Those answer 400. Everything
    else is a server failure and is let through to FastAPI's 500, which logs
    the traceback instead of hiding it in a 400.
  - the five engine sites become `except INPUT_ERROR_TYPES as error:
    raise 400`; the broad clause goes away. The chart site keeps ValueError
    alone, because render_chart validates everything itself and raises
    ValueError for all of it.
  - the five LLM fallbacks stay broad - an unavailable or misbehaving LLM may
    never block the loop - but the reason is logged at warning level, so a
    fallback caused by our own bug is visible instead of silent.
NON-GOALS: changing any success-path behaviour or response shape; touching the
           validation endpoints, whose `except (ValueError, Exception)` is
           correct - a finding that no longer reproduces must answer 200 with a
           failed check, never a 500; rewriting the duckdb error text; a global
           error handler or structured logging framework (that is observability,
           a later P4 item); the two `referenced run/dataset is missing` 500s
           and the plan-validation 500, which are integrity violations the
           server allowed and where 500 is the honest answer.
CONSTRAINTS: no existing endpoint contract changes - every request that
             answers 400 today still answers 400, with the engine's own message
             rather than the generic "X failed: ..." wrapper; the LLM
             degradation contract is unchanged (any failure still falls back).
ACCEPTANCE CRITERIA:
- [x] SQL that cannot parse, and SQL naming an unknown column, answer 400 with
      the engine's message - narrowing the catch did not make bad input a 500
- [x] a sandbox rejection (script with no result, write attempt) still answers
      400
- [x] an injected server-side fault in each of the five engines answers 500
      instead of a 400 that blames the input
- [x] an LLM that raises anything - expected or not - still falls back to
      source=deterministic, and the reason is logged
- [x] no success path changed; full suite, the P2 gate and the P3 gate pass
TESTS: server/tests/test_error_semantics.py - bad SQL (syntax and unknown
       column), injected 500s for all five engines (run_query, run_query_multi,
       run_python, run_eda, render_chart), and the LLM fallback on an
       unexpected error type. Uses a TestClient with raise_server_exceptions
       off, which is the only way a 500 is observable in process.
VERIFICATION: pytest green + verification/p2/verify_p2.py PASS +
              verification/p3/verify_p3.py PASS.
STATE UPDATE: mark P4-RELIABILITY-002 done on pass.
```

### P4-UX-003 contract

```
TASK ID: P4-UX-003
MILESTONE: P4 Production Candidate
CAPABILITY: UX (case workspace + chat)
GOAL: DAH can be *used* from the shell, not only from curl: find a case, open
      it, see where it stands, and ask it a question.

CONTEXT: the React bundle still shows the P0/P1 surface - one case-creation
         form. Every P3 capability - the derived workflow, the evidence graph,
         the four assistant slices - is reachable only through the API. The
         assistant surfaces need somewhere to live, so the workspace comes
         first; chat is the one assistant slice that needs nothing but a case,
         and its citations are the honesty property the UI should make visible.
         The run-scoped slices (interpret, draft-finding, generate-code) need a
         run-selection surface and are P4-UX-004.
INPUTS: a case id; a chat message.
RELEVANT FILES: web/src/api.ts, web/src/App.tsx, web/src/CaseList.tsx (NEW),
                web/src/CaseWorkspace.tsx (NEW), web/src/CaseCreation.tsx,
                web/src/index.css, web/src/CaseList.test.tsx (NEW),
                web/src/CaseWorkspace.test.tsx (NEW)
REQUIRED CHANGE:
  - api.ts becomes a typed client over the real contracts: GET /cases (with
    q), GET /cases/{id}, GET .../progress, GET .../datasets, GET .../runs,
    POST + GET .../chat. One shared request() throws an ApiError carrying the
    status and a message parsed from the body only when the body is JSON - a
    500 answers plain text (P4-RELIABILITY-002), and res.json() on it must not
    become a second, hiding failure.
  - CaseList lists cases with a literal-substring search box; opening one
    navigates to the workspace. CaseCreation survives as the way a new case
    starts, and creating one opens it.
  - CaseWorkspace shows the question, the derived stage and single next action
    (progress is recomputed on open, so the UI can never show a stage the data
    does not support), the attached datasets, the runs with their kind and row
    counts, and the chat panel: a message box, the answer, each ground rendered
    as a citation chip, and a badge for which engine spoke (source). Prior
    turns load oldest-first, so a reopened case resumes mid-thought.
  - App.tsx owns state-based navigation - list, workspace, create - with no
    router dependency, keeping the bundle dependency-free as DEC-001 intends.
NON-GOALS: the run-scoped assistant surfaces (P4-UX-004); running queries or
           accepting drafts from the UI (those still belong to the endpoints
           that write); charts and evidence-graph rendering; styling beyond
           readable; a router or state-management library.
CONSTRAINTS: every screen reads its own data from the API on mount - nothing
             is cached across navigation, so the UI cannot go stale against
             the core; the existing two web tests keep passing; the bundle
             gains no dependency.
ACCEPTANCE CRITERIA:
- [x] cases list, and the search box filters them by the API's q parameter
- [x] opening a case shows its question, its derived stage and next action,
      its datasets and its runs
- [x] a chat message is posted and the answer renders with its grounds as
      citation chips and the engine that spoke
- [x] prior turns load on open, oldest-first
- [x] an API failure renders as readable text and never as a crash; a
      plain-text 500 body does not break the client
- [x] creating a case lands in its workspace
- [x] web tests pass; the server suite and both gates stay green
TESTS: web/src/CaseList.test.tsx and CaseWorkspace.test.tsx - render from
       mocked api responses, search, open, chat round trip with grounds and
       source badge, and an error rendered rather than thrown.
VERIFICATION: cd web && npm test green + the P2/P3 gates as regression.
STATE UPDATE: mark P4-UX-003 done on pass; the run-scoped slices are next.
```

### P4-UX-004 contract

```
TASK ID: P4-UX-004
MILESTONE: P4 Production Candidate
CAPABILITY: UX (run-scoped assistant surfaces)
GOAL: The three remaining assistant slices are reachable from the workspace:
      generate code from a question, read what a run shows, and draft the
      finding it would support - each proposing, none deciding.

CONTEXT: P4-UX-003 gave the shell a case workspace with chat, the one slice
         that needs nothing but a case. The other three are run-scoped: they
         need a dataset to generate against and a run to read or draft from.
         They also need the analyst to be able to attach data, profile it and
         run a query in the first place, or the surfaces have nothing to hang
         on - so the workspace gains the steps the core loop actually walks.
INPUTS: a case; a dataset; a run; a question in plain language.
RELEVANT FILES: web/src/CaseWorkspace.tsx, web/src/api.ts,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - api.ts gains the remaining contracts: attach a dataset, profile one, run
    SQL (single- and multi-dataset), the three assistant calls
    (generate-code, interpret, draft-finding) and the two that accept a
    proposal (POST /findings, POST .../validate).
  - CaseWorkspace becomes the loop the core walks, one panel per step, each
    reading its own data and each proposal surfaced as a decision the human
    makes:
      * Attach + profile: file picker, then profile, then the columns and
        nulls it found;
      * Generate code: a question against a profiled dataset returns code,
        explanation and the columns it reads, with a Run button that posts it
        to the runs endpoint - the only path that persists a run;
      * Runs: each lists its kind and row count, with Interpret (what it
        shows) and Draft finding (what it claims) buttons;
      * A draft renders its statement, interpretation, caveat and grounds,
        and Accept posts it to /findings - the only path that writes one -
        after which Validate reruns the computation and reports the verdict.
  - Every assistant panel shows which engine spoke (source), because a
    deterministic answer citing only real values and an LLM answer carry
    different weight.
NON-GOALS: a SQL editor with highlighting or schema introspection beyond the
           profile; charts in the UI (a later slice); multi-dataset join
           building (the attach UI stays one file at a time; the API still
           accepts a list); streaming; executing generated code without the
           human's explicit Run.
CONSTRAINTS: no server change - every call is an existing endpoint; no new
             runtime dependency; every screen reads its own data after an
             action, so the UI cannot go stale against the core; acceptance
             still goes through the findings endpoint and running still
             through the runs endpoint, so the propose/human-decides split
             stays structural rather than becoming a UI flag.
ACCEPTANCE CRITERIA:
- [x] a dataset attaches and profiles from the UI; the columns and null counts
      it reports are the profile's own
- [x] a question against a profiled dataset returns generated code with its
      explanation and columns used, and the code runs through the runs
      endpoint when the analyst chooses Run
- [x] a run interprets: summary, observations and caveats render, with the
      engine that spoke
- [x] a run drafts a finding: statement, interpretation, caveat and grounds
      render, and Accept creates a real finding (not_evaluated, as the API
      insists)
- [x] a created finding validates and the verdict renders
- [x] no assistant action writes state except through the endpoints that own
      it - generation and interpretation-creation aside, drafting and
      generating create nothing, and a rejected draft leaves nothing behind
- [x] an API failure renders as text, never a crash
- [x] web tests cover each surface; the server suite and both gates stay green
TESTS: web/src/CaseWorkspace.test.tsx extended - attach+profile, generate-code
       round trip with Run, interpret, draft + accept + validate, error
       rendering, no state written by a draft.
VERIFICATION: cd web && npm test green + the P2/P3 gates as regression.
STATE UPDATE: mark P4-UX-004 done on pass; this closes the assistant surfaces
              and roadmap item 3.
```

### P4-VALID-005 contract

```
TASK ID: P4-VALID-005
MILESTONE: P4 Production Candidate
CAPABILITY: Validation (rerun determinism)
GOAL: Validating the same finding twice always gives the same verdict.

CONTEXT: the live-LLM smoke of P4-UX-004 walked the whole loop repeatedly and
         validation started flipping between `supported` and
         `insufficient_evidence` on identical inputs. The cause was in the
         comparison, not the data: DuckDB does not promise a row order for a
         result that never asked for one, and a GROUP BY can return its groups
         in a different order on a different connection (observed: 2 distinct
         orders across 8 reruns of one query). `_reproduce_sql` compared rows
         positionally, so an unordered query validated as a rerun mismatch
         roughly half the time - and a verdict that depends on which
         connection happened to answer is not a verdict at all.
INPUTS: a finding whose run stored an unordered result set.
RELEVANT FILES: server/app/main.py, server/tests/test_validation.py
REQUIRED CHANGE:
  - `_row_key(row)` canonicalises one row as JSON, so the sort key is
    type-aware and deterministic;
  - `_reproduce_sql` compares `sorted(rerun rows) == sorted(stored rows)` - a
    multiset comparison. An SQL result set is a bag of rows; only ORDER BY
    makes it a sequence, and when the query asks for one DuckDB honours it
    deterministically, so the sort is a no-op there and a correction
    everywhere else;
  - `_reproduce_python` is deliberately unchanged: the Python tabulator is
    deterministic and column order is a shape signal (a changed shape is a
    changed result), so positional comparison stays right there.
NON-GOALS: normalising row order at store time; changing the verdict
           vocabulary; touching the null or duplicate checks; any UI change.
CONSTRAINTS: the fix must not weaken the gate - rows that differ as a
             multiset still fail reproducibility, and a query that no longer
             binds still reports a failed check rather than a 500.
ACCEPTANCE CRITERIA:
- [x] a stored result whose rows were deliberately reordered validates
      `supported`
- [x] an unordered GROUP BY validated 12 times returns exactly {"supported"}
- [x] a genuine multiset drift still fails reproducibility (the pre-existing
      drift test, which substitutes a value no rerun can produce)
- [x] the full suite and both the P2 and P3 gates stay green
TESTS: server/tests/test_validation.py +2 - `test_validate_accepts_reordered_unordered_result`
       (verified to FAIL without the fix) and
       `test_validate_unordered_groupby_is_stable_across_reruns` (12 reruns).
VERIFICATION: pytest green (225 passed) + P2/P3 gates PASS.
STATE UPDATE: mark P4-VALID-005 done on pass; a validation verdict no longer
              depends on which DuckDB connection answered.
```

### P4-PERF-006 contract

```
TASK ID: P4-PERF-006
MILESTONE: P4 Production Candidate
CAPABILITY: Performance (large-dataset behaviour)
GOAL: DAH stays responsive on a dataset too large to be a toy, and the
      behaviour that protects memory at scale is measured and pinned rather
      than assumed.

CONTEXT: the 1000-row result cap has existed since P1 and nothing had ever
         been measured at scale - "it probably holds" is not a property. A
         benchmark on a 200k-row / 13.4MB CSV found the real cost: attaching
         and querying were fine (0.2s and 0.8s), export was fine (0.4s,
         17.8MB package, dominated by the dataset bytes), but PROFILING took
         ~6s. Instrumented internally, the cause was exact and wasteful:
         profile_csv ran `SELECT *` and then `fetchall()` on the entire
         dataset purely to read the column description - 2.68s of materialising
         rows that were then thrown away - followed by four separate full
         scans (aggregates, COUNT(*), and duplicate-row count's own COUNT(*)
         plus DISTINCT). The description, names AND inferred types, is
         available with LIMIT 0 and fetches nothing.
INPUTS: a large CSV (100k+ rows); a case with several artifacts.
RELEVANT FILES: server/app/analysis.py, server/tests/test_profiles.py,
                server/tests/test_large_datasets.py (NEW)
REQUIRED CHANGE:
  - profile_csv reads the description via `SELECT * ... LIMIT 0` instead of
    materialising every row;
  - the row total is folded into the single per-column aggregate pass as a
    leading COUNT(*), so the separate COUNT(*) scan is gone;
  - _duplicate_row_count takes the already-known total instead of recounting;
  - the result cap and the truncation flag are exercised at scale, and the
    profile's correctness at scale is pinned by tests.
NON-GOALS: rewriting the profile vocabulary; streaming/async endpoints;
           paginating results; changing the 1000-row cap or the 100MB export
           guard; memory-profiling the Python sandbox worker; chart rendering
           cost.
CONSTRAINTS: the profile output must be byte-for-byte the same shape as
             before (the tests are the proof); correctness must not be traded
             for speed - a wrong fast profile is worse than a slow right one;
             the fix must not depend on file format (csv/parquet/xlsx all
             reach the same code path).
ACCEPTANCE CRITERIA:
- [x] profiling a 200k-row CSV is materially faster than before (measured
      ~6.0s -> ~1.9s, a 3x improvement) with an identical profile output
- [x] a SELECT * run at scale reports row_count=1000 and truncated=true
- [x] the profile at scale reports the right row count, nulls, distinct counts
      and duplicate rows (known-answer data, generated deterministically)
- [x] export on a case carrying a large dataset stays bounded and round-trips
- [x] the existing profile tests (including header-only and parquet/xlsx)
      stay green, and the full suite plus both gates pass
TESTS: server/tests/test_large_datasets.py (NEW) - a deterministic 50k-row
       generator, profile correctness at scale, the result cap truncating a
       full-table query, a wide table (many columns) profiling correctly, and
       the duplicate count on data with known duplicates.
VERIFICATION: pytest green + P2/P3 gates PASS; the benchmark numbers above
              are recorded in ai/CURRENT_STATE.md so the next regression is
              measured against a number, not a feeling.
STATE UPDATE: mark P4-PERF-006 done on pass; roadmap item 4 is measured and
              the profiling hot path is fixed.
```

### P4-CI-007 contract

```
TASK ID: P4-CI-007
MILESTONE: P4 Production Candidate
CAPABILITY: Distribution (CI + signing decision)
GOAL: Every layer is verified by CI on a clean machine, including the desktop
      shell's core lifecycle and the sidecar build, and the app-signing
      question is answered in writing rather than left open.

CONTEXT: P3-SHELL-008 shipped a desktop shell whose lifecycle was only ever
         tested locally - `cargo test --features e2e` spawns the real uvicorn
         and asserts the core answers and then stops, but nothing ran it on a
         fresh checkout. There was also no CI of any kind in the repo: no
         workflow file existed, so the 231 server tests, 17 web tests and 7
         Rust tests were green only because a developer happened to run them.
         Separately, the packaged app is unsigned and the question of when to
         sign was carried from P3 without a decision.
INPUTS: the repo as cloned (no local venv, no built sidecar, no LLM keys).
RELEVANT FILES: .github/workflows/ci.yml (NEW), README.md (NEW),
                ai/DECISIONS.md, server/pyproject.toml, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - .github/workflows/ci.yml: four jobs.
      * server - uv venv from pyproject, pytest, then the P2 and P3 gates
        in-process, with the gate reports uploaded as an artifact.
      * web - npm ci, npm test, npm run build (tsc -b runs first, so a type
        error the jsdom tests cannot see still fails CI).
      * desktop - the server venv at the exact path the resolver looks for,
        then cargo test (unit) and cargo test --features e2e (lifecycle:
        spawn a real core, wait on /health, assert the port is freed).
      * packaging - build the sidecar from declared extras and smoke it: the
        binary must actually serve /health, not merely build.
    macOS-only on purpose: the hard sandbox is macOS seatbelt and the packaged
    app and sidecar are macOS builds; another platform would skip the paths
    that most need exercising. No LLM credentials are ever set, so every
    assistant step is deterministic and the run makes no network call.
  - server/pyproject.toml: two fixes found by validating the install path on a
    clean venv. (1) `[tool.setuptools] packages = ["app"]` - flat-layout
    discovery saw `app` and `tests` as competing top-level packages and failed
    on a fresh checkout; a stale egg-info masked it locally. (2) a `packaging`
    extra declares PyInstaller, which was previously installed ad-hoc and was
    not reproducible.
  - README.md (NEW): the layers and their test commands, and the unsigned-app
    first-launch workaround in plain language.
  - ai/DECISIONS.md DEC-004: signing deferred to P5, with the reason, the
    alternatives considered (ad-hoc signing, xattr bypass), and the
    consequences - including that nothing in P4 may depend on the app being
    signed.
NON-GOALS: the P0 gate in CI (it binds a port and duplicates the later
           gates); Windows/Linux runners; release automation or artifact
           publishing; actually signing or notarizing the app (DEC-004 defers
           it); load/performance testing in CI.
CONSTRAINTS: every command in the workflow was validated by running it
             locally in the order the workflow runs it - the venv install on a
             clean directory, the suite and both gates, npm ci and the build,
             the cargo lifecycle tests, and the sidecar build plus a health
             smoke against the freshly built binary. The workflow must never
             need an LLM key or any other secret (DEC-004 keeps signing out,
             so no identity is required either).
ACCEPTANCE CRITERIA:
- [x] a workflow file exists and is valid YAML, covering server, web, desktop
      and packaging
- [x] the server job installs from pyproject on a clean venv and the suite
      plus both gates pass (231 tests)
- [x] the desktop job runs the two live-core lifecycle tests (7 Rust tests)
- [x] the packaging job builds the sidecar from declared extras and the built
      binary answers /health
- [x] no secret, key or credential is required for any job to pass
- [x] the signing question has a written decision with consequences, and the
      user-facing workaround is documented in the README
- [x] the local suite and both gates still pass on this machine
TESTS: none new - this task's verification is that the existing 231 + 17 + 7
       tests run under the CI it creates, plus a health smoke on the built
       sidecar.
VERIFICATION: validated step by step locally (venv install on a clean
              directory, suite + P2/P3 gates, npm ci + build, cargo test
              --features e2e, build_sidecar.sh + /health smoke); pytest 231
              passed, web 17 passed, cargo 7 passed, both gates PASS.
STATE UPDATE: mark P4-CI-007 done on pass; the P4 checklist's distribution
              item is closed (signing formally deferred to P5 by DEC-004).
```

### P5-VERIFY-001 contract

```
TASK ID: P5-VERIFY-001
MILESTONE: P5 Production Grade
CAPABILITY: Verification (P4 gate)
GOAL: Prove the P4 properties hold as one journey, not as separate suites.

CONTEXT: every earlier phase has a gate that walks its journey end to end -
         P4 alone relied on the P3 gate plus the per-task suite, which is
         honest but never exercised the P4 capabilities against each other.
         The two properties that make P4 *P4* - the error taxonomy
         (P4-RELIABILITY-002) and rerun determinism (P4-VALID-005) - are
         invisible on the happy path, so no existing gate saw them.
INPUTS: an in-process TestClient; a dataset larger than the result cap.
RELEVANT FILES: verification/p4/verify_p4.py (NEW), verification/p4/REPORT.md
                (emitted), .github/workflows/ci.yml, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - verification/p4/verify_p4.py: 18 steps walking the edges a controlled
    external user reaches - a 5000-row dataset, the result cap truncating a
    full scan while an aggregate over the same data stays exact, bad SQL
    answering 400 with the engine's own message and persisting nothing, a
    write and a sandbox escape both refused, an injected harness fault
    answering 500, a deliberately broken LLM degrading to deterministic, the
    assistant drafting without writing, the human accepting, eight repeat
    validations of an unordered result agreeing, and an export/import round
    trip.
  - .github/workflows/ci.yml: the server job runs the P4 gate alongside P2
    and P3, and its report is uploaded with the others.
NON-GOALS: the P0 gate (binds a port); testing the React shell (a vitest
           concern); testing CI itself; signing (DEC-004, P5-DIST).
CONSTRAINTS: hermetic - no LLM credential is ever set and the one step that
             sets a dummy key breaks the LLM on purpose, so no run makes a
             network call. Every dataset value is a closed function of the
             row index, so the expectations are known by construction rather
             than measured. Injected faults are restored in a finally block
             so a failure cannot leak a broken engine into later steps.
ACCEPTANCE CRITERIA:
- [x] the gate exits 0 with all 18 steps and all 10 exit criteria PASS
- [x] bad input answers 400 with a message and leaves no run behind
- [x] an injected harness fault answers 500, never 400
- [x] a broken LLM degrades to deterministic and still returns a plan
- [x] the result cap truncates a full scan but an aggregate reads every row
- [x] eight validations of an unordered GROUP BY return exactly {"supported"}
- [x] the case exports and reproduces elsewhere; the suite runs green (231)
- [x] CI runs the gate on every push
TESTS: the gate is the test; it also re-runs the suite as its last step.
VERIFICATION: verification/p4/REPORT.md PASS; P2/P3 gates still PASS.
STATE UPDATE: mark P5-VERIFY-001 done on pass; the P5 checklist's verification
              item is closed and P4 has the gate it previously lacked.
```

### P5-OBSERVE-002 contract

```
TASK ID: P5-OBSERVE-002
MILESTONE: P5 Production Grade
CAPABILITY: Observability
GOAL: When something goes wrong in a packaged app, there is a log to read.

CONTEXT: P4 made a 500 honest - the exception propagates and uvicorn logs a
         traceback. But in the packaged app the core is a PyInstaller sidecar
         whose stderr goes nowhere a user can read, so that traceback lands in
         a void and a support question has nothing behind it. uvicorn's stderr
         is a developer surface; a packaged app needs a file.
INPUTS: DAH_LOG_DIR (optional override), DAH_LOG_LEVEL (optional), the same
        DAH_DATA_DIR the shell already sets.
RELEVANT FILES: server/app/logging_config.py (NEW), server/app/main.py
                (configure at startup, the request middleware, GET /logs),
                server/tests/test_logging.py (NEW), docs/Observability.md (NEW),
                ai/ROADMAP.md, ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - app/logging_config.py owns one setup function, `configure_logging`, that
    installs a size-capped RotatingFileHandler (2MB x 3 backups, so the log
    can never eat the disk) plus a stderr handler, and points the uvicorn
    loggers at the same file so request logs are not lost. Idempotent - a
    second call replaces rather than stacks. The directory defaults to
    DAH_DATA_DIR/logs and DAH_LOG_DIR overrides it, exactly as DAH_DB_PATH
    overrides the default database location. An unwritable log dir degrades
    to stderr-only with a warning instead of preventing the server from
    starting - a log is not worth more than the app.
  - The file handler is NOT installed under pytest (the suite overrides
    DATA_DIR post-import, so an import-time handler would write into the
    repo); tests configure it explicitly against a tmp dir.
  - app/main.py: a request middleware logs method, path, status and duration
    per request. Only those four - the body is never logged, so an analyst's
    SQL, their question and their data stay out of the log.
  - GET /logs?lines=N returns the path, the size, the rotated file names and
    the last N lines (default 200, clamped to 1000) read-only, and reports
    `enabled: false` when file logging is off rather than erroring.
  - docs/Observability.md: where the log lives, how to read it, and the
    explicit privacy boundary - what is logged and what is not.
NON-GOALS: shipping logs anywhere off the machine, a UI for the log (the shell
           can call /logs; wiring a menu is a follow-up), serving the rotated
           backups' contents, structured JSON logs (a plain parseable line is
           enough and stays greppable), authentication on /logs (the core binds
           to 127.0.0.1 for a single local user, like every other endpoint).
CONSTRAINTS: no behaviour change to any existing endpoint; the gates and the
             test suite must be unaffected; nothing the analyst typed may
             appear in the log.
ACCEPTANCE CRITERIA:
- [x] a packaged-style core (DAH_DATA_DIR set) writes dah-core.log under it
      without any caller wiring
- [x] the log rotates at the cap and the total stays bounded (no unbounded
      growth, no rotation storm)
- [x] a 500's traceback is in the file, recoverable through GET /logs
- [x] each request logs method/path/status/duration and the *body* does not:
      an analyst's question text is provably absent from the log
- [x] an unwritable log dir does not stop the server
- [x] GET /logs is read-only (a POST to it changes nothing) and clamps lines
- [x] pytest never writes a log file into the repo
TESTS: server/tests/test_logging.py - 12 tests: default location, env override,
       rotation bound, idempotent reconfiguration, unwritable dir, tail reading,
       the 500 traceback round-tripped through /logs, the request line, the
       body-not-logged property, /logs when disabled, line clamping, and no
       repo writes under pytest.
VERIFICATION: `cd server && .venv/bin/python -m pytest -q` green (243 total);
              the P2, P3 and P4 gates still PASS; CI green.
STATE UPDATE: mark P5-OBSERVE-002 done on pass; the P5 checklist's
              observability item is closed.
```

### P5-RELIABILITY-003 contract

```
TASK ID: P5-RELIABILITY-003
MILESTONE: P5 Production Grade
CAPABILITY: Reliability (the carried 500 envelope)
GOAL: A 500 answers the same shape as every other error, and an id that finds
      its traceback.

CONTEXT: P4-RELIABILITY-002 made a fault answer 500 instead of a 400 that
         blamed the analyst, and deliberately declined to change the body -
         Starlette's plain-text "Internal Server Error". The client tolerates
         it (api.ts parses JSON only when the core sent it), but it is the one
         remaining rough edge in the error contract, and P5-OBSERVE-002 just
         put the traceback somewhere an id can point at.
INPUTS: an unhandled exception reaching the middleware stack.
RELEVANT FILES: server/app/main.py (the exception handler), server/app/models.py,
                server/tests/test_error_semantics.py, web/src/api.ts,
                web/src/api.test.ts (NEW), docs/Observability.md,
                ai/ROADMAP.md, ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - A registered handler for `Exception` answers 500 with
    `{"detail": "internal error", "request_id": "<hex>"}`, and logs the
    traceback under that id. Logging matters as much as the envelope: catching
    the exception means uvicorn no longer logs it, so without an explicit
    record the traceback P5-OBSERVE-002 promised would stop reaching the file.
  - The body carries no exception text. A fault's message can quote what it was
    holding - an unknown column, a filename, a value that failed to parse - so
    only the id and a fixed message leave the process. The traceback stays in
    the log, on the user's machine.
  - HTTPException is untouched: a 400/404 still answers its own `detail`.
  - api.ts surfaces the id on ApiError so a user can quote it and the UI can
    say "this is error <id>, it is in the log" instead of "request failed".
NON-GOALS: retry, rate limiting, user-visible log browsing in the shell (the
           endpoint exists; a menu item is a separate UI task), any change to
           the 4xx contract, correlation ids threaded through the request
           middleware (the handler's id is enough for a single-user local tool).
CONSTRAINTS: the status code must stay 500 - the whole point of P4 was that a
             fault is never flattened into a client error - and the P4 gate's
             fault step must still pass.
ACCEPTANCE CRITERIA:
- [x] a fault answers 500 with `detail` and a `request_id`
- [x] the same id is in the log line carrying the traceback
- [x] the exception's own message is in the log and NOT in the body
- [x] a 400 and a 404 are unchanged: their own `detail`, no request id
- [x] the client turns the envelope into an ApiError carrying the id
TESTS: server: the envelope, the id-in-log round trip, the no-leak property,
       and the 4xx contract unchanged. web: 3 tests on api.ts - the 500
       envelope yields an ApiError with the id, a plain 4xx is unchanged, and a
       500 that is not JSON still works (the fallback path the envelope
       replaced).
VERIFICATION: `cd server && .venv/bin/python -m pytest -q` green (256 total);
              `cd web && npm test` green (20 total); P2/P3/P4 gates PASS; CI
              green.
STATE UPDATE: mark P5-RELIABILITY-003 done on pass; the carried item from
              P4-RELIABILITY-002 is closed.
```

### P5-CI-004 contract

```
TASK ID: P5-CI-004
MILESTONE: P5 Production Grade
CAPABILITY: CI floor
GOAL: Make the minimum supported macOS version a real, tested floor rather
      than an assumption.
GOAL NOTE: "just CI refine, target Mac minimal Ventura" - the user asked for
      exactly this and nothing more.
CONTEXT: every job ran on macos-latest, which is whatever GitHub newest is at
         the moment - currently arm64, while the development machine and the
         sidecar triple are x86_64. A green run was therefore a binary nothing
         else in the project ever produced, and the oldest macOS DAH might be
         asked to run on had never been built against at all.
INPUTS: the runner image label.
RELEVANT FILES: .github/workflows/ci.yml, README.md, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - A single MACOS_RUNNER env (macos-13) drives all four jobs, so the floor is
    stated once and a bump touches one line. macos-13 is Ventura and the last
    Intel image, which matches the dev machine and the
    x86_64-apple-darwin sidecar triple.
  - The packaging job's smoke step now asserts the packaged core's file
    logging is on and lands under the data dir it was given - a packaged
    app's stderr is unreadable, so this is the one place the observability
    work is provable in the real PyInstaller bundle rather than a dev
    checkout.
NON-GOALS: arm64 as a second CI lane (real, but a separate task that needs a
           second runner and a second sidecar triple), signing (blocked on the
           Developer ID, DEC-004), any change to the jobs themselves beyond
           the runner and the smoke step, Windows or Linux.
CONSTRAINTS: no job may gain a secret; nothing may stop running on the floor.
ACCEPTANCE CRITERIA:
- [x] all four jobs run on macos-13 and the runner is defined once
- [x] the smoke step fails when the packaged core does not log into its data
      dir (verified locally against a stale binary, which 404'd on /logs and
      failed the new assertions)
- [x] the smoke step passes against a sidecar built from current source
- [x] README states the minimum supported version
TESTS: none new - this task is CI configuration. Verified by running the
       smoke block locally against both the stale sidecar (fails as designed)
       and a freshly built one (passes), and by parsing the workflow YAML.
VERIFICATION: workflow YAML valid; the four jobs' commands unchanged; server
              256 / web 21 / desktop 7 still green locally (this commit moves
              no code).
STATE UPDATE: mark P5-CI-004 done on pass; record the floor in README.
```

### P5-RELEASE-005 contract

```
TASK ID: P5-RELEASE-005
MILESTONE: P5 Production Grade
CAPABILITY: Release automation
GOAL: a versioned artifact a user can download instead of having to build.

CONTEXT: the packaging job in ci.yml already proves the sidecar builds and
         serves on a clean machine, but the output went nowhere - the artifact
         was uploaded for one job and deleted a day later. Three files held
         0.1.0 independently (server/pyproject.toml, web/package.json,
         desktop/package.json, tauri.conf.json) and nothing kept them honest
         with each other or with anything a user would see.
INPUTS: a git tag `v<x.y.z>` whose x.y.z matches server/pyproject.toml.
RELEVANT FILES: .github/workflows/release.yml (NEW), README.md, ai/ROADMAP.md,
                ai/CURRENT_STATE.md, ai/HANDOFF.md
REQUIRED CHANGE:
  - .github/workflows/release.yml: on a `v*` tag, one job on the CI floor -
    read the version from server/pyproject.toml and FAIL if the tag does not
    match it (so a stale version file can never publish a build whose label
    lies), run the server suite, build and smoke the sidecar (health plus the
    packaged-log assertions from P5-CI-004), build the .app with the version
    stamped from the pyproject, ditto-zip it with its architecture in the name,
    shasum it, generate notes that state the unsigned status and the Gatekeeper
    steps, and publish a flagged pre-release with the zip and its checksum.
  - server/pyproject.toml is the single version source of truth; tauri.conf.json
    is patched at build time by --config rather than kept in sync by hand.
NON-GOALS: signing and notarization (DEC-004, blocked on the Developer ID -
           this job has the slot they slot into, between build and upload),
           arm64 or universal builds (a second lane, this machine is x86_64),
           auto-changelog generation, publishing to a package registry,
           releasing from anywhere but a tag.
CONSTRAINTS: no secret is needed - the unsigned build uses only the default
             GITHUB_TOKEN with contents:write; the release must never be
             created from a version mismatch; nothing may publish on a branch
             push.
ACCEPTANCE CRITERIA:
- [x] a tag that disagrees with the pyproject version fails before any build
- [x] the server suite runs inside the release job
- [x] the packaged core is smoked (health + log in the data dir) before packaging
- [x] the .app's version is the pyproject's, not tauri.conf.json's
- [x] the published asset is a zip plus a sha256, with the architecture named
- [x] the release body states it is unsigned, how to open it, and that the
      published build is Intel
- [x] the release is flagged a pre-release
TESTS: none new - this task is a workflow. Verified by running every step it
       runs, locally: the tag-mismatch check (fails as designed), the sidecar
       smoke, `npm run tauri -- build --config '{"version":...}'`, the ditto
       zip, the shasum, and the generated notes. The only step not exercisable
       locally is `gh release create` against GitHub.
VERIFICATION: workflow YAML parses; every command in it was run by hand against
              the current tree; the zip contains a .app whose
              CFBundleShortVersionString is the pyproject version.
STATE UPDATE: mark P5-RELEASE-005 done on pass; the P5 checklist's release item
              is closed, leaving only signing (blocked) on it.
```

### P5-UX-006 contract

```
TASK ID: P5-UX-006
MILESTONE: P5 Production Grade
CAPABILITY: Shell UX
GOAL: A user hits a problem and finds the log without ever opening a terminal.

CONTEXT: P5-OBSERVE-002 made the core write a log next to the user's cases and
         answer GET /logs with its path - but a path inside a JSON body is
         still a terminal answer, and the shell exists precisely because this
         user does not have a terminal open.
INPUTS: the running core on port 8123; GET /logs.
RELEVANT FILES: desktop/src-tauri/src/logs.rs (NEW), desktop/src-tauri/src/main.rs
                (the menu and its handler), desktop/src-tauri/Cargo.toml,
                docs/Observability.md, ai/ROADMAP.md, ai/CURRENT_STATE.md,
                ai/HANDOFF.md
REQUIRED CHANGE:
  - logs.rs owns the bridge: logs_url, LogLocation (File | Disabled),
    parse_log_location, log_location (one GET through the ureq the shell
    already depends on), reveal_in_finder (`open -R`, macOS-native, no new
    dependency) and reveal_core_logs, which is the menu item's whole job.
  - Everything degrades to a sentence rather than an error. A core still
    booting, hung, or older than the endpoint is Disabled - a menu item that
    says "logging is off" beats one that fails when it is needed most - and a
    body that is not the expected shape is Disabled too, so a menu can never
    panic on a body it does not recognise.
  - main.rs: a real macOS menu bar. The app menu keeps About and Cmd+Q, which
    setting any custom menu takes away, Edit keeps the text editing a data
    tool needs, and DAH > Reveal DAH Logs is the one item DAH adds.
NON-GOALS: browsing the log inside the app (the terminal and the file are both
           already fine for that), a web UI button for the same command (the
           browser host has no core-spawned log to reveal), serving the
           rotated backups, anything but macOS (`open -R` is macOS-only, and
           so is the app).
CONSTRAINTS: no new runtime dependency beyond serde_json, which is already in
             the tree through tauri; the existing 7 Rust tests must still pass;
             the menu bar must not lose the standard macOS items.
ACCEPTANCE CRITERIA:
- [x] the menu item exists in the running app's menu bar
- [x] clicking it opens Finder on the log the running core is actually writing
- [x] a core with file logging off yields a stated reason, not a failure
- [x] a malformed or unexpected /logs body cannot panic the menu
- [x] the standard macOS app and Edit menus survive the custom menu
TESTS: 4 unit (enabled/disabled/odd-shape/url) plus 1 e2e that starts the real
       dev core and asserts the reported log is under the data dir the shell
       pointed it at and is a file that exists - 12 Rust tests total, was 7.
VERIFICATION: cargo test --features e2e green; the built app smoke-tested by
              hand - the menu bar introspected with AppleScript, the item
              clicked, and the handler's outcome in the shell log naming the
              real path; the core stopped and the port freed afterwards.
STATE UPDATE: mark P5-UX-006 done on pass; the "Reveal logs" follow-up is
              closed.
```

```
TASK: P5-CI-FIX-007 - repair CI: it had not run for three commits
ID: P5-CI-FIX-007
PRIORITY: high
STATUS: DONE
SUMMARY: CI was silently broken since 5e68fbb (P5-CI-004). Every push failed at
         parse time - 0s, no job ever started, both workflows - reported only as
         "a workflow file issue". Two separate bugs, one hiding the other.
WHAT CHANGED:
- 3ad554b: the immediate cause. P5-CI-004 referenced the runner label as
  `${{ env.MACOS_RUNNER }}` in every job's `runs-on`, and GitHub does not
  expand the `env` context there. Inlined the literal; the env entry and the
  misleading comment went with it. Recorded in both headers why runs-on is a
  literal, because a parse-time failure reports nothing and blocks all jobs at
  once - it had hidden itself for three commits.
- 37c6e16: the deeper cause the first fix exposed. GitHub has retired the
  macos-13 hosted pool, so the Ventura floor P5-CI-004 targeted was never
  provisionable - with the parse bug fixed, the jobs unblocked into a queue
  they never left. A throwaway probe workflow settled it: an identical pair of
  jobs, macos-latest completed in under a minute while macos-13 sat queued with
  zero steps for 18 minutes. All jobs moved to macos-latest; the Ventura floor
  stays documented as the minimum supported macOS but is no longer enforced by
  CI. See DEC-005 for what a green run no longer proves (the Intel triple) and
  what restoring it costs (a self-hosted runner).
- 4dca009: the release job's web install ran `npm ci` in desktop/ only, but the
  Tauri beforeBuildCommand is `npm --prefix ../web run build:desktop` - a
  script in web/package.json whose deps (vite, tsc) live in web/node_modules.
  desktop/ carries only the Tauri CLI, so the prefixed script had nothing to
  run and the build died with exit code 127. Both trees are now installed.
- The release notes no longer assert the build is Intel: the paragraph is
  chosen from the runner's actual triple, so an arm64 or Intel lane both
  describe themselves.
ACCEPTANCE CRITERIA:
- [x] all four ci.yml jobs pass on GitHub's own runners (server + 3 gates, web,
      packaging sidecar smoke, desktop lifecycle incl. both e2e tests)
- [x] release.yml runs end to end from a tag for the first time
- [x] the published zip's sha256 matches its checksum asset
- [x] the .app bundle carries the sidecar and the version the tag verified
VERIFICATION: run 35490199963 four-for-four green; run 35490519483 published
              v0.1.0. `shasum -a 256 -c` OK on the downloaded 79MB zip;
              Info.plist CFBundleShortVersionString 0.1.0; Contents/MacOS/
              carries dah-shell (15MB) and dah-core (78MB).
LESSON: two independent bugs compounded. The `env` context is unavailable in
        runs-on, and that silent parse failure masked a second problem - the
        label it was finally resolving to no longer exists. Fixing a reported
        error is not the same as fixing the underlying state; verify the
        workflow actually *runs*, not merely that it parses. CI visibility had
        been blocked all session, which is how three commits shipped without
        anyone noticing CI had stopped entirely.
```

```
TASK: P6-MEMORY-001 - cross-case recall: let an answer cite previous cases
ID: P6-MEMORY-001
PRIORITY: high
STATUS: DONE
SUMMARY: A case could already cite its own artifacts - runs, datasets, findings -
         via the grounds budget in assistant.py. Nothing let it cite a PREVIOUS
         case: summarize_case read exactly one case's rows, so every
         investigation started from scratch even when the same anomaly was
         found and explained last month. Analysis memory closes that. New
         app/memory.py derives, per question, which prior cases bear on it;
         the assistant can now cite `case:<id>` and the prior finding, both
         validated against real rows.
WHAT CHANGED:
- server/app/memory.py (NEW): summarize_memory is a pure projection over cases
  and findings. Relevance is a shared-content-word count against the question,
  the dataset label and every finding statement, with a hand-written stoplist
  and a threshold of 2 shared words - deliberately not an embedding: no
  dependency, no network, deterministic, and it makes the "nothing bears on
  this" answer honest. A case with no findings is skipped however similar its
  question sounds; there is nothing to recall. Writes nothing.
- server/app/assistant.py: a new KIND_CASE ground and a recall branch in the
  deterministic answer. It fires when the question is *about* prior work
  (before/previous/earlier/...) or when the case has nothing of its own - and
  it sits ahead of the column/dataset branches on purpose, because "what did I
  find before about revenue?" names a column and would otherwise be answered
  with this case's column stats: a true answer to a question nobody asked. A
  case with its own artifacts and no prior framing still gets its own stage.
  _references admits case: and the prior finding's id, so an invented
  cross-case citation is rejected exactly as an invented column is. The LLM
  prompt carries memory and its citation budget names the case kind.
- server/app/main.py: the chat endpoint passes the message to summarize_case,
  because which prior cases are relevant depends on what was asked.
- server/tests/test_memory.py (NEW): 11 tests.
NON-GOALS: replaying another case's result rows (a conversation points at
           evidence, it does not replay it), writing anything on read, a vector
           store (SQLite already holds everything), cloud sync.
CONSTRAINTS held: the P3 honesty budgets survive - a cross-case ground must
             resolve to a real finding in a real other case or be rejected;
             the deterministic path needs no LLM key; nothing logs what the
             analyst typed; no new runtime dependency.
ACCEPTANCE CRITERIA:
- [x] a question whose answer is in another case is answered citing that case
      by name, deterministically (source=deterministic)
- [x] an invented cross-case citation is rejected by validate_answer, exactly
      as an invented in-case ground is
- [x] an answer that no other case supports says so plainly rather than
      dragging in a weakly-related case
- [x] no read path writes; the memory is a projection over existing rows
- [x] the LLM path degrades to deterministic on any failure and records source
- [x] the P4 gate and the full suite stay green; new tests pin every criterion
TESTS: 11 in server/tests/test_memory.py - the headline recall, the cited case
       and finding are real rows, invented case and invented prior finding both
       rejected, an off-topic prior case is not dragged in, a case with its own
       artifacts answers from its own state, an explicit prior question recalls
       anyway, the LLM receives memory and validates, a malformed LLM memory
       answer falls back, recalling writes nothing, and a case is never its own
       previous case.
VERIFICATION: server suite 267 passed (was 256, +11); P4 gate PASS on all 18
              steps and all 10 exit criteria; P3 gate PASS; web 21 passed;
              desktop 12 Rust tests. All green locally.
LESSON: three of the eleven tests failed first run for the same reason - the
        test's own fixture. The helper hardcoded a finding about "revenue" in
        "sales.csv" while the question was about revenue, so an allegedly
        off-topic prior case still shared two content words and was correctly
        recalled. The code was right; the test was asserting a separation its
        own data did not have. A relevance threshold is only as honest as the
        corpus it is measured against - and a fixture that says "weather" while
        quoting "sales" is not a weather fixture.
```

```

### P6-AGENT-002 contract

```
TASK ID: P6-AGENT-002
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Agentic Analysis
GOAL: A plan that executes itself: walk the loop (generate code, run it, read
      the result, iterate, draft a finding) with the human approving each
      write, over the endpoints that already exist.

CONTEXT: every stage of the loop already has a validated endpoint with an
         honesty budget behind it - generate-code (P3-AI-013), runs, interpret
         (P3-AI-011), draft-finding (P3-AI-012), findings, charts, validate.
         What does not exist is the loop driver: a human still clicks through
         one panel at a time. P6-MEMORY-001 landed the recall an agent needs;
         this task is the orchestration over the validated primitives.

INPUTS: a case id (with at least one attached, profiled dataset).
RELEVANT FILES: server/app/agent.py (NEW), server/app/main.py, models.py, db.py,
                server/app/generator.py (variant), server/tests/test_agent.py (NEW)
REQUIRED CHANGE:
  - app/agent.py: a step machine, not a script. Each call to advance() performs
    ONE write or one read-only proposal and returns the next pending step.
    Steps: profile -> plan -> analyze (generate code, then run it) ->
    interpret -> draft -> accept -> chart -> validate -> done. The next step is
    DERIVED from the case's artifacts (the same projection workflow.py uses),
    so an interrupted agent resumes exactly where it stopped and can never
    claim a step the data does not support.
  - main.py: POST /cases/{id}/agent (start/advance), GET .../agent (state),
    POST .../agent/approve {step_id} (the human's yes), POST .../agent/reject
    {step_id, reason?}. Every write step requires an explicit approval id; a
    proposal step (generate code, draft) writes nothing and needs no approval,
    because its endpoints are already stateless by design.
  - The human's decision is recorded, not inferred: an agent_step row holds the
    step, the payload it proposed, the outcome and, for writes, the approval
    that let it run. An agent that was never approved has written nothing.
  - generator.py: generate_code gains an optional `variant` (default 0) so a
    retry proposes a genuinely different query - different measure/dimension
    axis - rather than re-proposing the one that just returned nothing.
NON-GOALS: autonomous write (a write without an approval id is a 500-class
           contract violation, tested as such), a new LLM engine or prompt
           chain (the agent composes the existing deterministic-or-LLM
           primitives and carries their `source` through unchanged), a web UI
           for the agent (the endpoints are the contract; the shell wires
           later), multi-dataset join planning by the agent, retries that
           re-propose identical code.
CONSTRAINTS: every run the agent makes goes through the same read-only gate
             and row cap as a hand-written one - the agent earns no
             privileges; a finding is still created only by POST /findings,
             never by the agent module; the honesty budgets of P3-AI-011..014
             are untouched and still reject an invented magnitude or column at
             the same boundaries; deterministic by default (source records
             which engine each proposal came from); nothing the analyst typed
             is logged; no new runtime dependency; the agent terminates
             (a bounded retry budget, and a case with no usable axis ends at
             a stated reason rather than looping).
ACCEPTANCE CRITERIA:
- [x] starting an agent on a profiled case proposes the plan step and nothing
      has been written
- [x] each write step performs exactly one write and only after its approval
      id is supplied; approving a stale or unknown step id is a 409/404
- [x] an empty first result makes the agent iterate: the next proposal is a
      different query (variant), not the same one
- [x] the retry budget is bounded; exhausting it ends the run at a stated
      reason, not a silent stop and not an infinite loop
- [x] the agent reaches a draft and, on approval, a validated finding - the
      full loop - on a case built through the public API alone
- [x] a case with no usable axis (no repeating numeric, no categorical) ends
      with a stated reason instead of proposing nothing forever
- [x] every step carries the source of the proposal that made it
- [x] no read path writes; the agent's own state is one append-only table
- [x] delete removes the agent state with the case; export carries it
- [x] the full server suite, the P2/P3/P4 gates and the web suite stay green
TESTS: server/tests/test_agent.py - the full happy walk (plan -> analyze ->
       interpret -> draft -> accept -> chart -> validate), write-without-
       approval refused, stale approval id, iteration on an empty result,
       budget exhaustion with a stated reason, no-axis early end, source
       propagation, resumption after interruption, delete cleanup, 404s.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS.
STATE UPDATE: mark P6-AGENT-002 done on pass; ROADMAP item 2 flips to DONE.
```

```
TASK: P6-AGENT-002 - agentic analysis: a plan that executes itself, one approved
write at a time
ID: P6-AGENT-002
PRIORITY: high
STATUS: DONE
SUMMARY: Every stage of the loop already had a validated endpoint with an
         honesty budget behind it. What did not exist was the driver over them:
         a human still walked the panels one click at a time even when the next
         click was never in doubt. The agent is that driver, and it is
         deliberately not an autonomous one. It proposes a step whose payload is
         settled at proposal time; a human approves that step by id; the write
         runs through the endpoint that already owns it. The agent holds no
         privilege a hand-written call lacks.
WHAT CHANGED:
- server/app/agent.py (NEW): a step machine, not a script. next_step() derives
  the one thing to do next as a pure projection over the case's artifacts - the
  same discipline as the workflow stage (P3-FLOW-004) - so an interrupted agent
  resumes exactly where it stopped and can never be ahead of or behind the data.
  Loop order: profile -> plan -> analyze -> interpret -> accept -> chart ->
  validate. `accept` carries the drafter's candidate finding inside its payload,
  because the draft is stateless by design (P3-AI-012) and there is no separate
  draft row to take; `analyze` carries its generate-code proposal the same way.
  An empty result is the one real decision point: the variant rotates so the
  retry is a *different* query, a proposal identical to one already tried is a
  dead end, and three empty attempts end the run at a stated reason rather than
  a silent stop. `end` is a terminal record, not work: it says why the agent
  stopped so an abandoned case falls silent nowhere.
- server/app/generator.py: _pick_axes and generate_code take a `variant` that
  rotates the measure/dimension/period through the usable columns, and the LLM
  retry prompt names the empty attempts so its proposal differs from the one
  that struck out. A family with a single usable column keeps that column, so a
  dataset with no alternative axis produces an identical proposal - which is how
  the caller detects the dead end rather than spending its budget.
- server/app/main.py: four endpoints over one path. GET /agent is strictly
  read-only (a refresh that proposed would commit work the human never saw);
  POST /agent derives and records the next pending step, idempotently;
  POST /agent/approve refuses any id that is not the case's *current* pending
  step with a 409, so a stale page can never cause a second write;
  POST /agent/reject records the analyst's reason and performs no write. Every
  approved step awaits the async endpoint that owns the write, which is what
  keeps the read-only gate, the row cap, the honesty budgets and the single
  finding-creation path in force for an agent-run case.
- server/app/exporter.py: the `agent_steps` section. Export carries the whole
  trail; import remaps the ids a payload cites (dataset, run, finding) to the
  restored case's own artifacts, so a package stands on its own. A package from
  before this task has no such section, so its absence is tolerated rather than
  treated as corruption.
- server/app/main.py duplicate: the trail travels with the copy, citing the
  copy's own rows - an agent-proposed finding keeps the approvals that let it
  run. Delete already removed it with the case.
- server/app/db.py: the `agent_steps` table, one row per step, created with the
  others under IF NOT EXISTS so older databases migrate in place.
- server/app/models.py: AgentStep, AgentState, AgentApproval.
- server/tests/test_agent.py (NEW): 24 tests.
NON-GOALS held: no autonomous write (an approval is required for every one, and
             approving a stale id is a 409 tested as such), no new LLM engine or
             prompt chain (the agent composes the existing deterministic-or-LLM
             primitives and carries each one's `source` through unchanged), no
             web UI for the agent, no multi-dataset join planning, no retry that
             re-proposes identical code.
CONSTRAINTS held: the agent's SQL passes the same read-only gate and row cap as
             a hand-written one; a finding is still created only by the findings
             endpoint, never by the agent module; the honesty budgets of
             P3-AI-011..014 are untouched; deterministic by default with `source`
             recorded at every step; nothing the analyst typed is logged; no new
             runtime dependency; the agent terminates (bounded budget, and a
             case with no usable axis ends at a stated reason).
ACCEPTANCE CRITERIA: all 10 - see the checked boxes above.
TESTS: 24 in server/tests/test_agent.py - the full happy walk to a validated
       finding, the seven kinds in loop order, write-without-approval refused,
       stale and unknown approval ids 409, rejection recording its reason and
       writing nothing, iteration to a different query on an empty result,
       budget exhaustion at a stated reason with three distinct queries, the
       no-axis early end, source propagation, resumption after interruption,
       the state never being ahead of the data, idempotent proposal, GET writing
       nothing, export carrying the trail, the import round trip with remapped
       references, an older package without the section, delete cleanup, the
       duplicate keeping a remapped trail, and the one-row-per-step invariant.
VERIFICATION: server suite 291 passed (was 267, +24); web 21 passed; desktop 12
              Rust tests; P2, P3 and P4 gates all PASS. All green locally; CI
              will run it on push.
LESSON: two of the first 24 tests failed on the first run and both were the
        tests' fault, not the code's. One asserted an import answers 200 when
        the endpoint answers 201; one ended with a leftover `del json` line that
        crashed at assertion time. Neither was a behaviour bug, and both were
        found only because the test ran - which is the smaller lesson, that a
        test file is itself untested code until its own suite is green. The
        larger one is the same one the memory task recorded: verify the
        assertion against the real contract, not against the shape you assumed
        while writing it.
```

### P6-TEMPLATE-003 contract

```
TASK ID: P6-TEMPLATE-003
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Case reuse
GOAL: Promote a finished investigation into a reusable template carrying its
      analytical shape - its plan, its proposals and how its findings validated
      - not just its question, and let a case started from it inherit that shape
      as validated starting proposals.

CONTEXT: P3-CASE-007 shipped templates that copy the question and the dataset
         label alone. The template machinery exists; the investigation does not
         travel with it, so "same analysis, new month's file" still means
         re-deriving the plan and re-typing the query that worked last time.
         The plan, the proposals and the finding outcomes are all already on
         disk; nothing new needs to be computed to carry them.

INPUTS: a case with a plan, runs and/or findings.
RELEVANT FILES: server/app/main.py, server/app/models.py, server/app/db.py,
                server/app/exporter.py, server/tests/test_case_templates.py
REQUIRED CHANGE:
  - promotion captures a shape: a pure projection over the case's artifacts -
    its latest plan and which engine produced it, the code proposals its agent
    run made (falling back to its runs when the case was hand-run), and its
    findings' statements with their validation status. A case with nothing to
    carry promotes a shapeless template and behaves exactly as before.
  - the template row gains a nullable shape_json; the Template model exposes it.
  - a case created from a template records its lineage (template_id), so the
    case knows where it came from rather than the connection being implicit.
  - the plan step prefers the template's plan when the case has one and has no
    plan of its own yet, validated through the same validate_plan and falling
    back to the normal derivation on any problem, with source recorded as
    "template" so a reviewer sees the plan came from history, not this dataset.
  - generate-code prefers a template proposal whose every column exists in the
    profiled dataset - the profile check is what makes a historical proposal
    safe to offer against different data - and falls back to the generator
    otherwise, again recording source="template".
  - export carries the lineage; import preserves it; duplicate keeps it.
NON-GOALS: copying data, runs, findings or charts into the templated case (it
           still starts clean; the shape is proposals a human accepts, not
           artifacts it inherits), reusing a proposal that names a column the
           new dataset lacks, autonomous application of a shape (every write
           is still a POST the human makes), a template editor, sharing
           templates between installs.
CONSTRAINTS: the honesty budgets are untouched - a reused plan is still just a
             plan, and a draft or interpretation still only quotes numbers the
             actual run produced; a shapeless or missing template degrades to
             the existing deterministic path with no error; nothing the
             analyst typed is logged; no new runtime dependency; the existing
             template tests must pass unmodified.
ACCEPTANCE CRITERIA:
- [x] promoting a case with a plan, runs and findings captures all three in the
      shape
- [x] promoting an empty case yields a shapeless template indistinguishable
      from today's
- [x] a templated case starts clean and records its template id
- [x] the plan step offers the template's plan, validated, with source=template
- [x] a malformed or missing template plan falls back to derivation
- [x] generate-code offers a template proposal only when every column it reads
      exists in the profiled dataset, with source=template
- [x] a proposal naming a column the new dataset lacks is never offered; the
      generator answers instead
- [x] every shape-derived answer records source=template
- [x] a shapeless older template still promotes, lists and instantiates
- [x] deleting a template a case points at degrades to the normal path, not an
      error
- [x] export/import and duplicate carry the lineage
- [x] the full server suite, the P2/P3/P4 gates and the web suite stay green
TESTS: server/tests/test_case_templates.py - shape capture for a finished case,
       a shapeless promotion, lineage recorded on instantiation, the plan step
       preferring the template plan, the fallbacks, a proposal accepted and
       refused by column existence, source propagation, a deleted template
       degrading, the export/import and duplicate round trips, and the
       unmodified existing behaviours.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS.
STATE UPDATE: mark P6-TEMPLATE-003 done on pass; ROADMAP item 3 flips to DONE.
```
```
TASK: P6-TEMPLATE-003 - templates carry the analytical shape of a finished case
ID: P6-TEMPLATE-003
PRIORITY: high
STATUS: DONE
SUMMARY: P3-CASE-007 shipped templates that copied the question and the dataset
         label alone, so "same analysis, new month's file" still meant
         re-deriving the plan and re-typing the query that worked last time. A
         template now carries the *shape* of a finished investigation too, and
         a case started from it inherits that shape as validated starting
         proposals - not as artifacts, and never applied without a human.

Five pieces, all projections over what is already on disk:

- **`_capture_shape` (main.py)** - a pure projection, nothing computed. The
  case's latest plan and which engine produced it; the code proposals its
  agent run made, falling back to its runs when a human drove the case; and
  its findings' statements with the verdicts validation already gave them. A
  case with none of these promotes the shapeless skeleton it always promoted
  and behaves exactly as before.
- **`templates.shape_json` + `cases.template_id` (db.py, models.py)** - the
  shape has somewhere to live and a case knows where it came from. Both
  nullable, both added to `_ensure_column`, so an older database migrates in
  place.
- **the plan step** prefers the template's plan when the case has none of its
  own, validated through the same `validate_plan` and falling back to the
  normal derivation on any problem, with `source="template"` so a reviewer
  sees the plan came from history rather than this dataset.
- **generate-code** prefers a template proposal only when every column it
  reads exists in the profiled dataset - that profile check is what makes a
  historical proposal safe to offer against different data - and falls back
  to the generator otherwise, again recording `source="template"`.
- **exporter.py** - the lineage travels with the package, import preserves it,
  and a duplicated case keeps it.

Two real bugs the tests found. `SOURCE_TEMPLATE` was referenced in two
helpers but its definition silently never landed, so the first request to a
templated case's plan step raised a `NameError` - a compile-time name in a
module that imports cleanly is still a runtime error when the path is never
exercised, and only a test that walked the path caught it. And hand-run
cases' proposals captured `columns_used: []`, which made the column-existence
safety check pass *vacuously* - a template query could be offered against a
dataset lacking its columns, which is exactly the one thing the check existed
to prevent. Proposals now compute their reach at capture time through
`generator._columns_referenced`, so a hand-run proposal carries the same
reach an agent's does. A guard that is never fed the data it guards is not a
guard.

NON-GOALS held: no data, runs, findings or charts are copied into a templated
             case (it starts clean; the shape is proposals a human accepts),
             no proposal naming a column the new dataset lacks is ever
             offered, no shape is applied autonomously (every write is still a
             POST the human makes), no template editor, no cross-install
             sharing.
CONSTRAINTS held: the honesty budgets are untouched (a reused plan is still
             just a plan, and a draft or interpretation still only quotes
             numbers the actual run produced); a shapeless, malformed or
             deleted template degrades to the existing deterministic path with
             no error; nothing the analyst typed is logged; no new runtime
             dependency; the 10 existing template tests pass unmodified.
ACCEPTANCE CRITERIA: all 12 - see the checked boxes above.
TESTS: 11 appended to server/tests/test_case_templates.py (21 total, the first
       10 unmodified) - shape capture for a finished case, a shapeless
       promotion, lineage recorded on instantiation, the plan step preferring
       the template plan, both fallbacks, a proposal accepted and refused by
       column existence, source propagation, a deleted template degrading, and
       the export/import and duplicate round trips.
VERIFICATION: server suite 302 passed (was 291, +11); P2, P3 and P4 gates all
              PASS (the P4 gate re-ran the suite at 302); web 21 passed;
              desktop 12 Rust tests. All green locally; CI will run it on push.
LESSON: a safety check whose input is collected at the wrong moment is a
        safety check that does not run. `columns_used` was captured empty for
        hand-run cases, so the column-existence gate passed vacuously and would
        have offered a template's query against a dataset that lacked its
        columns - the single failure the gate was written to prevent. The guard
        was in the right place; the data never reached it. Any check over a
        historical artifact must be verified against the path that created the
        artifact, not only against the path that consumes it.

```

### P6-MIGRATE-004 contract

```
TASK ID: P6-MIGRATE-004
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Maintainability
GOAL: Give the store a versioned, forward-only migration path, so a database
      written by any past release is brought to the current shape by a recorded
      chain of named migrations - and the app can state which shape it opened.

CONTEXT: the store grew by seven `_ensure_column` in-place additions across
         P2-P6, each guarded and each correct, but nothing records which of them
         a given database has had. There is no version number anywhere in the
         file, so no code can tell "is this store current?" - it can only probe
         for each column and hope. That was tolerable while the schema only ever
         gained nullable columns; it stops being tolerable the moment a task
         renames, splits or backfills anything, which is exactly what P6's
         remaining items (memory tables, release metadata) are about to do.

INPUTS: a SQLite store at DAH_DB_PATH, of any age (including one written by a
        release older than this task, which has no version recorded at all).
RELEVANT FILES: server/app/db.py, server/app/main.py, server/app/models.py,
                server/tests/test_migrations.py (NEW)
REQUIRED CHANGE:
  - a schema version number lives in the file itself, via SQLite's
    `user_version` (stored in the header, so it survives without a table), and
    a `schema_migrations` row records each migration actually applied, with its
    name and timestamp - the audit trail the `_ensure_column` list could never
    give. A fresh store records nothing: it was created whole at the current
    shape and nothing was applied to it, which is the truth.
  - an ordered `MIGRATIONS` list; each entry is a version, a name and a call.
    The seven historical additions become migrations 1-7, still guarded, so a
    store at any intermediate state converges instead of erroring on a column
    it already has. Migration N runs only when the recorded version is below N.
  - opening a store upgrades it in place, one migration per transaction, the
    version advanced after each; a failure mid-chain leaves a consistent store
    at the last good version, and the next open resumes from there rather than
    restarting. That resumability is the property that makes an in-place
    upgrade safe to run at request time.
  - the store refuses to operate against a version NEWER than the app knows
    (an older binary opening a newer store), rather than silently treating it
    as current; a downgrade against a schema it does not understand is how data
    is corrupted quietly.
  - `GET /schema-version` reports the recorded version, the target, and the
    applied migrations - the one way a user can ask "is my data safe with this
    build", and the answer a release note can point at.
NON-GOALS: down migrations (the store is forward-only, always; a local
           single-user database's rollback path is a backup, not a second
           schema to maintain and get wrong), destructive or backfilling
           migrations (this task establishes the mechanism; the first migration
           that moves data is a later one), online/rolling upgrades across a
           server fleet (one process, one store), a migration CLI (the app
           upgrades on open; a CLI is ceremony for a single-user tool).
CONSTRAINTS: an upgrade runs on the ordinary open path, so it must be
             idempotent (running it on an already-current store is a no-op that
             writes nothing), fast on the warm path (one PRAGMA read), and safe
             to interleave with reads; existing rows survive every migration
             unmodified; no existing test may change; nothing the analyst typed
             is logged; no new runtime dependency; a store written by v0.1.0 -
             which has no version and a pre-migration shape - must open, upgrade
             and work, because that is the one store that actually exists in the
             wild.
ACCEPTANCE CRITERIA:
- [x] a fresh store is created at the current version with an empty migration
      table, without running the historical ALTERs
- [x] a store written by a pre-migration release upgrades to the current shape
      and every historical column is present afterwards
- [x] existing rows survive the upgrade, byte for byte in value
- [x] reopening a current store is a no-op: version unchanged, no new migration
      rows, no writes
- [x] a partially-upgraded store (some migrations applied, version recorded
      mid-chain) resumes from where it stopped and reaches the current shape
- [x] a store claiming a version newer than the app is refused with a clear
      error, not silently downgraded
- [x] a fresh store and an upgraded store have identical table shapes - the
      schema and the migration chain agree
- [x] `GET /schema-version` reports the recorded version, whether it is
      current, and the applied migrations
- [x] the full server suite, the P2/P3/P4 gates and the web suite stay green
TESTS: server/tests/test_migrations.py - the fresh-store baseline, the legacy
       upgrade over a store built with the pre-migration schema, row survival,
       the no-op reopen, mid-chain resumption, the newer-than-app refusal, the
       fresh-vs-upgraded shape equivalence across every table, and the endpoint.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS.
STATE UPDATE: mark P6-MIGRATE-004 done on pass; ROADMAP item 4 flips to DONE.
```

```
TASK: P6-MIGRATE-004 - a versioned, forward-only migration path for the store
ID: P6-MIGRATE-004
PRIORITY: high
STATUS: DONE
SUMMARY: The store grew by seven ad-hoc `_ensure_column` additions across P2-P6.
         Each was guarded and each was correct, but nothing anywhere recorded
         which of them a given database had received. There was no version
         number in the file, so no code could answer "is this store current?" -
         it could only probe for each column and hope. That was tolerable while
         the schema only ever gained nullable columns; it stopped being
         tolerable the moment a task needed to rename, split or backfill
         anything, which is exactly what P6's remaining items do.

Four pieces, all in `server/app/db.py`:

- **The version lives in the file itself**, via SQLite's `PRAGMA user_version`.
  It is stored in the database header rather than a table, so it is readable
  before the schema exists and survives a crash that leaves tables half-made.
  `LATEST_SCHEMA_VERSION` is the shape this build understands.
- **`MIGRATIONS`** - an ordered, named, forward-only chain. The seven
  historical additions become migrations 1-7, still guarded, so a store at any
  intermediate state converges instead of erroring on a column it already has.
  Migration N runs only when the recorded version is below N. Entries are
  appended, never edited or renumbered.
- **`_migrate`** - one transaction per migration: the change, its audit row in
  `schema_migrations` and its version stamp land together or none of them does.
  A failure mid-chain leaves a consistent store at the last good version and
  the next open resumes there. Idempotent: a current store runs no migration
  and writes nothing but the pragma read.
- **`GET /schema-version`** - the one place to ask whether the local data is
  safe with the build being run. It reports the recorded version, the target,
  whether they match, and the audit trail. Read-only.

Two deliberate behaviours worth stating. A store whose recorded version is
*above* what this build knows is refused with a clear `SchemaVersionError`
naming both numbers, never silently treated as current - an older binary
writing against a schema it does not understand is how a store is corrupted
quietly. And a store created by this build is stamped current with an empty
migration table, because the truth is that nothing was applied to it: it was
born current. The audit trail records what *ran*, not a padding of entries that
never did.

One real constraint the implementation had to respect: SQLite refuses to add a
`NOT NULL` column to a table that already has rows unless the statement carries
a default. So `datasets.format` migrates as `TEXT NOT NULL DEFAULT 'unknown'`
and `profiles.duplicate_rows` as `INTEGER NOT NULL DEFAULT 0`, and SCHEMA
declares the same defaults so that a fresh store and an upgraded store are
identical - not merely compatible. A test pins that equivalence across every
table, because "the two agree by construction" is exactly the kind of claim
that silently stops being true when the next migration lands.

NON-GOALS held: no down migrations (forward-only, always; a local single-user
             store's rollback path is a backup, not a second schema to maintain
             and get wrong), no destructive or backfilling migration (this task
             establishes the mechanism; the first migration that moves data is
             a later one), no online/rolling upgrade across a fleet (one
             process, one store), no migration CLI (the app upgrades on open).
CONSTRAINTS held: an upgrade runs on the ordinary open path and is idempotent
             (a current store writes nothing but a pragma read), fast on the
             warm path, and safe to interleave with reads; existing rows survive
             every migration unmodified (verified against the real dev store,
             34 cases); no existing test changed; nothing the analyst typed is
             logged; no new runtime dependency; the v0.1.0 store - no version,
             pre-migration shape - opens, upgrades and works, because that is
             the one store that exists in the wild.
ACCEPTANCE CRITERIA: all 9 - see the checked boxes above.
TESTS: 13 in server/tests/test_migrations.py - the fresh-store baseline, the
       legacy upgrade over a store built with the pre-migration schema, the
       audit trail, row survival, the no-op reopen, mid-chain resumption, the
       newer-than-app refusal, fresh-vs-upgraded shape equivalence across every
       table, the endpoint, and the empty-legacy edge.
VERIFICATION: server suite 315 passed (was 302, +13); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 315); web 21 passed; desktop 12
              Rust tests. All green locally; CI will run it on push. The real
              dev store was upgraded in place as a live check, not only a
              synthetic one: 34 cases intact, 7 migrations recorded.
LESSON: the first version of `_migrate` decided "is this store new?" by counting
        tables - after running SCHEMA, which creates the `schema_migrations`
        table. Every newborn store therefore looked like an old one that needed
        the whole chain, and three tests failed on the empty-audit-trail
        assertion. The fix was to decide emptiness *before* creating anything.
        The general shape: a freshness check that runs after the thing it
        detects has been created cannot detect freshness. State inspected for a
        decision must be read before the action that would change it - the same
        lesson as P6-TEMPLATE-003's `columns_used`, in a different costume.

```

### P6-UPDATE-005 contract

```
TASK ID: P6-UPDATE-005
MILESTONE: P6 Post-Launch Evolution
CAPABILITY: Distribution
GOAL: A new release tag reaches an installed app: the app says a newer build
      exists and puts the download in front of the user, and when it cannot
      know, it says so instead of claiming the app is current.

CONTEXT: the release pipeline now publishes a versioned build per tag, but an
         installed app has no way to learn that. Two facts constrain what is
         buildable now, and both are already decisions rather than gaps: the
         repository is PRIVATE (an unauthenticated release-feed request answers
         404, verified), and the app is UNSIGNED (DEC-006), so an update payload
         cannot be signature-verified and a self-replacing updater cannot be
         tested end to end. So the task delivers the half that is verifiable -
         the check - and leaves the install half as a documented slot, exactly
         as DEC-004/006 left signing.

INPUTS: the version this build was published at; a release feed.
RELEVANT FILES: server/app/updates.py (NEW), server/app/main.py,
                server/app/models.py, server/tests/test_updates.py (NEW),
                desktop/src-tauri/src/updates.rs (NEW),
                desktop/src-tauri/src/main.rs, .github/workflows/release.yml
REQUIRED CHANGE:
  - the core learns its own version, one source of truth: the version the
    release workflow already stamps from server/pyproject.toml. Resolved by
    importlib.metadata when installed or bundled, falling back to reading the
    pyproject beside the source in a dev checkout, and finally to "unknown" -
    never to a guessed number.
  - server/app/updates.py: pure functions. `parse_version` and
    `is_update_available` (semver-style tuple comparison, no dependency), and
    `latest_release` over an injected HTTP client, so the parsing and the
    comparison are tested without a network and the transport is a seam.
  - GET /updates/latest: read-only, no body accepted, nothing the caller
    supplies is written anywhere. It answers one of three truths:
    `current` (the feed named a version and it is not newer),
    `available` (it named a newer one, with its tag, its page URL and the
    published notes), or `unknown` - and `unknown` carries a reason: the feed
    was unreachable, the repository is private, the rate limit was hit, or the
    body was not the shape expected. An unknown answer is never reported as
    current, because "could not check" and "is up to date" are different
    statements and only one of them is true.
  - the shell bridges it the way it bridges /logs: a DAH > Check for
    Updates... menu item asks the core, opens the release page in the user's
    browser when one exists, and otherwise shows the reason it could not tell.
    It degrades to a sentence rather than an error at every step, and never
    panics on a body it does not recognise.
  - release.yml publishes the version, the page URL and the notes the check
    reads, so the feed and the pipeline cannot drift apart.
NON-GOALS: a self-replacing updater (unsigned builds cannot verify a payload,
           DEC-006; tauri-plugin-updater slots in when signing does, and the
           check it would consume is what this task builds), background or
           scheduled checks (a single user does not need a poller burning
           battery and network; the menu item is the trigger), auto-download
           or auto-install, a channel/staging mechanism (one release stream),
           update notifications in the web bundle.
CONSTRAINTS: the check is read-only and makes no authenticated request - no
             token is shipped and none ever can be, so a private repository is
             answered with `unknown` and a reason, never with a silent guess;
             the network call is bounded by a timeout so a hung feed cannot
             freeze a menu; nothing the analyst typed is logged; no new runtime
             dependency (httpx is already in the tree; the browser opens
             through `open`, as the reveal-logs menu already does, so the shell
             gains no crate); the existing test suites stay green and hermetic.
ACCEPTANCE CRITERIA:
- [x] the core resolves its own version from the pyproject, and the endpoint
      reports it, never a guess
- [x] a newer published version is reported as available with its tag, its
      page URL and its notes
- [x] an equal or older published version is reported as current
- [x] an unreachable or private feed is reported as unknown WITH a reason, and
      never as current
- [x] a rate-limited feed and a malformed body are each reported as unknown
      with their own reason
- [x] the comparison is a pure function, tested without a network
- [x] the endpoint is read-only: it accepts no body and writes nothing
- [x] the menu item opens the release page when an update exists and shows a
      sentence when it cannot tell
- [x] the shell degrades on every failure path, including a body it does not
      recognise, without panicking
- [x] release.yml publishes the fields the check reads
- [x] the full server suite, the P2/P3/P4 gates, the web suite and the desktop
      tests stay green
TESTS: server/tests/test_updates.py - version resolution, the pure comparison
       across older/equal/newer and malformed inputs, the three feed outcomes
       and every failure reason, each driven through an injected client so no
       test touches a network; desktop/src-tauri unit tests for the parse and
       the degradation table.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS;
              cd desktop/src-tauri && cargo test PASS.
STATE UPDATE: mark P6-UPDATE-005 done on pass; ROADMAP item 5 flips to DONE and
              P6 closes.
```

```
TASK: P6-UPDATE-005 - a new release tag reaches an installed app
ID: P6-UPDATE-005
PRIORITY: high
STATUS: DONE
SUMMARY: The release pipeline publishes a build per tag, but an installed app
         had no way to learn that. This task delivers the half of an update
         flow that is verifiable today: the app says a newer build exists and
         puts its download page in front of the user - and when it cannot know,
         it says so, instead of claiming the app is current.

Two facts decided the scope, and both are recorded decisions rather than gaps:
the repository is **private**, so an unauthenticated release-feed request
answers 404 (verified, not assumed), and the app is **unsigned** (DEC-006), so
an update payload cannot be signature-verified and a self-replacing updater
cannot be tested end to end. A full `tauri-plugin-updater` integration would
have been unverifiable code claiming a capability it cannot prove. The check
ships; the install slots in when signing does, exactly as DEC-004/006 left
signing itself.

Three pieces:

- **`server/app/updates.py` (new)** - the honest core of it. `parse_version` and
  `is_update_available` are pure functions (semver-style tuple comparison, no
  dependency, tolerant of a leading `v` and a pre-release suffix); `latest_release`
  runs over an *injected* HTTP client, so the parsing is tested without a
  network and the transport is a seam. `check_for_update` answers one of three
  truths - `current`, `available`, or `unknown` - and `unknown` always carries a
  reason: the feed was unreachable, the repository may be private, the rate
  limit was hit, or the body was not the shape expected.
- **`GET /updates/latest`** - read-only, GET-only, unauthenticated, accepts no
  body and writes nothing. The core resolves its own version from the pyproject
  (importlib metadata when installed or bundled, the file beside the source in a
  dev checkout, then "unknown" - never a guessed number).
- **`desktop/src-tauri/src/updates.rs` (new)** - the bridge, shaped exactly like
  the reveal-logs menu it sits beside: it asks the core, opens the release page
  in the browser through `open` when one exists, and otherwise shows the
  sentence. **DAH > Check for Updates...** is the menu item. Every failure path,
  including a body it does not recognise, degrades to a sentence rather than
  panicking.

The property the tests actually pin is not "does it find an update" but "does
it tell the truth". An unreachable feed, a 404, a 403, a 503, a non-JSON body, a
body without a tag and a transport timeout are each `unknown` with their own
reason - never a silent `current`, because "could not check" and "is up to
date" are different statements and only one of them is true. Verified live
against the real private repository: the answer is `unknown`, "the release feed
is not reachable; the repository may be private" - the honest one, and it
answers properly the day the repository goes public with no code change.

NON-GOALS held: no self-replacing updater (unsigned builds cannot verify a
             payload, DEC-006; the plugin slots in when signing does, and the
             check it would consume is what this task builds), no background or
             scheduled checks (a single user does not need a poller), no
             auto-download or auto-install, no channel mechanism, no web-bundle
             notification surface.
CONSTRAINTS held: read-only and unauthenticated - no token is shipped and none
             ever can be, so a private repository is a *state to report*; the
             network call is bounded by a timeout so a hung feed cannot freeze
             a menu; nothing the analyst typed is logged; no new runtime
             dependency (httpx was already in the tree, and the browser opens
             through `open` as the reveal-logs menu already does, so the shell
             gains no crate); the existing suites stayed green and hermetic -
             every feed outcome in the tests is driven through the injected
             client, so no test touches a network.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 21 in server/tests/test_updates.py - version resolution, the pure
       comparison across older/equal/newer and malformed inputs, and every feed
       outcome and failure reason through the injected client; 7 in
       desktop/src-tauri/src/updates.rs - the parse table and the degradation
       cases, including a body that is not JSON and a newer build with no page.
VERIFICATION: server suite 336 passed (was 315, +21); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 336); web 21 passed; desktop 22
              Rust tests (19 unit + 3 e2e, was 12). The live check against the
              real private repository was run by hand and answered `unknown`
              with the private-repository reason, not a false "current".
LESSON: two of the first tests failed for the same reason, and it was the
        tests' fault both times. The endpoint holds its own *imported* reference
        to `httpx_client` (`from app.updates import httpx_client`), so
        monkeypatching `updates.httpx_client` patched a name the endpoint had
        already copied - the call escaped the fake and hit the real network.
        The seam is the module the call site reads, not the module the symbol
        came from. The same misreading produced the second failure: the test
        passed `json=` to a GET, asserting a property ("no body accepted") that
        a GET cannot even express. The real property is that the route is
        GET-only, so a POST is refused with 405 before any handler runs - and
        that is what the test now asserts. A test that fails because it
        misstates the contract is still a test failure worth having, but the
        contract is verified against the route, not against an assumption about
        it.

```

### P7-SHELL-002 contract

```
TASK ID: P7-SHELL-002
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A user can hand DAH work that came from elsewhere and read the nine-axis
      audit without a terminal. POST .../evaluate answers nine verdicts and
      nothing in the shell reaches it today; this task puts a surface in front
      of it.

CONTEXT: P7-EVAL-001 shipped the core half of EVALUATE mode. The web shell
         walks the ANALYZE loop one panel per step - data, runs, findings,
         chat - and every one of those panels posts to the endpoint that owns
         its write. The evaluate endpoint is the first endpoint with no panel
         at all, and it is the flagship capability of the phase, so closing
         that one gap is the slice of the web-shell work that pays first. The
         other un-UI'd endpoints (the agent, templates, memory, EDA, the
         evidence graph, case history, case management) are later tasks in the
         same checklist item, not this one.

INPUTS: a case with at least one attached, profiled dataset; the artifact's
        code, its kind (SQL or Python) and the claim it was offered to support,
        typed or pasted.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `AxisFinding` and `Evaluation` interfaces matching the
    core's models, plus `evaluateDataset(caseId, datasetId, code, claim, kind)`
    and `listEvaluations(caseId, datasetId)`. Failures travel as `ApiError`, so
    a 400's `detail` and a 500's `request_id` reach the panel unchanged - the
    existing error contract, not a new one.
  - web/src/CaseWorkspace.tsx: an `EvaluatePanel`, shown once the case has a
    profiled dataset (an unprofiled case has no columns to audit against, and
    the panel says so rather than offering a submission that cannot succeed).
    A kind toggle between SQL and Python, a textarea for the code, an input for
    the claim, and a submit that posts to the evaluate endpoint and nothing
    else. The audit renders as nine rows, one per axis in the spec's order,
    each with its verdict as a badge - pass / concern / fail - and its sentence;
    the verdict is the summary and the sentence is the substance, so neither is
    rendered without the other. Audits already recorded over that dataset are
    listed below, newest first, so an audit is itself inspectable from the
    workspace the way a run is.
  - The panel degrades rather than breaking: a 400 (a non-read-only artifact,
    an empty code or claim, an unknown kind) shows the core's own message
    inline and the panel stays usable, because that message is the actionable
    thing - "only single read-only SELECT queries are supported" tells the
    user what to change. A 500 shows the message with its request id, as every
    other panel does.
  - When the case has several datasets the panel offers a chooser, because the
    axis verdicts are per-dataset - an artifact audited against the wrong file
    would fail every column check for a reason that is not the artifact's.
NON-GOALS: ingesting a whole notebook, dashboard, spreadsheet or report as a
           file (this task takes the code and the claim, the common core, as
           P7-EVAL-001 did), editing or re-running a past audit's artifact (the
           artifact is already stored as a run and appears in the Runs panel),
           a chart or score over the audit (the core deliberately returns no
           score), an LLM phrasing of the verdicts (deterministic, as the core
           is), a mode switcher that reorganises the workspace around ANALYZE /
           EVALUATE / LEARN (the workspace is ANALYZE's loop; EVALUATE is a
           labelled panel beside it, and a mode architecture is a later
           design), the other un-UI'd endpoints (each is its own task).
CONSTRAINTS: every write posts to the evaluate endpoint - the panel proposes
             nothing else and creates no run, finding or chart of its own;
             deterministic; no new dependency; the existing panels and their
             tests are unchanged; `tsc -b` passes (the build is CI's type gate,
             and a type error the jsdom tests cannot see fails it); the desktop
             bundle builds from the same source, so nothing may assume a
             browser-only environment; nothing the analyst typed is logged by
             the core (P5-OBSERVE-002) and the shell adds no logging of its
             own; the server suite and the gates are untouched by this change
             and stay green.
ACCEPTANCE CRITERIA:
- [x] a case with a profiled dataset shows the EVALUATE panel; a case with no
      dataset or no profile does not
- [x] submitting clean work shows all nine axes, each with a pass verdict and
      its sentence, in the spec's order
- [x] a claim quoting a magnitude the run does not contain shows a fail on
      Evidence, with the value and the sentence
- [x] a non-read-only artifact shows the core's 400 message inline; the panel
      stays usable and no audit was recorded
- [x] an audit is recorded and listed afterwards, newest first, with its claim
      and its nine verdicts
- [x] the kind toggle switches the submission between SQL and Python
- [x] a failed request never crashes the workspace: the error is a sentence
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the clean nine-axis baseline, the
       invented magnitude on Evidence, the read-only refusal rendered as a
       sentence, the recorded audit listed newest first, the panel's absence
       without a profiled dataset, and the kind toggle.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS (tsc -b
              runs first, so a type error the jsdom tests cannot see fails
              it). The server suite and the three gates are unchanged.
STATE UPDATE: mark P7-SHELL-002 done on pass; ROADMAP item 2 records EVALUATE's
              surface as delivered.
```


```

TASK: P7-SHELL-002 - EVALUATE mode in the web shell
ID: P7-SHELL-002
PRIORITY: high
STATUS: DONE
SUMMARY: The core half of EVALUATE mode shipped with P7-EVAL-001 and nothing
         in the shell could reach it. The web workspace walks the ANALYZE loop
         one panel per step - data, runs, findings, chat - and the evaluate
         endpoint was the first one with no panel at all, in the phase whose
         flagship capability it is. This task puts a surface in front of it
         without adding a single endpoint, contract or dependency: the panel
         only renders what the core already answers.

Two files of substance:

- **`web/src/api.ts`** - `AxisFinding` and `Evaluation` interfaces matching the
  core's models, and the two functions the panel needs: `evaluateDataset` (the
  submission) and `listEvaluations` (so an audit is inspectable after the fact,
  the way a run is). Failures travel as `ApiError`, so a 400's `detail` and a
  500's `request_id` reach the panel unchanged - the error contract the rest of
  the shell already uses, not a new one.
- **`web/src/CaseWorkspace.tsx`** - an `EvaluatePanel` placed after the loop it
  audits and before the assistant. It appears once a dataset is profiled (an
  unprofiled case has no columns to audit against, so the panel says so rather
  than offering a submission that cannot succeed); offers a kind toggle, a code
  textarea and a claim input; and renders nine rows - one per axis in the
  spec's own order - each a verdict badge and its sentence, because the verdict
  is the summary and the sentence is the substance and neither is rendered
  without the other. Recorded audits list below, newest first. With several
  datasets there is a chooser, because the verdicts are per-dataset and an
  artifact audited against the wrong file fails every column check for a reason
  that is not the artifact's.

The panel holds to the discipline every other panel keeps: the submit posts to
the evaluate endpoint and nothing else. The panel never runs code and never
decides whether work is sound - the endpoint does, under the same read-only
gate, row cap and hard sandbox as any other run. A 400 is part of the contract
rather than a failure: a non-read-only artifact is refused before anything
executes, and its detail ("only single read-only SELECT queries are supported")
is shown as a sentence next to a panel still ready for corrected work.

NON-GOALS held: no whole-file ingestion of notebooks, dashboards or
             spreadsheets (the code and the claim, as P7-EVAL-001 took them),
             no editing or re-running a past audit's artifact (it is already a
             run, in the Runs panel), no chart or score over the audit (the core
             returns neither), no LLM phrasing of verdicts, no mode switcher
             reorganising the workspace around ANALYZE/EVALUATE/LEARN - the
             workspace is ANALYZE's loop and EVALUATE is a labelled panel
             beside it; a mode architecture is a later design, and the other
             un-UI'd endpoints (the agent, templates, memory, EDA, the evidence
             graph, case history, case management) are their own tasks.
CONSTRAINTS held: every write posts to the evaluate endpoint alone; the panel
             creates no run, finding or chart of its own; deterministic; no new
             dependency; the existing panels and their tests are unchanged;
             `tsc -b` passes (the build is CI's type gate, and a type error the
             jsdom tests cannot see fails it); the desktop bundle builds from
             the same source and nothing assumes a browser-only environment;
             the shell adds no logging of its own.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 6 added to web/src/CaseWorkspace.test.tsx (21 -> 27) - the clean
       nine-axis baseline scoped to the audit container, the failing Evidence
       axis with its value, the read-only refusal rendered as a sentence with
       the panel still usable, the recorded-audit listing newest first, the
       kind toggle reaching the endpoint with kind: "python", and the panel's
       absence without a profile.
VERIFICATION: cd web && npm test - 27 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS; the
              server suite is untouched by this change and stays at 358 passed.
LESSON: two of the six tests failed first for the same reason - the query, not
        the component. The nine verdict badges and the workflow's stage list
        both render a checkmark and an axis name ("✓ question"), so a page-wide
        `getByText` found two elements; and userEvent parses `[` and `]` as key
        descriptors, so typing `result = []` was read as a key sequence. The
        fix for the first was to scope the query to the audit's own container
        with `within` - an assertion should name where it is looking, because a
        page is not a component. The second is a reminder that `user.type`
        types *keys*, not text: fixtures that stay clear of `[]{}` are cheaper
        than escaping them.
```

### P7-SHELL-003 contract

```
TASK ID: P7-SHELL-003
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A plan that executes itself one approved write at a time is observable
      only through the API today. This task gives it a surface: the workspace
      shows what the agent proposes, and the human's yes or no is a button
      rather than a curl.

CONTEXT: P6-AGENT-002 shipped the driver. It proposes a step; the human
         approves it by id; the write runs through the endpoint that already
         owns it. Four endpoints serve it - a read-only GET, an idempotent
         proposing POST, /approve and /reject - and not one of them has a
         panel. This is the highest-value of the un-UI'd endpoints, because the
         agent is the capability that most changes what the workspace is for:
         every other panel is a step, and this one is the loop.

INPUTS: a case with artifacts (or none - the agent's first step is to profile,
        if a dataset is attached but unprofiled).
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx, web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `AgentStep` and `AgentState` interfaces matching the core's
    models, and the four functions - `getAgentState` (read-only),
    `proposeAgentStep` (idempotent), `approveAgentStep(stepId)` and
    `rejectAgentStep(stepId, reason?)`.
  - api.ts also fixes a real gap the 409 exposes: the agent's approve/reject
    answer 409 with an OBJECT as the detail (`{detail, expected, given}`), not
    a string. The existing client copies `body.detail` straight into the
    message, so a stale approval would render as "[object Object]". The client
    now unwraps a nested `detail` when the body sends one, so the sentence the
    core wrote reaches the user - the same standard every other failure path
    already meets.
  - web/src/CaseWorkspace.tsx: an `AgentPanel`, placed beside the workflow it
    drives. It loads the read-only state, a button proposes the next step
    (idempotent, so a second click is a no-op rather than a second write), and
    a pending step renders what it WILL do - one sentence per kind, built from
    the step's own payload, so the human approves something concrete rather
    than a promise, together with Approve and Reject buttons and an optional
    rejection reason that is recorded on the step. The history lists every
    step with its status and the note the write produced, so an agent-run case
    states what it did at every point. When nothing is pending and the trail
    ends in `end`, the panel shows why the agent stopped, because an abandoned
    case should say so rather than fall silent.
  - A stale approval is a 409, never a second write: the panel shows the
    sentence and reloads, because the pending step it was looking at is no
    longer the case's pending step.
NON-GOALS: autonomy (the write never happens without the button; that is
           P6-AGENT-002's contract and this task does not relax it), editing a
           proposal before approving it (the payload is settled at proposal
           time by design - rejecting and re-proposing is the path), running
           the agent in the background or on a timer, an agent over multiple
           cases, the other un-UI'd endpoints (templates, memory, EDA, the
           evidence graph, case history, case management - each its own task).
CONSTRAINTS: the panel writes only through the four agent endpoints, and each
             write those endpoints perform still goes through the endpoint
             that owns it - the panel introduces no new write path, so the
             read-only gate, the row cap and the single finding-creation path
             are all still in force; the GET never proposes, so a page refresh
             commits nothing; deterministic; no new dependency; `tsc -b`
             passes; the existing panels and tests are unchanged; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] the panel shows the agent's state: a pending proposal, or the absence of
      one, with the history behind it
- [x] proposing is idempotent: a second call returns the same pending step and
      creates no second write
- [x] a pending step states what it will do, in a sentence built from its own
      payload, before the human decides
- [x] approving runs the step and the next proposal appears without a second
      click, with the step's note in the history
- [x] rejecting records the reason and writes nothing: no run, no finding
- [x] a stale approval is shown as a sentence, not "[object Object]", and the
      panel reloads rather than writing twice
- [x] a case the agent finished shows why it stopped
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the state rendering, the idempotent
       proposal, the payload sentence, the approve round trip, the reject with
       a reason, the 409 degradation, and the end reason.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS. The server
              suite and the three gates are untouched by this change and stay
              green.
STATE UPDATE: mark P7-SHELL-003 done on pass; ROADMAP item 2 records the agent
              surface as delivered.
```


```

TASK: P7-SHELL-003 - the agent as a surface in the web shell
ID: P7-SHELL-003
PRIORITY: high
STATUS: DONE
SUMMARY: A plan that executes itself one approved write at a time was
         observable only through the API. P6-AGENT-002 shipped the driver and
         four endpoints serve it - a read-only GET, an idempotent proposing
         POST, /approve and /reject - and not one had a panel. The workspace
         now carries an Agent panel beside the workflow it drives: it shows the
         pending proposal as a sentence built from the step's own payload, and
         the human's yes or no is a button.

Every other panel in the workspace is a step; this one is the sequence. It
keeps the agent's contract exactly - the write never happens without the
button, and the write then runs through the endpoint that owns it, so the
read-only gate, the row cap and the single finding-creation path are all still
in force for an agent-run case. The GET never proposes, so a page refresh
commits nothing; the proposing POST is idempotent, so an impatient second
click is a no-op rather than a second write; and approving a step that is no
longer the case's pending one is a 409 the panel shows as a sentence before
resyncing - never a second write.

One real gap the panel exposed in the client itself: the agent's 409 answers
with an OBJECT as the detail (`{detail, expected, given}`), and the typed
client copied `body.detail` straight into the message, so a stale approval
would have rendered as "[object Object]". The client now unwraps a nested
detail, so the sentence the core wrote reaches the user - the same standard
every other failure path already met.

NON-GOALS held: no autonomy (the write still waits for the button; that is
             P6-AGENT-002's contract and this task does not relax it), no
             editing a proposal before approving it (the payload is settled at
             proposal time by design - reject and re-derive is the path), no
             background or timer-driven running, no agent across cases, no new
             endpoints for the other un-UI'd capabilities.
CONSTRAINTS held: writes only through the four agent endpoints, each of which
             still writes through the endpoint that owns it; no new write path;
             deterministic; no new dependency; `tsc -b` passes; the existing
             panels and tests unchanged; the desktop bundle builds from the
             same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 7 added (web suite 27 -> 34) - six in CaseWorkspace.test.tsx: the state
       rendering, the idempotent proposal, the payload sentence, the approve
       round trip with the next proposal arriving in the same response, the
       reject with a reason writing nothing, the 409 shown as a sentence and
       never as "[object Object]", and the end reason; one in api.test.ts for
       the nested-detail unwrap.
VERIFICATION: cd web && npm test - 34 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched and stay green.
LESSON: the suite had no spy-reset between tests, so the module-level mocks
        accumulated call history across the file; the first negative assertion
        ("approve was not called") therefore answered for every test that had
        run before it. A beforeEach with vi.clearAllMocks is what makes "not
        called" mean "not called in this test". The same class of bug hid
        inside the component too: the panel's refresh() cleared the error
        before resyncing, so a 409 message was set and then erased a tick
        later - an error handler that runs after the thing it prepared for.
        Both are the same shape: state that outlives the action that produced
        it, read as though it were fresh.
```

### P7-EVAL-001 contract
```
TASK ID: P7-EVAL-001
MILESTONE: P7 Product Modes
CAPABILITY: EVALUATE mode
GOAL: Audit existing analytical work. A user submits work someone already did -
      a SQL query and the claim it was used to support - and DAH answers the
      nine questions the specification names, each against the data rather than
      against the claim's own confidence.

CONTEXT: the master specification defines three product modes. ANALYZE is the
         one that exists and it is finished through P6. EVALUATE is the second:
         "audit existing analytical work", over inputs that can include SQL,
         Python, a notebook, a dashboard, a spreadsheet, a report or
         AI-generated analysis, judged on Question / Data / Quality / Method /
         Calculation / Evidence / Claim / Visualization / Limitations.
         Most of the machinery already exists and is validated - read-only
         execution with a row cap, deep profiling, rerun determinism, the
         evidence graph, the honesty budgets that bound what a claim may quote.
         What does not exist is the frame: today every one of those primitives
         serves the user's *own* analysis. EVALUATE turns them on work that
         came from elsewhere, and that turn is the whole task.

INPUTS: a case with at least one attached, profiled dataset; a submitted
        artifact - its code (SQL or Python), the kind, and the claim the code
        was offered as evidence for.
RELEVANT FILES: server/app/evaluator.py (NEW), server/app/main.py,
                server/app/models.py, server/app/db.py,
                server/tests/test_evaluator.py (NEW)
REQUIRED CHANGE:
  - server/app/evaluator.py: a pure module, the way evidence.py and workflow.py
    are pure. `evaluate` takes the artifact, the dataset's profile and the
    run it produced, and returns one finding per spec axis. Nothing is computed
    that the data does not contain; nothing is asserted the run does not show.
  - the nine axes, each a named check with a verdict and a sentence:
    * Question - the claim is stated and is answerable from this dataset.
    * Data - every column the code reads exists in the profile, and the
      profile's own caveats (nulls, duplicates) are surfaced as limitations.
    * Quality - the profile's missing-value and duplicate-row counts reach the
      verdict, so a claim over a column that is 40% null is a *finding*, not a
      pass.
    * Method - the code is read-only (the existing gate), bounded by the row
      cap, and deterministic: an artifact whose result depends on unordered
      output is flagged, because a rerun could disagree without anything
      changing.
    * Calculation - the code runs, and it reproduces: the artifact is executed
      twice and the two results must agree, the same standard a finding's
      validation holds (P4-VALID-005).
    * Evidence - the claim's magnitudes all appear in the result the code
      actually produced, checked against the same honesty budget a draft is
      checked against (P3-AI-012): a claim quoting a number the run does not
      contain is the single most common way an analysis lies.
    * Claim - the claim is specific enough to be wrong: it names a magnitude or
      a direction, not only a topic. "Revenue declined in north" is auditable;
      "revenue was analysed" is not, and the verdict says so.
    * Visualization - whether the artifact's result is chartable, and if a
      chart exists, whether its axes match the result's own columns. Not a
      requirement that one exist - an honest "no chart, and none needed" is a
      valid verdict.
    * Limitations - the accumulated caveats, stated as sentences rather than
      as an error code.
  - POST /cases/{id}/datasets/{id}/evaluate accepts the artifact and the claim,
    executes the code through the *existing* run endpoints' engine (never a
    second code path), and returns the evaluation. It writes the artifact as a
    run and the evaluation beside it, so an audit is itself inspectable and
    reproducible - the standard every other artifact in DAH is held to.
  - GET .../evaluations lists them, newest first, the same as runs and plans.
  - the endpoint refuses an artifact whose code is not read-only, exactly as
    the run endpoints do, and refuses a claim that is empty; both are 400s with
    a message, never a 500.
NON-GOALS: evaluating a notebook, a dashboard, a spreadsheet or a report as a
           whole file (this task takes the code and the claim, which is the
           common core of all of them; whole-file ingestion is a later task),
           an LLM judgement of the claim (deterministic by default, as every
           other assistant slice is - the LLM may later rephrase, never
           decide), a score or a grade (a verdict per axis with a sentence is
           the honest output; a number would imply a precision the axes do not
           have), evaluating an artifact against a dataset it never ran
           against, fixing the artifact.
CONSTRAINTS: the code executes under the same read-only gate, row cap and
             (for Python) hard sandbox as any other run - EVALUATE earns no
             privilege, and untrusted code is the *premise* of the mode; the
             honesty budgets from P3-AI-011..014 are reused unchanged; an
             evaluation never mutates the case, the dataset or any run, only
             appends its own row; nothing the analyst submitted is logged (the
             log holds method/path/status/duration, as P5-OBSERVE-002 pins);
             deterministic by default with `source` recorded; no new runtime
             dependency; the suite, the P2/P3/P4 gates, the web and desktop
             suites stay green.
ACCEPTANCE CRITERIA:
- [x] a clean artifact over a clean dataset passes all nine axes
- [x] an artifact reading a column the dataset lacks is flagged on Data, not
      silently passed
- [x] a claim quoting a magnitude absent from the result is flagged on
      Evidence with the value it should have been
- [x] a claim too vague to be wrong ("revenue was analysed") is flagged on
      Claim
- [x] a non-deterministic artifact (unordered output treated as a ranking) is
      flagged on Method
- [x] an artifact over a mostly-null column reports the null share as a
      Quality limitation, not a pass
- [x] an artifact that does not reproduce is flagged on Calculation
- [x] a non-read-only artifact is refused with 400 before anything executes
- [x] an evaluation is persisted, listed and inspectable; it never mutates
      another artifact
- [x] every verdict carries a sentence a reader can act on, not only a code
- [x] the full server suite, the P2/P3/P4 gates, the web suite and the desktop
      tests stay green
TESTS: server/tests/test_evaluator.py - the clean baseline; each axis's failure
       case (unknown column, invented magnitude, vague claim, unordered
       ranking, null-heavy column, non-reproducing artifact, non-read-only
      refusal); the persistence and listing round trip; the no-mutation
       invariant; 404s including a cross-case dataset.
VERIFICATION: server suite + verification/p2/verify_p2.py +
              verification/p3/verify_p3.py + verification/p4/verify_p4.py PASS;
              cd desktop/src-tauri && cargo test PASS.
STATE UPDATE: mark P7-EVAL-001 done on pass; ROADMAP item 1 flips to DONE.
```


```
TASK: P7-EVAL-001 - audit existing analytical work against nine axes
ID: P7-EVAL-001
PRIORITY: high
STATUS: DONE
SUMMARY: EVALUATE mode - the spec's second product mode. Until now every
         primitive DAH has served the analyst's *own* work: read-only
         execution, deep profiling, rerun validation, the evidence graph, the
         honesty budgets. This task turns those primitives on work that came
         from elsewhere. A user submits an artifact - its code (SQL or Python)
         and the claim that code was offered to support - and DAH answers the
         nine questions the specification names, each against the data rather
         than against the claim's own confidence.

Three pieces:

- **`server/app/evaluator.py` (new)** - a pure module, the way evidence.py and
  workflow.py are pure. `evaluate()` returns one finding per axis - question,
  data, quality, method, calculation, evidence, claim, visualization,
  limitations - each a verdict (pass / concern / fail, deliberately not a
  score: a single number would imply a precision nine heterogenous axes do not
  have) and a sentence a reader can act on. The Evidence axis reuses the
  drafter's honesty budget unchanged (`_allowed_numbers`, `_numbers_in`), so a
  claim quoting a magnitude the run does not contain is caught by the same
  standard a draft is judged by.
- **`POST /cases/{id}/datasets/{id}/evaluate`** - executes the artifact through
  the *existing* run engine, never a second code path, so the read-only gate,
  the row cap and the hard sandbox are the ones every other run answers to.
  EVALUATE earns no privilege, and untrusted code is the premise of the mode.
  The artifact is stored as a run and the evaluation beside it, so an audit is
  itself inspectable and reproducible. `GET .../evaluations` lists them newest
  first.
- **`server/app/db.py`** - the `evaluations` table, migration 8, so an audit is
  a first-class artifact rather than a transient response.

Four judgement calls the contract left open, each written into the code:

- **A non-read-only artifact is a 400 before anything executes**, exactly as the
  run endpoints refuse one. A mutation is not an artifact to audit - it is a
  request the store must never honour, and it is refused before the engine is
  asked to do anything. But an artifact that *is* read-only and still fails at
  run time is a **Calculation finding, not a 400**: the work is not the user's
  to fix, it came from elsewhere, and "this does not run" is the answer an
  auditor exists to give.
- **An unknown column is a Data fail, never a silent pass.** The first version
  of the check intersected the code's identifiers with the profile's columns,
  which drops every name the dataset lacks - the axis passed on exactly the
  case it exists to catch. The fix reuses the generator's own notion of a
  column read (`_sql_identifiers`, `_python_read_columns`, `_SQL_KEYWORDS`),
  so an invented name is *reported* rather than filtered away.
- **A chart is not required.** The contract's baseline is that a clean artifact
  passes all nine axes, and "no chart, and none needed" is a valid verdict,
  because a table's numbers are checkable without one. What *is* a fail is a
  chart whose axes are not the result's own columns - a check the previous
  shape (a bare `has_chart` boolean) could not make, because a boolean cannot
  be wrong.
- **A single-row result is deterministic without an ORDER BY**, because one row
  has no row order to disagree about; the Method axis flags only an unordered
  *multi-row* result, whose order a rerun may present differently.

NON-GOALS held: no whole-file ingestion of notebooks, dashboards or
             spreadsheets (this task takes the code and the claim, which is the
             common core of all of them), no LLM judgement of the claim
             (deterministic by default, as every assistant slice is; an LLM may
             later rephrase a sentence, never decide one), no score or grade,
             no evaluating an artifact against a dataset it never ran against,
             no fixing the artifact.
CONSTRAINTS held: the code executes under the same read-only gate, row cap and
             hard sandbox as any other run; the honesty budgets from
             P3-AI-011..014 are reused unchanged; an evaluation appends its own
             row and mutates nothing else (pinned by a test that counts runs,
             findings and evaluations around one); nothing the analyst
             submitted is logged (the log holds method/path/status/duration, as
             P5-OBSERVE-002 pins); deterministic, `source` recorded; no new
             runtime dependency; the suite, the gates and the web and desktop
             suites stayed green.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 22 in server/tests/test_evaluator.py - the clean baseline across all nine
       axes, each axis's failure case (unknown column, invented magnitude, vague
       claim, unordered ranking, null-heavy column, non-reproducing artifact,
       artifact that does not run), the read-only refusal with nothing written,
       the empty-code / empty-claim / bad-kind 400s, both the SQL and the Python
       artifact paths, persistence and newest-first listing, the no-mutation
       invariant, 404s including a cross-case dataset, the unprofiled dataset,
       and the pure module's chart branches - which the endpoint cannot reach,
       because a chart cannot exist for the run the request itself creates.
VERIFICATION: server suite 358 passed (was 336, +22); P2, P3 and P4 gates all
              PASS (each re-ran the suite at 358); web 21 passed; desktop 22
              Rust tests. All green locally; CI will run it on push.
LESSON: three of the eleven criteria were satisfied by code that had not been
        written yet, and the missing half was the interesting half. The Data
        axis "passed" an unknown column because it asked "which of the code's
        names are in the profile?" instead of "which are NOT?"; the
        Visualization axis could never pass at all, because it treated the
        absence of a chart as a defect the contract explicitly calls a valid
        verdict; and the read-only refusal had been softened into a Calculation
        finding, which is kinder but is not what the contract asks. Each was
        found the same way - reading the acceptance criteria as assertions and
        asking what code would make each one true. The general shape: a check
        that filters its inputs before testing them is testing the survivors,
        and a check that cannot fail cannot pass either.
```

### P7-SHELL-004 contract

```
TASK ID: P7-SHELL-004
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A case can be renamed, duplicated and deleted from the shell. These are
      the everyday operations on the front door, and today all three answer
      only through the API.

CONTEXT: the three endpoints have existed since P2-CASE-010 and are tested in
         the core, but the case list renders a row per case whose only
         affordance is opening it. A user who mistyped a question cannot fix
         it; a finished investigation cannot be copied as a starting point for
         a variant; and a case that has served its purpose cannot be removed,
         so the list only ever grows. This is the cheapest slice of the
         web-shell gap, and it is the one a user meets first.

INPUTS: the case list; for a rename, the edited question and the dataset label.
RELEVANT FILES: web/src/api.ts, web/src/CaseList.tsx, web/src/CaseList.test.tsx,
                web/src/index.css
REQUIRED CHANGE:
  - web/src/api.ts: `updateCase(caseId, {question?, dataset?})` for the PATCH,
    `duplicateCase(caseId)` for the POST, `deleteCase(caseId)` for the DELETE.
    The core's `Case` also carries `template_id`, which the shell's type now
    admits as optional so a templated case round-trips without the type
    disagreeing with the payload.
  - web/src/CaseList.tsx: each row keeps opening the case as its primary
    affordance and gains three actions - Rename, Duplicate, Delete. Rename is
    an inline edit of the question and the dataset label with Save and Cancel,
    so a correction never needs a second screen. Duplicate creates the copy and
    the list reloads with it. Delete is irreversible - the core removes the
    case row, every child and the case's on-disk directory - so it asks twice:
    a first click arms the row and a second, labelled with what will be lost,
    is the one that removes it. Nothing is deleted by a single click, and the
    armed state is per row, so confirming one case never endangers another.
  - Every action reports a failure as the core's own sentence and leaves the
    list usable, the way the list already does for a failed load.
NON-GOALS: bulk operations (a single-user tool with a handful of cases does not
           need selection machinery), undo for a delete (the core's contract is
           that deletion is final and its data dir goes with it; an undo would
           be a second store to keep consistent), renaming a dataset label that
           renames the file on disk (the label is a case property, not a
           filename), templates (their own task), case history and the evidence
           graph (read-only views, their own task).
CONSTRAINTS: each action calls its endpoint and nothing else; the list reloads
             after a write rather than mutating its own copy, so what it shows
             is what the core has; `tsc -b` passes; no new dependency; the
             existing list tests and the workspace stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case can be renamed inline, and the list shows the corrected question
- [x] a duplicate appears in the list after the action
- [x] a delete needs two clicks, and the second names what it removes
- [x] an armed delete is per row: confirming one case deletes no other
- [x] a failed action shows the core's message and leaves the list usable
- [x] opening a case is still the row's primary affordance
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseList.test.tsx - the rename round trip, the duplicate
       appearing, the two-click delete, the per-row isolation, and a failure
       rendered as a sentence.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS. The server
              suite and the three gates are untouched by this change and stay
              green.
STATE UPDATE: mark P7-SHELL-004 done on pass; ROADMAP item 2 records case
              management as delivered.
```


```
TASK: P7-SHELL-004 - rename, duplicate and delete a case from the shell
ID: P7-SHELL-004
PRIORITY: medium
STATUS: DONE
SUMMARY: The three everyday operations on the front door answered only through
         the API. The case list rendered a row per case whose only affordance
         was opening it: a mistyped question could not be fixed, a finished
         investigation could not be copied as the start of a variant, and a
         case that had served its purpose could not be removed, so the list
         only ever grew. All three are buttons now.

Each row keeps opening the case as its primary affordance and gains Rename,
Duplicate and Delete:

- **Rename** is inline - the question and the dataset label become inputs on
  the row itself, with Save and Cancel, so a correction never needs a second
  screen and a cancelled edit restores what was there.
- **Duplicate** creates the copy and the list reloads with it.
- **Delete** asks twice, because the core's deletion is final and takes the
  case's on-disk directory with it. A first click arms the row; the second is
  labelled with the case's own question ("Delete "Why did revenue decline?" for
  good"), because the question is the thing a user would be sorry to lose. The
  armed state is per row - confirming one case never endangers another, and an
  armed row offers "Keep it" as an escape.

Every action reports a failure as the core's own sentence and leaves the list
usable, the way a failed load already did.

NON-GOALS held: no bulk operations (a single-user tool with a handful of cases
             does not need selection machinery), no undo for a delete (the
             core's contract is that deletion is final; an undo would be a
             second store to keep consistent), no file rename behind a dataset
             label (the label is a case property), no templates, history or
             evidence-graph surfaces (their own tasks).
CONSTRAINTS held: each action calls its endpoint and nothing else, and the list
             reloads after a write rather than mutating its own copy, so what
             it shows is what the core has; `tsc -b` passes; no new dependency;
             the existing list and workspace tests stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 5 added to web/src/CaseList.test.tsx (web suite 34 -> 39) - the rename
       round trip, the duplicate appearing, the two-click delete whose second
       click names the case, the per-row isolation of an armed delete, and a
       failed delete rendered as a sentence with the case still present.
VERIFICATION: cd web && npm test - 39 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched and stay green.
LESSON: the two-click delete and the aria-labels solved each other. The first
        draft named the buttons "Rename"/"Duplicate"/"Delete" and the tests
        could not address one case among two; per-row aria-labels naming the
        question fixed the tests AND are the accessible thing to do - an action
        button that does not say which case it acts on is ambiguous to a screen
        reader for exactly the reason it was ambiguous to a test. The same
        spy-accumulation bug CaseWorkspace hit recurred here, and for the same
        reason: this file's module-level mocks had no reset between tests.
```

### P7-SHELL-005 contract

```
TASK ID: P7-SHELL-005
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A finished investigation becomes a reusable template and a template
      becomes a new case, both from the shell. Today the four template
      endpoints answer only through the API, so the shape of a case that was
      worked out once is never offered to the next one.

CONTEXT: P6-TEMPLATE-003 made a template carry the analytical shape of the case
         it came from - its plan and which engine produced it, the proposals it
         offered, and its findings' statements with the verdicts validation gave
         them - and made a case started from a template offer that shape as
         proposals a human accepts. Four endpoints serve it and all are tested
         in the core; none has a surface. Templates are not case children and
         outlive the case they came from, so they do not belong inside a case
         workspace - they belong on the front door beside the case list.

INPUTS: the case list screen (where templates are listed and started); a case
        workspace (where one is promoted); an optional name for a promotion.
RELEVANT FILES: web/src/api.ts, web/src/Templates.tsx (NEW), web/src/CaseList.tsx,
                web/src/CaseWorkspace.tsx, web/src/index.css,
                web/src/Templates.test.tsx (NEW), web/src/CaseWorkspace.test.tsx,
                web/src/api.test.ts
REQUIRED CHANGE:
  - web/src/api.ts: `Template`, `TemplateShape`, `TemplateProposal` and
    `TemplateFindingSummary` types matching the core's models, and four
    functions - `promoteCaseToTemplate(caseId, name?)` for the POST, a GET
    `listTemplates`, `createCaseFromTemplate(templateId, {question?, dataset?})`
    for the POST that seeds a case, and `deleteTemplate(templateId)` for the
    DELETE. A DELETE answers 204 and an empty body, so the shared request
    helper returns nothing for an empty body rather than trying to parse one -
    without that, every DELETE the shell makes fails at the parse after
    succeeding at the write.
  - web/src/Templates.tsx (NEW): a section for the front door. Each template
    row shows its name, the question and the dataset label it seeds, and a
    shape summary - how many proposals it carries and how many findings, with
    each finding's validation verdict - so a template says what kind of
    investigation it is, not only what it asked. A template with no shape says
    so instead of showing zeroes that imply an empty case. Each row has two
    actions: **Start a case from this**, which posts to the from-template
    endpoint and opens the seeded case, and **Retire**, which removes the
    template. A template carries no data of its own - no datasets, runs or
    findings travel with it - and the core's contract is that cases already
    created from a template are unaffected when it goes, degrading to normal
    derivation, so retiring needs no second confirmation the way deleting a
    case does.
  - web/src/CaseList.tsx: the templates section renders below the case list on
    the same screen, because templates are the other thing a user comes to the
    front door for.
  - web/src/CaseWorkspace.tsx: a **Save as a template** panel. The name is
    optional - the core defaults it to the case's question, because the common
    gesture needs no second prompt - and a promotion reports success as a
    sentence and leaves the workspace usable on failure.
  - Every write posts to its endpoint and nothing else; the list reloads after
    a write rather than mutating its own copy; a failure degrades to the
    core's own sentence.
NON-GOALS: editing a template (a template is a snapshot; changing one would
           make it disagree with the case it was captured from - the honest
           edit is to fix the case and promote again), a template gallery or
           sharing (single user, local-first), promoting from the case list
           (promotion belongs to the workspace that shows what would be
           captured), cross-case memory, EDA, the evidence graph and case
           history (read-only views, their own tasks).
CONSTRAINTS: each action calls its endpoint and nothing else; `tsc -b` passes;
             no new dependency; the existing list, workspace and client tests
             stay green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case can be saved as a template from its workspace, with an optional name
- [x] a promotion without a name is named for the case's question
- [x] the template list shows a template's name, question, dataset and shape
- [x] a shapeless template is shown as such, not as an empty case
- [x] a case started from a template is created and opened
- [x] a template can be retired, and cases created from it are unaffected
- [x] a failed write shows the core's message and leaves the screen usable
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/Templates.test.tsx - the list and its shape summary, the
       shapeless template, starting a case, retiring, and a failure rendered as
       a sentence; web/src/CaseWorkspace.test.tsx - the promotion, named and
       unnamed; web/src/api.test.ts - an empty 204 body parses to nothing.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-005 done on pass; ROADMAP item 2 records templates
              as delivered.
```


```
TASK: P7-SHELL-005 - templates in the web shell
ID: P7-SHELL-005
PRIORITY: medium
STATUS: DONE
SUMMARY: The four template endpoints answered only through the API, so the
         shape of an investigation worked out once was never offered to the
         next one from the shell. A finished case becomes a template from its
         workspace, and a template becomes a new case from the front door.

Two surfaces:

- **web/src/Templates.tsx (NEW)** sits on the case-list screen, because
  templates are not case children and outlive the case they came from - they
  are the other thing a user comes to the front door for. Each row shows the
  name, the question and the dataset label it seeds, and a **shape summary**:
  how many proposals it carries and how many findings, with each finding's
  validation verdict counted. A name alone cannot say whether a template is a
  finished method or a question-only skeleton, so a shapeless template *says
  so* - "A question-only skeleton - no shape was captured" - rather than
  showing zeroes that would imply an empty investigation. Each row has
  **Start a case from this**, which posts to the from-template endpoint and
  opens the seeded case, and **Retire**. Retiring is one click, deliberately:
  a template carries no data of its own, and the core's contract is that cases
  created from it are unaffected when it goes - `_template_of` answers None and
  the case degrades to normal derivation - so unlike deleting a case, nothing
  is lost.
- **CaseWorkspace** gains a **Save as a template** panel. The name is optional
  - the core defaults it to the case's question, because the common gesture
  needs no second prompt - and a promotion reports the saved name as a
  sentence, so a user learns where to find it.

One real bug surfaced while wiring the DELETE, and it was not in this task's
endpoints: the shared `request` helper parsed every successful body as JSON,
and the core answers 204 with an empty body for all three of the shell's
DELETEs (a case, a dataset, now a template). The write had already landed when
the response arrived, so the client threw "Unexpected end of JSON input" and
the row reported a success as "The action failed". The helper now returns
nothing for an empty body. The case-delete that P7-SHELL-004 shipped was
broken in exactly this way - its tests mocked the client, so the path never
ran for real - and it is fixed by the same two lines.

NON-GOALS held: no editing a template (a template is a snapshot; changing one
             would make it disagree with the case it was captured from, and
             the honest edit is to fix the case and promote again), no gallery
             or sharing (single user, local-first), no promoting from the list
             (promotion belongs to the workspace that shows what would be
             captured), and the remaining shell surfaces (cross-case memory,
             EDA, the evidence graph, case history) stay unowned.
CONSTRAINTS held: every write posts to its endpoint and nothing else, and the
             template list reloads after a write rather than mutating its own
             copy; `tsc -b` passes; no new dependency; the desktop bundle
             builds from the same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 11 added (web suite 39 -> 50) - 7 in the new web/src/Templates.test.tsx
       (the shape summary, the shapeless template, the empty list, starting a
       case, retiring, a failed start rendered as a sentence, a failed load),
       3 in web/src/CaseWorkspace.test.tsx (the unnamed promotion naming it for
       the question, a chosen name, a failed promotion leaving the panel
       usable), and 1 in web/src/api.test.ts (an empty 204 body parses to
       nothing).
VERIFICATION: cd web && npm test - 50 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: three of the eleven tests failed on the first run for reasons that
        were the fixtures' fault, and each taught the same thing - a test
        suite is only as honest as the DOM it asserts against. The template
        row renders the question and the dataset label as one sentence, so an
        exact `getByText('sales.csv')` could not find it; the list screen now
        loads templates beside the cases, so a test that mocked only the case
        calls saw a second alert from an unresolved spy; and the WHATWG
        Response constructor refuses a body with a 204, so the client's own
        fixture had to build one without. Each was the test describing a DOM
        the component did not produce, and the component was right.
```

### P7-SHELL-006 contract

```
TASK ID: P7-SHELL-006
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A citation of a previous case is something the analyst can follow. The
      core's cross-case recall already answers "what did I find before about
      revenue?" with the prior case's question and its strongest finding, but
      the shell renders that citation as an inert chip carrying a uuid - the
      one thing recall exists for, going to look at what was concluded last
      time, is not reachable.

CONTEXT: P6-MEMORY-001 made memory a derived, read-only projection over the
         cases and findings on disk, and P3-AI-014 made the chat answer carry
         each claim's source in `grounds` as `kind:name`. A recall answer cites
         `case:<id>` and the prior finding's `finding:<id>`. The shell's Chat
         panel renders those grounds as plain text chips, so a prior case is
         named in the sentence and unreachable below it. Memory has no
         endpoint of its own and needs none: the chat turn is the contract.

INPUTS: a conversation turn's grounds; a click on a cited case.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx, web/src/App.tsx,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/CaseWorkspace.tsx: the Chat panel's grounds chips are replaced by
    a small resolver. A `case:<id>` ground is looked up once per cited case
    (read-only GET, and only for case grounds - the other kinds are not
    case-scoped) and rendered as a button that opens that prior case in the
    workspace, labelled with the case's own question because that is how the
    analyst recognises it. Any other ground keeps rendering as the chip it
    always was. A lookup that fails - a deleted case, an unreachable core - is
    not an error: the chip falls back to the id and the answer stays readable,
    because a citation that cannot be resolved is still a citation.
  - web/src/App.tsx: the workspace gains an `onOpenCase` handler so a prior
    case opens as its own workspace rather than dumping the analyst back on
    the list.
NON-GOALS: a memory endpoint (memory is derived per question and already
           answers through the chat; a GET would be a second copy of a
           projection that cannot drift), editing or pinning memory (it is
           computed, not stored - pinning would be a store to keep consistent),
           resolving a cross-case `finding:<id>` to its statement (it needs a
           case-scoped read the shell does not have, and the answer sentence
           already quotes it), EDA, the evidence graph and case history (their
           own tasks).
CONSTRAINTS: no new endpoint; the lookup is a GET and writes nothing; a click
             only navigates - it creates no case state; `tsc -b` passes; no new
             dependency; the existing workspace tests stay green; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a chat answer citing a previous case shows that case's question as a
      button
- [x] clicking it opens the cited case's workspace
- [x] a cited case that cannot be resolved degrades to a chip, not an error
- [x] grounds of other kinds still render as they did
- [x] a case cited by more than one turn is looked up once
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the cited case as a button that opens,
       the unresolved citation degrading to a chip, and other grounds
       unaffected.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-006 done on pass; ROADMAP item 2 records
              cross-case memory as delivered.
```


```
TASK: P7-SHELL-006 - cross-case memory, actionable in the shell
ID: P7-SHELL-006
PRIORITY: medium
STATUS: DONE
SUMMARY: P6-MEMORY-001 let an answer cite what a previous case found, and the
         shell rendered that citation as an inert chip carrying a uuid. The
         one thing recall exists for - going to read what was concluded last
         time - was a click that did nothing.

The Chat panel now resolves each `case:<id>` ground to the prior case's own
question and renders it as a button that opens that case as its own workspace,
so a citation is something the analyst can follow. The question is the label
because that is how the case is recognised; a uuid would not be.

Three behaviours that had to be right rather than present:

- **One lookup per cited case.** The panel collects the case ids across every
  turn's grounds, fetches each once, and shares the result. A case cited by
  five turns costs one call.
- **A failed lookup is not an error.** A citation outlives the case it names -
  the case may have been deleted while the conversation stayed. A 404 records
  the id as absent and the chip says "a previous case that is no longer
  available", so the answer stays readable and the missing case is not
  refetched on every render. The state update returns the same object when
  nothing was learned, because a fresh object on an all-failed batch would
  re-run the effect forever.
- **Only `case:` grounds change.** Columns, datasets, runs and findings keep
  rendering as the chips they always were.

NON-GOALS held: no memory endpoint (memory is derived per question and already
             answers through the chat; a GET would be a second copy of a
             projection that cannot drift), no pinning or editing memory
             (computed, not stored), no resolution of a cross-case
             `finding:<id>` to its statement (it needs a case-scoped read the
             shell does not have, and the answer sentence already quotes it).
CONSTRAINTS held: no new endpoint and no new dependency; the lookup is a GET
             that writes nothing, and a click only navigates; `tsc -b` passes;
             the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA: all 6 - see the checked boxes above.
TESTS: 4 added to web/src/CaseWorkspace.test.tsx (web suite 50 -> 54) - the
       cited case as a button that opens it, the single lookup across two
       citations, the deleted case degrading to a chip with the answer intact,
       and the other ground kinds unchanged.
VERIFICATION: cd web && npm test - 54 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: two of the four tests failed on the first run for the same reason -
        the fixture described a component in isolation, but the workspace
        loads its own case on mount. A rejection mocked for every id took the
        whole workspace to its error screen before the chat could render, and
        the spy counted the workspace's own lookup alongside the citation's.
        The workspace is the thing under test, and it has its own life in the
        fixture's mocks.
```

---

### P7-SHELL-007 contract

```
TASK ID: P7-SHELL-007
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: The "what should I look at first" steps are reachable. Segment a measure
      by a category, correlate two columns, or read a column's spread - each
      one click from the profile - instead of a hand-written query the analyst
      only wrote because there was no button.

CONTEXT: P3-ANALYSIS-005 shipped `POST /cases/{id}/datasets/{id}/eda` with
         three ops (segment, correlate, distribution), each compiling to
         read-only SQL under the same gate and row cap as a hand-written query,
         and each deliberately *not persisted* - EDA is exploration, and a
         finding must anchor on a query the analyst wrote. Nothing in the shell
         reaches it, so the profile that names every column is shown one screen
         away from the question those columns pose.

INPUTS: a profiled dataset's columns and per-column types; the op and its
        column choices.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx, web/src/index.css,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `EdaOp`, an `EdaRequest` for the three ops' inputs, an
    `EdaResult` matching the core's, and `runEda(caseId, datasetId, request)`.
  - web/src/CaseWorkspace.tsx: an **EDA panel** between the data and runs
    panels - exploration sits between profiling and a hand-written query, which
    is where the core's own module puts it. It needs a profile (the columns are
    the inputs and the types decide which summary a distribution yields), and
    it says so rather than offering a submission that cannot succeed, the way
    the EVALUATE panel does. Where several datasets are profiled there is a
    chooser, because the ops are per-dataset.
    The op is a chooser and each op renders only its own column pickers:
    segment asks *by* and *measure*, correlate asks *x* and *y*, distribution
    asks one *column*. The profile's per-column type steers the defaults - a
    measure or a correlation axis defaults to a numeric column - but every
    column stays selectable, because the core's 400 is the honest answer to a
    wrong choice and the sentence is what teaches it.
    The result is a table of the columns the core returned, with the row count
    and a truncated marker. Nothing is kept: the panel says plainly that an EDA
    result is not a finding, and making it one is a query the analyst writes -
    the same discipline the runs and findings panels keep.
  - Every write is the one POST to the eda endpoint; a failure degrades to the
    core's own sentence and the panel stays usable for a corrected attempt.
NON-GOALS: persisting an EDA result (the core's contract is that exploration
           is not evidence; persistence would make a snapshot look like a
           finding), charts from EDA results (the chart endpoint belongs to a
           persisted run), generating the "equivalent query" from an op (the
           core does not return one, and inventing SQL the analyst did not
           write is exactly what EDA is not), new ops (their own task in the
           core), the evidence graph and case history (their own tasks).
CONSTRAINTS: the panel calls only the eda endpoint and reads only the profile;
             `tsc -b` passes; no new dependency; the existing workspace tests
             stay green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a profiled dataset offers the three ops with column pickers
- [x] each op shows only the inputs it takes
- [x] a segment returns a table grouped by the chosen category
- [x] a correlation returns the coefficient and the paired row count
- [x] a distribution adapts to a numeric or a categorical column
- [x] an unprofiled dataset explains itself rather than offering a run
- [x] a 400 shows the core's sentence and leaves the panel usable
- [x] the panel states that an EDA result is not a finding
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the three ops' round trips, the op
       chooser swapping pickers, the unprofiled message, and a refusal as a
       sentence.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-007 done on pass; ROADMAP item 2 records EDA as
              delivered.
```


```
TASK: P7-SHELL-007 - EDA in the web shell
ID: P7-SHELL-007
PRIORITY: medium
STATUS: DONE
SUMMARY: The "what should I look at first" steps were reachable only by
         writing a query. P3-ANALYSIS-005 shipped three ops - segment a measure
         by a category, correlate two columns, describe a column's distribution
         - each compiling to read-only SQL under the same gate and row cap as a
         hand-written query, and nothing in the shell could ask for one. The
         profile that names every column was shown one panel away from the
         question those columns pose.

A new **EDA panel** sits between the data and runs panels, which is where the
core's own module puts exploration: between profiling and a hand-written query.
The op is a chooser, and each op renders only its own pickers - segment asks
*by* and *measure*, correlate asks *x* and *y*, distribution asks one *column* -
so a question is asked with the shape of its answer, not a free-form form.

Four behaviours that had to be right rather than present:

- **The profile steers, but does not forbid.** A measure or a correlation axis
  defaults to a numeric column, read off the profile's per-column type family;
  every column stays selectable, because the core's 400 is the honest answer to
  a wrong choice and its sentence is what teaches the correction. A dataset with
  no numeric columns offers all of them and lets the core say why not.
- **A stale pick can never be submitted.** The pickers hold advisory state; the
  request is built from values resolved against the *current* dataset's columns,
  so a choice left over from another dataset or another op is replaced rather
  than sent.
- **The table is what the core returned.** A numeric distribution has seven
  columns and a categorical one has two, and the panel assumes neither - it
  renders the columns the answer carries. Numbers are rounded to four decimals
  for reading; the stored value is untouched.
- **Nothing is kept.** The panel says plainly that an EDA result is exploration,
  not evidence, and that making a finding of it is a query the analyst writes -
  the discipline the runs and findings panels keep. Switching ops drops an
  earlier result, because a distribution's answer is not an answer to a
  correlation's question.

NON-GOALS held: no persistence of an EDA result (the core's contract is that
             exploration is not evidence; persistence would make a snapshot
             look like a finding), no charts from EDA results (the chart
             endpoint belongs to a persisted run), no generated "equivalent
             query" (the core does not return one, and inventing SQL the analyst
             did not write is exactly what EDA is not), no new ops.
CONSTRAINTS held: the panel calls only the eda endpoint and reads only the
             profile; no new endpoint and no new dependency; `tsc -b` passes;
             the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA: all 9 - see the checked boxes above.
TESTS: 6 added to web/src/CaseWorkspace.test.tsx (web suite 54 -> 60) - the
       three ops' round trips, the op chooser swapping pickers, an earlier
       result dropping on an op change, the unprofiled message, and a 400 as a
       sentence with the op still runnable.
VERIFICATION: cd web && npm test - 60 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: four of the ten new and existing tests failed on the first run, and all
        four were the same failure - the workspace is one page, and a sentence
        or a button name that was unique when its panel was alone is not unique
        beside another panel. "Run this" matched "Run this op"; "Attach and
        profile a dataset first" matched the EVALUATE panel's version; a cell
        value of 100 appeared twice in one table. Each is fixed by saying
        exactly which thing the test means, and each fix is also the accessible
        thing - a button that two panels answer to is a button a screen reader
        cannot aim. The one type error the suite could not see was the same
        lesson at the compiler's level: `runEda`'s parameter was named
        `request`, shadowing the module's own request helper, and the tests
        never ran that code because the module was mocked.
```

---

### P7-SHELL-009 contract

```
TASK ID: P7-SHELL-009
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A reviewer reopening a case can ask "what did I do here, and when?" and
      read the answer. The timeline exists in the core as a projection over the
      persisted rows; nothing in the shell shows it, so the shape of a case -
      how it grew, and in what order - is only reconstructable by opening every
      panel and comparing timestamps yourself.

CONTEXT: P3-CASE-007 ships `GET /cases/{id}/history` -> `CaseHistory`: one event
         per artifact (case created, dataset attached and profiled, plan
         created, run executed, chart rendered, finding recorded), each carrying
         the artifact's own timestamp, a label and a detail; plus counts. It is
         a read-side projection like the evidence graph, so it cannot drift from
         the rows. A just-created case answers one event, not an error. The only
         failure is 404 for an unknown case - and the workspace loads its own
         case on mount, so that answer means the workspace is already on its
         error screen.

INPUTS: the case's persisted artifacts, read read-only.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `HistoryEvent` and `CaseHistory` matching the core's models,
    and `getCaseHistory(caseId)` for the GET.
  - web/src/CaseWorkspace.tsx: a **History panel** at the end of the workspace,
    after the evidence panel, because it is the other read-only review surface -
    where the evidence graph says what backs each claim, this says what
    happened in the case at all. It loads with the workspace, read-only. Each
    event is one line in chronological order: the timestamp, the kind as a
    phrase a reader does not have to decode ("dataset attached", not
    "dataset_attached"), the artifact's own label, and its detail - the same
    fields the core returns, shown rather than transformed. The counts are one
    summary sentence so a reader can see the case's shape at a glance.
  - A 404 degrades to muted guidance, not an alert: the workspace loads its own
    case on mount, so a 404 here means the case is already unreachable and the
    header already says so - a second alert would report the same failure twice.
    Any other failure is the sentence in an alert, the way every other panel
    reports one.
NON-GOALS: filtering or collapsing events (a case has as many events as it has
           artifacts, and the whole timeline is the point), editing history (it
           is a projection; the only way to change it is to change the case
           through the endpoints that own it), per-artifact timestamps of their
           own for validation (the finding keeps its status, not when it was
           set, so the status rides along as the event's detail - the core's
           decision, kept rather than re-derived).
CONSTRAINTS: the panel calls only the read-only GET and writes nothing; `tsc -b`
             passes; no new dependency; the existing workspace tests stay
             green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case with artifacts shows every event in chronological order
- [x] each event's kind is readable, and its label and detail are shown
- [x] a young case's single event is shown, not reported as emptiness
- [x] the counts appear as one summary sentence
- [x] an unknown case degrades to guidance rather than a duplicate alert
- [x] the panel writes nothing and reloads with the workspace
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the events of a worked case in order
       with their kinds, labels and details; the single event of a just-created
       case; the counts summary; and the 404 rendered as guidance.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-009 done on pass; ROADMAP item 2 records the
              web-shell gap as closed.

```

TASK: P7-SHELL-009 - case history, as a review surface
ID: P7-SHELL-009
PRIORITY: medium
STATUS: DONE
SUMMARY: P3-CASE-007 shipped `GET /cases/{id}/history` - one event per
         artifact, chronological, each carrying its own timestamp, a label and
         a detail - and nothing in the shell showed it, so the shape of a case,
         how it grew and in what order, was reconstructible only by opening
         every panel and comparing timestamps yourself.

A **Case history panel** now sits at the end of the workspace, after the
evidence panel, because the two are the read-only review surfaces: the graph
says what backs each claim, the timeline says what happened in the case at all.
It loads with the workspace and writes nothing. Each event is one line in the
order the core sends them: the timestamp, the kind as a phrase a reader does
not have to decode ("dataset attached", not "dataset_attached"), the artifact's
own label, and its detail beneath - the same fields the core returns, shown
rather than transformed. The counts are one summary sentence naming only the
kinds the case actually has, so a young case is not described by a row of
zeroes it would have to explain away.

Two behaviours that had to be right rather than present:

- **A 404 is guidance, not a second alert.** The only failure the endpoint
  answers is an unknown case, and the workspace loads its own case on mount, so
  that answer already reaches the user at the top of the page. The panel says
  the sentence once, muted, rather than raising an alert for a failure the
  header already reported. Every other failure is the sentence in an alert, the
  way every other panel reports one.
- **A young case is its beginning, not an empty list.** A just-created case
  answers one event, and the panel renders it - the timeline of a case that has
  only started is the start of a story, not a placeholder.

NON-GOALS held: no filtering or collapsing (a case has as many events as it has
             artifacts, and the whole timeline is the point), no editing (it is
             a projection; the only way to change it is to change the case
             through the endpoints that own the artifacts), no invented
             per-artifact timestamps for validation (the finding keeps its
             status, not when it was set, so the status rides along as the
             event's detail - the core's decision, kept).
CONSTRAINTS held: the panel calls only the read-only GET and writes nothing; no
             new endpoint and no new dependency; `tsc -b` passes; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 3 added to web/src/CaseWorkspace.test.tsx (web suite 64 -> 67) - a
       worked case's events in order with their kinds, labels, details and the
       counts summary, a young case's single event shown rather than reported
       as emptiness, and a 404 rendered as guidance with no alert.
VERIFICATION: cd web && npm test - 67 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: the timeline's first event is the case's creation, whose label is the
        case's own question - so the question now appears twice on the page,
        once as its title and once as the timeline's first line, and five
        existing assertions that meant the title broke on the duplication. Each
        now asks for the heading by role, which is the accessible thing anyway:
        an assertion that says which of two identical texts it means is the
        same judgement a screen reader user needs. The second collision was
        subtler and cost more guessing than it should have: a label inside a
        <strong> is invisible to getByText, because the matcher reads an
        element's own text nodes, not its descendants' - so a line whose label
        is emphasised cannot be matched by the phrase it renders. The event
        line is plain text now, and the lesson is to keep a line's asserted
        content in its own text nodes.


### P7-SHELL-008 contract

```
TASK ID: P7-SHELL-008
MILESTONE: P7 Product Modes
CAPABILITY: UX (the web-shell gap)
GOAL: A reviewer can ask of a case "what backs each claim, and does every one
      of them reach the data?" and get an answer. The graph exists in the core
      as a projection over persisted rows; nothing in the shell shows it, so
      the case's own evidence is only inspectable one finding at a time, and a
      claim with no source is invisible.

CONTEXT: P3-EVIDENCE-006 shipped `GET /cases/{id}/evidence-graph`, answering
         nodes (datasets, runs, charts, plans, findings), edges that say how
         one was derived from another (anchored_on, queries, rendered_from,
         planned_from), one trace per finding walking it out to the datasets it
         stands on, the findings that reach no source as `orphan_findings`, and
         counts. It is derived, never stored, so it cannot drift from the rows.
         The endpoint answers 400 with a sentence when the case has no
         artifacts to graph - that is the normal state of a young case rather
         than a failure, and the shell has to say so as guidance rather than as
         an error.

INPUTS: the case's persisted artifacts, read read-only.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx, web/src/index.css,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `EvidenceNode`, `EvidenceEdge`, `ClaimTrace` and
    `EvidenceGraph` matching the core's models, and `getEvidenceGraph(caseId)`
    for the GET.
  - web/src/CaseWorkspace.tsx: an **Evidence panel** after the findings panel,
    because the evidence graph is what reviews them. It loads with the
    workspace, read-only. Two parts:
      - **Claims and what they rest on** - one block per trace: the finding's
        statement with its validation badge, and its path rendered as nodes
        joined by arrows (finding -> run -> dataset), so a reviewer reads the
        chain without leaving the case. A trace that does not reach a source
        says so plainly and is marked, because a claim with no source is what
        the graph exists to surface.
      - **How each artifact was derived** - every edge as a sentence
        ("chart 'Revenue by region' is rendered from the sql run"), so the
        graph's structure is visible as text rather than as a diagram only a
        library could draw. No node is left out: a node with no edges still
        appears under its kind.
  - The 400 of an artifact-free case is shown as muted guidance, not as an
    alert: the core's own sentence names what would build a graph, and a young
    case is not a failed review. Any other failure is the sentence in an alert,
    the way every other panel reports one.
NON-GOALS: a drawn graph (an SVG layout is a library's job and DEC-001 keeps
           the bundle dependency-free; the edges-as-sentences list carries the
           same information a reader can act on), editing the graph (it is a
           projection; there is nothing to edit, only artifacts to add or
           remove through the endpoints that own them), the single-finding
           chain (`GET .../findings/{id}/evidence`, its own surface one day),
           case history (its own task).
CONSTRAINTS: the panel calls only the read-only GET and writes nothing; `tsc
             -b` passes; no new dependency; the existing workspace tests stay
             green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] a case with artifacts shows its claims and the path each one rests on
- [x] a finding's validation status is shown with its statement
- [x] a claim that reaches no source is marked and does not pass silently
- [x] every edge is visible as a sentence, and a node without one appears
- [x] an artifact-free case shows the core's guidance rather than an error
- [x] the panel writes nothing and reloads with the workspace
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - a case with a trace and its path, an
       orphan flagged, the edge list, and the empty-case guidance.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-008 done on pass; ROADMAP item 2 records the
              evidence graph as delivered.
```



```
TASK: P7-SHELL-008 - the evidence graph, as a review surface
ID: P7-SHELL-008
PRIORITY: medium
STATUS: DONE
SUMMARY: P3-EVIDENCE-006 could answer "what backs each claim in this case, and
         does every one of them reach the data?" - and nothing in the shell
         showed it, so a case's own evidence was only inspectable one finding at
         a time and a claim with no source was invisible.

An **Evidence panel** now sits after the findings panel, because the graph is
what reviews them. It loads read-only with the workspace. Two parts, both
textual - an SVG layout is a library's job and DEC-001 keeps the bundle
dependency-free, and a sentence carries the same information a reader can act
on:

- **Claims and what they rest on** - one block per trace: the finding's
  statement with its validation status, and its path rendered as a chain of
  chips (finding -> run -> dataset), the same shape the chat uses for a citation
  so a reviewer reads it the same way.
- **How each artifact was derived** - every edge as a sentence
  ("chart 'Revenue by region' is rendered from the sql run"), so the graph's
  structure is visible without a diagram. A node with no edge is still listed
  under its kind - an attached dataset nothing has queried yet, a plan nothing
  has run - because leaving it out would make the graph say the case has less
  than it does.

Three behaviours that had to be right rather than present:

- **A claim with no source is marked, not smoothed over.** A finding whose run
  is gone is the thing the graph exists to surface; it renders with "a claim
  with no source: its run is gone" so a reviewer cannot read it as supported.
- **A broken edge says so.** Such a finding still has its edge to a run the case
  no longer has, so an edge whose target is missing renders as "an artifact no
  longer in the case" rather than as a uuid.
- **The 400 of an artifact-free case is guidance, not an error.** The endpoint
  answers 400 with a sentence naming what would build a graph, and a young case
  is not a failed review - so it is a muted paragraph, and only other failures
  become an alert.

NON-GOALS held: no drawn graph (DEC-001 keeps the bundle dependency-free; the
             edge sentences carry the same information), no editing the graph
             (it is a projection; there is nothing to edit, only artifacts to
             add through the endpoints that own them), no single-finding chain
             surface (`GET .../findings/{id}/evidence`, its own task one day).
CONSTRAINTS held: the panel calls only the read-only GET and writes nothing; no
             new endpoint and no new dependency; `tsc -b` passes; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 4 added to web/src/CaseWorkspace.test.tsx (web suite 60 -> 64) - a claim
       with its path, an orphan flagged, the derivations and the unused
       artifacts, and the empty case's guidance rendered without an alert.
VERIFICATION: cd web && npm test - 64 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: the patch script failed three times before a line of it landed, and the
        cause was the script, not the file - an earlier replacement had moved
        the anchor a later assertion looked for, so the whole script died at
        an assert and nothing was written. Writing the file after each
        replacement instead of once at the end turned a silent all-or-nothing
        failure into a resumable one, and the same idempotency check
        ("already applied") is what made the retry safe. The same discipline
        that keeps a task atomic applies to the tool that edits it.
```


### P7-LEARN-001 contract

```
TASK ID: P7-LEARN-001
MILESTONE: P7 Product Modes
CAPABILITY: Product mode: LEARN
GOAL: A learner - someone who does not yet know what order to do these things
      in - can open a case and be walked through the analytical process as the
      spec's LEARN ladder: Why -> What -> How -> Validate. The machinery is all
      there (P3-FLOW-004 derives the stage, names the action and owns the
      endpoints); nothing sequences it as teaching, so the workspace answers
      "what do I do next" and never "why am I doing it".

CONTEXT: `case_progress` (P3-FLOW-004) derives seven stages - question, data,
         profile, plan, analyze, evidence, validate - from the artifacts the
         case actually has, and names the single action and endpoint that
         advance. The spec's LEARN ladder is four phases over those same
         stages. This task is the mapping and the teaching, nothing more: a
         read-side projection like evidence.py and history.py, recomputed from
         the same counts, writing nothing.

INPUTS: the case row and the artifact counts workflow.py already computes.
RELEVANT FILES: server/app/learn.py (new), server/app/models.py,
                server/app/main.py, server/tests/test_learn.py (new)
REQUIRED CHANGE:
  - server/app/learn.py (new): `build_learn_walk(db, case_id)` maps the seven
    ANALYZE stages onto the four LEARN phases - why (question, data), what
    (profile, plan), how (analyze, evidence), validate (validate). Every stage
    appears in exactly one phase, so the ladder is the workflow, regrouped -
    not a second sequence the case can disagree with. Each phase carries:
      - `purpose` - what this phase of the process teaches, the thing the
        workspace's "next action" never says;
      - `prompt` - the question a learner should be able to answer before
        moving on, which is what makes it teaching rather than a checklist;
      - the stages it covers, each with its own completion and the action that
        closes it, from workflow's own table so there is one source of truth;
      - `status` - complete / current / pending, derived as: complete when
        every stage it covers is complete, current when it is the first phase
        that is not, pending otherwise.
  - server/app/models.py: `LearnStage`, `LearnStep` and `LearnWalk`.
  - server/app/main.py: `GET /cases/{case_id}/learn` -> `LearnWalk`, read-only;
    404 for an unknown case.
  - The walk reports `done` when the trust loop has closed - a finding has been
    validated - and says only that. Per workflow.py, a closed loop means the
    loop RAN, not that the answer is right; LEARN must not graduate a learner
    on a stronger claim than the artifacts support.
NON-GOALS: executing anything (LEARN sequences work the learner does through
           the endpoints that already own it; the projection writes nothing),
           scoring the learner (there is no measure of understanding here, and
           inventing one would imply a precision the data cannot back - the
           same reason EVALUATE reports verdicts and not a score), storing
           progress (it is derived, so it cannot drift from the artifacts, and
           a learner who deletes a dataset moves back honestly), teaching
           content per dataset (the phases are the process; the specifics come
           from the profile and the plan, which the learner reads), the shell
           surface (its own task, P7-SHELL-010).
CONSTRAINTS: no new dependency; the endpoint is GET-only and writes nothing;
             the mapping is exhaustive and non-overlapping by construction and
             tested as a property; the seven stages' actions and hints come
             from workflow.py's table, not a copy; the existing suite stays
             green.
ACCEPTANCE CRITERIA:
- [x] a just-created case answers a walk whose first phase is current and whose
      last is pending
- [x] a case that has walked the whole loop answers every phase complete and
      done true
- [x] the phase statuses are exactly complete / current / pending, with at most
      one current
- [x] every workflow stage appears in exactly one phase
- [x] deleting an artifact moves the walk back - the projection is derived, not
      stored
- [x] each phase carries a purpose and a prompt, both sentences
- [x] an unknown case answers 404
- [x] the endpoint writes nothing; the server suite and the three gates stay
      green
TESTS: server/tests/test_learn.py - the fresh case, the walked-through case,
       the mid-case phase boundary, the one-current invariant, the
       exhaustive-mapping property, the deletion moving the walk back, the
       teaching content, and the 404.
VERIFICATION: cd server && .venv/bin/python -m pytest PASS (358 + N); the P2,
              P3 and P4 gates PASS. The web suite is untouched by this change
              and stays at 67.
STATE UPDATE: mark P7-LEARN-001 done on pass; ROADMAP item 3 records the core
              of LEARN mode as delivered, with the surface still to build.

```

TASK: P7-LEARN-001 - LEARN mode, the guided walk (core)
ID: P7-LEARN-001
PRIORITY: medium
STATUS: DONE
SUMMARY: The spec names three product modes; ANALYZE is the one that exists,
         and its workspace answers "what do I do next" without ever saying
         why. LEARN is that loop regrouped into the spec's four phases -
         Why -> What -> How -> Validate - and explained, so a learner who does
         not yet know the order can be walked through it.

The core piece is a mapping and the teaching, nothing more.
`server/app/learn.py` (new) is a read-side projection like evidence.py and
history.py: it recomputes the walk from the artifact counts `case_progress`
already derives, so it cannot drift from the case, and nothing is stored or
executed. Each phase covers the ANALYZE stages it is made of - why (question,
data), what (profile, plan), how (analyze, evidence), validate (validate) -
and every stage appears in exactly one phase, which the suite asserts as a
property rather than an intention. Each phase carries:

- **`purpose`** - what the phase of the process is *for*, the thing the
  workflow's "next action" never says.
- **`prompt`** - the question a learner should be able to answer before
  leaving the phase. That is what makes it teaching rather than a checklist,
  and answering it is what the artifacts then rest on.
- its stages, each with workflow's own action and hint read out of
  `_STAGE_ACTIONS`, so there is one source of truth for what closes a stage
  and no second copy to disagree with it.

Statuses are complete / current / pending, with at most one current - a
learner always has one thing to do next, never two - and `done` says the trust
loop closed, which per workflow.py means the loop *ran*, not that the answer is
right. LEARN does not graduate a learner on a stronger claim than the artifacts
support, and it does not score understanding, for the same reason EVALUATE
reports verdicts instead of a number: a score would imply a precision no data
here can back.

NON-GOALS held: no execution (LEARN sequences work the learner does through
             the endpoints that already own it; the projection writes
             nothing), no scoring, no stored progress (deleting an artifact
             moves the walk back as honestly as adding one), no per-dataset
             teaching content (the phases are the process; the specifics come
             from the profile and the plan), no shell surface (its own task,
             P7-SHELL-010).
CONSTRAINTS held: no new dependency; the endpoint is GET-only and writes
             nothing; the mapping is exhaustive and non-overlapping by
             construction and tested as a property.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 9 added in server/tests/test_learn.py (server suite 358 -> 367) - the
       exhaustive-once-only mapping property, the just-created case starting
       on Why, the walked-through case graduating, the phase boundary at
       profiled-but-unplanned, the one-current invariant held at every step of
       the build rather than in one state, a deletion reopening a phase and
       restoring it, the teaching being sentences, the 404, and the walk
       reading only.
VERIFICATION: cd server && .venv/bin/python -m pytest - 367 passed; the P2,
              P3 and P4 gates each PASS (each re-ran the suite at 367). The
              web suite is untouched and stays at 67.
LESSON: two of the nine tests failed on the first run for a reason that was
        the tests' own premise, not the code's - they deleted runs and
        findings to force a phase to reopen, and no such DELETE exists (only
        cases, datasets and templates are deletable, because a run is evidence
        a finding binds and the core refuses to delete bound evidence). The
        deletes answered 405 and the walk, correctly, did not move. Rewritten
        against what the core actually permits - attach an unprofiled dataset
        to reopen What, then delete it to close the case again - the same
        property is asserted with a mechanism that exists, and the assertion
        is stronger for checking the invariant at every step of a build rather
        than in one contrived state.


### P7-SHELL-010 contract

```
TASK ID: P7-SHELL-010
MILESTONE: P7 Product Modes
CAPABILITY: UX (LEARN mode's surface)
GOAL: A learner can open a case and be walked through the analytical process.
      P7-LEARN-001 ships `GET /cases/{id}/learn` - the four phases, each with
      what it teaches, the question a learner answers, and workflow's own
      action for the stage to do next - and none of it is reachable from the
      shell, so the mode exists as an endpoint and not as a product.

CONTEXT: the walk is a read-side projection over the artifact counts; the
         workspace already loads it per case. The endpoint answers 404 for an
         unknown case, which the workspace's own load reports at the top, and a
         done walk only ever claims the trust loop closed.

INPUTS: the walk, read read-only.
RELEVANT FILES: web/src/api.ts, web/src/CaseWorkspace.tsx,
                web/src/CaseWorkspace.test.tsx
REQUIRED CHANGE:
  - web/src/api.ts: `LearnStage`, `LearnStep` and `LearnWalk` matching the
    core's models, and `getLearnWalk(caseId)` for the GET.
  - web/src/CaseWorkspace.tsx: a **Learn panel** beside the workflow panel it
    explains - the workflow says where the case stands, this says why each
    step of that exists and what a learner should be able to answer before
    leaving it. It loads with the workspace, read-only. Each phase renders
    its name, its status, what it is for, the question that tests
    understanding, and the stages it covers as the actions that close them
    (with workflow's own hints), so a learner reads what to do and why in one
    place. The panel names the single phase and action to work on now, the
    way the workflow panel names the next stage; a completed walk says the
    loop closed, and says it as the core does - the loop ran, not that the
    answer is right.
  - A 404 degrades to muted guidance rather than an alert, for the same
    reason as every other read-only panel: the workspace loads its own case
    on mount, so the failure is already reported at the top. Any other
    failure is the sentence in an alert.
NON-GOALS: scoring or assessing the learner (the core has no measure of
           understanding and the shell invents none), writing anything (the
           panel calls only the GET; the learner's work happens through the
           endpoints the stages name), a separate route or mode switch (the
           workspace is one page, and the walk is a sequencing and teaching
           layer over the panels already below it, not a second app),
           dataset-specific teaching content (the phases are the process; the
           specifics come from the profile and plan the learner reads).
CONSTRAINTS: the panel calls only the read-only GET and writes nothing; `tsc
             -b` passes; no new dependency; the existing workspace tests stay
             green; the desktop bundle builds from the same source.
ACCEPTANCE CRITERIA:
- [x] the four phases render with their names and statuses
- [x] each phase shows what it is for, and the question that tests it
- [x] the stages render as the actions that close them, complete and incomplete
- [x] the panel names the one phase and action to work on now
- [x] a completed walk says the loop closed, without claiming the answer is
      right
- [x] an unknown case degrades to guidance rather than a duplicate alert
- [x] the panel writes nothing and reloads with the workspace
- [x] `tsc -b` and the web suite stay green
TESTS: web/src/CaseWorkspace.test.tsx - the four phases of a fresh case with
       the first current and the next action named, the teaching (purpose and
       prompt per phase), the stage actions with their marks, a mid-walk case
       whose current phase is What, the completed walk's sentence, and the 404
       as guidance.
VERIFICATION: cd web && npm test PASS; cd web && npm run build PASS; cd web &&
              npm run build:desktop PASS. The server suite and the three gates
              are untouched by this change and stay green.
STATE UPDATE: mark P7-SHELL-010 done on pass; ROADMAP item 3 records LEARN
              mode as delivered in core and shell.

```

TASK: P7-SHELL-010 - LEARN mode in the web shell
ID: P7-SHELL-010
PRIORITY: medium
STATUS: DONE
SUMMARY: P7-LEARN-001 ships the guided walk - the four phases, each with what
         it teaches, the question a learner answers, and workflow's own action
         for the stage to do next - and none of it was reachable from the
         shell, so LEARN existed as an endpoint and not as a product.

A **Learn this case panel** now sits beside the workflow panel it explains: the
workflow says where the case stands, this says why each step of that exists and
what a learner should be able to answer before leaving it. It loads with the
workspace, read-only. Each phase renders its name and status, what it is for,
the question that tests understanding, and the stages it covers as the actions
that close them - with the workflow's own hints - so a learner reads what to do
and why in one place, and a complete stage is marked while an open one is not.

Two things carried from the core into the shell rather than reinvented:

- **One thing to do next, never two.** The core guarantees at most one current
  phase; the panel names that phase and its action as a single sentence, the
  way the workflow panel names the next stage. A completed walk does not offer
  one, because there is nothing to do.
- **Graduation is not a claim about the answer.** A finished walk says the loop
  closed - a finding was validated - and says it as the core does: the trust
  loop *ran*, not that the answer is right. A learner is not graduated on a
  stronger claim than the artifacts support.

NON-GOALS held: no scoring or assessment (the core has no measure of
             understanding and the shell invents none), no writes (the panel
             calls only the GET; the learner's work happens through the
             endpoints the stages name), no separate route or mode switch (the
             workspace is one page, and the walk is a sequencing and teaching
             layer over the panels already below it, not a second app), no
             dataset-specific teaching content.
CONSTRAINTS held: the panel calls only the read-only GET and writes nothing; no
             new endpoint and no new dependency; `tsc -b` passes; the desktop
             bundle builds from the same source.
ACCEPTANCE CRITERIA: all 8 - see the checked boxes above.
TESTS: 6 added to web/src/CaseWorkspace.test.tsx (web suite 67 -> 73) - the four
       phases with exactly one current and the next action named, the teaching
       per phase, the stage actions with their marks, a mid-walk case whose
       current phase is How, the completed walk's honest sentence, and a 404
       as guidance rather than an alert.
VERIFICATION: cd web && npm test - 73 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: three existing tests broke, and all three for the reason the workspace
        is one page. The ladder's stage rows are labelled with the workflow's
        own actions, so "attach a dataset" now names both the data panel's
        uploader and a stage row - and the uploader's test found two. Fixed by
        saying which panel the input is in, which is the accessible thing too.
        The other two were the same trap from the previous task come back: a
        phrase that spans a <strong> cannot be matched by text, because the
        matcher reads an element's own text nodes and not its descendants'. The
        "work on now" sentence is plain text now. And one failure was not a
        failure of its own test at all - the ambiguous-label test died midway
        and left a queued mock value behind, so the next test received a
        dataset id from the case before it. A test that fails can corrupt the
        one after it, which is why the fix belongs to the first one.


### P7-AGENT-001 contract

```
TASK ID: P7-AGENT-001
MILESTONE: P7 Product Modes
CAPABILITY: P6 Agentic Analysis (continued) - multi-agent workflows
GOAL: A case can be worked by more than one agent, each with a role of its own,
      and the roles disagree in the case's own audit trail rather than in
      private. The single driver (P6-AGENT-002) proposes the analysis loop one
      human-approved step at a time; nothing examines what it produced. This
      task adds a second role whose entire method is EVALUATE (P7-EVAL-001) -
      the reason the roadmap gated multi-agent work behind it - so an
      agent-proposed finding is audited by a different agent with a different
      objective, and a verdict that fails the analyst's own finding is recorded
      where a reviewer can read it.

CONTEXT: the spec names "autonomous multi-agent system" as an explicit
         non-goal and "Human control" in its Never-lose list, while "Agent
         orchestration" sits on the LEVEL 5 -> 6 ladder. So this is
         orchestration, not autonomy: every role shares the one approval gate
         the existing driver already uses, every write still runs through the
         endpoint that owns it, and a page refresh commits nothing. What is new
         is specialisation and a second point of view, not self-direction.

INPUTS: the case's artifacts - for the analyst, exactly what it reads today;
        for the reviewer, the findings and the runs that back them, plus the
        evaluations already recorded (an audit matching a finding's run and its
        statement means that finding has been examined).
RELEVANT FILES: server/app/agent.py, server/app/db.py, server/app/main.py,
                server/app/models.py, server/tests/test_multi_agent.py (new),
                server/tests/test_migrations.py (a case for the new migration)
REQUIRED CHANGE:
  - server/app/db.py: migration 9 - `agent_steps` gains a `role` column
    defaulting to `analyst`, so every step recorded before this task reads as
    the analyst role and the legacy paths keep their meaning. LATEST_SCHEMA_VERSION
    becomes 9.
  - server/app/agent.py: the driver becomes role-aware - the pending step, the
    history, the proposals and the settle/decide path all take a role. The
    `analyst` role is today's decision procedure, unchanged. The `reviewer`
    role is new and small: derive the case's first finding whose (run, claim)
    has no evaluation, and propose an `evaluate` step carrying the run's own
    code and the finding's statement. Every finding audited means no step, and
    an end row names what the reviewer is waiting for rather than falling
    silent.
  - server/app/main.py: `/cases/{case_id}/agents/{role}` with the same four
    verbs the single driver answers (GET state, POST propose, approve, reject),
    and the `evaluate` step kind applied through the existing evaluate
    endpoint - the reviewer has no write path of its own, exactly as the
    analyst has none. The existing `/cases/{case_id}/agent` family stays, as
    the analyst role, so the shell's agent panel and every existing test keep
    working. An unknown role is a 400 naming the roles that exist.
  - server/app/models.py: `AgentState` carries the role; `AgentStep` already
    exists.
  - The case export and the duplicate path carry the role with the steps they
    copy, so an agent-run case round-trips with its roles intact.
NON-GOALS: autonomy (the spec's own non-goal - a role never writes without an
           approval, and a GET never proposes), inter-agent messages or
           negotiation (two agents do not talk to each other; each addresses
           the case, and the case's rows are the shared state), resolving a
           disagreement (a reviewer's failing verdict is recorded beside the
           analyst's finding, not folded into the finding's own validation
           status - rerun support and an audit are two honest notions, and
           conflating them would make both say less), new analysis capability
           (the reviewer audits; it does not discover), the shell surface (its
           own task, P7-SHELL-011).
CONSTRAINTS: no new dependency; at most one pending step per role, and an
             approval that is not that role's live step is a 409; the
             reviewer's audits land in the evaluations table through the same
             endpoint a human audit uses; the existing agent tests stay green
             unchanged.
ACCEPTANCE CRITERIA:
- [x] a case carries agents in two roles, each with its own pending step and
      audit trail
- [x] the analyst role behaves exactly as P6-AGENT-002's driver did
- [x] the reviewer proposes an evaluate step over an unaudited finding, and
      approving it records an evaluation whose claim is the finding's
      statement and whose code is the run's
- [x] a finding that has been audited is not re-proposed
- [x] an approval for one role is not the other's; a mismatch answers 409 with
      that role's own pending step
- [x] an unknown role answers 400 naming the roles that exist
- [x] a reviewer's failing verdict does not touch the finding's
      validation_status
- [x] the legacy /agent paths are the analyst role and keep working
- [x] a store from before this task upgrades and its existing steps read as
      analyst
- [x] the export round trip carries the role
- [x] the endpoint family writes only through approvals; the server suite and
      the three gates stay green
TESTS: server/tests/test_multi_agent.py - the two roles side by side, the
       reviewer's audit and its idempotence, the 409 naming the right role's
       step, the unknown-role 400, the failing verdict leaving the finding's
       own status alone, the legacy paths as the analyst role, and the export
       round trip carrying the role; test_migrations.py gains a case for
       migration 9.
VERIFICATION: cd server && .venv/bin/python -m pytest PASS (367 + N); the P2,
              P3 and P4 gates PASS. The web suite is untouched by this change
              and stays at 73.
STATE UPDATE: mark P7-AGENT-001 done on pass; ROADMAP item 4 records the core
              of multi-agent workflows as delivered, with the surface still to
              build.

```

TASK: P7-AGENT-001 - multi-agent workflows, roles over one case (core)
ID: P7-AGENT-001
PRIORITY: medium
STATUS: DONE
SUMMARY: A case can be worked by more than one agent, each with a role of its
         own - and the roles disagree in the case's own audit trail rather than
         in private. The single driver (P6-AGENT-002) proposes the analysis
         loop one human-approved step at a time; nothing examined what it
         produced. This task adds a second role whose entire method is
         EVALUATE, so an agent-proposed finding is audited by a different agent
         with a different objective, and a verdict that fails the analyst's own
         finding is recorded where a reviewer can read it.

The design turns on a distinction the spec itself draws: an *autonomous*
multi-agent system is an explicit non-goal, and "Human control" is in the
Never-lose list, while "Agent orchestration" is on the LEVEL 5 -> 6 ladder. So
this is orchestration, not autonomy. Every role shares the one approval gate
the existing driver already uses, every write still runs through the endpoint
that owns it, and a GET never proposes - a page refresh commits nothing no
matter how many roles are open.

Two roles, one case:

- **analyst** - the existing decision procedure, unchanged: profile, plan,
  analyze, interpret, accept, chart, validate.
- **reviewer** - deliberately small, and deliberately not the analyst's. It
  derives the case's first finding whose (code, claim) has no evaluation and
  proposes the EVALUATE audit of the run that backs it: the claim is the
  finding's own statement, the code is the run's own query. The reviewer
  invents neither, discovers nothing, and writes nothing of its own - the audit
  goes through the same evaluate endpoint a human audit uses, and the verdict
  lands in the evaluations table beside every other audit.

Three things that had to be right rather than present:

- **Idempotence keyed on code and claim, not run.** EVALUATE stores the
  artifact as a run of its own, so an evaluation's run_id is the audit's
  artifact, not the finding's - joining on it would never match, and the
  reviewer would re-audit forever. The (code, claim) pair is exactly what the
  reviewer proposed, so matching it is a projection: an audit cannot be
  repeated without an evaluation existing, and a finding cannot be skipped by
  forgetting.
- **Two honest notions stay distinct.** A failing audit is recorded beside the
  finding; it does not touch the finding's own validation_status, which is
  about rerun support. Folding them together would make both say less.
- **One role's approval never authorises another role's write.** A mismatch is
  a 409 naming that role's own pending step, so two open panels cannot collide
  into a double write.

NON-GOALS held: autonomy (a role never writes without an approval), inter-agent
             messages or negotiation (the roles do not talk to each other; each
             addresses the case, and the case's rows are the shared state),
             resolving disagreement (a failing verdict is recorded, not folded
             in), new analysis capability (the reviewer audits; it does not
             discover), the shell surface (its own task, P7-SHELL-011).
CONSTRAINTS held: no new dependency; at most one pending step per role; the
             reviewer's audits land through the evaluate endpoint; the existing
             agent tests stayed green unchanged.
ACCEPTANCE CRITERIA: all 11 - see the checked boxes above.
TESTS: 12 in server/tests/test_multi_agent.py (server suite 367 -> 380, with one
       migration case) - the two roles side by side, the audit's claim and code
       being the finding's own, the recorded evaluation, idempotence, the
       no-findings reason, the cross-role 409, the unknown-role 400, the
       failing verdict leaving the finding's status alone, rejection writing
       nothing, the export round trip carrying the role, and the GET that never
       proposes. Plus test_migrations.py: a pre-roles store whose steps read as
       analyst.
VERIFICATION: cd server && .venv/bin/python -m pytest - 380 passed; the P2, P3
              and P4 gates each PASS (each re-ran the suite at 380). The web
              suite is untouched and stays at 73.
LESSON: most of the failures on the way to green were the migration's own
        bookkeeping - a changed INSERT column list here, a values tuple that
        kept its old length there, a SELECT that gained a WHERE column without
        gaining the SELECT column - each surfacing as "incorrect number of
        bindings" or a KeyError far from the site of the edit. The discipline
        that caught them was running the existing agent and export suites
        first, before writing a new test, because those suites already encode
        every write path and said exactly which statement was wrong. A schema
        change is not one edit; it is one edit per writer, and the writers are
        found by the tests, not by grep.

### P7-SHELL-011 contract

```
TASK ID: P7-SHELL-011
MILESTONE: P7 Product Modes
CAPABILITY: UX (the multi-agent surface - the reviewer in the web shell)
GOAL: `/cases/{id}/agents/{role}` has the same four verbs the single driver
      has, and nothing in the shell reaches it, so a second agent's audits are
      observable today only through the API - exactly where the single driver
      was before P7-SHELL-003. The reviewer becomes a second agent panel beside
      the analyst's: each loads read-only with the workspace, each proposes
      only when the analyst asks, and each write still runs through the
      endpoint that owns it.
CONTEXT: P7-AGENT-001 delivered the roles in the core. The workspace is one
         page (P4-UX-003), so two panels that share wording would be
         ambiguous - getByText matches an element's own text nodes, and a
         phrase spanning a <strong> cannot be matched at all.
INPUTS: `GET /cases/{id}/agents/{role}` for each role - the pending step and
        the audit trail, read-only.
RELEVANT FILES: web/src/api.ts (the typed client for the role family),
                web/src/CaseWorkspace.tsx (a panel per role),
                web/src/CaseWorkspace.test.tsx (the reviewer as a surface)
REQUIRED CHANGE:
  - api.ts: `AgentRole = 'analyst' | 'reviewer'`; `getRoleAgentState`,
    `proposeRoleAgentStep`, `approveRoleAgentStep`, `rejectRoleAgentStep`
    against `/cases/{id}/agents/{role}` and its approve/reject children.
    `AgentState` and `AgentStep` carry the `role` the core now returns. The
    legacy analyst functions stay, and the analyst panel keeps calling them,
    so no existing test changes.
  - CaseWorkspace.tsx: the reviewer's state loads read-only on mount beside
    the analyst's. `AgentPanel` becomes role-aware - one component, two sets
    of wording, chosen by role, so the two panels never share a phrase a
    matcher or a reader could confuse. The analyst's strings are unchanged.
    `stepSentence` learns the `evaluate` kind (audit the finding's own claim).
    The reviewer panel sits after the findings panel, because findings are its
    input; the analyst panel stays where it is, because it drives the loop.
  - A cross-role 409 (an approval for a step the other role holds) surfaces as
    that role's own sentence, exactly as the stale-approval case already does.
NON-GOALS: autonomy (a GET never proposes; a write never happens without the
           button), inter-agent messages or negotiation (the panels do not
           talk to each other; each addresses the case), resolving a
           disagreement (a failing verdict is shown beside the finding, and
           the finding's own validation status is untouched by it), new
           endpoints, new dependencies.
CONSTRAINTS: no new dependency; `tsc -b` passes; the desktop bundle builds
             from the same source; the existing agent tests stay green
             unchanged.
ACCEPTANCE CRITERIA:
- [x] the workspace carries an agent panel per role, each with its own state,
      and both load read-only on mount
- [x] the reviewer proposes an audit of the first unaudited finding, and the
      sentence names the finding's own claim
- [x] approving the audit runs it and the evaluation appears in the EVALUATE
      panel (the workspace reloads, as the analyst's approvals do)
- [x] rejecting records the reason and writes nothing
- [x] a cross-role 409 is shown as a sentence naming the other role's pending
      step, never as "[object Object]"
- [x] the analyst panel's wording and behaviour are unchanged
- [x] an unknown role is never sent from the shell; the two panels name the
      roles they use
TESTS: web/src/CaseWorkspace.test.tsx - the reviewer's state and its proposal,
       the approved audit reaching the evaluate endpoint's surface, rejection
       writing nothing, the cross-role 409 as a sentence, and both panels
       distinguishable on one page.
VERIFICATION: cd web && npm test PASS (73 + N); cd web && npm run build PASS
              (tsc -b + vite); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
STATE UPDATE: mark P7-SHELL-011 done on pass; ROADMAP item 4 records the
              multi-agent surface as delivered, closing the P7 checklist's
              last build item.

```

TASK: P7-SHELL-011 - the reviewer in the web shell
ID: P7-SHELL-011
PRIORITY: medium
STATUS: DONE
SUMMARY: P7-AGENT-001 gave a case two roles behind one approval gate, and
         nothing in the shell reached the role family, so a second agent's
         audits were observable only through the API - exactly where the
         single driver stood before P7-SHELL-003. The reviewer is now a second
         agent panel beside the analyst's. Both load read-only with the
         workspace, both propose only when the analyst asks, and every write
         still runs through the endpoint that owns it.

`web/src/api.ts` gains the typed client for the role family -
`getRoleAgentState`, `proposeRoleAgentStep`, `approveRoleAgentStep`,
`rejectRoleAgentStep` against `/cases/{id}/agents/{role}` - and the `role`
field the core now returns on a state and a step. The legacy analyst functions
stay, and the analyst panel keeps calling them, so its behaviour is untouched.

`web/src/CaseWorkspace.tsx` makes `AgentPanel` one component with two sets of
wording chosen by role, so the two panels on one page are never ambiguous - a
reader and a matcher can tell the analysis loop from the audit loop at a
glance. The reviewer sits after the findings panel, because findings are its
input; the analyst stays where it is, because it drives the loop. `stepSentence`
learns the `evaluate` kind, so the human approves an audit of a concrete claim
rather than a step named for its machinery.

Three things that had to be right rather than present:

- **The idle paragraph was the last hardcoded string.** The panel's every other
  phrase had been parameterised; the idle one had not, and it was invisible to
  the eye because the analyst's wording is correct for the analyst's panel. The
  reviewer told the analyst's lie - "nothing is pending, propose a step" - on a
  case with no findings, which is the reviewer's honest finished state and not
  a thing it could act on. The failure was found by the test, not by reading.
- **A recorded audit's summary shares its paragraph with the artifact kind.**
  `sql — every axis passed` is one element's text, so an exact-string match
  cannot reach the phrase; a regex can. The same trap the evidence panel hit,
  and the same fix.
- **A step's kind is not its status.** A rejected step renders its kind as the
  label, so a rejected audit that forgot `kind: 'evaluate'` rendered as a
  rejected `analyze` and the assertion read the reviewer's own history as the
  analyst's. The fixture, not the component, was wrong.

NON-GOALS held: autonomy (a GET never proposes; a write never happens without
             the button), inter-agent messages (the panels do not talk to each
             other), resolving disagreement (a failing verdict is shown beside
             the finding and the finding's own validation status is untouched),
             new endpoints, new dependencies.
CONSTRAINTS held: no new dependency; `tsc -b` passes; the desktop bundle builds
             from the same source; the existing agent tests stayed green
             unchanged.
ACCEPTANCE CRITERIA: all 7 - see the checked boxes above.
TESTS: 5 added to web/src/CaseWorkspace.test.tsx (web suite 73 -> 78) - the two
       panels distinguishable on one page, the reviewer's proposal and its
       idempotence, the approved audit reaching the evaluate endpoint's own
       surface, rejection writing nothing, and the cross-role 409 as a
       sentence naming the reviewer, never as an object.
VERIFICATION: cd web && npm test - 78 passed; cd web && npm run build PASS
              (tsc -b + vite build); cd web && npm run build:desktop PASS. The
              server suite and the three gates are untouched by this change
              and stay green.
LESSON: three of the five tests failed on the first run for the fixture's
        sake, not the component's - a missing step kind, an exact-string match
        against a phrase that shares its element, and a button name expected
        for the idle state on a panel that had a pending step. Each was the
        test asserting a premise the component's own states do not hold at the
        same time. The component was right in all three; the discipline that
        found them was asserting one state per wait and reading the rendered
        panel's own text when a match failed, rather than reasoning about what
        the panel must show.

### P7-E2E-001 contract

```
TASK ID: P7-E2E-001
MILESTONE: P7 Product Modes
CAPABILITY: Verification (the whole app over real HTTP)
GOAL: The P2/P3/P4 gates drive the app in-process through Starlette's
      TestClient. That is fast and is what caught every regression this repo
      has fixed, but it never binds a port, never parses a real multipart
      upload and never runs uvicorn's startup or shutdown. This task adds the
      complement: a fresh uvicorn server on a free port, an isolated data dir,
      and the whole product driven over real HTTP - the case built by hand, the
      reviewer agent auditing it, a second case driven entirely by the analyst
      agent, and the export round trip.
CONTEXT: every verification artifact so far is in-process. A release is the
         next step on the roadmap, and a release ships a packaged server a
         user runs for real; something should have started the actual server
         and talked to it before that.
INPUTS: none from the caller. A free port is chosen by binding a socket, the
        data dir and the database are temp directories, and the LLM env vars
        are emptied for the server's subprocess so the deterministic engines
        answer and the run needs no network.
RELEVANT FILES: verification/e2e/verify_e2e.py (new),
                verification/e2e/REPORT.md (written by the run),
                .github/workflows/ci.yml (the server job runs it after the
                gates and uploads its report)
REQUIRED CHANGE:
  - verification/e2e/verify_e2e.py starts uvicorn as a subprocess, waits for
    its listening line and then /health, drives the journey, and terminates the
    server in a finally. A failure in any step still writes the report and
    exits 1.
  - The journey asserts the real contracts, not approximations of them: the
    profile counts the null and the duplicate in the fixture, a write attempt
    is a 400 from the read-only gate, validation's verdict is accepted as
    honest when the data has a null (partially_supported, with the
    reproducibility check passed), EVALUATE answers all nine axes, the
    reviewer's GET proposes nothing, the reviewer's proposal carries the
    finding's own statement, a cross-role approval is a 409 in either of its
    two real shapes, an unknown role is a 400 naming the roles, and the
    analyst agent terminates with every step's source recorded.
  - No new dependency: urllib from the stdlib, not requests.
NON-GOALS: replacing the in-process gates (they stay; this is the complement
           and is slower), testing the web shell (the web suite does), testing
           the desktop lifecycle (the Rust e2e does), anything that needs an
           LLM key or a network.
CONSTRAINTS: deterministic and offline - the run repeats green; no new
             dependency; exits 1 on any failure; leaves no server process
             behind.
ACCEPTANCE CRITERIA:
- [x] a real uvicorn server starts on a free port and answers /health before
      any step runs
- [x] one case is built by hand end to end: upload, profile, plan, generated
      SQL, a refused write, interpretation, a drafted finding accepted,
      validation, EVALUATE on nine axes
- [x] the reviewer agent audits the finding through the shared approval gate,
      and the audit is recorded with its verdict
- [x] a cross-role approval is refused with a 409, and an unknown role is a
      400 naming the roles
- [x] a second case is driven entirely by the analyst agent to a stated stop,
      with every step's source recorded and the loop closed
- [x] the read-side surfaces answer: the evidence graph, the case history, the
      LEARN walk's four phases, a cited chat answer
- [x] the case round-trips through export/import
- [x] three consecutive runs exit 0, and the server leaves no process behind
- [x] CI runs it after the gates and uploads its report
TESTS: the script IS the test - 25 steps, each asserted, exit code 1 on any
       failure. No pytest file: a journey against a live server is not a unit.
VERIFICATION: three consecutive `server/.venv/bin/python
              verification/e2e/verify_e2e.py` runs, all exit 0, all 25 steps
              PASS, 3.1s each. CI runs it in the server job.
STATE UPDATE: mark P7-E2E-001 done; CURRENT_STATE and ROADMAP name the real-
              server e2e beside the in-process gates.
```

TASK: P7-E2E-001 - the whole app against a real server
ID: P7-E2E-001
PRIORITY: medium
STATUS: DONE
SUMMARY: Every verification artifact in this repo drives the app in-process
         through Starlette's TestClient, which is fast and is what caught every
         regression fixed here - but it never binds a port, never parses a real
         multipart upload, and never runs uvicorn's lifecycle. This task adds
         the complement: a fresh uvicorn server on a free port with an isolated
         data dir, and the whole product driven over real HTTP.

`verification/e2e/verify_e2e.py` starts uvicorn as a subprocess, reads its
listening line for the port, waits on /health, drives the journey, and
terminates the server in a finally so a failure still writes the report and
exits 1. The LLM env vars are emptied for the subprocess rather than merely
unset, because `app.main` loads `server/.env` on a plain uvicorn start and
`load_dotenv` never overrides a variable that is already set - an empty value
wins over the file, and the engines treat an empty key as absent. The first
draft scrubbed the parent environment instead, and the live key from .env made
the plan answer `source=llm` mid-journey.

The journey asserts the real contracts rather than approximations of them, and
four of them were wrong on the first run for assuming instead of reading:

- `SchemaVersion` is `version`/`target`, not `recorded`; `Profile.columns` is a
  list of names with the per-column detail in `stats`; validation answers
  `status`, not `validation_status`; the history counts are keyed by kind with
  no `total`; the LEARN walk's phases are `steps`.
- Validation's verdict on this fixture is `partially_supported`, not
  `supported`: the null revenue trips the missing-data check. That is the
  honesty budget working, so the assertion now accepts the honest verdict and
  checks that reproducibility itself passed and that the null was flagged -
  which is a stronger statement than the one it replaced.
- The cross-role 409 has two shapes, both of which refuse: a dict naming the
  role's own live step when one is pending, and a plain sentence when none is.
  The check handles both and, in the dict case, asserts the `expected` id is
  the analyst's actual pending step, so it cannot pass vacuously.
- The `run_query` read-only gate answers the attempted write with the engine's
  own sentence, quoted in the report rather than summarised.

The agent half drives a second case with no human choice in it: the loop
proposes, each write is approved by id, and it terminates at a stated reason
(profile -> plan -> analyze -> interpret -> accept -> chart -> validate, then
no further step) with the loop closed and every step's `source` recorded as
deterministic.

NON-GOALS held: the in-process gates are unchanged and still the primary
             suite; the web shell and the desktop lifecycle are untouched; no
             step needs a network.
CONSTRAINTS held: no new dependency (urllib, not requests); deterministic
             offline - three consecutive runs green; exit 1 on any failure; no
             server process left behind.
ACCEPTANCE CRITERIA: all 9 - see the checked boxes above.
TESTS: the script is the test - 25 asserted steps over real HTTP.
VERIFICATION: three consecutive runs, all exit 0, all 25 steps PASS, ~3.1s
              each; CI runs it in the server job after the gates and uploads
              its report.
LESSON: four endpoint-shape assumptions were wrong on the first run, and every
        one of them came from reading the contract's prose instead of the
        response model - `version` for `recorded`, `stats` for per-column
        detail, `status` for `validation_status`, `steps` for `phases`. The
        response models in `app/models.py` are the contract and they are one
        grep away; the prose paraphrases them, and a paraphrase is where a
        false assumption enters. The fifth failure was the interesting one:
        the journey went to the live LLM because `.env` is loaded by the server
        itself, so scrubbing the parent environment was not enough. An empty
        value beats the file, and the empty is what the engines treat as
        absent - two behaviours that only compose into "deterministic" if both
        are known.

### P7-WALK-001 contract

```
TASK ID: P7-WALK-001
MILESTONE: P7 Product Modes
CAPABILITY: Verification (the shipped product, used by hand)
GOAL: P7-E2E-001 proved the contracts over real HTTP, but it drives the
      endpoints, not the shell an analyst actually sits in front of. This task
      is the complement: a human-shaped walkthrough of the shipped web shell,
      one real action at a time - create a case, attach a file, approve the
      agent's plan, run its SQL, interpret, draft and accept a finding,
      validate it, let the reviewer audit it, render the chart, ask the case
      a question, promote a template and start a case from it - reading what
      the UI actually renders at each step rather than what the contract
      promises.
CONTEXT: every automated artifact in the repo drives either the core through
         TestClient or the shell through jsdom. Neither notices when a panel
         that renders beautifully in a test never shows the analyst the number
         behind it, and neither can approve the wrong panel's button.
INPUTS: a real uvicorn server on :8123 against an isolated data dir
        (DAH_DATA_DIR/DAH_DB_PATH under /tmp), the LLM env vars emptied so the
        deterministic engines answer, a real headless Chrome driven over the
        DevTools protocol with genuine keyboard input (Input.insertText), and
        the same fixture CSV the e2e uses - one null revenue and one duplicate
        row, so the profiler and the honesty budgets have something to say.
RELEVANT FILES: server/app/main.py (the verdict-summary fix),
                server/tests/test_multi_agent.py (the regression assertions),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - One bug fixed: the reviewer's settled-step summary counted verdicts over a
    SET of verdict strings (`{axis.verdict for axis in axes}`), so a nine-axis
    audit could never report more than one pass or one concern - it read
    "9 axes, 1 pass, 1 concern, 0 fail" for an audit that was 7 pass / 2
    concern / 0 fail. The counts are now summed per axis.
  - Two tests strengthened: the clean-audit and failing-audit cases now assert
    the pass/concern/fail tallies against the evaluation the endpoint
    recorded, so a summary that collapses verdicts to a set cannot pass again.
  - No new feature; no contract changed.
NON-GOALS: fixing every gap the walkthrough surfaced - the findings below are
           recorded for prioritising, not silently expanded into. Only the
           one-line correctness bug and its test landed here.
CONSTRAINTS: green only - 380 server tests pass and all 25 real-server e2e
             steps pass with the fix in place; nothing committed while red.
ACCEPTANCE CRITERIA:
- [x] the whole product is driven through the shipped shell, not the API: case
      creation, file attach, the plan, the SQL run, interpretation, the drafted
      finding accepted, validation, the reviewer's audit, the chart, a cited
      chat answer, a template promoted and a case started from it
- [x] each step's rendered text was read from the DOM and checked against what
      the case actually holds, not against what the contract says
- [x] the reviewer's audit verdict summary is correct per axis, with a
      regression test that derives its expectation from the recorded evaluation
- [x] 380 server tests pass; all 25 real-server e2e steps pass
TESTS: test_multi_agent.py - the two audit tests now assert the tallies; the
       suite is 380. The e2e's own step now prints "9 axes, 7 pass, 2 concern,
       0 fail" instead of the collapsed "1 pass, 1 concern".
VERIFICATION: `server/.venv/bin/python -m pytest` -> 380 passed;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` ->
              ALL STEPS PASS, the audit step reading 7 pass / 2 concern.
STATE UPDATE: TASKS/CURRENT_STATE gain the walkthrough and its findings; the
              release remains the next roadmap step.
```

TASK: P7-WALK-001 - the shipped shell, used by hand
ID: P7-WALK-001
PRIORITY: medium
STATUS: DONE
SUMMARY: The automated verification in this repo drives either the core
         through TestClient or the shell through jsdom. Both are fast and both
         are blind to the thing a walkthrough catches: a panel that renders
         fine in a test while never showing the analyst the number behind it.
         This task walked the shipped web shell one real action at a time -
         case created by keyboard, file attached, the agent's plan approved,
         its SQL run, interpreted, the draft accepted as a finding, validated,
         the reviewer's audit approved, the chart rendered, the case asked a
         question, a template promoted and a second case started from it -
         reading the rendered DOM at every step.

The loop works end to end, and the honesty budgets show up where they should:
the profiler counts the duplicate, validation answers `partially_supported`
because the null revenue trips the missing-data check while reproducibility
itself passes, and the LEARN panel closes with "the trust loop ran, not that
the answer is right".

ONE BUG FIXED: the reviewer's settled-step summary built a SET of verdict
strings and summed membership over it, so a nine-axis audit reported at most
one pass and one concern - "9 axes, 1 pass, 1 concern, 0 fail" for an audit
that was 7 pass / 2 concern / 0 fail. Every audit the reviewer has ever
recorded in the shell understated its own pass count. The two audit tests in
test_multi_agent.py now derive their tallies from the recorded evaluation, so
the shape of the bug - counting over distinct verdicts instead of axes - can-
not pass again.

FINDINGS NOT FIXED (recorded, in priority order):
- **Evaluations do not travel with an exported case.** `app/exporter.py` has
  no reference to the evaluations table, so a package carries the audit's own
  run (the code) but not its nine-axis verdicts. The reviewer's whole purpose
  is an audit trail that survives the analyst leaving; a restored case has
  every finding and none of its audits. exporter + importer + models + tests.
- **A stale agent step can be approved after its write happened out of band.**
  The draft panel's "Accept as a finding" and the agent's pending "accept"
  step are two paths to one endpoint. Accepting out of band does not retire
  the agent's step, so approving it later records the finding a second time -
  this walkthrough produced a duplicate finding, and the chat then cited the
  unvalidated duplicate as "the latest finding". Either retire a pending step
  whose precondition is already met, or make the accept idempotent.
- **Three core numbers are not rendered in the shell.** The plan's sub-questions
  and hypotheses, a run's result rows, and the profile's per-column null count
  are all persisted and all absent from the workspace - the analyst approves
  "Plan the analysis from the profile" having never seen the plan, and reads
  "sql over sales.csv - 2 rows" without the rows. Each is a panel over an
  existing contract; none needs a new endpoint. (The profile's duplicate IS
  shown; the null is not.)
- **A draft's grounds run together with its count.** "row_count ranges 2..32
  row(s)" is the range `2..3` butted against "2 row(s)" with no separator.
- **Two near-identical inputs sit side by side.** "What would you like to
  know?" (generate code) and "How many datasets does this case have?" (chat)
  are adjacent single-line boxes; this walkthrough typed a chat question into
  the code generator on the first attempt.

NON-GOALS held: no contract changed, no new feature; the findings above are
             for prioritising.
CONSTRAINTS held: nothing committed while red.
ACCEPTANCE CRITERIA: all 4 - see the checked boxes above.
TESTS: test_multi_agent.py, 12 tests (2 strengthened); suite 380.
VERIFICATION: 380 passed in 152s; the real-server e2e's audit step now reads
              "9 axes, 7 pass, 2 concern, 0 fail" and all 25 steps PASS.
LESSON: a set where a list was needed is the smallest possible bug and the
        hardest to see - the summary is grammatical either way, and "1 pass"
        reads as a number rather than as a collapse. The tests asserted "9
        axes" and "0 fail", which were both still true, so the suite was green
        while the count was wrong. A tally asserted against the recorded
        evaluation is the only kind of assertion that catches it. The wider
        lesson: this repo's verification drives contracts, and contracts do
        not render - three panels pass their tests while showing the analyst
        nothing, and only a hand on the shell finds that.

### P8-VALID-003 contract

```
TASK ID: P8-VALID-003
MILESTONE: P8 Analytical Contract
CAPABILITY: Validation (3 checks to the PRD's 9 dimensions)
GOAL: a finding's verdict accounts for all nine dimensions the PRD names, not
      three. Today `validate_finding` answers reproducibility, missing data and
      evidence integrity; the PRD's AT-17 requires Calculation, Data,
      Population, Timeframe, Method, Evidence, Assumptions, Causality and
      Alternative explanations. Six are uncomputed, and these are the checks
      that catch a *correct* calculation answering the *wrong* question - a
      finding that compares groups a filter excluded, or reads a trend into one
      period, or claims causation from a correlation. The EVALUATE engine
      already computes a nine-axis audit of imported work; this task points
      that machinery at the case's own finding rather than writing a second
      one, and adds the dimensions EVALUATE does not cover.
CONTEXT: the gap analysis (`docs/PRD & UX Conformance Evaluation.md`, G1) found
         the nine-axis audit exists but is aimed at imported artifacts; a
         finding inside the app gets none of it. The three current checks are
         the honest core - they are what "supported" means today - so they stay
         and become three of the nine, rather than being replaced. The six new
         ones are derived from objects the task's predecessors already built:
         the profile's quality list (P8-QUALITY-002) feeds Data, Method and
         Assumptions; the case's context (P8-CONTEXT-001) feeds Population and
         Timeframe; the run's own SQL and result feed Method and Alternatives.
INPUTS: a finding, its run (code, columns, rows, kind), the dataset's profile
        (stats and the quality list), the case's question and context. Nothing
        new is executed: the run is already stored and the profile already
        computed, so the six new checks are pure functions of what is on disk -
        which is also why they cannot regress the 4-second validation budget.
RELEVANT FILES: server/app/validation.py (new - the nine checks and the
                verdict assembly), server/app/main.py (validate_finding calls
                it, keeps the rerun it already performs),
                server/app/models.py (ValidationCheck gains a dimension,
                ValidationResult keeps its shape),
                server/app/evaluator.py (shared: number-quoting and
                column-read helpers, reused not duplicated),
                server/app/db.py (no migration - a check is derived, never
                stored, so the schema stays at v11),
                web/src/CaseWorkspace.tsx, web/src/api.ts,
                web/src/CaseWorkspace.test.tsx,
                server/tests/test_validation.py, ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - `server/app/validation.py` (new): nine checks, one per PRD dimension. Each
    is a pure function returning (passed, detail) and never raises - a check
    that cannot decide answers `passed=true` with a sentence saying it was
    skipped, because a verdict must not punish a finding for the validator's
    own blindness. The three existing checks move in as Calculation
    (reproducibility), Data (the profile's missing-data quality issue) and
    Evidence (the finding's magnitudes all appear in its run's result - the
    same number-quoting budget EVALUATE uses, reused).
  - The six new checks, each derived from an object that already exists:
      * Population - the result's rows are a *subset* the analyst must be told
        about. A GROUP BY over a filtered table answers a narrower question
        than the one asked, and a comparison across groups of wildly uneven
        sizes rests mostly on one of them.
      * Timeframe - a trend or a "same period last year" claim is checked
        against the temporal column's actual span and gaps: one period cannot
        support a trend, and a gap the claim steps over is a comparison of
        non-adjacent windows.
      * Method - the computation matches the question's shape. Averages over a
        column the profile flagged extreme, a COUNT used where a rate is asked,
        and a comparison that ignores the column the question is about.
      * Assumptions - the unstated premises a finding rests on, taken from the
        profile: an implicit "missing is zero", a comparison of unnormalised
        totals across groups of different sizes.
      * Causality - the weakest form of AT-18, deliberately: it flags causal
        language in the finding's own statement when the evidence is a
        correlation, and leaves the full guard to P8-CAUSAL-004. It is a check
        that *says* the claim outruns the method, not one that refuses it.
      * Alternative explanations - the columns the question names that the
        run never read, plus a categorical variable the profile shows is
        confounded with the grouping. A finding that does not look at the
        alternative has not ruled it out.
  - The verdict assembly stays three-valued - supported /
    partially_supported / insufficient_evidence - and the rule stays honest: a
    single failing *hard* check (calculation, evidence, population) blocks
    `supported`, while a soft concern (method, assumptions, causality,
    alternatives) yields `partially_supported`, the verdict that says "the
    numbers reproduce and the claim is phrased within them, but the analysis
    has a stated limitation". Nothing is failed silently and nothing is
    promoted silently.
  - `validate_finding` calls the module and keeps the rerun it already
    performs - the new checks read the rerun's outcome rather than re-running
    anything, so validation costs one execution, not nine.
  - The shell renders each check's dimension and detail; a concern is shown as
    a concern rather than folded into the pass count, because an analyst who
    sees "7 pass, 2 concern" reads a different analysis than one who sees
    "supported".
NON-GOALS: the full causal-language guard with its own thresholds (P8-CAUSAL-
           004 - this task ships the *check*, that one ships the policy and
           the 50-case evaluation); widening the EVALUATE engine's own axes
           (that audit is of imported work and stays as-is); measuring the
           >= 95% detection rate AT-17 names (that is the golden suite,
           P8-GOLDEN-005 - this task ships the checks the suite will measure);
           storing checks (a validation is recomputed on demand and is
           deterministic, so it needs no column and no migration).
CONSTRAINTS: green only. No new SQL execution in the checks - they read the
             stored run and the stored profile. The API's response shape stays
             backwards-compatible: `checks` gains entries and each entry gains
             a `dimension`, and a client reading the old three names still
             finds them. The schema stays at v11.
ACCEPTANCE CRITERIA:
- [x] all nine PRD dimensions have a check, and every finding's validation
      answer carries all nine
- [x] the three pre-existing behaviours are preserved verbatim: a clean
      finding is `supported`, a null in the profile is `partially_supported`,
      a drifted result is `insufficient_evidence`
- [x] a check that cannot decide answers `passed=true` with a skip sentence,
      never a fail and never a 500
- [x] a finding quoting a magnitude absent from its run fails Evidence, and a
      finding claiming causation from a correlation is flagged on Causality
- [x] validation costs one execution of the finding's code, not one per check
- [x] the shell shows each dimension with its verdict, distinguishing a
      concern from a failure
TESTS: test_validation.py - the three preserved behaviours, one raising test
       per new dimension (a fixture per defect), the skip-when-undecidable
       rule, and the one-execution budget (a counter on the run engine).
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11.
```

TASK: P8-VALID-003 - validation across the PRD's nine dimensions
ID: P8-VALID-003
PRIORITY: high
STATUS: DONE
SUMMARY: a finding's verdict now accounts for all nine dimensions the PRD names
         (AT-17) rather than three. `server/app/validation.py` is new: nine
         pure checks - calculation, data, population, timeframe, method,
         evidence, assumptions, causality, alternative_explanations - each
         returning a verdict and a sentence, and never raising; a check that
         cannot decide passes with a "skipped -" sentence rather than punishing
         a finding for the validator's own blindness. The three checks that
         existed survive as three of the nine: reproducibility became
         calculation, missing_data became data (it reads the quality issue's
         impact sentence, so the audit and the Data stage say the same thing
         about the same null) and evidence_integrity became evidence (the
         number-quoting budget EVALUATE already used, reused rather than
         reimplemented). Six are new and are derived from objects the task's
         predecessors built - the profile's quality list, the case's context,
         the run's own SQL and result - so nothing new is executed: a
         validation costs one rerun, not nine, and that is pinned by a test
         with a counter on the query engine, proven to fail when a second
         execution is injected. The verdict stays three-valued and stays
         honest: a hard failure (calculation, evidence, population) yields
         `insufficient_evidence`, a soft concern yields `partially_supported`,
         and only a clean sweep is `supported`. The run's ownership of the case
         is the one fact the module cannot derive from stored objects, so it is
         folded in by the route as an evidence override. The shell renders each
         dimension with its sentence and distinguishes a concern from a
         failure, because an analyst reading "7 pass, 2 concern" reads a
         different analysis from one reading "supported". The schema stays at
         v11 - a check is derived, never stored. Also fixed along the way: the
         check key rename broke three older tests and two phase gates that
         asserted the pre-existing names, and the web suite's 5000ms timeouts
         under parallel file execution were load, not code - `fileParallelism:
         false` makes the gate deterministic without costing wall-clock time.

### P8-GOLDEN-005 contract

```
TASK ID: P8-GOLDEN-005
MILESTONE: P8 Analytical Contract
CAPABILITY: Verification (the analytical golden suite)
GOAL: the trust machinery P8 built is unmeasured. AT-40 names ten analytical
      shapes a product like this must compute correctly - aggregation,
      filtering, joins, missingness, duplicates, dates, percentages,
      segmentation, statistical calculations, validation - and requires 100% of
      deterministic reference calculations to match expected results. AT-01
      requires >= 95% of scripted workflow attempts to complete the full loop
      over >= 20 runs and >= 3 datasets. Today neither number exists: the
      detectors and the nine dimensions are pinned by per-feature tests, but a
      test that asserts its own fixture cannot tell you the product computes a
      percentile correctly against data it did not write. This task ships the
      golden datasets as fixtures with hand-computed reference values, and a
      suite that runs the real workflow over them and reports the two numbers.
CONTEXT: the phase's own rule is that convenience is sacrificed before
         analytical trust, and the three tasks before this built the objects a
         measurement would cover - quality detection (P8-QUALITY-002), the nine
         validation dimensions (P8-VALID-003) and the causal guard with its
         50-case corpus (P8-CAUSAL-004). That corpus is the model for this one:
         data plus a measurement, not a wall of assertions. The golden values
         are computed by hand and by an independent path (Python's statistics
         module over the same fixture), never by running the query and
         recording what came back - which would make the suite tautological.
INPUTS: three or more deterministic CSV fixtures, each covering a subset of
        AT-40's ten shapes, each with: the reference SQL or Python the analyst
        would run, and the expected rows computed independently. The workflow
        measurement drives the loop over them - create, question, attach,
        profile, plan, run, interpret, draft, accept, validate, reopen.
RELEVANT FILES: verification/golden/datasets/*.csv (new fixtures),
                verification/golden/reference.py (new - the hand-computed
                expectations and the independent-path recomputation),
                verification/golden/verify_golden.py (new - the runner: the
                reference-calculation check and the workflow-completion
                measurement, writing verification/golden/REPORT.md),
                server/tests/test_golden.py (new - asserts the runner's two
                numbers in the suite, so a regression fails a test rather
                than a report nobody reads),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - Deterministic fixtures, at least three, each exercising several of AT-40's
    shapes: a sales dataset with missingness, duplicates, dates and
    segmentation; a spend/signups dataset for joins and correlation; a tickets
    dataset for percentages and statistical calculations. Small enough to hold
    a reference value in the head, real enough that the shapes are not
    synthetic one-rows.
  - Reference values computed two ways: by hand from the fixture's own numbers,
    and independently in the suite by a second path (Python over the parsed
    CSV, not the engine's own SQL), so the golden value is not the engine
    agreeing with itself. Where the two paths disagree the fixture is wrong,
    not the engine.
  - A runner that, per dataset and shape: attaches the fixture to a real server
    on an isolated store, runs the reference query over HTTP, and compares the
    result to the golden value within a stated tolerance. Floats compare to a
    tolerance; exact types (counts, category labels) compare exactly.
  - The workflow-completion measurement: a scripted run over each dataset
    walking the whole loop AT-01 names, counting a run complete when every
    stage produced its artifact and the case reopens with it. >= 20 scripted
    runs, >= 3 datasets, reported as a rate.
  - Both numbers asserted in the test suite, not only written to a report.
NON-GOALS: the traceability matrix (P8-TRACE-010); coverage/perf/a11y
           measurement (P8-MEASURE-009); new core capability - every shape the
           suite measures is computed by code that already exists, and a
           failure in the suite is a finding about an existing calculation, not
           a reason to build one; LLM-judged quality.
CONSTRAINTS: green only. Deterministic and offline - no LLM calls (the planner
             falls back to deterministic with the LLM vars empty, which the
             e2e already relies on). The suite runs against a real server with
             an isolated data dir, the pattern verify_e2e.py established, so it
             exercises the HTTP surface a user actually touches. Reference
             values are never derived from the engine's own output.
ACCEPTANCE CRITERIA:
- [x] at least 3 fixtures exist, covering all 10 of AT-40's shapes between them
- [x] every reference calculation matches its golden value, 100%, within a
      stated tolerance, and each golden value is independently recomputed
- [x] no golden value is derived from the engine's own output
- [x] >= 20 scripted workflow runs across >= 3 datasets complete, and the
      measured completion rate is >= 95%
- [x] the two numbers are asserted in the test suite, so a regression fails a
      test
- [x] the suite is deterministic and offline, no LLM call
TESTS: test_golden.py - the fixtures' shapes are all covered, the runner's two
       measurements meet their thresholds, and at least one fixture carries a
       deliberately-wrong reference value that the runner catches (proving the
       measurement can fail, per the repo's proven-to-fail discipline).
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green;
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green;
              `cd web && npm test && npm run build` green.
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11.
```

TASK: P8-GOLDEN-005 - the analytical golden suite
ID: P8-GOLDEN-005
PRIORITY: high
STATUS: DONE
SUMMARY: the trust machinery P8 built is now measured, and the two numbers the
         PRD names exist. Three fixtures (sales, spend, tickets) carry 21
         reference calculations covering all ten of AT-40's shapes, and each
         golden value is computed twice before the engine is ever asked: by
         hand from the fixture's own numbers, and again by an independent
         implementation (plain Python and `statistics` over the parsed CSV -
         never DuckDB). Where the two disagree the fixture is wrong, and the
         suite fails before a single query runs. Only then does the runner ask
         a real server the same question over HTTP and compare: 21/21 match,
         100%, against a threshold of 100%. The same 21 journeys answer
         AT-01's workflow rate, because the query a scripted run makes *is* the
         reference query - create, attach, profile, plan, run, interpret,
         draft, accept, validate, reopen - and 21/21 complete the loop over 3
         datasets, against thresholds of 95%, 20 runs and 3 datasets. A verdict
         of `insufficient_evidence` still counts as a complete run: a finding
         the evidence does not support is a finished analysis, not a failed
         one. Both numbers are asserted in test_golden.py rather than only in a
         report, and the proven-to-fail discipline holds - a deliberately wrong
         expectation (average resolution time claimed as 25.0h against a true
         19.83h) is caught by the audit. The suite is offline by construction:
         the runner fails the `plan` stage unless the planner answers
         `source: "deterministic"`, so a completion rate above zero is itself
         proof no LLM was called. Two real bugs the suite surfaced on the way,
         both fixed with their own tests: grouping by a date column handed a
         raw `datetime.date` to `json.dumps` and answered a 500 for a valid
         query (the profile already described one as an ISO string; the run
         path now agrees), and the runner's own health check raced the stdout
         pump thread for the server's announcement and blocked forever on a
         `readline()` with no timeout.

### P8-SHELL-006 contract

```
TASK ID: P8-SHELL-006
MILESTONE: P8 Analytical Contract
CAPABILITY: UX (the orientation spine)
GOAL: AT-33 asks whether a user can understand "current case, current stage,
      current task, next useful action, analysis status" - and until this task
      the shell answered those with one text sentence and thirteen panels in a
      fixed vertical column. The UX document's own orientation machinery was
      absent: no persistent rail with per-stage status (UX 7), no three-zone
      workspace (UX 8), no case overview (UX 45). This task is the only one in
      the phase that restructures a working surface, and it is deliberately a
      rearrangement: every panel it places already existed and already had a
      contract, so the layout changes and the assertions do not have to.
CONTEXT: the five tasks before it built the objects the spine presents -
         context, quality defects, nine validation dimensions, the causal
         guard, and the golden suite that measures them. Rendering them is now
         possible and is now the gap: the walkthrough (P7-WALK-001) recorded
         that a run's result rows, the plan's contents and the per-column null
         counts were all computed by the core and never shown back, and that
         the chat and generate-code inputs were adjacent near-identical boxes.
INPUTS: the case, the derived progress (stage, completed stages, next action,
        artifact counts), the profiles with their quality issues and per-column
        stats, the findings with their validation statuses, the context's
        purpose, and the plan and run rows the endpoints already served. No new
        endpoint and no new schema: every number on the new surfaces is an
        artifact count or a stored row the core already computed.
RELEVANT FILES: web/src/CaseWorkspace.tsx (the rail, the overview, the plan
                panel, the run's rows, the per-column nulls, the zones),
                web/src/api.ts (getRun and getPlan, over endpoints that
                already existed), web/src/index.css (the three-zone grid, the
                sticky rail, the marks), web/src/App.tsx (the wide main),
                web/src/CaseWorkspace.test.tsx (+13 tests), ai/HANDOFF.md,
                ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The persistent workflow rail (UX 5/7) with the document's four marks:
    `✓` complete, `⚠` requires attention, `●` the current stage, `○` not
    started. The marks are derived the way the core derives the stage itself -
    from `progress.completed` and `progress.stage` - so the rail cannot
    disagree with the core. The one judgement is the warning, and it is
    measured: the data stage's `⚠` is the profiler's own quality issue
    (P8-QUALITY-002), never a guess. The rail is sticky, so the workflow
    indicator stays visible while the work zone scrolls.
  - The three-zone layout (UX 8): left = orientation (the rail, the case
    overview, the LEARN walk, the history, the template action), center = work
    (data, the plan, EDA, runs, findings, EVALUATE, the evidence graph),
    right = intelligence (the context, the analyst agent, the reviewer, the
    chat). The zones are real landmarks - `<section>` with an aria-label each -
    so "where am I / what am I doing / what can help me" is the DOM as well as
    the design. On a narrow screen the grid collapses to one column and the
    rail stops being sticky.
  - The case overview (UX 45, AT-33): objective, question, status as "N / M
    stages complete", key findings, open issues (the profiler's defects plus
    findings still awaiting validation), data sources, and the validation
    counts. The objective reads the context's purpose and falls back to the
    question, so a case that never stated intent is still described.
  - The three render gaps: a run's result rows and the query that produced
    them, reopened on demand over the endpoint that already served them; the
    plan's own contents - objective, sub-questions, hypotheses with their
    rationale and check, steps, data requirements, and the basis it was
    planned from; and each column's measured null count at the Data stage.
  - The two adjacent input boxes are separated by the zones themselves:
    generate-code sits in the work zone, ask-this-case in the intelligence
    zone.
NON-GOALS: the decision view (P8-DECISION-008 - this is orientation, not the
           loop's exit); question refinement (P8-REFINE-007); measurement
           (P8-MEASURE-009 - AT-33's own 8/10 threshold is a usability study,
           not something a unit suite asserts; what this task delivers is the
           surface the study would be run against, and the suite asserts the
           seven questions are answerable from it); any new core capability -
           every endpoint the new surfaces read already existed, and a failure
           in one of them is a finding about an existing contract.
CONSTRAINTS: green only. No new endpoint, no schema change, no new dependency
             (DEC-001). Deterministic: nothing new is executed and no LLM is
             involved. The rearrangement must not weaken an existing panel's
             contract - each panel keeps its own heading and its own asserted
             content, and the tests that pinned them were not edited to fit
             the new layout.
ACCEPTANCE CRITERIA:
- [x] the rail renders the four marks and its current stage agrees with the
      core's derived stage, asserted against the progress the core answers
- [x] a measured data-quality defect marks the data stage `⚠`, and a clean
      stage beside it stays `✓`
- [x] AT-33's seven questions are answerable from the rendered workspace
      alone - case, stage, task, next action and analysis status all assert on
      rendered text
- [x] the three zones are distinguishable landmarks, and the assistants live
      only in the intelligence zone
- [x] a run's result rows and its query render on demand, including the
      truncation notice when the stored result was capped
- [x] the plan's contents render, and a case without a plan is guidance
      rather than an error
- [x] every column's measured null count renders at the Data stage
- [x] the layout is responsive: narrow screens collapse to one column and the
      rail stops being sticky
TESTS: CaseWorkspace.test.tsx - the seven AT-33 questions asserted from the
       rendered workspace, the purpose-as-objective path, the open-issue count
       over quality defects plus pending validation, the three zones as
       landmarks with the assistants on one side and the work on another, the
       four marks over completed/current/attention stages, the per-column null
       counts, the plan's full body, the no-plan-yet degradation, the run's
       rows with its query, the hide path, the truncation notice, and a failed
       read reported rather than hidden.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (477);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (25/25); `cd web && npm test && npm run build` green (99, build
              ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; the schema stays at v11 and
              the server suite is unchanged - this task touched only the
              shell.
```

TASK: P8-SHELL-006 - the orientation spine
ID: P8-SHELL-006
PRIORITY: high
STATUS: DONE
SUMMARY: the shell now answers "where am I, what am I doing, what can help me"
         as a layout rather than as a sentence. The persistent rail carries the
         UX document's four marks - `✓` complete, `⚠` requires attention, `●`
         the current stage, `○` not started - derived the same way the core
         derives the stage, from `progress.completed` and `progress.stage`, so
         the rail cannot disagree with the core. The one judgement is the
         warning, and it is measured: the data stage's `⚠` is the profiler's
         own quality defect from P8-QUALITY-002, never a guess. Beside it sits
         the case overview (UX 45) - objective, question, status as "N / M
         stages complete", key findings, open issues, data sources, validation
         counts - every one of them an artifact count the core already
         computed, and the objective reading the context's purpose with the
         question as the fallback. The workspace splits into three landmark
         zones (orientation / work / intelligence), which is a rearrangement of
         panels that already existed: no panel was rewritten and the tests that
         pinned them were not edited to fit the new layout - only the one that
         asserted a stage the loop is on was "pending" now reads "current", the
         rail's own sharper vocabulary. The three render gaps the walkthrough
         found are closed over endpoints that already existed: a run's result
         rows and the query that produced them reopen on demand (with the
         truncation notice when the stored result was capped), the plan's own
         contents - sub-questions, hypotheses with their rationale and check,
         steps, data requirements, the basis it was planned from - render
         instead of being written and never read back, and every column's
         measured null count shows at the Data stage. The two adjacent
         near-identical input boxes are separated by the zones themselves. One
         limitation worth naming rather than papering over: the overview's
         labels are unstyled text, because splitting a label into its own
         element breaks the text matching a test and a screen reader both read
         - the sentence stays whole, and the first two rows carry the weight
         instead.

### P8-REFINE-007 contract

```
TASK ID: P8-REFINE-007
MILESTONE: P8 Analytical Contract
CAPABILITY: AI (question refinement)
GOAL: AT-04 requires that an AI refinement preserves the user's original
      question, presents the revision separately, allows accept / reject /
      edit, and never silently overwrites - and measures it over 50 cases:
      >= 95% preserve the original, >= 90% semantically relevant, 0 silent
      overwrites, 0 fabricated data references. Before this task nothing
      proposed a sharpening at all: a vague question ("why are sales down?")
      was carried verbatim into every plan, every generated query and every
      finding, so the analysis inherited its vagueness and the product had no
      surface where the gap was even visible.
CONTEXT: the six tasks before it built the objects a refinement reads and the
         surfaces it sits beside - the context object (P8-CONTEXT-001), the
         profile's own measurements with their quality defects
         (P8-QUALITY-002), and the orientation spine that places the question
         at the top of the case (P8-SHELL-006). The refinement grounds itself
         in the profiler's measured columns and ranges, so it proposes from
         the same data every other assistant reads.
INPUTS: the case's question, the most recently profiled dataset's profile
        (columns, per-column stats, measured min/max and cardinality), and the
        context's purpose / sub-questions / hypotheses when the case stated
        intent.
RELEVANT FILES: server/app/refine.py (new - the deterministic engine, the
                validation gate, the LLM refiner behind the same interface),
                server/app/main.py (the five refine endpoints and the
                duplicate/delete wiring), server/app/db.py (schema v12, the
                refinements table and its migration), server/app/models.py
                (Refinement, RefinementGround, RefinementEdit,
                REFINEMENT_STATUSES), server/app/history.py (the two new event
                kinds), server/app/exporter.py (the round trip),
                verification/refine/{cases.py,verify_refine.py} (new - the
                50-case corpus and the measurement runner),
                server/tests/test_refine.py (new, 41 tests),
                web/src/RefinePanel.tsx (new), web/src/CaseWorkspace.tsx,
                web/src/api.ts, web/src/CaseWorkspace.test.tsx (+7 tests),
                ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - One interface, two engines, as in the planner / assistant / drafter /
    generator: `refine_question` is deterministic and always available;
    `LLMRefiner` calls an OpenAI-compatible endpoint when DAH_LLM_API_KEY is
    set and its output is gated by `validate_refinement` before it is stored.
    A failure of the LLM falls back to the deterministic proposal, which may
    itself be a decline.
  - The deterministic engine appends grounding rather than rewording: the
    refined question is the original with clauses added - the measure, the
    split, the time window, the comparison a direction word leaves unstated -
    each one a column and a range the profile measured. So the original is
    preserved by construction and the refinement is relevant by construction,
    and the suite measures both anyway because a structural guarantee is one
    renamed variable away from a regression. It declines rather than invents:
    no profile, nothing numeric or temporal, no subject terms to preserve, or
    a question already naming its measure, split and window is left alone, and
    the decline is recorded rather than answered as an empty proposal.
  - The gate: the original must be echoed verbatim, the subject terms must
    survive, every cited column must be one the profile has, every quoted
    column name must exist, every figure must be one the profile measured (in
    any spelling the formatter or the analyst might use), and a rationale is
    required - a bare proposal never reaches the analyst.
  - Five endpoints, and only two of them write: POST /refine proposes
    (idempotent while pending and the question unmoved); GET /refine and GET
    /refinements are read-only; accept and edit are the only paths that move
    the case's question, and reject keeps the original and writes nothing but
    the decision. A decided proposal is a 409, not a second decision; an edit
    that restores the original is refused with "use keep original instead".
  - The original is carried on the proposal row, so recoverability is a
    property of the store, not of the client that happened to be looking: it
    survives the accept that replaced it on the case row, travels with the
    export and the duplicate, and is readable from the case's refinement
    history and its timeline (two new event kinds - the proposal, then the
    decision).
  - The measurement: verification/refine/verify_refine.py drives 50 cases over
    6 datasets against a real server over HTTP with the LLM vars scrubbed,
    walking accept / edit / keep / pending at volume, and reports the four
    numbers to verification/refine/REPORT.md. Relevance is measured
    mechanically, not judged: the refined question keeps the original's subject
    terms and names at least one real column. The same four numbers are
    asserted in the test suite.
  - The shell panel (UX 12) shows the transformation explicitly - "Your
    question" above "Refined question", the arrow between them, the engine that
    spoke, the rationale and the grounds behind a disclosure - and accept /
    edit / keep original are the only three buttons. It sits in the orientation
    zone, where the question is described.
NON-GOALS: the decision view (P8-DECISION-008); measurement of coverage /
           perf / a11y (P8-MEASURE-009); refining the context's sub-questions
           and hypotheses rather than the primary question; an LLM judgement of
           relevance - the measurement is mechanical by design, and the
           deterministic engine makes three of the four thresholds structural.
CONSTRAINTS: green only. No new dependency (DEC-001 - the LLM client is
             httpx, already required). Schema moves to v12 with a migration
             that upgrades an existing store in place. Deterministic and
             offline by default: the runner fails unless the deterministic
             engine answered, so a passing suite is itself proof no LLM was
             called. Zero silent overwrites is a Level 0 requirement.
ACCEPTANCE CRITERIA:
- [x] the original question is preserved verbatim beside the proposal, and is
      recoverable after accept, after edit, and after keep-original
- [x] accept / edit / keep-original are the only three paths, and there is no
      fourth that moves the question
- [x] 0 silent overwrites: the case's question moves only through the accept
      and edit endpoints, and the original stays on the row
- [x] 0 fabricated data references: the gate rejects a cited or quoted column
      the profile does not have and a figure it did not measure, before the
      analyst sees the proposal
- [x] AT-04 measured over 50 cases: preserve 100% (>= 95%), relevant 100%
      (>= 90%), 0 silent overwrites, 0 fabrications
- [x] the four numbers are asserted in the test suite, so a regression fails a
      test rather than a report nobody reads
- [x] a deliberately-wrong expectation is caught, proving the measurement can
      fail
- [x] the round trip through export keeps the refinement history, and the
      original with it
- [x] the suite is deterministic and offline, no LLM call
TESTS: test_refine.py (41) - the engine's additions and its four decline
       paths, its determinism, the gate's nine rejection paths and its
       allowance of a measured figure in any spelling, the five endpoints
       (proposes nothing, a read never proposes, idempotency, the decline
       answer, accept / keep / edit and their error contracts: 409 on a second
       decision, 404 on another case's proposal, 400 on an edit that restores
       the original or is empty), the history's two events, the export round
       trip including a decline, the duplicate carrying the history, the delete
       removing the proposals, the schema upgrade recording the migration, and
       the measurement over a real server. CaseWorkspace.test.tsx (+7) - the
       transformation shown with both halves, accept moving the question while
       the original stays visible, keep original writing nothing, the edit
       pre-filled from the proposal, a failed decision reported, the decline
       said rather than shown as an empty panel, and the panel in the
       orientation zone.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (518);
              `server/.venv/bin/python verification/refine/verify_refine.py`
              green (50 cases, four thresholds);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (25/25); `cd web && npm test && npm run build` green (106, build
              ok).
STATE UPDATE: TASKS/CURRENT_STATE gain the task; schema v11 -> v12.
```

TASK: P8-REFINE-007 - question refinement
ID: P8-REFINE-007
PRIORITY: high
STATUS: DONE
SUMMARY: AT-04's four numbers now exist, and the question is the one place in
         the loop a vague ask was carried verbatim into every artifact after
         it. Two engines sit behind one interface, as in every other assistant:
         a deterministic refiner that appends grounding the profile measured
         (the measure, the split, the window, and the comparison a direction
         word like "down" leaves unstated) and an LLM refiner whose output is
         gated before the analyst sees it - the original echoed verbatim, the
         subject terms surviving, every cited and quoted column real, every
         figure measured, a rationale present. The refined question is the
         original with clauses added, never a replacement, so preserve and
         relevant are structural; the suite measures them anyway. The engine
         declines rather than invents - no profile, nothing numeric or
         temporal, nothing to preserve, or an already-answerable question - and
         the decline is recorded, not answered as an empty proposal.
         Measured over 50 cases and 6 datasets against a real server:
         preserve 100%, relevant 100%, 0 silent overwrites, 0 fabrications.
         The three paths are the only three: accept and edit are the sole
         writes to the case's question, and keep-original writes nothing but
         the no. Recoverability is a property of the store, not the client -
         the original rides on the proposal row, so it survives the accept
         that replaced it, the export round trip and the duplicate, and it is
         readable in the case's timeline as two events. Schema v12, one
         migration, upgrading in place. Two bugs the work surfaced, both fixed
         with their own tests: the new suite's schema test caught that a fresh
         store records no migration rows at all (it is born current, which is
         the truth - the assertion now builds the legacy store the upgrade
         path is actually about), and the web test caught that the api spies
         are module-level, so a "not called" assertion in a top-level describe
         answers for every test before it (its own beforeEach clear, the same
         discipline the CaseWorkspace describe already had).

### P8-MEASURE-009 contract

```
TASK ID: P8-MEASURE-009
MILESTONE: P8 Analytical Contract
CAPABILITY: Verification (the measurement layer)
GOAL: the PRD's measurement targets existed as prose and nothing in the
      product computed one of them. AT-38's coverage, AT-27..30's performance
      budgets, AT-32's accessibility, AT-37's dependency security and AT-45/
      46's size envelopes each had a threshold and no number. This task
      attaches a measured number to each - measured against a real core over
      real HTTP, against the OSV database, or by running the suite itself
      under a line counter - and asserts every one of them in the test suite,
      so a regression fails a test rather than a report nobody reads.
CONTEXT: the eight tasks before it built what the layer measures and two
         measured suites to borrow the pattern from - the golden suite
         (AT-40/AT-01) and the refinement runner (AT-04), both of which start
         a real uvicorn on a free port with an isolated data dir and the LLM
         vars scrubbed. The web side (AT-27, AT-30, AT-32) was already
         asserted in the shell's own suite by the a11y and measure test files
         this task found in flight; what was missing was the fold that reads
         them as a measurement and the server-side numbers beside them.
INPUTS: the suite (coverage's driver - its calls are what coverage means),
        the production inventory computed from pyproject.toml and
        package.json plus the installed distributions' own metadata, the OSV
        database over HTTP, a generated 50k-row benchmark dataset, and the
        envelope's own declared limits.
RELEVANT FILES: verification/measure/verify_measure.py (new - the runner,
                the fold, the report), verification/measure/perf.py (new -
                AT-28/29/46 against a real core), verification/measure/
                coverage.py (AT-38, the line counter - in flight, its
                denominator corrected), verification/measure/deps.py (AT-37,
                in flight), server/app/limits.py (AT-45/46, in flight),
                server/app/main.py (GET /envelope, the attach-time refusal),
                server/app/analysis.py (the profiling fix AT-29's measurement
                forced), server/tests/test_measure.py (new, 26),
                server/tests/test_python_guards.py (new, 18),
                server/tests/test_envelope.py and test_llm_adapters.py (in
                flight), web/src/{accessibility,measure}.{ts,test.tsx} (in
                flight), web/vite.config.ts (css: true, so the a11y audit
                reads the shipped stylesheet), ai/HANDOFF.md, ai/TASKS.md,
                ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The runner folds five measurements into one report, one line per
    acceptance test, and exits non-zero when a measured threshold did not
    hold. Each measurement is injected so a test can prove a failure fails
    the gate, and each can be skipped - a skipped measurement is named in the
    report rather than silently making it smaller.
  - AT-27/30/32 are asserted in the web suite, not measured here, and the
    report says so: jsdom is not a browser, and a millisecond there is not a
    millisecond in one. The suite's green is the measurement; the thresholds
    are pinned in its tests. Its summary line is the evidence the report
    quotes.
  - AT-28 measures an opening as the workspace actually opens one - the case,
    its datasets, runs, findings, decision and history as one user-visible
    wait - and takes the p95 over the heaviest case in the envelope, because a
    percentile over an empty case measures nothing.
  - AT-29 profiles a generated 50k-row benchmark dataset (the scale P4 pinned,
    with a date, a split, a measure, a duplicate and a null) and takes the p95.
  - AT-46 builds a case *at* the envelope - ten datasets, a hundred
    multi-dataset runs that each bind all ten so the evidence graph crosses a
    thousand edges, two hundred findings - then reads every surface a reopened
    case offers and requires each to answer, in budget, at that scale.
    Stability is a measured property of the reads at the boundary, and the
    import round trip is among them, so a case that heavy must still restore
    or the boundary is a dead end.
  - AT-45's two halves are both measured: the declaration is the PRD's literal
    numbers, and a dataset past each limit is refused through the same
    function the attach endpoint calls. The row refusal runs at a tightened
    value because the PRD's own five million rows would be the fixture the
    refusal exists to avoid loading; the suite pins the real number.
  - AT-37 scans the computed inventory against OSV and classifies severity
    from the advisory's own CVSS vector. An unreachable database answers
    `unknown` with a reason and the gate is red for it, because "could not
    check" and "nothing to fix" are different statements.
  - Two bugs the measurement surfaced, both fixed with their own tests. (1)
    Profiling a 50k-row dataset took 12.5s against AT-29's 5s, because every
    one of the profile's dozen bounded lookups re-read and re-parsed the CSV.
    One materialisation into a temp table gives every later query an
    in-memory table - same types, same values, same counts - and the same
    profile takes 1.7s. (2) The coverage counter's denominator counted
    function-signature continuation lines, which the compiler attributes to
    the function's code object but the interpreter never reports; the
    denominator was bigger than the numerator could reach, so coverage read
    lower than it was. The exclusion is AST-derived and signature-only, and
    the numerator is intersected with the executable set so a line cannot
    count as covered outside the denominator either.
  - The guards python_exec enforces in the child are now tested in the process
    that measures them: the dunder-hardened handle, the import wall, the
    restricted builtins, the tabulation shapes and the wall-clock alarm. They
    are security-relevant (AT-36) and they ran only in a process the line
    counter cannot instrument, so testing them directly is worth more than
    relying on the child to reach them - and it is what lifted the evidence
    group to its target.
NON-GOALS: the traceability matrix (P8-TRACE-010); re-measuring AT-01, AT-04
           or AT-40, which have their own runners and reports (the report
           points at them); a browser-side p95, which needs benchmark hardware
           and a browser this layer does not have; numeric contrast
           measurement (jsdom does not paint), recorded in the audit itself.
CONSTRAINTS: green only. No new dependency (DEC-001 - the coverage counter is
             sys.monitoring, the scanner is urllib, the p95 is arithmetic).
             Deterministic and offline: the LLM vars are scrubbed from every
             server the runner starts, and a passing run needs no network
             except AT-37's scan, which reports `unknown` rather than a
             fabricated clean when it cannot reach OSV. The profiling fix
             changes no measured result - the existing at-scale correctness
             tests pin the values.
ACCEPTANCE CRITERIA:
- [x] every one of AT-27..30, AT-32, AT-37, AT-38, AT-45 and AT-46 has a
      measured number attached, not a claim
- [x] AT-38 holds at every target: core >= 80%, analytical >= 90%, evidence
      >= 90%
- [x] AT-37 scans the real inventory: 0 critical, 0 high, with the scan's
      state named when it could not run
- [x] AT-28 and AT-29 hold at their p95 targets over the benchmark shapes
- [x] AT-46's boundary case holds - the counts reach the envelope and every
      surface answers in budget, including the export round trip
- [x] AT-45 is both declared with the PRD's numbers and enforced at each limit
- [x] the measurement can fail: a deliberately wrong expectation is caught for
      the percentile, the coverage ratio, the dependency counts, the envelope
      drift, the refusal and the fold
- [x] the numbers are asserted in the suite, so a regression fails a test
- [x] the profiling cost the measurement exposed is fixed and its at-scale
      correctness is unchanged
TESTS: test_measure.py (26) - the percentile's interpolation and its empty
       sample, a timing over budget failing and a timing with no samples
       measuring nothing, the boundary counts being the PRD's envelope, a
       boundary case below it or that does not answer failing, the import's
       201 as its success and a refused round trip named, the declaration
       being the PRD's numbers and a drifted limit caught, both refusals and a
       check that stopped refusing, the dependency classifier counting a
       Critical from its vector and an unreachable database answering unknown
       never clean, the coverage groups' ratios and their named shortfalls, a
       vacuous group failing, the fold green with all measurements holding,
       one failing measurement failing the gate and being named, an offline
       dependency scan red with its reason, a red web suite failing the shell
       targets, and a skipped measurement named rather than silent.
       test_python_guards.py (18) - the dunder-hardened handle and its query
       callable, read-only SQL through the handle, the import wall's refusals
       and its allowlist, the meta_path finder's installation and removal, the
       builtins' dangerous omissions, the tabulation's three shapes and two
       rejections, in-process execution and its three contract violations, the
       resource limits' restoration, and the wall-clock alarm. The suite's own
       process is kept away from the CPU rlimit the child is meant to enforce.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (644);
              `server/.venv/bin/python verification/measure/verify_measure.py`
              green (every measured threshold holds, the report written to
              verification/measure/REPORT.md);
              `server/.venv/bin/python verification/e2e/verify_e2e.py` green
              (28/28); `cd web && npm test && npm run build` green (138).
STATE UPDATE: TASKS/CURRENT_STATE gain the task. No schema change.
```

TASK: P8-MEASURE-009 - the measurement layer
ID: P8-MEASURE-009
PRIORITY: high
STATUS: DONE
SUMMARY: the PRD's thresholds were prose; nine of them are numbers now. One
         runner folds five measurements into a report with a verdict per
         acceptance test and exits non-zero when one does not hold. AT-38 is
         the suite run under a sys.monitoring line counter - core 93.9%,
         analytical 92.9%, evidence 92.4%. AT-28 and AT-29 are measured
         against a real core over HTTP: an opening p95 of 223ms against a 2s
         target over the heaviest case in the envelope, and a profiling p95 of
         1.5s against 5s over a generated 50k-row benchmark. AT-46 builds a
         case at the boundary itself - a hundred multi-dataset runs, two
         hundred findings, twelve hundred evidence edges - and requires every
         surface a reopened case offers to answer in budget, the export round
         trip among them. AT-45 is both halves: the declaration is the PRD's
         literal numbers, and a dataset past each limit is refused through the
         same function attach calls. AT-37 scans the computed inventory
         against OSV and classifies from the CVSS vector: 0 critical, 0 high,
         22 of 22 packages. AT-27, AT-30 and AT-32 are asserted in the web
         suite and the report says where the number lives instead of inventing
         one, because jsdom is not a browser.
         Two bugs the measurement surfaced, both fixed with their own tests.
         Profiling a 50k-row dataset took 12.5s against AT-29's 5s, because
         each of the profile's dozen bounded lookups re-parsed the CSV; one
         materialisation gives every later query an in-memory table and the
         same profile takes 1.7s, with no measured result changed. And the
         counter's denominator counted function-signature lines the
         interpreter never reports, so coverage read lower than it was - the
         exclusion is AST-derived, and the numerator is intersected with the
         denominator's notion of line. A third gap the coverage number named:
         the guards python_exec enforces in the child were unreachable by
         measurement, so they are tested in the process that measures them -
         eighteen tests of the dunder wall, the import wall, the builtins and
         the tabulation, which is what lifted the evidence group to its
         target. One hazard the work surfaced along the way: the CPU rlimit is
         process-wide and cumulative, so an in-process test that sets it
         delivers SIGXCPU to the suite itself once it has burned more CPU
         seconds than one run allows; the fixture that fakes the setter is
         documented for the same reason.

### FIX-PLAN-003 contract

```
TASK ID: FIX-PLAN-003
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: UX (the plan stage's missing button, W-011)
GOAL: the orientation rail names "Generate an analysis plan" and the endpoint
      that performs it, and nothing in the shell performs it. The plan panel
      reads a plan and, when there is none, tells the analyst to generate one
      - with no control that does. The loop's own to-do list points at a step
      the shipped UI cannot take, so the plan stage is only finishable from
      a terminal. The endpoint exists, is schema-validated and answers 201; the
      shell never calls it.
CONTEXT: WALK-E2E-001 Fase C reached this by following the rail and finding
         no control; `grep -rn "POST.*plan" web/src` is empty and
         `PlanPanel` holds only `getPlan`. The plan is what makes the next
         action legible, so a case that cannot plan cannot reach the stages
         after it either - the rail and the shell disagree about where the
         case stands.
INPUTS: the plan endpoint's request and response shape (main.py:3750), the
        rail's next_action and next_endpoint (workflow.py:31), the plan
        panel's empty state, and the panel's reload contract.
RELEVANT FILES: web/src/CaseWorkspace.tsx (PlanPanel, the new control),
                web/src/api.ts (a POST helper), web/src/CaseWorkspace.test.tsx
                (the tests), ai/HANDOFF.md, ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - The plan panel's empty state gains a control that POSTs the plan
    endpoint for the dataset it already reads, and busy and error states like
    every other panel's: a generation in flight is labelled, a 400 (the
    endpoint refuses to plan an unprofiled dataset) is a sentence, and a
    success reloads the plan and the case, so the rail and the panel move
    together.
  - The generated plan renders in the same panel that reads it, so the
    analyst sees what was produced without a reload, and the control is what
    the empty state's own sentence asks for.
  - A plan that already exists is not regenerated: the control is the empty
    state's answer, and a case that has planned shows its plan.
NON-GOALS: auto-generating the plan (the plan is the analyst's to ask for);
           planning against a dataset other than the first attached one; a
           plan editor (the planner writes it, the shell reads it).
CONSTRAINTS: green only. No new dependency. The POST goes to the endpoint
             that already owns the write; the panel does not fabricate a
             plan client-side.
ACCEPTANCE CRITERIA:
- [x] a case with a profile and no plan offers a control that generates the
      plan, and the plan renders without a manual reload
- [x] the rail's next_action and the control agree while generation is in
      flight and after it lands
- [x] a generation that fails shows the endpoint's own reason as a sentence
- [x] a case that already has a plan does not offer to regenerate it
- [x] the workspace's reload contract is used, so progress counts and the
      rail move with the plan
TESTS: CaseWorkspace.test.tsx (+4) - the control generates and the plan
       renders in place, the reload fires and the rail's stage completes, the
       400's own sentence surfaces beside an offer that stays, and an existing
       plan suppresses the control.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
              .venv/bin/python -m pytest -q` green (727);
              `cd web && npm test && npm run build` green (167, build ok);
              `verify_e2e.py` green; `verify_trace.py` green (48/48).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; W-011 closes.
```

TASK: FIX-PLAN-003 - the plan stage's missing button
ID: FIX-PLAN-003
PRIORITY: high
STATUS: DONE
SUMMARY: the empty state's own sentence now has the control that performs it.
         The button POSTs the endpoint that owns the write, labels itself
         while the planner works, and on success renders the plan in place and
         calls the workspace's reload - so the rail's stage, the progress
         counts and the panel move together, because the plan is what makes
         the rail's next action legible. A refusal shows the endpoint's own
         reason as a sentence and the offer stays; a case that has already
         planned shows its plan and offers nothing. One thing the first test
         run caught and fixed: the generation's error shared the read's
         `error` state, and the empty state rendered that only in its
         non-missing branch - so a 400 in the missing branch was swallowed
         and the panel stayed silent, exactly the failure the fix exists to
         remove. The two are separate states now (`generateError`), because
         they are never both live: the control lives where the read answered
         404, and a 404 is not the reason a generation failed.


### P9-F2-001 contract

```
TASK ID: P9-F2-001
MILESTONE: P9 UI/UX Redesign (phase F2, the surfaces)
CAPABILITY: Surfaces (the walk-test's last three findings)
GOAL: the redesign's first delivered surface change, and the last of
      WALK-E2E-001's findings. F1 made the redesign possible and moved
      nothing the analyst sees; F2 pays the first part of the debt by
      fixing the three findings that were left open because they were
      defects a redesign had to own rather than patches on the old CSS:
      a run that landed but never appeared until a reopen (W-013), an
      error message that named the artifact when the field was empty
      (W-017), and a capability that worked but the shell never said
      it had (W-018). The full restyle of the panels onto the tokens is
      F2's second half, P9-F2-002.
CONTEXT: W-013 is `GeneratePanel.run()`, which posted to the runs
         endpoint and cleared its proposal but never called `onChanged`,
         so the workspace never re-read the case and the runs panel kept
         answering the state before the run; the finding's own report
         names the double-run it caused. W-017 is the EVALUATE panel's
         single catch, which showed `messageOf(err)` verbatim: three
         different causes answer 400 (`the artifact's code is empty`, `no
         claim was submitted to audit`, `not a single read-only query`)
         and the core's sentences all name the artifact, so an analyst
         who left a field blank read it as their SQL being refused.
         W-018 is the chat panel, whose memory recalls findings from the
         analyst's other cases (P6-MEMORY-001) and whose shell said
         nothing about it. The three are together because none needs a
         new endpoint, a new component or a new dependency - each is one
         panel's own surface, and the constraint they share is the one
         the panels test pins: the split's exports stay a complete set.
INPUTS: `web/src/panels/GeneratePanel.tsx` (the run), `DataPanel.tsx`
        (the only render of it), `EvaluatePanel.tsx` (the catch), and
        `Chat.tsx` (the hint), plus `CaseWorkspace.test.tsx`'s existing
        assertions, which are the behaviour contract.
RELEVANT FILES: the four panels above, `web/src/CaseWorkspace.test.tsx`
                (+3 tests), `web/src/panels/panels.test.tsx` (the two
                new exports the split test now resolves), and
                `ai/HANDOFF.md`, `ai/TASKS.md`, `ai/CURRENT_STATE.md`.
REQUIRED CHANGE:
  - W-013: `GeneratePanel` accepts `onChanged` and calls it once the run
    endpoint answers, before it clears the proposal, so the workspace
    re-reads the case and the runs panel, the rail and the evidence
    graph pick the run up without a reopen. The panel stays pure: the
    workspace owns the reload, exactly as `RunsPanel`, `DataPanel` and
    `FindingsPanel` already do. The kind selector is untouched - the
    proposal's own kind still decides the endpoint.
  - W-017: a named map, `EVALUATE_REFUSALS`, carries each 400 the audit
    endpoint raises to its own sentence, and `evaluateRefusal(error)` is
    the single place the panel's catch goes. The key is the core's own
    detail string, not an invented code, so a core that rewords a
    refusal reads as an unknown 400 and is shown verbatim: the honesty
    budget is not paid by hiding a reason the map stops recognising. A
    non-400 and a network failure still take the path they always did.
  - W-018: one muted sentence under the chat panel's heading says the
    memory is cross-case and names what it cannot do. No new control, no
    new endpoint, and no claim the hint itself measures - the capability
    was already tested; the hint is the discoverability.
  - The token layer `lib/ui.tsx` gains the `surfaces` strings and an
    `accent` that is a class rather than a hex, so F2-002's restyle
    composes them. Nothing imports them yet, by the same rule that let
    F1 ship its dependencies unused.
NON-GOALS: restyling any panel onto the tokens (F2-002), motion (F3),
           the on-screen chart (F4), changing any endpoint or its
           response shape, changing any verdict vocabulary, and touching
           the server at all - the three findings are the shell's.
CONSTRAINTS: green only. No new dependency (DEC-001 - the three fixes
             are plain React). Deterministic and offline. The
             accessibility audit's STATUS_CLASSES contract is unchanged:
             no status class is added or removed, and nothing new carries
             a status by colour alone.
ACCEPTANCE CRITERIA:
- [x] a run posted from the generate panel appears in the runs panel
      without reopening the case, and the proposal clears so the same
      code is not offered twice
- [x] the three causes that answer 400 each show their own sentence,
      naming the field that is wrong rather than the artifact
- [x] a 400 the map does not recognise is shown verbatim, not swallowed
- [x] the chat panel states that its memory reaches across cases
- [x] the panel split's completeness test still resolves every export
      the workspace renders, including the two new ones
- [x] no other behaviour moved: the existing 181 assertions pass
      unchanged
TESTS: `CaseWorkspace.test.tsx` (+3) - the run landing reloads the case
       (the workspace's own `listRuns` is called again and the "Run
       this" button is gone), the three EVALUATE causes are named
       separately in one flow, and the chat hint renders.
VERIFICATION: `cd web && npm test && npm run build` green (184 = 181
               + 3, tsc clean, build ok);
               `server/.venv/bin/python verification/trace/verify_trace.py`
               green (48/48 rows, AT-48 PASS - the symbols the matrix
               cites still resolve). The change is web-only, so the
               server suite, the e2e, golden, refine and measure gates
               are not re-run: no line outside `web/` moved (verified by
               `git status`), and their last runs are green at 727,
               28/28, 21/21, AT-04 and 9/9.
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the task; the P9 table
              opens at F2-001. No schema change, no version bump. The
              walk-test's open findings are all closed: W-013, W-017,
              W-018 here, W-001/W-005/W-008/W-009/W-011/W-014/W-015/W-016
              before it.
```

### P9-F2-001 done-record

```
TASK: P9-F2-001 - the walk-test's last three findings
ID: P9-F2-001
PRIORITY: high
STATUS: DONE
SUMMARY: F1 moved nothing the analyst sees; this is the first surface
         change of the redesign and it closes the walk-test's last
         three. W-013: a run the generate panel posted landed in the
         core and the panel cleared its proposal, but the panel never
         told the workspace to re-read the case, so the runs panel kept
         saying no analysis had run until the case was reopened - and
         the finding's own report records the analyst double-running it.
         The panel now calls `onChanged` the way every other writing
         panel does, and the run appears where it landed. W-017: three
         causes answer 400 from the audit endpoint and the core's
         sentences name the artifact in all three, so an empty field
         read as the SQL being refused. `EVALUATE_REFUSALS` maps each
         detail string to its own sentence naming the field, and
         `evaluateRefusal` is the one place the catch reads; the key is
         the core's own wording, so a reworded refusal is an unknown 400
         shown verbatim rather than hidden. W-018: the chat memory
         recalls other cases' findings and the shell never said so; one
         muted sentence under the heading is the surface. The token
         layer gained the `surfaces` strings F2-002 composes, imported
         nowhere yet, by the same rule that let F1 ship its deps unused.
```

### FIX-EVIDENCE-002 contract

```
TASK ID: FIX-EVIDENCE-002
MILESTONE: post-phase (the walk-test's findings)
CAPABILITY: Validation (the evidence check's number regex, W-015)
GOAL: a finding whose statement names a `YYYY-MM` period - or any value whose
      digits sit inside a longer token - fails the evidence dimension with
      "quotes values absent from its own result", and the dimension is HARD,
      so the verdict is insufficient_evidence. The finding was correct: every
      magnitude it quoted was a cell value in its own run. The check invented
      two numbers by splitting a token, then refused the finding for quoting
      them. This makes the check compare the magnitudes a statement actually
      quotes against the magnitudes the result actually holds.
CONTEXT: found by WALK-E2E-001's Fase C, reproduced directly in the
         interpreter: `_numbers_in("2026-07 has the highest revenue at
         1526309.57, the largest of 44 grouped value(s)")` returns
         `[-7.0, 44.0, 2026.0, 1526309.57]`, and `2026.0` and `-7.0` are not
         in `_allowed_numbers`. The same `_numbers_in` backs
         `drafter.py:246`, `evaluator.py:379` and `validation.py:220`
         (check_evidence, the HARD one), so the fix lands once and all four
         sites stop splitting tokens. A second defect surfaced in the same
         run: `_allowed_numbers` does not include the row count or the number
         of groups a result has, so "44 grouped value(s)" - which the
         deterministic drafter writes and which is true - was also reported
         invented. Both are the evidence dimension's honesty budget.
INPUTS: the statement and the run's columns and rows, exactly as check_evidence
        receives them; the deterministic drafter's own sentence shapes, which
        are what a correct regex must accept; the EVALUATE corpus, which
        judges the same field.
RELEVANT FILES: server/app/evaluator.py (`_numbers_in`, `_allowed_numbers`),
                server/app/validation.py (no change beyond the behaviour it
                reads), server/tests/test_validation.py and
                server/tests/test_evaluator.py (the tests), ai/HANDOFF.md,
                ai/TASKS.md, ai/CURRENT_STATE.md
REQUIRED CHANGE:
  - A numeric token is only a magnitude when it is a token, not a fragment of
    one. A run of digits that sits inside a longer alphanumeric run - a date
    like 2026-07, an id like ORD-100331, a code like SKU-4001 - is not a
    number the statement quotes, so the regex must not emit it. The
    neighbouring characters are what decide: digits bounded by digits,
    commas, dots, whitespace or string edges are magnitudes; digits with a
    letter or a hyphen-then-digit against them are part of something larger.
    A negative number is only negative when its minus is a sign, not a date's
    separator, which is the exact confusion that produced -7.
  - `_allowed_numbers` gains the row count and the number of groups the
    result has (the distinct count per column already covers frequency, but
    not the totals the drafter names as "N grouped value(s)" or "N row(s)"),
    so a statement that names the shape of its own result is quoting a
    magnitude the result holds.
  - A claim that names a magnitude a result does not hold still fails - the
    honesty budget's purpose is unchanged, and a fabricated number in a
    correct-looking sentence still must not pass.
NON-GOALS: changing the verdict vocabulary or the HARD/soft classification;
           re-judging the golden suite's reference claims (they pass and keep
           passing); teaching the check to parse dates semantically (the fix
           is that it stops counting them, not that it understands them).
CONSTRAINTS: green only. No new dependency (DEC-001). Deterministic and
             offline: the check is pure over its inputs. Read-only: it
             judges, it never writes.
ACCEPTANCE CRITERIA:
- [x] a finding naming `YYYY-MM` periods with correct magnitudes passes its
      evidence dimension, where before it failed as insufficient_evidence
- [x] a date, an id and a sku are not extracted as magnitudes, verified per
      shape
- [x] a negative number inside a longer token is not emitted as one
- [x] a statement naming its result's own row count or group count passes
- [x] a genuinely fabricated magnitude still fails, and the failure names the
      invented number
- [x] the golden suite's reference claims still hold their evidence verdicts
- [x] the evidence check's sentence, when it fails, still names what the
      statement quoted that the result does not hold
TESTS: test_validation.py (+5) - the WALK-E2E-001 regression as a literal case
       (a `YYYY-MM` statement over twelve monthly rows passes evidence), a
       date / id / sku shape emitting no magnitude, a negative inside a token
       versus a real negative, the group-count allowance, and a fabricated
       magnitude still failing.
VERIFICATION: `cd server && DAH_LLM_API_KEY= DAH_LLM_BASE_URL= DAH_LLM_MODEL=
               .venv/bin/python -m pytest -q` green (694 + 5 = 699);
               `verification/e2e/verify_e2e.py` green (all steps);
               `verify_golden.py` green (21/21 reference, 21/21 workflow);
               `verify_refine.py` green (AT-04);
               `verify_measure.py` green (9/9);
               `verify_trace.py` green (48/48);
               `cd web && npm test && npm run build` green (138).
STATE UPDATE: TASKS/CURRENT_STATE/HANDOFF gain the fix; the walk-test's
              W-015 closes. No schema change, no version bump.
```
