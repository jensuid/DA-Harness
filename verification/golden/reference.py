"""The golden reference values for the analytical suite (P8-GOLDEN-005).

AT-40 names ten analytical shapes a product like this must compute correctly -
aggregation, filtering, joins, missingness, duplicates, dates, percentages,
segmentation, statistical calculations and validation - and requires 100% of
deterministic reference calculations to match expected results. This module
holds those expectations as data, and the independent path that recomputes
them.

The discipline that makes this worth anything: **a golden value is never the
engine's own output recorded as truth.** Every expectation below was computed
by hand from the fixture's own numbers, and `recompute` derives it again by a
second implementation - plain Python over the parsed CSV, with `statistics`
for the moments and `Decimal` ROUND_HALF_UP where SQL rounds. The suite asserts
the two agree, which pins the *fixture*, not the engine; if hand and
independent paths disagree, the fixture is wrong and the suite fails before a
single query runs.

Then, and only then, does the runner ask the engine the same question and
compare. Two numbers come out, both asserted in test_golden.py:

    - reference calculations matching, 100% within a stated tolerance (AT-40)
    - scripted workflow attempts completing the full loop, >= 95% over
      >= 20 runs and >= 3 datasets (AT-01)
"""

from __future__ import annotations

import csv
import statistics
from dataclasses import dataclass, field
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from typing import Callable

DATASETS_DIR = Path(__file__).parent / "datasets"

# The ten shapes AT-40 names, spelt exactly once so a misspelling in a check is
# a test failure rather than a silently-uncovered shape.
AT40_SHAPES = (
    "aggregation",
    "filtering",
    "joins",
    "missingness",
    "duplicates",
    "dates",
    "percentages",
    "segmentation",
    "statistical_calculations",
    "validation",
)

DATASETS = ("sales.csv", "spend.csv", "tickets.csv")


@dataclass(frozen=True)
class GoldenCheck:
    """One reference calculation over one fixture.

    `expected` is the hand-computed answer; `recompute` derives the same answer
    a second way. The runner never reads `expected` until the two agree.
    """

    check_id: str
    dataset: str
    shape: str
    question: str
    sql: str
    columns: list[str]
    expected: list[list]
    tolerance: float = 1e-9
    # The independent path, keyed by check_id in RECOMPUTE so the dataclass
    # stays plain data a report can serialise.
    recompute_key: str = ""


def load_rows(filename: str) -> list[dict[str, str]]:
    """A fixture as rows of strings, the way an analyst's CSV arrives."""
    with (DATASETS_DIR / filename).open(encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def _num(text: str | None) -> float | None:
    """A cell as a number, with an empty or absent cell as None (SQL's NULL)."""
    if text is None or text == "":
        return None
    return float(text)


def _round2(value: float) -> float:
    """Half-up rounding to two places, matching SQL's ROUND rather than the
    banker's rounding Python's built-in does on an exact .xx5 boundary."""
    return float(Decimal(repr(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


# --- the checks ------------------------------------------------------------
# Every figure below is computed by hand from the fixture. The sales fixture
# carries a duplicate row on purpose: a SUM over it counts the duplicate, so
# 2024q2's revenue is 18100 (4200 + 3100 + 5400 + the repeated 5400), not 12700.
# That is the honest answer the SQL gives over the data as it stands, and
# exactly the kind of thing a golden suite exists to pin.

CHECKS: tuple[GoldenCheck, ...] = (
    # ---- sales.csv: revenue by quarter, region and product -----------
    GoldenCheck(
        check_id="sales-aggregation-quarter",
        dataset="sales.csv",
        shape="aggregation",
        question="What is total revenue by quarter?",
        sql=(
            "SELECT quarter, SUM(revenue) AS revenue "
            "FROM read_csv_auto(?) GROUP BY quarter ORDER BY quarter"
        ),
        columns=["quarter", "revenue"],
        expected=[["2024q2", 18100.0], ["2024q3", 11300.0]],
        recompute_key="sales-aggregation-quarter",
    ),
    GoldenCheck(
        check_id="sales-filtering-region",
        dataset="sales.csv",
        shape="filtering",
        question="How is Q3 revenue split across regions?",
        sql=(
            "SELECT region, SUM(revenue) AS revenue FROM read_csv_auto(?) "
            "WHERE quarter = '2024q3' GROUP BY region ORDER BY region"
        ),
        columns=["region", "revenue"],
        expected=[
            ["east", 1900.0],
            ["north", 3800.0],
            ["south", 2900.0],
            ["west", 2700.0],
        ],
        recompute_key="sales-filtering-region",
    ),
    GoldenCheck(
        check_id="sales-missingness-revenue",
        dataset="sales.csv",
        shape="missingness",
        question="How much revenue data is missing?",
        sql=(
            "SELECT COUNT(*) AS rows, COUNT(revenue) AS with_revenue, "
            "COUNT(*) - COUNT(revenue) AS nulls FROM read_csv_auto(?)"
        ),
        columns=["rows", "with_revenue", "nulls"],
        expected=[[9, 8, 1]],
        tolerance=0.0,
        recompute_key="sales-missingness-revenue",
    ),
    GoldenCheck(
        check_id="sales-duplicates-orders",
        dataset="sales.csv",
        shape="duplicates",
        question="Which orders appear more than once?",
        sql=(
            "SELECT order_id, COUNT(*) AS occurrences FROM read_csv_auto(?) "
            "GROUP BY order_id HAVING COUNT(*) > 1 ORDER BY order_id"
        ),
        columns=["order_id", "occurrences"],
        expected=[[103, 2]],
        tolerance=0.0,
        recompute_key="sales-duplicates-orders",
    ),
    GoldenCheck(
        check_id="sales-dates-trend",
        dataset="sales.csv",
        shape="dates",
        question="How did revenue change quarter over quarter?",
        sql=(
            "SELECT quarter, SUM(revenue) AS revenue, "
            "LAG(SUM(revenue)) OVER (ORDER BY quarter) AS previous_quarter "
            "FROM read_csv_auto(?) GROUP BY quarter ORDER BY quarter"
        ),
        columns=["quarter", "revenue", "previous_quarter"],
        expected=[
            ["2024q2", 18100.0, None],
            ["2024q3", 11300.0, 18100.0],
        ],
        recompute_key="sales-dates-trend",
    ),
    GoldenCheck(
        check_id="sales-percentages-region",
        dataset="sales.csv",
        shape="percentages",
        question="What share of total revenue does each region hold?",
        sql=(
            "SELECT region, ROUND(100.0 * SUM(revenue) / "
            "(SELECT SUM(revenue) FROM read_csv_auto(?)), 2) AS pct "
            "FROM read_csv_auto(?) GROUP BY region ORDER BY region"
        ),
        columns=["region", "pct"],
        expected=[
            ["east", 6.46],
            ["north", 27.21],
            ["south", 20.41],
            ["west", 45.92],
        ],
        recompute_key="sales-percentages-region",
    ),
    GoldenCheck(
        check_id="sales-segmentation-region-quarter",
        dataset="sales.csv",
        shape="segmentation",
        question="How do units break down by region and quarter?",
        sql=(
            "SELECT region, quarter, SUM(units) AS units FROM read_csv_auto(?) "
            "GROUP BY region, quarter ORDER BY region, quarter"
        ),
        columns=["region", "quarter", "units"],
        expected=[
            ["east", "2024q3", 7],
            ["north", "2024q2", 14],
            ["north", "2024q3", 12],
            ["south", "2024q2", 10],
            ["south", "2024q3", 9],
            ["west", "2024q2", 36],
            ["west", "2024q3", 15],
        ],
        tolerance=0.0,
        recompute_key="sales-segmentation-region-quarter",
    ),
    GoldenCheck(
        check_id="sales-statistics-revenue",
        dataset="sales.csv",
        shape="statistical_calculations",
        question="What is the spread of revenue per order?",
        sql=(
            "SELECT MIN(revenue) AS min_revenue, MAX(revenue) AS max_revenue, "
            "AVG(revenue) AS avg_revenue FROM read_csv_auto(?)"
        ),
        columns=["min_revenue", "max_revenue", "avg_revenue"],
        expected=[[1900.0, 5400.0, 3675.0]],
        recompute_key="sales-statistics-revenue",
    ),
    # ---- spend.csv: weekly spend against signups, by channel ---------
    GoldenCheck(
        check_id="spend-statistics-correlation",
        dataset="spend.csv",
        shape="statistical_calculations",
        question="Does weekly spend move with signups?",
        sql="SELECT corr(spend, signups) AS correlation FROM read_csv_auto(?)",
        columns=["correlation"],
        # Hand-computed Pearson r over the eight weeks; the two implementations
        # agree to the last digit they share, so the tolerance is generous
        # rather than the value being rounded.
        expected=[[0.9982317253838763]],
        tolerance=1e-9,
        recompute_key="spend-statistics-correlation",
    ),
    GoldenCheck(
        check_id="spend-filtering-high-spend",
        dataset="spend.csv",
        shape="filtering",
        question="Which channels get signups in the high-spend weeks?",
        sql=(
            "SELECT channel, COUNT(*) AS weeks, AVG(signups) AS avg_signups "
            "FROM read_csv_auto(?) WHERE spend >= 150 GROUP BY channel "
            "ORDER BY channel"
        ),
        columns=["channel", "weeks", "avg_signups"],
        expected=[["organic", 1, 64.0], ["paid", 4, 74.5]],
        recompute_key="spend-filtering-high-spend",
    ),
    GoldenCheck(
        check_id="spend-dates-weekly-delta",
        dataset="spend.csv",
        shape="dates",
        question="How does week-over-week spend change?",
        sql=(
            "SELECT week, spend - LAG(spend) OVER (ORDER BY week) AS delta "
            "FROM read_csv_auto(?) ORDER BY week"
        ),
        columns=["week", "delta"],
        expected=[
            ["2024w01", None],
            ["2024w02", 50.0],
            ["2024w03", -30.0],
            ["2024w04", 80.0],
            ["2024w05", -20.0],
            ["2024w06", -90.0],
            ["2024w07", 120.0],
            ["2024w08", -50.0],
        ],
        recompute_key="spend-dates-weekly-delta",
    ),
    GoldenCheck(
        check_id="spend-joins-channel-average",
        dataset="spend.csv",
        shape="joins",
        question="How does each week's spend compare with its channel's average?",
        sql=(
            "SELECT a.week, a.spend, b.channel_avg FROM read_csv_auto(?) a "
            "JOIN (SELECT channel, AVG(spend) AS channel_avg FROM read_csv_auto(?) "
            "GROUP BY channel) b ON a.channel = b.channel ORDER BY a.week"
        ),
        columns=["week", "spend", "channel_avg"],
        expected=[
            ["2024w01", 100.0, 160.0],
            ["2024w02", 150.0, 160.0],
            ["2024w03", 120.0, 160.0],
            ["2024w04", 200.0, 160.0],
            ["2024w05", 180.0, 160.0],
            ["2024w06", 90.0, 125.0],
            ["2024w07", 210.0, 160.0],
            ["2024w08", 160.0, 125.0],
        ],
        recompute_key="spend-joins-channel-average",
    ),
    GoldenCheck(
        check_id="spend-percentages-signups",
        dataset="spend.csv",
        shape="percentages",
        question="What share of signups does each channel bring?",
        sql=(
            "SELECT channel, ROUND(100.0 * SUM(signups) / "
            "(SELECT SUM(signups) FROM read_csv_auto(?)), 2) AS pct "
            "FROM read_csv_auto(?) GROUP BY channel ORDER BY channel"
        ),
        columns=["channel", "pct"],
        expected=[["organic", 20.12], ["paid", 79.88]],
        recompute_key="spend-percentages-signups",
    ),
    # ---- tickets.csv: support tickets, resolution and priority -------
    GoldenCheck(
        check_id="tickets-aggregation-category",
        dataset="tickets.csv",
        shape="aggregation",
        question="How are tickets distributed across categories?",
        sql=(
            "SELECT category, COUNT(*) AS tickets FROM read_csv_auto(?) "
            "GROUP BY category ORDER BY category"
        ),
        columns=["category", "tickets"],
        expected=[["billing", 3], ["bug", 4], ["support", 3]],
        tolerance=0.0,
        recompute_key="tickets-aggregation-category",
    ),
    GoldenCheck(
        check_id="tickets-statistics-category",
        dataset="tickets.csv",
        shape="statistical_calculations",
        question="How does resolution time vary by category?",
        sql=(
            "SELECT category, MIN(resolved_hours) AS min_hours, "
            "MAX(resolved_hours) AS max_hours, AVG(resolved_hours) AS avg_hours "
            "FROM read_csv_auto(?) GROUP BY category ORDER BY category"
        ),
        columns=["category", "min_hours", "max_hours", "avg_hours"],
        expected=[
            ["billing", 2.0, 26.0, 10.833333333333334],
            ["bug", 3.0, 72.0, 29.0],
            ["support", 1.5, 49.5, 19.666666666666668],
        ],
        recompute_key="tickets-statistics-category",
    ),
    GoldenCheck(
        check_id="tickets-percentages-priority",
        dataset="tickets.csv",
        shape="percentages",
        question="What share of tickets sits in each priority?",
        sql=(
            "SELECT priority, ROUND(100.0 * COUNT(*) / "
            "(SELECT COUNT(*) FROM read_csv_auto(?)), 2) AS pct "
            "FROM read_csv_auto(?) GROUP BY priority ORDER BY priority"
        ),
        columns=["priority", "pct"],
        expected=[["high", 30.0], ["low", 50.0], ["medium", 20.0]],
        recompute_key="tickets-percentages-priority",
    ),
    GoldenCheck(
        check_id="tickets-dates-opened",
        dataset="tickets.csv",
        shape="dates",
        question="How many tickets opened each day?",
        sql=(
            "SELECT opened, COUNT(*) AS tickets FROM read_csv_auto(?) "
            "GROUP BY opened ORDER BY opened"
        ),
        columns=["opened", "tickets"],
        expected=[
            ["2024-06-01", 2],
            ["2024-06-02", 2],
            ["2024-06-03", 1],
            ["2024-06-04", 1],
            ["2024-06-05", 1],
            ["2024-06-06", 1],
            ["2024-06-07", 1],
            ["2024-06-08", 1],
        ],
        tolerance=0.0,
        recompute_key="tickets-dates-opened",
    ),
    GoldenCheck(
        check_id="tickets-missingness-resolution",
        dataset="tickets.csv",
        shape="missingness",
        question="How many tickets lack a resolution time?",
        sql=(
            "SELECT COUNT(*) AS rows, COUNT(resolved_hours) AS resolved, "
            "COUNT(*) - COUNT(resolved_hours) AS unresolved FROM read_csv_auto(?)"
        ),
        columns=["rows", "resolved", "unresolved"],
        expected=[[10, 9, 1]],
        tolerance=0.0,
        recompute_key="tickets-missingness-resolution",
    ),
    GoldenCheck(
        check_id="tickets-segmentation-priority",
        dataset="tickets.csv",
        shape="segmentation",
        question="How does resolution time differ by priority?",
        sql=(
            "SELECT priority, AVG(resolved_hours) AS avg_hours "
            "FROM read_csv_auto(?) GROUP BY priority ORDER BY priority"
        ),
        columns=["priority", "avg_hours"],
        expected=[
            ["high", 49.166666666666664],
            ["low", 2.75],
            ["medium", 10.0],
        ],
        recompute_key="tickets-segmentation-priority",
    ),
    GoldenCheck(
        check_id="tickets-validation-average",
        dataset="tickets.csv",
        shape="validation",
        question="What is the average resolution time across resolved tickets?",
        sql=(
            "SELECT COUNT(*) AS tickets, AVG(resolved_hours) AS avg_hours "
            "FROM read_csv_auto(?)"
        ),
        columns=["tickets", "avg_hours"],
        # The value the product's own validation must reproduce: a finding
        # quoting these figures has to be recomputed, not trusted.
        expected=[[10, 19.833333333333332]],
        recompute_key="tickets-validation-average",
    ),
    GoldenCheck(
        check_id="tickets-filtering-bug",
        dataset="tickets.csv",
        shape="filtering",
        question="How much resolution time do bugs take, by priority?",
        sql=(
            "SELECT priority, SUM(resolved_hours) AS total_hours "
            "FROM read_csv_auto(?) WHERE category = 'bug' GROUP BY priority "
            "ORDER BY priority"
        ),
        columns=["priority", "total_hours"],
        expected=[["high", 72.0], ["low", 3.0], ["medium", 12.0]],
        recompute_key="tickets-filtering-bug",
    ),
)


def _sum_by(rows: list[dict[str, str]], key: str, measure: str) -> dict[str, float]:
    """SUM(measure) GROUP BY key, SQL's null-skipping included."""
    out: dict[str, float] = {}
    for row in rows:
        value = _num(row.get(measure))
        if value is None:
            continue
        out[row[key]] = out.get(row[key], 0.0) + value
    return out


def _recompute_sales(check_id: str) -> list[list]:
    rows = load_rows("sales.csv")
    if check_id == "sales-aggregation-quarter":
        totals = _sum_by(rows, "quarter", "revenue")
        return [[quarter, totals[quarter]] for quarter in sorted(totals)]
    if check_id == "sales-filtering-region":
        q3 = [r for r in rows if r["quarter"] == "2024q3"]
        totals = _sum_by(q3, "region", "revenue")
        return [[region, totals[region]] for region in sorted(totals)]
    if check_id == "sales-missingness-revenue":
        count = len(rows)
        present = sum(1 for r in rows if _num(r.get("revenue")) is not None)
        return [[count, present, count - present]]
    if check_id == "sales-duplicates-orders":
        seen: dict[str, int] = {}
        for row in rows:
            seen[row["order_id"]] = seen.get(row["order_id"], 0) + 1
        return [[int(k), v] for k, v in sorted(seen.items()) if v > 1]
    if check_id == "sales-dates-trend":
        totals = _sum_by(rows, "quarter", "revenue")
        quarters = sorted(totals)
        out = []
        for index, quarter in enumerate(quarters):
            previous = totals[quarters[index - 1]] if index else None
            out.append([quarter, totals[quarter], previous])
        return out
    if check_id == "sales-percentages-region":
        totals = _sum_by(rows, "region", "revenue")
        grand = sum(totals.values())
        return [[r, _round2(100.0 * totals[r] / grand)] for r in sorted(totals)]
    if check_id == "sales-segmentation-region-quarter":
        totals: dict[tuple[str, str], float] = {}
        for row in rows:
            key = (row["region"], row["quarter"])
            totals[key] = totals.get(key, 0) + float(row["units"])
        return [
            [region, quarter, totals[(region, quarter)]]
            for region, quarter in sorted(totals)
        ]
    if check_id == "sales-statistics-revenue":
        values = [v for v in (_num(r.get("revenue")) for r in rows) if v is not None]
        return [[min(values), max(values), sum(values) / len(values)]]
    raise KeyError(check_id)


def _recompute_spend(check_id: str) -> list[list]:
    rows = load_rows("spend.csv")
    if check_id == "spend-statistics-correlation":
        spend = [float(r["spend"]) for r in rows]
        signups = [float(r["signups"]) for r in rows]
        return [[statistics.correlation(spend, signups)]]
    if check_id == "spend-filtering-high-spend":
        high = [r for r in rows if float(r["spend"]) >= 150]
        by_channel: dict[str, list[float]] = {}
        for row in high:
            by_channel.setdefault(row["channel"], []).append(float(row["signups"]))
        return [
            [channel, len(values), sum(values) / len(values)]
            for channel, values in sorted(by_channel.items())
        ]
    if check_id == "spend-dates-weekly-delta":
        ordered = sorted(rows, key=lambda r: r["week"])
        spend = [float(r["spend"]) for r in ordered]
        out = [[row["week"], None] for row in ordered]
        for index in range(1, len(ordered)):
            out[index][1] = spend[index] - spend[index - 1]
        return out
    if check_id == "spend-joins-channel-average":
        averages: dict[str, float] = {}
        for row in rows:
            averages.setdefault(row["channel"], []).append(float(row["spend"]))
        means = {c: sum(v) / len(v) for c, v in averages.items()}
        return [
            [row["week"], float(row["spend"]), means[row["channel"]]]
            for row in sorted(rows, key=lambda r: r["week"])
        ]
    if check_id == "spend-percentages-signups":
        by_channel = {}
        for row in rows:
            by_channel.setdefault(row["channel"], []).append(float(row["signups"]))
        grand = sum(sum(v) for v in by_channel.values())
        return [
            [channel, _round2(100.0 * sum(values) / grand)]
            for channel, values in sorted(by_channel.items())
        ]
    raise KeyError(check_id)


def _recompute_tickets(check_id: str) -> list[list]:
    rows = load_rows("tickets.csv")
    if check_id == "tickets-aggregation-category":
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["category"]] = counts.get(row["category"], 0) + 1
        return [[c, counts[c]] for c in sorted(counts)]
    if check_id == "tickets-statistics-category":
        groups: dict[str, list[float]] = {}
        for row in rows:
            value = _num(row.get("resolved_hours"))
            if value is not None:
                groups.setdefault(row["category"], []).append(value)
        return [
            [c, min(v), max(v), sum(v) / len(v)]
            for c, v in sorted(groups.items())
        ]
    if check_id == "tickets-percentages-priority":
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["priority"]] = counts.get(row["priority"], 0) + 1
        total = len(rows)
        return [[p, _round2(100.0 * counts[p] / total)] for p in sorted(counts)]
    if check_id == "tickets-dates-opened":
        counts: dict[str, int] = {}
        for row in rows:
            counts[row["opened"]] = counts.get(row["opened"], 0) + 1
        return [[d, counts[d]] for d in sorted(counts)]
    if check_id == "tickets-missingness-resolution":
        count = len(rows)
        resolved = sum(1 for r in rows if _num(r.get("resolved_hours")) is not None)
        return [[count, resolved, count - resolved]]
    if check_id == "tickets-segmentation-priority":
        groups: dict[str, list[float]] = {}
        for row in rows:
            value = _num(row.get("resolved_hours"))
            if value is not None:
                groups.setdefault(row["priority"], []).append(value)
        return [[p, sum(v) / len(v)] for p, v in sorted(groups.items())]
    if check_id == "tickets-validation-average":
        values = [v for v in (_num(r.get("resolved_hours")) for r in rows) if v is not None]
        return [[len(rows), sum(values) / len(values)]]
    if check_id == "tickets-filtering-bug":
        groups: dict[str, float] = {}
        for row in rows:
            if row["category"] != "bug":
                continue
            value = _num(row.get("resolved_hours"))
            if value is not None:
                groups[row["priority"]] = groups.get(row["priority"], 0.0) + value
        return [[p, groups[p]] for p in sorted(groups)]
    raise KeyError(check_id)


def recompute(check: GoldenCheck) -> list[list]:
    """The same expectation derived a second way, never by the engine.

    This is the fixture's own audit: hand-computed against independently
    implemented, both from the CSV and neither from DuckDB.
    """
    if check.dataset == "sales.csv":
        return _recompute_sales(check.recompute_key or check.check_id)
    if check.dataset == "spend.csv":
        return _recompute_spend(check.recompute_key or check.check_id)
    if check.dataset == "tickets.csv":
        return _recompute_tickets(check.recompute_key or check.check_id)
    raise KeyError(check.dataset)


def shapes_covered() -> dict[str, int]:
    """How many checks exercise each of AT-40's shapes."""
    out = {shape: 0 for shape in AT40_SHAPES}
    for check in CHECKS:
        out[check.shape] += 1
    return out


def check_by_id(check_id: str) -> GoldenCheck:
    for check in CHECKS:
        if check.check_id == check_id:
            return check
    raise KeyError(check_id)
