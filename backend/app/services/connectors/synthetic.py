from __future__ import annotations

import zlib

import numpy as np
import pandas as pd
from loguru import logger

from app.services.connectors.base import BaseDataConnector

"""
SyntheticConnector — deterministyczny generator danych OHLCV (review 2026-07-16).

Źródło 'synthetic' było zarejestrowane w UI, ale konektor nie istniał —
każdy run kończył się "Unknown connector 'synthetic'". Generator działa
w pełni offline (Air-Gapped) i deterministycznie: ten sam (symbol, zakres,
timeframe) zawsze daje identyczną serię, a różne symbole różne serie —
dzięki temu multi-symbol broadcasting (Faza 10) ma sensowne dane testowe.
Obsługa listy symboli (format LONG MultiIndex [symbol, date]) pochodzi
z BaseDataConnector.fetch() — konektor implementuje tylko _download().
"""

# Mapowanie timeframe'ów BlockBT na częstotliwości pandas date_range
_FREQ_MAP = {
    "1m": "min",
    "5m": "5min",
    "15m": "15min",
    "30m": "30min",
    "1h": "h",
    "4h": "4h",
    "1d": "D",
    "1w": "W",
    "1M": "MS",
}


class SyntheticConnector(BaseDataConnector):
    """Deterministyczny random-walk OHLCV — bez sieci, bez uwierzytelniania."""

    CONNECTOR_KEY = "synthetic"
    REQUIRES_AUTH = False

    def _download(
        self,
        symbol: str,
        start: str,
        end: str,
        timeframe: str = "1d",
    ) -> pd.DataFrame:
        freq = _FREQ_MAP.get(timeframe)
        if freq is None:
            logger.warning("SyntheticConnector: unknown timeframe {!r}, using '1d'", timeframe)
            freq = "D"

        index = pd.date_range(start=start, end=end, freq=freq)
        n = len(index)
        if n == 0:
            logger.warning("SyntheticConnector: empty date range {} → {}", start, end)
            return pd.DataFrame()

        # Deterministyczny seed z pełnego kontekstu zapytania — ten sam request
        # zawsze zwraca te same dane, różne symbole różne serie
        seed = zlib.crc32(f"{symbol}|{start}|{end}|{timeframe}".encode())
        rng = np.random.default_rng(seed)

        # Geometryczny random walk z lekkim dryfem — ceny zawsze dodatnie
        returns = rng.normal(loc=0.0003, scale=0.015, size=n)
        close = 100.0 * np.exp(np.cumsum(returns))
        open_ = np.concatenate([[100.0], close[:-1]])
        spread = np.abs(rng.normal(0.0, 0.005, size=n))
        high = np.maximum(open_, close) * (1.0 + spread)
        low = np.minimum(open_, close) * (1.0 - spread)
        volume = rng.integers(100_000, 1_000_000, size=n).astype(float)

        logger.debug("SyntheticConnector: generated {} rows for {} (seed={})", n, symbol, seed)
        return pd.DataFrame(
            {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
            index=index,
        )

    def health_check(self) -> dict[str, str]:
        return {
            "connector": self.CONNECTOR_KEY,
            "requires_auth": "false",
            "status": "ok",
        }
