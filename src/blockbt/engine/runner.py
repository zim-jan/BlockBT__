"""
run_vectorbt_backtest — Phase 2 background task entry-point.

Wraps OpenSourceEngine with:
  - Synthetic OHLCV data generation (random-walk, no network required).
  - DB persistence: updates BacktestJob status + metrics.
  - Full error capture with FAILED status on any exception.

This function is designed to be called via FastAPI BackgroundTasks:

    background_tasks.add_task(run_vectorbt_backtest, job_id, parameters)
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

# Ensure the vendored vectorbt directory is importable when not pip-installed.
_VENDORED_VBT = Path(__file__).resolve().parents[4] / "vectorbt"
try:
    import vectorbt  # noqa: F401 — check if already installed
except ImportError:
    if _VENDORED_VBT.exists() and str(_VENDORED_VBT) not in sys.path:
        sys.path.insert(0, str(_VENDORED_VBT))


# ---------------------------------------------------------------------------
# Data generation
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


# ---------------------------------------------------------------------------
# Core backtest runner
# ---------------------------------------------------------------------------


def _execute_backtest(parameters: dict[str, Any]) -> dict[str, Any]:
    """Run a vectorbt SMA-crossover backtest on synthetic data.

    Returns a metrics dict on success.
    Raises on failure (caller handles DB persistence of the error).
    """
    try:
        import vectorbt as vbt  # type: ignore[import]
    except ImportError as exc:
        raise RuntimeError(
            "vectorbt is not importable. "
            f"Checked vendored path: {_VENDORED_VBT}"
        ) from exc

    symbol = parameters.get("symbol", "SYNTHETIC")
    initial_capital = float(parameters.get("initial_capital", 10_000.0))
    sma_fast = int(parameters.get("sma_fast", 10))
    sma_slow = int(parameters.get("sma_slow", 30))
    fees = float(parameters.get("fees", 0.001))
    n_days = int(parameters.get("n_days", 504))

    logger.info(
        "BacktestRunner: starting | symbol={} sma=({}/{}) capital={}",
        symbol, sma_fast, sma_slow, initial_capital,
    )

    # 1. OHLCV data — synthetic unless a real connector is wired in Phase 3
    data = _generate_ohlcv(n_days=n_days)
    close = data["close"]

    # 2. SMA indicators (open-source vectorbt only)
    fast_ma = vbt.MA.run(close, window=sma_fast).ma
    slow_ma = vbt.MA.run(close, window=sma_slow).ma

    # 3. Crossover signals (pure pandas arithmetic — no .vbt accessor dependency)
    entries = (fast_ma > slow_ma) & (fast_ma.shift(fill_value=False) <= slow_ma.shift(fill_value=False))
    exits   = (fast_ma < slow_ma) & (fast_ma.shift(fill_value=False) >= slow_ma.shift(fill_value=False))

    # 4. Portfolio simulation
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
        "sma_fast": sma_fast,
        "sma_slow": sma_slow,
        "n_days": n_days,
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
        "BacktestRunner: completed | return={:.2f}% sharpe={} trades={}",
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
    from datetime import datetime, timezone

    from blockbt.models.orm import BacktestJob, JobStatus
    from blockbt.models.session import get_session

    def _utcnow() -> datetime:
        return datetime.now(timezone.utc).replace(tzinfo=None)

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
