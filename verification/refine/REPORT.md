# AT-04 — AI Question Refinement, measured

Cases: **50** over 6 datasets, each driven through one of accept / edit / keep-original / left pending. The deterministic engine answered (no LLM was configured), so every number below is reproducible offline.

| Threshold | Required | Measured | |
|---|---|---|---|
| Preserve the original question | >= 95% | **100.0%** (50/50) | PASS |
| Semantically relevant refinement | >= 90% | **100.0%** (40/50) | PASS |
| Silent overwrites | 0 | **0** | PASS |
| Fabricated data references | 0 | **0** | PASS |

Proposals made: 40; declines: 10 (the already-specific, the topicless, the unprofiled and the column-less).

How relevance is measured, not judged: the refined question keeps every one of the original's subject terms (so it is the same question, sharpened) and names at least one real column from the profile (so it is sharpened by measured data). A decline the corpus expected counts as relevant, because leaving an already-answerable question alone is the correct behaviour; a decline it did not expect counts against it.

How preservation is measured: the proposal carries the original verbatim, and after every decision - including the accept that replaced it on the case row - the original is still readable from the case's refinement history.
