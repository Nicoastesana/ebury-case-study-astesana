# Star Schema — Ebury Case Study

## Current Schema

```
                        ┌─────────────────────────────────────────┐
                        │           fact_transactions             │
                        ├─────────────────────────┬───────────────┤
                        │ transaction_id          │ INTEGER (PK)  │
              ┌─────────┤ customer_id             │ INTEGER (FK)  │
              │         │ product_id              │ INTEGER       │
              │         │ product_name            │ VARCHAR       │
              │         │ transaction_date        │ DATE          │
              │         │ quantity                │ INTEGER       │
              │         │ unit_price              │ NUMERIC       │
              │         │ tax                     │ NUMERIC       │
              │         │ gross_amount            │ NUMERIC       │
              │         │ total_amount            │ NUMERIC       │
              │         │ tax_rate_pct            │ NUMERIC       │
              │         │ loaded_at               │ TIMESTAMP     │
              │         └─────────────────────────┴───────────────┘
              │
              ▼
┌─────────────────────────────────────────┐
│             dim_customers               │
├─────────────────────────┬───────────────┤
│ customer_id             │ INTEGER (PK)  │
│ first_transaction_date  │ DATE          │
│ last_transaction_date   │ DATE          │
│ total_transactions      │ INTEGER       │
│ distinct_products_purch │ INTEGER       │
│ total_gross_amount      │ NUMERIC       │
│ total_tax_paid          │ NUMERIC       │
│ total_amount_incl_tax   │ NUMERIC       │
│ avg_unit_price          │ NUMERIC       │
└─────────────────────────┴───────────────┘
```

## Proposed Full Schema

```
                              ┌─────────────────────────────────────────┐
                              │           fact_transactions             │
                              ├─────────────────────────┬───────────────┤
                ┌─────────────┤ transaction_id          │ INTEGER (PK)  │
                │  ┌──────────┤ customer_id             │ INTEGER (FK)  │
                │  │  ┌───────┤ product_id              │ INTEGER (FK)  │
                │  │  │  ┌────┤ date_id                 │ DATE    (FK)  │
                │  │  │  │    │ quantity                │ INTEGER       │
                │  │  │  │    │ unit_price              │ NUMERIC       │
                │  │  │  │    │ tax                     │ NUMERIC       │
                │  │  │  │    │ gross_amount            │ NUMERIC       │
                │  │  │  │    │ total_amount            │ NUMERIC       │
                │  │  │  │    │ tax_rate_pct            │ NUMERIC       │
                │  │  │  │    │ loaded_at               │ TIMESTAMP     │
                │  │  │  │    └─────────────────────────┴───────────────┘
                │  │  │  │
                │  │  │  │    ┌─────────────────────────────────────────┐
                │  │  │  │    │               dim_date                  │
                │  │  │  │    ├─────────────────────────┬───────────────┤
                │  │  │  └───►│ date_id                 │ DATE    (PK)  │
                │  │  │       │ day                     │ INTEGER       │
                │  │  │       │ month                   │ INTEGER       │
                │  │  │       │ quarter                 │ INTEGER       │
                │  │  │       │ year                    │ INTEGER       │
                │  │  │       │ day_of_week             │ VARCHAR       │
                │  │  │       │ is_weekend              │ BOOLEAN       │
                │  │  │       └─────────────────────────┴───────────────┘
                │  │  │
                │  │  │       ┌─────────────────────────────────────────┐
                │  │  │       │             dim_products                │
                │  │  │       ├─────────────────────────┬───────────────┤
                │  │  └──────►│ product_id              │ INTEGER (PK)  │
                │  │          │ product_name            │ VARCHAR       │
                │  │          └─────────────────────────┴───────────────┘
                │  │
                │  │          ┌─────────────────────────────────────────┐
                │  │          │             dim_customers               │
                │  │          ├─────────────────────────┬───────────────┤
                │  └─────────►│ customer_id             │ INTEGER (PK)  │
                │             │ first_transaction_date  │ DATE          │
                │             │ last_transaction_date   │ DATE          │
                │             │ total_transactions      │ INTEGER       │
                │             │ distinct_products_purch │ INTEGER       │
                │             │ total_gross_amount      │ NUMERIC       │
                │             │ total_tax_paid          │ NUMERIC       │
                │             │ total_amount_incl_tax   │ NUMERIC       │
                │             │ avg_unit_price          │ NUMERIC       │
                │             └─────────────────────────┴───────────────┘
                │
                (transaction_id has no dimension — it is the grain of the fact)
```

## Notes

- `dim_products` normalises `product_id` / `product_name` out of the fact table
- `dim_date` enables time-based slicing (by month, quarter, weekday) without
  computing date parts in every query
- The current implementation covers `dim_customers` + `fact_transactions`;
  `dim_products` and `dim_date` are the natural next step
