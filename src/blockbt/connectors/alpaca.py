"""
AlpacaConnector — optional data provider using the Alpaca Markets API.

Authentication model: BYOK (Bring Your Own Key).
Required env vars:
  ALPACA_API_KEY    — Alpaca API key ID
  ALPACA_SECRET_KEY — Alpaca secret key

If credentials are missing the connector raises ``AuthenticationError``
rather than silently returning empty data.

Supports:
  - Historical stock bars (IEX / SIP feed)
  - Paper trading data endpoint (default)

Install the optional extra to use:
    pip install blockbt[alpaca]
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
from loguru import logger

from blockbt.config import settings
from blockbt.connectors.base import BaseDataConnector


class AuthenticationError(Exception):
    """Raised when Alpaca credentials are not configured."""


class AlpacaConnector(BaseDataConnector):
    """Market data connector backed by the Alpaca Markets API.

    Phase 1 Status: **Stub / Integration Template**

    The download path calls the real Alpaca SDK when it's available.
    If ``alpaca-py`` is not installed (it's an optional dependency) or
    credentials are absent, the connector raises clearly described errors
    so developers know exactly what to configure.
    """

    CONNECTOR_KEY = "alpaca"
    REQUIRES_AUTH = True

    def __init__(self, cache_dir: Path | None = None) -> None:
        super().__init__(cache_dir)
        self._api_key = settings.ALPACA_API_KEY
        self._secret_key = settings.ALPACA_SECRET_KEY
        self._base_url = settings.ALPACA_BASE_URL

    # ------------------------------------------------------------------
    # Core download implementation
    # ------------------------------------------------------------------

    def _download(
        self,
        symbol: str,
        start: str,
        end: str,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        self._require_credentials()

        try:
            from alpaca.data.historical import StockHistoricalDataClient  # type: ignore[import]
            from alpaca.data.requests import StockBarsRequest  # type: ignore[import]
            from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "alpaca-py is not installed. Install the optional extra: "
                "pip install blockbt[alpaca]"
            ) from exc

        client = StockHistoricalDataClient(
            api_key=self._api_key,
            secret_key=self._secret_key,
        )

        tf = self._map_timeframe(timeframe)
        logger.debug("Alpaca requesting {} {} ({} → {})", symbol, timeframe, start, end)

        request = StockBarsRequest(
            symbol_or_symbols=symbol,
            timeframe=tf,
            start=start,
            end=end,
        )
        bars = client.get_stock_bars(request)
        df: pd.DataFrame = bars.df

        if df.empty:
            logger.warning("Alpaca returned no data for {} ({} → {})", symbol, start, end)
            return df

        # Alpaca returns a MultiIndex (symbol, timestamp); flatten to simple DatetimeIndex.
        if isinstance(df.index, pd.MultiIndex):
            df = df.reset_index(level=0, drop=True)

        df.index = pd.to_datetime(df.index)
        df = df.rename(columns=str.lower)
        return df

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, str]:
        """Verify credentials are configured (does not make a live API call)."""
        if not self._api_key or not self._secret_key:
            return {
                "connector": self.CONNECTOR_KEY,
                "status": "unconfigured",
                "error": "ALPACA_API_KEY and ALPACA_SECRET_KEY are required.",
            }
        try:
            import alpaca  # type: ignore[import]

            sdk_version = getattr(alpaca, "__version__", "?")
        except ImportError:
            sdk_version = "not-installed"

        return {
            "connector": self.CONNECTOR_KEY,
            "requires_auth": "true",
            "status": "configured",
            "alpaca_sdk_version": sdk_version,
            "base_url": self._base_url,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _require_credentials(self) -> None:
        if not self._api_key or not self._secret_key:
            raise AuthenticationError(
                "Alpaca credentials not set. "
                "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables."
            )

    @staticmethod
    def _map_timeframe(timeframe: str) -> TimeFrame:  # type: ignore[name-defined]
        """Map BlockBT timeframe strings to Alpaca SDK TimeFrame objects."""
        from alpaca.data.timeframe import TimeFrame, TimeFrameUnit  # type: ignore[import]

        mapping = {
            "1m": TimeFrame(1, TimeFrameUnit.Minute),
            "5m": TimeFrame(5, TimeFrameUnit.Minute),
            "15m": TimeFrame(15, TimeFrameUnit.Minute),
            "30m": TimeFrame(30, TimeFrameUnit.Minute),
            "1h": TimeFrame(1, TimeFrameUnit.Hour),
            "4h": TimeFrame(4, TimeFrameUnit.Hour),
            "1d": TimeFrame(1, TimeFrameUnit.Day),
            "1w": TimeFrame(1, TimeFrameUnit.Week),
            "1M": TimeFrame(1, TimeFrameUnit.Month),
        }
        if timeframe not in mapping:
            logger.warning("AlpacaConnector: unknown timeframe {!r}, using '1d'", timeframe)
            return TimeFrame(1, TimeFrameUnit.Day)
        return mapping[timeframe]
