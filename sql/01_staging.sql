-- ========== SALES ==========
DROP TABLE IF EXISTS staging.sales;
CREATE TABLE staging.sales AS
WITH cleaned AS (
    SELECT
        transaction_id,
        CASE WHEN "date" ~ '^\d{2}/\d{2}/\d{4}$' THEN TO_DATE("date", 'DD/MM/YYYY')
             ELSE "date"::date END                       AS sale_date,
        UPPER(TRIM(store_code))                          AS store_code,
        employee_id,
        sku,
        quantity::int                                    AS quantity,
        REPLACE(unit_price, '$', '')::numeric(10,2)      AS unit_price,
        NULLIF(customer_id, '')                          AS customer_id
    FROM raw.sales
),
dedup AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY transaction_id ORDER BY transaction_id) AS rn
    FROM cleaned
)
SELECT transaction_id, sale_date, store_code, employee_id, sku,
       quantity, unit_price,
       quantity * unit_price AS line_amount,
       quantity < 0          AS is_return,
       customer_id
FROM dedup
WHERE rn = 1;
ALTER TABLE staging.sales ADD PRIMARY KEY (transaction_id);

-- ========== STORES ==========
DROP TABLE IF EXISTS staging.stores;
CREATE TABLE staging.stores AS
SELECT UPPER(TRIM(store_code)) AS store_code, store_name, city, province,
       open_date::timestamp::date AS open_date
FROM raw.stores;
ALTER TABLE staging.stores ADD PRIMARY KEY (store_code);

-- ========== PRODUCTS ==========
DROP TABLE IF EXISTS staging.products;
CREATE TABLE staging.products AS
SELECT sku, category, product_name, unit_price::numeric(10,2) AS unit_price
FROM raw.products;
ALTER TABLE staging.products ADD PRIMARY KEY (sku);

-- ========== EMPLOYEES ==========
DROP TABLE IF EXISTS staging.employees;
CREATE TABLE staging.employees AS
SELECT employee_id, full_name, UPPER(TRIM(store_code)) AS store_code, role,
       hire_date::timestamp::date AS hire_date
FROM raw.employees;
ALTER TABLE staging.employees ADD PRIMARY KEY (employee_id);

-- ========== CUSTOMERS (JSON) ==========
DROP TABLE IF EXISTS staging.customers;
CREATE TABLE staging.customers AS
SELECT DISTINCT ON (record->>'id')
    record->>'id'                              AS customer_id,
    record->>'name'                            AS full_name,
    record->'contact'->>'email'                AS email,
    record->'contact'->>'phone'                AS phone,
    record->'plan'->>'type'                    AS plan_type,
    (record->'plan'->>'monthly_fee')::numeric(10,2) AS monthly_fee,
    (record->>'signup_date')::date             AS signup_date,
    record->>'status'                          AS status,
    record->>'home_store'                      AS home_store
FROM raw.customers
ORDER BY record->>'id';
ALTER TABLE staging.customers ADD PRIMARY KEY (customer_id);