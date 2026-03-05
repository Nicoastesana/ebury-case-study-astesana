"""
Ebury ELT Pipeline — Extract & Load
=====================================
Loads customer_transactions.csv into raw.customer_transactions using the
most efficient PostgreSQL bulk-load pattern:

  1. COPY FROM STDIN → temporary table (no constraints, maximum speed)
  2. INSERT INTO raw ... SELECT FROM temp ON CONFLICT DO NOTHING (idempotent)
  3. DROP temporary table

Why this pattern?
-----------------
- COPY FROM STDIN streams the file directly into PostgreSQL with constant
  memory usage regardless of file size — no intermediate list in RAM.
- The temp table has no indexes or constraints, so COPY never fails on
  duplicate transaction_ids (safe to re-run the DAG multiple times).
- The final INSERT handles deduplication via ON CONFLICT DO NOTHING on the
  partial unique index defined in 01_init.sql.
- All data quality issues in the source file (malformed dates, non-numeric
  prices, missing IDs, "T"-prefixed transaction IDs, etc.) are preserved
  in the raw layer; cleaning is delegated to dbt staging models.

Schedule: daily at midnight UTC.
"""

from __future__ import annotations

import io
import logging
import os
from datetime import datetime, timedelta

import psycopg2
from airflow import DAG
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

CSV_PATH = "/opt/airflow/data/customer_transactions.csv"

RAW_COLUMNS = (
    "transaction_id",
    "customer_id",
    "transaction_date",
    "product_id",
    "product_name",
    "quantity",
    "price",
    "tax",
)

default_args = {
    "owner": "ebury",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_conn() -> psycopg2.extensions.connection:
    return psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )


# ---------------------------------------------------------------------------
# Task callable
# ---------------------------------------------------------------------------

def load_csv_to_raw(**_context) -> None:
    """
    Stream the CSV into PostgreSQL via COPY FROM STDIN.

    Steps
    -----
    1. Create a session-scoped temporary table (identical schema to
       raw.customer_transactions but with no indexes or constraints).
    2. COPY the CSV file directly into the temp table — O(1) memory.
    3. INSERT from the temp table into raw.customer_transactions with
       ON CONFLICT DO NOTHING so re-runs are safe.
    4. Log how many rows were inserted vs skipped as duplicates.
    """
    conn = _get_conn()
    try:
        with conn:
            with conn.cursor() as cur:

                # -- 1. Temporary landing table (no constraints) ------------
                cur.execute("""
                    CREATE TEMP TABLE tmp_customer_transactions (
                        transaction_id   VARCHAR(50),
                        customer_id      VARCHAR(50),
                        transaction_date VARCHAR(50),
                        product_id       VARCHAR(50),
                        product_name     VARCHAR(100),
                        quantity         VARCHAR(50),
                        price            VARCHAR(50),
                        tax              VARCHAR(50)
                    ) ON COMMIT DROP
                """)

                # -- 2. COPY FROM STDIN — streams file, constant memory -----
                columns = ", ".join(RAW_COLUMNS)
                copy_sql = f"""
                    COPY tmp_customer_transactions ({columns})
                    FROM STDIN
                    WITH (FORMAT csv, HEADER true, NULL '')
                """
                with open(CSV_PATH, "r", encoding="utf-8") as fh:
                    cur.copy_expert(copy_sql, fh)

                cur.execute("SELECT COUNT(*) FROM tmp_customer_transactions")
                total = cur.fetchone()[0]
                log.info("COPY loaded %d rows into temp table", total)

                # -- 3. Idempotent insert into raw layer --------------------
                cur.execute(f"""
                    INSERT INTO raw.customer_transactions ({columns})
                    SELECT {columns}
                    FROM tmp_customer_transactions
                    ON CONFLICT (transaction_id)
                    WHERE transaction_id IS NOT NULL
                    DO NOTHING
                """)
                inserted = cur.rowcount

                skipped = total - inserted
                log.info(
                    "Inserted %d rows into raw.customer_transactions "
                    "(%d skipped as duplicates)",
                    inserted, skipped,
                )

    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------

with DAG(
    dag_id="ebury_elt_pipeline",
    default_args=default_args,
    description=(
        "ELT pipeline: stream customer_transactions CSV into the raw "
        "PostgreSQL layer via COPY FROM STDIN + idempotent upsert"
    ),
    schedule_interval="@daily",
    start_date=datetime(2023, 7, 1),
    catchup=False,
    tags=["ebury", "elt", "raw"],
) as dag:

    PythonOperator(
        task_id="load_csv_to_raw",
        python_callable=load_csv_to_raw,
    )
