{{ config(materialized='table') }}

with products as (
    select * from {{ ref('stg_products') }}
)

select
    product_id,
    product_name,
    description,
    cast(created_at as date) as product_launch_date
from products
