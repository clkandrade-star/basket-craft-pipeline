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
