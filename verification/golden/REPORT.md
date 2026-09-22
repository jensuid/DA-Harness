# Golden Suite Report (P8-GOLDEN-005)

Measured against a real server over HTTP, isolated to a temporary data
dir, with the LLM variables empty so the deterministic engines answer.
Every expectation was verified two ways - hand-computed and
independently recomputed from the fixture - before the engine ran.

## The two numbers

- **AT-40 reference calculations:** 21/21 match within a stated tolerance (**100.0%**, threshold 100%)
- **AT-01 workflow completion:** 21/21 scripted runs complete the full loop (**100.0%**, threshold 95%)
- **Datasets:** 3 (minimum 3); runs: 21 (minimum 20)

## Coverage of AT-40's ten shapes

| Shape | Checks | All match |
|-------|--------|-----------|
| aggregation | 2 | yes |
| filtering | 3 | yes |
| joins | 1 | yes |
| missingness | 2 | yes |
| duplicates | 1 | yes |
| dates | 3 | yes |
| percentages | 3 | yes |
| segmentation | 2 | yes |
| statistical_calculations | 3 | yes |
| validation | 1 | yes |

## Runs

| Check | Dataset | Shape | Reference | Workflow | Verdict |
|-------|---------|-------|-----------|----------|---------|
| sales-aggregation-quarter | sales.csv | aggregation | match | complete | partially_supported |
| sales-filtering-region | sales.csv | filtering | match | complete | insufficient_evidence |
| sales-missingness-revenue | sales.csv | missingness | match | complete | partially_supported |
| sales-duplicates-orders | sales.csv | duplicates | match | complete | partially_supported |
| sales-dates-trend | sales.csv | dates | match | complete | partially_supported |
| sales-percentages-region | sales.csv | percentages | match | complete | partially_supported |
| sales-segmentation-region-quarter | sales.csv | segmentation | match | complete | partially_supported |
| sales-statistics-revenue | sales.csv | statistical_calculations | match | complete | partially_supported |
| spend-statistics-correlation | spend.csv | statistical_calculations | match | complete | partially_supported |
| spend-filtering-high-spend | spend.csv | filtering | match | complete | insufficient_evidence |
| spend-dates-weekly-delta | spend.csv | dates | match | complete | partially_supported |
| spend-joins-channel-average | spend.csv | joins | match | complete | supported |
| spend-percentages-signups | spend.csv | percentages | match | complete | partially_supported |
| tickets-aggregation-category | tickets.csv | aggregation | match | complete | partially_supported |
| tickets-statistics-category | tickets.csv | statistical_calculations | match | complete | partially_supported |
| tickets-percentages-priority | tickets.csv | percentages | match | complete | partially_supported |
| tickets-dates-opened | tickets.csv | dates | match | complete | partially_supported |
| tickets-missingness-resolution | tickets.csv | missingness | match | complete | partially_supported |
| tickets-segmentation-priority | tickets.csv | segmentation | match | complete | partially_supported |
| tickets-validation-average | tickets.csv | validation | match | complete | partially_supported |
| tickets-filtering-bug | tickets.csv | filtering | match | complete | insufficient_evidence |

No failures.

