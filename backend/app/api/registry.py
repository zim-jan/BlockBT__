"""Endpointy Dynamic Introspection Engine (Faza 14): ``GET /api/v1/registry/*``.

Pierwszy prefiks ``/api/v1/`` w repo. Odpowiedzi są zwracane **surowo** (nie owinięte
w kopertę ``ApiResponse{success,data,error}``) — zgodnie z kontraktem testu
``test_api/test_registry.py``: top-level klucze odpowiedzi ``/indicators`` to nazwy wskaźników.

Budowa katalogu jest leniwa (w handlerze) i odporna na brak vbt (``runner.vbt is None``).
"""


from typing import Any

from fastapi import APIRouter
from loguru import logger

from app.schemas.registry import IndicatorSpec, NodeCategorySpec, RegistrySnapshot
from app.services.engine.introspection import (
    build_indicator_catalog,
    build_node_catalog,
)

router = APIRouter()


def _get_vbt() -> Any | None:
    """Leniwie pobiera singleton vbt z runnera; zwraca ``None``, gdy niedostępny.

    Import jest wykonywany wewnątrz funkcji (nie na poziomie modułu), aby uniknąć
    kosztownej inicjalizacji vbt przy imporcie routera oraz aby bezpiecznie obsłużyć
    środowiska, w których vbt się nie załadował (guard vbt-null).
    """
    try:
        from app.services.engine.runner import vbt

        return vbt
    except Exception as e:  # noqa: BLE001 — brak vbt nie może blokować rejestru
        logger.debug(f"registry: vbt niedostępny lub import runner.py nieudany: {e}")
        return None


@router.get("/indicators", response_model=dict[str, IndicatorSpec])
def get_indicators() -> dict[str, IndicatorSpec]:
    """Zwraca surowy katalog wskaźników (klucze top-level = nazwy wskaźników)."""
    return build_indicator_catalog(_get_vbt())


@router.get("/nodes", response_model=dict[str, NodeCategorySpec])
def get_nodes() -> dict[str, NodeCategorySpec]:
    """Zwraca surowy katalog kategorii węzłów DAG (klucze = nazwy kategorii)."""
    node_categories, _ = build_node_catalog()
    return node_categories


@router.get("/", response_model=RegistrySnapshot)
def get_snapshot() -> RegistrySnapshot:
    """Zwraca pełny zrzut rejestru: wskaźniki + kategorie węzłów + macierz kompatybilności."""
    node_categories, compatibility_matrix = build_node_catalog()
    return RegistrySnapshot(
        indicators=build_indicator_catalog(_get_vbt()),
        node_categories=node_categories,
        compatibility_matrix=compatibility_matrix,
    )
