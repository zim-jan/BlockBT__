from __future__ import annotations

from collections.abc import Callable
from typing import Any

import pandas as pd
from loguru import logger


class IndicatorRegistry:
    """
    Registry for technical indicators from various libraries (vbt, TA-Lib, etc.).
    Allows discovery and dynamic execution of indicators.
    """
    
    _indicators: dict[str, dict[str, Any]] = {}

    @classmethod
    def register(
        cls, 
        name: str, 
        func: Callable, 
        params: list[dict[str, Any]], 
        library: str = "custom"
    ) -> None:
        """Register a new indicator."""
        cls._indicators[name.lower()] = {
            "name": name,
            "func": func,
            "params": params,
            "library": library
        }
        logger.debug(f"Registered indicator: {name} ({library})")

    @classmethod
    def get_all(cls) -> list[dict[str, Any]]:
        """Return metadata for all registered indicators."""
        return list(cls._indicators.values())

    @classmethod
    def get(cls, name: str) -> dict[str, Any] | None:
        """Get indicator by name."""
        return cls._indicators.get(name.lower())

    @classmethod
    def discover_vbt_indicators(cls, vbt: Any) -> None:
        """Automatically discover indicators from vectorbt."""
        # vectorbt has many indicators. We can register common ones.
        common = ["MA", "EMA", "RSI", "BBANDS", "MACD", "ATR", "STOCH"]
        for name in common:
            if hasattr(vbt, name):
                getattr(vbt, name)
                # We'd need to parse the signature to get params automatically
                # For now, we manual register key ones or use a more generic way
                pass
        
        # Manual registration for common vbt indicators for now
        cls.register(
            "vbt_MA", 
            vbt.MA.run, 
            [{"name": "window", "type": "int", "default": 10}], 
            "vectorbt"
        )
        cls.register(
            "vbt_RSI", 
            vbt.RSI.run, 
            [{"name": "window", "type": "int", "default": 14}], 
            "vectorbt"
        )

    @classmethod
    def discover_talib_indicators(cls) -> None:
        """Discover indicators from TA-Lib."""
        try:
            import talib
            functions = talib.get_functions()
            for _func_name in functions:
                # We can't easily get params for all without more introspection
                # But we can register the existence
                pass
            logger.info(f"Discovered {len(functions)} indicators from TA-Lib")
        except ImportError:
            logger.warning("TA-Lib not installed, skipping discovery")

    @classmethod
    def execute(cls, name: str, data: pd.Series, **kwargs) -> Any:
        """Execute a registered indicator."""
        indicator = cls.get(name)
        if not indicator:
            raise ValueError(f"Indicator {name} not found in registry.")
        
        return indicator["func"](data, **kwargs)

# Initial discovery
def initialize_registry(vbt: Any):
    IndicatorRegistry.discover_vbt_indicators(vbt)
    IndicatorRegistry.discover_talib_indicators()
