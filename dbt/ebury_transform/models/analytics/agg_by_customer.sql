/*
  agg_by_customer
  ===============
  One row per customer. Full activity summary including product array.
*/

select
    customer_id,
    count(distinct transaction_id)                          as total_transactions,
    min(transaction_date)                                   as first_transaction_date,
    max(transaction_date)                                   as last_transaction_date,
    array_agg(distinct product_id order by product_id)     as product_ids,
    count(distinct product_id)                              as count_different_products,
    sum(quantity)                                           as total_products,
    round(sum(total_amount)::numeric, 2)                    as total_paid,
    round(sum(tax)::numeric, 2)                             as total_taxes

from {{ ref('fact_transactions') }}
group by customer_id
order by customer_id
