# P4 Production Candidate Verification

Run: 2026-09-19T15:59:52.454944+00:00

## Journey under test

```
attach a dataset larger than the result cap -> profile is exact at scale
-> a full scan is capped and flagged (never unbounded)
-> an aggregation still reads every row (the cap costs nothing)
-> bad SQL answers 400 with the engine's message, persists nothing
-> a write is refused -> a sandbox escape is refused
-> a harness fault answers 500 instead of blaming the analyst
-> a broken LLM degrades to deterministic, never blocks
-> the assistant drafts a finding and writes nothing
-> the human accepts -> validation agrees across reruns
-> the loop closes at scale -> the case reproduces elsewhere
```

P3 proved the loop is useful; this gate proves it is safe to hand to
someone else. The two properties that make it P4 rather than a P3 re-run
- the error taxonomy and rerun determinism - are invisible on the happy
path, and both are what 'production candidate' has to mean.

## Steps

| Step | Result | Detail |
|------|--------|--------|
| Create case | PASS | HTTP 201 |
| Attach a dataset larger than the result cap | PASS | HTTP 201, 5000 rows |
| Profile is correct at scale | PASS | rows=5000, distinct regions=5 |
| A full scan is capped and flagged | PASS | row_count=1000, truncated=True |
| An aggregation reads every row, not the capped page | PASS | rows=[[5000, 300000.0]] |
| Bad SQL answers 400 with the engine's message | PASS | HTTP 400, detail=Parser Error: syntax error at end of input |
| A write query is refused | PASS | HTTP 400 |
| A sandbox escape is refused and persists nothing | PASS | HTTP 400 |
| A harness fault answers 500, not 400 | PASS | HTTP 500 (a 400 here would blame the analyst for our own bug) |
| A broken LLM degrades instead of blocking | PASS | source=deterministic, sub_questions=4 |
| Run the unordered aggregation | PASS | row_count=5, totals={'east': 60000.0, 'north': 100000.0, 'south': 80000.0, 'west': 40000.0, 'central': 20000.0} |
| The assistant drafts a finding, writes nothing | PASS | source=deterministic, grounds=2 |
| Accept the draft as a finding | PASS | HTTP 201 |
| Validation is deterministic across reruns | PASS | verdicts={'supported'} (a flake would show more than one) |
| Render the chart the evidence stage needs | PASS | HTTP 201, image bytes=17021 |
| The loop closes at scale | PASS | stage=validated, loop_closed=True |
| The case reproduces elsewhere | PASS | totals={'east': 60000.0, 'south': 80000.0, 'west': 40000.0, 'central': 20000.0, 'north': 100000.0} |
| Test suite runs | PASS | 231 passed, 2 warnings in 72.80s (0:01:12) |

## Exit criteria (P4 gate: error semantics, determinism, scale,
the read-only and sandbox boundaries, graceful degradation)

| Criterion | Status |
|-----------|--------|
| Bad input is the input's fault, with a message and no side effects | PASS |
| A harness fault is never reported as the user's fault | PASS |
| Read-only and OS-sandbox boundaries hold and persist nothing | PASS |
| A failure of the LLM degrades rather than blocking | PASS |
| Results are bounded but aggregates stay exact | PASS |
| Profiling is correct at scale | PASS |
| The same finding validates the same way every time | PASS |
| The assistant proposes and never decides | PASS |
| The loop closes on a large dataset | PASS |
| A case moves elsewhere and reproduces | PASS |

## Decision

PASS. The harness behaves correctly at every edge a controlled external user can reach: bad input is answered with the engine's own message and leaves nothing behind, a fault in the harness is reported as the server's problem instead of the analyst's, an unavailable LLM degrades rather than blocking, results are capped without losing aggregates, and validating the same finding twice always agrees. P4 is done and the project is ready for the production-grade track (distribution, observability, signing).
