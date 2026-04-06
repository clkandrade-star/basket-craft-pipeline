# Basket Craft Sales Pipeline — Design Spec

**Date:** 2026-04-06  
**Project:** basket-craft-pipeline  
**Goal:** Monthly sales dashboard for Basket Craft — revenue, order counts, and average order value grouped by product name and month.

---

## 1. Architecture & Data Flow

```
MySQL (basket_craft)
  └── extract.py
        ├── SELECT * FROM orders
        ├── SELECT * FROM order_items
        └── SELECT * FROM products
              │
              ▼
  PostgreSQL (Docker)
    ├── stg_orders
    ├── stg_order_items
    └── stg_products
              │
              ▼
        transform.py
    (JOIN + aggregate)
              │
              ▼
    monthly_sales_summary
              │
              ▼
        run_pipeline.py  ← manual trigger entry point
```

**Pattern:** Two-layer EL+T. Raw rows are extracted into PostgreSQL staging tables first, then a separate transform step aggregates them into the final summary table. This preserves raw data for debugging and allows re-aggregation without re-extracting from MySQL.

**Trigger:** Manual — run `python run_pipeline.py`.

---

## 2. Source Schema (MySQL — basket_craft)

Key tables used:

| Table | Key Columns |
|---|---|
| `orders` | `order_id`, `created_at`, `user_id`, `primary_product_id`, `items_purchased`, `price_usd`, `cogs_usd` |
| `order_items` | `order_item_id`, `created_at`, `order_id`, `product_id`, `is_primary_item`, `price_usd`, `cogs_usd` |
| `products` | `product_id`, `created_at`, `product_name`, `description` |

`products` has no category column — `product_name` is used as the grouping dimension.

---

## 3. Extraction (`extract.py`)

- Connects to MySQL via `SQLAlchemy` + `pymysql`
- Reads each table with `pandas.read_sql()`
- Writes to PostgreSQL staging tables (`stg_orders`, `stg_order_items`, `stg_products`) using `pandas.to_sql(if_exists='replace')`
- Full truncate-and-reload on every run
- On connection failure: prints error and exits with non-zero code

---

## 4. Transformation (`transform.py`)

Reads from PostgreSQL staging and runs this aggregation:

```sql
SELECT
    p.product_name,
    EXTRACT(YEAR  FROM o.created_at) AS year,
    EXTRACT(MONTH FROM o.created_at) AS month,
    COUNT(DISTINCT o.order_id)        AS order_count,
    SUM(oi.price_usd)                 AS total_revenue,
    SUM(oi.price_usd) / COUNT(DISTINCT o.order_id) AS avg_order_value
FROM stg_order_items oi
JOIN stg_orders   o ON oi.order_id  = o.order_id
JOIN stg_products p ON oi.product_id = p.product_id
GROUP BY p.product_name, year, month
ORDER BY year, month, p.product_name
```

Writes result to `monthly_sales_summary` with `if_exists='replace'`.

---

## 5. Project Structure

```
basket-craft-pipeline/
├── .env                  # DB credentials (gitignored)
├── .env.example          # Template with placeholder values
├── requirements.txt
├── run_pipeline.py       # Manual trigger entry point
├── extract.py
├── transform.py
└── docker-compose.yml    # PostgreSQL container
```

---

## 6. Dependencies

```
pandas
sqlalchemy
pymysql
psycopg2-binary
python-dotenv
```

---

## 7. Environment Variables (`.env`)

```
MYSQL_HOST=
MYSQL_PORT=3306
MYSQL_USER=
MYSQL_PASSWORD=
MYSQL_DATABASE=basket_craft

POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=
POSTGRES_PASSWORD=
POSTGRES_DATABASE=
```

---

## 8. Error Handling

- Connection failures in either `extract.py` or `transform.py` print the error and exit with a non-zero code — no silent failures.
- `run_pipeline.py` propagates failures so the user knows which step failed.
