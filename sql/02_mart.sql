DROP TABLE IF EXISTS mart.fact_sales, mart.fact_targets, mart.dim_date, mart.dim_store,
                     mart.dim_product, mart.dim_employee, mart.dim_customer CASCADE;

-- ========== DIM_DATE ==========
CREATE TABLE mart.dim_date AS
SELECT
    TO_CHAR(d, 'YYYYMMDD')::int        AS date_key,
    d::date                            AS full_date,
    EXTRACT(YEAR FROM d)::int          AS year,
    EXTRACT(QUARTER FROM d)::int       AS quarter,
    EXTRACT(MONTH FROM d)::int         AS month_num,
    TO_CHAR(d, 'Mon')                  AS month_name,
    DATE_TRUNC('month', d)::date       AS month_start,
    EXTRACT(ISODOW FROM d)::int        AS day_of_week,
    TO_CHAR(d, 'Dy')                   AS day_name,
    EXTRACT(ISODOW FROM d) IN (6, 7)   AS is_weekend
FROM generate_series('2025-01-01'::date, '2025-12-31'::date, interval '1 day') AS d;
ALTER TABLE mart.dim_date ADD PRIMARY KEY (date_key);

-- ========== DIM_STORE ==========
CREATE TABLE mart.dim_store AS
SELECT ROW_NUMBER() OVER (ORDER BY store_code)::int AS store_key,
       store_code, store_name, city, province, open_date
FROM staging.stores;
ALTER TABLE mart.dim_store ADD PRIMARY KEY (store_key);

-- ========== DIM_PRODUCT ==========
CREATE TABLE mart.dim_product AS
SELECT ROW_NUMBER() OVER (ORDER BY sku)::int AS product_key,
       sku, product_name, category, unit_price AS list_price
FROM staging.products;
ALTER TABLE mart.dim_product ADD PRIMARY KEY (product_key);

-- ========== DIM_EMPLOYEE ==========
CREATE TABLE mart.dim_employee AS
SELECT ROW_NUMBER() OVER (ORDER BY employee_id)::int AS employee_key,
       employee_id, full_name, role, store_code, hire_date
FROM staging.employees;
ALTER TABLE mart.dim_employee ADD PRIMARY KEY (employee_key);

-- ========== DIM_CUSTOMER (with unknown member) ==========
CREATE TABLE mart.dim_customer AS
SELECT 0 AS customer_key, 'UNKNOWN' AS customer_id, 'Unknown customer' AS full_name,
       NULL::text AS plan_type, NULL::numeric(10,2) AS monthly_fee,
       NULL::date AS signup_date, NULL::text AS status, NULL::text AS home_store
UNION ALL
SELECT ROW_NUMBER() OVER (ORDER BY customer_id)::int,
       customer_id, full_name, plan_type, monthly_fee, signup_date, status, home_store
FROM staging.customers;
ALTER TABLE mart.dim_customer ADD PRIMARY KEY (customer_key);

-- ========== FACT_SALES (grain: one transaction) ==========
CREATE TABLE mart.fact_sales AS
SELECT s.transaction_id,
       TO_CHAR(s.sale_date, 'YYYYMMDD')::int AS date_key,
       ds.store_key, dp.product_key, de.employee_key,
       COALESCE(dc.customer_key, 0)          AS customer_key,
       s.quantity, s.unit_price, s.line_amount, s.is_return
FROM staging.sales s
JOIN mart.dim_store    ds ON ds.store_code  = s.store_code
JOIN mart.dim_product  dp ON dp.sku         = s.sku
JOIN mart.dim_employee de ON de.employee_id = s.employee_id
LEFT JOIN mart.dim_customer dc ON dc.customer_id = s.customer_id;
ALTER TABLE mart.fact_sales ADD PRIMARY KEY (transaction_id);
ALTER TABLE mart.fact_sales
    ADD FOREIGN KEY (date_key)     REFERENCES mart.dim_date (date_key),
    ADD FOREIGN KEY (store_key)    REFERENCES mart.dim_store (store_key),
    ADD FOREIGN KEY (product_key)  REFERENCES mart.dim_product (product_key),
    ADD FOREIGN KEY (employee_key) REFERENCES mart.dim_employee (employee_key),
    ADD FOREIGN KEY (customer_key) REFERENCES mart.dim_customer (customer_key);

-- ========== FACT_TARGETS (grain: one store per month) ==========
CREATE TABLE mart.fact_targets AS
SELECT TO_CHAR(t.month, 'YYYYMMDD')::int AS date_key,
       ds.store_key, t.revenue_target, t.activation_target
FROM staging.targets t
JOIN mart.dim_store ds ON ds.store_code = t.store_code;
ALTER TABLE mart.fact_targets ADD PRIMARY KEY (date_key, store_key);
ALTER TABLE mart.fact_targets
    ADD FOREIGN KEY (date_key)  REFERENCES mart.dim_date (date_key),
    ADD FOREIGN KEY (store_key) REFERENCES mart.dim_store (store_key);