"""
Ebury ELT Pipeline
==================
Full ELT pipeline orchestrated by Airflow:

  Task 1 — load_csv_to_raw
    Streams customer_transactions.csv into PostgreSQL via COPY FROM STDIN.
    Uses a temporary staging table for idempotency (ON CONFLICT DO NOTHING).

  Task 2 — dbt_run
    Runs all dbt models in dependency order:
      raw → staging.stg_customer_transactions (view)
           → analytics.dim_customers          (table)
           → analytics.fact_transactions      (table)
           → analytics.agg_by_customer        (table)
           → analytics.agg_by_customer_product(table)
           → analytics.agg_by_product         (table)
           → auditing.audit_errors_by_*       (tables)

  Task 3 — dbt_test
    Runs all dbt schema tests (unique, not_null, relationships,
    accepted_values) against the materialised models.

Dependencies:  load_csv_to_raw >> dbt_run >> dbt_test

Retries: 2 attempts with 5-minute delay between them.

Notifications: on_failure_callback logs a structured error message for every
failed task (dag, task, run_id, exception, log URL). Extend notify_failure()
to send Slack / email / PagerDuty alerts as needed.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timedelta

import psycopg2
from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator

log = logging.getLogger(__name__)

CSV_PATH = "/opt/airflow/data/customer_transactions.csv"


# ---------------------------------------------------------------------------
# Notification callback — fired on any task failure
# ---------------------------------------------------------------------------
def notify_failure(context: dict) -> None:
    """
    Log a structured error message when a task fails.

    Extend this function to send Slack/email alerts by replacing the
    log.error call with your preferred notification library.
    """
    dag_id   = context["dag"].dag_id
    task_id  = context["task_instance"].task_id
    run_id   = context["run_id"]
    log_url  = context["task_instance"].log_url
    exception = context.get("exception", "n/a")

    log.error(
        "TASK FAILED | dag=%s | task=%s | run_id=%s | exception=%s | logs=%s",
        dag_id, task_id, run_id, exception, log_url,
    )
DBT_PROJECT_DIR = "/opt/airflow/dbt/ebury_transform"

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

# ---------------------------------------------------------------------------
# Default args — applied to every task
# ---------------------------------------------------------------------------
default_args = {
    "owner": "ebury",
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
    "email_on_failure": False,        # set to True and configure SMTP for alerts
    "email_on_retry": False,
    "on_failure_callback": notify_failure,
}


# ---------------------------------------------------------------------------
# Task 1: load CSV → raw.customer_transactions
# ---------------------------------------------------------------------------
def load_csv_to_raw(**_context) -> None:
    """
    Stream the CSV into PostgreSQL via COPY FROM STDIN.

    Pattern
    -------
    1. CREATE TEMP TABLE (no constraints)  → safe for COPY
    2. COPY FROM STDIN                     → O(1) memory, maximum speed
    3. INSERT INTO raw ON CONFLICT DO NOTHING → idempotent
    """
    conn = psycopg2.connect(
        host=os.environ["POSTGRES_HOST"],
        port=int(os.environ.get("POSTGRES_PORT", 5432)),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
    )
    try:
        with conn:
            with conn.cursor() as cur:

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

                cur.execute(f"""
                    INSERT INTO raw.customer_transactions ({columns})
                    SELECT {columns} FROM tmp_customer_transactions
                    ON CONFLICT (transaction_id)
                    WHERE transaction_id IS NOT NULL
                    DO NOTHING
                """)
                log.info(
                    "Inserted %d rows into raw.customer_transactions "
                    "(%d skipped as duplicates)",
                    cur.rowcount, total - cur.rowcount,
                )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# DAG definition
# ---------------------------------------------------------------------------
with DAG(
    dag_id="ebury_elt_pipeline",
    default_args=default_args,
    description="ELT: ingest CSV → raw PostgreSQL, then trigger dbt transformations",
    schedule_interval="@daily",
    start_date=datetime(2023, 7, 1),
    catchup=False,
    tags=["ebury", "elt", "dbt"],
) as dag:

    # ── Task 1: ingest ───────────────────────────────────────────────────────
    t_load = PythonOperator(
        task_id="load_csv_to_raw",
        python_callable=load_csv_to_raw,
    )

    # ── Task 2: dbt run ──────────────────────────────────────────────────────
    t_dbt_run = BashOperator(
        task_id="dbt_run",
        bash_command=(
            f"dbt run "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROJECT_DIR} "
            f"--no-use-colors"
        ),
        env={
            "POSTGRES_HOST":     os.environ.get("POSTGRES_HOST", "postgres"),
            "POSTGRES_PORT":     os.environ.get("POSTGRES_PORT", "5432"),
            "POSTGRES_DB":       os.environ.get("POSTGRES_DB", "ebury_db"),
            "POSTGRES_USER":     os.environ.get("POSTGRES_USER", "ebury_admin"),
            "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "PATH": "/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin",
        },
        append_env=True,
    )

    # ── Task 3: dbt test ─────────────────────────────────────────────────────
    t_dbt_test = BashOperator(
        task_id="dbt_test",
        bash_command=(
            f"dbt test "
            f"--project-dir {DBT_PROJECT_DIR} "
            f"--profiles-dir {DBT_PROJECT_DIR} "
            f"--no-use-colors"
        ),
        env={
            "POSTGRES_HOST":     os.environ.get("POSTGRES_HOST", "postgres"),
            "POSTGRES_PORT":     os.environ.get("POSTGRES_PORT", "5432"),
            "POSTGRES_DB":       os.environ.get("POSTGRES_DB", "ebury_db"),
            "POSTGRES_USER":     os.environ.get("POSTGRES_USER", "ebury_admin"),
            "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
            "PATH": "/home/airflow/.local/bin:/usr/local/bin:/usr/bin:/bin",
        },
        append_env=True,
    )

    # ── Dependencies ─────────────────────────────────────────────────────────
    t_load >> t_dbt_run >> t_dbt_test
