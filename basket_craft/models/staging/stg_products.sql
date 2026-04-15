with source as (
    select * from {{ source('raw', 'products') }}
)

select
    product_id,
    cast(created_at as timestamp) as created_at,
    product_name,
    description
from source
