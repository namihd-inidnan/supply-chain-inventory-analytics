-- 06_turnover_by_warehouse.sql
-- Inventory turnover = COGS / average month-end inventory value, per warehouse.
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
