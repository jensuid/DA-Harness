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

## Recent completions

The last tasks to land, newest first. The contract and done-record for each
is in `ai/TASKS.md` (rolling window) or `ai/TASKS-ARCHIVE.md`.

- **FIX-EVIDENCE-002** - the evidence check's number regex (W-015); a
  `YYYY-MM` finding validates, a date/id/sku is not a magnitude, and a
  fabricated figure still fails and is named.
- **FIX-VERSION-001** - the packaged core reports its own version; the spec
  stamps it from pyproject, `current_version` reads it first, and both
  packaged-core smokes assert it.
- **WALK-E2E-001** - the walk-test end-to-end; 19 findings (8 MAJOR), the
  report that prioritises them, and the list of what works that the fixes
  must not break.

Contracts for the rolling window (the two most recent). Older blocks are in
`ai/TASKS-ARCHIVE.md`.
