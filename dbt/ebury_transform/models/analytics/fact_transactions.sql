/*
  fact_transactions
  =================
  One row per valid, fully-resolved transaction.
  Contains cleaned measures and foreign keys to dimension tables.

  Rows excluded:
    - is_valid = FALSE  (NULL transaction_id, customer_id, or transaction_date)
    - price or tax non-numeric after cleaning (kept in staging for audit,
      excluded here so all measures are trustworthy)

  Derived measures
  ----------------
  gross_amount      = price × quantity          (pre-tax revenue)
  total_amount      = gross_amount + tax        (total charged to customer)
  tax_rate_pct      = tax / gross_amount × 100  (effective tax rate)
*/

with stg as (

    select *
    from {{ ref('stg_customer_transactions') }}
    where is_valid = true
      and price    is not null
      and quantity is not null
      and tax      is not null

)

select
    -- Keys
    transaction_id,
    customer_id,
    product_id,

    -- Descriptors
    product_name,
    transaction_date,

    -- Base measures
    quantity,
    price                                               as unit_price,
    tax,

    -- Derived measures
    round((price * quantity)::numeric, 2)               as gross_amount,
    round((price * quantity + tax)::numeric, 2)         as total_amount,
    round((tax / nullif(price * quantity, 0) * 100)::numeric, 4)
                                                        as tax_rate_pct,

    -- Audit
    loaded_at

from stg
