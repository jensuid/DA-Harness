"""Generate the B2B sales dataset for WALK-E2E-001.

Realistic enough to drive a real analysis; seeded so the walk-test is
reproducible across sessions. Defects are planted deliberately so the
profiling, quality-detection, validation and EVALUATE surfaces have
something real to catch.
"""

import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(20260924)

OUT = Path(__file__).resolve().parent / "b2b_sales_q3_2026.csv"

# --- the clean reference data -------------------------------------------------
REGIONS = ["North", "South", "East", "West", "Central"]
# Two products share a name but differ in SKU/category - the classic
# "same label, different thing" that breaks naive GROUP BY reporting.
PRODUCTS = [
    ("SKU-1001", "Atom Workspace", "Software", 1200.0),
    ("SKU-1002", "Atom Workspace", "Service", 180.0),
    ("SKU-2001", "Beacon Analytics", "Software", 2400.0),
    ("SKU-2002", "Beacon Insights", "Software", 1500.0),
    ("SKU-3001", "Cobalt Storage", "Hardware", 3400.0),
    ("SKU-3002", "Cobalt Storage", "Service", 420.0),
    ("SKU-4001", "Drift Integrator", "Service", 640.0),
    ("SKU-5001", "Ember Secure", "Software", 980.0),
]
ACCOUNTS = [
    ("ACC-5001", "Meridian Health Group", "Healthcare", "Enterprise"),
    ("ACC-5002", "Atlas Logistics", "Transportation", "Enterprise"),
    ("ACC-5003", "Northwind Capital", "Financial Services", "Enterprise"),
    ("ACC-5004", "Bluepine Retail", "Retail", "Mid-Market"),
    ("ACC-5005", "Crestline Energy", "Energy", "Enterprise"),
    ("ACC-5006", "Solstice Media", "Media", "Mid-Market"),
    ("ACC-5007", "Ironclad Manufacturing", "Manufacturing", "Enterprise"),
    ("ACC-5008", "Lumen Education", "Education", "Mid-Market"),
    ("ACC-5009", "Vanguard Insurance", "Financial Services", "Mid-Market"),
    ("ACC-5010", "Harbor & Field", "Retail", "Small"),
    ("ACC-5011", "Quantum Leap Labs", "Technology", "Small"),
    ("ACC-5012", "Riverside Council", "Public Sector", "Mid-Market"),
]
REPS = ["R-01 Dana Okafor", "R-02 Theo Lindqvist", "R-03 Priya Raman",
        "R-04 Marcus Bell", "R-05 Sara Nadeau"]
CHANNELS = ["Direct", "Partner", "Online Self-Serve"]


def d(iso: str) -> date:
    return date.fromisoformat(iso)


START, END = d("2026-07-01"), d("2026-09-30")
rows: list[dict] = []
oid = 100000

# July: strong month
for _ in range(190):
    oid += 1
    day = START + timedelta(days=random.randint(0, 30))
    sku, name, cat, price = random.choice(PRODUCTS)
    acc = random.choice(ACCOUNTS)
    units = random.randint(2, 40)
    rows.append(dict(
        order_id=f"ORD-{oid}", order_date=day.isoformat(), quarter="2026-Q3",
        account_id=acc[0], account_name=acc[1], industry=acc[2], segment=acc[3],
        region=random.choice(REGIONS), product_sku=sku, product_name=name,
        category=cat, units=units, unit_price=round(price, 2),
        revenue=round(units * price, 2),
        rep=random.choice(REPS), channel=random.choice(CHANNELS),
        discount_pct=round(random.choice([0, 0, 0, 5, 10, 15]), 1),
    ))

# August: dip (vacation season, smaller orders)
for _ in range(120):
    oid += 1
    day = d("2026-08-01") + timedelta(days=random.randint(0, 30))
    sku, name, cat, price = random.choice(PRODUCTS)
    acc = random.choice(ACCOUNTS)
    units = random.randint(1, 12)
    rows.append(dict(
        order_id=f"ORD-{oid}", order_date=day.isoformat(), quarter="2026-Q3",
        account_id=acc[0], account_name=acc[1], industry=acc[2], segment=acc[3],
        region=random.choice(REGIONS), product_sku=sku, product_name=name,
        category=cat, units=units, unit_price=round(price, 2),
        revenue=round(units * price, 2),
        rep=random.choice(REPS), channel=random.choice(CHANNELS),
        discount_pct=round(random.choice([0, 0, 5, 10, 20]), 1),
    ))

# September: recovery, but Enterprise orders land late in the month
for _ in range(170):
    oid += 1
    day = d("2026-09-01") + timedelta(days=random.randint(0, 29))
    sku, name, cat, price = random.choice(PRODUCTS)
    acc = random.choice([a for a in ACCOUNTS if a[3] == "Enterprise"])
    units = random.randint(5, 50)
    rows.append(dict(
        order_id=f"ORD-{oid}", order_date=day.isoformat(), quarter="2026-Q3",
        account_id=acc[0], account_name=acc[1], industry=acc[2], segment=acc[3],
        region=random.choice(REGIONS), product_sku=sku, product_name=name,
        category=cat, units=units, unit_price=round(price, 2),
        revenue=round(units * price, 2),
        rep=random.choice(REPS), channel=random.choice(CHANNELS),
        discount_pct=round(random.choice([0, 0, 0, 5, 10]), 1),
    ))

# --- planted defects ---------------------------------------------------------

# D1: exact duplicate rows (a double-submit in the CRM export)
dups = random.sample(rows, 4)
for r in dups:
    rows.append(dict(r))

# D2: a null account_id on a few rows (lead converted without an account)
for r in random.sample(rows, 6):
    r["account_id"] = ""

# D3: inconsistent category labels for the SAME sku - drift the profiler
# should surface and any category rollup must handle
for r in rows:
    if r["product_sku"] == "SKU-3001" and random.random() < 0.35:
        r["category"] = "HW"
    if r["product_sku"] == "SKU-4001" and random.random() < 0.3:
        r["category"] = "Svc"

# D4: revenue that does NOT equal units x unit_price (the juicy one)
for r in random.sample(rows, 10):
    r["revenue"] = round(r["revenue"] * random.uniform(1.4, 2.1), 2)

# D5: mixed date formats - a second export wrote ISO-with-space
for r in random.sample(rows, 5):
    r["order_date"] = r["order_date"].replace("-", "/")

# D6: implausible units (a data-entry slip)
for r in random.sample(rows, 3):
    r["units"] = 9999

# D7: a segment value that is not in the vocabulary
for r in random.sample(rows, 2):
    r["segment"] = "Strategic"

# D8: a negative discount
for r in random.sample(rows, 2):
    r["discount_pct"] = -7.0

random.shuffle(rows)

FIELDS = ["order_id", "order_date", "quarter", "account_id", "account_name",
          "industry", "segment", "region", "product_sku", "product_name",
          "category", "units", "unit_price", "revenue", "rep", "channel",
          "discount_pct"]

with OUT.open("w", newline="") as fh:
    w = csv.DictWriter(fh, fieldnames=FIELDS)
    w.writeheader()
    w.writerows(rows)

print(f"wrote {OUT}")
print(f"rows: {len(rows)}")

# verification counts (for the handoff note)
from collections import Counter
print("empty account_id:", sum(1 for r in rows if not r["account_id"]))
print("category drift rows (HW/Svc):",
      sum(1 for r in rows if r["category"] in ("HW", "Svc")))
bad_rev = [r for r in rows
           if abs(r["revenue"] - r["units"] * r["unit_price"]) > 0.01]
print("revenue != units*price:", len(bad_rev))
print("non-iso dates:",
      sum(1 for r in rows if "/" in r["order_date"]))
print("units==9999:", sum(1 for r in rows if r["units"] == 9999))
print("segment 'Strategic':",
      sum(1 for r in rows if r["segment"] == "Strategic"))
print("negative discount:",
      sum(1 for r in rows if r["discount_pct"] < 0))
ids = Counter(r["order_id"] for r in rows)
print("duplicate order_ids:", sum(c - 1 for c in ids.values() if c > 1))
