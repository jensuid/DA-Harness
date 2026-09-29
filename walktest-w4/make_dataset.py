"""Build the walk-test 4 dataset: a B2B subscription/renewal export.

Deterministic (seeded). 3,000 subscription months over 4 product plans and
5 customer segments, Jan-Dec 2026, planted with the imperfections a real
CRM/billing export carries so the profiler, the quality gate and the
edge-case UX all have something to say:

  - 3 blank `segment` values        (a categorical with holes)
  - 1 `revenue_usd` outlier         (a 40x annual prepay a monthly row should not carry)
  - 1 `renewed_on` in a US format   (month-first, while every other row is ISO)
  - 1 duplicate `subscription_id`   (a row that is there twice)
  - 1 `seats` out of range          (a 0 on a plan whose minimum is 1)
  - `scaleup` vs `ScaleUp`          (a categorical split, same segment twice)

The narrative hook: renewals for the ScaleUp segment dipped in Q3 and the
analyst wants to know whether product usage (active_users / seats) explains
it - the plan's seat utilisation is the candidate cause, and the outlier is
the row that would crown a naive average if it were not flagged first.

Run:  python make_dataset.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path(__file__).parent / "saas_renewals_2026.csv"

PLANS = ["Solo", "Team", "Business", "Enterprise"]
SEGMENTS = ["Startup", "ScaleUp", "MidMarket", "Agency", "Nonprofit"]
SEAT_FLOOR = {"Solo": 1, "Team": 3, "Business": 10, "Enterprise": 50}
SEAT_CEIL = {"Solo": 5, "Team": 25, "Business": 100, "Enterprise": 500}
PLAN_PRICE = {"Solo": 29.0, "Team": 99.0, "Business": 299.0, "Enterprise": 999.0}

START_YEAR = 2026


def iso(d: tuple[int, int, int]) -> str:
    y, m, d = d
    return f"{y:04d}-{m:02d}-{d:02d}"


def us_style(d: tuple[int, int, int]) -> str:
    _, m, d = d
    return f"{m:02d}/{d:02d}/2026"


def month_of(s: str) -> int:
    if "/" in s:
        return int(s.split("/")[0])
    return int(s.split("-")[1])


def build(rng: random.Random) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    n = 0
    for month in range(1, 13):  # Jan..Dec 2026
        # ScaleUp renewal dips in Jul-Sep: the cohort that grew fast in H1
        # turned out to renew at a lower rate, and its seat utilisation
        # dropped before the dip - the candidate cause the analyst chases.
        scaleup_dip = 1.0
        if month in (7, 8, 9):
            scaleup_dip = 0.62
        for _ in range(250):
            n += 1
            plan = rng.choice(PLANS)
            segment = rng.choice(SEGMENTS)
            seats = rng.randint(SEAT_FLOOR[plan], SEAT_CEIL[plan])
            active = max(0, min(seats, int(round(seats * rng.uniform(0.35, 0.95)))))
            if segment == "ScaleUp":
                active = max(0, min(seats, int(round(active * scaleup_dip))))
            list_price = PLAN_PRICE[plan] * seats
            # A discounted deal is the norm, not the exception, in this export.
            revenue = round(list_price * rng.uniform(0.80, 1.00), 2)
            status = "renewed" if rng.random() < 0.86 else "churned"
            day = rng.randint(1, 28)
            renewed = iso((START_YEAR, month, day))
            row = {
                "subscription_id": f"SUB-{n:05d}",
                "renewed_on": renewed,
                "plan": plan,
                "segment": segment,
                "seats": str(seats),
                "active_users": str(active),
                "list_price_usd": f"{list_price:.2f}",
                "revenue_usd": f"{revenue:.2f}",
                "status": status,
                "payment_cycle": "monthly",
            }
            rows.append(row)

    # The planted imperfections, each one a thing the profiler must surface.
    #
    # W4 keeps W3's six shapes (a categorical with holes, an outlier that
    # would crown a naive average, a mixed date format, a duplicate key, a
    # value out of range and a categorical that means two things) because a
    # walk-test that plants nothing cannot find the profiler working.

    # 1. Three blank segments - the categorical with holes.
    for i in (700, 1400, 2100):
        rows[i]["segment"] = ""

    # 2. One revenue outlier: an Enterprise annual prepay on a monthly row.
    #    40x the row's own list price, and ~20x the column's next largest
    #    value, so a mean over `revenue_usd` describes this one row.
    rows[1500]["revenue_usd"] = f"{rows[1500]['list_price_usd'] and 499500.0:.2f}"
    rows[1500]["payment_cycle"] = "annual"

    # 3. One renewed_on in US month-first format while every other row is ISO.
    rows[2200]["renewed_on"] = us_style((START_YEAR, 9, 12))

    # 4. One duplicated subscription_id - the row that is there twice.
    rows[2900]["subscription_id"] = rows[400]["subscription_id"]

    # 5. One seats value below the plan's own floor (Solo's minimum is 1).
    rows[950]["seats"] = "0"
    rows[950]["active_users"] = "0"

    # 6. A categorical split: `scaleup` is the same segment as `ScaleUp`.
    for i in (300, 1800, 2600):
        rows[i]["segment"] = "scaleup"

    return rows


def main() -> None:
    rng = random.Random(20260930)
    rows = build(rng)

    # The duplicate row must survive the sort the export would do, so it is
    # planted before the write, not after it.
    rows.sort(key=lambda r: (r["renewed_on"], r["subscription_id"]))

    with open(OUT, "w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print(f"wrote {len(rows)} rows to {OUT}")
    print(f"out of range: seats=0 x{sum(1 for r in rows if r['seats'] == '0')}")
    print(f"out of range: revenue 499500 x{sum(1 for r in rows if r['revenue_usd'] == '499500.00')}")
    print(f"blank segment: x{sum(1 for r in rows if r['segment'] == '')}")
    print(f"lowercase scaleup: x{sum(1 for r in rows if r['segment'] == 'scaleup')}")
    print(f"us date: {sum(1 for r in rows if '/' in r['renewed_on'])}")
    ids = [r["subscription_id"] for r in rows]
    print(f"duplicate ids: {len(ids) - len(set(ids))}")


if __name__ == "__main__":
    main()
