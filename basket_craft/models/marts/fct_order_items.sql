{{ config(materialized='table') }}

with order_items as (
    select * from {{ ref('stg_order_items') }}
),

orders as (
    select * from {{ ref('stg_orders') }}
)

select
    -- keys
    oi.order_item_id,
    oi.order_id,
    o.customer_id,
    oi.product_id,
    cast(o.created_at as date) as order_date,

    -- order item attributes
    oi.is_primary_item,

    -- measures
    1                          as quantity,
    oi.price_usd               as unit_price,
    1 * oi.price_usd           as line_revenue,
    oi.cogs_usd                as unit_cogs,
    1 * oi.cogs_usd            as line_cogs,
    1 * oi.price_usd
        - 1 * oi.cogs_usd      as line_gross_profit,

    -- timestamps
    oi.created_at              as order_item_created_at
from order_items oi
inner join orders o on o.order_id = oi.order_id
