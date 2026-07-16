from __future__ import annotations

from loguru import logger

from app.core.config import settings
from app.services.connectors.base import BaseDataConnector

"""
ConnectorRegistry — auto-discovery and lookup for data provider plugins.

Usage:
    from app.services.connectors.registry import ConnectorRegistry

    connector = ConnectorRegistry.get("yahoo")  # or "alpaca"
    df = connector.fetch("AAPL", "2022-01-01", "2023-12-31")
"""





class ConnectorRegistry:
    """Central registry for all registered data connectors.

    Connectors are registered by key (string).  Lookups are case-insensitive.
    The default connector is determined by ``settings.DATA_CONNECTOR``.
    """

    _registry: dict[str, type[BaseDataConnector]] = {}

    @classmethod
    def register(cls, key: str, connector_class: type[BaseDataConnector]) -> None:
        """Register a connector class under the given key."""
        cls._registry[key.lower()] = connector_class
        logger.debug("ConnectorRegistry: registered {!r}", key)

    @classmethod
    def get(cls, key: str | None = None) -> BaseDataConnector:
        """Instantiate and return a connector by key.

        Falls back to the default connector key from settings if ``key`` is None.
        Raises ``KeyError`` if the key is not registered.
        """
        cls._ensure_defaults_registered()
        resolved = (key or settings.DATA_CONNECTOR).lower()
        if resolved not in cls._registry:
            available = list(cls._registry.keys())
            raise KeyError(f"Unknown connector {resolved!r}. Available: {available}")
        return cls._registry[resolved]()

    @classmethod
    def available(cls) -> list[str]:
        """Return list of registered connector keys."""
        cls._ensure_defaults_registered()
        return list(cls._registry.keys())

    @classmethod
    def _ensure_defaults_registered(cls) -> None:
        """Register built-in connectors if they haven't been yet."""
        if "yahoo" not in cls._registry:
            from app.services.connectors.yahoo_finance import YahooFinanceConnector

            cls.register("yahoo", YahooFinanceConnector)

        if "alpaca" not in cls._registry:
            from app.services.connectors.alpaca import AlpacaConnector

            cls.register("alpaca", AlpacaConnector)

        if "synthetic" not in cls._registry:
            from app.services.connectors.synthetic import SyntheticConnector

            cls.register("synthetic", SyntheticConnector)
