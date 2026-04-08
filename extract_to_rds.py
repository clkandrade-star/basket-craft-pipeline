import pandas as pd
from sqlalchemy import inspect, text
from db import get_mysql_engine, get_rds_engine


def extract_to_rds():
    mysql_engine = get_mysql_engine()
    rds_engine = get_rds_engine()

    tables = inspect(mysql_engine).get_table_names()
    print(f"Found {len(tables)} tables: {tables}")

    for table in tables:
        df = pd.read_sql(f'SELECT * FROM `{table}`', mysql_engine)
        with rds_engine.connect() as conn:
            conn.execute(text(f'DROP TABLE IF EXISTS "{table}"'))
            conn.commit()
        df.to_sql(table, rds_engine, if_exists='replace', index=False)
        print(f'Loaded {len(df)} rows into {table}')


if __name__ == '__main__':
    extract_to_rds()
