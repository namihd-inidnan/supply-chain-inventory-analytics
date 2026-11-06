-- 00_schema.sql
-- PostgreSQL schema for the Supply Chain Inventory Analytics project.
-- Load the CSVs from data/raw/ into these tables (pgAdmin: right-click table > Import/Export Data).
-- Primary keys are omitted on purpose: the raw sales file contains duplicate sale_id rows,
-- which are removed in 01_clean_views.sql.

CREATE TABLE dim_product (
  product_id VARCHAR(10), product_name VARCHAR(100), category VARCHAR(50),
  brand VARCHAR(50), unit_cost NUMERIC(10,2), unit_price NUMERIC(10,2), supplier_id VARCHAR(10));

CREATE TABLE dim_warehouse (
  warehouse_id VARCHAR(10), warehouse_name VARCHAR(50), city VARCHAR(50),
  state VARCHAR(50), region VARCHAR(20));

CREATE TABLE dim_supplier (
  supplier_id VARCHAR(10), supplier_name VARCHAR(60),
  lead_time_days NUMERIC(5,1), reliability NUMERIC(4,2));

CREATE TABLE dim_reorder_level (
  product_id VARCHAR(10), warehouse_id VARCHAR(10), reorder_level NUMERIC(10,1), safety_stock INT);

CREATE TABLE fact_sales (
  sale_id VARCHAR(12), order_date DATE, product_id VARCHAR(10), warehouse_id VARCHAR(10),
  quantity INT, unit_price NUMERIC(10,2), discount_pct NUMERIC(5,1), revenue NUMERIC(12,2));

CREATE TABLE fact_inventory_snapshot (
  snapshot_date DATE, product_id VARCHAR(10), warehouse_id VARCHAR(10),
  stock_on_hand INT, stockout_days INT);

CREATE TABLE fact_purchase_orders (
  po_id VARCHAR(12), product_id VARCHAR(10), warehouse_id VARCHAR(10), supplier_id VARCHAR(10),
  order_date DATE, expected_date DATE, received_date DATE, quantity INT, unit_cost NUMERIC(10,2));

CREATE TABLE fact_inventory_batches (
  batch_id VARCHAR(12), product_id VARCHAR(10), warehouse_id VARCHAR(10), received_date DATE,
  qty_received INT, qty_remaining INT, unit_cost NUMERIC(10,2), source VARCHAR(15));
