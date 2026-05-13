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
    def generate_sma_crossover(
        close: pd.Series, fast_window: Any, slow_window: Any, vbt: Any
    ) -> tuple[pd.Series | pd.DataFrame, pd.Series | pd.DataFrame]:
        """
        Generate signals based on SMA Crossover strategy.
        Supports vectorization (fast_window and slow_window can be lists).
        """
        logger.debug(f"IndicatorService: Generating SMA signals (fast={fast_window}, slow={slow_window})")

        fast_ma = vbt.MA.run(close, window=fast_window).ma
        slow_ma = vbt.MA.run(close, window=slow_window).ma

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
        logger.debug(f"IndicatorService: Generating MACD signals (fast={fast}, slow={slow}, signal={signal})")

        macd = vbt.MACD.run(close, fast_window=fast, slow_window=slow, signal_window=signal)

        entries = macd.macd.vbt.crossed_above(macd.signal)
        exits = macd.macd.vbt.crossed_below(macd.signal)

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

        # Check Indicator Registry
        registered = IndicatorRegistry.get(strategy_type)
        if registered:
            logger.info(f"IndicatorService: Executing registry indicator '{strategy_type}'")
            # Filter params that are in registered['params']
            call_params = {}
            for p in registered["params"]:
                p_name = p["name"]
                if p_name in params:
                    call_params[p_name] = cls._get_val(params, p_name, p["default"])
            
            # Execute
            res = IndicatorRegistry.execute(strategy_type, close, **call_params)
            
            # Handle results (vbt indicators return an object with signals or just signals)
            if hasattr(res, "entries") and hasattr(res, "exits"):
                return res.entries, res.exits
            if hasattr(res, "signals"):
                return res.signals, ~res.signals # Fallback
            
            # Generic fallback for registry
            return res, ~res

        # Default / Fallback: SMA Crossover
        fast_w = cls._get_val(params, "sma_fast", 10)
        slow_w = cls._get_val(params, "sma_slow", 30)

        return cls.generate_sma_crossover(close, fast_w, slow_w, vbt)
