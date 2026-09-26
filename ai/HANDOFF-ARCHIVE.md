# DAH - Handoff Archive

Older `## Next action` sections and legacy change logs, moved out of
`ai/HANDOFF.md` by the rolling-window rule in `AGENTS.md` so a fresh session
can resume without reading the project's whole narrative history. Nothing here
is edited on the way in - these are the records as they were written. Look here
for the reasoning behind a past task; look at `ai/HANDOFF.md` for what to do
next.

---

## Next action

**P9-F2-001 (the walk-test's last three findings) DONE.** F1 moved nothing
the analyst sees; this is the redesign's first surface change, and it closes
the three findings that stayed open because they were the shell's, not the
CSS's.

W-013: a run the generate panel posted landed in the core and the panel
cleared its proposal, but the panel never told the workspace to re-read the
case, so the runs panel kept saying no analysis had run until a reopen -
the walk-test's own report records the analyst double-running it. The panel
now calls `onChanged`, as every other writing panel does.

W-017: three causes answer 400 from the audit endpoint and the core's
sentences name the *artifact* in all three, so an analyst who left a field
blank read it as their SQL being refused. `EVALUATE_REFUSALS` maps each of
the core's own detail strings to its own sentence naming the field, and
`evaluateRefusal` is the one place the catch reads. The key is the core's
wording, so a reworded refusal is an unknown 400 shown verbatim rather than
hidden - the honesty budget is not paid by swallowing a reason the map
stops recognising.

W-018: the chat memory recalls other cases' findings and the shell never
said so. One muted sentence under the heading is the whole surface.

One operational lesson. The first mapping key I wrote was an invented code
(`empty_code`), and the test failed on the real message string. A refusal
map keyed on anything but the core's own sentence is a second contract the
core never agreed to; key on the words the endpoint actually sends.

**Gates:** web 184 (181 + 3), tsc clean, build ok, trace 48/48. Web-only -
no line outside `web/` moved, so the server suite (727), e2e (28/28),
golden (21/21), refine (AT-04) and measure (9/9) are not re-run.

**Next, in priority order:**

1. **P9-F2-002, the restyle.** The debt F2 took on: `lib/ui.tsx` ships a
   `surfaces` set (panel, heading, subpanel, proposal, card, row) and an
   `accent` that is a class rather than a hex, and nothing imports them yet
   - by the same rule that let F1 ship its dependencies unused. The panels
   swap their `className="panel"` / `"subpanel"` / `"proposal"` / `"run"`
   for those strings, one zone at a time (work, orientation, intelligence,
   then CaseList/CaseCreation), green at each. The old CSS rules stay until
   every consumer has moved, then the dead ones go in one pass - deleting a
   rule a panel still reads is how a restyle breaks an audit that reads the
   emitted stylesheet.
2. **Then F3** motion (respecting `prefers-reduced-motion`) and **F4** the
   chart surface (recharts, which F1 installed and F2 still does not
   import), then a re-walk.

The walk-test's findings are all closed now: W-013/W-017/W-018 here,
W-001/W-005/W-008/W-009/W-011/W-014/W-015/W-016 before it.

## Next action

**FIX-CHART-004 (W-016) DONE.** A chart is an evidence artifact the core
renders, stores and exports, and the shell could not produce one. The chart
endpoint answered 201 while `web/src` never called it - `grep -c chart
web/src/api.ts` was zero - so every chart was reachable only through its file
path and every PNG only through that.

The run row now holds the control and the surface. `web/src/api.ts` gained
`createChart`, `chartImageUrl` and `getChartImage`; `RunRow` gained a
`ChartPanel`. The control appears once the analyst has opened the run's rows,
because those columns are the renderer's input and are exactly what its
pickers offer - a column the run does not have is not among the choices, and
the measure defaults to a numeric column. A success POSTs the endpoint that
owns the write, fetches the SVG the core drew and renders it inline through
`dangerouslySetInnerHTML`: the shell draws what the core already drew rather
than re-rendering it, because a second renderer would be a second source of
truth for what the chart looks like. A PNG is a link to the persisted artifact
instead of a redrawn image. The workspace reloads with a chart, so the
evidence graph's count moves with the panel; a refusal shows the renderer's
own sentence and the control stands.

Two things the first test run caught: the control was offered before the rows
were read, which is before there is anything to draw from, so it now waits on
the result; and the surface was asserted as an img role, which jsdom does not
give an inline SVG - the assertion reads the element instead.

**Gates:** 727 server (unchanged), web 173 (+6), tsc clean, build ok,
e2e 28/28, trace 48/48.

**Next, in priority order:**

1. **FIX-PYTHON-005 (W-016)** - the other half. The codegen panel generates
   SQL only and posts to the SQL runs endpoint; a python run is only
   reachable by curl, so the hard sandbox (P3-SEC-001, the hardening the
   sandbox exists to prove) is untested by anyone using the app. The
   generator already supports kind 'python' and the endpoint and its
   `PythonRunCreate` model already exist; only the shell's request is
   missing. `web/src/api.ts` gains a python run helper and the codegen panel
   gains a kind, its proposal matching it. Contract in `ai/TASKS.md`.
2. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,800 lines into `web/src/panels/`), F2 the surfaces
   (closing what remains of W-013, W-017, W-018 - W-011 and W-016 are now
   closed), F3 motion (respecting `prefers-reduced-motion`), F4 the chart
   surface and a re-walk.


**FIX-PROFILE-008 (W-008) DONE.** Opening a case no longer writes to it. The
mount effect called `profileDataset` - a POST - per attached dataset on every
visit, and strict mode's double render made it two, so a profile that already
existed was recomputed and rewritten, and the step the rail names as the
analyst's was being silently completed by the shell. The GET endpoint already
existed (`server/app/main.py:1654`, a 404 when nothing is stored), so the fix
is a new `getProfile` in `web/src/api.ts` and a one-word change at
`web/src/CaseWorkspace.tsx:196`: the mount reads. The POST moved to a control
in the Data panel - "Re-profile" beside a dataset that has a profile, "Profile
this dataset" for one that does not, replacing the "profiling…" placeholder
that was the shell finishing the step.

**Gates:** 723 server (no change), web 147 (+4), tsc clean, build ok.

A design note worth carrying: the contract's "a GET is preferred to a POST
when the endpoint can answer one" turned out to already be answered - the
read endpoint shipped in P2-DATA-007 and the write was the only thing the
shell ever called. The panel and the rail now agree about the profile stage
because the panel is no longer the thing that completes it; a read per mount
is correct and a write is not.

**Next, in priority order:**

1. **FIX-UPDATES-009 (W-005)** - the Check for Updates item performs a check
   and reports it to a log only; the three statuses the core distinguishes
   never reach the window. `desktop/src-tauri/src/main.rs:48-60` is the
   handler; the delivery is added, not substituted. Contract in
   `ai/TASKS.md`.
2. **Then FIX-VERSION-010 (W-001)** - a dev checkout answers `current: 0.1.0`
   because `server/app/updates.py` reads the stale installed metadata before
   the pyproject beside the source. Fix-VERSION-001's stamp stays first; the
   source moves ahead of the metadata.
3. **FIX-PLAN-003 / FIX-CHART-004 / FIX-PYTHON-005** precede none of these in
   the table but FIX-PLAN-003 is the next of them in priority - the rail
   names "Generate an analysis plan" and no control performs it.
4. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,501 lines into `web/src/panels/`), F2 the surfaces
   (closing W-011, W-016, W-013, W-017, W-018), F3 motion (respecting
   `prefers-reduced-motion`), F4 the chart surface and a re-walk.



## Next action

**FIX-REFINE-007 (W-009) DONE.** The refinement's "Why these changes" no longer
hides behind a click. The panel rendered the API's `rationale` and `grounds`
inside a `<details>` that ships collapsed, and the walk-test clicked the
heading and saw nothing - the data was a curl away in
`walktest/evidence/refine-latest.json`, complete, and the panel had it. A
disclosure widget was the wrong primitive for the answer to the panel's own
question, so it is gone: `web/src/RefinePanel.tsx:185-209` now renders a
real `<h4>Why these changes</h4>`, the rationale under it, and the grounds as
a list, always visible. `web/src/index.css` gives the block the same left rule
and ground the proposals use, so it reads as the proposal's support rather
than another paragraph, and gains `.panel h4` because no panel had used one.

**Gates:** 723 server (no change), web 95/95 in the file and the suite's
143 (+3), tsc clean, build ok, e2e all steps, golden both thresholds, refine
AT-04, measure 9/9, trace 48/48.

One diagnosis worth carrying: the instinct was a styling bug, and the fix is
not one. A collapsed `<details>` shows its summary but nothing else, with no
affordance the panel announces; the heading read as inert text. Where a panel
asks "why" and the API answers, the answer is shown - a disclosure is for
detail the analyst may want to skip, and this is the reason they are being
asked to decide at all.

**Next, in priority order:**

1. **FIX-PROFILE-008 (W-008)** - the shell POSTs the profile endpoint on every
   case mount, so opening a case re-profiles and rewrites, and strict mode's
   double render makes it two writes. `web/src/CaseWorkspace.tsx:191` is the
   effect; contract in `ai/TASKS.md`.
2. **Then FIX-UPDATES-009 (W-005)** (Rust + the window's own message surface)
   and **FIX-VERSION-010 (W-001)** (`server/app/updates.py`'s resolution order
   reads the stale metadata before the pyproject beside the source), order
   free. **FIX-PLAN-003 / FIX-CHART-004 / FIX-PYTHON-005** precede none of
   these in the table but FIX-PLAN-003 is the next of them in priority.
3. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,501 lines into `web/src/panels/`), F2 the surfaces
   (closing W-011, W-016, W-013, W-017, W-018), F3 motion (respecting
   `prefers-reduced-motion`), F4 the chart surface and a re-walk.

## Next action
**P8-TRACE-010 is DONE, and P8 with it.** The PRD's own control artifact
(section 59) is code rather than a document: forty-eight rows carry every
acceptance threshold from the PRD, through the UX surface, the implementation
and the test, to the threshold that says it holds. `verification/trace/
verify_trace.py` resolves every cell against the repository as it stands, so
a renamed symbol, a deleted test, a renumbered UX section, an uncommitted
report or a red one is a named failure instead of a claim that quietly stopped
being true. 48/48 rows PASS, and AT-48's own thresholds compute from that:
15/15 release-blocking requirements traceable (100%) and 33/33 of the rest
against a >= 95% target.

The requirement set is checked against the PRD's own headers, so an acceptance
threshold the PRD adds is a red gate until a row exists for it - and a row the
PRD no longer states is a phantom the gate rejects. Fifteen rows are P0 by the
PRD's section 53, each naming the release-blocking category it guards. The
matrix is honest about which rows are measured and which asserted: the measured
ones cite a runner and its committed report, the asserted ones name the suite.

**Gates:** 686 server (+42 in test_trace.py), 138 web, build green, 28/28 e2e,
golden 21/21, refinement's four thresholds, the measurement layer 9/9, and the
matrix 48/48.

### What is next, in priority order

- **Nothing is open.** P8 is complete (10 of 10) and **v0.3.0 is published**
  (`ab56541`, pre-release with its checksum): the phase's releases are v0.2.0
  and v0.3.0. The roadmap's remaining ladder - cloud, collaboration, warehouse
  connectors, governance - stays deferred at a user count of one, and the
  conformance evaluation's deliberately-not-built list is explicit deferral.
  Two environmental notes carry: CI's billing is still suspended, so nothing
  since `c73118c` has run in CI; and the Ventura floor is documented but no
  longer CI-enforced (DEC-005).


## Next action
**P8-MEASURE-009 is DONE**: the PRD's thresholds were prose, and nine of them
are numbers now. One runner folds five measurements into a report with a
verdict per acceptance test and exits non-zero when one does not hold -
`server/.venv/bin/python verification/measure/verify_measure.py`, 9/9 PASS.

Measured: AT-38 is the suite itself under a `sys.monitoring` line counter
(core 93.9%, analytical 92.9%, evidence 92.4%, all above the PRD's targets);
AT-28 an opening p95 of 223ms against 2s over the heaviest case in the
envelope; AT-29 a profiling p95 of 1.5s against 5s over a generated 50k-row
benchmark; AT-46 a case built at the boundary - a hundred multi-dataset runs,
two hundred findings, twelve hundred evidence edges - with every surface a
reopened case offers answering in budget, export round trip included; AT-45
declared with the PRD's numbers and refused at each limit; AT-37 scanned
against OSV, 0 critical / 0 high over 22 packages. AT-27, AT-30 and AT-32 are
asserted in the web suite and the report says where the number lives rather
than inventing one - jsdom is not a browser.

Three findings the measurement made, each fixed with its own tests. Profiling
a 50k-row dataset took 12.5s against AT-29's 5s, because each of the profile's
dozen bounded lookups re-parsed the CSV; one materialisation into a temp table
gives every later query an in-memory table and the same profile takes 1.7s,
with no measured result changed. The counter's denominator counted
function-signature lines the interpreter never reports, so coverage read lower
than it was - the exclusion is AST-derived and the numerator is intersected
with the executable set. And the guards `python_exec` enforces in the child
were unreachable by measurement, so eighteen tests now exercise them in the
process that measures them - which is what lifted the evidence group to its
target, and is worth more than relying on the child to reach them.

**Gates:** 644 server (+44: 26 measurement, 18 guards), 138 web, build green,
28/28 e2e, the golden suite still 21/21 and AT-04's four still holding.

### What is next, in priority order

- **P8-TRACE-010** - the traceability matrix (AT-48); last, because it traces
  what 1-9 delivered. Every AT now has a number for it to point at.


## Next action
**P8-GOLDEN-005 is DONE**: the trust machinery is measured. Three fixtures
(sales, spend, tickets) carry 21 reference calculations covering all ten of
AT-40's shapes; each golden value is computed twice before the engine is asked
- by hand, and by an independent Python path over the CSV, never DuckDB - and a
disagreement fails the suite, because a fixture the two paths disagree on is a
wrong fixture. Then a real server answers the same question over HTTP: 21/21
match (AT-40, threshold 100%). The same 21 journeys answer AT-01, because the
query a scripted run makes *is* the reference query - 21/21 complete the loop
over 3 datasets (thresholds 95%, 20 runs, 3 datasets). Both numbers are
asserted in test_golden.py, and a deliberately wrong expectation is caught by
the audit, so the measurement is known to be able to fail. The suite is offline
by construction: the runner fails the `plan` stage unless the planner answers
`source: "deterministic"`, so a completion rate above zero proves no LLM was
called. An `insufficient_evidence` verdict still counts complete - a finding
the evidence does not support is a finished analysis.

**Two real bugs the suite surfaced**, each fixed with its own test: grouping by
a date column handed a raw `datetime.date` to `json.dumps` and answered a 500
for a valid query (the profile already described a date as an ISO string; the
run path now agrees, and Decimals and bytes are covered by the same rule); and
the runner's health check raced the stdout pump thread for the server's
announcement, blocking forever on a `readline()` with no timeout.

**Gates:** 477 server (6 for this task: 5 fast data-layer tests plus the one
slow measurement), 86 web, build green, 25/25 e2e.

### What is next, in priority order

- **P8-SHELL-006** - the orientation spine (AT-33/34/35): the shell tells an
  analyst where they are in the loop and what the next action is.
- **P8-REFINE-007** - question refinement (AT-04), editing the context object
  P8-CONTEXT-001 built.
- **P8-DECISION-008** - the decision view (UX 46).

**P8-QUALITY-002 is DONE**: a profile states what the data *cannot* support,
before the analyst spends a question on it. AT-08 names seven defect classes
and AT-09 requires each to carry an analytical impact; before this, two
classes existed as bare counts - "1 null value(s)" - and they surfaced only at
validation, after a finding existed. The UX document (section 15) wants quality
visible at the Data stage, before analysis. That is where it now is.

The two pre-existing classes (missing values, duplicate rows) gained impact
sentences. Five are new, each raising only on evidence the profile itself
measured - never on a heuristic that could fire on clean data, which is what
holds AT-08's <= 5% false-positive budget before the golden suite that will
measure it exists:

- **invalid_types** - a column typed `other` that is mostly numeric or temporal
  but not entirely. This is the defect that breaks a calculation *silently*:
  DuckDB types the column VARCHAR, the SQL still runs, and a SUM yields NULL or
  a comparison drops the row instead of erroring.
- **inconsistent_categories** - case/whitespace variants ("north" vs "North")
  that split a GROUP BY without any error.
- **date_gaps** - a hole in an otherwise regular series, so a
  period-over-period comparison treats non-adjacent windows as consecutive.
- **extreme_values** - a value dwarfing its neighbour. Measured against the
  *next* value, not a mean, because an outlier inflates the very statistics a
  z-score would measure it with.
- **insufficient_coverage** - too few rows for a comparison to mean anything,
  or a category so dominant a group-by is really about that one group.

One design decision worth carrying: the extreme-value detector compares the
largest value against the next-distinct value rather than using a z-score. The
obvious implementation - mean and standard deviation - is the one the defect
defeats, because the outlier moves the mean and inflates the deviation it is
measured against. Comparing against a neighbour is robust to exactly the case
the detector exists for, and a run of ties at the top is correctly read as a
repeated value rather than an extreme.

The list is computed inside the profiler's own pass with bounded queries (top-k
for extremes, distinct lists for temporal, one scan for the type casts), so a
profile costs what it cost plus targeted lookups rather than a scan per
detector. It persists as schema v11 (a v10 store opens, upgrades and keeps
every row), travels with an exported case and survives a duplicate. The
validation endpoint's missing-data check now reads the same impact sentence the
Data stage shows, so the audit and the panel cannot drift apart on the same
null.

**435 server tests** (26 new in test_quality.py: one raising test per class,
false-positive guards for each, persistence across reopen, the export round
trip and the v10->v11 migration), **84 web tests** (2 new for the Data-stage
panel), the build green and all 25 real-server e2e steps passing. The schema
is at v11.

The v0.2.0 release this landed after is published; CI's billing is still
suspended (see below), so nothing pushed since c73118c has run in CI.

### What is next, in priority order

- **P8-VALID-003** - validation from 3 checks to the PRD's 9 dimensions
  (AT-17). The largest single trust gap, and the natural consumer of this
  task's work: the EVALUATE engine already computes a nine-axis audit, but it
  is pointed at imported work rather than at the case's own findings.
- **P8-CAUSAL-004** - the causal-language guard (AT-18).
- **P8-GOLDEN-005** - the analytical golden suite with reference values (AT-40)
  and the workflow-completion rate (AT-01). This is what *measures* the
  95%/5% thresholds the detectors above were built to hold.

## Next action
**The v0.2.0 release is DONE, and it is published.** Tag `v0.2.0` sits on
`ec819fc` (the bump commit), matching `server/pyproject.toml` as `release.yml`
demands. 409 server tests pass on the tag, run by hand. The sidecar, `.app`
and DMG were built locally from the same steps the workflow runs, the packaged
core was proven on an isolated store - profile -> plan (it reads the context:
`context_basis: ['purpose','sub_questions:2','hypotheses:2']`) -> generated SQL
-> run -> interpret -> draft -> accept -> validate, ending honestly on
`partially_supported` because the null revenue trips `missing_data` while
`reproducibility` passes - and the ditto zip plus its sha256 were published as
a flagged pre-release:
github.com/jensuid/DA-Harness/releases/tag/v0.2.0

**One thing needs your attention, and it is not code.** GitHub Actions is
refusing to start *any* job - the Release workflow and both CI suites - with
"recent account payments have failed or your spending limit needs to be
increased". It is an account billing problem (Settings > Billing & plans), and
it is why this release was built and uploaded by hand instead of by
`release.yml`. Nothing pushed since `c73118c` has run in CI, so local gates
are the only green signal right now. Fix the billing and the pipeline works
unchanged; the workflow itself is correct and would have produced these exact
artifacts.

The shipped `.app` in `desktop/src-tauri/target/release/bundle/` is current to
`ec819fc` - it carries the Context panel, the CORS fix and the comma fix. The
user's *running* app is still the P7-CSV-002 build; relaunch from the new
bundle if they want the Context panel, and the store at
`~/Library/Application Support/com.jensuid.dah/` survives the swap (a Cmd+R
in the window is all the shell needs after).

### What is next, in priority order

- **P8-QUALITY-002** - quality detection beyond missingness. The profile finds
  missing values and duplicate rows; the PRD wants seven defect classes
  (AT-08), each with an *impact* sentence (AT-09) shown at the Data stage,
  *before* analysis, rather than only at validation. The context object is
  already in place, so an impact can be phrased against the case's stated
  purpose instead of generic boilerplate.
- **P8-VALID-003** - validation from 3 checks to the PRD's 9 dimensions
  (AT-17). The largest single trust gap. The EVALUATE engine already computes a
  nine-axis audit; it is pointed at imported work, never at the case's own
  findings.
- **P8-CAUSAL-004** - the causal-language guard (AT-18).
- **P8-GOLDEN-005** - the analytical golden suite (AT-40) and the
  workflow-completion rate (AT-01). This is what turns the above into measured
  numbers.

# DAH - Handoff

## Next action
**P8-CONTEXT-001 is DONE**, and with it the first of the PRD's Level 1 gaps
closes: a case carries the analyst's stated intent, not just a question string.
AT-03 requires purpose, sub-questions and hypotheses to be captured, edited and
reopened; a case was `question + dataset` before this.

A new `contexts` table (schema **v10**) holds a purpose and three lists -
sub-questions, hypotheses, known constraints. The primary question stays on the
case row, where it was already editable, rather than being duplicated. `GET
/cases/{id}/context` answers an empty default instead of a 404, so the shell's
form always has something to render; `PUT` replaces the whole object so a retry
after a failed save leaves the store identical to the form rather than merging
two drafts. Malformed input answers 400 and changes nothing.

Three readers now consume the intent:

- **The planner.** The analyst's sub-questions and hypotheses are prepended to
  the ones the profile suggests - intent outranks inference - and a stated
  purpose stands in for a thin objective. The plan records a `context_basis`
  naming the fields it actually read, on *both* engines: `_basis_for` describes
  the intent the caller supplied, not which engine spoke, so the basis and
  `source` answer two different questions.
- **The assistant.** "What is this case trying to establish?" is answered from
  the stated purpose and hypotheses, citing `context:purpose` and
  `context:hypotheses`. The branch sits *ahead* of the column branch on
  purpose: that question names no column, and without it the assistant fell
  through to whichever statistic it could find.
- **Export, duplicate and delete.** The context travels with an exported
  package and is restored on import; a duplicate carries it; a delete removes
  it. An older package without the section degrades to an empty context rather
  than erroring.

One thing worth carrying: the LLM path initially recorded no basis at all. The
plan came back `source=llm` with no `context_basis`, which read as though the
intent had been ignored when it had in fact been in the prompt. A basis
describes what was *asked*, so it is recorded on whichever engine answers - an
engine that ignored the intent still records that it was supplied.

**409 server tests** (21 new), **82 web tests** (4 new), the build green, and
all 25 real-server e2e steps passing. The schema is at v10 and a v9 store opens,
upgrades and keeps every row.

### What is next, in priority order

- **P8-QUALITY-002** - quality detection beyond missingness. The profile finds
  missing values and duplicate rows; the PRD wants seven defect classes
  (AT-08), each with an *impact* sentence (AT-09) shown at the Data stage,
  *before* analysis, rather than only at validation.
- **P8-VALID-003** - validation from 3 checks to the PRD's 9 dimensions
  (AT-17). The largest single trust gap. The EVALUATE engine already computes a
  nine-axis audit; it is pointed at imported work, never at the case's own
  findings.
- **P8-CAUSAL-004** - the causal-language guard (AT-18), sitting on the verdict
  vocabulary P8-VALID-003 formalises.
- **P8-GOLDEN-005** - the analytical golden suite with reference values (AT-40)
  and the workflow-completion rate (AT-01). This is what turns the above into
  measured numbers.
- **P8-SHELL-006** - the orientation spine: the persistent workflow rail with
  per-stage status, the three-zone adaptive workspace, the case overview, and
  rendering the three numbers the walkthrough found unrendered. Deliberately
  after 001-005: the panels place objects that already exist, so the objects
  should exist first.
- The release (v0.2.0) remains independent and unblocked - tag it any time.

### The packaged app is behind this change

The shipped sidecar was rebuilt for P7-CSV-002 and is current to that commit,
not this one. Rebuild before the next release:

    cd server && ./build_sidecar.sh && cd ../desktop && npm run tauri -- build

---

## Next action
**P7-CSV-002 is DONE**: an analyst's CSV is accepted as it arrives. The first
three worked cases were being seeded into the shipped app when one fixture -
`106,2024q3,west,,` - made the profiler answer `columns:
['order_id,quarter,region,revenue']`: one column holding each raw line, and a
profile that describes nothing. The SQL written from those columns then failed
on the same file it was derived from.

The file was not corrupt; one row was *wider* than its header. read_csv_auto
guesses the delimiter, and a row carrying more fields than the header derails
that guess. The bisect is worth remembering, because the honest shape next to
it works: `106,2024q3,west,` (an empty revenue, matching the header's four
fields) is a null and always profiled correctly; the collapse needs the *extra*
comma, and only when more rows follow it. One keystroke past a null, and the
whole table stops being a table.

`server/app/analysis.py` gains `_sniffed_reader_for`, and all four reader call
sites go through it - `_bind_dataset`, `_bind_datasets`, `profile_csv` and
`_duplicate_row_count` - because a profile that recovered while its runs
collapsed would describe columns the SQL cannot see. It compares the sniffed
width against the header's own comma count and re-sniffs with
`ignore_errors=true` when sniffing collapsed, taking that only when it widens
the description. Every row survives; the stray field becomes a null, which is
what the missing-data check exists to catch.

`null_padding=true` is *not* the fix and the reason is the lesson: it widens
the table to fit the mistake, inventing a synthetic `column4` and silently
extending every row. `ignore_errors` narrows the mistake to fit the table.
Only one of those keeps the file the analyst uploaded.

The retry is conditional on purpose and that is a security-shaped decision, not
a lazy one: `ignore_errors` on a well-formed file would turn a genuine
conversion error into a silent null, so it is *earned* by a collapse, never
applied by default. A quoted header containing a comma overcounts by one, and
the widening guard means that costs a single sniff and changes nothing.

**388 server tests** (4 new; each proven to fail on the pre-fix code), all 25
real-server e2e steps green, and the three seeded cases below are in the
running app's store.

### The seeded cases are in the app right now

The store at `~/Library/Application Support/com.jensuid.dah/` holds three
worked cases at three different stages, so the case list shows the ladder the
app walks rather than one finished example:

1. **"Why did western region revenue dip in Q3?"** (sales_q3.csv) - the closed
   loop: profiled (8 rows, 4 columns, 1 duplicate, 1 null revenue), planned, a
   GROUP BY run, interpreted, the drafted finding **accepted**, a bar chart
   rendered, and **validated `partially_supported`** - the null revenue trips
   the missing-data check while reproducibility itself passes, which is the
   honesty budget doing its job.
2. **"Does marketing spend drive signups?"** (spend.csv) - stopped at a
   **drafted but unaccepted** finding: profiled, planned, run, interpreted, and
   the draft waiting in the panel for the analyst to accept or edit.
3. **"Which support category is slowest to resolve?"** (tickets.csv) - freshly
   attached and profiled only, so the "what do I do next" state is visible.

The user should reload the open window (Cmd+R) to see them; the running sidecar
is the rebuilt one, and `Origin: tauri://localhost` is answered with
`access-control-allow-origin` and `Vary: Origin`, so the list loads.

### The shipped app now carries it

Rebuilt and relaunched: `./server/build_sidecar.sh` then `npm run tauri --
build` in `desktop/`. This time the DMG step succeeded as well - both
`DAH.app` and `DAH_0.1.0_x64.dmg` are fresh at
`desktop/src-tauri/target/release/bundle/`. The old app was quit and the new
one opened; the core on 127.0.0.1:8123 is the new sidecar, and the packaged
binary itself was proven on an isolated data dir before the relaunch - the
malformed CSV profiles four columns there and the SQL written from those
columns returns `[['north', 4200.0], ['west', 8100.0]]`.

The store is at `~/Library/Application Support/com.jensuid.dah/` and survived
the relaunch unchanged; a reload of the open window (Cmd+R) is all the shell
needs.

---

## Next action
**P7-CORS-001 is DONE**: the packaged app could not reach its own core. A human
opened the shipped .app and got "Failed to load cases: Failed to fetch" with the
New Case form unreachable behind it - so the report that found the last bug was
the thing that found this one, and it is the reason a walkthrough by hand is not
a luxury in this repo.

Tauri serves the bundled frontend from its own scheme while the core answers on
127.0.0.1:8123, so every fetch the app makes is cross-origin, and the core
answered with no `Access-Control-Allow-Origin`. The browser discarded each
response before the app saw it - while the core's own log recorded a clean 200
for the identical request. That is not a contradiction, it is the whole bug.

Reproduced in a real headless Chrome before the fix - the shipped bundle served
from a foreign origin fetches the core and fails with exactly the message the
user saw, while the core logs 200 - and the same fetch succeeds after it.
`server/app/main.py` gains `ALLOWED_ORIGINS` and a CORS middleware: an origin on
the list is echoed with `Vary: Origin`, an OPTIONS preflight answers 204 with
methods and headers, and anything else gets nothing. No wildcard: the core
holds an analyst's cases and chat, and `*` would let a webpage the user merely
visits read them. Written as a plain middleware rather than starlette's
CORSMiddleware because no endpoint handles OPTIONS, and a 405 preflight means
the real request is never sent.

### The packaged .app is still stale, and this fix is not in it

The bundled sidecar was built Sep 20 09:22, **33 commits ago**, and it predates
`/schema-version`, `/updates/latest`, all of P7 and this fix. The source is
fixed; the artifact a user runs is not. Rebuild before any release:

    cd server && ./build_sidecar.sh && cd ../desktop && npm run build

### What is unbuilt, in priority order

- **A release, after the rebuild.** Every P7 checklist item that builds
  something is delivered, and now both verified against a real server *and*
  walked through the shipped shell. Eighteen tasks have landed since v0.1.0;
  `0.2.0` is the honest next label.
- **P7-WALK-001's five findings**, still open: evaluations do not travel with
  an exported case; a stale agent step can be approved after its write happened
  out of band; the plan's contents, a run's result rows and the profile's
  per-column null count are persisted and never rendered; a draft's grounds run
  together with its count; the chat and generate-code inputs are near-identical
  adjacent boxes.
- **The two endpoint-only surfaces, by design.** `/schema-version` answers "is
  my data safe with this build", a question a support conversation asks rather
  than a step in an analysis.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Rebuild the sidecar first, then tag `v<x.y.z>` where x.y.z matches
server/pyproject.toml. The published build is arm64 and unsigned, flagged
pre-release (DEC-006). Eighteen tasks have landed since v0.1.0, so `0.2.0` is
the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---

## Next action
**P7-WALK-001 is DONE**: the shipped shell, used by hand. Every other
verification artifact in this repo drives a contract - the core through
Starlette's TestClient, the shell through jsdom - and a contract does not
render. This one sat in front of the actual product: a real server on :8123
against an isolated data dir, a real headless Chrome over the DevTools
protocol with genuine keyboard input, and the journey done the way an analyst
does it - case created by keyboard, file attached, the agent's plan approved,
its SQL run, interpreted, the draft accepted as a finding, validated, the
reviewer's audit approved, the chart rendered, the case asked a question, a
template promoted and a second case started from it. The rendered DOM was read
at every step and checked against what the case actually holds.

The loop closes, and the honesty budgets show up where they should: the
profiler counts the duplicate, validation answers `partially_supported`
because a null revenue trips the missing-data check while reproducibility
itself passes, and the LEARN panel ends on "the trust loop ran, not that the
answer is right".

One bug, found only because a human reads what renders: the reviewer's
settled-step summary summed over a **set** of verdict strings, so a
nine-axis audit could never report more than one pass or one concern. Every
audit the shell has ever shown understated its own pass count -
"9 axes, 1 pass, 1 concern, 0 fail" for an audit that was 7 pass / 2 concern.
`server/app/main.py` counts per axis now, and the two audit tests in
`tests/test_multi_agent.py` derive their tallies from the recorded evaluation
so the shape of the bug (counting distinct verdicts instead of axes) cannot
pass again. 380 server tests green; the real-server e2e's audit step now
prints "9 axes, 7 pass, 2 concern, 0 fail".

### Findings recorded, not fixed (in priority order)

- **Evaluations do not travel with an exported case.** `app/exporter.py` has
  no reference to the evaluations table, so a package carries the audit's own
  run (its code) but none of its nine-axis verdicts. A restored case has every
  finding and none of its audits - the reviewer's whole purpose is an audit
  trail that outlives the analyst. exporter + importer + models + tests.
- **A stale agent step can be approved after its write happened out of band.**
  The draft panel's "Accept as a finding" and the agent's pending "accept"
  step are two paths to one endpoint; accepting out of band does not retire
  the step, so approving it later records the finding twice. This walkthrough
  produced a duplicate finding, and the chat then cited the unvalidated
  duplicate as "the latest finding".
- **Three numbers the core computes and the shell never renders:** the plan's
  sub-questions and hypotheses, a run's result rows, and the profile's
  per-column null count. The analyst approves "Plan the analysis from the
  profile" having never seen the plan, and reads "sql over sales.csv - 2
  rows" without the rows. Each is a panel over an existing contract; none
  needs a new endpoint. (The duplicate IS shown; the null is not.)
- **A draft's grounds run together with its count** - "row_count ranges
  2..32 row(s)" is the range `2..3` butted against "2 row(s)".
- **The chat and generate-code inputs are adjacent near-identical boxes** -
  "What would you like to know?" and "How many datasets does this case have?"
  This walkthrough typed a chat question into the code generator first.

### What is unbuilt, in priority order

- **A release.** Every P7 checklist item that builds something is delivered,
  and now both verified against a real server *and* walked through the shipped
  shell. Seventeen tasks have landed since v0.1.0; `0.2.0` is the honest next
  label. The pipeline publishes per tag, and the update check is already
  behind the **Check for Updates...** menu item.
- **The findings above**, in the order listed. The first two are correctness
  gaps in shipped capability; the third is the distance between "works" and
  "usable" that this task existed to measure.
- **The two endpoint-only surfaces, by design.** `/schema-version` answers "is
  my data safe with this build", a question a support conversation asks rather
  than a step in an analysis.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build
is arm64 and unsigned, flagged pre-release (DEC-006). Seventeen tasks have
landed since v0.1.0, so `0.2.0` is the honest next label when a release is
wanted.

Nothing is unblocked-but-undone.

---

## Next action
**P7-E2E-001 is DONE**: the whole app, against a real server. Every other
verification artifact in this repo drives the app in-process through
Starlette's TestClient - fast, and what caught every regression fixed here -
but it never binds a port, never parses a real multipart upload and never runs
uvicorn's lifecycle. This one starts a fresh uvicorn server on a free port with
an isolated data dir and drives the product over real HTTP.

`verification/e2e/verify_e2e.py`: one case built by hand (upload, profile, plan,
generated SQL, a refused write, interpretation, a drafted finding accepted,
validation, EVALUATE on nine axes), then the reviewer agent auditing that
finding through the shared approval gate, then a second case driven entirely by
the analyst agent to a closed loop, then the export round trip. 25 asserted
steps; three consecutive green runs at ~3s each; CI runs it in the server job
after the gates and uploads its report.

The run is deterministic and offline, and the way that is achieved is the one
detail worth remembering: the LLM env vars are **emptied** for the server's
subprocess, not unset. `app.main` loads `server/.env` on a plain uvicorn start,
and `load_dotenv` never overrides a variable that is already set - so an empty
value beats the file, and the engines treat an empty key as absent. The first
draft scrubbed only the parent environment, and the live key from `.env` made
the plan answer `source=llm` mid-journey.

### What is unbuilt, in priority order

- **A release.** Every P7 checklist item that builds something is delivered,
  and now verified against a real server as well as in-process. Seventeen tasks
  have landed since v0.1.0; `0.2.0` is the honest next label. The pipeline
  publishes per tag, and the update check is already behind the **Check for
  Updates...** menu item.
- **The two endpoint-only surfaces, by design.** `/schema-version` answers "is
  my data safe with this build", a question a support conversation asks rather
  than a step in an analysis.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Seventeen tasks have landed
since v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---

**P7-SHELL-011 is DONE**: the reviewer is a second agent panel beside the
analyst's. P7-AGENT-001 gave a case two roles behind one approval gate, and
nothing in the shell reached the role family, so a second agent's audits were
observable only through the API - exactly where the single driver stood before
P7-SHELL-003. Both panels now load read-only with the workspace, both propose
only when the analyst asks, and every write still runs through the endpoint that
owns it.

`web/src/api.ts` carries the typed client for the role family and the `role`
field the core returns on a state and a step. `AgentPanel` is one component with
two sets of wording chosen by role, so two panels on one page are never
ambiguous - the reviewer says what the reviewer does, in its own words, and the
analyst's strings are unchanged. The reviewer sits after the findings panel,
because findings are its input; `stepSentence` names the finding's own claim for
an `evaluate` step, so the human approves an audit of something concrete.

The web suite is 78 tests (was 73: +5 in `CaseWorkspace.test.tsx`), `npm run
build` passes - `tsc -b` runs first - and the desktop bundle builds from the same
source. The server side is untouched by this change and stays at 380.

### What is unbuilt, in priority order

- **A release.** Every P7 checklist item that builds something is delivered -
  EVALUATE (core and shell), the web-shell gap (eight surfaces), LEARN (core and
  shell) and multi-agent workflows (core and shell). Sixteen tasks have landed
  since v0.1.0; `0.2.0` is the honest next label. The pipeline publishes per tag,
  and the update check is already behind the **Check for Updates...** menu item.
- **The two endpoint-only surfaces, by design.** `/schema-version` answers "is my
  data safe with this build", a question a support conversation asks rather than
  a step in an analysis.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`), cloud
  sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Sixteen tasks have landed since
v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---

**P7-AGENT-001 is DONE**: a case can be worked by more than one agent, each with a
role of its own, and the roles disagree in the case's own audit trail rather than in
private. P6-AGENT-002's driver proposes the analysis loop one human-approved step at a
time; nothing examined what it produced. A second role joins it whose entire method is
EVALUATE - the reason the roadmap gated multi-agent work behind it - so an
agent-proposed finding is audited by a different agent with a different objective, and a
verdict that fails the analyst's own finding is recorded where a reviewer can read it.

Two roles, one case: **analyst** is the existing decision procedure, unchanged, and the
legacy `/agent` family is it; **reviewer** derives the case's first finding whose
(code, claim) has no evaluation and proposes the EVALUATE audit of the run that backs it
- the claim is the finding's own statement, the code is the run's own query, the verdict
lands in the evaluations table through the same endpoint a human audit uses, and the
reviewer invents neither and writes nothing of its own. This is orchestration, not
autonomy (the spec's own distinction - an autonomous multi-agent system is a non-goal,
"Human control" is in its Never-lose list): every role shares the one approval gate, a
GET never proposes, and a page refresh commits nothing.

The server suite is 380 tests (was 367: +12 in the new `tests/test_multi_agent.py`, +1
migration case in `tests/test_migrations.py`), and the P2, P3 and P4 gates each PASS,
each re-running the suite at 380. The web suite is untouched and stays at 73.

### What is unbuilt, in priority order

- **The reviewer in the shell** - P7-SHELL-011, and the last item on the P7 checklist.
  `/cases/{id}/agents/{role}` has the same four verbs the single driver has, and nothing
  in the shell reaches it, so a second agent's audits are observable today only through
  the API - exactly where the single driver was before P7-SHELL-003. A typed client for
  the role family plus an agent panel per role in `web/src/CaseWorkspace.tsx`.
- **A release.** Fifteen tasks have landed since v0.1.0; `0.2.0` is the honest next
  label. The pipeline publishes per tag, and the update check is already behind the
  **Check for Updates...** menu item.
- **The two endpoint-only surfaces, by design.** `/schema-version` answers "is my data
  safe with this build", a question a support conversation asks rather than a step in an
  analysis.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`), cloud sync,
  team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is arm64
and unsigned, flagged pre-release (DEC-006). Fifteen tasks have landed since v0.1.0, so
`0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---


**P7-SHELL-010 is DONE**: LEARN mode has a surface as well as a core, and with
EVALUATE before it, both product modes the spec names - and that DAH uniquely
owns - are built. A **Learn this case panel** sits beside the workflow panel it
explains: the workflow says where the case stands, this says why each step
exists and what a learner should be able to answer before leaving it. Each
phase renders what it is for, the question that tests understanding, and the
stages as the actions that close them; the panel names the one phase and action
to work on now, and a finished walk says the trust loop closed - the loop ran,
not that the answer is right.

The web suite is 73 tests (was 67: +6 in `CaseWorkspace.test.tsx`), `npm run
build` passes - `tsc -b` runs first - and the desktop bundle builds from the
same source. The server side is untouched by this change and stays at 367.

### What is unbuilt, in priority order

- **Multi-agent workflows** - the last item on the P7 checklist, and the spec's
  ladder above the single driver that exists (P6-AGENT-002). Only after
  EVALUATE, which is the audit layer an agent's own output has to survive -
  and EVALUATE is built now, so the precondition is met.
- **A release.** Fourteen tasks have landed since v0.1.0; `0.2.0` is the honest
  next label. The pipeline publishes per tag, and the update check is already
  behind the **Check for Updates...** menu item.
- **The two endpoint-only surfaces, by design.** `/schema-version` answers "is
  my data safe with this build", a question a support conversation asks rather
  than a step in an analysis.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Fourteen tasks have landed
since v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---

**P7-SHELL-008 is DONE**: a case's evidence graph is a review surface. The web
suite is 64 tests (was 60: +4 in `CaseWorkspace.test.tsx`), `npm run build`
passes and the desktop bundle builds from the same source. The server side is
untouched and stays at 358.

### What is unbuilt, in priority order

- **The last of the web-shell gap** - P7 item 2, now seven surfaces closed
  (EVALUATE, the agent, case management, templates, cross-case memory, EDA, the
  evidence graph). Only this still has an endpoint and no UI: **case history**
  (`/cases/{id}/history`), the read-only timeline of everything that happened in
  a case. It is a panel over an existing contract and needs no new endpoint.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk. Mostly a
  sequencing layer over the workflow stages that already exist (P3-FLOW-004).
- **Multi-agent workflows** - only after EVALUATE, which is the audit layer an
  agent's own output has to survive.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Twelve tasks have landed
since v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---


**P7-SHELL-007 is DONE**: the "what should I look at first" steps are one panel
away. The web suite is 60 tests (was 54: +6 in `CaseWorkspace.test.tsx`),
`npm run build` passes - `tsc -b` runs first, and it caught a name the test
suite could not see: `runEda`'s parameter was named `request`, shadowing the
module's own request helper, and the tests never ran that code because the
module was mocked - and the desktop bundle builds from the same source. The
server side is untouched and stays at 358.

### What is unbuilt, in priority order

- **The last of the web-shell gap** - P7 item 2, now six surfaces closed
  (EVALUATE, the agent, case management, templates, cross-case memory, EDA).
  Still no UI: the evidence graph (`/evidence-graph`), case history,
  `/schema-version` and `/updates/latest`. Each is a panel over an existing
  contract; none needs a new endpoint.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk. Mostly a
  sequencing layer over the workflow stages that already exist (P3-FLOW-004).
- **Multi-agent workflows** - only after EVALUATE, which is the audit layer an
  agent's own output has to survive.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Eleven tasks have landed
since v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---


**P7-SHELL-006 is DONE**: a cited previous case is something the analyst can
follow. The web suite is 54 tests (was 50: +4 in `CaseWorkspace.test.tsx`),
`npm run build` passes and the desktop bundle builds from the same source. The
server side is untouched and stays at 358.

### What is unbuilt, in priority order

- **The rest of the web-shell gap** - P7 item 2, now five surfaces closed
  (EVALUATE, the agent, case management, templates, cross-case memory). Still
  no UI: EDA (`/eda`), the evidence graph (`/evidence-graph`), case history,
  `/schema-version` and `/updates/latest`. Each is a panel over an existing
  contract; none needs a new endpoint.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk. Mostly a
  sequencing layer over the workflow stages that already exist (P3-FLOW-004).
- **Multi-agent workflows** - only after EVALUATE, which is the audit layer an
  agent's own output has to survive.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Ten tasks have landed since
v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---


**P7-SHELL-005 is DONE**: templates have a surface as well as a core. The web
suite is 50 tests (was 39: +7 in the new `Templates.test.tsx`, +3 in
`CaseWorkspace.test.tsx` for the promote panel, +1 in `api.test.ts` for the
empty 204), `npm run build` passes - `tsc -b` runs first, so a type error the
jsdom tests cannot see fails it - and the desktop bundle builds from the same
source. The server side is untouched and stays at 358.

### What is unbuilt, in priority order

- **The rest of the web-shell gap** - P7 item 2, now four surfaces closed
  (EVALUATE, the agent, case management, templates). Still no UI: cross-case
  memory, EDA (`/eda`), the evidence graph (`/evidence-graph`), case history,
  `/schema-version` and `/updates/latest`. Each is a panel over an existing
  contract; none needs a new endpoint.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk. Mostly a
  sequencing layer over the workflow stages that already exist (P3-FLOW-004).
- **Multi-agent workflows** - only after EVALUATE, which is the audit layer an
  agent's own output has to survive.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Nine tasks have landed since
v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.

---

## What was completed
- P7-E2E-001 PASSED: the whole app against a real server. The P2/P3/P4 gates
  drive the app in-process, which is what every regression this repo has fixed
  was caught by - but a release ships a packaged server a user runs for real,
  and nothing had ever started the actual server and talked to it.
  `verification/e2e/verify_e2e.py` starts uvicorn on a free port (the port is
  read from uvicorn's own listening line), waits on /health, drives the journey
  and terminates the server in a finally so a failure still writes the report
  and exits 1.
  LESSON: five things were wrong on the first run, and four of them were
  endpoint shapes assumed from the contract's prose rather than read from the
  response models - `version` not `recorded`, per-column detail in `stats` not
  in `columns`, `status` not `validation_status` on a validation result, `steps`
  not `phases` on the LEARN walk. `app/models.py` is the contract and is one
  grep away; the prose paraphrases it, and a paraphrase is where a false
  assumption enters. The fifth was the interesting one: the journey went to the
  live LLM because `app.main` loads `server/.env` itself, so scrubbing the
  parent environment was not enough - an empty value beats the file, and the
  empty is what the engines treat as absent. Two behaviours that only compose
  into "deterministic" if both are known.
  Also worth carrying: validation's verdict on a dataset with a null revenue is
  `partially_supported`, not `supported`. The first assertion demanded the
  flattering verdict; the honest one is the missing-data check doing its job, so
  the assertion now accepts either and checks that reproducibility itself
  passed and the null was flagged - a stronger statement than the one it
  replaced.

- P7-SHELL-011 PASSED: the reviewer in the web shell. P7-AGENT-001's role family
  answered only through the API, so a second agent's audits - the whole point of
  the role - were as unreadable as the single driver's loop was before
  P7-SHELL-003. The workspace now carries an agent panel per role: the analyst
  where it always was, and a reviewer after the findings panel, because findings
  are what it audits.
  `web/src/api.ts` gains `getRoleAgentState`, `proposeRoleAgentStep`,
  `approveRoleAgentStep` and `rejectRoleAgentStep` against
  `/cases/{id}/agents/{role}`, plus the `role` field on `AgentState` and
  `AgentStep`. The legacy analyst client functions stay and the analyst panel
  keeps calling them, so its behaviour - and every existing test - is unchanged.
  `AgentPanel` parameterises every string it renders, so the two roles never
  share a phrase a reader or a matcher could confuse: the reviewer's idle state
  says nothing is pending *review*, its button proposes the next *audit*, and its
  history is what the reviewer has done.
  LESSON: the panel's idle paragraph was the last hardcoded string - every other
  phrase had been parameterised, and it was invisible to the eye because the
  analyst's wording is correct on the analyst's panel. The reviewer was telling
  the analyst's lie ("nothing is pending, propose a step") on a case with no
  findings, which is the reviewer's honest finished state rather than a thing it
  could act on. The test found it, reading the rendered panel's own text. Two
  smaller traps of the same family: a recorded audit's summary shares its
  paragraph with the artifact kind ("sql — every axis passed"), so an exact
  string match cannot reach the phrase and a regex must; and a step's kind is
  not its status, so a rejected audit that omitted `kind: 'evaluate'` rendered as
  a rejected `analyze` and read the reviewer's history as the analyst's.

- P7-AGENT-001 PASSED: multi-agent workflows, roles over one case (core). The single
  driver (P6-AGENT-002) proposes the analysis loop one human-approved step at a time,
  and nothing examined what it produced. A second role joins it whose entire method is
  EVALUATE, so an agent-proposed finding is audited by a different agent with a
  different objective, and a failing verdict is recorded where a reviewer can read it
  rather than folded into the finding it failed.
  `server/app/db.py` gains migration 9 - `agent_steps.role TEXT NOT NULL DEFAULT
  'analyst'` - so every step recorded before this task reads as the analyst role and
  the legacy paths keep their meaning. `server/app/agent.py` becomes role-aware: the
  pending step, history, attempt count, proposals and the settle/decide path all take
  a role, dispatching to `_analyst_step` (unchanged procedure) or `_reviewer_step`
  (derives the first unaudited finding and proposes an `evaluate` step carrying that
  finding's claim and its run's code). `server/app/main.py` answers
  `/cases/{id}/agents/{role}` - GET state, POST propose, approve, reject - with
  `_require_role` answering 400 naming the roles that exist, and the legacy `/agent`
  family delegating to the shared approvers as the analyst role. The `evaluate` step
  kind posts through the existing evaluate endpoint, and its settle note is
  "audited finding {id}: 9 axes, N pass, M concern, K fail" plus the failing axes'
  own detail. `models.py`, `exporter.py` and the duplicate path carry the role.
  Three things that had to be right rather than present: **idempotence is keyed on
  (code, claim), not (run_id, claim)** - EVALUATE stores the artifact as a run of its
  own, so an evaluation's run_id is the audit's artifact rather than the finding's, and
  joining on it would re-audit forever; **two honest notions stay distinct** - a
  failing audit sits beside the finding and never touches its validation_status, which
  is about rerun support; and **one role's approval never authorises another role's
  write** - a mismatch is a 409 naming that role's own pending step.
  LESSON: most of the failures on the way to green were the migration's own
  bookkeeping - a changed INSERT column list here, a values tuple that kept its old
  length there, a SELECT that gained a WHERE column without gaining the SELECT column
  - each surfacing as "incorrect number of bindings" or a KeyError far from the site
  of the edit. The discipline that caught them was running the existing agent and
  export suites first, before writing a new test, because those suites already encode
  every write path and said exactly which statement was wrong. A schema change is not
  one edit; it is one edit per writer, and the writers are found by the tests, not by
  grep.

- P7-SHELL-010 PASSED: LEARN mode in the web shell. P7-LEARN-001 shipped the
  guided walk and nothing in the shell reached it, so the mode existed as a
  contract and not as a product. A **Learn this case panel** now sits beside
  the workflow panel it explains - the workflow says where the case stands,
  this says why each step of that exists and what a learner should be able to
  answer before leaving it. It loads read-only with the workspace.
  Each phase renders its name and status, what it is for, the question that
  tests understanding, and the stages it covers as the actions that close them
  - with the workflow's own hints, so what to do and why sit in one place. The
  panel names the single phase and action to work on now, the way the workflow
  panel names the next stage, and a completed walk says the loop closed in the
  core's own words: the trust loop ran, not that the answer is right. A learner
  is not graduated on a stronger claim than the artifacts support, and nothing
  is scored - for the same reason EVALUATE reports nine verdicts rather than a
  number.
  LESSON: three existing tests broke, all because the workspace is one page.
  The ladder's stage rows carry the workflow's own actions as their labels, so
  "attach a dataset" named both the data panel's uploader and a stage row;
  fixed by saying which panel the input is in, which is the accessible thing
  too. The other two were the previous task's trap come back: a phrase that
  spans a <strong> cannot be matched by text, because the matcher reads an
  element's own text nodes and not its descendants' - the "work on now"
  sentence is plain text now. And one failure was not its own: the
  ambiguous-label test died midway and left a queued mock value behind, so the
  next test received a dataset id from the case before it. A failing test can
  corrupt the one after it, which is why the fix belongs to the first.

- P7-LEARN-001 PASSED: LEARN mode, the guided walk (core). The spec names three
  product modes; ANALYZE exists and its workspace answers "what do I do next"
  without ever saying why. LEARN is the same loop regrouped into the spec's
  four phases and explained.
  `server/app/learn.py` (new) maps the seven ANALYZE stages onto Why (question,
  data), What (profile, plan), How (analyze, evidence) and Validate (validate)
  - every stage in exactly one phase, asserted as a property by the suite. Each
  phase carries a **purpose** (what the phase is for, the thing the workflow's
  next action never says) and a **prompt** (the question a learner should be
  able to answer before leaving it - what makes it teaching rather than a
  checklist). It recomputes from the same counts `case_progress` derives, so it
  cannot drift: deleting an artifact moves the walk back as honestly as adding
  one. At most one phase is current, and `done` says only that the trust loop
  closed - a finding was validated - which per workflow.py means the loop *ran*,
  not that the answer is right.
  Two non-decisions worth naming: LEARN does not score a learner, for the same
  reason EVALUATE reports nine verdicts instead of a number - a score would
  imply a precision no data here can back; and it stores no progress, because a
  derived walk cannot disagree with the case the way a stored one can.
  LESSON carried into the record: two of the nine tests initially asserted a
  premise the core does not permit - deleting runs and findings to force a
  phase to reopen. No such DELETE exists: a run is evidence a finding binds, and
  the core refuses to delete bound evidence (405). Rewritten against what the
  core permits, the invariant is now checked at every step of a build rather
  than in one contrived state.

- P7-SHELL-009 PASSED: case history, as a review surface. P3-CASE-007 shipped
  `GET /cases/{id}/history` - one event per artifact, chronological, each
  carrying its own timestamp, a label and a detail, plus counts - and nothing in
  the shell showed it, so the shape of a case was reconstructible only by
  opening every panel and comparing timestamps yourself. A **Case history
  panel** now sits at the end of the workspace, after the evidence panel: the
  graph says what backs each claim, the timeline says what happened in the case
  at all. Each event is one line in the order the core sends them, with the kind
  as a phrase a reader does not have to decode ("dataset attached", not
  "dataset_attached"), the artifact's own label, and its detail beneath - the
  same fields the core returns, shown rather than transformed. The counts are
  one summary sentence naming only the kinds the case actually has, so a young
  case is not described by a row of zeroes.
  Two things that had to be right rather than present: a **404 is guidance, not
  a second alert** - the only failure the endpoint answers is an unknown case,
  and the workspace loads its own case on mount, so that failure already reaches
  the user at the top of the page and the panel does not raise it twice; and a
  **young case is its beginning, not an empty list** - one event renders as one
  event.
  The task's own lesson is in its record: the timeline's first event is the
  case's creation, whose label is the case's own question, so the question now
  appears twice on the page and five existing assertions that meant the title
  broke. They now ask for the heading by role - which is the accessible thing
  anyway.
- P7-SHELL-008 PASSED: the evidence graph, as a review surface. P3-EVIDENCE-006
  could answer "what backs each claim in this case, and does every one of them
  reach the data?" - and nothing in the shell showed it, so a case's own
  evidence was inspectable only one finding at a time, and a claim with no
  source was invisible. An **Evidence panel** now sits after the findings panel
  and loads read-only with the workspace. Each trace renders the finding's
  statement with its validation status and the chain back to the data as chips -
  the same shape the chat uses for a citation; each edge renders as a sentence
  ("chart 'Revenue by region' is rendered from the sql run"); and a node with no
  edge is still listed under its kind, because leaving it out would make the
  graph say the case has less than it does. Three things that had to be right
  rather than present: a finding whose run is gone is flagged as **a claim with
  no source** instead of being smoothed over; its broken edge says "an artifact
  no longer in the case" rather than showing a uuid; and the endpoint's 400 for
  an artifact-free case is muted guidance rather than an alert, because a young
  case is not a failed review.

- P7-SHELL-007 PASSED: EDA in the web shell. The "what should I look at first"
  steps needed a hand-written query: P3-ANALYSIS-005 shipped three ops -
  segment a measure by a category, correlate two columns, describe a column's
  distribution - each compiling to read-only SQL under the same gate and row
  cap as any query, and nothing in the shell could ask for one. A new **EDA
  panel** sits between the data and runs panels, where the core's own module
  puts exploration. The op is a chooser and each op renders only its own
  pickers, so a question is asked with the shape of its answer. The profile's
  per-column type steers the defaults without forbidding anything, a stale pick
  is resolved against the current dataset's columns rather than submitted, the
  table is exactly the columns the core returned (seven for a numeric
  distribution, two for a categorical one), and the panel says plainly that an
  EDA result is exploration, not evidence.

- P7-SHELL-006 PASSED: cross-case memory, actionable in the shell. P6-MEMORY-001
  let a chat answer cite what a previous case found - "Before this case, a
  previous case, \"Why did revenue decline?\", which found North leads
  revenue" - and the shell rendered the citation behind it as an inert chip
  carrying a uuid. The one thing recall exists for, going to read what was
  concluded last time, was a click that did nothing. The Chat panel now
  resolves each `case:<id>` ground to that prior case's own question and
  renders it as a **button that opens the case as its own workspace**; the
  question is the label because a uuid is not how anyone recognises a case.
  Three behaviours had to be right rather than present: each cited case is
  looked up **once**, shared across every turn that cites it; a lookup that
  fails is recorded as absent and degrades to a chip ("a previous case that is
  no longer available") rather than an error - a citation outlives the case it
  names, and the same object returned from an all-failed batch keeps the
  effect from refetching forever; and grounds of other kinds render exactly as
  the chips they always did.

- P7-SHELL-005 PASSED: templates in the web shell. The four template
  endpoints - promote a case, list them, start a case from one, retire one -
  were tested in the core and reached nowhere in the shell, so the shape of an
  investigation worked out once was never offered to the next one. Two
  surfaces now: the workspace carries **Save as a template** (the name is
  optional and defaults to the case's question, because the common gesture
  needs no second prompt), and the case-list screen carries a **Templates**
  section below the list - templates are not case children and outlive the
  case they came from, so they belong on the front door, not inside a case.
  Each row shows the name, the question and dataset label it seeds, and a
  **shape summary**: how many proposals it carries and how many findings, with
  each finding's validation verdict counted. A template promoted from a case
  with nothing to carry - or before shapes existed - *says so* ("a
  question-only skeleton") rather than showing zeroes that would imply an empty
  investigation. **Start a case from this** posts to the from-template endpoint
  and opens the seeded case; **Retire** is one click, because a template carries
  no data of its own and the core's contract is that cases created from it keep
  working without it (`_template_of` answers None and the case degrades to
  normal derivation), so nothing is lost the way a case deletion loses things.
  The wiring surfaced a bug older than this task, and it was in the client the
  whole shell shares: `request` parsed every successful body as JSON, and the
  core answers 204 with an empty body for every DELETE the shell makes. The
  write had already landed when the response arrived, so the client threw
  "Unexpected end of JSON input" and the row reported a success as "The action
  failed". The case delete P7-SHELL-004 shipped was broken exactly this way -
  its test mocked the client, so the real path never ran. Two lines fix it:
  an empty body answers nothing.

- P7-SHELL-004 PASSED: case management from the shell. The three everyday
  operations on the front door - rename, duplicate, delete - answered only
  through the API, and the list rendered a row whose only affordance was
  opening it. A mistyped question could not be fixed, a finished investigation
  could not be copied as the start of a variant, and a case that had served its
  purpose could not be removed, so the list only ever grew. Each row keeps
  opening the case as its primary action and gains the three buttons: **Rename**
  is inline (question and dataset label become inputs with Save and Cancel, and
  a cancelled edit restores what was there), **Duplicate** reloads the list with
  the copy, and **Delete asks twice** - the core's deletion is final and takes
  the case's on-disk directory, so the first click arms the row and the second
  is labelled with the case's own question, because that is the thing a user
  would be sorry to lose. The armed state is per row, so confirming one case
  never endangers another.
  The two-click delete and the aria-labels solved each other: the first draft's
  bare button names could not address one case among two in a test, and per-row
  labels naming the question fixed the tests and are the accessible thing to do
  - an action button that does not say which case it acts on is ambiguous to a
  screen reader for exactly the reason it was ambiguous to a test.

- P7-SHELL-003 PASSED: the agent, as a surface. P6-AGENT-002 shipped a driver
  that proposes a step and waits for a human's approval, and four endpoints
  served it - a read-only GET, an idempotent proposing POST, /approve and
  /reject - with no panel anywhere. The workspace now carries an **Agent**
  panel beside the workflow it drives: the pending proposal renders as a
  sentence built from the step's own payload ("Accept the draft as a finding:
  North leads revenue"), and Approve / Reject - with an optional reason that is
  recorded on the step - are buttons. Every other panel is a step; this one is
  the sequence, and it is the capability that most changes what the workspace
  is for.
  The guarantees did not move: the write still waits for the button, still runs
  through the endpoint that owns it, and the GET never proposes, so a page
  refresh commits nothing. A stale approval is a 409 shown as a sentence before
  the panel resyncs - never a second write.
  The panel exposed one real gap in the typed client: the agent's 409 answers
  with an OBJECT as its detail, and the client copied `body.detail` straight
  into the message, so a stale approval would have rendered as "[object
  Object]". The client now unwraps a nested detail, and the sentence the core
  wrote reaches the user.

- P7-SHELL-002 PASSED: the EVALUATE surface, the first panel of the web-shell
  gap. `POST .../evaluate` shipped with P7-EVAL-001 and nothing in the shell
  could reach it - the workspace walked the ANALYZE loop (data, runs, findings,
  chat) and the evaluate endpoint was the first one with no panel at all, in
  the phase whose flagship capability it is. The workspace now carries an
  **Audit submitted work (EVALUATE)** panel: paste the artifact's code and the
  claim it was offered to support, and read the nine axes - question, data,
  quality, method, calculation, evidence, claim, visualization, limitations -
  each as a verdict badge and its sentence, in the spec's own order. Recorded
  audits list below, newest first, so an audit is itself inspectable the way a
  run is; with several datasets there is a chooser, because the verdicts are
  per-dataset.
  No new endpoint, contract or dependency - the panel only renders what the
  core already answers. It keeps the discipline every other panel keeps: the
  submit posts to the evaluate endpoint and nothing else, and the panel never
  runs code and never decides whether work is sound. A 400 is part of the
  contract rather than a failure - a non-read-only artifact is refused before
  anything executes, and its own message is shown as a sentence beside a panel
  still ready for corrected work.

- P7-EVAL-001 PASSED: EVALUATE mode, the spec's second product mode, and the
  largest capability DAH did not have. Until P7, every primitive served the
  analyst's *own* work - read-only execution, deep profiling, rerun validation,
  the evidence graph, the honesty budgets. This task turns those primitives on
  work that came from elsewhere, and that turn is the whole product difference:
  a user submits an artifact (its SQL or Python code) and the claim that code
  was offered to support, and DAH answers the nine questions the specification
  names, each against the data rather than against the claim's own confidence.
  Verdicts are pass / concern / fail - deliberately not a score, because a
  single number would imply a precision nine heterogenous axes do not have -
  and every verdict carries a sentence a reader can act on.

  Three pieces. `server/app/evaluator.py` is a pure module (like evidence.py
  and workflow.py) returning nine `AxisFinding`s; `POST .../evaluate` executes
  the artifact through the *existing* run engine - never a second code path, so
  the read-only gate, the row cap and the hard sandbox are the ones every other
  run answers to, and EVALUATE earns no privilege while untrusted code is the
  premise of the mode; and the `evaluations` table (migration 8) stores the
  artifact as a run and the audit beside it, so an audit is itself inspectable
  and reproducible - the standard every other artifact is held to.

  Four judgement calls the contract left open, each written into the code. A
  **non-read-only artifact is a 400 before anything executes** (a mutation is a
  request the store must never honour, not an artifact to audit), but a
  read-only artifact that **fails at run time is a Calculation finding, not a
  400** - the work came from elsewhere, it is not the user's to fix, and "this
  does not run" is the answer an auditor exists to give. An **unknown column is
  a Data fail, never a silent pass**: the first version of that check
  intersected the code's identifiers with the profile's columns, which drops
  every name the dataset lacks - the axis passed on exactly the case it exists
  to catch, and the fix reuses the generator's own notion of a column read. A
  **chart is not required**: the contract's baseline is a clean artifact
  passing all nine axes, and "no chart, and none needed" is a valid verdict -
  what *is* a fail is a chart whose axes are not the result's own columns, a
  check the previous `has_chart` boolean could not make because a boolean
  cannot be wrong. And a **single-row result is deterministic without an ORDER
  BY**, because one row has no row order to disagree about.

- P6-UPDATE-005 PASSED, and with it P6 closes: a new release tag reaches an
  installed app. The release pipeline publishes a build per tag, but the app
  had no way to learn that. `GET /updates/latest` answers one of three truths -
  `current`, `available` (with the tag, the release page and the notes), or
  `unknown` with a reason - and the shell's new **DAH > Check for Updates...**
  menu item opens the release page or shows that sentence. Everything degrades
  to a sentence, the way the reveal-logs menu does, and never panics on a body
  it does not recognise.
  What is deliberately *not* here is the self-replacing install, and the reason
  is two recorded facts rather than two gaps: the repository is private, so an
  unauthenticated feed request answers 404 (verified, not assumed), and the app
  is unsigned (DEC-006), so an update payload cannot be signature-verified.
  `tauri-plugin-updater` slots in when signing does, and the check it would
  consume is what this task built. The whole design turns on one distinction:
  "could not check" and "is up to date" are different statements, and only one
  of them is true - so every failure (404, 403, 503, a timeout, a non-JSON body,
  a body without a tag) is `unknown` with its own reason, never a silent
  `current`. Verified live against the real private repository: `unknown`,
  "the release feed is not reachable; the repository may be private".
- P6-MIGRATE-004 PASSED: a versioned, forward-only migration path for the store.
  The database had grown by seven ad-hoc `_ensure_column` additions across P2-P6
  - each guarded, each correct, and no version recorded anywhere in the file, so
  no code could answer "is this store current?" but only probe for each column
  and hope. That was tenable while the schema only ever gained nullable columns;
  it stopped being tenable the moment a task needed to rename, split or backfill
  anything. Now the version lives in SQLite's `user_version` (the file header,
  readable before any table exists and durable across a crash that leaves
  tables half-made), the seven historical additions are an ordered named chain
  applied one transaction at a time - the change, its audit row and its version
  stamp land together or none does, so a failure mid-chain leaves a consistent
  store that the next open resumes - and `GET /schema-version` reports the state
  so a user can ask whether their data is safe with the build they are running.
  Two deliberate behaviours: a store *newer* than the build is refused with both
  numbers named, never silently downgraded, and a store created by this build is
  stamped current with an empty audit trail, because the truth is that nothing
  was applied to it. SQLite itself set one constraint the implementation had to
  respect: a `NOT NULL` column cannot be added to a populated table without a
  default, so the historical migrations carry defaults that SCHEMA declares too -
  a test pins that a fresh store and an upgraded one are identical, not merely
  compatible, because "they agree by construction" is exactly the claim that
  silently stops being true when the next migration lands.
- P6-MIGRATE-004 PASSED: a versioned, forward-only migration path for the store.
  The database had grown by seven ad-hoc `_ensure_column` additions across P2-P6
  - each guarded, each correct, and no version recorded anywhere in the file, so
  no code could answer "is this store current?" but only probe for each column
  and hope. That was tenable while the schema only ever gained nullable columns;
  it stopped being tenable the moment a task needed to rename, split or backfill
  anything. Now the version lives in SQLite's `user_version` (the file header,
  readable before any table exists and durable across a crash that leaves
  tables half-made), the seven historical additions are an ordered named chain
  applied one transaction at a time - the change, its audit row and its version
  stamp land together or none does, so a failure mid-chain leaves a consistent
  store that the next open resumes - and `GET /schema-version` reports the state
  so a user can ask whether their data is safe with the build they are running.
  Two deliberate behaviours: a store *newer* than the build is refused with both
  numbers named, never silently downgraded, and a store created by this build is
  stamped current with an empty audit trail, because the truth is that nothing
  was applied to it. SQLite itself set one constraint the implementation had to
  respect: a `NOT NULL` column cannot be added to a populated table without a
  default, so the historical migrations carry defaults that SCHEMA declares too -
  a test pins that a fresh store and an upgraded one are identical, not merely
  compatible, because "they agree by construction" is exactly the claim that
  silently stops being true when the next migration lands.
- P6-TEMPLATE-003 PASSED: a template carries the analytical shape of a finished
  case, not just its question. The plan, the proposals and the finding outcomes
  were all already on disk, so promotion is a pure projection over them
  (`_capture_shape`), and a case started from the template inherits that shape
  as *proposals a human accepts* - the plan step offers the template's plan
  through the same `validate_plan`, and generate-code offers a template
  proposal only when every column it reads exists in the profiled dataset. Both
  record `source="template"` and both degrade to the deterministic path on any
  problem, so a shapeless, malformed or deleted template is never an error -
  it is the absence of a template, which the code already handled. No data,
  runs, findings or charts are copied; every write is still a POST the human
  makes, so the read-only gate, the row cap and the honesty budgets are all
  still in force for a templated case.
  Two bugs the new tests caught: `SOURCE_TEMPLATE` was referenced by two
  helpers whose definition never landed (a `NameError` at request time on a
  path no existing test walked), and hand-run cases' proposals carried
  `columns_used: []`, which made the column-existence check pass vacuously -
  the one failure it existed to prevent. A guard never fed the data it guards
  is not a guard.
- P6-AGENT-002 PASSED: a plan that executes itself, one approved write at a time.
  Every stage of the loop already had a validated endpoint; the agent is the
  driver over them, and it holds no privilege a hand-written call lacks. Its SQL
  passes the same read-only gate and row cap, its findings are created by the
  same POST, and its drafts and proposals come from the same stateless modules
  with the same validation. What it contributes is the sequence, the memory of
  what it already tried, and an audit row for every step. Nothing is written
  without an approval, and an approval id that is not the case's current pending
  step is a 409 rather than a second write.
- P5-UX-006 PASSED: a user can find the log without a terminal. The core answers
  `GET /logs` with a path, but a path in a JSON body is a terminal answer, and
  the shell exists precisely because this user does not have one open. New
  `desktop/src-tauri/src/logs.rs` is the bridge - `log_location` asks the core,
  `reveal_in_finder` hands the answer to Finder with `open -R` (macOS-native,
  no new dependency), and `reveal_core_logs` is the menu item's whole job.
  Everything degrades to a sentence rather than an error: a core still booting,
  hung, or older than the endpoint is `Disabled`, and a body that is not the
  expected shape is `Disabled` too, so a menu can never panic on a body it does
  not recognise. main.rs gains a real macOS menu bar - the app menu keeps About
  and Cmd+Q, which setting any custom menu otherwise takes away, Edit keeps the
  text editing a data tool needs, and **DAH > Reveal DAH Logs** is the one item
  DAH adds.
  Verified by hand, not only by test: the built app's menu bar was introspected
  with AppleScript (an earlier attempt ran a stale debug binary and showed a
  menu without the item - `cargo test` does not refresh the runnable
  `target/debug/dah-shell`, so an explicit `cargo build` is what makes a smoke
  honest), the item was clicked through AppleScript, and the shell's own log
  recorded `revealed the core's log at ~/Library/Application Support/
  com.jensuid.dah/logs/dah-core.log`. 5 new Rust tests, 12 total (was 7),
  including an e2e test that starts the real dev core and asserts the reported
  log is under the data dir the shell pointed it at and is a file that exists.

- P5-RELEASE-005 PASSED: a tag now produces a downloadable app. The packaging
  job in ci.yml proved the sidecar builds and serves on a clean machine, but
  its artifact was uploaded for one job and deleted a day later. Now
  `.github/workflows/release.yml` reads the version from server/pyproject.toml
  and FAILS if the tag does not match it, runs the server suite, builds and
  smokes the sidecar, builds the .app with the version stamped from the
  pyproject through `tauri build --config`, ditto-zips it with its architecture
  in the name, checksums it, generates notes stating the unsigned status and the
  Gatekeeper steps, and publishes a flagged pre-release with the zip and its
  sha256. UNSIGNED was the user's explicit call; signing slots in between the
  build and the upload when the Developer ID exists.

- P5-CI-004 PASSED:
## P1 vertical slice (verified)

```
Create Case -> Question -> Load CSV -> Profile -> SQL Analysis
-> Finding -> Evidence chain -> Validation (rerun) -> Save -> Reopen
```

## What the CI runs after the P4 gate caught (two test races)

Both were invisible locally - seven consecutive local runs passed before the
fix, which is the definition of passing by timing luck. CI failed twice, on a
*different* test each time, which is what pointed at interference rather than
a broken test.

1. **The two lifecycle tests raced for port 8123.** Both start a real core on
   the same fixed port and each asserts the port is its own afterwards (that is
   the orphan check). Cargo runs tests in parallel by default, so one won the
   bind and the other died on `[Errno 48] address already in use` - presenting
   as a 180s timeout that looked like a dead sidecar.
2. **The resolution tests shared `DAH_DEV_CORE`.** The override test sets that
   variable process-wide, resolves, and removes it. A concurrently-running
   resolution test observed it mid-flight and resolved to the virtualenv while
   a sidecar was present, so `release_resolution_uses_a_bundled_sidecar_when_present`
   panicked on an assertion about its own input.

The fix was `#[serial]` on all five tests, with a comment naming both races.
Serialization is right and a port is not: giving each test its own port would
have hidden the interference instead of removing it, and the tests exist to
assert exclusive use of the one port the app actually uses.

The general lesson, now stated twice in this handoff: **parallel test
interference presents as a flaky failure in whatever test happens to be
running alongside**. When a test fails intermittently and the failing test
changes between runs, suspect shared global state - a port, an env var, a
fixed temp path - before suspecting the code under test.

## What changed (P5-VERIFY-001)

- verification/p4/verify_p4.py (NEW): the gate, modelled on the P3 one. In-
  process TestClient, one journey, a step table and an exit-criteria table
  written to verification/p4/REPORT.md, exit 0 only when every step passes.
- Every dataset value is a closed function of the row index (revenue depends
  only on the region, so each region's sum is exactly rate x group size), so
  the expectations are known by construction rather than measured against a
  captured value that could drift.
- Hermeticity: the LLM credentials are scrubbed from the process and from the
  pytest subprocess, so no assistant step makes a live call. The one step that
  sets a dummy DAH_LLM_API_KEY does it to *break* the LLM on purpose and prove
  the fallback; `_BrokenLLM` raises without touching the network.
- The injected harness fault is observed through a second TestClient with
  `raise_server_exceptions=False` - the only way a 500 is visible in process -
  and the engine is restored in a `finally` so a failure cannot leak a broken
  function into later steps.
- .github/workflows/ci.yml: the server job runs the P4 gate alongside P2 and
  P3, and uploads its report with the others. A gate CI never runs is a gate
  that rots.
- One genuine bug in the gate itself, caught by its own first run: the journey
  never rendered a chart, so the workflow's `evidence` stage stayed open and
  the loop never closed. Not a code bug - the stage derives from artifacts and
  a chart is one of them. The gate now renders one.

## What the first CI runs caught (P4-CI-007, follow-up)

Five separate failures across five pushes, each a case of local state hiding a
gap that only a clean machine could see. All are fixed and the run is green;
this list is the reason the workflow was worth building, and it is the pattern
to expect whenever something "works on my machine":

1. **The gate scripts were invoked from the wrong directory.** They resolve
   the repo root from `__file__` and live at the repo root, but the server job
   runs with `working-directory: server`. `verification/p2/...` did not exist
   from there.
2. **The packaging job had no Rust toolchain.** `build_sidecar.sh` derives the
   target triple from `rustc -vV`, which macOS runners do not ship, so the
   triple came out empty and the sidecar would have landed under the wrong
   name.
3. **`@testing-library/jest-dom` was declared in the wrong package.json.**
   `setup-tests.ts` imports it, but it lived in the *root* package.json while
   the web job runs `npm ci` in `web/`. Locally the hoisted root node_modules
   resolved it; on the runner all three suites failed on the import.
4. **The shell could not compile at all.** `tauri::generate_context!()` embeds
   `web/dist-desktop` at compile time and `tauri-build` validates the
   `externalBin` resource - neither exists on a clean checkout. Two fixes: the
   desktop job builds the desktop web bundle, and it consumes the sidecar the
   packaging job builds (uploaded as an artifact) instead of each job building
   its own.
5. **The artifact transport dropped the executable bit.** The downloaded
   sidecar arrived without +x and `spawn()` failed with PermissionDenied. The
   workflow chmods it back rather than making the Rust test tolerant of a
   binary it could not run - that test's purpose is a real packaged sidecar.

The lesson carried forward: **anything that "works locally" but was never run
from a clean directory is suspect.** The stale egg-info, the hoisted
node_modules, the prebuilt dist-desktop and the local sidecar were all the same
bug in four costumes.

## What changed (P4-CI-007)

- .github/workflows/ci.yml (NEW): four jobs - `server` (uv venv from pyproject,
  pytest, P2 and P3 gates, reports uploaded), `web` (npm ci, npm test,
  npm run build - tsc -b runs first, so a type error the jsdom tests cannot see
  fails CI), `desktop` (the server venv at the exact path the resolver looks
  for, then `cargo test` and `cargo test --features e2e`), `packaging`
  (build_sidecar.sh plus a /health smoke against the built binary). Every
  command was validated by running it locally in the order the job runs it.
- server/pyproject.toml: two fixes found by validating the install path on a
  clean venv. `[tool.setuptools] packages = ["app"]` - flat-layout discovery
  saw `app` and `tests` as competing top-level packages and failed on a fresh
  checkout; a stale egg-info was masking it locally, which is exactly the kind
  of bug CI exists to catch. And a `packaging` extra declares PyInstaller,
  which was installed ad-hoc and was not reproducible.
- README.md (NEW): the layers and their test commands, the gates, and the
  unsigned-app first-launch workaround in plain language - DEC-004's
  consequence is that this is a documented user-facing behaviour, not an
  omission.
- ai/DECISIONS.md DEC-004: signing deferred to P5, with the reason, the
  alternatives considered (ad-hoc/self-signed, `xattr -cr` bypass) and why each
  is worse, and the consequences - chiefly that nothing in P4 may depend on the
  app being signed.
- ai/ROADMAP.md: P4 marked COMPLETE, the stage marker moved to P5, and a P5
  entry checklist proposed (signing first, then a P4 gate, observability, the
  carried 500 JSON envelope, release automation).

## What changed (P4-PERF-006)

- server/app/analysis.py: `profile_csv` reads the description via
  `SELECT * FROM <reader> LIMIT 0` instead of `SELECT *` + `fetchall()`. The
  per-column aggregate pass now leads with `COUNT(*) AS _total` and the row
  total is read from slot 0 (offset starts at 1), so the separate COUNT(*) scan
  is gone. `_duplicate_row_count(connection, path, total_rows)` takes the total
  it already has instead of rescanning for it.
- server/tests/test_large_datasets.py (NEW): 6 tests over a deterministic
  50k-row generated dataset whose stats are analytically known (id 1..N, region
  cycling through 5 values, quantity cycling 1..50, revenue = quantity * 2.5,
  one null every ten rows). Profile correctness at scale, the wide-table width
  slicing (40 columns), exact duplicate counts (500 groups x 4 repeats), the
  result cap truncating `SELECT *`, an aggregation summing every row, and an
  export/import round trip that re-profiles to the same row count.
- No API or output-shape change - the profile dict is identical, so nothing
  downstream (the planner, the generator, export) needed to move. The speedup
  is documented as benchmark numbers in ai/CURRENT_STATE.md so the next
  regression is measured against a number.

## What changed (P4-VALID-005)

- server/app/main.py: `_row_key(row)` (new) canonicalises one row as JSON so the
  sort key is type-aware and deterministic; `_reproduce_sql` now compares
  `sorted(rerun["rows"], key=_row_key) == sorted(stored, key=_row_key)`. Nothing
  else moved - the stored shape, the verdict vocabulary and the
  missing_data / evidence_integrity checks are untouched, and a query that no
  longer binds still records a failed reproducibility check rather than a 500.
- `_reproduce_python` was deliberately NOT changed: the Python tabulator is
  deterministic, and there a changed column order *is* a changed result, so the
  positional comparison stays correct.
- server/tests/test_validation.py: +2 tests.
  `test_validate_accepts_reordered_unordered_result` reverses the stored rows of
  a real GROUP BY run in SQLite and requires a `supported` verdict - this is the
  one verified to FAIL before the fix. `test_validate_unordered_groupby_is_stable_across_reruns`
  validates an ORDER BY-less GROUP BY 12 times and requires the verdict set to be
  exactly `{"supported"}`; repetition is the only honest way to pin it, since the
  order is not under the test's control. The pre-existing
  `test_validate_fails_when_result_drifts` (a substituted value no rerun can
  produce) is what proves the fix did not weaken the gate.
- ai/TASKS.md: the P4-VALID-005 contract, plus the P4-UX-004 table row that its
  commit had missed.

## What changed (P4-UX-004)

- web/src/CaseWorkspace.tsx: the workspace becomes the loop the core walks, one
  panel per step - attach + profile (file picker, then columns and nulls), a
  profile-scoped generate-code panel whose Run posts to the runs endpoint, the
  run list with Interpret and Draft-finding buttons, a draft rendered with its
  statement / interpretation / caveat / grounds and an Accept that posts to
  /findings, then a Validate that renders the verdict and its checks. Each
  assistant panel shows which engine spoke (source).
- web/src/api.ts: the remaining contracts - attach, profile, run SQL (single-
  and multi-dataset), generate-code, interpret, draft-finding, POST /findings,
  POST .../validate.
- web/src/index.css: panel and action styles for the new surfaces.
- web/src/CaseWorkspace.test.tsx: +9 tests (17 web total).
- No server change - every call is an existing endpoint, which is what keeps the
  propose / human-decides split structural rather than a UI flag.

## What changed (P4-UX-003)

- web/src/api.ts: rewritten as a typed client over the real contracts - GET
  /cases (with q), GET /cases/{id}, .../progress, .../datasets, .../runs,
  POST + GET .../chat. One shared request() throws ApiError carrying the status
  and a message parsed from the body only when the body is JSON.
- web/src/CaseList.tsx (NEW): the front door - list, search, open, or create.
  Exports messageOf(), the one place an error becomes readable text.
- web/src/CaseWorkspace.tsx (NEW): the question, the Workflow panel (stage,
  next action, per-stage completion), the Artifacts panel (datasets, runs), and
  the Chat panel with citation chips and an engine badge.
- web/src/CaseCreation.tsx: unchanged form, now navigates into the created
  case; takes onCreated/onCancel.
- web/src/App.tsx: state-based navigation (list | workspace | create) - no
  router, so the bundle gains no runtime dependency.
- web/src/index.css: panel, list, chip and stage styles.
- web/src/CaseList.test.tsx, CaseWorkspace.test.tsx (NEW), CaseCreation.test.tsx
  (+1 test).
- One real markup lesson, caught by the tests: React Testing Library's text
  matcher sees only an element's *direct* text nodes, so `Stage:
  <strong>analyze</strong>` could not be matched by any regex or function
  matcher. The sentences are now single text nodes - better for a screen
  reader and for translation too.
- No browser is registered with the computer-use surface on this machine, so
  the visual check is a data-path smoke: the exact calls the components make,
  run against the live core (create, list, search, progress, datasets, runs,
  chat round trip, 404 detail). The rendering is covered by vitest against the
  real response shapes, and the vite proxy was confirmed serving the bundle.

## What changed (P4-RELIABILITY-002)

- server/app/errors.py (NEW): the taxonomy in one place. `INPUT_ERROR_TYPES`
  is `(ValueError, duckdb.Error)` - the former is what every engine raises for
  what it validates, the latter is what DuckDB raises for SQL that cannot run
  and is deliberately *not* a ValueError. Importing duckdb here keeps that
  knowledge in the module that owns it.
- server/app/main.py: the five engine sites (single SQL run, multi-dataset SQL
  run, Python run, EDA, chart render) drop `except Exception -> 400` for
  `except INPUT_ERROR_TYPES`. The chart site catches ValueError alone, since
  render_chart validates everything itself.
- server/app/{planner,interpreter,drafter,generator,assistant}.py: the LLM
  fallback keeps catching everything but logs the reason first. `import
  logging` added to each.
- server/tests/test_error_semantics.py (NEW): 12 tests. Input errors stay 400
  (bad SQL, unknown column, multi-dataset bad SQL, a sandbox rejection, an
  unknown EDA op, an unknown chart kind); an injected harness fault answers 500
  in all five engines, via a TestClient with `raise_server_exceptions=False`
  - the only way a 500 is observable in process. Plus one pinning that an
  unexpected LLM failure still falls back *and* is logged.
- One nuance worth carrying: a 500 answers with Starlette's plain-text
  "Internal Server Error", not JSON. That is honest and logged, but the React
  shell does `res.json()` on errors, so the UX task should give it a JSON
  envelope - noted in CURRENT_STATE.md rather than expanded into this task.

## What changed (P4-VERIFY-001)

- verification/p3/verify_p3.py (NEW): the P3 gate, modelled on the P0/P1/P2
  gates. In-process TestClient, one atomic journey, a step table and an exit
  criteria table written to verification/p3/REPORT.md, exit 0 only when every
  step passes. It builds its own data - a CSV plus a Parquet written from a
  table with DuckDB, so the join deliberately mixes formats - and uses clean
  data on purpose, so validation reaching `supported` proves the join
  reproduces rather than that a messy finding was tolerated.
- Hermeticity is the one design decision worth stating: app.main loads
  server/.env at import (a gate is a script, not a pytest module) and every
  assistant engine reads DAH_LLM_API_KEY at *call* time, so scrubbing those
  variables after import is enough to make the whole journey deterministic.
  The LLM paths stay covered by the suite, which tests both engines
  explicitly; the gate's own report says source=deterministic on every
  assistant step.
- ai/ROADMAP.md, ai/CURRENT_STATE.md, ai/TASKS.md: P4 is IN PROGRESS with
  P4-VERIFY-001 DONE, the P3 gate added to the standing checks, and the
  P4-VERIFY-001 contract recorded.

## What changed (P3-EVIDENCE-006)

- server/app/evidence.py (NEW): `build_evidence_graph` reads the case's rows
  and builds nodes, edges and traces. Nothing is stored - it is a pure
  projection, so it cannot drift from what is on disk.
- server/app/main.py + models.py: the `/evidence-graph` endpoint and
  `EvidenceGraph` / `EvidenceNode` / `EvidenceEdge` / `ClaimTrace`.
- server/tests/test_evidence_graph.py (NEW): 7 tests, including orphan
  reporting (a dangling claim inserted directly into SQLite) and a join run
  whose trace covers both datasets it bound.

## What changed (P3-ANALYSIS-005)

- server/app/eda.py (NEW): `run_eda` compiles segment / correlate /
  distribution to SQL; column names are quoted and refused if they contain a
  quote; the numeric-vs-categorical choice for distribution reads DuckDB's own
  column types via DESCRIBE rather than probing with AVG.
- server/app/main.py + models.py: the `/eda` endpoint, `EdaCreate`, `EdaResult`.
- server/tests/test_eda.py (NEW): 9 tests.

## What changed (P3-FLOW-004)

- server/app/workflow.py (NEW): `case_progress` counts the case's artifacts and
  returns the first stage with nothing behind it, plus the deterministic next
  action and the endpoint that performs it. The loop closes when a finding has
  been validated.
- server/app/main.py + models.py: the `/progress` endpoint, `CaseProgress` and
  `WorkflowStage`.
- server/tests/test_workflow.py (NEW): 5 tests, including a full walk of the
  loop from case creation to a closed loop.

## What changed (P3-DATA-003)

- server/app/analysis.py: `run_query_multi(paths, sql)` binds placeholders
  positionally; `run_query` and the new path share `_execute_read_only`.
- server/app/main.py: `POST /cases/{case_id}/runs`; `dataset_ids_json` on the
  runs schema and in every read path; `_remap_dataset_ids` so a duplicated
  case's runs point at the copy's own datasets; validation reproduces through
  the multi path and now treats a query that no longer binds as a failed check
  rather than a 500.
- server/app/exporter.py: packages carry `dataset_ids` per run; import remaps
  them to the imported case's datasets.
- server/tests/test_multi_dataset_runs.py (NEW): 10 tests.
- Two real bugs surfaced and are pinned by tests: the placeholder regex needed
  escaping (a literal `?` inside a group is not a regex extension), and an
  INSERT value list had shifted a column (found by the validation tests).

## What changed (P3-CHART-002)

- server/app/charts.py: `render_chart(..., fmt="svg"|"png")` dispatches to
  `_render_svg` / `_render_png` after building a `ChartModel` that owns all
  geometry (scale, ticks, category order, bar geometry). Pillow is imported
  lazily; a missing install is a clear ValueError, not a crash.
- server/app/main.py: `ChartCreate.format`; artifact named `chart_<id>.<fmt>`;
  `_chart_media_type` sniffs PNG/SVG from stored bytes; duplicate preserves
  the source chart extension.
- server/app/exporter.py: charts exported with `format` + base64 `image_b64`
  (legacy `svg` text kept); import accepts both shapes.
- server/pyproject.toml: `charts` optional dependency (`pillow>=10`).
- server/tests/test_charts_raster.py (NEW): 9 tests, including a pixel scan of
  bar geometry and PNG export round trip.
- A refactor bug was caught here: the grouped-bar x-offset must use the series
  index, not the point index, or later bars slide off-canvas. Fixed in both
  backends and pinned by the new pixel test.

## What changed (P3-CASE-007)

- server/app/history.py (NEW): `build_case_history` reads the case's rows and
  derives a timeline - one event per artifact, stamped with that artifact's own
  timestamp. Like the evidence graph it is a pure projection, so it cannot drift
  from what is on disk. Validation has no persisted timestamp of its own, so a
  finding's validation status rides along as its event's detail rather than
  being invented as a separate timestamped entry.
- server/app/db.py: new `templates` table (`id, name, question, dataset,
  created_at`) under `CREATE TABLE IF NOT EXISTS` - older databases need no
  migration.
- server/app/main.py: `q` on `GET /cases` (LIKE on LOWER(question)/LOWER(dataset)
  with the term's wildcards escaped so a search is a literal substring);
  `GET /cases/{id}/history`; the four template endpoints. Case insertion is now
  a shared `_insert_case` helper so direct creation and templated creation
  cannot diverge on defaults.
- server/app/models.py: `Template`, `TemplateCreate`, `CaseFromTemplate`,
  `HistoryEvent`, `CaseHistory`.
- server/tests/test_case_history.py (NEW): 6 tests. server/tests/
  test_case_templates.py (NEW): 10 tests. tests/test_cases.py: 4 search tests,
  including one pinning that `%` and `_` in a term stay literal.

## What changed (P3-SEC-001)

- server/app/python_exec.py: `run_python` is now an orchestrator. It writes a
  JSON job into a per-run scratch dir, spawns `app.python_worker` as a child
  (sandbox-exec wrapped when available) with a scrubbed environment, and reads
  the tabulated result back from stdout. The old in-process body is
  `execute_user_code`, which the worker calls; timeouts are enforced three
  ways - parent kills the process group after limit + startup grace, child
  RLIMIT_CPU, child SIGALRM.
- server/app/python_worker.py (NEW): the in-sandbox entrypoint. Reads the job,
  runs `execute_user_code`, and emits either the result or `{"error": ...}`;
  it stays alive to report contract violations so the parent answers 400 with
  a useful message.
- server/tests/test_python_hard_sandbox.py (NEW): 6 tests at the process
  boundary - real seatbelt enforcement (scratch write allowed, outside write
  and network denied), child env scrub, process-group kill, runaway loop,
  dead worker, contract violation.

## What changed (P2-CASE-012)

- server/app/exporter.py (NEW): `export_case` assembles one self-contained JSON
  package (case, datasets with base64 bytes, profiles, runs, findings, charts
  with inline SVG, plans); `import_package` reconstructs it with fresh IDs and
  remapped references. `PackageError` covers malformed packages.
- server/app/main.py: `GET /cases/{id}/export` and `POST /cases/import`.
- server/tests/test_export.py (NEW): 5 tests - every section present with
  embedded bytes/SVG, 404 on unknown case, round trip restores state
  losslessly, references relink and artifacts are live (chart served, imported
  dataset queryable), malformed packages rejected.
- verification/p2/verify_p2.py (NEW): the P2 milestone gate, modelled on the P1
  gate. Walks the whole loop on deliberately messy data (a null, a duplicate
  row, a categorical split) and requires every P2 capability to fire.

## What changed (P2-AI-011)

- server/app/planner.py (NEW): the Analysis Planner. `plan_analysis` derives a
  structured plan deterministically from the question + profile - missingness,
  numeric spread/outliers, categorical splits, temporal trends, duplicates - so
  every item references real columns. `LLMPlanner` is an OpenAI-compatible
  backend on httpx (no SDK dependency), enabled by DAH_LLM_API_KEY (plus
  optional DAH_LLM_BASE_URL / DAH_LLM_MODEL). `create_plan` prefers the LLM,
  validates its output with `validate_plan`, and falls back to the deterministic
  planner on any failure - an unavailable or misbehaving LLM never blocks the
  loop. The persisted `source` field says which engine made the plan.
- server/app/main.py: `POST /cases/{id}/datasets/{id}/plan` (creates),
  `GET .../plan` (latest), `GET .../plans` (history). Planning requires a
  profile first (400 names the missing step). Duplicate now copies plans and
  delete now removes them.
- server/app/models.py: `Plan`, `PlanSummary`.
- server/app/db.py: new `plans` table.
- server/tests/test_plans.py (NEW): 10 tests - create/retrieve across sessions,
  plan references real columns, 400 without a profile, 404s, newest-first
  listing, LLM fallback on failure and on malformed output, valid LLM output
  persisted with source=llm, schema validation, and survival through
  duplicate/delete.

## What changed (P2-CASE-010)

- server/app/main.py: three endpoints - `PATCH /cases/{id}` (rename question
  and/or dataset label, bumps updated_at), `POST /cases/{id}/duplicate` (deep
  copy: case, datasets with bytes on disk, profiles, runs, findings, charts,
  all with fresh IDs and remapped references), `DELETE /cases/{id}` (children
  in FK order then the case row, plus `shutil.rmtree` of the case directory).
- server/app/models.py: `CaseUpdate`.
- server/tests/test_case_management.py (NEW): 9 tests - rename persists and
  leaves data alone, single-field rename, 404s, duplicate is deep and
  independent (new IDs, mutating the copy does not touch the original,
  dataset bytes copied into the copy's own directory), delete removes rows,
  files, and 404s afterwards, other cases untouched.

## What changed (P2-ANALYSIS-009)

- server/app/charts.py (NEW): deterministic, dependency-free SVG renderer.
  `bar` and `line` over one or more series (optional `series` column splits the
  result into legend-ordered series). Rendering from the *stored* run result
  keeps a chart reproducible after the run; SVG is stored in the case dir.
- server/app/main.py: chart endpoints - `POST /cases/{id}/runs/{id}/charts`,
  `GET .../charts` (list), `GET /cases/{id}/charts/{id}` (metadata),
  `GET /cases/{id}/charts/{id}/image` (serves the SVG as image/svg+xml).
- server/app/models.py: `ChartCreate`, `Chart`, `ChartSummary`.
- server/app/db.py: new `charts` table (run-scoped, case-owned).
- server/tests/test_charts.py (NEW): 11 tests - persist and serve, reopen in a
  new session, byte-identical re-render, multi-series line, chart from a Python
  run, rejection of unknown kind/column and non-numeric measure, 404s, and bar
  geometry (anchored on the zero baseline, heights proportional to values).

## What changed (P2-ANALYSIS-008)

- server/app/python_exec.py (NEW): restricted Python engine. User code gets a
  read-only `dataset` handle (`dataset.rows` as list of dicts, `dataset.query(sql)`
  under the same read-only SQL gate) and leaves its answer in `result`; a list of
  dicts or lists becomes the run's columns/rows.
- server/app/main.py: `POST /cases/{case_id}/datasets/{dataset_id}/runs/python`;
  `runs` read/write paths now carry `kind` and `code`; SQL runs unchanged.
- server/app/models.py: `PythonRunCreate`, `RUN_KINDS`, `Run`/`RunSummary` gained
  `kind` (`sql` | `python`) and nullable `code`; `sql` is now nullable.
- server/app/db.py: `runs` gained `kind` (default `sql`) and `code` columns, both
  added by `_ensure_column` so older databases migrate in place.
- server/tests/test_python_runs.py (NEW): 11 tests - persist/reopen, DuckDB query
  from Python, listing alongside SQL, and rejection of write queries, blocked
  imports, filesystem writes, dunder escapes, missing/empty `result`, 404s.

## What changed (P3-AI-011)

- app/interpreter.py (NEW): `interpret_result` (the deterministic reader -
  every figure it quotes is computed from the result's own rows, so it cannot
  invent a number), `LLMInterpreter` (OpenAI-compatible, httpx, JSON-only
  prompt), `validate_interpretation`, and `create_interpretation`, which prefers
  the LLM and falls back on any failure.
- app/db.py: the `interpretations` table (a child of a run, like charts).
- app/main.py: the three endpoints - POST (create), GET .../interpret (latest),
  GET .../interpretations (history, newest first) - plus duplication copying a
  case's readings onto the copy's own runs and deletion removing them.
- app/models.py: `Interpretation`.
- tests/test_interpretations.py (NEW): 9 tests, including one that pins the
  honesty property - the deterministic read may only quote values the result
  actually contains (the two aggregated totals, 80.5 and 325.0, and no others).

## What changed (P3-AI-014)

- app/assistant.py (NEW): `summarize_case` (the facts, read from the case's
  rows - runs carry columns and row counts, not result rows, because a
  conversation points at evidence rather than replaying it), `answer_question`
  (deterministic; counts, a named column's real profiled stats, a dataset
  summary, the latest finding, or the derived stage and next action),
  `_references` / `parse_ground` / `validate_answer` (the citation budget: each
  ground must be `kind:name` with name in the case), `LLMAssistant`
  (OpenAI-compatible, httpx, JSON-only prompt, told the exact artifact ids and
  the last ten turns) and `create_answer`, which prefers the LLM and falls back
  on any failure - unavailable, malformed, or citing an artifact the case does
  not have.
- app/db.py: the `conversations` table under `CREATE TABLE IF NOT EXISTS`, so
  older databases need no migration.
- app/main.py + models.py: `POST /cases/{id}/chat` (201, persists the turn) and
  `GET /cases/{id}/chat` (oldest first), `ChatRequest` and `ConversationTurn`.
  Case deletion now removes the conversation with the rest of the case's
  children; duplication deliberately does not copy one (a duplicate starts a
  fresh investigation).
- tests/test_conversation.py (NEW): 12 tests - counts, a column's real stats,
  the derived stage and next action, grounds checked against the case's own
  rows, LLM accepted, the prior turn reaching the LLM, invented citation
  rejected, failure and malformed fallbacks, persistence oldest-first, delete
  cleanup at the row level, 404s.

## What changed (P3-AI-013)

- app/generator.py (NEW): `generate_code` (deterministic; `_pick_axes` chooses
  the measure and dimension from the profile and `_is_identifier` keeps a unique
  key from being summed or grouped by), `_sql_identifiers` /
  `_python_read_columns` / `_columns_referenced` (the reach of a proposal -
  aliases, function calls, qualified names and SQL literals are treated as
  structure, and a Python proposal's *reads* are checked while its output dict
  keys are not, because inventing an output name invents nothing), the
  read-only check `_looks_read_only`, `validate_code`, `LLMGenerator`
  (OpenAI-compatible, httpx, JSON-only prompt, told the exact columns that
  exist) and `create_code`, which prefers the LLM and falls back on any failure
  - unavailable, malformed, a wrong `kind`, a statement that is not read-only,
  or a column the dataset does not have.
- app/main.py + models.py: the stateless `POST .../generate-code` endpoint (200
  - no INSERT, no new table), `GenerateCodeRequest` and `GeneratedCode`. It
  requires a profile first (400 names the missing step), exactly as planning
  does, because a proposal against an unprofiled dataset is a guess.
- tests/test_code_generation.py (NEW): 13 tests - deterministic SQL and Python
  proposals naming the dataset's real columns (and not its identifier), columns
  used checked against the profiled set, both proposals running as-is through
  the existing run endpoints, single-read-only check, LLM accepted, invented
  column rejected, DELETE rejected, failure and malformed fallbacks, no state
  written for either kind, 400 without a profile, 404s including a cross-case
  dataset.

## What changed (P3-AI-012)

- app/drafter.py (NEW): `draft_finding` (the deterministic drafter - every figure
  is computed from the result's own rows, and a result with no numeric measure
  gets an honest weaker draft that says so), `_allowed_numbers` (the honesty
  budget: cell values, the row/column counts, and how often each value repeats),
  `validate_draft`, `LLMDrafter` (OpenAI-compatible, httpx, JSON-only prompt)
  and `create_draft`, which prefers the LLM and falls back on any failure -
  unavailable, malformed, schema-invalid, or quoting a magnitude the result does
  not contain.
- app/main.py + models.py: the stateless `POST .../draft-finding` endpoint (200 -
  no INSERT, no new table) and `DraftFinding`. It loads exactly what an
  interpretation loads (run columns/rows, question, SQL or script, profile) so
  the two slices compose.
- tests/test_drafting.py (NEW): 10 tests - deterministic draft naming the run's
  real columns, grounds checked against the result's own honesty budget via the
  API, LLM accepted, invented magnitude rejected, failure and malformed
  fallbacks, the findings table left empty, accept-then-validate round trip
  (an accepted draft validates `supported`), the no-numeric-column draft, 404s.

## What changed (P3-VALID-010)

- server/app/main.py: validate_finding no longer special-cases Python runs
  aside with a 400. Reproduction is factored into `_reproduce_sql` and
  `_reproduce_python` (both record the same reproducibility check through
  `_record_repro`), and the missing_data / evidence_integrity checks and the
  status arithmetic are shared between the two kinds. Python compares both
  columns and rows, because the tabulator names columns in first-seen order and
  a shape change would otherwise hide behind matching values.
- One real bug surfaced and is pinned by a test: the run lookup in
  validate_finding did not select `runs.code`, so `run_row["code"]` raised
  sqlite3's IndexError "No item with that key" - which the broad except
  faithfully reported as "script rejected". Fixed by selecting the column.
- server/tests/test_validation.py: +4 tests (reproduces, row drift, shape drift,
  and a script that now raises returning a verdict rather than a 500).
  tests/test_python_runs.py: the one test that pinned the old 400 now asserts a
  real `supported` verdict.

## What changed (P3-DATA-009)

- server/app/main.py: `DELETE /cases/{case_id}/datasets/{dataset_id}` (204),
  plus `_runs_touching_dataset`, the lookup that decides whether deletion is
  safe. It scans a case's runs for the dataset as either the primary
  (runs.dataset_id) or one of several (runs.dataset_ids_json, P3-DATA-003) -
  legacy runs have no JSON list, so the primary column is checked on its own.
  Deletion removes the profile, the plans and the file alongside the row.
- server/tests/test_dataset_delete.py (NEW): 8 tests. The refusal is exercised
  both for a single-dataset run and for the non-primary member of a join run,
  and one proves the gate is live data rather than a stored flag by removing
  the run row directly (no run-delete endpoint exists yet) and watching
  deletion succeed.

## What changed (P3-SHELL-008)

- desktop/ (NEW): the whole Tauri 2 shell. `src/core_server.rs` is the pure,
  tested resolution + health-gate logic (`resolve_server_command`,
  `wait_for_health`, `ServerCommand::to_process`, group-kill `ServerChild`);
  `src/main.rs` is the window lifecycle; `tauri.conf.json` has **no `devUrl`**,
  so every build - debug included - serves the embedded bundle and can never
  point the webview at a port nothing is serving. Capabilities grant only
  `core:default`; the webview never loads a remote URL, so the desktop bundle
  is built with an absolute API URL (`VITE_API_URL=http://127.0.0.1:8123`).
- server/app/supervisor.py (NEW): `start_parent_watchdog()` - a daemon thread
  that `os._exit(0)`s the core when `DAH_PARENT_PID` is gone. No-op without the
  variable; rejects junk and <= 0. Called from main.py after the imports.
- server/dah_core_main.py + dah-core.spec + build_sidecar.sh (NEW): the
  PyInstaller one-file sidecar and the script that installs it as
  `desktop/src-tauri/binaries/dah-core-<triple>` (gitignored, 85MB, never
  committed).
- web: `build:desktop` and `build:desktop:watch` produce the desktop bundle;
  `vite.config.ts` pins the dev server to port **5273** with `strictPort` -
  5173 (vite's default) collides with another local dev server, and a silent
  port hop is what left the shell's webview on a dead page.
- Two test-hygiene fixes landed while verifying: `test_export.py` is now
  hermetic against an ambient LLM key, and the P2 gate no longer leaks
  `DAH_LLM_API_KEY` into the pytest subprocess it spawns (see below).

## Sandbox posture (documented, see module docstring)

Blocked: filesystem writes, process execution, network egress, resource
exhaustion (wall-clock + CPU limits). This is a *soft* sandbox for a local
single-user tool: it stops accidental writes and runaway AI-generated code, not a
hostile user who owns the machine. Address-space limits were tried and dropped -
macOS maps far more VM than a useful cap allows; a real memory bound needs the
separate-process hard sandbox planned for V1. Validation of Python runs is
reported as unsupported (clear 400) rather than faked; that gate is future work.

## Tests performed (current)

- server pytest: 336 passed (315 + 21 update check; verified again on a clean
  venv built from pyproject - the install path CI uses)
- CI on GitHub's own runners: ALL FOUR JOBS GREEN
  (run 35490199963, the first green run since ae0ba33 - server suite + P2/P3/P4
  gates, web suite + build, sidecar packaging + the /health and packaged-log
  smoke, desktop shell lifecycle with both e2e tests against the real sidecar).
  The runner is macos-latest; macos-13 is retired from the hosted pool (DEC-005)
- Release pipeline: v0.1.0 published end to end from tag (run 35490519483).
  The 79MB zip's sha256 verified against its checksum asset, Info.plist reads
  0.1.0, and the bundle carries dah-shell (15MB) + dah-core (78MB). The build
  is arm64 and unsigned, flagged pre-release
- P4 gate: `server/.venv/bin/python verification/p4/verify_p4.py` PASS on all
  18 journey steps and all 10 exit criteria (the last step re-runs the suite)
- desktop shell: 7 Rust tests, now stable - five are #[serial] after CI caught
  two interference races (port 8123 and the DAH_DEV_CORE env var)
- web: 17 passed (CaseList 5, CaseCreation 3, CaseWorkspace 9); `cd web && npm test`
- desktop shell: 12 Rust tests - `cd desktop/src-tauri && cargo test` (7 unit)
  and `cargo test --features e2e` (+2 live-core tests)
- P3 gate: `server/.venv/bin/python verification/p3/verify_p3.py` PASS on all
  23 journey steps and all 15 exit criteria (the last step re-runs the suite)
- P2 gate: `server/.venv/bin/python verification/p2/verify_p2.py` PASS on all
  18 steps

## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

**P7-SHELL-004 is DONE**: case management has a surface. The web suite is 39
tests (was 34, +5 in `CaseList.test.tsx`), `npm run build` passes, and the
desktop bundle builds from the same source. The server side is untouched and
stays at 358.

### What is unbuilt, in priority order

- **The rest of the web-shell gap** - P7 item 2, now three surfaces closed.
  Still no UI: templates (`/templates`, `/from-template`, promote-a-case),
  cross-case memory, EDA (`/eda`), the evidence graph (`/evidence-graph`), and
  case history. Each is a panel over an existing contract; none needs a new
  endpoint.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk. Mostly a
  sequencing layer over the workflow stages that already exist (P3-FLOW-004).
- **Multi-agent workflows** - only after EVALUATE, which is the audit layer an
  agent's own output has to survive.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Eight tasks have landed
since v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.
## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

**P7-SHELL-003 is DONE**: the agent has a surface as well as a core. The web
suite is 34 tests (was 27, +6 in `CaseWorkspace.test.tsx` and +1 in
`api.test.ts` for the nested-detail unwrap), `npm run build` passes and the
desktop bundle builds from the same source. The server side is untouched and
stays at 358.

### What is unbuilt, in priority order

- **The rest of the web-shell gap** - P7 item 2, now two surfaces closed.
  Still no UI: templates (`/templates`, `/from-template`), cross-case memory,
  EDA (`/eda`), the evidence graph (`/evidence-graph`), case history, and
  rename/duplicate/delete. Each is a panel over an existing contract; none
  needs a new endpoint.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk. Mostly a
  sequencing layer over the workflow stages that already exist (P3-FLOW-004).
- **Multi-agent workflows** - only after EVALUATE, which is the audit layer an
  agent's own output has to survive.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Seven tasks have landed
since v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.
## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

**P7-SHELL-002 is DONE**: EVALUATE mode now has a surface as well as a core.
The web suite is 27 tests (was 21, +6 in `CaseWorkspace.test.tsx`), `npm run
build` passes - `tsc -b` runs first, so a type error the jsdom tests cannot see
fails it - and the desktop bundle builds from the same source. The server side
is untouched by this change and stayed at 358 tests.

### What is unbuilt, in priority order

- **The rest of the web-shell gap** - P7 item 2, partly closed. Still no UI:
  the agent (`/agent`, with its approve/reject loop - the highest-value of
  them, because a plan executing itself one approved write at a time is
  observable today only through the API), templates (`/templates`,
  `/from-template`), cross-case memory, EDA (`/eda`), the evidence graph
  (`/evidence-graph`), case history, and rename/duplicate/delete. Each is a
  panel over an existing contract; none needs a new endpoint.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk. Mostly a
  sequencing layer over the workflow stages that already exist (P3-FLOW-004).
- **Multi-agent workflows** - only after EVALUATE, which is the audit layer an
  agent's own output has to survive.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). Six tasks have landed since
v0.1.0, so `0.2.0` is the honest next label when a release is wanted.

Nothing is unblocked-but-undone.
## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

**P7-EVAL-001 is DONE**, and with it the first of P7's four checklist items.
EVALUATE mode audits submitted work against the nine axes the specification
names; the core can now be pointed at an analysis it did not write and answer
whether it holds up. Everything below was verified green: 358 server tests
(was 336, +22 in `server/tests/test_evaluator.py`), the P2, P3 and P4 gates
each re-running the suite at 358, the web suite at 21 and the desktop shell at
22 Rust tests.

### What is unbuilt, in priority order

- **The web shell is behind the core** - P7 item 2, and the highest-value work
  left that needs no new core capability. These endpoints have no UI at all:
  the agent (`/agent`), templates (`/templates`, `/from-template`), cross-case
  memory, EDA (`/eda`), the evidence graph (`/evidence-graph`), case history,
  rename/duplicate/delete, `/schema-version`, `/updates/latest` - and now
  `/evaluate`, which currently answers only through the API. The core can do
  all of it; the shell is the distance between "works" and "usable".
- **LEARN mode** - a guided Why -> What -> How -> Validate walk over a dataset.
  Mostly a sequencing and presentation layer over the workflow stages that
  already exist (P3-FLOW-004), which is why it follows the shell gap.
- **Multi-agent workflows** - the spec's ladder above the single driver that
  exists (P6-AGENT-002). Only after EVALUATE, which is how an agent's own
  output gets audited.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.
  None pays for itself at a user count of one, and the architecture is
  deliberately not shaped around them.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build
is arm64 and unsigned, flagged pre-release (DEC-006). The version has not been
bumped since v0.1.0; five tasks have landed since, so a `0.2.0` is the honest
next label when a release is wanted.

Nothing is unblocked-but-undone.
## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

**P6 is CLOSED.** All five entry-checklist items are delivered: cross-case
recall, agentic analysis, analytical-shape templates, the versioned migration
path, and the update check. P0 through P6 are complete.

The last task, P6-UPDATE-005, delivered the half of an update flow that is
verifiable and deliberately not the other half. `GET /updates/latest` answers
one of three truths and the shell's **DAH > Check for Updates...** menu item
opens the release page or shows why it could not tell. The self-replacing
install did not ship, because the repository is private (an unauthenticated
feed answers 404, verified) and the app is unsigned (DEC-006), so a payload
cannot be signature-verified. That is a slot, not a gap: `tauri-plugin-updater`
consumes exactly this check when signing lands, and the design's core
distinction - "could not check" is never reported as "is up to date" - is what
makes the slot safe to fill later.

### What is unbuilt, in priority order

- **EVALUATE mode** - the spec's third product mode, and the one DAH uniquely
  owns. Import existing analytical work (SQL, a Python script, a notebook, a
  dashboard export, a spreadsheet, an AI-generated analysis) as the *thing under
  inspection*, and audit it against nine axes the spec names: question, data,
  quality, method, calculation, evidence, claim, visualization, limitations.
  Most of the machinery already exists - read-only execution, deep profiling,
  rerun validation, the evidence graph, the honesty budgets. What does not is
  importing an artifact *as a claim being evaluated* rather than as data to
  analyse. This is the largest genuine capability left, and it is the one that
  separates DAH from a notebook.
- **LEARN mode** - a guided Why -> What -> How -> Validate walk over a dataset.
  Mostly a sequencing and presentation layer over the workflow stages that
  already exist (P3-FLOW-004), which is why it is second.
- **The web shell is behind the core.** These endpoints have no UI at all: the
  agent (`/agent`), templates (`/templates`, `/from-template`), cross-case
  memory, EDA (`/eda`), the evidence graph (`/evidence-graph`), case history,
  rename/duplicate/delete, `/schema-version` and `/updates/latest`. The core
  can do all of it; the shell is the distance between "works" and "usable".
- **Multi-agent workflows** - the spec's ladder above the single driver that
  exists. Only after EVALUATE, which is how an agent's own output gets audited.
- **Deferred, not dropped:** signing (DEC-006, the slot is in `release.yml`),
  cloud sync, team collaboration, warehouse connectors, enterprise governance.
  None pays for itself at a user count of one, and the architecture is
  deliberately not shaped around them.

### If the next step is a release

Tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The published build is
arm64 and unsigned, flagged pre-release (DEC-006). The version has not been
bumped since v0.1.0; four tasks have landed since, so a `0.2.0` is the honest
next label when a release is wanted.

Nothing is unblocked-but-undone.
## Repository state

- Every P3 task is one atomic commit, all pushed to `origin/master`
  (github.com/jensuid/DA-Harness), plus the phase close; P4 opens with
  P4-VERIFY-001, P4-RELIABILITY-002, P4-UX-003, P4-UX-004, P4-VALID-005,
  P4-PERF-006 and P4-CI-007 as their own commits, then the P4 phase close.
  `dfb115b` P3-SEC-001, `2c7b11f` P3-CHART-002, `f5df5d1` P3-DATA-003,
  `967544b` P3-FLOW-004, `7b7e49f` P3-ANALYSIS-005, `ebaa30e` P3-EVIDENCE-006,
  P3-CASE-007, P3-SHELL-008, P3-DATA-009, P3-VALID-010, P3-AI-011,
  P3-AI-012, P3-AI-013, P3-AI-014, and the phase close
  `bffc6ad docs: mark P3 V1 complete...`
- `.gitignore` covers `web/dist-desktop/`, `server/build/` (the 98MB PyInstaller
  tree) and `desktop/src-tauri/{target,gen,binaries}` - the 85MB sidecar is
  never committed.
- `.git` is writable under the current permission profile (this changed
  mid-session; the earlier read-only restriction is gone).

## Unresolved problems

- A test-isolation hole is closed but worth remembering: `app.main` skips
  loading `server/.env` under pytest, but that only stops the *file* load. If
  `DAH_LLM_API_KEY` is already in the environment - as it was for the pytest
  subprocess the P2 gate spawns, because the gate itself does load .env - the
  planner silently switches to the LLM inside the suite. That made the gate
  both slow (a live call per plan) and flaky (a fast LLM flipped an assertion
  that expected `source=deterministic`; a slow one fell back and passed). Fixed
  three ways: the P2 gate scrubs the LLM vars from its subprocess, the P3
  gate scrubs them from its own process as well (its journey would otherwise
  make a live call per assistant step), and `test_export.py` deletes them. Any
  future runner that spawns the suite must do the same.

## Next action

P6-MEMORY-001 is **DONE**: cross-case recall. A case could already cite its own
artifacts - runs, datasets, findings - through the grounds budget in
`assistant.py`, but `summarize_case` read exactly one case's rows, so every
investigation started from scratch even when the same anomaly was found and
explained last month. Now an answer can cite a *previous* case.

Three pieces:

- **`server/app/memory.py` (new)** - `summarize_memory` is a pure projection
  over the cases and findings already on disk. Relevance is a
  shared-content-word count against the prior case's question, dataset label
  and finding statements, with a hand-written stoplist and a threshold of two
  shared words. Deliberately not an embedding: no dependency, no network call,
  deterministic, and it makes the "nothing bears on this" answer honest rather
  than a confident stretch. A case with no findings is skipped however similar
  its question sounds - there is nothing to recall. It writes nothing; memory
  is derived, never stored, so it cannot drift from what is on disk any more
  than the evidence graph can.
- **`server/app/assistant.py`** - a new `case:` ground kind, a recall branch in
  the deterministic answer, and `_references` admitting both the prior case and
  its finding id. The recall branch fires when the question is *about* prior
  work (before/previous/earlier/...) or when the case has nothing of its own.
  It sits **ahead** of the column and dataset branches on purpose: "what did I
  find before about revenue?" names a column, and would otherwise be answered
  with this case's column stats - a true answer to a question nobody asked. A
  case with its own artifacts and no prior framing still gets its own stage and
  next action, because its own state is the more actionable thing. The LLM
  prompt now carries memory and its citation budget names the case kind.
- **`server/app/main.py`** - the chat endpoint passes the message through to
  `summarize_case`, because which prior cases are relevant depends on what was
  asked, not on the case.

The honesty budgets from P3-AI-011..014 survive by construction: a cross-case
ground must resolve to a real finding in a real other case or the answer is
rejected, exactly as an invented column is. The deterministic path needs no LLM
key, nothing logs what the analyst typed, and no new runtime dependency was
added - SQLite already holds everything.

**Verified:** server suite 267 passed (was 256, +11 in
`server/tests/test_memory.py`); the P4 gate PASS on all 18 journey steps and
all 10 exit criteria; the P3 gate PASS; web 21 passed; desktop 12 Rust tests.
Everything green locally; CI will run it on push.

One lesson worth carrying: three of the eleven tests failed on the first run
for a reason that was the *test's* fault, not the code's. The helper hardcoded
a finding about revenue in sales.csv while the question was about revenue, so
an allegedly off-topic prior case still shared two content words and was
correctly recalled. The code was right; the test asserted a separation its own
data did not have. A relevance threshold is only as honest as the corpus it is
measured against, and a fixture that says "weather" while quoting "sales" is
not a weather fixture.

**Next on the P6 checklist: agentic analysis** - a plan that executes itself
over the endpoints that already exist (generate code, run it, interpret, draft,
accept), with the human approving each write. It is the highest
capability-per-risk item left, and it is only safe because P4 pinned the
honesty budgets and P5 made faults observable. Its contract is not yet written;
the memory it will need is now in place, which is exactly why it was second.

After that: case templates carrying the analytical shape rather than just the
question, a versioned migration path before memory grows new tables, and a
Tauri update flow now that releases publish per tag.

Releasing: tag `v<x.y.z>` where x.y.z matches server/pyproject.toml. The
published build is arm64 and unsigned, flagged pre-release (DEC-006).

Nothing is unblocked-but-undone.

## Next action
**P8-CAUSAL-004 is DONE**: the causality check stopped commenting and started
guarding. An unsupported causal claim now gates the verdict - causality is the
fourth hard dimension, so "spend drives signups" over a correlation reaches
`insufficient_evidence`, not `supported`. New `server/app/causality.py` makes
three judgements: unhedged causal language over an observational comparison is
unsupported; a hedge ("may drive") or negation ("does not cause") is the author
naming the limit and passes; an intervention the context records *and the SQL
compares across* earns causation. The branch AT-18 turns on: an intervention
merely mentioned but never compared across still fails - mentioning is not
using.

**The 50-case corpus is data, and the measurement runs in the suite**: 100%
detection, 100% discrimination, 0 conversions against AT-18's 95%/95%/0. The
corpus found two real bugs the eyeball missed - normalisation strips the slash
("a/b test" arrives as "a b test"), and the negation window needed 5 words, not
3.

**Gates:** 468 server, 86 web, build green, 25/25 e2e.

### What is next, in priority order

- **P8-GOLDEN-005** - the analytical golden suite (AT-40/AT-01). This is what
  *measures* the workflow-completion rate; the causal corpus above can fold
  into it.
- **P8-SHELL-006** - the orientation spine (AT-33/34/35).
- **P8-REFINE-007** - question refinement (AT-04), editing the context object.

## Next action
**P8-SHELL-006 is DONE**: the shell answers "where am I, what am I doing, what
can help me" as a layout rather than as a sentence. The persistent rail carries
UX 7's four marks - `✓` complete, `⚠` requires attention, `●` the current
stage, `○` not started - derived the same way the core derives the stage, from
`progress.completed` and `progress.stage`, so the rail cannot disagree with the
core. The one judgement is the warning, and it is measured: the data stage's
`⚠` is the profiler's own quality defect (P8-QUALITY-002), never a guess.
Beside the rail sits the case overview (UX 45) - objective, question, "N / M
stages complete", key findings, open issues, data sources, validation counts -
each an artifact count the core already computed, with the objective reading
the context's purpose and the question as the fallback. The workspace splits
into three landmark zones (orientation / work / intelligence), a
rearrangement of panels that already existed: no panel was rewritten, and the
tests that pinned them were not edited to fit the layout - only the assertion
that a stage the loop is on was "pending" now reads "current", the rail's own
sharper vocabulary.

The three render gaps the walkthrough found are closed over endpoints that
already existed: a run's result rows and the query that produced them reopen
on demand (with the truncation notice when the result was capped); the plan's
own contents - sub-questions, hypotheses with their rationale and check,
steps, data requirements, the basis it was planned from - render instead of
being written and never read back; and every column's measured null count
shows at the Data stage. The two adjacent near-identical input boxes are
separated by the zones themselves. One limitation recorded rather than papered
over: the overview's labels are unstyled text, because splitting a label into
its own element breaks the text matching a test and a screen reader both read.

**Gates:** 477 server (unchanged - this task touched only the shell), 99 web
(13 new), build green, 25/25 e2e.

### What is next, in priority order

- **P8-REFINE-007** - question refinement (AT-04): AI proposes a refinement,
  the original is preserved verbatim beside it, and accept / edit /
  keep-original are the only three paths. It edits the context object
  P8-CONTEXT-001 built.
- **P8-DECISION-008** - the decision view (UX 46, AT-43): the loop's exit,
  reading the validated findings and their residual uncertainty.
- **P8-MEASURE-009** - the measurement layer (AT-27..30/32/37/38/45/46):
  coverage, perf, a11y, deps, the data-size envelope.

## Next action
**P8-REFINE-007 is DONE**: AT-04's four numbers exist, and the vague question -
the one thing carried verbatim into every plan, query and finding after it - is
now the one place the loop proposes a sharpening. Two engines behind one
interface, as in every other assistant: a deterministic refiner that *appends*
grounding the profiler measured (the measure, the split, the window, and the
comparison a word like "down" leaves unstated), and an LLM refiner gated before
the analyst sees it - original echoed verbatim, subject terms surviving, every
cited and quoted column real, every figure measured, a rationale present. The
refined question is the original plus clauses, never a replacement, so
preservation and relevance are structural; the 50-case suite measures them
anyway. Measured over 50 cases and 6 datasets against a real server: preserve
100%, relevant 100%, 0 silent overwrites, 0 fabrications.

The three paths are the only three: accept and edit are the sole writes to the
case's question, keep-original writes nothing but the no, and a decided
proposal is a 409. Recoverability is a property of the store, not the client -
the original rides on the proposal row, so it survives the accept that replaced
it, the export round trip and the duplicate, and it shows in the timeline as two
events. Schema v11 -> v12, one in-place migration. The shell panel (UX 12)
shows the transformation with both halves and the three buttons, in the
orientation zone.

**Gates:** 518 server (+41), 106 web (+7), build green, 25/25 e2e, AT-04's own
runner green (50 cases).

### What is next, in priority order

- **P8-DECISION-008** - the decision view (UX 46, AT-43): the loop's exit,
  reading the validated findings and their residual uncertainty - the failing
  checks, not a score.
- **P8-MEASURE-009** - the measurement layer (AT-27..30/32/37/38/45/46):
  coverage, perf, a11y, deps, the data-size envelope. Mechanical now that two
  measured suites exist to borrow the pattern from.
- **P8-TRACE-010** - the traceability matrix (AT-48); last, it traces what
  1-9 delivered.

## Next action
**P8-DECISION-008 is DONE**: the loop has an exit. A validated finding used to be
the last thing the product did with itself - the verdict was computed, shown and
discarded, only the status surviving on the finding, and nothing closing over
what the loop had established. Two changes fix that. The verdict is now kept
(all nine checks, not only the status), so a decision is read without re-running
a single query and a reopened case shows what validation found; and a decision
view assembles it - the question, the findings validation stood behind with
their caveats and the checks that did not pass (a sentence each, never a score,
per UX 44), the claims still open with the reason each is unresolved, and the
implications the analyst writes.

The implications are the view's only write and the one thing in it a human
authors - nothing proposes them and nothing derives them, because a tool that
drafts the action to take is a tool making the decision. A malformed entry is a
400 naming the first one to fix. The loop's closure is the core's own value,
read from `workflow.case_progress` rather than restated, so the decision cannot
say the loop is open while the rail says it is closed - the same
one-definition discipline the rail itself used against the stage derivation.
The decision travels: the export carries the verdicts and the implications, the
round trip restores both with fresh ids, the duplicate carries them, the delete
removes them, and the timeline gains two events (the validation itself, now
that it has a timestamp of its own - AT-44 names it among its minimum events -
and the decision). Schema v12 -> v13, two tables, one in-place migration.

The shell gained the panel and, with it, the case's export, which existed as an
endpoint and had no surface in the product at all - its natural home is the
decision it sits beside, per UX 48's flow ending at Decision Support -> Export.

**Gates:** 548 server (+30), 116 web (+10), build green, 28/28 e2e, the golden
suite still 21/21 on both thresholds, AT-04's four still holding.

### What is next, in priority order

- **P8-MEASURE-009** - the measurement layer (AT-27..30/32/37/38/45/46):
  coverage, perf, a11y, deps and the data-size envelope. Mechanical now that
  two measured suites exist to borrow the pattern from.
- **P8-TRACE-010** - the traceability matrix (AT-48); last, it traces what
  1-9 delivered.

## Next action
**All ten phases are complete and v0.3.2 is published.** P0 through P8 are
DONE; the last task (P8-TRACE-010) made the PRD's section 59 control artifact
code, and the three releases after it re-cut the app icon - v0.3.1 rounded the
full-bleed 60px-corner tile to the standard Ventura squircle, v0.3.2 scaled the
bar-chart artwork from 68% of the canvas to 52% and centred it. The tree is
green: 686 server, 138 web, 28/28 e2e, the measurement layer 9/9, the matrix
48/48.

There is no open task. What a next session inherits is the **open follow-up
list** in `ai/TASKS.md`, which is where to look first - it carries the
packaged-core version gap (`/updates/latest` answers `current: unknown`,
because the PyInstaller bundle sees neither the distribution metadata nor
`pyproject.toml`), the DMG bundling's dependence on a local `create-dmg` that
is not the bundler Tauri expects, the icon proportion still chosen blind
(52%; the source is the committed `icon.png`, and `ai/TASKS.md`'s carried
follow-ups carry the exact recipe to re-cut it), and the `web/src/CaseWorkspace.test.tsx` refinement describe that
still inherits the previous test's persistence.

**Gates:** 686 server, 138 web, build green, 28/28 e2e, golden 21/21, AT-04's
four thresholds, measurement 9/9, matrix 48/48. Two environmental notes carry:
CI's billing is suspended, so nothing since `c73118c` has run in CI and every
release artifact was built locally; and the Ventura floor is documented but no
longer CI-enforced (DEC-005).

### What is next, in priority order

- **Fix the packaged core's version** so `/updates/latest` can compare: carry
  the version into the PyInstaller bundle. It is the one open defect that
  touches a user-visible promise (the Check for Updates menu item), present
  since v0.2.0.
- **Restore CI** at GitHub Settings > Billing & plans, then re-run the suites
  against `v0.3.2`; nothing since `c73118c` has been verified by CI.
- **Then extension**, not before: the roadmap's scale ladder (cloud,
  collaboration, warehouse connectors, governance) is deferred at a user count
  of one, and the deliberately-not-built list in `docs/PRD & UX Conformance
  Evaluation.md` (the Analysis Canvas, the command palette, the Knowledge nav)
  is explicit deferral, not backlog - pick from it deliberately.

---

## Next action (walk-test, selesai 2026-09-25)

**WALK-E2E-001 — walk-test end-to-end sedang IN FLIGHT.** Tugas tambahan dari
user (tidak tercatat di sini saat mulai, sudah didaftarkan ke
`ai/TASKS.md`): siapkan satu case + dataset, jalankan app sungguh, evaluasi
flow, UI, UX untuk bahan perbaikan. Mode comprehensive, LLM nyata.

**Fase A (akses) + Fase B (case + data) SELESAI.** State mesin lengkap di
`walktest/HANDOFF.md` — session baru baca file itu pertama, lalu lanjut di
step "berikutnya" (sekarang: Fase C, plan + code generation). Jangan
menderivasi state dari memori; semua ada di `walktest/`.

Singkatnya: core master jalan via `.app` v0.3.2 + `DAH_DEV_CORE=1`, web dev
server `:5273`, dataset B2B 484 baris dengan 8 cacat ditanam (3 tertangkap
profiler), refinement deterministic di-accept. **10 temuan, 4 di antaranya
MAJOR:**

- **W-009** — "Why these changes" (refinement) kosong; API punya `rationale`
  + `grounds` lengkap tapi tidak dirender. Accept jadi black-box.
- **W-008** — profil dataset di-POST otomatis (2x) tiap halaman case dibuka;
  `profileDataset` di `api.ts:572` POST, dipanggil di `useEffect`
  (`CaseWorkspace.tsx:191`). "Stage: profile" jadi ambigu.
- **W-005** — menu "Check for Updates..." hanya `eprintln!` hasilnya
  (`main.rs:48-60`); repo privat selalu `unknown`, jadi item selalu diam.
- **W-001** — dev checkout melaporkan `current: 0.1.0` (metadata install
  stale `dah_server-0.1.0`), padahal pyproject `0.3.2`; `0.1.0` lebih buruk
  dari "unknown".

Positif yang teramati: guardrail AT-04 menolak jawaban LLM yang kehilangan
subjek pertanyaan Indonesia lalu fallback deterministic; Accept refinement
mempertahankan pertanyaan asli di UI + history; kualitas 3 temuan profiler
sangat baik (dampak terhitung, bukan sekadar "ada duplikat").

Sisa Fase C-F: plan + code gen + run SQL/Python + chart + finding + validate
+ decision; EVALUATE, agent & reviewer, LEARN, history/memory/template;
UX shell (error taxonomy, empty state); agregasi `walktest/REPORT.md`.

Ketika walk-test selesai, section ini kembali ke "tidak ada tugas terbuka"
dan hasilnya jadi post-phase fix (satu fix per temuan MAJOR, prioritas:
W-009, W-005, W-008, W-001).
---

## Next action (post-phase fixes, sebelum W-015 dikerjakan)

**Tidak ada tugas terbuka.** Walk-test end-to-end (WALK-E2E-001) SELESAI:
semua fase A-F dijalankan sungguh melawan core master + shell Tauri v0.3.2 +
bundle web yang sama di Chromium, dengan LLM nyata. Laporan akhir
`walktest/REPORT.md`; 19 temuan (8 MAJOR, 8 MINOR, 3 OBS) di
`walktest/FINDINGS.md`; state mesin live di `walktest/HANDOFF.md`.

Hasilnya jadi post-phase fix (satu commit per temuan, prioritas berurutan):

1. **W-015 MAJOR** — check evidence menolak finding yang benar. Regex
   `_numbers_in` (`server/app/evaluator.py`) `-?\d[\d,]*\.?\d*` memotong token
   "2026-07" menjadi `2026` dan `-7`; keduanya absen dari
   `_allowed_numbers`, jadi verdict `insufficient_evidence` pada HARD check.
   Setiap analisis time-series `YYYY-MM` gagal validasi. Diverifikasi
   langsung di interpreter. Perbaikan terlokalisir; `_allowed_numbers` (yang
   tidak memasukkan row_count / jumlah group yang statement sebut) perlu
   diperiksa bersamaan.
2. **W-011 MAJOR** — `PlanPanel` (`web/src/CaseWorkspace.tsx`) hanya GET
   plan; rail menunjuk "Generate an analysis plan" (`POST /plan`) tapi tidak
   ada satu pun elemen UI yang memanggilnya. Plan stage tidak bisa
   diselesaikan dari shell.
3. **W-016 MAJOR** — chart (`POST /runs/{id}/charts`) dan Python run
   (`POST /runs/python`) punya endpoint tapi `grep -c chart web/src/api.ts`
   = 0; dua kapabilitas inti tak terjangkau tanpa terminal.
4. **W-014 MAJOR** — interpret + draft-finding LLM selalu timeout 30s
   (`interpreter.py:239`, `drafter.py:312`) lalu fallback deterministic
   diam-diam; UI "Working…" 30s tanpa sinyal. Planner/refine (60s) sukses.

Sisa MAJOR: W-009 (rationale+grounds tak dirender), W-008 (profil di-POST
otomatis tiap buka case), W-005 (Check for Updates hanya eprintln), W-001
(dev checkout melaporkan 0.1.0).

Yang terbukti bekerja dengan baik (jangan rusak saat memperbaiki): guardrail
refinement AT-04, validasi 9 dimensi + carry-over uncertainty ke decision,
profiler dengan dampak terhitung, sandbox Python seatbelt, EVALUATE 9 axis,
agent approve/reject + reviewer, cross-case memory dengan grounds, error
taxonomy (400/404/422/500 — tidak ada jalan input-user ke 500), export 13
struktur + template round-trip.

### What is next, in priority order

- **Tag the release that ships it** (v0.3.3): the fix is on master, but no
  published binary carries it - v0.2.0 through v0.3.2 still answer "unknown",
  and that cannot be repaired without rebuilding. The release procedure is
  unchanged; the new smoke step does the verification.
- **Restore CI** at GitHub Settings > Billing & plans, then re-run the suites
  against the tag; nothing since `c73118c` has been verified by CI.
- **Then extension**, not before: the roadmap's scale ladder (cloud,
  collaboration, warehouse connectors, governance) is deferred at a user count
  of one, and the deliberately-not-built list in `docs/PRD & UX Conformance
  Evaluation.md` (the Analysis Canvas, the command palette, the Knowledge nav)
  is explicit deferral, not backlog - pick from it deliberately.

---

## Next action

**FIX-EVIDENCE-002 (W-015) DONE.** The evidence check no longer splits a
token and refuses the finding for quoting the fragments. `_numbers_in`
(`server/app/evaluator.py`) matched `-?\d[\d,]*\.?\d*`, which cut `2026-07`
into `2026` and `-7`; neither was in `_allowed_numbers`, so a correct
`YYYY-MM` finding answered `insufficient_evidence` on a HARD check and every
time-series analysis failed validation. The run is a regex that finds a digit
run and an accept step that reads the characters at both edges: a digit, a
letter or a hyphen against either side means the run is part of a longer
token, and the minus is only a sign when it starts one. `_allowed_numbers`
also gained the column's own length, the shape the deterministic drafter
names as "N grouped value(s)".

**Gates:** 699 server (+5 in test_validation.py), 138 web + build, golden
21/21, e2e all steps, refine AT-04, measure 9/9, trace 48/48.

A scope correction worth carrying: the first attempt wrote its own ad-hoc
shape suite and looped for ~40 iterations chasing five edge cases that were
never in the contract - European decimal commas, broken comma runs, sentence
dots, version strings, dotted ranges. Two of them are mutually inconsistent
and one (a bare year at a sentence end) is a magnitude the check *should*
extract, since it is a real cell value in a time-series result. The contract
is the boundary; when a regex's edge cases fight each other, the answer is to
stop widening the spec, not to keep tuning it.

**Next, in priority order:**

1. **FIX-TIMEOUT-006 (W-014)** — the interpret and draft LLM calls wait a
   hardcoded 30s, time out, and fall back to deterministic silently while the
   UI shows "Working…" for the whole thirty seconds. Contract already written
   in `ai/TASKS.md`; the five call sites are `interpreter.py:239`,
   `drafter.py:312`, `assistant.py:576` at 30.0 and `planner.py:366`,
   `refine.py:595` at 60.0. Server + the web panel that renders the source
   label. `test_llm_adapters.py` patches `httpx.post`, so a timeout is
   injected as a raised `httpx.ReadTimeout`, not waited for.
2. **Tag v0.3.3** once the two backend fixes are on master; nothing since
   `c73118c` has run in CI (billing suspended), so the smokes are local.
3. **Then P9, the UI/UX redesign** the user asked for, decided in this order:
   npm (CI hardcodes `npm ci`, Tauri's beforeDevCommand uses `npm --prefix`),
   light theme first, and recharts on screen because the server's chart SVG
   bakes a white background into the image (a white box on a light page) and
   is static - while its layout engine and PNG export stay for the export
   path. Four phases, green at each: F1 the foundation (tailwind, shadcn,
   framer-motion, recharts, splitting `CaseWorkspace.tsx`'s 2,501 lines into
   `web/src/panels/`), F2 the surfaces (which also closes W-011, W-016, W-013,
   W-009, W-017, W-018), F3 motion (respecting `prefers-reduced-motion`), F4
   the chart surface and a re-walk. A new DEC records the dependency change;
   the tests use role/text/label queries with zero `className` references, so
   a restyle does not break them.

---

## Next action

**FIX-UPDATES-009 (W-005) DONE.** The Check for Updates menu item is silent no
more. The handler asked the core and wrote the answer to stderr, so on this
private repository - where the feed always 404s - the item was permanently dead
while the core answered honestly. The delivery is added, not substituted: the
log line still writes, and the answer also reaches the window.

The shell owns the delivery because the shell is the only host with a menu bar,
and it delivers through the bundle's own surface - `tauri-plugin-dialog` is a
network-fetched plugin on Tauri 2 and the app is offline after install, so a
native dialog was not available without breaking DEC-001. `updates.rs` gained
`notice_script` (a `CustomEvent('dah-notice')` carrying the core's own JSON
body, so the window's vocabulary is the core's - an unreachable feed stays
"could not tell" rather than becoming the silent "up to date" P6-UPDATE-005
built the check to avoid) and `deliver_update_notice`, plus a
`check_for_update_with_body` that keeps the raw body beside the parsed answer.
`main.rs` logs first, then opens the release page for an `Available`, then
delivers. A body that is not JSON is re-serialised from the parsed answer,
because embedding it would throw a `SyntaxError` in the webview and silence the
item a second time - that case is a test. The bundle side is `web/src/shell.ts`
(`describeUpdate`, mirroring `update_summary`) and `web/src/NoticeLayer.tsx`,
mounted on all three screens, inert until a notice arrives, dismissable, and a
`role="status"` region. One include_str test pins the event name both sides
must agree on, which is the single thing a rename would silently break.

**Gates:** 723 server (unchanged), web 163 (+16), Rust 25 (+6), tsc clean,
build ok, e2e, golden 21/21, refine AT-04, trace 48/48.

**Next, in priority order:**

1. **FIX-VERSION-010 (W-001)** - a dev checkout answers `current: 0.1.0`
   because `server/app/updates.py` reads the stale installed metadata before
   the pyproject beside the source. FIX-VERSION-001's stamp stays first; the
   source moves ahead of the metadata. Contract in `ai/TASKS.md`.
2. **Then FIX-PLAN-003 / FIX-CHART-004 / FIX-PYTHON-005** - the rail names
   "Generate an analysis plan" and no control performs it; the chart and python
   run surfaces are the same class of gap.
3. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,501 lines into `web/src/panels/`), F2 the surfaces
   (closing W-011, W-016, W-013, W-017, W-018), F3 motion (respecting
   `prefers-reduced-motion`), F4 the chart surface and a re-walk.

---

## Next action

**FIX-VERSION-010 (W-001) DONE.** A dev checkout answered `current: 0.1.0` at
`/updates/latest` - four releases wrong, and a wrong number is believed where
an absent one is questioned. `current_version` read the editable install's
stale `dah_server-0.1.0.dist-info` before the pyproject beside the source the
checkout was actually running.

The order is now stamp > pyproject > metadata. The stamp stays first because
it was read from pyproject at build time (FIX-VERSION-001's packaged path is
unchanged, and a test now pins it against both other sources). The metadata is
demoted, not discarded: an installed wheel with no pyproject beside the source
still answers, which is the case the metadata was right for. A disagreement is
not papered over - when both answer and disagree the source wins and the two
numbers plus the reason land in the log at WARNING, so a stale install is
visible rather than silently believed. `_read_pyproject_version` and the new
`_installed_version` also treat `0.0.0` as "no answer", a placeholder a build
never replaced being no more a version in the source than in the metadata.
This checkout now answers `current: 0.3.3`.

**Gates:** 727 server (+4), web 163 (unchanged, server-only fix) green at the
second run, tsc clean, build ok, e2e 28/28, golden 21/21, refine AT-04,
measure 9/9, trace 48/48.

**W-001 closes, and with it the walk-test's last MAJOR finding:** all eight
WALK-E2E-001 majors (W-015, W-011 twice, W-014, W-009, W-008, W-005, W-001)
now have their fixes committed.

**Next, in priority order:**

1. **FIX-PLAN-003 (W-011)** - the rail names "Generate an analysis plan", the
   plan panel's empty state tells the analyst to generate one, and no control
   performs it; `POST .../plan` exists and answers 201 while
   `grep -rn "POST.*plan" web/src` is empty, so the stage is only finishable
   from a terminal. PlanPanel gains the control, `web/src/api.ts` a POST
   helper. Contract in `ai/TASKS.md`.
2. **FIX-CHART-004 / FIX-PYTHON-005 (W-016)** - the chart and the python run
   surfaces, the same class of gap; split because they share no code but the
   panel they land in.
3. **Then P9, the UI/UX redesign** the user asked for: npm (CI hardcodes
   `npm ci`), light theme first, recharts on screen because the server's chart
   SVG bakes a white background and is static, while its layout engine and PNG
   export stay for the export path. Four phases, green at each: F1 the
   foundation (tailwind, shadcn, framer-motion, recharts, splitting
   `CaseWorkspace.tsx`'s 2,501 lines into `web/src/panels/`), F2 the surfaces
   (closing W-011, W-016, W-013, W-017, W-018), F3 motion (respecting
   `prefers-reduced-motion`), F4 the chart surface and a re-walk.

## FIX-PLAN-003

**FIX-PLAN-003 (W-011) DONE.** The orientation rail names "Generate an analysis
plan" and nothing in the shell performed it. `PlanPanel` read a plan and, when
there was none, told the analyst to generate one - with no control that does;
`POST .../plan` existed and answered 201 while the shell never called it, so
the plan stage was only finishable from a terminal.

The empty state's own sentence now has the control that performs it. The
button POSTs the endpoint that owns the write, labels itself while the
planner works, and on success renders the plan in place and calls the
workspace's reload - so the rail's stage, the progress counts and the panel
move together, because the plan is what makes the rail's next action
legible. A refusal shows the endpoint's own reason as a sentence and the
offer stays; a case that has already planned shows its plan and offers
nothing.

One thing the first test run caught and fixed: the generation's error shared
the read's `error` state, and the empty state rendered that only in its
non-missing branch - so a 400 in the missing branch was swallowed and the
panel stayed silent, exactly the failure the fix exists to remove. The two
are separate states now (`generateError`), because they are never both live:
the control lives where the read answered 404, and a 404 is not the reason a
generation failed.

**Gates:** 727 server (unchanged), web 167 (+4), tsc clean, build ok,
e2e 28/28, trace 48/48.

## Next action

**P9-F1-001 (the redesign's foundation) DONE.** Three prerequisites landed
and nothing the analyst sees moved.

The toolchain: tailwindcss@4 through `@tailwindcss/vite` (CSS-first - one
`@import "tailwindcss"` in `index.css`, no postcss config, no
`tailwind.config.js`), framer-motion, recharts and the shadcn support deps,
with `package-lock.json` regenerated. **Nothing imports them yet**; a
dependency that ships unused is F1's debt and F2's capital.

The tokens: `web/src/lib/ui.tsx` holds the light theme the hand-written CSS
already used (#fafafa page, #fff panel, #ddd border, #666 muted, #1a4a7a
accent, and the three status pairs DAH renders as text-plus-chip, never
colour alone) plus the `Panel` / `Button` / `Card` primitives.

The split: `CaseWorkspace.tsx` fell from 2,889 lines to a 337-line
composition root, and its 15 panels moved into `web/src/panels/`, each under
the 600-line ceiling (RunsPanel the largest at 485).

The split is generated by `split_panels.py`, and the script now closes the
loop with the compiler: the heuristic import lists are a first guess, tsc
is the authority, and the script parses its own two import errors (TS6133
unused, TS2304 missing) and adjusts the lists per file until the compiler
is quiet. Four things the loop surfaced that the heuristic could not: a
duplicate span had defined `CaseOverview` twice; `formatValue` was
EdaPanel's TS2304 because no group owned it; AgentPanel's `Profile`/`Run`
read as unused because the heuristic stripped template literals as prose
(`` `Profile ${str('filename')}` `` is where the panel reaches the type);
and the panels test's own `[\s\S]*?` spec matched across a whole file. The
matrix's AT-30 row cited a `FindingRow.tsx` the split never made - it lives
in `FindingsPanel.tsx`, and `matrix.py:607` follows it.

**Gates:** web 181 (177 unchanged + 4 panels tests), tsc clean, build ok,
server 727, e2e 28/28, golden 21/21, refine AT-04, measure 9/9, trace 48/48.

**Two operational lessons.** `verify_measure.py` must run from the repo
root: its coverage module calls `pytest.main` with no path and inherits the
cwd, so a run from `verification/measure` collects the wrong suite and
AT-38 reads 22% instead of 94%. And the measurement and trace gates are
mutually dependent - `verify_measure` runs the server suite under a line
counter, so a red trace REPORT makes `test_trace.py` fail, which makes the
coverage suite exit non-zero, which turns AT-38 red, which is a failure
marker the trace matrix then cites. Regenerate the trace report first when
both are stale.

**Next, in priority order:**

1. **P9-F2, the surfaces.** The debt F1 took on is paid here: the panels
   restyle onto the tokens and primitives, one panel at a time, green at
   each. This also closes what remains of W-013, W-017, W-018. Then F3
   motion (respecting `prefers-reduced-motion`) and F4 the chart surface
   (recharts, which F1 installed and F2 still does not import), then a
   re-walk.

## Next action (P9-F2-002, archived when F3-001 landed)

**P9-F2-002 (the restyle onto the tokens) DONE.** The debt F1 and F2-001 took
on is paid: the token layer in `lib/ui.tsx` is the vocabulary every panel and
screen renders, and 109 lines of the hand-written CSS that named those
surfaces retired with them.

The panels swapped their literal `className="panel"` / `"subpanel"` /
`"proposal"` / `"run"` / `"turn"` / `"muted"` / `"row"` for the `surfaces`
string holding the same values as utility classes. The restyle is parity by
contract - a surface is the rule it replaced, so nothing looks different and
the palette is one set of names in one file. What stays in the CSS is what no
token can own: the three-zone grid, the sticky rail, the verdict and chip
shapes the status vocabulary renders as text-plus-chip, the quality and
notice surfaces, and the literal `:focus-visible` the accessibility audit
resolves.

One lesson the audit earned, and the reason this task's own test exists.
Deleting the retired rules was only safe once the rules were checked against
the source that used them, not against the list of rules the restyle
touched. Two literals survived the move and lost their rules:
`LearnPanel`'s `className="stage done"` (the rule is kept - a completed stage
is the one green status, and the word is the rail's and the ladder's shared
vocabulary) and `FindingsPanel`'s `className="muted"`, which moved to
`surfaces.note`. A panel that goes back to a literal now fails by name.

**Gates:** web 185 (184 + 1), tsc clean, build ok (the emitted CSS is
14.44 kB and still resolves the focus rule), trace 48/48. Web-only - no line
outside `web/` moved, so the server suite (727), e2e (28/28), golden (21/21),
refine (AT-04) and measure (9/9) are not re-run.

**Next, in priority order:**

1. **P9-F3, motion.** framer-motion@13 is installed and imported nowhere - the
   same debt shape F2 just paid, one phase earlier. The motion is the
   surfaces' own: a panel's content appearing as the case loads, a run row
   opening, a verdict landing. The constraint is `prefers-reduced-motion`,
   which the CSS already honours for the shell notice (`index.css`'s explicit
   `animation: none` rule); F3 makes the JS-driven motion honour it too
   rather than only the CSS-driven kind. A motion budget is the discipline: an
   animation that costs a frame the measurement layer (AT-27/AT-30) counts is
   a regression, not a polish.
2. **Then P9-F4, the chart surface and a re-walk.** recharts@3 is installed
   and unused. The on-screen chart is the server's SVG replaced by an
   interactive one - the server's layout engine and PNG export stay for the
   export path, because a chart that changes shape between the screen and the
   exported artifact is not evidence.

F2's two tasks are done: F2-001 the walk-test's last three findings, F2-002
the restyle. The walk-test's findings are all closed, and the redesign's
foundation is now the surface the analyst reads.

---

## Next action

**P9-F3-001 (the motion layer and its gate) DONE.** framer-motion@13 was
installed in F1 and imported nowhere - the same debt F2 paid for the tokens,
one phase earlier. The motion is paid too, and the gate that decides whether
any of it runs is the task's real subject.

`web/src/lib/motion.tsx` names three transitions - `surface` at 0.18s for
what a click opens, `enter` at 0.28s for what a case loads, `arrive` as a
spring for what a verdict does - and three variants to match, each a
`hidden` and a `shown` state with the transition riding inside the target.
The movement is 4-6px and never an element's own height, because layout
shift is the frame AT-27 counts; the verdict scales by 2% rather than
sliding, because the loop's exit is the one place weight reads.

The gate is `prefers-reduced-motion`, and the collapse is this layer's own
rather than the library's. framer-motion makes positional keys instant under
reduced motion but still fades opacity, so a reduced-motion setting that
still moves the surface is a setting the surface is not honouring:
`MotionSurface` reads `useReducedMotionConfig()` and sets `initial={false}`,
rendering the shown state with no animation at all - the same result the CSS
gives the shell notice. A second `prefers-reduced-motion` rule in
`index.css` holds a `[data-motion-surface]` at opacity 1, because a surface
that starts hidden and is never animated to shown - the engine absent, a
frame dropped on a slow machine - is invisible content, and that failure is
the one the JS gate cannot see itself out of.

The lesson the gate earned, and the reason the test reads the preference
from inside the provider: `useReducedMotion()` caches the OS preference in
`useState` at first read, so a probe that reads it outside `MotionConfig`
always answers the default. The preference is a context, not a global, and
the two are not interchangeable. jsdom has no `matchMedia` either, so a shim
in `setup-tests.ts` is what makes the gate behave in the suite the way it
behaves in a browser - stubbed per test and unstubbed after, so it does not
leak into the accessibility audit or the measurement layer.

**Gates:** web 197 (185 + 12), tsc clean, build ok (CSS 15.11 kB, JS 347 kB,
still resolving the focus rule), trace 48/48. Web-only - no line outside
`web/` moved, so the server suite (727), e2e (28/28), golden (21/21), refine
(AT-04) and measure (9/9) are not re-run.

**Next, in priority order:**

1. **P9-F4, the chart surface and a re-walk.** recharts@3 is installed and
   unused - the last of F1's three dependencies still at zero imports. The
   on-screen chart is the server's SVG replaced by an interactive one: a
   tooltip and a hover state are what the static SVG cannot give, and the
   evidence the chart is does not change with the renderer. The server's
   layout engine and its PNG export stay for the export path, because a
   chart that changes shape between the screen and the exported artifact is
   not evidence. The re-walk is the same kind of check the walk-test was:
   use the shipped shell, and record what the redesign changed for a reader
   who is not the one who built it.
2. **Then P9 closes.** Four phases, green at each: F1 the foundation, F2 the
   surfaces, F3 the motion, F4 the chart and the re-walk. Nothing after F4 is
   planned against the redesign itself; what follows it is whatever the
   re-walk finds.

F3's surfaces are the wrappers F2 already rendered - a run row, a verdict, a
chat answer, a case row, the three zones of the workspace - now a
`MotionSurface` carrying the same `className`. No markup was added and no
surface was restyled; the motion is the surface's own, not a second layer
over it.
