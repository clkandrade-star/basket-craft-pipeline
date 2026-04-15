import os
from unittest.mock import patch, MagicMock
from sqlalchemy.engine import Engine
from db import get_mysql_engine, get_postgres_engine, get_snowflake_connection


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
