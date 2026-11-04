# supply-chain-inventory-analytics
End-to-end supply chain inventory analytics project: data cleaning, star-schema model, KPI measures and an interactive Power BI dashboard for replenishment and inventory review.
Tools
Tool	Used for
Python (pandas, NumPy)	Synthetic data generation
Power Query	Data cleaning and transformation
Power BI	Data model and dashboard
DAX	KPI measures
SQL (MySQL / PostgreSQL)	Analytical queries
Git / GitHub	Version control
Dataset

The generator simulates 12 months of daily operations (Nov 2025 to Oct 2026) for 120 products across 5 warehouses. Each product-warehouse pair follows a reorder-point policy with FIFO stock batches, so the data is internally consistent: sales never exceed available stock, and current stock equals the sum of remaining batches.

A share of product-warehouse pairs is deliberately badly managed (reordering too late, over-ordering, or demand collapsing mid-year) so that low stock, excess stock and ageing inventory appear in the data.

File	Rows (approx.)	Description
dim_product	120	Category, brand, unit cost, unit price, supplier
dim_warehouse	5	Panipat, Mumbai, Bengaluru, Kolkata, Hyderabad
dim_supplier	12	Lead time, reliability
dim_reorder_level	600	Reorder level and safety stock per product and warehouse
fact_sales	180,000	Daily sales with discount and revenue
fact_inventory_snapshot	7,200	Month-end stock on hand and stockout days
fact_purchase_orders	8,600	Order, expected and received dates, quantity, cost
fact_inventory_batches	650	Current stock by received date (used for ageing analysis)

The raw files intentionally contain a few data-quality issues so that the cleaning step is meaningful.

Reproduce the data
bash
pip install pandas numpy
python scripts/generate_dataset.py            # raw files with data-quality issues
python scripts/generate_dataset.py --clean    # no injected issues

The generator uses a fixed random seed, so results are repeatable.

Data cleaning (Power Query)
Table	Issue	Fix
dim_product	Inconsistent spacing and casing in category	Trimmed whitespace and standardised casing
fact_sales	Duplicate rows (same sale_id)	Removed duplicates on sale_id
dim_supplier	2 missing lead_time_days values	Filled with the rounded average lead time of the other suppliers; flagged in a lead_time_imputed column

Assumption: mean imputation is simple, but it hides real differences between suppliers, which is why imputed rows are flagged rather than silently overwritten.

Repository structure
supply-chain-inventory-analytics/
├── data/
│   └── raw/                 # CSV files produced by the generator
├── scripts/
│   └── generate_dataset.py  # synthetic data generator
├── powerbi/
│   └── inventory_analytics.pbix
└── README.md
