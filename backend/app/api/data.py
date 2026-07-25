import asyncio
import json
import math
from typing import Any

import numpy as np
import talib
import yfinance as yf
from fastapi import APIRouter, HTTPException, Query
from loguru import logger

from app.schemas.base import ApiResponse

router = APIRouter()

# Kolumny surowe z yfinance, które nie są wskaźnikami — pomijane przy eksporcie.
_RAW_COLUMNS = frozenset(
    {"Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits", "Capital Gains"}
)


def _json_safe(value: Any) -> Any:
    """Zamienia wartości niereprezentowalne w JSON (NaN, ±inf) na ``None``.

    Wskaźniki mają NaN na pierwszych ``period - 1`` świecach (okres rozgrzewania).
    Bez tej konwersji serializator wypuszcza literalne ``NaN``, którego
    ``JSON.parse`` w przeglądarce nie przyjmuje — cały wykres zostaje pusty.
    """
    if value is None:
        return None
    if isinstance(value, (float, np.floating)):
        return None if not math.isfinite(float(value)) else float(value)
    if isinstance(value, (int, np.integer)):
        return int(value)
    return value


@router.get(
    "/realtime",
    summary="Get realtime-like intraday data",
    response_model=ApiResponse[list[dict[str, Any]]],
)
async def get_realtime_data(
    symbol: str = "BTC-USD",
    interval: str = "5m",
    indicators: str | None = Query(
        None, description="JSON string of indicators e.g. [{'type': 'SMA', 'period': 20}]"
    ),
) -> ApiResponse[list[dict[str, Any]]]:
    """Pobiera świeczki intraday za pomocą yfinance do celów demonstracyjnych na Dashboardzie."""
    try:
        def fetch_data():
            ticker = yf.Ticker(symbol)
            # Dobierzmy odpowiedni period dla interwału
            period = "1d"
            if interval in ["1m", "2m", "5m"]:
                period = "5d"
            elif interval in ["15m", "30m", "1h"]:
                period = "1mo"
            elif interval in ["1d", "1wk"]:
                period = "1y"
                
            df = ticker.history(period=period, interval=interval)
            if df.empty:
                df = ticker.history(period="5d", interval="15m")
                
            if not df.empty and indicators:
                try:
                    inds = json.loads(indicators)
                    # TA-Lib operuje na tablicach numpy float64, nie na Series.
                    close = df["Close"].to_numpy(dtype=np.float64)
                    for ind in inds:
                        itype = ind.get("type")
                        period_val = int(ind.get("period", 14))
                        # TA-Lib wymaga timeperiod >= 2 — mniejsze wartości rzucają Exception.
                        period_val = max(2, period_val)

                        col_name = f"{itype}_{period_val}"
                        if itype == "SMA":
                            df[col_name] = talib.SMA(close, timeperiod=period_val)
                        elif itype == "EMA":
                            df[col_name] = talib.EMA(close, timeperiod=period_val)
                        elif itype == "RSI":
                            df[col_name] = talib.RSI(close, timeperiod=period_val)
                        elif itype == "MACD":
                            macd_line, macd_signal, macd_hist = talib.MACD(
                                close, fastperiod=12, slowperiod=26, signalperiod=9
                            )
                            df["MACD_line"] = macd_line
                            df["MACD_signal"] = macd_signal
                            df["MACD_diff"] = macd_hist
                except Exception as ex:
                    logger.error(f"Error calculating indicators: {ex}")
            return df
        
        loop = asyncio.get_running_loop()
        df = await loop.run_in_executor(None, fetch_data)
        
        if df.empty:
            logger.warning(f"No realtime data found for {symbol}")
            return ApiResponse(success=True, data=[])
            
        # Nie odrzucamy wierszy z NaN (przy dużym oknie wskaźnika ucięłoby to
        # większość świec) — zamiast tego każda wartość przechodzi przez
        # _json_safe, które zamienia NaN/±inf na None.
        indicator_columns = [col for col in df.columns if col not in _RAW_COLUMNS]

        data = []
        for index, row in df.iterrows():
            point = {
                "date": index.isoformat(),
                "open": _json_safe(row["Open"]),
                "high": _json_safe(row["High"]),
                "low": _json_safe(row["Low"]),
                "close": _json_safe(row["Close"]),
                "volume": _json_safe(row["Volume"]),
            }
            # Dodaj obliczone wskaźniki
            for col in indicator_columns:
                point[col] = _json_safe(row[col])
            data.append(point)
            
        return ApiResponse(success=True, data=data)
        
    except Exception as e:
        logger.error(f"Error fetching realtime data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching realtime data") from e
