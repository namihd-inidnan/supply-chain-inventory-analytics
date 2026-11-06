-- 04_ageing.sql
-- Inventory value by age bucket, as of 2026-10-31.
SELECT CASE
         WHEN age <= 30  THEN '0-30 days'
         WHEN age <= 60  THEN '31-60 days'
         WHEN age <= 90  THEN '61-90 days'
         WHEN age <= 180 THEN '91-180 days'
         ELSE '180+ days' END AS age_bucket,
       ROUND(SUM(qty_remaining * unit_cost), 2) AS stock_value
FROM (SELECT *, DATE '2026-10-31' - received_date AS age FROM fact_inventory_batches) b
GROUP BY 1
ORDER BY MIN(age);
