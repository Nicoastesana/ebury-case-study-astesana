# Full Star Schema — Proposed Design

## Overview

The complete star schema for the `customer_transactions` dataset would consist
of one fact table and three dimension tables.

---

## fact_transactions

The **grain** is one row per transaction.

| Column           | Type      | Description                        |
|------------------|-----------|------------------------------------|
| transaction_id   | INTEGER   | Primary key                        |
| customer_id      | INTEGER   | FK → dim_customers                 |
| product_id       | INTEGER   | FK → dim_products                  |
| date_id          | DATE      | FK → dim_date                      |
| quantity         | INTEGER   | Units purchased                    |
| unit_price       | NUMERIC   | Price per unit                     |
| tax              | NUMERIC   | Tax charged                        |
| gross_amount     | NUMERIC   | unit_price × quantity              |
| total_amount     | NUMERIC   | gross_amount + tax                 |
| tax_rate_pct     | NUMERIC   | tax / gross_amount × 100           |
| loaded_at        | TIMESTAMP | When the row entered the warehouse |

---

## dim_customers

One row per customer. Descriptive attributes and activity summary.

| Column                    | Type    | Description                              |
|---------------------------|---------|------------------------------------------|
| customer_id               | INTEGER | Primary key                              |
| first_transaction_date    | DATE    | Date of first purchase                   |
| last_transaction_date     | DATE    | Date of most recent purchase             |
| total_transactions        | INTEGER | Count of valid transactions              |
| distinct_products_purchased | INTEGER | Number of unique products bought       |
| total_gross_amount        | NUMERIC | Sum of gross_amount across transactions  |
| total_tax_paid            | NUMERIC | Sum of tax across transactions           |
| total_amount_incl_tax     | NUMERIC | Sum of total_amount across transactions  |
| avg_unit_price            | NUMERIC | Average unit price across transactions   |

---

## dim_products

One row per product. Normalises product attributes out of the fact table.

| Column       | Type    | Description           |
|--------------|---------|-----------------------|
| product_id   | INTEGER | Primary key           |
| product_name | VARCHAR | Human-readable name   |

> **Why this matters:** without `dim_products`, `product_name` is repeated in
> every row of `fact_transactions`. If a product is renamed, you'd need to
> update millions of rows. With a dimension table, you update one row.

---

## dim_date

One row per calendar date. Standard in every data warehouse — avoids computing
date parts in every query and enables consistent time-based slicing.

| Column       | Type    | Description                        |
|--------------|---------|------------------------------------|
| date_id      | DATE    | Primary key                        |
| day          | INTEGER | Day of month (1–31)                |
| month        | INTEGER | Month number (1–12)                |
| month_name   | VARCHAR | e.g. "July"                        |
| quarter      | INTEGER | Quarter (1–4)                      |
| year         | INTEGER | e.g. 2023                          |
| day_of_week  | VARCHAR | e.g. "Tuesday"                     |
| is_weekend   | BOOLEAN | TRUE for Saturday and Sunday       |

> **Why this matters:** instead of writing `EXTRACT(month FROM transaction_date)`
> in every query, analysts simply filter on `dim_date.month = 7`. It also
> allows adding business-specific flags (e.g. `is_holiday`, `is_quarter_end`)
> in one place.

---

## Relationships

```
dim_customers (1) ────── (N) fact_transactions (N) ────── (1) dim_products
                                     │
                                    (N)
                                     │
                              dim_date (1)
```

---

## Why the current implementation only has dim_customers

The dataset only provides `customer_id`, `product_id`, and `transaction_date`
as dimensional attributes. With richer source data we would populate all three
dimensions. The current design is pragmatic — it implements what the data
supports and documents what would be added in a production system.
