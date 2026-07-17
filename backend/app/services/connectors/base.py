from __future__ import annotations

import re
from abc import ABC, abstractmethod
from pathlib import Path

import pandas as pd
from loguru import logger

from app.core.config import settings
from app.core.utils.parquet import load_parquet, save_parquet

"""
BaseDataConnector — abstract interface for all market data providers.

Every connector must:
  1. Implement ``fetch()`` to return a normalised OHLCV DataFrame.
  2. Use Parquet caching to avoid redundant network calls.
  3. Clearly document its authentication requirements (none / BYOK / OAuth).
"""




class BaseDataConnector(ABC):
    """Abstract data provider plugin.

    Subclasses override ``_download()`` to fetch raw data from their source.
    Caching, normalisation, and Parquet I/O are handled here in the base class
    so connector authors only need to implement the network call.
    """

    #: Human-readable connector key (used in config / registry).
    CONNECTOR_KEY: str = "base"
    #: Whether an API key / credentials are required.
    REQUIRES_AUTH: bool = False

    def __init__(self, cache_dir: Path | None = None) -> None:
        self._cache_dir = cache_dir or settings.PARQUET_DIR
        self._cache_ttl_hours = settings.PARQUET_CACHE_TTL_HOURS

    # ------------------------------------------------------------------
    # Public interface
    # ------------------------------------------------------------------

    def fetch(
        self,
        symbol: str | list[str],
        start: str,
        end: str,
        timeframe: str = "1d",
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Fetch OHLCV data, using the Parquet cache when available.

        Parameters
        ----------
        symbol:     Ticker symbol ``"AAPL"`` lub lista tickerów ``["AAPL", "MSFT"]``.
        start:      ISO date string, e.g. ``"2020-01-01"``.
        end:        ISO date string, e.g. ``"2023-12-31"``.
        timeframe:  Data frequency, e.g. ``"1d"``, ``"1h"``.
        use_cache:  If False, bypass the cache and always re-download.

        Returns
        -------
        pd.DataFrame
            - Single symbol (``str``): DatetimeIndex, kolumny ``open high low close volume`` (float64).
            - Lista symboli: format LONG — wierszowy 2-poziomowy MultiIndex ``[symbol, date]``
              (te same kolumny co single), zbudowany deterministycznie: per-symbol pobranie
              (cache per ticker działa dalej) + ``pd.concat(..., keys=symbols, names=["symbol"]).sort_index()``.
              Nie używamy ``vbt.YFData(list)`` — wyłącznie pętla per-symbol + concat.
        """
        # Faza 10: lista tickerów → LONG MultiIndex [symbol, date] (broadcasting w silniku).
        if isinstance(symbol, (list, tuple)):
            # Review Fazy 10: deduplikacja (kolizja kolumn po unstack) z zachowaniem kolejnosci.
            unique_symbols: list[str] = list(dict.fromkeys(symbol))
            if not unique_symbols:
                return pd.DataFrame()
            # Review Fazy 10: pojedynczy ticker degraduje do formatu single (spojnosc z "AAPL").
            if len(unique_symbols) == 1:
                return self.fetch(
                    unique_symbols[0], start, end, timeframe=timeframe, use_cache=use_cache
                )
            frames: list[pd.DataFrame] = []
            keys: list[str] = []
            for sym in unique_symbols:
                frames.append(
                    self.fetch(sym, start, end, timeframe=timeframe, use_cache=use_cache)
                )
                keys.append(sym)
            combined = pd.concat(frames, keys=keys, names=["symbol"])
            return combined.sort_index()

        cache_path = self._cache_path(symbol, start, end, timeframe)

        if use_cache and self._cache_valid(cache_path):
            logger.debug("{} cache hit: {}", self.CONNECTOR_KEY, cache_path)
            df = load_parquet(cache_path)
            return self._normalise(df)

        logger.info(
            "{} downloading {} {} ({} → {})",
            self.CONNECTOR_KEY,
            symbol,
            timeframe,
            start,
            end,
        )
        df = self._download(symbol, start, end, timeframe)
        df = self._normalise(df)

        if not df.empty:
            save_parquet(df, cache_path)
            logger.debug("{} cached {} rows → {}", self.CONNECTOR_KEY, len(df), cache_path)

        return df

    @abstractmethod
    def _download(
        self,
        symbol: str,
        start: str,
        end: str,
        timeframe: str,
    ) -> pd.DataFrame:
        """Fetch raw data from the upstream source.

        Must return a DataFrame with at minimum: open, high, low, close columns.
        The index should be datetime-like; ``fetch()`` will normalise it.
        """
        ...

    def health_check(self) -> dict[str, str]:
        """Return connector health / authorization status for diagnostics."""
        return {
            "connector": self.CONNECTOR_KEY,
            "requires_auth": str(self.REQUIRES_AUTH),
            "status": "ok",
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _normalise(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardise column names and index type."""
        df = df.copy()
        df.columns = [c.lower() for c in df.columns]
        # Ensure DatetimeIndex (timezone-naive)
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)
        df.sort_index(inplace=True)
        # Keep only OHLCV columns (drop Adj Close etc.)
        keep = [c for c in ("open", "high", "low", "close", "volume") if c in df.columns]
        return df[keep].astype(float)

    # Audyt 2026-07-17: komponenty ścieżki cache pochodzą wprost z parametrów
    # węzła DAG (frontend) — bez sanityzacji wartość "../../evil" uciekała
    # poza katalog cache przy zapisie Parquet (path traversal).
    _SAFE_PATH_COMPONENT = re.compile(r"^[A-Za-z0-9._-]+$")

    def _cache_path(self, symbol: str, start: str, end: str, timeframe: str) -> Path:
        safe_sym = symbol.upper().replace("/", "_")
        for name, value in (
            ("symbol", safe_sym),
            ("start", start),
            ("end", end),
            ("timeframe", timeframe),
        ):
            text = str(value)
            if ".." in text or not self._SAFE_PATH_COMPONENT.fullmatch(text):
                raise ValueError(
                    f"Niebezpieczny komponent ścieżki cache: {name}={value!r} "
                    f"(dozwolone znaki: litery, cyfry, '.', '_', '-')."
                )
        fname = f"{start}_{end}_{timeframe}.parquet"
        return self._cache_dir / safe_sym / fname

    def _cache_valid(self, path: Path) -> bool:
        """Return True if the cached file is fresh enough to use."""
        import time

        if not path.exists():
            return False
        age_hours = (time.time() - path.stat().st_mtime) / 3600
        return age_hours < self._cache_ttl_hours

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} key={self.CONNECTOR_KEY!r}>"
