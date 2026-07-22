"""Schematy Pydantic dla Dynamic Introspection Engine (Faza 14).

Opisują kontrakt endpointu ``GET /api/v1/registry`` — kuratorowany, deterministyczny
katalog wskaźników oraz kategorii węzłów DAG (BYOL-safe). Klucze API/JSON po angielsku.
"""


from typing import Any

from pydantic import BaseModel, Field


class ParameterSpec(BaseModel):
    """Specyfikacja pojedynczego parametru wskaźnika.

    ``type`` to logiczny typ parametru (np. ``"int"``, ``"float"``, ``"str"``).
    Pola ``min``/``max``/``options`` są opcjonalne i służą walidacji/UI we frontendzie.
    """

    type: str
    default: Any = None
    min: float | int | None = None
    max: float | int | None = None
    options: list[Any] | None = None


class IndicatorSpec(BaseModel):
    """Specyfikacja pojedynczego wskaźnika w katalogu.

    ``library`` wskazuje pochodzenie definicji: ``"blockbt"`` dla natywnego,
    kuratorowanego katalogu lub ``"vectorbt"`` dla wpisów wzbogaconych żywą introspekcją.
    """

    name: str
    library: str
    parameters: dict[str, ParameterSpec] = Field(default_factory=dict)


class NodeCategorySpec(BaseModel):
    """Specyfikacja kategorii węzła DAG i jej dozwolonych następników."""

    category: str
    allowed_targets: list[str] = Field(default_factory=list)


class RegistrySnapshot(BaseModel):
    """Pełny, spójny zrzut rejestru: wskaźniki, kategorie węzłów i macierz kompatybilności."""

    indicators: dict[str, IndicatorSpec]
    node_categories: dict[str, NodeCategorySpec]
    compatibility_matrix: dict[str, list[str]]
