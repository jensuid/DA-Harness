"""Build the walk-test 5 dataset: a retail inventory export.

Deterministic (seeded). 2,800 SKU/store/week rows across 6 store regions and
4 product categories, Jan-Jun 2026, planted with the imperfections a real
inventory/ERP export carries so the profiler, the quality gate and the
edge-case UX all have something to say:

  - 3 blank `store_region` values    (a categorical with holes)
  - 1 `revenue` outlier              (a 40x bulk order in a normal week)
  - 1 `week_start` in a US format    (month-first, while every other row is ISO)
  - 1 duplicate `sku_store_id`       (a row that is there twice)
  - 1 `on_hand` out of range         (a 0 for a SKU that is not discontinued)
  - `north` vs `North`               (a categorical split, same region twice)

The narrative hook: out-of-stock for the electronics SKUs in the North region
spiked in March, and the analyst wants to know whether lead time or the
on-hand policy explains it - on_hand is the candidate cause, and the outlier
is the row that would crown a naive average if it were not flagged first.

Run:  python make_dataset.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path(__file__).parent / "retail_inventory_2026_h1.csv"

SEED = 20260501
REGIONS = ["North", "South", "East", "West", "Central", "Northeast"]
CATEGORIES = ["Electronics", "Apparel", "Grocery", "Home"]
SKU_PER_CATEGORY = 9
STORES = 5

WEEKS = [
    "2026-01-06", "2026-01-13", "2026-01-20", "2026-01-27",
    "2026-02-03", "2026-02-10", "2026-02-17", "2026-02-24",
    "2026-03-03", "2026-03-10", "2026-03-17", "2026-03-24",
    "2026-03-31", "2026-04-07", "2026-04-14", "2026-04-21",
    "2026-04-28", "2026-05-05", "2026-05-12", "2026-05-19",
    "2026-05-26", "2026-06-02", "2026-06-09", "2026-06-16",
    "2026-06-23", "2026-06-30",
]

# Electronics in the North region spike out-of-stock in March.
STOCKOUT_BUMP = {("Electronics", "North"): {"2026-03-03", "2026-03-10",
                                           "2026-03-17", "2026-03-24",
                                           "2026-03-31"}}


def main() -> None:
    rnd = random.Random(SEED)
    rows: list[dict[str, str]] = []
    sku_counter = 0

    for category in CATEGORIES:
        for _ in range(SKU_PER_CATEGORY):
            sku_counter += 1
            sku = f"SKU-{sku_counter:04d}"
            base_price = round(rnd.uniform(8.0, 420.0), 2)
            base_lead = rnd.randint(3, 21)

            for store in range(1, STORES + 1):
                region = REGIONS[(store + sku_counter) % len(REGIONS)]
                stockout_weeks = STOCKOUT_BUMP.get((category, region), set())

                for week in WEEKS:
                    units = rnd.randint(6, 90)
                    if week in stockout_weeks:
                        units = max(1, units // 9)
                    on_hand = rnd.randint(0, 240)
                    if units >= on_hand and week in stockout_weeks:
                        on_hand = 0
                    lead = base_lead + rnd.randint(-2, 2)
                    revenue = round(units * base_price, 2)

                    rows.append({
                        "sku_store_id": f"{sku}-S{store:02d}",
                        "week_start": week,
                        "sku": sku,
                        "category": category,
                        "store_id": f"ST-{store:03d}",
                        "store_region": region,
                        "on_hand": str(on_hand),
                        "units_sold": str(units),
                        "unit_price_usd": f"{base_price:.2f}",
                        "revenue": f"{revenue:.2f}",
                        "lead_time_days": str(lead),
                        "discontinued": "no",
                    })

    # 3 blank store_region
    for r in rnd.sample(rows, 3):
        r["store_region"] = ""

    # 1 revenue outlier: a 40x bulk order on a normal week
    tgt = rnd.choice(rows)
    tgt["revenue"] = f"{round(float(tgt['revenue']) * 40.0, 2):.2f}"
    tgt["units_sold"] = str(int(tgt["units_sold"]) * 40)

    # 1 week_start in US month-first format
    tgt = rnd.choice(rows)
    iso = tgt["week_start"]
    y, m, d = iso.split("-")
    tgt["week_start"] = f"{m}/{d}/{y}"

    # 1 duplicate sku_store_id (the same row, twice)
    dup = dict(rnd.choice(rows))
    rows.append(dup)

    # 1 on_hand = 0 for a SKU that is not discontinued
    tgt = rnd.choice(rows)
    tgt["on_hand"] = "0"

    # categorical split: 'north' vs 'North'
    n_split = 0
    for r in rows:
        if r["store_region"] == "North" and n_split < 14:
            r["store_region"] = "north"
            n_split += 1

    rnd.shuffle(rows)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)

    print(f"wrote {len(rows)} rows -> {OUT}")


if __name__ == "__main__":
    main()
