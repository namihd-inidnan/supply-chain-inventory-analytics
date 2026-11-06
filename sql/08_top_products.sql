-- 08_top_products.sql
-- Top 3 products by revenue in each category (window function).
SELECT * FROM (
  SELECT p.category, p.product_name, ROUND(SUM(s.revenue), 0) AS revenue,
         RANK() OVER (PARTITION BY p.category ORDER BY SUM(s.revenue) DESC) AS rnk
  FROM fact_sales_clean s JOIN v_product p ON p.product_id = s.product_id
  GROUP BY p.category, p.product_name) t
WHERE rnk <= 3
ORDER BY category, rnk;
