{{
    config(
        materialized='table'
    )
}}

with transactions as (
    select * from {{ ref('stg_customer_transactions') }}
)

select distinct
    customer_id,
    min(transaction_date) over (partition by customer_id) as first_transaction_date,
    max(transaction_date) over (partition by customer_id) as last_transaction_date,
    count(*) over (partition by customer_id) as total_transactions,
    current_timestamp as created_at
from transactions

