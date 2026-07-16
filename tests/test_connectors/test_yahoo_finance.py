"""
Tests for YahooFinanceConnector — Parquet caching round-trip.
(No live network calls — uses patched yfinance download.)
"""

from __future__ import annotations

from unittest.mock import patch

import numpy as np
import pandas as pd


def _make_ohlcv(n: int = 50) -> pd.DataFrame:
    rng = np.random.default_rng(1)
    dates = pd.date_range("2022-01-01", periods=n, freq="D")
    close = 100.0 * (1 + rng.normal(0, 0.01, n)).cumprod()
    return pd.DataFrame(
        {
            "Open": close,
            "High": close * 1.01,
            "Low": close * 0.99,
            "Close": close,
            "Volume": rng.integers(1_000_000, 5_000_000, n).astype(float),
        },
        index=dates,
    )


class TestYahooFinanceConnector:
    def test_fetch_downloads_and_caches(self, tmp_path):
        from blockbt.connectors.yahoo_finance import YahooFinanceConnector

        mock_df = _make_ohlcv()
        connector = YahooFinanceConnector(cache_dir=tmp_path)

        with patch("yfinance.download", return_value=mock_df) as mock_dl:
            df = connector.fetch("AAPL", "2022-01-01", "2022-03-01", use_cache=True)

        assert not df.empty
        mock_dl.assert_called_once()
        # Parquet file should now exist
        cached = list(tmp_path.rglob("*.parquet"))
        assert len(cached) == 1

    def test_fetch_uses_cache_on_second_call(self, tmp_path):
        from blockbt.connectors.yahoo_finance import YahooFinanceConnector

        mock_df = _make_ohlcv()
        connector = YahooFinanceConnector(cache_dir=tmp_path)

        with patch("yfinance.download", return_value=mock_df) as mock_dl:
            connector.fetch("MSFT", "2022-01-01", "2022-03-01")
            # Override TTL to ensure it's considered fresh
            connector._cache_ttl_hours = 1000
            connector.fetch("MSFT", "2022-01-01", "2022-03-01")

        # Should only download once
        assert mock_dl.call_count == 1

    def test_columns_are_normalised_to_lowercase(self, tmp_path):
        from blockbt.connectors.yahoo_finance import YahooFinanceConnector

        mock_df = _make_ohlcv()
        connector = YahooFinanceConnector(cache_dir=tmp_path)

        with patch("yfinance.download", return_value=mock_df):
            df = connector.fetch("GOOG", "2022-01-01", "2022-03-01", use_cache=False)

        assert all(c == c.lower() for c in df.columns)
        assert "close" in df.columns

    def test_parquet_round_trip_preserves_data(self, tmp_path):
        from blockbt.utils.parquet import load_parquet, save_parquet

        df = _make_ohlcv()
        df.columns = [c.lower() for c in df.columns]
        path = tmp_path / "TEST" / "2022-01-01_2022-03-01_1d.parquet"
        save_parquet(df, path)
        loaded = load_parquet(path)

        pd.testing.assert_frame_equal(df, loaded, check_freq=False)
