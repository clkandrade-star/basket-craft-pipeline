# RDS to Snowflake Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Write a Python script that reads all 8 Basket Craft tables from AWS RDS PostgreSQL and loads them into the `basket_craft.raw` Snowflake schema using truncate-and-reload.

**Architecture:** Add `get_snowflake_connection()` to `db.py` following the existing engine-factory pattern, then write `extract_rds_to_snowflake.py` mirroring `extract_to_rds.py` — discover tables via `sqlalchemy.inspect`, read with `pd.read_sql`, drop in Snowflake, write with `write_pandas`. The function accepts optional engine/connection arguments so it can be tested without live connections.

**Tech Stack:** `snowflake-connector-python[pandas]` (`write_pandas`), `sqlalchemy` (RDS read), `pandas`, `python-dotenv`

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `.env.example` | Modify | Add 7 `SNOWFLAKE_*` placeholder vars |
| `requirements.txt` | Modify | Add `snowflake-connector-python[pandas]` |
| `db.py` | Modify | Add `get_snowflake_connection()` factory |
| `extract_rds_to_snowflake.py` | Create | Pipeline: RDS → Snowflake for all 8 tables |
| `tests/test_db.py` | Modify | Add test for `get_snowflake_connection` |
| `tests/test_extract_rds_to_snowflake.py` | Create | Tests for the new pipeline script |

---

## Task 1: Update `.env.example` and `requirements.txt`

**Files:**
- Modify: `.env.example`
- Modify: `requirements.txt`

- [ ] **Step 1: Add Snowflake vars to `.env.example`**

Open `.env.example` and append after the existing `RDS_*` block:

```
SNOWFLAKE_ACCOUNT=
SNOWFLAKE_USER=
SNOWFLAKE_PASSWORD=
SNOWFLAKE_WAREHOUSE=
SNOWFLAKE_DATABASE=
SNOWFLAKE_SCHEMA=
SNOWFLAKE_ROLE=
```

- [ ] **Step 2: Add Snowflake dependency to `requirements.txt`**

Append to `requirements.txt`:

```
snowflake-connector-python[pandas]
```

- [ ] **Step 3: Install the new dependency**

```bash
.venv/Scripts/pip install snowflake-connector-python[pandas]
```

Expected: installs successfully, no errors.

- [ ] **Step 4: Commit**

```bash
git add .env.example requirements.txt
git commit -m "chore: add Snowflake env vars and connector dependency"
```

---

## Task 2: Add `get_snowflake_connection()` to `db.py`

**Files:**
- Modify: `db.py`
- Modify: `tests/test_db.py`

- [ ] **Step 1: Write the failing test**

Open `tests/test_db.py` and add at the bottom:

```python
import snowflake.connector
from unittest.mock import MagicMock, patch
from db import get_snowflake_connection


def test_get_snowflake_connection_calls_connector_with_env_vars():
    env = {
        'SNOWFLAKE_ACCOUNT': 'myorg-myaccount',
        'SNOWFLAKE_USER': 'testuser',
        'SNOWFLAKE_PASSWORD': 'secret',
        'SNOWFLAKE_WAREHOUSE': 'COMPUTE_WH',
        'SNOWFLAKE_DATABASE': 'BASKET_CRAFT',
        'SNOWFLAKE_SCHEMA': 'RAW',
        'SNOWFLAKE_ROLE': 'SYSADMIN',
    }
    with patch.dict(os.environ, env):
        with patch('db.snowflake.connector.connect', return_value=MagicMock()) as mock_connect:
            get_snowflake_connection()

    mock_connect.assert_called_once_with(
        account='myorg-myaccount',
        user='testuser',
        password='secret',
        warehouse='COMPUTE_WH',
        database='BASKET_CRAFT',
        schema='RAW',
        role='SYSADMIN',
    )
```

Note: `os` is already imported at the top of `tests/test_db.py`.

- [ ] **Step 2: Run to verify it fails**

```bash
.venv/Scripts/pytest tests/test_db.py::test_get_snowflake_connection_calls_connector_with_env_vars -v
```

Expected: FAIL with `ImportError` or `cannot import name 'get_snowflake_connection'`.

- [ ] **Step 3: Implement `get_snowflake_connection` in `db.py`**

Add `import snowflake.connector` at the top of `db.py`, then append this function at the bottom:

```python
import snowflake.connector


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

The `import snowflake.connector` line goes at the top of `db.py` with the other imports.

- [ ] **Step 4: Run to verify it passes**

```bash
.venv/Scripts/pytest tests/test_db.py::test_get_snowflake_connection_calls_connector_with_env_vars -v
```

Expected: PASS.

- [ ] **Step 5: Run the full test suite to check for regressions**

```bash
.venv/Scripts/pytest -v
```

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add db.py tests/test_db.py
git commit -m "feat: add get_snowflake_connection factory to db.py"
```

---

## Task 3: Write tests for `extract_rds_to_snowflake`

**Files:**
- Create: `tests/test_extract_rds_to_snowflake.py`

- [ ] **Step 1: Create the test file**

Create `tests/test_extract_rds_to_snowflake.py` with this content:

```python
import os
import pandas as pd
from unittest.mock import MagicMock, patch
from extract_rds_to_snowflake import extract_rds_to_snowflake

EIGHT_TABLES = [
    'employees', 'order_item_refunds', 'order_items', 'orders',
    'products', 'users', 'website_pageviews', 'website_sessions',
]

SNOWFLAKE_ENV = {
    'SNOWFLAKE_SCHEMA': 'raw',
    'SNOWFLAKE_DATABASE': 'basket_craft',
}


def test_reads_all_eight_tables_from_rds():
    mock_df = pd.DataFrame({'id': [1]})
    mock_rds = MagicMock()
    mock_conn = MagicMock()

    with patch('extract_rds_to_snowflake.inspect') as mock_inspect, \
         patch('extract_rds_to_snowflake.pd.read_sql', return_value=mock_df) as mock_read, \
         patch('extract_rds_to_snowflake.write_pandas', return_value=MagicMock()), \
         patch.dict(os.environ, SNOWFLAKE_ENV):
        mock_inspect.return_value.get_table_names.return_value = EIGHT_TABLES
        extract_rds_to_snowflake(rds_engine=mock_rds, snowflake_conn=mock_conn)

    assert mock_read.call_count == 8


def test_drops_each_table_before_loading():
    mock_df = pd.DataFrame({'id': [1]})
    mock_rds = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch('extract_rds_to_snowflake.inspect') as mock_inspect, \
         patch('extract_rds_to_snowflake.pd.read_sql', return_value=mock_df), \
         patch('extract_rds_to_snowflake.write_pandas', return_value=MagicMock()), \
         patch.dict(os.environ, SNOWFLAKE_ENV):
        mock_inspect.return_value.get_table_names.return_value = EIGHT_TABLES
        extract_rds_to_snowflake(rds_engine=mock_rds, snowflake_conn=mock_conn)

    executed_sqls = [c.args[0] for c in mock_cursor.execute.call_args_list]
    for table in EIGHT_TABLES:
        assert any(table in sql and 'DROP TABLE IF EXISTS' in sql for sql in executed_sqls), \
            f"Expected DROP TABLE IF EXISTS for {table}"


def test_lowercases_column_names_before_write():
    # Simulate PostgreSQL returning mixed-case column names
    mock_df = pd.DataFrame({'Order_ID': [1], 'User_ID': [2]})
    mock_rds = MagicMock()
    mock_conn = MagicMock()
    captured_dfs = []

    def capture_write(conn, df, table_name, **kwargs):
        captured_dfs.append(df.copy())
        return MagicMock()

    with patch('extract_rds_to_snowflake.inspect') as mock_inspect, \
         patch('extract_rds_to_snowflake.pd.read_sql', return_value=mock_df), \
         patch('extract_rds_to_snowflake.write_pandas', side_effect=capture_write), \
         patch.dict(os.environ, SNOWFLAKE_ENV):
        mock_inspect.return_value.get_table_names.return_value = ['orders']
        extract_rds_to_snowflake(rds_engine=mock_rds, snowflake_conn=mock_conn)

    assert list(captured_dfs[0].columns) == ['order_id', 'user_id']


def test_calls_write_pandas_for_each_table():
    mock_df = pd.DataFrame({'id': [1]})
    mock_write = MagicMock(return_value=MagicMock())
    mock_rds = MagicMock()
    mock_conn = MagicMock()

    with patch('extract_rds_to_snowflake.inspect') as mock_inspect, \
         patch('extract_rds_to_snowflake.pd.read_sql', return_value=mock_df), \
         patch('extract_rds_to_snowflake.write_pandas', mock_write), \
         patch.dict(os.environ, SNOWFLAKE_ENV):
        mock_inspect.return_value.get_table_names.return_value = EIGHT_TABLES
        extract_rds_to_snowflake(rds_engine=mock_rds, snowflake_conn=mock_conn)

    assert mock_write.call_count == 8
    written_table_names = [c.args[2] for c in mock_write.call_args_list]
    for table in EIGHT_TABLES:
        assert table.upper() in written_table_names, f"Expected write_pandas called for {table.upper()}"


def test_write_pandas_uses_correct_kwargs():
    mock_df = pd.DataFrame({'id': [1]})
    mock_write = MagicMock(return_value=MagicMock())
    mock_rds = MagicMock()
    mock_conn = MagicMock()

    with patch('extract_rds_to_snowflake.inspect') as mock_inspect, \
         patch('extract_rds_to_snowflake.pd.read_sql', return_value=mock_df), \
         patch('extract_rds_to_snowflake.write_pandas', mock_write), \
         patch.dict(os.environ, SNOWFLAKE_ENV):
        mock_inspect.return_value.get_table_names.return_value = ['orders']
        extract_rds_to_snowflake(rds_engine=mock_rds, snowflake_conn=mock_conn)

    kwargs = mock_write.call_args.kwargs
    assert kwargs['schema'] == 'RAW'
    assert kwargs['database'] == 'BASKET_CRAFT'
    assert kwargs['auto_create_table'] is True
    assert kwargs['quote_identifiers'] is False
```

- [ ] **Step 2: Run to verify the file fails to collect**

```bash
.venv/Scripts/pytest tests/test_extract_rds_to_snowflake.py -v
```

Expected: collection ERROR with `ModuleNotFoundError: No module named 'extract_rds_to_snowflake'` (the module-level import fails before any test runs).

- [ ] **Step 3: Commit the failing tests**

```bash
git add tests/test_extract_rds_to_snowflake.py
git commit -m "test: add failing tests for extract_rds_to_snowflake"
```

---

## Task 4: Implement `extract_rds_to_snowflake.py`

**Files:**
- Create: `extract_rds_to_snowflake.py`

- [ ] **Step 1: Create the script**

Create `extract_rds_to_snowflake.py`:

```python
import os
import pandas as pd
from sqlalchemy import inspect
from snowflake.connector.pandas_tools import write_pandas
from db import get_rds_engine, get_snowflake_connection


def extract_rds_to_snowflake(rds_engine=None, snowflake_conn=None):
    if rds_engine is None:
        rds_engine = get_rds_engine()
    if snowflake_conn is None:
        snowflake_conn = get_snowflake_connection()

    tables = inspect(rds_engine).get_table_names()
    print(f"Found {len(tables)} tables: {tables}")

    schema = os.getenv('SNOWFLAKE_SCHEMA').upper()
    database = os.getenv('SNOWFLAKE_DATABASE').upper()
    cursor = snowflake_conn.cursor()
    try:
        for table in tables:
            df = pd.read_sql(f'SELECT * FROM "{table}"', rds_engine)
            df.columns = [c.lower() for c in df.columns]
            cursor.execute(f'DROP TABLE IF EXISTS {database}.{schema}.{table}')
            write_pandas(
                snowflake_conn,
                df,
                table.upper(),
                schema=schema,
                database=database,
                auto_create_table=True,
                quote_identifiers=False,
            )
            print(f'Loaded {len(df)} rows into {table}')
    finally:
        cursor.close()
        snowflake_conn.close()


if __name__ == '__main__':
    extract_rds_to_snowflake()
```

- [ ] **Step 2: Run the tests to verify they pass**

```bash
.venv/Scripts/pytest tests/test_extract_rds_to_snowflake.py -v
```

Expected: all 5 tests PASS.

- [ ] **Step 3: Run the full test suite to check for regressions**

```bash
.venv/Scripts/pytest -v
```

Expected: all tests pass.

- [ ] **Step 4: Commit**

```bash
git add extract_rds_to_snowflake.py
git commit -m "feat: add RDS-to-Snowflake pipeline script"
```

---

## Self-Review Notes

- All 4 spec requirements covered: all 8 tables, truncate-and-reload, `write_pandas`, lowercase unquoted columns.
- `get_snowflake_connection` is tested via mock — no live Snowflake connection needed.
- `extract_rds_to_snowflake` accepts optional engine/conn args, matching the existing testable pattern in `extract.py` and `extract_to_rds.py`.
- `write_pandas` kwargs (`schema`, `database`, `auto_create_table`, `quote_identifiers`) verified in a dedicated test.
- Column lowercasing verified by capturing the DataFrame passed to `write_pandas`.
- DROP verified by inspecting cursor.execute call args.
