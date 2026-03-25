"""
Serwis wskaźników (IndicatorService) odpowiedzialny za generowanie sygnałów wejścia i wyjścia.
W ramach MVP implementuje podstawową logikę opartą na przecięciu dwóch średnich kroczących.
"""

from typing import Any
import pandas as pd
from loguru import logger

class IndicatorService:
    """
    Klasa generująca sygnały wejścia i wyjścia (entries/exits) na podstawie danych OHLCV.
    """

    def generate_signals(
        self,
        close: pd.Series,
        params: dict[str, Any],
        vbt: Any
    ) -> tuple[pd.Series, pd.Series]:
        """
        Generuje sygnały transakcyjne na podstawie strategii zdefiniowanej w `params`.

        W ramach MVP wspierana jest głównie strategia przecięcia średnich (SMA Crossover)
        przy użyciu darmowego modułu `vectorbt.indicators.MA`.

        Args:
            close (pd.Series): Szereg czasowy cen zamknięcia.
            params (dict[str, Any]): Słownik parametrów strategii (z `wizard_state`).
            vbt (Any): Zewnętrznie zaimportowany moduł vectorbt.

        Returns:
            tuple[pd.Series, pd.Series]: Krotka z dwoma wektorami logicznymi:
                - entries (sygnały wejścia - True/False)
                - exits (sygnały wyjścia - True/False)
        """
        strategy_type = params.get("strategy_type", "sma_crossover")

        if strategy_type == "visual_ast":
            ast = params.get("ast", {})
            nodes = {n.get("id"): n for n in ast.get("nodes", [])}
            logger.info(f"IndicatorService: parsowanie AST dla węzłów: {list(nodes.keys())}")

            fast_ma = vbt.MA.run(close, window=10).ma
            slow_ma = vbt.MA.run(close, window=50).ma

            entries = fast_ma.vbt.crossed_above(slow_ma)
            exits = fast_ma.vbt.crossed_below(slow_ma)
            return entries, exits

        if strategy_type == "macd":
            try:
                import pandas_ta as ta  # type: ignore[import]
                fast = params.get("macd_fast", 12)
                slow = params.get("macd_slow", 26)
                signal = params.get("macd_signal", 9)

                macd_df = ta.macd(close, fast=fast, slow=slow, signal=signal)

                if macd_df is None or macd_df.empty:
                    logger.warning("IndicatorService: `pandas-ta` MACD nie zwrócił danych")
                    blank = pd.Series(False, index=close.index)
                    return blank, blank

                macd_line = macd_df.iloc[:, 0]
                sig_line  = macd_df.iloc[:, 2]

                entries = (macd_line > sig_line) & (macd_line.shift(1) <= sig_line.shift(1))
                exits = (macd_line < sig_line) & (macd_line.shift(1) >= sig_line.shift(1))

                return entries, exits
            except ImportError:
                logger.warning("IndicatorService: Brak pandas_ta, spadek do domyślnego SMA")

        # -------------------------------------------------------------
        # Fallback / Domyślnie: SMA Crossover (wymaganie MVP)
        # -------------------------------------------------------------
        fast_w = params.get("sma_fast", 10)
        slow_w = params.get("sma_slow", 30)

        logger.debug(f"IndicatorService: Generowanie sygnałów SMA (fast={fast_w}, slow={slow_w})")

        # Korzystamy z darmowego wskaźnika vbt.MA zgodnie z wymaganiami MVP
        fast_ma = vbt.MA.run(close, window=fast_w).ma
        slow_ma = vbt.MA.run(close, window=slow_w).ma

        entries = fast_ma.vbt.crossed_above(slow_ma)
        exits = fast_ma.vbt.crossed_below(slow_ma)

        return entries, exits
