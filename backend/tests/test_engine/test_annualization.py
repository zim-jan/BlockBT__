"""
Annualizacja wg timeframe (audyt 2026-07-17, P2).

Silnik przekazywał zawsze ``freq="D"`` do vectorbt, a WFO annualizowało
Sharpe'a stałym 252 — niezależnie od faktycznego timeframe'u danych.
Dla danych intraday metryki annualizowane były liczbowo błędne.

Konwencja: kalendarz giełdowy US (252 sesje/rok, sesja 6.5h).
"""


import math

import numpy as np
import pandas as pd
import pytest

from app.services.engine.opensource_engine import (
    OpenSourceEngine,
    freq_for_timeframe,
    periods_per_year_for_timeframe,
)


def test_freq_for_timeframe_known_values():
    assert freq_for_timeframe("1d") == "D"
    assert freq_for_timeframe("1h") == "60min"
    assert freq_for_timeframe("60m") == "60min"
    assert freq_for_timeframe("30m") == "30min"
    assert freq_for_timeframe("15m") == "15min"
    assert freq_for_timeframe("5m") == "5min"
    assert freq_for_timeframe("1m") == "1min"
    assert freq_for_timeframe("1wk") == "W"


def test_freq_for_timeframe_unknown_falls_back_to_daily():
    assert freq_for_timeframe("13q") == "D"


def test_periods_per_year_for_timeframe_known_values():
    assert periods_per_year_for_timeframe("1d") == 252
    assert periods_per_year_for_timeframe("1h") == 1638  # 252 * 6.5
    assert periods_per_year_for_timeframe("60m") == 1638
    assert periods_per_year_for_timeframe("30m") == 3276
    assert periods_per_year_for_timeframe("1wk") == 52
    assert periods_per_year_for_timeframe("unknown") == 252


def test_sharpe_annualization_respects_timeframe():
    """Te same zwroty per bar: Sharpe(1h) / Sharpe(1d) == sqrt(8760/365) == sqrt(24).

    vectorbt annualizuje przez year_freq/freq — jedyną różnicą między
    przebiegami jest etykieta timeframe, więc stosunek Sharpe'ów musi
    odpowiadać stosunkowi czynników annualizacji.
    """
    idx = pd.date_range("2023-01-01", periods=600, freq="h")
    rng = np.random.default_rng(7)
    close = 100.0 * np.exp(np.cumsum(rng.normal(0.0005, 0.01, len(idx))))
    df = pd.DataFrame({"close": close}, index=idx)

    base = {
        "symbol": "TEST",
        "strategy_type": "sma_crossover",
        "sma_fast": 10,
        "sma_slow": 30,
        "initial_capital": 10000.0,
        "fees": 0.001,
        "slippage": 0.001,
    }

    engine = OpenSourceEngine()
    hourly = engine.run_backtest(df, {**base, "timeframe": "1h"})
    daily_label = engine.run_backtest(df, {**base, "timeframe": "1d"})

    assert hourly["num_trades"] > 0
    assert daily_label["sharpe_ratio"] not in (None, 0.0)
    assert hourly["sharpe_ratio"] == pytest.approx(
        daily_label["sharpe_ratio"] * math.sqrt(24.0), rel=1e-6
    )


class _EquityCurveEngine:
    """Atrapa silnika: deterministyczna krzywa kapitału — do testu WFO."""

    def run_backtest(self, data: pd.DataFrame, params: dict) -> dict:
        # Naprzemienne zwroty ±1% → stała, niezerowa wariancja zwrotów OOS
        values = [10000.0]
        for i in range(len(data) - 1):
            values.append(values[-1] * (1.01 if i % 2 == 0 else 0.99))
        return {
            "status": "COMPLETED",
            "metrics": {"Total Return [%]": 1.0, "Sharpe Ratio": 0.5},
            "equity_curve": [
                {"date": str(ts), "value": v} for ts, v in zip(data.index, values, strict=True)
            ],
        }


def test_wfo_overall_sharpe_respects_timeframe():
    """Łączny Sharpe OOS w WFO annualizowany wg timeframe'u z parametrów."""
    from app.services.engine.optimizer import WalkForwardOptimizer, WfoConfig

    idx = pd.date_range("2022-01-01", periods=400, freq="D")
    df = pd.DataFrame({"close": np.linspace(100.0, 120.0, len(idx))}, index=idx)
    config = WfoConfig(window_size="180d", step_size="60d")

    wfo = WalkForwardOptimizer(_EquityCurveEngine())
    daily = wfo.run_wfo(df, {"timeframe": "1d"}, config)
    hourly_label = wfo.run_wfo(df, {"timeframe": "1h"}, config)

    ratio = (
        hourly_label["overall_metrics"]["Sharpe Ratio"]
        / daily["overall_metrics"]["Sharpe Ratio"]
    )
    assert ratio == pytest.approx(math.sqrt(1638.0 / 252.0), rel=1e-6)
