from typing import Any

import numpy as np
import pandas as pd
from loguru import logger

from app.services.engine.indicator_registry import IndicatorRegistry


class IndicatorService:
    """
    Service for generating entry and exit signals (entries/exits) based on OHLCV data.
    Supports native vectorbt vectorization for parameters and dynamic registry.
    """

    @staticmethod
    def _get_val(params: dict[str, Any], key: str, default: Any) -> Any:
        """Helper to extract a parameter value, supporting lists for vectorization."""
        val = params.get(key, default)
        if isinstance(val, (list, np.ndarray, pd.Series)):
            return val
        try:
            # Try to convert to int if it's a simple scalar string/float
            return int(val)
        except (TypeError, ValueError):
            return val

    @staticmethod
    def _is_param_list(*params: Any) -> bool:
        """Faza 10: wykrywa wektoryzację parametrów (lista/tablica okien)."""
        return any(isinstance(p, (list, np.ndarray, pd.Series)) for p in params)

    @staticmethod
    def _guard_multi_symbol_params(close: pd.Series | pd.DataFrame, *params: Any) -> bool:
        """
        Faza 10: zwraca True, gdy close reprezentuje wiele symboli (DataFrame — kolumny=symbole).
        Blokuje jednoczesną wektoryzację parametrów i symboli (poza zakresem Fazy 10).
        """
        is_multi_symbol = isinstance(close, pd.DataFrame)
        if is_multi_symbol and IndicatorService._is_param_list(*params):
            raise ValueError(
                "Faza 10 nie wspiera jednoczesnej wektoryzacji parametrów i symboli "
                "(lista okien + wiele tickerów)."
            )
        return is_multi_symbol

    @staticmethod
    def _align_to_symbols(
        indicator: pd.Series | pd.DataFrame, close: pd.Series | pd.DataFrame
    ) -> pd.Series | pd.DataFrame:
        """
        Faza 10: przy DataFrame wieloma symbolami vbt dokleja poziom parametru (np. 'ma_window')
        do kolumn wskaźnika. Sprowadzamy kolumny z powrotem do czystych symboli (close.columns),
        aby crossed_above/portfel operowały na jednoznacznych kluczach per ticker.
        """
        if isinstance(close, pd.DataFrame) and isinstance(indicator, pd.DataFrame):
            aligned = indicator.copy()
            aligned.columns = close.columns
            return aligned
        return indicator

    @staticmethod
    def generate_sma_crossover(
        close: pd.Series, fast_window: Any, slow_window: Any, vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Generate signals based on SMA Crossover strategy.
        Supports vectorization (fast_window and slow_window can be lists).
        Faza 10: obsługuje też DataFrame wielu symboli (broadcasting po kolumnach).
        """
        logger.debug(f"IndicatorService: Generating SMA signals (fast={fast_window}, slow={slow_window})")

        IndicatorService._guard_multi_symbol_params(close, fast_window, slow_window)

        align = IndicatorService._align_to_symbols
        fast_ma = align(vbt.MA.run(close, window=fast_window).ma, close)
        slow_ma = align(vbt.MA.run(close, window=slow_window).ma, close)

        entries = fast_ma.vbt.crossed_above(slow_ma)
        exits = fast_ma.vbt.crossed_below(slow_ma)

        return entries, exits

    @staticmethod
    def generate_macd(
        close: pd.Series, fast: Any, slow: Any, signal: Any, vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Generate signals based on MACD strategy.
        Supports vectorization.
        """
        # Defensive defaults — frontend may send None when fields weren't filled
        fast = fast if fast is not None else 12
        slow = slow if slow is not None else 26
        signal = signal if signal is not None else 9

        logger.debug(f"IndicatorService: Generating MACD signals (fast={fast}, slow={slow}, signal={signal})")

        IndicatorService._guard_multi_symbol_params(close, fast, slow, signal)

        macd = vbt.MACD.run(close, fast_window=fast, slow_window=slow, signal_window=signal)
        macd_line = IndicatorService._align_to_symbols(macd.macd, close)
        signal_line = IndicatorService._align_to_symbols(macd.signal, close)

        entries = macd_line.vbt.crossed_above(signal_line)
        exits = macd_line.vbt.crossed_below(signal_line)

        return entries, exits

    @staticmethod
    def generate_custom(
        close: pd.Series, code_content: str, vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Execute custom Python/vectorbt code to generate signals.
        The code should define 'entries' and 'exits' variables.
        """
        logger.info("IndicatorService: Executing custom strategy code")
        
        local_scope = {
            "close": close,
            "vbt": vbt,
            "np": np,
            "pd": pd,
        }
        
        try:
            # Execute the user code
            exec(code_content, {}, local_scope)
            
            entries = local_scope.get("entries")
            exits = local_scope.get("exits")
            
            if entries is None or exits is None:
                raise ValueError("Custom code must define 'entries' and 'exits' variables.")
                
            return entries, exits
        except Exception as e:
            logger.error(f"Error executing custom strategy code: {e}")
            raise RuntimeError(f"Custom strategy execution failed: {e}") from e

    @classmethod
    def generate_signals(
        cls, close: pd.Series, params: dict[str, Any], vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Orchestrator for signal generation based on the strategy defined in `params`.
        """
        strategy_type = params.get("strategy_type", "sma_crossover").lower()

        if strategy_type == "custom":
            code_content = params.get("code_content", "")
            if not code_content:
                # Fallback or error? Let's try to find it in parameters if not top-level
                code_content = params.get("parameters", {}).get("code_content", "")
            
            if not code_content:
                raise ValueError("Custom strategy type requested but no code_content provided.")
                
            return cls.generate_custom(close, code_content, vbt)

        if strategy_type == "macd":
            fast = cls._get_val(params, "sma_fast", 12)  # Shared UI fields for simplicity
            if "macd_fast" in params:
                fast = cls._get_val(params, "macd_fast", 12)
            
            slow = cls._get_val(params, "sma_slow", 26)
            if "macd_slow" in params:
                slow = cls._get_val(params, "macd_slow", 26)
                
            signal = cls._get_val(params, "macd_signal", 9)

            return cls.generate_macd(close, fast, slow, signal, vbt)

        # --- Bridge: vbt_MA → SMA crossover using DAG params ---
        if strategy_type == "vbt_ma":
            fast_w = cls._get_val(params, "sma_fast", 10)
            slow_w = cls._get_val(params, "sma_slow", 30)
            logger.info(f"IndicatorService: vbt_MA bridge → SMA crossover (fast={fast_w}, slow={slow_w})")
            import vectorbt as vbt_mod
            return cls.generate_sma_crossover(close, fast_w, slow_w, vbt_mod)

        # --- Bridge: vbt_RSI → threshold-based entries/exits ---
        if strategy_type == "vbt_rsi":
            window = cls._get_val(params, "window", 14)
            oversold = float(cls._get_val(params, "oversold", 30))
            overbought = float(cls._get_val(params, "overbought", 70))
            logger.info(f"IndicatorService: vbt_RSI bridge → threshold (win={window}, OS={oversold}, OB={overbought})")
            import vectorbt as vbt_mod
            cls._guard_multi_symbol_params(close, window)
            rsi = vbt_mod.RSI.run(close, window=window).rsi.astype("float64")
            rsi = cls._align_to_symbols(rsi, close)
            entries = rsi.vbt.crossed_below(oversold)  # Buy when RSI < oversold
            exits = rsi.vbt.crossed_above(overbought)   # Sell when RSI > overbought
            return entries, exits

        # Check Indicator Registry (generic path)
        registered = IndicatorRegistry.get(strategy_type)
        if registered:
            logger.info(f"IndicatorService: Executing registry indicator '{strategy_type}'")
            call_params = {}
            for p in registered["params"]:
                p_name = p["name"]
                if p_name in params:
                    call_params[p_name] = cls._get_val(params, p_name, p["default"])
            
            res = IndicatorRegistry.execute(strategy_type, close, **call_params)
            
            if hasattr(res, "entries") and hasattr(res, "exits"):
                return res.entries, res.exits
            if hasattr(res, "signals"):
                return res.signals, ~res.signals
            
            # Safety: if result is not bool-like, raise clear error
            logger.warning(f"Registry indicator '{strategy_type}' returned non-signal object: {type(res)}")
            raise TypeError(
                f"Registry indicator '{strategy_type}' returned {type(res).__name__}, "
                f"not entries/exits. Add explicit bridge in IndicatorService."
            )

        # Default / Fallback: SMA Crossover
        fast_w = cls._get_val(params, "sma_fast", 10)
        slow_w = cls._get_val(params, "sma_slow", 30)

        return cls.generate_sma_crossover(close, fast_w, slow_w, vbt)
