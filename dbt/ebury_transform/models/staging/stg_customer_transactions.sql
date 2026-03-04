{{
    config(
        materialized='view'
    )
}}

with source_data as (
    select * from {{ source('staging', 'customer_transactions') }}
)

select
    transaction_id,
    customer_id,
    transaction_date::date as transaction_date,
    amount::numeric as amount,
    current_timestamp as loaded_at
from source_data

