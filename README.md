# Basket Craft Sales Pipeline

A manual-trigger EL+T pipeline that extracts order data from MySQL into PostgreSQL staging tables, then aggregates it into a `monthly_sales_summary` table for a monthly sales dashboard. Raw source data is also available in AWS RDS PostgreSQL for ad-hoc analysis.

## What it does

1. **Extract** — pulls `orders`, `order_items`, and `products` from a MySQL source database into PostgreSQL staging tables (`stg_*`) via a full truncate-and-reload.
2. **Transform** — joins the staging tables and aggregates by product and month, producing `monthly_sales_summary` with order counts, total revenue, and average order value.
3. **RDS Load** — copies all 8 MySQL source tables as-is into AWS RDS PostgreSQL for direct querying.

## Requirements

- Python 3
- Docker (for local PostgreSQL)

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

Edit `.env` with your MySQL, local PostgreSQL, and RDS connection details:

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

RDS_HOST=
RDS_PORT=5432
RDS_USER=
RDS_PASSWORD=
RDS_DATABASE=basket_craft
```

**3. Start local PostgreSQL:**

```bash
docker compose up -d
```

## Run the local pipeline

Extracts and transforms data into the local PostgreSQL container:

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

## Load raw data into AWS RDS

Copies all MySQL source tables as-is into AWS RDS PostgreSQL:

```bash
.venv/Scripts/python extract_to_rds.py
```

Output:
```
Found 8 tables: ['employees', 'order_item_refunds', 'order_items', 'orders', 'products', 'users', 'website_pageviews', 'website_sessions']
Loaded 20 rows into employees
Loaded 1731 rows into order_item_refunds
Loaded 40025 rows into order_items
Loaded 32313 rows into orders
Loaded 4 rows into products
Loaded 31696 rows into users
Loaded 1188124 rows into website_pageviews
Loaded 472871 rows into website_sessions
```

## Query the results

**Local — aggregated summary:**

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

**AWS RDS — raw source tables:**

Connect to the RDS instance and query any of the 8 raw tables directly:

```
Host: <RDS_HOST>
Port: 5432
Database: basket_craft
```

## Run tests

```bash
.venv/Scripts/pytest -v
```

All tests use mocked DB engines — no live database connection required.
