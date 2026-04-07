import pandas as pd
from db import get_postgres_engine

TRANSFORM_SQL = """
SELECT
    p.product_name,
    EXTRACT(YEAR  FROM o.created_at)::int AS year,
    EXTRACT(MONTH FROM o.created_at)::int AS month,
    COUNT(DISTINCT o.order_id)             AS order_count,
    SUM(oi.price_usd)                      AS total_revenue,
    ROUND(
        SUM(oi.price_usd) / COUNT(DISTINCT o.order_id), 2
    )                                      AS avg_order_value
FROM stg_order_items oi
JOIN stg_orders   o ON oi.order_id   = o.order_id
JOIN stg_products p ON oi.product_id = p.product_id
GROUP BY p.product_name,
         EXTRACT(YEAR  FROM o.created_at),
         EXTRACT(MONTH FROM o.created_at)
ORDER BY year, month, p.product_name
"""


def transform(postgres_engine=None):
    if postgres_engine is None:
        postgres_engine = get_postgres_engine()

    df = pd.read_sql(TRANSFORM_SQL, postgres_engine)
    df.to_sql('monthly_sales_summary', postgres_engine, if_exists='replace', index=False)
    print(f'Wrote {len(df)} rows to monthly_sales_summary')
