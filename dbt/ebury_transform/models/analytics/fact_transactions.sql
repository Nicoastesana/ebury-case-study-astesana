{{
    config(
        materialized='table'
    )
}}

with transactions as (
    select * from {{ ref('stg_customer_transactions') }}
)

select
    transaction_id,
    customer_id,
    transaction_date,
    amount,
    loaded_at,
    current_timestamp as created_at
from transactions

