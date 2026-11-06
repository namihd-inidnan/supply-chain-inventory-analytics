-- 05_monthly_revenue.sql
-- Monthly revenue and gross margin %.
SELECT TO_CHAR(s.order_date, 'YYYY-MM') AS sales_month,
       ROUND(SUM(s.revenue), 0) AS revenue,
       ROUND(100 * (SUM(s.revenue) - SUM(s.quantity * p.unit_cost)) / SUM(s.revenue), 1) AS gross_margin_pct
FROM fact_sales_clean s
JOIN v_product p ON p.product_id = s.product_id
GROUP BY 1
ORDER BY 1;
