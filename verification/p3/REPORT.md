# P3 V1 Milestone Verification

Run: 2026-09-20T06:22:51.654762+00:00

## Journey under test

```
real question -> attach CSV + Parquet -> profile both
-> assistant proposes the query (writes nothing) -> plan
-> join run -> hard sandbox refuses an escape attempt
-> assistant reads the result and drafts a finding (writes nothing)
-> human accepts the finding -> raster chart -> validation closes the loop
-> evidence graph reaches both datasets -> workflow reports the loop closed
-> assistant answers with citations -> EDA without a query
-> history -> search -> template outlives the case
-> dataset deletion blocked by its own evidence
-> export -> import -> the join reproduces elsewhere
```

## Steps

| Step | Result | Detail |
|------|--------|--------|
| Create case with a real question | PASS | HTTP 201 |
| Attach CSV dataset | PASS | HTTP 201 |
| Attach Parquet dataset | PASS | HTTP 201 |
| Profile both datasets | PASS | profiled=2 of 2 |
| Assistant proposes query, writes nothing | PASS | source=deterministic, columns_used=['revenue', 'region'], runs_created=False |
| Generate analysis plan | PASS | source=deterministic, sub_questions=4 |
| Join two datasets in one run | PASS | row_count=3, datasets=2 |
| Hard sandbox blocks an escape attempt | PASS | HTTP 400, runs before=1 after=1 |
| Assistant reads the result | PASS | source=deterministic, observations=3 |
| Assistant drafts a finding, writes nothing | PASS | source=deterministic, grounds=2, findings=False |
| Accept the draft as a finding | PASS | HTTP 201 |
| Render raster chart from run result | PASS | HTTP 201, image bytes=15752 |
| Validate the finding closes the loop | PASS | status=supported, reproducibility passed |
| Evidence graph traces claim to both datasets | PASS | counts={'datasets': 2, 'runs': 1, 'charts': 1, 'plans': 1, 'findings': 1, 'edges': 5}, reached=['orders.csv', 'targets.parquet'] |
| Workflow reports the loop closed | PASS | stage=validated, loop_closed=True |
| Assistant answers with citations | PASS | source=deterministic, grounds=['dataset:orders.csv', 'dataset:targets.parquet', 'run:541ffa1a-b5b3-496d-9dde-59ef5730d499', 'finding:f9196011-21a1-424d-9f06-fdb02a6ee052', 'chart:7476b17f-e930-4d39-8db0-f8a89114fd7f'] |
| Explore data without a query | PASS | op=segment, row_count=3 |
| Replay the case history | PASS | events=9, ordered=True |
| Search finds the case | PASS | matches=1 |
| Template outlives its source case | PASS | templated=True, from_template HTTP 201, retired HTTP 204 |
| Dataset deletion blocked by its evidence | PASS | primary HTTP 400, join member HTTP 400 |
| Export package carries the join | PASS | sections=['case', 'charts', 'datasets', 'findings', 'plans', 'profiles', 'runs'] |
| Import reproduces the join elsewhere | PASS | rows=[['east', 60.0, 100.0], ['north', 325.0, 300.0], ['south', 170.5, 250.0]] |
| Test suite runs | PASS | 267 passed, 2 warnings in 142.37s (0:02:22) |

## Exit criteria (P3 gate: multi-dataset joins, hard sandbox, the four
assistant slices, raster charts, validation, evidence, workflow, reuse)

| Criterion | Status |
|-----------|--------|
| Several datasets attach to one case in different formats | PASS |
| One run can join them | PASS |
| Generated Python runs under an OS-level sandbox | PASS |
| A question yields the computation that would answer it | PASS |
| A result yields a plain-language reading | PASS |
| A result yields the candidate finding it supports | PASS |
| A case answers questions about itself with citations | PASS |
| Charts render as raster behind the same interface | PASS |
| A finding on a join run validates | PASS |
| Every claim traces to the data it stands on | PASS |
| The workflow stage is derived and the loop closes | PASS |
| EDA answers without a written query | PASS |
| A case can be found, replayed and templated | PASS |
| Evidence protects the data it stands on | PASS |
| A case moves elsewhere and reproduces | PASS |

## Decision

PASS. The V1 loop is complete for repeated real-world use: multi-dataset joins, a hard sandbox around generated code, an assistant that proposes at every step and decides at none, and a case that survives search, templating and a move to another harness. P3 is done and the project is ready for the production-candidate track (reliability, UX, performance, observability).
