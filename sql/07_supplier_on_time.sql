-- 07_supplier_on_time.sql
-- On-time delivery % per supplier (received orders only).
SELECT su.supplier_name, COUNT(*) AS received_orders,
       ROUND(100 * AVG((po.received_date <= po.expected_date)::INT), 1) AS on_time_pct
FROM fact_purchase_orders po
JOIN v_supplier su ON su.supplier_id = po.supplier_id
WHERE po.received_date IS NOT NULL
GROUP BY su.supplier_name
ORDER BY on_time_pct;
