"""
Sanityzacja ścieżek cache Parquet (audyt 2026-07-17, P2 — path traversal).

``start``/``end``/``timeframe`` pochodzą wprost z parametrów węzła DAG
(frontend), a były interpolowane surowo do nazwy pliku — wartość w stylu
``../../evil`` uciekała poza katalog cache przy zapisie Parquet.
"""

from __future__ import annotations

import pytest

from app.services.connectors.synthetic import SyntheticConnector


@pytest.fixture()
def connector() -> SyntheticConnector:
    return SyntheticConnector()


@pytest.mark.parametrize(
    "kwargs",
    [
        {"start": "../../evil", "end": "2024-01-01", "timeframe": "1d"},
        {"start": "2023-01-01", "end": "../../../tmp/pwned", "timeframe": "1d"},
        {"start": "2023-01-01", "end": "2024-01-01", "timeframe": "../x"},
        {"start": "2023-01-01", "end": "2024-01-01", "timeframe": "1d/../.."},
    ],
)
def test_cache_path_rejects_path_traversal(connector, kwargs):
    with pytest.raises(ValueError):
        connector._cache_path("AAPL", **kwargs)


def test_cache_path_stays_inside_cache_dir(connector):
    path = connector._cache_path("BTC/USD", "2023-01-01", "2024-01-01", "1d")
    assert path.resolve().is_relative_to(connector._cache_dir.resolve())
    assert path.name == "2023-01-01_2024-01-01_1d.parquet"
