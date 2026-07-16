"""Testy SyntheticConnector (review Janka 2026-07-16).

Źródło 'synthetic' nie istniało w ogóle (Unknown connector), a frontend
blokował multi-symbol. Konektor musi generować deterministyczny random-walk
OHLCV offline i dziedziczyć format LONG MultiIndex [symbol, date] z bazy.
"""

import pandas as pd

from app.services.connectors.registry import ConnectorRegistry
from app.services.connectors.synthetic import SyntheticConnector

START, END = "2023-01-01", "2023-06-30"


def _connector(tmp_path) -> SyntheticConnector:
    return SyntheticConnector(cache_dir=tmp_path)


def test_registered_in_registry():
    assert "synthetic" in ConnectorRegistry.available()
    assert isinstance(ConnectorRegistry.get("synthetic"), SyntheticConnector)


def test_single_symbol_ohlcv(tmp_path):
    df = _connector(tmp_path).fetch("SYNTA", START, END, use_cache=False)

    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
    assert len(df) > 100
    assert df.index.min() >= pd.Timestamp(START)
    assert df.index.max() <= pd.Timestamp(END)
    # Spójność OHLC: high/low obejmują open i close, ceny dodatnie
    assert (df["high"] >= df[["open", "close"]].max(axis=1) - 1e-9).all()
    assert (df["low"] <= df[["open", "close"]].min(axis=1) + 1e-9).all()
    assert (df["close"] > 0).all()


def test_deterministic_same_call(tmp_path):
    a = _connector(tmp_path).fetch("SYNTA", START, END, use_cache=False)
    b = _connector(tmp_path).fetch("SYNTA", START, END, use_cache=False)
    pd.testing.assert_frame_equal(a, b)


def test_different_symbols_differ(tmp_path):
    a = _connector(tmp_path).fetch("SYNTA", START, END, use_cache=False)
    b = _connector(tmp_path).fetch("SYNTB", START, END, use_cache=False)
    assert not a["close"].equals(b["close"])


def test_multi_symbol_long_format(tmp_path):
    df = _connector(tmp_path).fetch(["SYNTA", "SYNTB"], START, END, use_cache=False)

    assert isinstance(df.index, pd.MultiIndex)
    assert df.index.names == ["symbol", None] or df.index.names[0] == "symbol"
    assert set(df.index.get_level_values("symbol")) == {"SYNTA", "SYNTB"}
    assert list(df.columns) == ["open", "high", "low", "close", "volume"]
