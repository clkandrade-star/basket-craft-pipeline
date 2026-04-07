# Basket Craft Sales Pipeline

A manual-trigger EL+T pipeline that extracts order data from MySQL into PostgreSQL staging tables, then aggregates it into a `monthly_sales_summary` table for a monthly sales dashboard.

## What it does

1. **Extract** — pulls `orders`, `order_items`, and `products` from a MySQL source database into PostgreSQL staging tables (`stg_*`) via a full truncate-and-reload.
2. **Transform** — joins the staging tables and aggregates by product and month, producing `monthly_sales_summary` with order counts, total revenue, and average order value.

## Requirements

- Python 3
- Docker (for PostgreSQL)

## Setup

**1. Clone the repo and create a virtual environment:**

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

**2. Configure credentials:**

```bash
cp .env.example .env
```

Edit `.env` with your MySQL connection details and desired PostgreSQL credentials:

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

**3. Start PostgreSQL:**

```bash
docker compose up -d
```

## Run the pipeline

```bash
.venv/Scripts/python run_pipeline.py
```

Output:
```
Starting extraction...
Loaded 32313 rows into stg_orders
Loaded 40025 rows into stg_order_items
Loaded 4 rows into stg_products
Starting transformation...
Wrote 94 rows to monthly_sales_summary
Pipeline complete.
```

## Query the results

```bash
docker exec <postgres-container> psql -U <user> -d <database> -c \
  "SELECT * FROM monthly_sales_summary ORDER BY year, month, product_name;"
```

| Column | Description |
|---|---|
| `product_name` | Product name from source |
| `year` / `month` | Calendar period |
| `order_count` | Distinct orders in that period |
| `total_revenue` | Sum of `price_usd` from order items |
| `avg_order_value` | Revenue divided by order count, rounded to 2 decimal places |

## Run tests

```bash
.venv/Scripts/pytest -v
```

All tests use mocked DB engines — no live database connection required.
