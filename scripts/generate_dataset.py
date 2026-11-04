"""
generate_dataset.py
-------------------
Generates a SYNTHETIC retail inventory dataset for the
Supply Chain Inventory Analytics project.

It simulates 12 months of daily operations (2025-11-01 to 2026-10-31) for
120 products across 5 warehouses. Each product-warehouse pair follows a
reorder-point policy with FIFO stock batches, so the data is internally
consistent: sales never exceed stock, stock = sum of batches, and ageing
stock comes from real received dates.

Some product-warehouse pairs are deliberately "badly managed" so the
dashboard has something to find:
    normal  -> healthy policy
    under   -> reorder too late/too little -> low stock & stockouts
    over    -> order far too much          -> excess stock
    slow    -> demand collapses mid-year   -> ageing / dead stock

Output (CSV, in data/raw/):
    dim_product.csv, dim_warehouse.csv, dim_supplier.csv,
    fact_sales.csv, fact_inventory_snapshot.csv,
    fact_purchase_orders.csv, fact_inventory_batches.csv

Usage:
    python scripts/generate_dataset.py            # raw files with a few injected data-quality issues
    python scripts/generate_dataset.py --clean    # no injected issues

NOTE: All data is synthetic. Not real company data.
"""

import argparse
import os
from collections import deque
from datetime import date, timedelta

import numpy as np
import pandas as pd

SEED = 42
START = date(2025, 11, 1)
N_DAYS = 365                      # 2025-11-01 .. 2026-10-31
AS_OF = START + timedelta(days=N_DAYS - 1)

rng = np.random.default_rng(SEED)

# ----------------------------------------------------------------------
# 1. Master data
# ----------------------------------------------------------------------
CATALOG = {
    "Grocery & Staples": (
        ["Basmati Rice 5kg", "Whole Wheat Atta 10kg", "Toor Dal 1kg", "Moong Dal 1kg",
         "Chana Dal 1kg", "Sugar 5kg", "Iodised Salt 1kg", "Mustard Oil 1L",
         "Sunflower Oil 1L", "Refined Oil 5L", "Poha 500g", "Besan 1kg", "Rajma 1kg",
         "Masoor Dal 1kg", "Jaggery 1kg", "Turmeric Powder 200g",
         "Red Chilli Powder 200g", "Garam Masala 100g", "Tea Leaves 500g", "Ghee 1L"],
        (40, 600)),
    "Beverages": (
        ["Cola 2L", "Orange Juice 1L", "Mango Drink 1.2L", "Packaged Water 1L",
         "Energy Drink 250ml", "Green Tea 25 bags", "Instant Coffee 100g",
         "Lemon Soda 750ml", "Coconut Water 200ml", "Iced Tea 500ml",
         "Sparkling Water 750ml", "Apple Juice 1L", "Mixed Fruit Juice 1L",
         "Soft Drink 600ml", "Buttermilk 200ml", "Lassi 200ml", "Cold Coffee 200ml",
         "Malt Drink 500g", "Tomato Juice 1L", "Electrolyte Drink 500ml"],
        (10, 220)),
    "Personal Care": (
        ["Shampoo 340ml", "Conditioner 180ml", "Body Wash 250ml", "Toothpaste 150g",
         "Toothbrush Pack", "Face Wash 100ml", "Moisturiser 200ml", "Hand Wash 250ml",
         "Deodorant 150ml", "Soap Bar 4-pack", "Hair Oil 200ml", "Sunscreen 50g",
         "Razor Pack", "Shaving Foam 200g", "Talcum Powder 200g", "Lip Balm",
         "Face Cream 50g", "Body Lotion 400ml", "Mouthwash 250ml", "Sanitary Pads 20ct"],
        (30, 420)),
    "Household": (
        ["Detergent Powder 2kg", "Liquid Detergent 1L", "Dishwash Gel 750ml",
         "Floor Cleaner 1L", "Toilet Cleaner 500ml", "Glass Cleaner 500ml",
         "Garbage Bags 30ct", "Tissue Roll 6-pack", "Kitchen Towel 2-pack",
         "Air Freshener 250ml", "Mosquito Repellent Refill", "Scrub Pad 3-pack",
         "Aluminium Foil 25m", "Cling Film 30m", "Matchbox 10-pack", "Candles 12-pack",
         "LED Bulb 9W", "Batteries AA 4-pack", "Phenyl 1L", "Fabric Softener 1L"],
        (20, 350)),
    "Packaged Foods": (
        ["Instant Noodles 5-pack", "Biscuits 600g", "Cornflakes 475g", "Oats 1kg",
         "Peanut Butter 340g", "Tomato Ketchup 950g", "Jam 500g", "Pasta 500g",
         "Pasta Sauce 400g", "Potato Chips 150g", "Namkeen 400g", "Chocolate Bar 55g",
         "Cookies 300g", "Instant Soup 4-pack", "Pickle 500g", "Honey 500g",
         "Muesli 500g", "Popcorn 3-pack", "Ready-to-Eat Meal 300g", "Mayonnaise 250g"],
        (15, 300)),
    "Dairy & Frozen": (
        ["Butter 500g", "Cheese Slices 200g", "Paneer 200g", "Curd 400g", "UHT Milk 1L",
         "Ice Cream 1L", "Frozen Peas 500g", "Frozen Parathas 5-pack", "French Fries 750g",
         "Cream 200ml", "Mozzarella 200g", "Cheese Spread 180g", "Flavoured Yogurt 100g",
         "Condensed Milk 400g", "Milk Powder 1kg", "Frozen Corn 500g",
         "Frozen Nuggets 400g", "Sweet Corn Can 400g", "Ice Cream Tub 500ml",
         "Skimmed Milk 1L"],
        (25, 380)),
}
BRANDS = ["Aarav", "Kisan Fresh", "PureLeaf", "Sunrise", "GreenField",
          "Everyday", "Nirmal", "Royal Harvest", "UrbanCart", "FreshBay"]

WAREHOUSES = [
    # id, name, city, state, region, demand_factor
    ("WH01", "Panipat DC", "Panipat", "Haryana", "North", 1.00),
    ("WH02", "Mumbai DC", "Mumbai", "Maharashtra", "West", 1.40),
    ("WH03", "Bengaluru DC", "Bengaluru", "Karnataka", "South", 1.20),
    ("WH04", "Kolkata DC", "Kolkata", "West Bengal", "East", 0.90),
    ("WH05", "Hyderabad DC", "Hyderabad", "Telangana", "South", 1.05),
]

N_SUPPLIERS = 12

# Calendar-month demand factor (festive season Oct-Nov is highest)
MONTH_FACTOR = {1: .95, 2: .90, 3: 1.00, 4: 1.05, 5: 1.10, 6: 1.00,
                7: .95, 8: 1.00, 9: 1.05, 10: 1.25, 11: 1.30, 12: 1.15}
DOW_FACTOR = {0: .90, 1: .90, 2: .95, 3: 1.00, 4: 1.10, 5: 1.25, 6: 1.25}


def build_suppliers():
    rows = []
    for i in range(1, N_SUPPLIERS + 1):
        rows.append({
            "supplier_id": f"SUP{i:02d}",
            "supplier_name": f"Supplier {i:02d} Traders",
            "lead_time_days": int(rng.integers(3, 15)),
            "reliability": round(float(rng.uniform(0.70, 0.98)), 2),
        })
    return pd.DataFrame(rows)


def build_products(suppliers):
    rows, n = [], 1
    for cat, (items, (lo, hi)) in CATALOG.items():
        for item in items:
            brand = BRANDS[int(rng.integers(0, len(BRANDS)))]
            cost = round(float(np.exp(rng.uniform(np.log(lo), np.log(hi)))), 2)
            margin = float(rng.uniform(0.15, 0.35))
            rows.append({
                "product_id": f"P{n:03d}",
                "product_name": f"{brand} {item}",
                "category": cat,
                "brand": brand,
                "unit_cost": cost,
                "unit_price": round(cost * (1 + margin), 2),
                "supplier_id": suppliers.supplier_id.iloc[int(rng.integers(0, N_SUPPLIERS))],
            })
            n += 1
    return pd.DataFrame(rows)


# ----------------------------------------------------------------------
# 2. Simulation
# ----------------------------------------------------------------------
def daily_factors(category):
    """Seasonality x day-of-week multiplier for each of the 365 days."""
    f = np.empty(N_DAYS)
    for d in range(N_DAYS):
        day = START + timedelta(days=d)
        m = MONTH_FACTOR[day.month] * DOW_FACTOR[day.weekday()]
        if category == "Beverages" and day.month in (4, 5, 6):
            m *= 1.35
        if category == "Dairy & Frozen" and day.month in (4, 5, 6):
            m *= 1.20
        f[d] = m
    return f


def simulate(products, suppliers, warehouses):
    sup = suppliers.set_index("supplier_id")
    month_end_days = {}
    for d in range(N_DAYS):
        day = START + timedelta(days=d)
        if (day + timedelta(days=1)).month != day.month:
            month_end_days[d] = day

    cat_factors = {c: daily_factors(c) for c in CATALOG}

    sales, snaps, pos, batches_out = [], [], [], []
    po_counter, batch_counter, pair_status = 1, 1, []

    for _, p in products.iterrows():
        popularity = float(np.exp(rng.normal(0.9, 0.55)))   # base units/day
        lead_base = int(sup.loc[p.supplier_id, "lead_time_days"])
        reliability = float(sup.loc[p.supplier_id, "reliability"])

        for wh_id, _, _, _, _, wh_factor in warehouses:
            mode = rng.choice(["normal", "under", "over", "slow"],
                              p=[0.66, 0.13, 0.13, 0.08])
            lam_plan = popularity * wh_factor * float(rng.uniform(0.8, 1.2))
            mult = np.ones(N_DAYS)
            if mode == "slow":      # demand collapses part-way through the year
                collapse_day = int(rng.integers(100, 280))
                mult[collapse_day:] = 0.10
            demand = rng.poisson(lam_plan * mult * cat_factors[p.category])

            # ordering policy (based on what the planner EXPECTS)
            if mode == "under":
                rop = lam_plan * lead_base * 0.7
                oqty = max(5, lam_plan * 10)
            elif mode == "over":
                rop = lam_plan * (lead_base + 12)
                oqty = max(30, lam_plan * 75)
            else:  # normal & slow (planner allows for seasonal peaks)
                rop = lam_plan * 1.15 * (lead_base + 6)
                oqty = max(12, lam_plan * 1.1 * 25)
            safety = max(2, int(round(lam_plan * 1.15 * 4)))

            # opening stock: 1-3 batches received before the start date
            batches = deque()
            if mode == "over":
                open_total = int(lam_plan * 60)
                age_range = (5, 150)
            elif mode == "under":
                open_total = int(lam_plan * 8)
                age_range = (3, 60)
            else:
                open_total = int(rop + oqty * 0.6)
                age_range = (3, 90)
            n_b = int(rng.integers(1, 4))
            for share in rng.dirichlet(np.ones(n_b)):
                q = int(open_total * share)
                if q > 0:
                    rcv = START - timedelta(days=int(rng.integers(*age_range)))
                    batches.append([rcv, q, q, f"OPENING", batch_counter])
                    batch_counter += 1
            batches = deque(sorted(batches, key=lambda b: b[0]))

            stock = sum(b[2] for b in batches)
            on_order = 0
            arrivals = {}          # day index -> list of PO dicts
            open_pos = []
            stockout_days_month = 0

            for d in range(N_DAYS):
                day = START + timedelta(days=d)

                # 1) receive purchase orders
                for po in arrivals.pop(d, []):
                    batches.append([day, po["qty"], po["qty"], po["po_id"], batch_counter])
                    batch_counter += 1
                    stock += po["qty"]
                    on_order -= po["qty"]
                    po["received_date"] = day

                # 2) sell FIFO
                want = int(demand[d])
                sold = 0
                while want > sold and batches:
                    b = batches[0]
                    take = min(b[2], want - sold)
                    b[2] -= take
                    sold += take
                    stock -= take
                    if b[2] == 0:
                        batches.popleft()
                if sold > 0:
                    disc = float(rng.choice([0, 0, 0, 0, 5, 10, 15]))
                    sales.append((day, p.product_id, wh_id, sold,
                                  p.unit_price, disc))
                if want > sold or stock == 0:
                    stockout_days_month += 1

                # 3) reorder check
                if stock + on_order <= rop:
                    q = int(max(1, round(oqty * float(rng.uniform(0.9, 1.1)))))
                    delay = int(rng.integers(2, 8)) if rng.random() > reliability else 0
                    arr = d + lead_base + delay
                    po = {"po_id": f"PO{po_counter:06d}", "product_id": p.product_id,
                          "warehouse_id": wh_id, "supplier_id": p.supplier_id,
                          "order_date": day,
                          "expected_date": day + timedelta(days=lead_base),
                          "received_date": None, "qty": q,
                          "unit_cost": round(p.unit_cost * float(rng.uniform(0.97, 1.03)), 2)}
                    po_counter += 1
                    on_order += q
                    open_pos.append(po)
                    if arr < N_DAYS:
                        arrivals.setdefault(arr, []).append(po)

                # 4) month-end snapshot
                if d in month_end_days:
                    snaps.append((month_end_days[d], p.product_id, wh_id,
                                  stock, stockout_days_month))
                    stockout_days_month = 0

            pos.extend(open_pos)
            for b in batches:
                batches_out.append({
                    "batch_id": f"B{b[4]:06d}", "product_id": p.product_id,
                    "warehouse_id": wh_id, "received_date": b[0],
                    "qty_received": b[1], "qty_remaining": b[2],
                    "unit_cost": p.unit_cost, "source": b[3]})
            pair_status.append((p.product_id, wh_id, mode, round(rop, 1), safety))

    fact_sales = pd.DataFrame(sales, columns=[
        "order_date", "product_id", "warehouse_id", "quantity",
        "unit_price", "discount_pct"])
    fact_sales.insert(0, "sale_id", [f"S{i:07d}" for i in range(1, len(fact_sales) + 1)])
    fact_sales["revenue"] = (fact_sales.quantity * fact_sales.unit_price
                             * (1 - fact_sales.discount_pct / 100)).round(2)

    snapshot = pd.DataFrame(snaps, columns=[
        "snapshot_date", "product_id", "warehouse_id",
        "stock_on_hand", "stockout_days"])

    purchase_orders = pd.DataFrame(pos).rename(columns={"qty": "quantity"})
    batches_df = pd.DataFrame(batches_out)
    status = pd.DataFrame(pair_status,
                          columns=["product_id", "warehouse_id", "_mode", "reorder_level", "safety_stock"])
    return fact_sales, snapshot, purchase_orders, batches_df, status


# ----------------------------------------------------------------------
# 3. Optional data-quality issues (so Power Query cleaning has a purpose)
# ----------------------------------------------------------------------
def inject_issues(products, sales, suppliers):
    notes = []
    # a) inconsistent category text
    idx = products.sample(frac=0.08, random_state=1).index
    products.loc[idx, "category"] = products.loc[idx, "category"].map(
        lambda s: " " + s.upper() + " ")
    notes.append("dim_product.category: extra spaces / inconsistent casing on ~8% of rows")
    # b) duplicate sales rows
    dup = sales.sample(n=max(50, int(len(sales) * 0.003)), random_state=2)
    sales = pd.concat([sales, dup], ignore_index=True).sample(
        frac=1, random_state=3).reset_index(drop=True)
    notes.append("fact_sales: ~0.3% exact duplicate rows")
    # c) missing values
    suppliers.loc[suppliers.sample(n=2, random_state=4).index, "lead_time_days"] = np.nan
    notes.append("dim_supplier.lead_time_days: 2 missing values")
    return products, sales, suppliers, notes


# ----------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--clean", action="store_true", help="do not inject data-quality issues")
    ap.add_argument("--out", default="data/raw", help="output folder")
    args = ap.parse_args()
    os.makedirs(args.out, exist_ok=True)

    suppliers = build_suppliers()
    products = build_products(suppliers)
    warehouses_df = pd.DataFrame(
        [w[:5] for w in WAREHOUSES],
        columns=["warehouse_id", "warehouse_name", "city", "state", "region"])

    sales, snapshot, pos, batches, status = simulate(products, suppliers, WAREHOUSES)

    # reorder_level and safety_stock per product/warehouse drive the low-stock KPIs
    reorder = status[["product_id", "warehouse_id", "reorder_level", "safety_stock"]]

    notes = []
    if not args.clean:
        products, sales, suppliers, notes = inject_issues(products, sales, suppliers)

    products.to_csv(f"{args.out}/dim_product.csv", index=False)
    warehouses_df.to_csv(f"{args.out}/dim_warehouse.csv", index=False)
    suppliers.to_csv(f"{args.out}/dim_supplier.csv", index=False)
    reorder.to_csv(f"{args.out}/dim_reorder_level.csv", index=False)
    sales.to_csv(f"{args.out}/fact_sales.csv", index=False)
    snapshot.to_csv(f"{args.out}/fact_inventory_snapshot.csv", index=False)
    pos.to_csv(f"{args.out}/fact_purchase_orders.csv", index=False)
    batches.to_csv(f"{args.out}/fact_inventory_batches.csv", index=False)

    print(f"Written to {args.out}/  (as-of date for batches: {AS_OF})")
    for name, df in [("products", products), ("warehouses", warehouses_df),
                     ("suppliers", suppliers), ("reorder levels", reorder),
                     ("sales", sales), ("inventory snapshots", snapshot),
                     ("purchase orders", pos), ("inventory batches", batches)]:
        print(f"  {name:<20}{len(df):>9,} rows")
    if notes:
        print("\nInjected data-quality issues (find them in Power Query!):")
        for n in notes:
            print("  -", n)


if __name__ == "__main__":
    main()
