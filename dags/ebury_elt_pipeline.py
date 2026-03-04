from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.providers.postgres.hooks.postgres import PostgresHook
import pandas as pd
import os

default_args = {
    'owner': 'ebury',
    'depends_on_past': False,
    'start_date': datetime(2026, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

dag = DAG(
    'ebury_elt_pipeline',
    default_args=default_args,
    description='ELT pipeline for Ebury case study',
    schedule_interval='@daily',
    catchup=False,
    tags=['ebury', 'elt'],
)


def ingest_customer_transactions(**context):
    """
    Ingest customer_transactions.csv into PostgreSQL staging table
    """
    csv_path = '/opt/airflow/data/customer_transactions.csv'

    # Check if file exists
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"CSV file not found at {csv_path}")

    # Read CSV
    df = pd.read_csv(csv_path)

    # Get PostgreSQL connection
    pg_hook = PostgresHook(postgres_conn_id='ebury_dwh')
    engine = pg_hook.get_sqlalchemy_engine()

    # Load to staging table
    df.to_sql(
        name='customer_transactions',
        schema='staging',
        con=engine,
        if_exists='replace',
        index=False,
        method='multi',
        chunksize=1000
    )

    print(f"Loaded {len(df)} rows into staging.customer_transactions")


def run_dbt_models(**context):
    """
    Run dbt models to transform data
    """
    import subprocess
    import os

    os.chdir('/opt/airflow/dbt/ebury_transform')

    # Run dbt
    result = subprocess.run(
        ['dbt', 'run', '--profiles-dir', '.'],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception("dbt run failed")


def run_dbt_tests(**context):
    """
    Run dbt tests for data quality validation
    """
    import subprocess
    import os

    os.chdir('/opt/airflow/dbt/ebury_transform')

    # Run dbt tests
    result = subprocess.run(
        ['dbt', 'test', '--profiles-dir', '.'],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise Exception("dbt tests failed")


# Task 1: Ingest data from CSV to staging
ingest_task = PythonOperator(
    task_id='ingest_customer_transactions',
    python_callable=ingest_customer_transactions,
    dag=dag,
)

# Task 2: Run dbt transformations
dbt_run_task = PythonOperator(
    task_id='run_dbt_models',
    python_callable=run_dbt_models,
    dag=dag,
)

# Task 3: Run dbt tests
dbt_test_task = PythonOperator(
    task_id='run_dbt_tests',
    python_callable=run_dbt_tests,
    dag=dag,
)

# Define task dependencies
ingest_task >> dbt_run_task >> dbt_test_task

