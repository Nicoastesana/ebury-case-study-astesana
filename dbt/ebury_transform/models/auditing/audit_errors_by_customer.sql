/*
  audit_errors_by_customer
  =========================
  For each customer_id (including NULL), counts how many rows had each
  type of data quality error. Helps identify if errors are concentrated
  around specific customers or spread across all of them.
*/

select
    coalesce(customer_id::text, 'NULL')                        as customer_id,
    count(*)                                                    as total_rows,

    count(*) filter (where transaction_id   is null)           as null_transaction_id,
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
group by customer_id
order by total_rows_with_errors desc, customer_id
