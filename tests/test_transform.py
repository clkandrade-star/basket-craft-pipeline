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
