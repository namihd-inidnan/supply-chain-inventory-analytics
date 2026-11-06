-- 03_excess_stock.sql
-- Stock larger than the last 90 days of sales, as of 2026-10-31.
WITH sold90 AS (
  SELECT product_id, warehouse_id, SUM(quantity) AS qty90
  FROM fact_sales_clean
  WHERE order_date > DATE '2026-10-31' - 90 AND order_date <= DATE '2026-10-31'
  GROUP BY product_id, warehouse_id)
SELECT p.product_name, w.warehouse_name, s.stock_on_hand,
       COALESCE(x.qty90, 0) AS sold_last_90d,
       ROUND(s.stock_on_hand * p.unit_cost, 2) AS stock_value
FROM fact_inventory_snapshot s
JOIN v_product p ON p.product_id = s.product_id
JOIN dim_warehouse w ON w.warehouse_id = s.warehouse_id
LEFT JOIN sold90 x ON x.product_id = s.product_id AND x.warehouse_id = s.warehouse_id
WHERE s.snapshot_date = DATE '2026-10-31'
  AND s.stock_on_hand > 0
  AND s.stock_on_hand > COALESCE(x.qty90, 0)
ORDER BY stock_value DESC;
