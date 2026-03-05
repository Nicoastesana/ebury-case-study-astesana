/*
  audit_errors_by_load_date
  ==========================
  For each load batch (loaded_at date), counts how many rows had each
  type of data quality error. Useful to detect if a specific ingestion
  run introduced more issues than others.

  Error types
  -----------
  - null_transaction_id  : transaction_id was NULL or unparseable
  - null_customer_id     : customer_id was NULL (is_valid = FALSE)
  - null_transaction_date: date was NULL or unparseable
  - null_quantity        : quantity was missing or non-numeric
  - null_price           : price was non-numeric ('Two Hundred')
  - null_tax             : tax was non-numeric ('Fifteen')
  - total_errors         : rows with at least one error
*/

select
    loaded_at::date                                             as load_date,
    count(*)                                                    as total_rows,

    count(*) filter (where transaction_id   is null)           as null_transaction_id,
    count(*) filter (where customer_id      is null)           as null_customer_id,
    count(*) filter (where transaction_date is null)           as null_transaction_date,
    count(*) filter (where quantity         is null)           as null_quantity,
    count(*) filter (where price            is null)           as null_price,
    count(*) filter (where tax              is null)           as null_tax,

    count(*) filter (
        where transaction_id   is null
           or customer_id      is null
           or transaction_date is null
           or quantity         is null
           or price            is null
           or tax              is null
    )                                                           as total_rows_with_errors

from {{ ref('stg_customer_transactions') }}
group by loaded_at::date
order by load_date
