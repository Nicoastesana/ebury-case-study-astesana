-- ============================================
-- Ebury Case Study - Database Initialization
-- ============================================

-- Create schemas
CREATE SCHEMA IF NOT EXISTS raw;
CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant privileges to the main user
GRANT ALL PRIVILEGES ON SCHEMA raw TO ebury_admin;
GRANT ALL PRIVILEGES ON SCHEMA staging TO ebury_admin;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO ebury_admin;

-- -----------------------------------------------
-- Raw layer: stores source data exactly as-is.
-- All columns are VARCHAR to absorb dirty values
-- (malformed dates, non-numeric amounts, etc.).
-- Cleaning happens downstream in dbt/staging.
-- -----------------------------------------------
CREATE TABLE IF NOT EXISTS raw.customer_transactions (
    transaction_id   VARCHAR(50),
    customer_id      VARCHAR(50),
    transaction_date VARCHAR(50),
    product_id       VARCHAR(50),
    product_name     VARCHAR(100),
    quantity         VARCHAR(50),
    price            VARCHAR(50),
    tax              VARCHAR(50),
    loaded_at        TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Partial unique index on non-null transaction_id to support ON CONFLICT upsert
CREATE UNIQUE INDEX IF NOT EXISTS uix_raw_transaction_id
    ON raw.customer_transactions (transaction_id)
    WHERE transaction_id IS NOT NULL;

-- Performance indexes
CREATE INDEX IF NOT EXISTS idx_raw_customer_id       ON raw.customer_transactions (customer_id);
CREATE INDEX IF NOT EXISTS idx_raw_transaction_date  ON raw.customer_transactions (transaction_date);

-- Grant privileges on all current and future objects
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA raw       TO ebury_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA raw       TO ebury_admin;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA staging   TO ebury_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA staging   TO ebury_admin;
GRANT ALL PRIVILEGES ON ALL TABLES    IN SCHEMA analytics TO ebury_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA analytics TO ebury_admin;

ALTER DEFAULT PRIVILEGES IN SCHEMA raw       GRANT ALL ON TABLES TO ebury_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA staging   GRANT ALL ON TABLES TO ebury_admin;
ALTER DEFAULT PRIVILEGES IN SCHEMA analytics GRANT ALL ON TABLES TO ebury_admin;
