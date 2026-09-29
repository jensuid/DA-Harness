"""Build the walk-test 3 dataset: a SaaS helpdesk export.

Deterministic (seeded). ~90 tickets Jan-Aug 2026 over 3 products and 3 tiers,
planted with the imperfections a real export carries so the profiler, the
quality gate and the edge-case UX all have something to say:

  - 2 blank `product` values          (a categorical with holes)
  - 1 `resolution_hours` outlier      (a 40-day ticket, 30x the median)
  - 1 `date` in a different format    (US style, month-first)
  - 1 duplicate `ticket_id`           (a row that is there twice)
  - 1 `satisfaction` out of range     (a 0 on a 1-5 scale)
  - `enterprise` vs `Enterprise`      (a categorical split, same tier twice)

The narrative hook: satisfaction for the Enterprise tier dipped in Q2 and the
analyst wants to know whether response time explains it.

Run:  python make_dataset.py
"""

from __future__ import annotations

import csv
import random
from pathlib import Path

OUT = Path(__file__).parent / "helpdesk_tickets_2026.csv"

PRODUCTS = ["Atlas", "Beacon", "Compass"]
TIERS = ["Starter", "Growth", "Enterprise"]
CHANNELS = ["Email", "Chat", "Phone", "Web Form"]
AGENTS = ["R. Okafor", "M. Lindqvist", "T. Nguyen", "S. Patel", "J. Moreau"]

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
    for month in range(1, 9):  # Jan..Aug 2026
        # Enterprise gets slower in Apr-Jun, which is what dips satisfaction.
        ent_slowdown = 1.0
        if month in (4, 5, 6):
            ent_slowdown = 2.4
        for _ in range(11):
            n += 1
            day = rng.randint(1, 28)
            date = iso((START_YEAR, month, day))
            product = rng.choice(PRODUCTS)
            tier = rng.choice(TIERS)
            first_response = round(max(0.2, rng.gauss(2.0, 1.2)), 2)
            base_resolution = max(
                first_response + 0.5, rng.gauss(6.0, 3.0)
            )
            if tier == "Enterprise":
                base_resolution *= ent_slowdown
            resolution = round(base_resolution, 2)
            satisfaction = max(1, min(5, round(5.4 - resolution / 8.0)))
            if satisfaction > 5:
                satisfaction = 5
            rows.append(
                {
                    "ticket_id": f"TK-{1000 + n}",
                    "created_date": date,
                    "product": product,
                    "tier": tier,
                    "agent": rng.choice(AGENTS),
                    "first_response_hours": f"{first_response:.2f}",
                    "resolution_hours": f"{resolution:.2f}",
                    "satisfaction": f"{satisfaction}",
                    "channel": rng.choice(CHANNELS),
                    "reopened": "yes" if rng.random() < 0.12 else "",
                }
            )
    return rows


def plant(rows: list[dict[str, str]], rng: random.Random) -> None:
    """Inject the imperfections, on deterministic indices."""
    # 1. Two blank products.
    rows[4]["product"] = ""
    rows[41]["product"] = ""
    # 2. One resolution outlier: a 40-day ticket.
    rows[17]["resolution_hours"] = "962.50"
    rows[17]["satisfaction"] = "1"
    # 3. One date in US month-first style.
    rows[29]["created_date"] = us_style(
        (START_YEAR, month_of(rows[29]["created_date"]), 11)
    )
    # 4. One duplicated ticket_id (and a near-duplicate row).
    dup = dict(rows[62])
    rows.append(dup)
    # 5. One out-of-range satisfaction (0 on a 1-5 scale).
    rows[70]["satisfaction"] = "0"
    # 6. A categorical split: the same tier spelled twice.
    for r in rows:
        if r["tier"] == "Enterprise" and int(r["ticket_id"].split("-")[1]) % 3 == 0:
            r["tier"] = "enterprise"


def main() -> None:
    rng = random.Random(20260929)
    rows = build(rng)
    plant(rows, rng)
    rows.sort(key=lambda r: (r["created_date"], r["ticket_id"]))
    with OUT.open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {len(rows)} rows to {OUT}")
    products = {}
    tiers = {}
    for r in rows:
        products[r["product"]] = products.get(r["product"], 0) + 1
        tiers[r["tier"]] = tiers.get(r["tier"], 0) + 1
    print("products:", products)
    print("tiers:", tiers)


if __name__ == "__main__":
    main()
