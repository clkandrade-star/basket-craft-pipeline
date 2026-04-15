{{ config(materialized='table') }}

with customers as (
    select * from {{ ref('stg_customers') }}
)

select
    customer_id,
    first_name,
    last_name,
    first_name || ' ' || last_name as full_name,
    email,
    billing_street_address,
    billing_city,
    billing_state,
    billing_postal_code,
    billing_country,
    shipping_street_address,
    shipping_city,
    shipping_state,
    shipping_postal_code,
    shipping_country,
    cast(created_at as date) as signup_date,
    created_at               as signup_at
from customers
