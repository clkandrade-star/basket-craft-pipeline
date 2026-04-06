# Basket Craft Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a manual-trigger EL+T pipeline that extracts orders, order_items, and products from MySQL into PostgreSQL staging tables, then aggregates them into a `monthly_sales_summary` table.

**Architecture:** Two-layer EL+T — `extract.py` does a full truncate-and-reload of three staging tables from MySQL; `transform.py` reads from staging and writes the aggregated summary; `run_pipeline.py` is the entry point that calls both in sequence. Shared DB connection factories live in `db.py`.

**Tech Stack:** Python 3, pandas, SQLAlchemy, pymysql, psycopg2-binary, python-dotenv, pytest, Docker (PostgreSQL 15)

---

## File Map

| File | Responsibility |
|---|---|
| `docker-compose.yml` | Runs PostgreSQL 15 container with named volume |
| `.env.example` | Credential template (committed); `.env` holds real values (gitignored) |
| `requirements.txt` | Python dependencies |
| `db.py` | `get_mysql_engine()` and `get_postgres_engine()` connection factories |
| `extract.py` | Reads orders/order_items/products from MySQL; writes to stg_* tables in PostgreSQL |
| `transform.py` | Reads staging tables; writes aggregated `monthly_sales_summary` |
| `run_pipeline.py` | Entry point — calls extract then transform |
| `tests/__init__.py` | Makes tests/ a package |
| `tests/test_db.py` | Tests for DB engine factories |
| `tests/test_extract.py` | Tests for extract logic |
| `tests/test_transform.py` | Tests for transform logic |
| `tests/test_run_pipeline.py` | Tests for pipeline runner |

---

## Task 1: Project Scaffolding

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `requirements.txt`
- Modify: `.gitignore`

- [ ] **Step 1: Create `requirements.txt`**

```
pandas
sqlalchemy
pymysql
psycopg2-binary
python-dotenv
pytest
```

- [ ] **Step 2: Create `.env.example`**

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

- [ ] **Step 3: Create `docker-compose.yml`**

```yaml
version: '3.8'
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DATABASE}
    ports:
      - "${POSTGRES_PORT:-5432}:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

- [ ] **Step 4: Add `.superpowers/` to `.gitignore`**

Append to the existing `.gitignore`:
```
# Superpowers brainstorm sessions
.superpowers/
```

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .env.example docker-compose.yml .gitignore
git commit -m "feat: add project scaffolding"
```

---

## Task 2: DB Connection Helpers

**Files:**
- Create: `db.py`
- Create: `tests/__init__.py`
- Create: `tests/test_db.py`

- [ ] **Step 1: Create `tests/__init__.py`** (empty file)

- [ ] **Step 2: Write failing tests**

Create `tests/test_db.py`:

```python
import os
from unittest.mock import patch
from sqlalchemy.engine import Engine
from db import get_mysql_engine, get_postgres_engine


def test_get_mysql_engine_returns_engine():
    env = {
        'MYSQL_USER': 'root', 'MYSQL_PASSWORD': 'secret',
        'MYSQL_HOST': 'localhost', 'MYSQL_PORT': '3306',
        'MYSQL_DATABASE': 'basket_craft',
    }
    with patch.dict(os.environ, env):
        engine = get_mysql_engine()
    assert isinstance(engine, Engine)
    assert 'mysql+pymysql' in str(engine.url)


def test_get_postgres_engine_returns_engine():
    env = {
        'POSTGRES_USER': 'user', 'POSTGRES_PASSWORD': 'secret',
        'POSTGRES_HOST': 'localhost', 'POSTGRES_PORT': '5432',
        'POSTGRES_DATABASE': 'basket_craft_dw',
    }
    with patch.dict(os.environ, env):
        engine = get_postgres_engine()
    assert isinstance(engine, Engine)
    assert 'postgresql+psycopg2' in str(engine.url)
```

- [ ] **Step 3: Run tests to confirm they fail**

```bash
pytest tests/test_db.py -v
```

Expected: `ModuleNotFoundError: No module named 'db'`

- [ ] **Step 4: Create `db.py`**

```python
import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

load_dotenv()


def get_mysql_engine():
    url = (
        f"mysql+pymysql://{os.getenv('MYSQL_USER')}:{os.getenv('MYSQL_PASSWORD')}"
        f"@{os.getenv('MYSQL_HOST')}:{os.getenv('MYSQL_PORT', '3306')}"
        f"/{os.getenv('MYSQL_DATABASE')}"
    )
    return create_engine(url)


def get_postgres_engine():
    url = (
        f"postgresql+psycopg2://{os.getenv('POSTGRES_USER')}:{os.getenv('POSTGRES_PASSWORD')}"
        f"@{os.getenv('POSTGRES_HOST')}:{os.getenv('POSTGRES_PORT', '5432')}"
        f"/{os.getenv('POSTGRES_DATABASE')}"
    )
    return create_engine(url)
```

- [ ] **Step 5: Run tests to confirm they pass**

```bash
pytest tests/test_db.py -v
```

Expected:
```
tests/test_db.py::test_get_mysql_engine_returns_engine PASSED
tests/test_db.py::test_get_postgres_engine_returns_engine PASSED
2 passed
```

- [ ] **Step 6: Commit**

```bash
git add db.py tests/__init__.py tests/test_db.py
git commit -m "feat: add DB connection helpers"
```

---

## Task 3: Extract Module

**Files:**
- Create: `extract.py`
- Create: `tests/test_extract.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_extract.py`:

```python
from unittest.mock import MagicMock, patch
from extract import extract


def test_extract_reads_all_three_tables():
    mock_df = MagicMock()
    mock_mysql = MagicMock()
    mock_postgres = MagicMock()

    with patch('extract.pd.read_sql', return_value=mock_df) as mock_read:
        extract(mysql_engine=mock_mysql, postgres_engine=mock_postgres)

    assert mock_read.call_count == 3
    tables_read = [c.args[0] for c in mock_read.call_args_list]
    assert 'SELECT * FROM orders' in tables_read
    assert 'SELECT * FROM order_items' in tables_read
    assert 'SELECT * FROM products' in tables_read


def test_extract_writes_staging_tables():
    mock_df = MagicMock()
    mock_mysql = MagicMock()
    mock_postgres = MagicMock()

    with patch('extract.pd.read_sql', return_value=mock_df):
        extract(mysql_engine=mock_mysql, postgres_engine=mock_postgres)

    staging_names = [c.args[0] for c in mock_df.to_sql.call_args_list]
    assert 'stg_orders' in staging_names
    assert 'stg_order_items' in staging_names
    assert 'stg_products' in staging_names


def test_extract_uses_replace_strategy():
    mock_df = MagicMock()
    mock_mysql = MagicMock()
    mock_postgres = MagicMock()

    with patch('extract.pd.read_sql', return_value=mock_df):
        extract(mysql_engine=mock_mysql, postgres_engine=mock_postgres)

    for c in mock_df.to_sql.call_args_list:
        assert c.kwargs.get('if_exists') == 'replace'
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_extract.py -v
```

Expected: `ModuleNotFoundError: No module named 'extract'`

- [ ] **Step 3: Create `extract.py`**

```python
import pandas as pd
from db import get_mysql_engine, get_postgres_engine

TABLES = ['orders', 'order_items', 'products']


def extract(mysql_engine=None, postgres_engine=None):
    if mysql_engine is None:
        mysql_engine = get_mysql_engine()
    if postgres_engine is None:
        postgres_engine = get_postgres_engine()

    for table in TABLES:
        df = pd.read_sql(f'SELECT * FROM {table}', mysql_engine)
        df.to_sql(f'stg_{table}', postgres_engine, if_exists='replace', index=False)
        print(f'Loaded {len(df)} rows into stg_{table}')
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_extract.py -v
```

Expected:
```
tests/test_extract.py::test_extract_reads_all_three_tables PASSED
tests/test_extract.py::test_extract_writes_staging_tables PASSED
tests/test_extract.py::test_extract_uses_replace_strategy PASSED
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add extract.py tests/test_extract.py
git commit -m "feat: add extract module"
```

---

## Task 4: Transform Module

**Files:**
- Create: `transform.py`
- Create: `tests/test_transform.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_transform.py`:

```python
from unittest.mock import MagicMock, patch
from transform import transform, TRANSFORM_SQL


def test_transform_runs_aggregation_sql():
    mock_df = MagicMock()
    mock_engine = MagicMock()

    with patch('transform.pd.read_sql', return_value=mock_df) as mock_read:
        transform(postgres_engine=mock_engine)

    mock_read.assert_called_once_with(TRANSFORM_SQL, mock_engine)


def test_transform_writes_summary_table():
    mock_df = MagicMock()
    mock_engine = MagicMock()

    with patch('transform.pd.read_sql', return_value=mock_df):
        transform(postgres_engine=mock_engine)

    mock_df.to_sql.assert_called_once_with(
        'monthly_sales_summary', mock_engine, if_exists='replace', index=False
    )


def test_transform_sql_contains_required_columns():
    assert 'product_name' in TRANSFORM_SQL
    assert 'order_count' in TRANSFORM_SQL
    assert 'total_revenue' in TRANSFORM_SQL
    assert 'avg_order_value' in TRANSFORM_SQL
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_transform.py -v
```

Expected: `ModuleNotFoundError: No module named 'transform'`

- [ ] **Step 3: Create `transform.py`**

```python
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
```

- [ ] **Step 4: Run tests to confirm they pass**

```bash
pytest tests/test_transform.py -v
```

Expected:
```
tests/test_transform.py::test_transform_runs_aggregation_sql PASSED
tests/test_transform.py::test_transform_writes_summary_table PASSED
tests/test_transform.py::test_transform_sql_contains_required_columns PASSED
3 passed
```

- [ ] **Step 5: Commit**

```bash
git add transform.py tests/test_transform.py
git commit -m "feat: add transform module"
```

---

## Task 5: Pipeline Runner

**Files:**
- Create: `run_pipeline.py`
- Create: `tests/test_run_pipeline.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_run_pipeline.py`:

```python
import pytest
from unittest.mock import patch
from run_pipeline import run


def test_run_calls_extract_then_transform():
    with patch('run_pipeline.extract') as mock_extract, \
         patch('run_pipeline.transform') as mock_transform:
        run()
    mock_extract.assert_called_once()
    mock_transform.assert_called_once()


def test_run_extract_called_before_transform():
    call_order = []
    with patch('run_pipeline.extract', side_effect=lambda: call_order.append('extract')), \
         patch('run_pipeline.transform', side_effect=lambda: call_order.append('transform')):
        run()
    assert call_order == ['extract', 'transform']


def test_run_propagates_extract_failure():
    with patch('run_pipeline.extract', side_effect=Exception('DB connection failed')), \
         patch('run_pipeline.transform') as mock_transform:
        with pytest.raises(Exception, match='DB connection failed'):
            run()
    mock_transform.assert_not_called()
```

- [ ] **Step 2: Run tests to confirm they fail**

```bash
pytest tests/test_run_pipeline.py -v
```

Expected: `ModuleNotFoundError: No module named 'run_pipeline'`

- [ ] **Step 3: Create `run_pipeline.py`**

```python
from extract import extract
from transform import transform


def run():
    print('Starting extraction...')
    extract()
    print('Starting transformation...')
    transform()
    print('Pipeline complete.')


if __name__ == '__main__':
    run()
```

- [ ] **Step 4: Run all tests**

```bash
pytest -v
```

Expected:
```
tests/test_db.py::test_get_mysql_engine_returns_engine PASSED
tests/test_db.py::test_get_postgres_engine_returns_engine PASSED
tests/test_extract.py::test_extract_reads_all_three_tables PASSED
tests/test_extract.py::test_extract_writes_staging_tables PASSED
tests/test_extract.py::test_extract_uses_replace_strategy PASSED
tests/test_transform.py::test_transform_runs_aggregation_sql PASSED
tests/test_transform.py::test_transform_writes_summary_table PASSED
tests/test_transform.py::test_transform_sql_contains_required_columns PASSED
tests/test_run_pipeline.py::test_run_calls_extract_then_transform PASSED
tests/test_run_pipeline.py::test_run_extract_called_before_transform PASSED
tests/test_run_pipeline.py::test_run_propagates_extract_failure PASSED
11 passed
```

- [ ] **Step 5: Commit**

```bash
git add run_pipeline.py tests/test_run_pipeline.py
git commit -m "feat: add pipeline runner"
```

---

## Running the Pipeline

1. Copy `.env.example` to `.env` and fill in credentials
2. Start PostgreSQL: `docker compose up -d`
3. Install dependencies: `pip install -r requirements.txt`
4. Run: `python run_pipeline.py`
5. Query results:
   ```sql
   SELECT * FROM monthly_sales_summary ORDER BY year, month, product_name;
   ```
