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
    accepted_values) against the materialized models.

Dependencies:  load_csv_to_raw >> dbt_run >> dbt_test

Retries: 2 attempts with 5-minute delay between them.

Notifications: on_failure_callback logs a structured error message for every
failed task (dag, task, run_id, exception, log URL). Extend notify_failure()
to send Slack / email / PagerDuty alerts as needed.
"""

from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from pipeline_tasks.landing import load_csv_to_raw
from pipeline_tasks.notifications import notify_failure

DBT_PROJECT_DIR = "/opt/airflow/dbt/ebury_transform"

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
