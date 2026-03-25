import abc

import pandas as pd


class BaseDataConnector(abc.ABC):
    """
    Abstract base class for all data connectors in BlockBT.

    This interface enforces a standard `fetch_data` method that all subclassed
    data providers must implement. The returned data must be a pandas DataFrame
    standardized for `vectorbt` backtesting (e.g., DatetimeIndex, specific column names).
    """

    @abc.abstractmethod
    def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        """
        Fetches historical OHLCV data for a given symbol and date range.

        Args:
            symbol (str): The financial instrument symbol (e.g., 'AAPL', 'BTC-USD').
            start_date (str): The start date for the data in 'YYYY-MM-DD' format.
            end_date (str): The end date for the data in 'YYYY-MM-DD' format.

        Returns:
            pd.DataFrame: A pandas DataFrame containing OHLCV data.
                          The index should be a timezone-naive or UTC DatetimeIndex.
                          Columns should at least include: 'Open', 'High', 'Low', 'Close', 'Volume'.
        """
        pass
