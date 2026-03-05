/*
  agg_by_customer_product
  =======================
  One row per customer-product pair. Reveals purchase patterns per combination.
*/

select
    customer_id,
    product_id,
    product_name,
    count(distinct transaction_id)          as total_transactions,
    min(transaction_date)                   as first_transaction_date,
    max(transaction_date)                   as last_transaction_date,
    sum(quantity)                           as total_quantity,
    round(sum(total_amount)::numeric, 2)    as total_paid,
    round(sum(tax)::numeric, 2)             as total_taxes

from {{ ref('fact_transactions') }}
group by customer_id, product_id, product_name
order by customer_id, product_id
