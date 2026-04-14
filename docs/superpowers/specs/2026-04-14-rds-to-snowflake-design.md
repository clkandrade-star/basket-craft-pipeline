# RDS to Snowflake Pipeline — Design Spec

**Date:** 2026-04-14
**Status:** Approved

## Overview

A Python script that reads all 8 Basket Craft raw tables from AWS RDS PostgreSQL and loads them into the `basket_craft.raw` schema in Snowflake using a full truncate-and-reload strategy.

## Files Changed

| File | Change |
|------|--------|
| `db.py` | Add `get_snowflake_connection()` factory |
| `extract_rds_to_snowflake.py` | New pipeline script |
| `requirements.txt` | Add `snowflake-connector-python[pandas]` |
| `.env.example` | Add 7 `SNOWFLAKE_*` placeholder vars |

## Architecture

Two connection sources:
- **RDS PostgreSQL** — existing `get_rds_engine()` SQLAlchemy engine from `db.py`
- **Snowflake** — new `get_snowflake_connection()` in `db.py` returning a `snowflake.connector` connection

### `db.py` addition

```python
def get_snowflake_connection():
    return snowflake.connector.connect(
        account=os.getenv('SNOWFLAKE_ACCOUNT'),
        user=os.getenv('SNOWFLAKE_USER'),
        password=os.getenv('SNOWFLAKE_PASSWORD'),
        warehouse=os.getenv('SNOWFLAKE_WAREHOUSE'),
        database=os.getenv('SNOWFLAKE_DATABASE'),
        schema=os.getenv('SNOWFLAKE_SCHEMA'),
        role=os.getenv('SNOWFLAKE_ROLE'),
    )
```

### Environment Variables (added to `.env.example`)

```
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=
SNOWFLAKE_ROLE=
```

## Data Flow

For each of the 8 tables (`employees`, `order_item_refunds`, `order_items`, `orders`, `products`, `users`, `website_pageviews`, `website_sessions`):

```
RDS PostgreSQL
  └─ pd.read_sql("SELECT * FROM {table}")
       └─ df.columns = [c.lower() for c in df.columns]
            └─ cursor.execute("DROP TABLE IF EXISTS basket_craft.raw.{table}")
                 └─ write_pandas(conn, df, table.upper(),
                                 schema=os.getenv('SNOWFLAKE_SCHEMA').upper(),
                                 database=os.getenv('SNOWFLAKE_DATABASE').upper(),
                                 auto_create_table=True, quote_identifiers=False)
```

- Table discovery via `sqlalchemy.inspect(rds_engine).get_table_names()`
- Column names lowercased on the DataFrame before write
- `quote_identifiers=False` — Snowflake stores identifiers as uppercase, accessible case-insensitively
- `auto_create_table=True` — Snowflake creates the table from DataFrame schema if it doesn't exist after the DROP

## Error Handling

No custom try/except. Exceptions propagate naturally and stop the run with a clear traceback — consistent with `extract_to_rds.py`. No partial-success logic.

## Connection Lifecycle

Snowflake connection opened once before the table loop, closed in a `finally` block after all tables are loaded.

## Progress Logging

`print()` per table showing table name and row count, matching `extract_to_rds.py` style.

## Dependencies

- `snowflake-connector-python[pandas]` — provides `write_pandas()`
- Existing: `pandas`, `sqlalchemy`, `psycopg2-binary`, `python-dotenv`
