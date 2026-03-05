/*
  agg_by_product
  ==============
  One row per product. Revenue and customer reach summary.
*/

select
    product_id,
    product_name,
    count(distinct transaction_id)                          as total_transactions,
    min(transaction_date)                                   as first_transaction_date,
    max(transaction_date)                                   as last_transaction_date,
    array_agg(distinct customer_id order by customer_id)   as customer_ids,
    count(distinct customer_id)                             as count_different_customers,
    sum(quantity)                                           as total_products,
    round(sum(total_amount)::numeric, 2)                    as total_paid,
    round(sum(tax)::numeric, 2)                             as total_taxes

from {{ ref('fact_transactions') }}
group by product_id, product_name
order by product_id
