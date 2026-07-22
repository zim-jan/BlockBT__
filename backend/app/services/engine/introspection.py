"""Dynamic Introspection Engine (Faza 14).

Buduje deterministyczny, BYOL-safe katalog wskaźników oraz kategorii węzłów DAG.

Zasady architektoniczne:
- **Źródłem prawdy jest kuratorowany katalog** (semantyka natywna BlockBT: ``SMA``, ``MACD``,
  ``RSI`` z parametrami ``fast_window``/``slow_window``/``signal_window``/``window``).
  Nie jest to proxy dla ``vbt.MA`` ani dla ``IndicatorRegistry.get_all()``.
- Żywa introspekcja ``vectorbt`` jest wyłącznie **opcjonalnym wzbogaceniem** — dodaje wpisy
  pod prefiksem ``vbt_*`` i jest w pełni owinięta w ``try/except`` (nigdy nie wywraca handlera).
- Kategorie węzłów i macierz kompatybilności są **importowane** z ``GraphParser``
  (jedno źródło prawdy — bez duplikacji).

Budowa katalogu jest leniwa (wywoływana w handlerze API), nie przy imporcie modułu.
"""


from typing import Any

from loguru import logger

from app.core.utils.graph_parser import GraphParser
from app.schemas.registry import IndicatorSpec, NodeCategorySpec, ParameterSpec

# Kandydaci do opcjonalnego wzbogacenia żywą introspekcją vectorbt.
# Wpisy trafiają do katalogu pod prefiksem ``vbt_*`` i nie nadpisują wpisów kuratorowanych.
_VBT_ENRICH_CANDIDATES: tuple[str, ...] = (
    "MA",
    "EMA",
    "RSI",
    "BBANDS",
    "MACD",
    "ATR",
    "STOCH",
)


def _curated_indicators() -> dict[str, IndicatorSpec]:
    """Zwraca kuratorowany katalog wskaźników (deterministyczne źródło prawdy)."""
    return {
        "SMA": IndicatorSpec(
            name="SMA",
            library="blockbt",
            parameters={
                "fast_window": ParameterSpec(type="int", default=10, min=1),
                "slow_window": ParameterSpec(type="int", default=30, min=1),
            },
        ),
        "MACD": IndicatorSpec(
            name="MACD",
            library="blockbt",
            parameters={
                "fast_window": ParameterSpec(type="int", default=12, min=1),
                "slow_window": ParameterSpec(type="int", default=26, min=1),
                "signal_window": ParameterSpec(type="int", default=9, min=1),
            },
        ),
        "RSI": IndicatorSpec(
            name="RSI",
            library="blockbt",
            parameters={
                "window": ParameterSpec(type="int", default=14, min=1),
            },
        ),
    }


def _enrich_from_vbt(catalog: dict[str, IndicatorSpec], vbt: Any) -> None:
    """Best-effort wzbogacenie katalogu o żywe wskaźniki vectorbt (pod prefiksem ``vbt_*``).

    Odczytuje wyłącznie statyczne metadane (``param_names``) klas fabryk wskaźników vbt.
    Nie wykonuje żadnego kodu na danych zewnętrznych. Każdy pojedynczy kandydat jest
    izolowany try/except, by częściowa niedostępność nie psuła całego katalogu.

    Uwaga: pole ``type`` dla wpisów ``vbt_*`` jest wartością domyślną/przybliżoną
    (zawsze ``"int"``) — nie jest introspekowane z faktycznego typu parametru vbt.
    To czysto opisowa metadana dla frontendu, nie odzwierciedla rzeczywistego typu.
    """
    for name in _VBT_ENRICH_CANDIDATES:
        try:
            factory = getattr(vbt, name, None)
            if factory is None:
                continue
            param_names = getattr(factory, "param_names", None) or []
            parameters = {p: ParameterSpec(type="int") for p in param_names}
            key = f"vbt_{name}"
            # Nie nadpisujemy wpisów kuratorowanych — prefiks vbt_ gwarantuje rozłączność kluczy.
            catalog.setdefault(
                key,
                IndicatorSpec(name=key, library="vectorbt", parameters=parameters),
            )
        except Exception as e:  # noqa: BLE001 — pojedynczy kandydat nie może wywrócić katalogu
            logger.debug(f"introspection: pominięto wzbogacenie vbt dla {name}: {e}")


def build_indicator_catalog(vbt: Any = None) -> dict[str, IndicatorSpec]:
    """Buduje katalog wskaźników: kuratorowany rdzeń + opcjonalne wzbogacenie vbt.

    Args:
        vbt: instancja modułu vectorbt (może być ``None`` — wtedy zwracany jest sam
            deterministyczny rdzeń kuratorowany).

    Returns:
        Mapowanie ``nazwa -> IndicatorSpec``. Zawsze zawiera co najmniej ``SMA``, ``MACD``, ``RSI``.
    """
    catalog = _curated_indicators()
    if vbt is not None:
        try:
            _enrich_from_vbt(catalog, vbt)
        except Exception as e:  # noqa: BLE001 — wzbogacenie jest opcjonalne i nie może psuć rdzenia
            logger.debug(f"introspection: wzbogacenie vbt pominięte całościowo: {e}")
    return catalog


def build_node_catalog() -> tuple[dict[str, NodeCategorySpec], dict[str, list[str]]]:
    """Buduje katalog kategorii węzłów DAG na podstawie ``GraphParser.COMPATIBILITY_MATRIX``.

    Returns:
        Krotka ``(node_categories, compatibility_matrix)`` — obie struktury pochodzą
        z jednego źródła prawdy (``GraphParser``), bez duplikacji logiki.
    """
    matrix: dict[str, list[str]] = {
        category: list(targets)
        for category, targets in GraphParser.COMPATIBILITY_MATRIX.items()
    }
    node_categories = {
        category: NodeCategorySpec(category=category, allowed_targets=list(targets))
        for category, targets in matrix.items()
    }
    return node_categories, matrix
