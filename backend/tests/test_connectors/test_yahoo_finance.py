
from unittest.mock import patch

import numpy as np
import pandas as pd

"""
Tests for YahooFinanceConnector — Parquet caching round-trip.
(No live network calls — uses patched _download method.)
"""




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
    """Tests mock at the _download boundary — the lowest-level method that
    calls vbt.YFData.download. This avoids fragile sys.modules patching
    and correctly tests the base-class caching/normalisation logic."""

    def test_fetch_downloads_and_caches(self, tmp_path):
        from app.services.connectors.yahoo_finance import YahooFinanceConnector

        mock_df = _make_ohlcv()
        connector = YahooFinanceConnector(cache_dir=tmp_path)

        with patch.object(connector, "_download", return_value=mock_df) as mock_dl:
            df = connector.fetch("AAPL", "2022-01-01", "2022-03-01", use_cache=True)

        assert not df.empty
        mock_dl.assert_called_once()
        # Parquet file should now exist
        cached = list(tmp_path.rglob("*.parquet"))
        assert len(cached) == 1

    def test_fetch_uses_cache_on_second_call(self, tmp_path):
        from app.services.connectors.yahoo_finance import YahooFinanceConnector

        mock_df = _make_ohlcv()
        connector = YahooFinanceConnector(cache_dir=tmp_path)

        with patch.object(connector, "_download", return_value=mock_df) as mock_dl:
            connector.fetch("MSFT", "2022-01-01", "2022-03-01")
            # Override TTL to ensure it's considered fresh
            connector._cache_ttl_hours = 1000
            connector.fetch("MSFT", "2022-01-01", "2022-03-01")

        # Should only download once — second call hits Parquet cache
        assert mock_dl.call_count == 1

    def test_columns_are_normalised_to_lowercase(self, tmp_path):
        from app.services.connectors.yahoo_finance import YahooFinanceConnector

        mock_df = _make_ohlcv()
        connector = YahooFinanceConnector(cache_dir=tmp_path)

        with patch.object(connector, "_download", return_value=mock_df):
            df = connector.fetch("GOOG", "2022-01-01", "2022-03-01", use_cache=False)

        assert all(c == c.lower() for c in df.columns)
        assert "close" in df.columns

    def test_parquet_round_trip_preserves_data(self, tmp_path):
        from app.core.utils.parquet import load_parquet, save_parquet

        df = _make_ohlcv()
        df.columns = [c.lower() for c in df.columns]
        path = tmp_path / "TEST" / "2022-01-01_2022-03-01_1d.parquet"
        save_parquet(df, path)
        loaded = load_parquet(path)

        pd.testing.assert_frame_equal(df, loaded, check_freq=False)


# Audyt 2026-07-17: "4h" było po cichu mapowane na 60m BEZ resamplingu —
# użytkownik dostawał bary godzinowe opisane jako 4-godzinne. Uczciwy błąd
# zamiast złej granulacji danych.
def test_timeframe_4h_rejected_loudly():
    import pytest

    from app.services.connectors.yahoo_finance import YahooFinanceConnector

    with pytest.raises(ValueError, match="4h"):
        YahooFinanceConnector._map_timeframe("4h")


def test_intraday_730_day_lookback_limit_raises_descriptive_error(tmp_path):
    import pytest
    from app.services.connectors.yahoo_finance import YahooFinanceConnector

    connector = YahooFinanceConnector(cache_dir=tmp_path)
    mock_data = patch("vectorbt.YFData.download").start()
    mock_data.return_value.get.return_value = pd.DataFrame()
    try:
        with pytest.raises(ValueError, match="730 days"):
            connector.fetch("GOOG", "2023-01-01", "2025-01-01", timeframe="1h", use_cache=False)
    finally:
        patch.stopall()


def test_1m_7_day_lookback_limit_raises_descriptive_error(tmp_path):
    import pytest
    from app.services.connectors.yahoo_finance import YahooFinanceConnector

    connector = YahooFinanceConnector(cache_dir=tmp_path)
    mock_data = patch("vectorbt.YFData.download").start()
    mock_data.return_value.get.return_value = pd.DataFrame()
    try:
        with pytest.raises(ValueError, match="7 days"):
            connector.fetch("GOOG", "2023-01-01", "2025-01-01", timeframe="1m", use_cache=False)
    finally:
        patch.stopall()


