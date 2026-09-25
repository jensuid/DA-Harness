# The measurement layer (P8-MEASURE-009)

One measured number per acceptance test, each against a real core or the
real suite - never the engine's own claim about itself. AT-01, AT-04 and
AT-40 are measured by their own runners: verification/golden/REPORT.md
and verification/refine/REPORT.md.

## AT-38                  PASS

- measured: core 93.9% (8179/8707 lines), analytical 93.1%, evidence 92.4%
- target: >= 80% core, >= 90% analytical and evidence

## AT-37                  PASS

- measured: 0 critical, 0 high (22/22 packages scanned)
- target: 0 critical, 0 high without a documented risk acceptance

## AT-28                  PASS

- measured: p95 149ms over 20 samples
- target: p95 <= 2000ms

## AT-29                  PASS

- measured: p95 1066ms over 10 samples
- target: p95 <= 5000ms

## AT-46                  PASS

- measured: 100 runs, 200 findings, 1200 evidence edges, 9/9 surfaces answered in budget
- target: the envelope (100/200/1000) holds and every surface answers

## AT-45                  PASS

- measured: declared ok, enforced ok
- target: the PRD's numbers, refused beyond

## AT-45                  PASS

- measured: the PRD's numbers: 5,000,000 rows and 100 columns for CSV/Parquet, 500,000 for Excel
- target: declared explicitly rather than claiming unlimited scale

## AT-45                  PASS

- measured: too wide refused (the dataset has 101 columns and the supported envelope allows 100; reduce the width or export a subset (GET /envelope publishes the limits)), too tall refused (the dataset has 4 rows and the supported CSV/Parquet envelope allows 3; reduce the size or export a subset (GET /envelope publishes the limits))
- target: a 400 naming the limit it broke, before any profile runs

## AT-27 / AT-30 / AT-32  PASS

- measured: the web suite is green (Tests  143 passed (143))
- target: p95 <= 200ms, every long-running operation shows its state, 0 critical accessibility violations

---

**PASS** - 9/9 measurements hold; measured in 367s.
