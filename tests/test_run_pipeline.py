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
