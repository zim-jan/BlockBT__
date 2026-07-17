from __future__ import annotations

import pandas as pd
from loguru import logger

from app.services.connectors.base import BaseDataConnector

"""
YahooFinanceConnector — default / fallback data provider.

Uses the ``yfinance`` library (no API key required). Downloaded data is
persisted as Parquet on disk, partitioned by symbol. On subsequent calls
the connector will serve from cache if it's still fresh (< TTL).
"""



# yfinance timeframe codes → readable string mapping for reference:
#   "1m","2m","5m","15m","30m","60m","90m","1h"
#   "1d","5d","1wk","1mo","3mo"
_VALID_INTERVALS = {
    "1m",
    "2m",
    "5m",
    "15m",
    "30m",
    "60m",
    "90m",
    "1h",
    "1d",
    "5d",
    "1wk",
    "1mo",
    "3mo",
}


class YahooFinanceConnector(BaseDataConnector):
    """Market data connector backed by Yahoo Finance via yfinance.

    Characteristics:
    - No authentication required.
    - Historical data up to ~70 years (daily).
    - Intraday data limited by yfinance's rate limits (≤ 60 days for 1m).
    - All data cached as Parquet for fast re-use.
    """

    CONNECTOR_KEY = "yahoo"
    REQUIRES_AUTH = False

    # ------------------------------------------------------------------
    # Core download implementation
    # ------------------------------------------------------------------

    def _download(
        self,
        symbol: str | list[str],
        start: str,
        end: str,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        try:
            import vectorbt as vbt
        except ImportError as exc:
            raise RuntimeError("vectorbt is not installed.") from exc

        interval = self._map_timeframe(timeframe)
        logger.debug("vbt.YFData.download({}, {}, {}, {})", symbol, start, end, interval)

        try:
            # vbt.YFData.download handles single symbol or list of symbols
            # It also handles caching and conversion to standard OHLCV format
            data = vbt.YFData.download(
                symbol,
                start=start,
                end=end,
                interval=interval,
            )
            df = data.get()  # Returns a combined DataFrame
        except Exception as e:
            # Audyt 2026-07-17: nie połykamy realnej przyczyny (sieć/rate-limit/
            # zły ticker) w mylące "No data returned" — propagujemy typowany błąd
            logger.error("vbt.YFData failed to download data for {}: {}", symbol, e)
            raise ConnectionError(
                f"Yahoo Finance download failed for {symbol!r}: {e}"
            ) from e

        if df.empty:
            logger.warning("vbt.YFData returned no data for {} ({} → {})", symbol, start, end)

        # Handle columns. YFData usually returns a multi-indexed DataFrame if multiple symbols
        # or single-indexed if one symbol.
        return df

    # ------------------------------------------------------------------
    # Health check
    # ------------------------------------------------------------------

    def health_check(self) -> dict[str, str]:
        try:
            import yfinance as yf  # type: ignore[import]

            ticker = yf.Ticker("AAPL")
            info = ticker.fast_info
            _ = info.last_price  # trigger a lightweight API call
            return {
                "connector": self.CONNECTOR_KEY,
                "requires_auth": "false",
                "status": "ok",
                "yfinance_version": getattr(yf, "__version__", "?"),
            }
        except Exception as exc:
            return {
                "connector": self.CONNECTOR_KEY,
                "status": "error",
                "error": str(exc),
            }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _map_timeframe(timeframe: str) -> str:
        """Map generic BlockBT timeframe strings to yfinance ``interval`` codes."""
        # Audyt 2026-07-17: "4h" było cicho mapowane na 60m BEZ resamplingu —
        # użytkownik dostawał bary godzinowe opisane jako 4-godzinne.
        if timeframe == "4h":
            raise ValueError(
                "Timeframe '4h' nie jest wspierany przez konektor Yahoo Finance "
                "(yfinance nie ma interwału 4h, a resampling nie jest zaimplementowany). "
                "Użyj '1h' albo '1d'."
            )
        mapping = {
            "1m": "1m",
            "5m": "5m",
            "15m": "15m",
            "30m": "30m",
            "1h": "60m",
            "1d": "1d",
            "1w": "1wk",
            "1M": "1mo",
        }
        result = mapping.get(timeframe, timeframe)
        if result not in _VALID_INTERVALS:
            logger.warning("YahooFinanceConnector: unknown timeframe {!r}, using '1d'", timeframe)
            return "1d"
        return result
