from __future__ import annotations

import sys
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import vectorbt  # noqa: F401 — ensure it loads the real __init__.py
from loguru import logger

"""
run_vectorbt_backtest — Phase 3 background task entry-point.

Wraps OpenSourceEngine with:
  - Synthetic OHLCV data generation (random-walk, no network required).
  - Real market data via ConnectorRegistry (Yahoo Finance, Alpaca, etc.).
  - DB persistence: updates BacktestJob status + metrics.
  - Full error capture with FAILED status on any exception.

This function is designed to be called via FastAPI BackgroundTasks:

    background_tasks.add_task(run_vectorbt_backtest, job_id, parameters)
"""



# Ensure the vendored vectorbt directory is importable.
# We must insert it into sys.path before any import attempt to prevent Python
# from mistakenly turning the repo's vectorbt folder into a namespace package
# if the backend is launched from the project root.
_VENDORED_VBT = Path(__file__).resolve().parents[4] / "vectorbt"
if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
    sys.path.insert(0, str(_VENDORED_VBT))


# ---------------------------------------------------------------------------
# Data generation / acquisition
# ---------------------------------------------------------------------------


def _generate_ohlcv(
    n_days: int = 504,
    start_price: float = 100.0,
    seed: int = 42,
) -> pd.DataFrame:
    """Generate a realistic synthetic OHLCV DataFrame (random walk).

    Parameters
    ----------
    n_days:       Number of trading days to simulate.
    start_price:  Starting close price.
    seed:         NumPy random seed for reproducibility.

    Returns
    -------
    pd.DataFrame with columns [open, high, low, close, volume].
    """
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-01-03", periods=n_days, freq="B")

    # Log-normal daily returns around 0% drift
    returns = rng.normal(loc=0.0003, scale=0.015, size=n_days)
    close = start_price * np.exp(np.cumsum(returns))

    spread = close * rng.uniform(0.002, 0.012, size=n_days)
    high = close + spread * 0.6
    low = close - spread * 0.4
    open_ = close * (1 + rng.normal(0, 0.003, size=n_days))
    volume = rng.integers(500_000, 5_000_000, size=n_days).astype(float)

    return pd.DataFrame(
        {"open": open_, "high": high, "low": low, "close": close, "volume": volume},
        index=dates,
    )


def _fetch_market_data(
    data_source: str,
    symbol: str,
    start_date: str | None,
    end_date: str | None,
    timeframe: str,
) -> pd.DataFrame:
    """Fetch real market data via ConnectorRegistry.

    Falls back to synthetic generation if the connector returns empty data.
    """
    from app.services.connectors.registry import ConnectorRegistry

    # Default date range: 2 years back from today
    if not end_date:
        end_date = datetime.now(UTC).strftime("%Y-%m-%d")
    if not start_date:
        start_dt = datetime.now(UTC) - timedelta(days=730)
        start_date = start_dt.strftime("%Y-%m-%d")

    logger.info(
        "BacktestRunner: fetching data | source={} symbol={} {} → {} {}",
        data_source, symbol, start_date, end_date, timeframe,
    )

    try:
        connector = ConnectorRegistry.get(data_source)
        df = connector.fetch(symbol, start_date, end_date, timeframe)
        if df.empty:
            logger.warning(
                "BacktestRunner: connector returned empty data for {}, falling back to synthetic",
                symbol,
            )
            return _generate_ohlcv()
        logger.info("BacktestRunner: fetched {} rows from {}", len(df), data_source)
        return df
    except Exception as exc:
        logger.error("BacktestRunner: connector error — {}", exc)
        raise RuntimeError(
            f"Failed to fetch data from '{data_source}' for {symbol}: {exc}"
        ) from exc


# ---------------------------------------------------------------------------
# Core backtest runner
# ---------------------------------------------------------------------------


def _execute_backtest(parameters: dict[str, Any]) -> dict[str, Any]:
    """Run a vectorbt backtest with configurable data source and strategy.

    Returns a metrics dict on success.
    Raises on failure (caller handles DB persistence of the error).
    """
    try:
        import vectorbt as vbt  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            f"vectorbt is not importable. Checked vendored path: {_VENDORED_VBT}"
        ) from exc

    symbol = parameters.get("symbol", "SYNTHETIC")
    data_source = parameters.get("data_source", "synthetic")
    initial_capital = float(parameters.get("initial_capital", 10_000.0))
    sma_fast = int(parameters.get("sma_fast", 10))
    sma_slow = int(parameters.get("sma_slow", 30))
    fees = float(parameters.get("fees", 0.001))
    n_days = int(parameters.get("n_days", 504))
    timeframe = parameters.get("timeframe", "1d")
    start_date = parameters.get("start_date")
    end_date = parameters.get("end_date")
    strategy_type = parameters.get("strategy_type", "sma_crossover")

    logger.info(
        "BacktestRunner: starting | source={} symbol={} strategy={} sma=({}/{}) capital={}",
        data_source, symbol, strategy_type, sma_fast,
        sma_slow,
        initial_capital,
    )

    # 1. OHLCV data — synthetic or real
    if data_source == "synthetic":
        data = _generate_ohlcv(n_days=n_days)
    else:
        data = _fetch_market_data(data_source, symbol, start_date, end_date, timeframe)

    close = data["close"]

    # 2. Generate entry/exit signals based on strategy type
    if strategy_type == "macd":
        macd_fast = int(parameters.get("macd_fast", 12))
        macd_slow_w = int(parameters.get("macd_slow", 26))
        macd_signal = int(parameters.get("macd_signal", 9))

        macd = vbt.MACD.run(close, fast_window=macd_fast, slow_window=macd_slow_w,
                            signal_window=macd_signal)
        macd_line = macd.macd
        sig_line = macd.signal

        # Crossover signals (pure pandas — no .vbt accessor dependency)
        entries = (macd_line > sig_line) & (macd_line.shift(fill_value=0.0)
                                            <= sig_line.shift(fill_value=0.0))
        exits = (macd_line < sig_line) & (macd_line.shift(fill_value=0.0)
                                          >= sig_line.shift(fill_value=0.0))

        logger.info("BacktestRunner: MACD({}/{}/{}) signals generated", macd_fast, macd_slow_w
                    , macd_signal)
    else:
        # Default: SMA Crossover
        fast_ma = vbt.MA.run(close, window=sma_fast).ma
        slow_ma = vbt.MA.run(close, window=sma_slow).ma

        # Crossover signals (pure pandas arithmetic — no .vbt accessor dependency)
        entries = (fast_ma > slow_ma) & (
        fast_ma.shift(fill_value=False) <= slow_ma.shift(fill_value=False)
    )
        exits = (fast_ma < slow_ma) & (
        fast_ma.shift(fill_value=False) >= slow_ma.shift(fill_value=False)
    )

    # 3. Portfolio simulation
    portfolio = vbt.Portfolio.from_signals(
        close,
        entries=entries,
        exits=exits,
        init_cash=initial_capital,
        fees=fees,
        freq="D",
    )

    stats = portfolio.stats()

    # portfolio.value is a property (Series) in vbtpro 2025+, callable in OSS vbt
    equity = portfolio.value() if callable(portfolio.value) else portfolio.value

    def _sf(v: Any) -> float | None:
        try:
            f = float(v)
            return None if np.isnan(f) else round(f, 4)
        except (TypeError, ValueError):
            return None

    def _si(v: Any) -> int | None:
        try:
            return int(v)
        except (TypeError, ValueError):
            return None

    metrics: dict[str, Any] = {
        "engine": "vectorbt-opensource",
        "symbol": symbol,
        "data_source": data_source,
        "strategy_type": strategy_type,
        "sma_fast": sma_fast,
        "sma_slow": sma_slow,
        "n_days": len(data),
        "total_return_pct": _sf(stats.get("Total Return [%]")),
        "sharpe_ratio": _sf(stats.get("Sharpe Ratio")),
        "max_drawdown_pct": _sf(stats.get("Max Drawdown [%]")),
        "win_rate_pct": _sf(stats.get("Win Rate [%]")),
        "num_trades": _si(stats.get("Total Trades")),
        "initial_capital": initial_capital,
        "final_capital": _sf(stats.get("End Value")),
        # Downsampled equity curve (≤ 200 pts) for frontend chart
        "equity_curve": [
            {"date": str(d.date()), "value": round(float(v), 2)}
            for d, v in zip(
                equity.index[:: max(1, len(equity) // 200)],
                equity.values[:: max(1, len(equity) // 200)], strict=False,
            )
        ],
    }

    logger.info(
        "BacktestRunner: completed | source={} return={:.2f}% sharpe={} trades={}",
        data_source,
        metrics["total_return_pct"] or 0,
        metrics["sharpe_ratio"],
        metrics["num_trades"],
    )
    return metrics


# ---------------------------------------------------------------------------
# Background task entry-point (called by FastAPI BackgroundTasks)
# ---------------------------------------------------------------------------


def run_vectorbt_backtest(job_id: int, parameters: dict[str, Any]) -> None:
    """Execute a backtest and persist results to the BacktestJob row.

    Status transitions:
        PENDING  →  RUNNING  →  COMPLETED   (success)
                              →  FAILED      (exception)

    This function intentionally swallows all exceptions after logging them
    so it doesn't crash the FastAPI worker thread.
    """
    from datetime import datetime

    from app.db.session import get_session
    from app.models.orm import BacktestJob, JobStatus

    def _utcnow() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    # Mark RUNNING
    try:
        with get_session() as db:
            job = db.get(BacktestJob, job_id)
            if not job:
                logger.error("BacktestRunner: job_id={} not found in DB", job_id)
                return
            job.status = JobStatus.RUNNING
    except Exception as exc:
        logger.error("BacktestRunner: failed to set RUNNING for job_id={}: {}", job_id, exc)
        return

    # Execute
    try:
        metrics = _execute_backtest(parameters)
        with get_session() as db:
            job = db.get(BacktestJob, job_id)
            if not job:
                return
            job.status = JobStatus.COMPLETED
            job.metrics = metrics
            job.total_return_pct = metrics.get("total_return_pct")
            job.sharpe_ratio = metrics.get("sharpe_ratio")
            job.max_drawdown_pct = metrics.get("max_drawdown_pct")
            job.num_trades = metrics.get("num_trades")
            job.final_capital = metrics.get("final_capital")
            job.completed_at = _utcnow()

    except Exception as exc:
        logger.exception("BacktestRunner: job_id={} FAILED: {}", job_id, exc)
        try:
            with get_session() as db:
                job = db.get(BacktestJob, job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.error_message = str(exc)
                    job.completed_at = _utcnow()
        except Exception as inner:
            logger.error("BacktestRunner: could not persist FAILED status: {}", inner)
