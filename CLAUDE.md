# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

Use the Python virtual environment for all commands:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in credentials before running anything.

Start the local PostgreSQL container:

```bash
docker compose up -d
```

## Commands

```bash
# Run the full local pipeline (extract → transform)
.venv/Scripts/python run_pipeline.py

# Extract all MySQL tables raw into AWS RDS
.venv/Scripts/python extract_to_rds.py

# Load all RDS tables into Snowflake (basket_craft.raw)
.venv/Scripts/python extract_rds_to_snowflake.py

# Run all tests
.venv/Scripts/pytest -v

# Run a single test file
.venv/Scripts/pytest tests/test_transform.py -v

# Run a single test
.venv/Scripts/pytest tests/test_transform.py::test_transform_writes_summary_table -v

# Inspect results in local PostgreSQL
docker exec basket-craft-pipeline-postgres-1 psql -U postgres -d basket_craft -c "SELECT * FROM monthly_sales_summary LIMIT 10;"
```

### dbt commands

dbt requires Python 3.13 — use `.venv313/Scripts/` not `.venv/Scripts/`. All
`SNOWFLAKE_*` vars must be exported to the shell before running dbt (they are
read via `env_var()` in `profiles.yml`, not loaded from `.env` automatically).

```bash
# Export credentials from .env into the current shell session
set -a && source .env && set +a

# Then run dbt from inside the project folder
cd basket_craft

# Build all models
../.venv313/Scripts/dbt run

# Run all tests
../.venv313/Scripts/dbt test

# Generate and browse documentation
../.venv313/Scripts/dbt docs generate
../.venv313/Scripts/dbt docs serve   # opens http://localhost:8080
```

## Architecture

There are two independent pipelines:

### Local EL+T pipeline (`run_pipeline.py`)

Extracts three tables from MySQL into a local PostgreSQL container, then aggregates them:

1. **`extract.py`** — truncate-and-reload of `orders`, `order_items`, `products` from MySQL into local PostgreSQL staging tables (`stg_orders`, `stg_order_items`, `stg_products`) via `pandas.read_sql` / `DataFrame.to_sql(if_exists='replace')`.
2. **`transform.py`** — reads the three staging tables and writes `monthly_sales_summary` (product_name × year × month with order_count, total_revenue, avg_order_value). The aggregation SQL lives in the `TRANSFORM_SQL` module-level constant.

### RDS bulk load (`extract_to_rds.py`)

Discovers all tables in MySQL via `sqlalchemy.inspect` and loads them as-is into AWS RDS PostgreSQL. Explicitly `DROP TABLE IF EXISTS` before each load to avoid PostgreSQL catalog conflicts from partial runs. The MySQL source has 8 tables: `employees`, `order_item_refunds`, `order_items`, `orders`, `products`, `users`, `website_pageviews`, `website_sessions`.

### Snowflake loader (`extract_rds_to_snowflake.py`)

Reads all 8 tables from AWS RDS PostgreSQL and loads them into Snowflake using truncate-and-reload. For each table: drops the existing Snowflake table, lowercases all column names, then bulk-loads via `snowflake-connector-python`'s `write_pandas`.

**Target:** `BASKET_CRAFT.RAW` (database and schema set via `SNOWFLAKE_DATABASE` / `SNOWFLAKE_SCHEMA` in `.env`)

**Credentials required in `.env`** (see `.env.example` for all keys):
- `SNOWFLAKE_ACCOUNT` — account identifier, e.g. `xy12345.us-east-1` (no `.snowflakecomputing.com`)
- `SNOWFLAKE_USER`, `SNOWFLAKE_PASSWORD` — login credentials
- `SNOWFLAKE_WAREHOUSE` — compute warehouse to use
- `SNOWFLAKE_DATABASE` — target database (`BASKET_CRAFT`)
- `SNOWFLAKE_SCHEMA` — target schema (`RAW`)
- `SNOWFLAKE_ROLE` — role to assume for the session

### Shared infrastructure

**`db.py`** — engine/connection factories reading from `.env` via python-dotenv:
- `get_mysql_engine()` — source MySQL (`MYSQL_*` vars)
- `get_postgres_engine()` — local Docker PostgreSQL (`POSTGRES_*` vars)
- `get_rds_engine()` — AWS RDS PostgreSQL (`RDS_*` vars)
- `get_snowflake_connection()` — Snowflake connector connection (`SNOWFLAKE_*` vars)

**Testing approach:** All tests mock DB engines — no live connections required. `extract()` and `transform()` accept optional `mysql_engine`/`postgres_engine` keyword arguments; when `None`, they call the factory functions.

**PostgreSQL note:** `ROUND()` requires a `::numeric` cast — `double precision` is not accepted by PostgreSQL's two-argument `ROUND`. See `TRANSFORM_SQL` in `transform.py`.

### dbt project (`basket_craft/`)

The dbt project lives at `basket_craft/` inside this repo and targets Snowflake.

**`profiles.yml`** is stored outside the repo at `~/.dbt/profiles.yml` so
credentials never touch version control. It reads all connection details from
the same `SNOWFLAKE_*` environment variables used by the Python loader, via
dbt's `env_var()` function. Models are written to the `BASKET_CRAFT.ANALYTICS`
schema in Snowflake.

**Staging models** (`basket_craft/models/staging/`) — views over `BASKET_CRAFT.RAW`,
one per source table. Rename columns to clean snake_case and cast types; no
joins, filters, or aggregations:
- `stg_orders` — one row per order
- `stg_order_items` — one row per order line item
- `stg_products` — product catalog
- `stg_customers` — one row per registered customer (source table: `users`)

**Mart models** (`basket_craft/models/marts/`) — materialized as tables:
- `dim_date` — date spine from 2020-01-01 covering ~10 years
- `dim_customers` — one row per customer with full address and signup date
- `dim_products` — one row per product with name and description
- `fct_order_items` — one row per order line item; joins to orders for
  customer and order date; includes `line_revenue`, `line_cogs`, and
  `line_gross_profit` measures

**Tests:** `order_item_id` in `fct_order_items` is tested for `unique` and
`not_null` via `basket_craft/models/marts/_schema.yml`.
