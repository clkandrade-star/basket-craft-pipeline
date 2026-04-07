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
