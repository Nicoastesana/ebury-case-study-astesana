-- ============================================
-- Create Airflow Metadata Database and User
-- ============================================
-- Runs as the superuser (ebury_admin) via docker-entrypoint-initdb.d.
-- PostgreSQL 15 removed the default CREATE privilege on the public schema,
-- so we must grant it explicitly after creating the airflow database.

-- Create the airflow database (only if it doesn't already exist)
SELECT 'CREATE DATABASE airflow'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = 'airflow')\gexec

-- Create the airflow role (only if it doesn't already exist)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'airflow') THEN
    CREATE USER airflow WITH PASSWORD 'airflow';
  END IF;
END
$$;

-- Full ownership of the airflow database
GRANT ALL PRIVILEGES ON DATABASE airflow TO airflow;

-- PostgreSQL 15+: grant CREATE on the public schema inside the airflow DB.
-- \connect switches context; the subsequent GRANTs execute there.
\connect airflow
GRANT ALL ON SCHEMA public TO airflow;
ALTER DATABASE airflow OWNER TO airflow;
