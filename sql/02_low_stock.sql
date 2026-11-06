-- 02_low_stock.sql
-- Items above zero stock but below safety stock at 2026-10-31.
-- (Out-of-stock items: change "> 0 AND ... < r.safety_stock" to "= 0".)
SELECT p.product_name, w.warehouse_name, s.stock_on_hand, r.safety_stock, r.reorder_level
FROM fact_inventory_snapshot s
JOIN v_product p ON p.product_id = s.product_id
JOIN dim_warehouse w ON w.warehouse_id = s.warehouse_id
JOIN dim_reorder_level r ON r.product_id = s.product_id AND r.warehouse_id = s.warehouse_id
WHERE s.snapshot_date = DATE '2026-10-31'
  AND s.stock_on_hand > 0
  AND s.stock_on_hand < r.safety_stock
ORDER BY s.stock_on_hand;
