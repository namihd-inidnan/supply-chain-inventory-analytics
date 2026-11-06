-- 01_clean_views.sql
-- Data cleaning in SQL (mirrors the Power Query steps).

-- Remove exact duplicate sales rows
CREATE TABLE fact_sales_clean AS SELECT DISTINCT * FROM fact_sales;

-- Standardise category text (trim + uppercase)
CREATE VIEW v_product AS
SELECT product_id, product_name, UPPER(TRIM(category)) AS category,
       brand, unit_cost, unit_price, supplier_id
FROM dim_product;

-- Fill missing lead times with the rounded average and flag them
CREATE VIEW v_supplier AS
SELECT supplier_id, supplier_name,
       COALESCE(lead_time_days, ROUND(AVG(lead_time_days) OVER ()))::INT AS lead_time_days,
       (lead_time_days IS NULL) AS lead_time_imputed,
       reliability
FROM dim_supplier;
