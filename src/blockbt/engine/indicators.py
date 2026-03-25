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
            fast = params.get("macd_fast", 12)
            slow = params.get("macd_slow", 26)
            signal = params.get("macd_signal", 9)

            # Korzystamy z natywnego wskaźnika vbt.MACD w celach wektoryzacji
            macd = vbt.MACD.run(close, fast_window=fast, slow_window=slow, signal_window=signal)

            macd_line = macd.macd
            sig_line = macd.signal

            entries = macd_line.vbt.crossed_above(sig_line)
            exits = macd_line.vbt.crossed_below(sig_line)

            return entries, exits

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
