# P2 MVP Milestone Verification

Run: 2026-09-21T05:40:17.208363+00:00

## Journey under test

```
real question -> load data -> profile -> SQL -> Python -> chart -> AI plan
-> finding -> evidence -> validation -> rename/duplicate/delete
-> export -> import -> reproduce -> serve restored artifact
```

## Steps

| Step | Result | Detail |
|------|--------|--------|
| Create case with a real question | PASS | HTTP 201 |
| Load CSV | PASS | HTTP 201 |
| Profile data | PASS | rows=5, duplicate_rows=1 |
| Execute SQL analysis | PASS | row_count=2 |
| Execute Python analysis | PASS | columns=['region', 'total'] |
| Create chart from run result | PASS | HTTP 201 |
| Generate AI plan | PASS | source=deterministic, hypotheses=5 |
| Create finding | PASS | HTTP 201 |
| Trace evidence chain | PASS | finding -> run -> dataset verified |
| Validate finding | PASS | status=partially_supported, missing_data check fired |
| Rename case | PASS | HTTP 200 |
| Duplicate case | PASS | copy has 2 run(s), all with fresh IDs |
| Delete case | PASS | HTTP 204, then 404 |
| Export case package | PASS | sections=['agent_steps', 'case', 'charts', 'datasets', 'findings', 'plans', 'profiles', 'runs'] |
| Import package round trip | PASS | 2 run(s) restored with fresh IDs |
| Reproduce analysis on restored data | PASS | rows=[['north', 325.0], ['south', 161.0]] |
| Serve restored chart artifact | PASS | HTTP 200 |
| Test suite runs | PASS | 380 passed, 2 warnings in 144.42s (0:02:24) |

## Exit criteria (P2 gate: real problem, data, SQL/Python, visualization,
AI, evidence, validation, export, reproducibility)

| Criterion | Status |
|-----------|--------|
| A real analytical problem can be framed as a case | PASS |
| Supported data loads and profiles | PASS |
| Both engines analyse it (SQL and Python) | PASS |
| Analysis results are visualized and persisted | PASS |
| AI produces a structured plan | PASS |
| Findings carry a traceable evidence chain | PASS |
| Findings are validated, not assumed | PASS |
| Cases can be renamed, duplicated, and deleted | PASS |
| A case exports as a self-contained package | PASS |
| The package imports and reproduces elsewhere | PASS |

## Decision

PASS. The MVP loop is complete and reproducible end to end; P2 is done and the project is ready for the V1 hardening track (hard sandbox, raster charts, LLM key configuration, desktop shell).
