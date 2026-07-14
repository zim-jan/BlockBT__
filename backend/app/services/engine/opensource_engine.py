"""
OpenSourceEngine — BackBT engine backed by the public vectorbt library.

The vendored ``vectorbt/`` directory is added to sys.path at load time so no
pip installation is strictly required if the folder exists.
"""

from __future__ import annotations

import sys
from typing import Any

import numpy as np
import pandas as pd
import quantstats as qs
from loguru import logger

from app.core.config import settings
from app.services.engine.base import BaseStrategyEngine
from app.services.engine.indicators import IndicatorService

# Make vendored vectorbt importable ONLY if it is not already installed or we want to force it.
_VENDORED_VBT = settings.PROJECT_ROOT / "vectorbt_src"

def _setup_vbt() -> Any:
    """Import vectorbt and configure the engine."""
    try:
        import vectorbt as vbt
        # Check if it's the new version that supports rust
        v_major = int(getattr(vbt, "__version__", "0.0.0").split(".")[0])
        if v_major < 1 and _VENDORED_VBT.exists():
            # Fallback to vendored if installed is too old
            if str(_VENDORED_VBT) not in sys.path:
                sys.path.insert(0, str(_VENDORED_VBT))
            import importlib
            vbt = importlib.reload(vbt)
    except ImportError:
        if _VENDORED_VBT.exists():
            if str(_VENDORED_VBT) not in sys.path:
                sys.path.insert(0, str(_VENDORED_VBT))
            import vectorbt as vbt
        else:
            raise ImportError("vectorbt not found (neither installed nor vendored)") from None

    # Configure engine
    target_engine = settings.VBT_ENGINE.lower()
    try:
        if target_engine == "rust":
            # Verify if rust kernels are actually available
            # vbt.settings['engine'] = 'rust' might fail later if binaries missing
            # We try to set it and see if it sticks or if we can detect it.
            vbt.settings["engine"] = "rust"
            logger.info("OpenSourceEngine: Using Rust engine.")
        else:
            vbt.settings["engine"] = "numba"
            logger.info("OpenSourceEngine: Using Numba engine.")
    except Exception as e:
        logger.warning(
            "OpenSourceEngine: Failed to set engine '{}', falling back to numba: {}",
            target_engine,
            e,
        )
        vbt.settings["engine"] = "numba"
    
    return vbt

class OpenSourceEngine(BaseStrategyEngine):
    """Backtest engine using the public open-source ``vectorbt`` library.

    Supports Numba and Rust engines (since v1.0.0).
    """

    ENGINE_NAME = "opensource"

    def __init__(self) -> None:
        """Initialize the OpenSource engine, verifying dependencies are present."""
        super().__init__()
        self.vbt = _setup_vbt()

    def _ensure_vectorbt(self) -> None:
        """Check if vectorbt can be imported (legacy, kept for compatibility)."""
        pass

    def get_engine_info(self) -> dict[str, str]:
        """Return metadata about this engine installation."""
        return {
            "name": self.ENGINE_NAME,
            "version": getattr(self.vbt, "__version__", "unknown"),
            "mode": "live",
            "library": "vectorbt (open-source)",
            "engine": self.vbt.settings.get("engine", "numba"),
            "vbt_path": str(_VENDORED_VBT) if _VENDORED_VBT.exists() else "installed",
        }

    def run_backtest(self, data: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
        """Run a vectorbt-powered backtest.
        Supports both single-run and vectorized (multi-parameter) execution.
        """
        vbt = self.vbt

        # Ensure datetime index
        if not isinstance(data.index, pd.DatetimeIndex):
            data.index = pd.to_datetime(data.index)

        # Ensure float data for Rust engine compatibility
        if not np.issubdtype(data["close"].dtype, np.floating):
            data = data.copy()
            data["close"] = data["close"].astype(np.float64)

        # Build entries / exits using consolidated IndicatorService
        entries, exits = IndicatorService.generate_signals(data["close"], params, vbt)

        # Simulate
        initial_capital = float(params.get("initial_capital", 10000.0))
        fees_param = params.get("fees", 0.001)
        if isinstance(fees_param, dict):
            fees = float(fees_param.get("commission_pct", 0.001))
        else:
            fees = float(fees_param)

        is_vectorized = isinstance(entries, pd.DataFrame)
        logger.info(
            "Executing vectorbt portfolio... (shape={}, capital={}, vectorized={})",
            data.shape,
            initial_capital,
            is_vectorized,
        )

        portfolio = vbt.Portfolio.from_signals(
            data["close"],
            entries,
            exits,
            init_cash=initial_capital,
            fees=fees,
            freq="D",  # vectorbt needs frequency for annualisation
        )

        symbol = params.get("symbol", "UNKNOWN")
        timeframe = params.get("timeframe", "1d")

        if not is_vectorized:
            # Standard single result
            stats = portfolio.stats()
            
            total_return = float(portfolio.total_return() * 100)
            sharpe = float(portfolio.sharpe_ratio())
            drawdown = float(portfolio.max_drawdown() * 100)
            
            if portfolio.trades.count() > 0:
                win_rate = float(portfolio.trades.win_rate() * 100)
            else:
                win_rate = 0.0
                
            trades_count = int(portfolio.trades.count())
            
            if len(portfolio.value()) > 0:
                final_val = float(portfolio.value().iloc[-1])
            else:
                final_val = initial_capital

            # QuantStats integration
            qs_metrics = {}
            try:
                # Get extended metrics from QuantStats directly on the returns
                qs_report = qs.reports.metrics(portfolio.returns(), display=False)
                if isinstance(qs_report, pd.Series):
                    qs_metrics = {
                        str(k): float(v) if not isinstance(v, (str, type(None))) else v
                        for k, v in qs_report.to_dict().items()
                    }
                elif isinstance(qs_report, pd.DataFrame):
                    # QuantStats metrics often returns a DataFrame where metrics are 
                    # index and strategy is column. We want a flat dict.
                    if "Strategy" in qs_report.columns:
                        qs_metrics = {
                            str(k): float(v) if not isinstance(v, (str, type(None))) else v
                            for k, v in qs_report["Strategy"].to_dict().items()
                        }
                    else:
                        qs_metrics = qs_report.to_dict()
            except Exception as e:
                logger.warning("QuantStats failed to generate metrics: {}", e)

            response_metrics = {
                "Total Return [%]": total_return,
                "Sharpe Ratio": sharpe,
                "Max Drawdown [%]": drawdown,
                "Total Trades": trades_count,
                "Final Value": final_val,
                "Win Rate [%]": win_rate,
            }
            response_metrics.update(qs_metrics)

            # Format equity curve for frontend
            equity_curve = []
            try:
                if isinstance(portfolio.value(), pd.Series):
                    curve_series = portfolio.value()
                    equity_curve = [
                        {"date": str(idx), "value": float(val)} 
                        for idx, val in curve_series.items()
                    ]
            except Exception as e:
                logger.warning("Failed to format equity curve: {}", e)

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "engine_name": self.ENGINE_NAME,
                "status": "COMPLETED",
                "total_return_pct": total_return,
                "sharpe_ratio": sharpe,
                "max_drawdown_pct": drawdown,
                "win_rate_pct": win_rate,
                "num_trades": trades_count,
                "initial_capital": initial_capital,
                "final_capital": final_val,
                "equity_curve": equity_curve,
                "metrics": response_metrics,
                "raw": stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
            }
        else:
            # Vectorized multi-result
            total_return = portfolio.total_return() * 100
            sharpe = portfolio.sharpe_ratio()
            drawdown = portfolio.max_drawdown() * 100
            trades_count = portfolio.trades.count()
            final_value = portfolio.value().iloc[-1]
            win_rate = portfolio.trades.win_rate() * 100

            # Convert MultiIndex to list of dictionaries
            results_list = []
            for i in range(len(total_return)):
                tr_val = float(total_return.iloc[i])
                
                # Sharpe Ratio can be NaN if no trades or zero volatility
                sr_val = float(sharpe.iloc[i]) if not np.isnan(sharpe.iloc[i]) else 0.0
                
                dd_val = float(drawdown.iloc[i])
                tc_val = int(trades_count.iloc[i])
                fv_val = float(final_value.iloc[i])
                
                # Win Rate can be NaN if no trades
                wr_val = float(win_rate.iloc[i]) if not np.isnan(win_rate.iloc[i]) else 0.0

                results_list.append({
                    "metrics": {
                        "Total Return [%]": tr_val,
                        "Sharpe Ratio": sr_val,
                        "Max Drawdown [%]": dd_val,
                        "Total Trades": tc_val,
                        "Final Value": fv_val,
                        "Win Rate [%]": wr_val,
                    }
                })

            return {
                "symbol": symbol,
                "timeframe": timeframe,
                "engine_name": self.ENGINE_NAME,
                "status": "COMPLETED",
                "is_vectorized": True,
                "vectorized_results": results_list,
            }

    @staticmethod
    def _find_close_level(columns: pd.MultiIndex) -> int:
        """Faza 10: poziom kolumnowego MultiIndex z polem 'close' (case-insensitive)."""
        for lvl in range(columns.nlevels):
            values = {str(v).lower() for v in columns.get_level_values(lvl)}
            if "close" in values:
                return lvl
        raise ValueError("Kolumnowy MultiIndex nie zawiera pola 'close'.")

    def _prepare_close(self, data: pd.DataFrame) -> pd.Series | pd.DataFrame:
        """
        Faza 10: przygotowuje ceny zamknięcia do wektoryzacji broadcastingiem.

        - Wierszowy 2-poziomowy MultiIndex [symbol, date] (format LONG z konektorów i testu red)
          → pivot do WIDE: index=daty, kolumny=symbole (broadcasting po kolumnach, bez pętli).
        - Kolumnowy MultiIndex (styl vbt.YFData: pola OHLCV × symbole) → wybór pola 'close'.
        - Zwykły single-symbol DataFrame → Series 'close' (zachowanie z faz 1–9).

        Wyrównanie NaN różnych kalendarzy: ffill + dropna(how='any') (udokumentowane uproszczenie).
        Rust engine wymaga float64. Zastępuje pd.to_datetime(index), które crashowało na MultiIndex.
        """
        # 1) Wierszowy MultiIndex [symbol, date] → WIDE (kolumny = symbole)
        if isinstance(data.index, pd.MultiIndex) and data.index.nlevels >= 2:
            if "close" not in data.columns:
                raise ValueError("Wejście multi-symbol wymaga kolumny 'close'.")
            index_names = list(data.index.names or [])
            level: Any = "symbol" if "symbol" in index_names else 0
            wide = data["close"].sort_index().unstack(level=level)
            if not isinstance(wide.index, pd.DatetimeIndex):
                wide.index = pd.to_datetime(wide.index)
            # daty rosnąco + deterministyczna kolejność symboli
            wide = wide.sort_index().sort_index(axis=1)
            wide = wide.ffill().dropna(how="any").astype(np.float64)
            return wide

        # 2) Kolumnowy MultiIndex (pola × symbole) → wybór 'close'
        if isinstance(data.columns, pd.MultiIndex):
            close_wide = data.xs("close", axis=1, level=self._find_close_level(data.columns))
            if not isinstance(close_wide.index, pd.DatetimeIndex):
                close_wide.index = pd.to_datetime(close_wide.index)
            close_wide = close_wide.sort_index().sort_index(axis=1)
            close_wide = close_wide.ffill().dropna(how="any").astype(np.float64)
            return close_wide

        # 3) Single-symbol → Series (dotychczasowe zachowanie)
        if not isinstance(data.index, pd.DatetimeIndex):
            data = data.copy()
            data.index = pd.to_datetime(data.index)
        close = data["close"]
        if not np.issubdtype(close.dtype, np.floating):
            close = close.astype(np.float64)
        return close

    def run_dag_backtest(self, data: pd.DataFrame, dag: dict[str, Any]) -> dict[str, Any]:
        """Execute a vectorbt backtest driven directly by the DAG schema.

        Faza 10: wykrywa wejście multi-symbol (MultiIndex) i wektoryzuje backtest po kolumnach,
        zwracając metryki oraz krzywe kapitału zgrupowane per ticker.
        """
        vbt = self.vbt

        # Faza 10: pivot LONG→WIDE (multi) albo Series (single); zastępuje crashujący pd.to_datetime
        close = self._prepare_close(data)
        is_multi = isinstance(close, pd.DataFrame)

        nodes = dag.get("nodes", [])
        data_node = next((n for n in nodes if n.get("category") == "DataIngestion"), {})
        ind_node = next((n for n in nodes if n.get("category") == "Indicators"), {})
        exec_node = next((n for n in nodes if n.get("category") == "Execution"), {})

        ind_params = ind_node.get("params", {})
        exec_params = exec_node.get("params", {})
        data_params = data_node.get("params", {})

        symbol = data_params.get("symbol", "UNKNOWN")
        timeframe = data_params.get("timeframe", "1d")

        # Map DAG indicator parameters to IndicatorService format
        flat_params = {
            "strategy_type": ind_params.get("indicatorType", "sma_crossover"),
            "sma_fast": ind_params.get("smaFast", 10),
            "sma_slow": ind_params.get("smaSlow", 30),
            "macd_fast": ind_params.get("macdFast", 12),
            "macd_slow": ind_params.get("macdSlow", 26),
            "macd_signal": ind_params.get("macdSignal", 9),
            "code_content": ind_params.get("codeContent", "")
        }

        # Indicators & LogicOperators (close: Series single lub DataFrame multi-symbol)
        entries, exits = IndicatorService.generate_signals(close, flat_params, vbt)

        # Apply TimeShift if LogicOperators node with time_shift present (Look-ahead Bias prevention)
        logic_nodes = [n for n in nodes if n.get("category") == "LogicOperators"]
        for logic_node in logic_nodes:
            lp = logic_node.get("params", {})
            if lp.get("operator_type") == "time_shift":
                shift = int(lp.get("shift_periods", 1))
                entries = self.apply_time_shift(entries, shift)
                exits = self.apply_time_shift(exits, shift)
                logger.info(f"Applied fshift({shift}) for Look-ahead Bias prevention.")

        # Execution
        initial_capital = float(exec_params.get("init_cash", exec_params.get("initialCapital", 10000.0)))
        portfolio = self.execute_dag_portfolio(
            price_data=close,
            entries=entries,
            exits=exits,
            params=exec_params
        )

        # Faza 10: gałąź multi-symbol — metryki i krzywe kapitału per ticker z wektorowych Series.
        if is_multi:
            return self._build_multi_symbol_result(portfolio, close, timeframe)

        stats = portfolio.stats()
        total_return = float(portfolio.total_return() * 100)
        sharpe = float(portfolio.sharpe_ratio())
        drawdown = float(portfolio.max_drawdown() * 100)
        
        if portfolio.trades.count() > 0:
            win_rate = float(portfolio.trades.win_rate() * 100)
        else:
            win_rate = 0.0
            
        trades_count = int(portfolio.trades.count())
        if len(portfolio.value()) > 0:
            final_val = float(portfolio.value().iloc[-1])
        else:
            final_val = initial_capital

        qs_metrics = {}
        try:
            qs_report = qs.reports.metrics(portfolio.returns(), display=False)
            if isinstance(qs_report, pd.Series):
                qs_metrics = {str(k): float(v) if not isinstance(v, (str, type(None))) else v for k, v in qs_report.to_dict().items()}
            elif isinstance(qs_report, pd.DataFrame):
                if "Strategy" in qs_report.columns:
                    qs_metrics = {str(k): float(v) if not isinstance(v, (str, type(None))) else v for k, v in qs_report["Strategy"].to_dict().items()}
                else:
                    qs_metrics = qs_report.to_dict()
        except Exception as e:
            logger.warning("QuantStats failed: {}", e)

        response_metrics = {
            "Total Return [%]": total_return,
            "Sharpe Ratio": sharpe,
            "Max Drawdown [%]": drawdown,
            "Total Trades": trades_count,
            "Final Value": final_val,
            "Win Rate [%]": win_rate,
        }
        response_metrics.update(qs_metrics)

        equity_curve = []
        try:
            if isinstance(portfolio.value(), pd.Series):
                equity_curve = [{"date": str(idx), "value": float(val)} for idx, val in portfolio.value().items()]
        except Exception as e:
            logger.warning("Failed equity curve: {}", e)

        return {
            "symbol": symbol,
            "timeframe": timeframe,
            "engine_name": self.ENGINE_NAME,
            "status": "COMPLETED",
            "total_return_pct": total_return,
            "sharpe_ratio": sharpe,
            "max_drawdown_pct": drawdown,
            "win_rate_pct": win_rate,
            "num_trades": trades_count,
            "initial_capital": initial_capital,
            "final_capital": final_val,
            "equity_curve": equity_curve,
            "metrics": response_metrics,
            "raw": stats.to_dict() if hasattr(stats, "to_dict") else dict(stats),
        }

    @staticmethod
    def _finite_or_zero(value: Any) -> float:
        """Faza 10: guard NaN/inf → 0.0 (stała cena → 0 trade → Sharpe=inf, Win Rate=NaN)."""
        try:
            fval = float(value)
        except (TypeError, ValueError):
            return 0.0
        return fval if np.isfinite(fval) else 0.0

    def _build_multi_symbol_result(
        self, portfolio: Any, close: pd.DataFrame, timeframe: str
    ) -> dict[str, Any]:
        """
        Faza 10: wynik multi-symbol z wektorowych metryk vbt (Series indeksowane symbolem).
        Pomija stats()/QuantStats (single-column-oriented w OSS vbt) — metryki liczone wprost, per ticker.
        Pętla jedynie serializuje wyniki do JSON (obliczenia pozostają zwektoryzowane).
        """
        symbols = [str(s) for s in close.columns]

        total_return = portfolio.total_return() * 100
        sharpe = portfolio.sharpe_ratio()
        drawdown = portfolio.max_drawdown() * 100
        trades_count = portfolio.trades.count()
        win_rate = portfolio.trades.win_rate() * 100
        value = portfolio.value()  # DataFrame: index=daty, kolumny=symbole
        final_value = value.iloc[-1]

        metrics: dict[str, dict[str, float]] = {}
        equity_curve: dict[str, list[dict[str, Any]]] = {}
        for sym in symbols:
            metrics[sym] = {
                "Total Return [%]": self._finite_or_zero(total_return.get(sym)),
                "Sharpe Ratio": self._finite_or_zero(sharpe.get(sym)),
                "Max Drawdown [%]": self._finite_or_zero(drawdown.get(sym)),
                "Total Trades": int(self._finite_or_zero(trades_count.get(sym))),
                "Final Value": self._finite_or_zero(final_value.get(sym)),
                "Win Rate [%]": self._finite_or_zero(win_rate.get(sym)),
            }
            col = value[sym]
            equity_curve[sym] = [
                {"date": str(idx), "value": float(val)} for idx, val in col.items()
            ]

        return {
            "symbol": symbols,
            "symbols": symbols,
            "is_multi_symbol": True,
            "timeframe": timeframe,
            "engine_name": self.ENGINE_NAME,
            "status": "COMPLETED",
            "metrics": metrics,
            "equity_curve": equity_curve,
        }

    def apply_typing_cast(self, tensor: pd.Series | pd.DataFrame, cast_type: str = "float64") -> np.ndarray:
        """
        Prewencja Numba Typing Errors.
        Rzutuje dane wejściowe na jednorodny typ przed kompilacją JIT.
        """
        try:
            if cast_type == "float64":
                return np.asarray(tensor, dtype=np.float64)
            elif cast_type == "bool":
                return np.asarray(tensor, dtype=np.bool_)
            return np.asarray(tensor)
        except Exception as e:
            logger.error(f"Typing Cast Error: {e}")
            raise ValueError(f"Nie można zrzutować tensora na typ {cast_type}. Numba JIT zablokowana.")

    def apply_time_shift(self, signal_tensor: pd.Series | pd.DataFrame, periods: int = 1) -> pd.Series | pd.DataFrame:
        """
        Prewencja Look-ahead Bias.
        Przesuwa maskę logiczną o N okresów do przodu używając natywnego vbt.fshift.
        Rust engine wymaga float64 — castujemy bool→float64→fshift→bool.
        """
        logger.debug(f"Aplikowanie fshift({periods}) na tensorze sygnałów.")
        # Rust engine: bool → float64 → fshift → bool
        float_tensor = signal_tensor.astype("float64")
        shifted = float_tensor.vbt.fshift(periods)
        return shifted.fillna(0.0).astype(bool)

    def execute_dag_portfolio(
        self,
        price_data: pd.Series | pd.DataFrame,
        entries: pd.Series | pd.DataFrame,
        exits: pd.Series | pd.DataFrame,
        params: dict,
    ) -> Any:
        """
        Egzekucja portfela z wymuszonymi parametrami kosztowymi (Zero-Cost Fallacy).
        Faza 10: przy DataFrame (wiele symboli) from_signals broadcastuje po kolumnach.
        """
        fees = float(params.get("fees", 0.001))
        slippage = float(params.get("slippage", 0.001))
        init_cash = float(params.get("init_cash", 10000.0))

        if fees <= 0 or slippage <= 0:
            raise ValueError("Zero-Cost Fallacy: Fees i Slippage muszą być > 0.")

        return self.vbt.Portfolio.from_signals(
            close=price_data,
            entries=entries,
            exits=exits,
            init_cash=init_cash,
            fees=fees,
            slippage=slippage,
            freq="D"
        )