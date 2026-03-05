/*
  stg_customer_transactions
  =========================
  Cleans and standardises every row from raw.customer_transactions.
  All source data quality issues are handled here:

  | Issue                              | Fix                                      |
  |------------------------------------|------------------------------------------|
  | transaction_id with 'T' prefix     | Strip prefix → cast to INTEGER           |
  | transaction_id NULL                | Keep NULL, flagged via is_valid          |
  | customer_id stored as '501.0'      | Cast float-string → INTEGER              |
  | customer_id NULL                   | Keep NULL, flagged via is_valid          |
  | transaction_date DD-MM-YYYY format | Detect and reformat to YYYY-MM-DD        |
  | transaction_date invalid           | Keep NULL, flagged via is_valid          |
  | product_id with 'P' prefix         | Strip prefix → cast to INTEGER           |
  | quantity NULL or non-numeric       | Cast to INTEGER, NULL if not parseable   |
  | price non-numeric ('Two Hundred')  | Cast to NUMERIC, NULL if not parseable   |
  | tax non-numeric ('Fifteen')        | Cast to NUMERIC, NULL if not parseable   |

  Rows that cannot meet the minimum quality bar (NULL transaction_id,
  customer_id, or transaction_date after cleaning) are flagged with
  is_valid = FALSE and excluded from the analytics layer.
*/

with source as (

    select * from {{ source('raw', 'customer_transactions') }}

),

cleaned as (

    select
        -- ── transaction_id ──────────────────────────────────────────────────
        -- Strip leading 'T' then cast; NULL if original was NULL
        case
            when transaction_id is null then null
            when transaction_id ilike 'T%'
                then nullif(regexp_replace(transaction_id, '^T', ''), '')::integer
            else nullif(transaction_id, '')::integer
        end                                         as transaction_id,

        -- ── customer_id ──────────────────────────────────────────────────────
        -- Source stores integers as floats ('501.0') — truncate decimal part
        case
            when customer_id is null then null
            else split_part(customer_id, '.', 1)::integer
        end                                         as customer_id,

        -- ── transaction_date ─────────────────────────────────────────────────
        -- Handle two formats: YYYY-MM-DD and DD-MM-YYYY
        case
            when transaction_date is null
                then null
            -- DD-MM-YYYY (day part ≤ 31, not a valid year when read as YYYY)
            when transaction_date ~ '^\d{2}-\d{2}-\d{4}$'
                then to_date(transaction_date, 'DD-MM-YYYY')
            -- Standard ISO format
            when transaction_date ~ '^\d{4}-\d{2}-\d{2}$'
                then to_date(transaction_date, 'YYYY-MM-DD')
            else null
        end                                         as transaction_date,

        -- ── product_id ───────────────────────────────────────────────────────
        -- Strip leading 'P' prefix if present
        case
            when product_id is null then null
            when product_id ilike 'P%'
                then nullif(regexp_replace(product_id, '^P', ''), '')::integer
            else nullif(product_id, '')::integer
        end                                         as product_id,

        product_name,

        -- ── quantity ─────────────────────────────────────────────────────────
        -- Stored as float string ('1.0'); non-numeric values → NULL
        case
            when quantity ~ '^\d+(\.\d+)?$'
                then quantity::numeric::integer
            else null
        end                                         as quantity,

        -- ── price ────────────────────────────────────────────────────────────
        -- Non-numeric strings ('Two Hundred') → NULL
        case
            when price ~ '^\d+(\.\d+)?$'
                then price::numeric
            else null
        end                                         as price,

        -- ── tax ──────────────────────────────────────────────────────────────
        -- Non-numeric strings ('Fifteen') → NULL
        case
            when tax ~ '^\d+(\.\d+)?$'
                then tax::numeric
            else null
        end                                         as tax,

        loaded_at

    from source

),

validated as (

    select
        *,
        -- A row is valid when the three identifying fields are present and clean
        (
            transaction_id is not null
            and customer_id    is not null
            and transaction_date is not null
        )                                           as is_valid
    from cleaned

)

select * from validated
