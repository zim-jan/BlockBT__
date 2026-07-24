import asyncio
import yfinance as yf
import pandas as pd
from fastapi import APIRouter, HTTPException, Query
from loguru import logger
from typing import Any, Optional
import json

from app.schemas.base import ApiResponse
from ta.trend import SMAIndicator, MACD, EMAIndicator
from ta.momentum import RSIIndicator

router = APIRouter()

@router.get("/realtime", summary="Get realtime-like intraday data", response_model=ApiResponse[list[dict[str, Any]]])
async def get_realtime_data(
    symbol: str = "BTC-USD",
    interval: str = "5m",
    indicators: Optional[str] = Query(None, description="JSON string of indicators e.g. [{'type': 'SMA', 'period': 20}]")
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
                    for ind in inds:
                        itype = ind.get("type")
                        period_val = int(ind.get("period", 14))
                        
                        col_name = f"{itype}_{period_val}"
                        if itype == "SMA":
                            df[col_name] = SMAIndicator(close=df["Close"], window=period_val).sma_indicator()
                        elif itype == "EMA":
                            df[col_name] = EMAIndicator(close=df["Close"], window=period_val).ema_indicator()
                        elif itype == "RSI":
                            df[col_name] = RSIIndicator(close=df["Close"], window=period_val).rsi()
                        elif itype == "MACD":
                            macd = MACD(close=df["Close"], window_slow=26, window_fast=12, window_sign=9)
                            df["MACD_line"] = macd.macd()
                            df["MACD_signal"] = macd.macd_signal()
                            df["MACD_diff"] = macd.macd_diff()
                except Exception as ex:
                    logger.error(f"Error calculating indicators: {ex}")
            return df
        
        loop = asyncio.get_running_loop()
        df = await loop.run_in_executor(None, fetch_data)
        
        if df.empty:
            logger.warning(f"No realtime data found for {symbol}")
            return ApiResponse(success=True, data=[])
            
        # Dropping NA might remove too much data if periods are large, 
        # so we keep them and just replace NaNs with None for JSON serialization
        df = df.where(pd.notnull(df), None)
        
        data = []
        for index, row in df.iterrows():
            point = {
                "date": index.isoformat(),
                "open": row["Open"],
                "high": row["High"],
                "low": row["Low"],
                "close": row["Close"],
                "volume": row["Volume"]
            }
            # Dodaj obliczone wskaźniki
            for col in df.columns:
                if col not in ["Open", "High", "Low", "Close", "Volume", "Dividends", "Stock Splits", "Capital Gains"]:
                    point[col] = row[col]
            data.append(point)
            
        return ApiResponse(success=True, data=data)
        
    except Exception as e:
        logger.error(f"Error fetching realtime data for {symbol}: {e}")
        raise HTTPException(status_code=500, detail="Error fetching realtime data") from e
