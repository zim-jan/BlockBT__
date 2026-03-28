from pathlib import Path
from unittest.mock import patch

import numpy as np
import pandas as pd
import pytest

from blockbt.data.yahoo import YFDataConnector


def _create_mock_df(start_date: str, end_date: str) -> pd.DataFrame:
    dates = pd.date_range(start_date, end_date, freq="D")
    n = len(dates)

    # We create a dataframe with the exact columns yfinance usually returns
    # (some multi-level if needed, but simple one-level works too)
    df = pd.DataFrame({
        "Open": np.random.rand(n) * 100,
        "High": np.random.rand(n) * 105,
        "Low": np.random.rand(n) * 95,
        "Close": np.random.rand(n) * 100,
        "Volume": np.random.randint(1000, 10000, n),
        "Adj Close": np.random.rand(n) * 100  # Will be filtered out
    }, index=dates)
    return df

@pytest.fixture
def temp_cache_dir(tmp_path):
    return str(tmp_path / "cache")

def test_yfin_connector_initialization(temp_cache_dir):
    # Test init with custom dir
    connector = YFDataConnector(cache_dir=temp_cache_dir)
    assert connector.cache_dir == Path(temp_cache_dir)
    assert connector.cache_dir.exists()

    # Test init with env var
    with patch.dict("os.environ", {"BLOCKBT_DATA_CACHE_DIR": str(temp_cache_dir + "_env")}):
        connector_env = YFDataConnector()
        assert connector_env.cache_dir == Path(temp_cache_dir + "_env")

@patch("blockbt.data.yahoo.yf.download")
def test_fetch_data_initial_download(mock_download, temp_cache_dir):
    # Mock yfinance
    mock_df = _create_mock_df("2023-01-01", "2023-01-10")
    mock_download.return_value = mock_df

    connector = YFDataConnector(cache_dir=temp_cache_dir)
    symbol = "AAPL"

    result = connector.fetch_data(symbol, "2023-01-01", "2023-01-10")

    # Assert download was called
    mock_download.assert_called_once()

    # Assert result is correct format
    assert isinstance(result.index, pd.DatetimeIndex)
    assert list(result.columns) == ["Open", "High", "Low", "Close", "Volume"]
    assert len(result) == len(mock_df)

    # Assert cache file was created
    cache_file = Path(temp_cache_dir) / f"{symbol}.parquet"
    assert cache_file.exists()

    # Check cache contents
    cached_df = pd.read_parquet(cache_file)
    assert len(cached_df) == len(mock_df)

@patch("blockbt.data.yahoo.yf.download")
def test_fetch_data_cache_hit(mock_download, temp_cache_dir):
    # Setup initial cache
    connector = YFDataConnector(cache_dir=temp_cache_dir)
    symbol = "AAPL"

    # Manually create cache file
    initial_df = _create_mock_df("2023-01-01", "2023-01-20")
    initial_df.index.name = "Date"
    # Ensure it's standardized
    standardized_df = connector._standardize_dataframe(initial_df)
    cache_file = Path(temp_cache_dir) / f"{symbol}.parquet"
    connector.cache_dir.mkdir(parents=True, exist_ok=True)
    standardized_df.to_parquet(cache_file)

    # Request subset of cached data
    result = connector.fetch_data(symbol, "2023-01-05", "2023-01-15")

    # Assert download was NOT called
    mock_download.assert_not_called()

    # Assert result contains the expected subset
    assert len(result) == 11  # inclusive 05 to 15
    assert result.index.min() == pd.Timestamp("2023-01-05")
    assert result.index.max() == pd.Timestamp("2023-01-15")

@patch("blockbt.data.yahoo.yf.download")
def test_fetch_data_partial_cache_miss(mock_download, temp_cache_dir):
    # Setup initial cache
    connector = YFDataConnector(cache_dir=temp_cache_dir)
    symbol = "AAPL"

    # Cached: 2023-01-01 to 2023-01-10
    initial_df = _create_mock_df("2023-01-01", "2023-01-10")
    initial_df.index.name = "Date"
    standardized_df = connector._standardize_dataframe(initial_df)
    cache_file = Path(temp_cache_dir) / f"{symbol}.parquet"
    connector.cache_dir.mkdir(parents=True, exist_ok=True)
    standardized_df.to_parquet(cache_file)

    # Mock download to return extended data (2023-01-01 to 2023-01-20)
    # The connector will fetch the full requested range
    mock_df = _create_mock_df("2023-01-01", "2023-01-20")
    mock_download.return_value = mock_df

    # Request: 2023-01-01 to 2023-01-20 (partially missing)
    result = connector.fetch_data(symbol, "2023-01-01", "2023-01-20")

    # Assert download WAS called
    mock_download.assert_called_once()

    # Assert result contains merged data
    assert len(result) == 20
    assert result.index.min() == pd.Timestamp("2023-01-01")
    assert result.index.max() == pd.Timestamp("2023-01-20")

    # Assert cache file was updated
    updated_cache = pd.read_parquet(cache_file)
    assert len(updated_cache) == 20

@patch("blockbt.data.yahoo.yf.download")
def test_fetch_data_empty_yfinance(mock_download, temp_cache_dir):
    # Mock yfinance returning empty dataframe
    mock_download.return_value = pd.DataFrame()

    connector = YFDataConnector(cache_dir=temp_cache_dir)
    result = connector.fetch_data("INVALID", "2023-01-01", "2023-01-10")

    assert result.empty

def test_safe_symbol_name(temp_cache_dir):
    connector = YFDataConnector(cache_dir=temp_cache_dir)

    # Test standard symbol
    assert connector._get_cache_path("AAPL").name == "AAPL.parquet"

    # Test symbol with slash (crypto pair usually)
    assert connector._get_cache_path("BTC/USD").name == "BTC_USD.parquet"
