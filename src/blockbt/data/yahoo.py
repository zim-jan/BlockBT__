import os
from pathlib import Path

import pandas as pd
import yfinance as yf

from blockbt.data.base import BaseDataConnector


class YFDataConnector(BaseDataConnector):
    """
    Yahoo Finance data connector with local Parquet caching.

    This connector uses `yfinance` to download historical OHLCV data.
    It implements intelligent caching:
    - Data is stored locally as `{symbol}.parquet` in a configurable directory.
    - If the requested date range is fully covered by the cache, it reads and filters the cache.
    - If not, it fetches missing data from Yahoo Finance, merges it with the existing cache,
      and updates the `.parquet` file to prevent future redundant API calls.

    Attributes:
        cache_dir (Path): The directory path for storing local cache files.
                          Configured via `BLOCKBT_DATA_CACHE_DIR` environment variable,
                          defaults to `data/cache`.
    """

    def __init__(self, cache_dir: str | None = None) -> None:
        """
        Initializes the YFDataConnector.

        Args:
            cache_dir (str | None): Optional custom path for the cache directory.
                                    If not provided, uses `BLOCKBT_DATA_CACHE_DIR` env var
                                    or 'data/cache' as fallback.
        """
        if cache_dir is None:
            cache_dir = os.environ.get("BLOCKBT_DATA_CACHE_DIR", "data/cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_cache_path(self, symbol: str) -> Path:
        """
        Returns the cache file path for a given symbol.

        Args:
            symbol (str): The financial instrument symbol.

        Returns:
            Path: The full file path to the Parquet cache file.
        """
        # Ensure safe filename
        safe_symbol = symbol.replace("/", "_").replace("\\", "_")
        return self.cache_dir / f"{safe_symbol}.parquet"

    def _standardize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Standardizes the DataFrame for `vectorbt`.

        Ensures the index is a timezone-naive DatetimeIndex and columns are
        formatted correctly (Title case 'Open', 'High', 'Low', 'Close', 'Volume').

        Args:
            df (pd.DataFrame): The raw pandas DataFrame.

        Returns:
            pd.DataFrame: The standardized pandas DataFrame.
        """
        # Ensure index is datetime
        if not isinstance(df.index, pd.DatetimeIndex):
            df.index = pd.to_datetime(df.index)

        # Remove timezone information
        if df.index.tz is not None:
            df.index = df.index.tz_localize(None)

        # Sort the index
        df.sort_index(inplace=True)

        # Ensure multi-level columns from yfinance (if any) are flattened
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)

        # Map to standard Title Case column names
        col_map = {col: col.capitalize() for col in df.columns}
        df.rename(columns=col_map, inplace=True)

        # Keep only required columns if they exist
        expected_cols = ["Open", "High", "Low", "Close", "Volume"]
        existing_cols = [col for col in expected_cols if col in df.columns]

        return df[existing_cols]

    def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches historical OHLCV data for a given symbol and date range.

        Checks the local Parquet cache first. If the requested data is fully available
        in the cache, it filters and returns it. Otherwise, it downloads the full
        requested date range from Yahoo Finance, merges it with the existing cache,
        saves the updated cache, and returns the requested data.

        Args:
            symbol (str): The financial instrument symbol (e.g., 'AAPL').
            start_date (str): The start date for the data in 'YYYY-MM-DD' format.
            end_date (str): The end date for the data in 'YYYY-MM-DD' format.

        Returns:
            pd.DataFrame: A standardized pandas DataFrame containing OHLCV data.
        """
        # Convert string dates to datetime objects for comparison
        req_start = pd.to_datetime(start_date)
        req_end = pd.to_datetime(end_date)

        cache_path = self._get_cache_path(symbol)

        cached_df = None
        if cache_path.exists():
            try:
                cached_df = pd.read_parquet(cache_path)
            except Exception:
                # If cache is corrupted, we will just act as if it's empty
                pass

        if cached_df is not None and not cached_df.empty:
            cache_start = cached_df.index.min()
            cache_end = cached_df.index.max()

            # Check if requested range is fully covered by cache
            if cache_start <= req_start and cache_end >= req_end:
                # Cache hit! Filter and return.
                # Use slicing (inclusive of boundaries)
                result_df = cached_df.loc[req_start:req_end]
                return result_df.copy()

        # Cache miss or partial hit: Fetch from Yahoo Finance
        # We fetch the requested range from yfinance. If we have cache, we'll merge them.
        fetched_df = yf.download(
            tickers=symbol,
            start=start_date,
            end=end_date,
            interval="1d",
            auto_adjust=True,
            progress=False,
            threads=False,
        )

        if fetched_df.empty:
            return pd.DataFrame()

        fetched_df = self._standardize_dataframe(fetched_df)

        # Merge with existing cache
        if cached_df is not None and not cached_df.empty:
            # Combine the two dataframes
            combined_df = pd.concat([cached_df, fetched_df])
            # Drop duplicates keeping the latest fetched data (if there are overlaps)
            # Actually, indices should be unique. Keep the last one.
            combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
            combined_df.sort_index(inplace=True)

            # Save merged data back to cache
            combined_df.to_parquet(cache_path, engine="pyarrow", compression="snappy")
            result_df = combined_df.loc[req_start:req_end]
        else:
            # Save the newly fetched data
            fetched_df.to_parquet(cache_path, engine="pyarrow", compression="snappy")
            result_df = fetched_df.loc[req_start:req_end]

        return result_df.copy()
