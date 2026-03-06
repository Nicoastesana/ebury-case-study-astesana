"""Landing-layer task callables used by Airflow DAGs."""

from __future__ import annotations

import logging
import os

import psycopg2

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


def load_csv_to_raw(**_context) -> None:
    """Load the source CSV into ``raw.customer_transactions`` idempotently."""
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
                cur.execute(
                    """
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
                    """
                )

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

                cur.execute(
                    f"""
                    INSERT INTO raw.customer_transactions ({columns})
                    SELECT {columns} FROM tmp_customer_transactions
                    ON CONFLICT (transaction_id)
                    WHERE transaction_id IS NOT NULL
                    DO NOTHING
                    """
                )
                log.info(
                    "Inserted %d rows into raw.customer_transactions (%d skipped as duplicates)",
                    cur.rowcount,
                    total - cur.rowcount,
                )
    finally:
        conn.close()
