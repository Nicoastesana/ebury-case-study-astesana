-- Create a separate database for the data warehouse
CREATE DATABASE ebury_dwh;

-- Connect to the new database and create schema
\c ebury_dwh;

CREATE SCHEMA IF NOT EXISTS staging;
CREATE SCHEMA IF NOT EXISTS analytics;

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE ebury_dwh TO airflow;
GRANT ALL PRIVILEGES ON SCHEMA staging TO airflow;
GRANT ALL PRIVILEGES ON SCHEMA analytics TO airflow;

