# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Environment Setup

Use the Python virtual environment for all commands:

```bash
python -m venv .venv
.venv/Scripts/pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in credentials before running anything.

Start the PostgreSQL container:

```bash
docker compose up -d
```

## Commands

```bash
# Run the full pipeline
.venv/Scripts/python run_pipeline.py

# Run all tests
.venv/Scripts/pytest -v

# Run a single test file
.venv/Scripts/pytest tests/test_transform.py -v

# Run a single test
.venv/Scripts/pytest tests/test_transform.py::test_transform_writes_summary_table -v

# Inspect results in PostgreSQL
docker exec basket-craft-pipeline-postgres-1 psql -U postgres -d basket_craft -c "SELECT * FROM monthly_sales_summary LIMIT 10;"
```

## Architecture

Two-layer EL+T pipeline triggered manually via `run_pipeline.py`:

1. **Extract** (`extract.py`) — full truncate-and-reload of three MySQL source tables (`orders`, `order_items`, `products`) into PostgreSQL staging tables (`stg_orders`, `stg_order_items`, `stg_products`) using `pandas.read_sql` / `DataFrame.to_sql(if_exists='replace')`.

2. **Transform** (`transform.py`) — reads from the three staging tables and writes aggregated output to `monthly_sales_summary` (product_name × year × month with order_count, total_revenue, avg_order_value). The aggregation SQL lives in the `TRANSFORM_SQL` module-level constant.

3. **`db.py`** — provides `get_mysql_engine()` and `get_postgres_engine()` connection factories via SQLAlchemy + python-dotenv. Both functions accept injected engines in tests via optional parameters on `extract()` and `transform()`.

**Testing approach:** All tests mock the DB engines — no live connections required. `extract()` and `transform()` accept optional `mysql_engine`/`postgres_engine` parameters for injection; when `None`, they fall back to the factory functions.

**PostgreSQL note:** `ROUND()` requires a `::numeric` cast — `double precision` is not accepted by PostgreSQL's two-argument `ROUND`. See `TRANSFORM_SQL` in `transform.py`.
