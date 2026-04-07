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
