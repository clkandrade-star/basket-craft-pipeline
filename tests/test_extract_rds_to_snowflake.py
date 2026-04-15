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
