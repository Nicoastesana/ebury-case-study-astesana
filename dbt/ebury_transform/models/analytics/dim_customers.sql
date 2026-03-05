/*
  dim_customers
  =============
  One row per customer derived from valid transactions.
  Contains descriptive attributes and activity summary for each customer.

  Only rows where is_valid = TRUE (non-null transaction_id, customer_id,
  and transaction_date) are considered.
*/

with valid_transactions as (

    select *
    from {{ ref('stg_customer_transactions') }}
    where is_valid = true

),

dim_customers as (

    select
        customer_id,

        -- Activity window
        min(transaction_date)                           as first_transaction_date,
        max(transaction_date)                           as last_transaction_date,

        -- Volume metrics
        count(distinct transaction_id)                  as total_transactions,
        count(distinct product_id)                      as distinct_products_purchased,

        -- Spend metrics (only rows where price and tax are not null)
        round(sum(price * quantity)::numeric, 2)        as total_gross_amount,
        round(sum(tax)::numeric, 2)                     as total_tax_paid,
        round(sum((price * quantity) + tax)::numeric, 2) as total_amount_incl_tax,
        round(avg(price)::numeric, 2)                   as avg_unit_price

    from valid_transactions
    where price    is not null
      and quantity is not null
    group by customer_id

)

select * from dim_customers
