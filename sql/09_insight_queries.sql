-- 09_insight_queries.sql
-- Queries used to gather the numbers behind documentation/insights.md
-- As-of date for stock and ageing: 2026-10-31
-- In pgAdmin: highlight ONE query at a time and press F5 (only the last result is shown otherwise).


-- ======================================================================
-- Q0. HEADLINE NUMBERS (one row; compare with your dashboard cards)
-- ======================================================================
WITH sold90 AS (
  SELECT product_id, warehouse_id, SUM(quantity) AS qty90
  FROM fact_sales_clean
  WHERE order_date > DATE '2026-10-31' - 90 AND order_date <= DATE '2026-10-31'
  GROUP BY product_id, warehouse_id),
snap AS (
  SELECT s.stock_on_hand, p.unit_cost, r.safety_stock, COALESCE(x.qty90, 0) AS qty90
  FROM fact_inventory_snapshot s
  JOIN v_product p ON p.product_id = s.product_id
  JOIN dim_reorder_level r ON r.product_id = s.product_id AND r.warehouse_id = s.warehouse_id
  LEFT JOIN sold90 x ON x.product_id = s.product_id AND x.warehouse_id = s.warehouse_id
  WHERE s.snapshot_date = DATE '2026-10-31')
SELECT
  (SELECT ROUND(SUM(revenue), 0) FROM fact_sales_clean)                       AS total_revenue,
  ROUND(SUM(stock_on_hand * unit_cost), 0)                                     AS inventory_value,
  COUNT(*) FILTER (WHERE stock_on_hand = 0)                                    AS out_of_stock_items,
  COUNT(*) FILTER (WHERE stock_on_hand > 0 AND stock_on_hand < safety_stock)   AS low_stock_items,
  COUNT(*) FILTER (WHERE stock_on_hand > 0 AND stock_on_hand > qty90)          AS excess_items,
  ROUND(SUM(stock_on_hand * unit_cost)
        FILTER (WHERE stock_on_hand > 0 AND stock_on_hand > qty90), 0)         AS excess_value,
  (SELECT ROUND(SUM(qty_remaining * unit_cost), 0) FROM fact_inventory_batches) AS batch_value,
  (SELECT ROUND(SUM(qty_remaining * unit_cost)
          FILTER (WHERE DATE '2026-10-31' - received_date > 90), 0)
     FROM fact_inventory_batches)                                              AS ageing_value_over_90d
FROM snap;


-- ======================================================================
-- Q1. EXCESS STOCK BY WAREHOUSE
-- ======================================================================
WITH sold90 AS (
  SELECT product_id, warehouse_id, SUM(quantity) AS qty90
  FROM fact_sales_clean
  WHERE order_date > DATE '2026-10-31' - 90 AND order_date <= DATE '2026-10-31'
  GROUP BY product_id, warehouse_id)
SELECT w.warehouse_name, COUNT(*) AS excess_items,
       ROUND(SUM(s.stock_on_hand * p.unit_cost), 0) AS excess_value
FROM fact_inventory_snapshot s
JOIN v_product p ON p.product_id = s.product_id
JOIN dim_warehouse w ON w.warehouse_id = s.warehouse_id
LEFT JOIN sold90 x ON x.product_id = s.product_id AND x.warehouse_id = s.warehouse_id
WHERE s.snapshot_date = DATE '2026-10-31'
  AND s.stock_on_hand > 0 AND s.stock_on_hand > COALESCE(x.qty90, 0)
GROUP BY w.warehouse_name
ORDER BY excess_value DESC;


-- ======================================================================
-- Q1b. EXCESS STOCK BY CATEGORY
-- ======================================================================
WITH sold90 AS (
  SELECT product_id, warehouse_id, SUM(quantity) AS qty90
  FROM fact_sales_clean
  WHERE order_date > DATE '2026-10-31' - 90 AND order_date <= DATE '2026-10-31'
  GROUP BY product_id, warehouse_id)
SELECT p.category, COUNT(*) AS excess_items,
       ROUND(SUM(s.stock_on_hand * p.unit_cost), 0) AS excess_value
FROM fact_inventory_snapshot s
JOIN v_product p ON p.product_id = s.product_id
LEFT JOIN sold90 x ON x.product_id = s.product_id AND x.warehouse_id = s.warehouse_id
WHERE s.snapshot_date = DATE '2026-10-31'
  AND s.stock_on_hand > 0 AND s.stock_on_hand > COALESCE(x.qty90, 0)
GROUP BY p.category
ORDER BY excess_value DESC;


-- ======================================================================
-- Q2. TOP 10 REPLENISHMENT PRIORITIES (below safety stock, ranked by daily revenue at risk)
-- ======================================================================
WITH sales90 AS (
  SELECT product_id, warehouse_id, SUM(quantity) / 90.0 AS avg_daily
  FROM fact_sales_clean
  WHERE order_date > DATE '2026-10-31' - 90 AND order_date <= DATE '2026-10-31'
  GROUP BY product_id, warehouse_id)
SELECT p.product_name, w.warehouse_name, s.stock_on_hand, r.safety_stock,
       ROUND(a.avg_daily, 1) AS avg_daily_units,
       ROUND(a.avg_daily * p.unit_price, 0) AS daily_revenue_at_risk
FROM fact_inventory_snapshot s
JOIN v_product p ON p.product_id = s.product_id
JOIN dim_warehouse w ON w.warehouse_id = s.warehouse_id
JOIN dim_reorder_level r ON r.product_id = s.product_id AND r.warehouse_id = s.warehouse_id
JOIN sales90 a ON a.product_id = s.product_id AND a.warehouse_id = s.warehouse_id
WHERE s.snapshot_date = DATE '2026-10-31' AND s.stock_on_hand < r.safety_stock
ORDER BY daily_revenue_at_risk DESC
LIMIT 10;


-- ======================================================================
-- Q3. AGEING STOCK (> 90 DAYS) BY CATEGORY
-- ======================================================================
SELECT p.category, ROUND(SUM(b.qty_remaining * b.unit_cost), 0) AS ageing_value
FROM fact_inventory_batches b
JOIN v_product p ON p.product_id = b.product_id
WHERE DATE '2026-10-31' - b.received_date > 90
GROUP BY p.category
ORDER BY ageing_value DESC;


-- ======================================================================
-- Q4. SUPPLIER ON-TIME % AND STOCKOUT DAYS
-- ======================================================================
WITH ot AS (
  SELECT supplier_id,
         ROUND(100 * AVG((received_date <= expected_date)::INT), 1) AS on_time_pct,
         ROUND(AVG(received_date - expected_date), 1) AS avg_days_late
  FROM fact_purchase_orders WHERE received_date IS NOT NULL
  GROUP BY supplier_id),
so AS (
  SELECT p.supplier_id, SUM(s.stockout_days) AS stockout_days
  FROM fact_inventory_snapshot s JOIN v_product p ON p.product_id = s.product_id
  GROUP BY p.supplier_id)
SELECT su.supplier_name, ot.on_time_pct, ot.avg_days_late, so.stockout_days
FROM v_supplier su
JOIN ot ON ot.supplier_id = su.supplier_id
JOIN so ON so.supplier_id = su.supplier_id
ORDER BY ot.on_time_pct;


-- ======================================================================
-- Q5. SEASONALITY: MONTHLY REVENUE
-- ======================================================================
SELECT TO_CHAR(order_date, 'YYYY-MM') AS sales_month, ROUND(SUM(revenue), 0) AS revenue
FROM fact_sales_clean
GROUP BY 1
ORDER BY 1;


-- ======================================================================
-- Q6. INVENTORY TURNOVER BY WAREHOUSE
-- ======================================================================
WITH cogs AS (
  SELECT s.warehouse_id, SUM(s.quantity * p.unit_cost) AS cogs
  FROM fact_sales_clean s JOIN v_product p ON p.product_id = s.product_id
  GROUP BY s.warehouse_id),
monthly_inv AS (
  SELECT sn.warehouse_id, sn.snapshot_date, SUM(sn.stock_on_hand * p.unit_cost) AS inv_value
  FROM fact_inventory_snapshot sn JOIN v_product p ON p.product_id = sn.product_id
  GROUP BY sn.warehouse_id, sn.snapshot_date),
avg_inv AS (
  SELECT warehouse_id, AVG(inv_value) AS avg_inv FROM monthly_inv GROUP BY warehouse_id)
SELECT w.warehouse_name, ROUND(c.cogs / a.avg_inv, 2) AS inventory_turnover
FROM cogs c
JOIN avg_inv a ON a.warehouse_id = c.warehouse_id
JOIN dim_warehouse w ON w.warehouse_id = c.warehouse_id
ORDER BY inventory_turnover DESC;


-- ======================================================================
-- Q7. GROSS MARGIN BY CATEGORY
-- ======================================================================
SELECT p.category,
       ROUND(SUM(s.revenue), 0) AS revenue,
       ROUND(100 * (SUM(s.revenue) - SUM(s.quantity * p.unit_cost)) / SUM(s.revenue), 1) AS gross_margin_pct
FROM fact_sales_clean s
JOIN v_product p ON p.product_id = s.product_id
GROUP BY p.category
ORDER BY revenue DESC;
