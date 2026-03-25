"""
EngineLoader — BYOL-aware engine selector.

Determines at runtime which engine to instantiate:
  1. If ``PREFER_PRO_ENGINE=true`` in config AND vbtpro is importable → ProEngine
  2. If vbtpro path exists AND vbtpro is importable                  → ProEngine
  3. Otherwise                                                        → OpenSourceEngine

Import once at startup; the result is cached.
"""

from __future__ import annotations

from loguru import logger

from blockbt.config import settings
from blockbt.engine.base import BaseStrategyEngine


class EngineLoader:
    """Singleton-style factory for the active BlockBT engine."""

    _instance: BaseStrategyEngine | None = None

    @classmethod
    def load(cls, force_reload: bool = False, force_opensource: bool = False) -> BaseStrategyEngine:
        """Return the appropriate engine, caching the result.

        Parameters
        ----------
        force_reload:
            If True, discard the cached engine and re-evaluate BYOL availability.
            Useful after the user drops in a vbtpro folder mid-session.
        force_opensource:
            If True, always return OpenSourceEngine regardless of BYOL availability.
            Used by the System Status diagnostic page to override the engine.
        """
        if force_opensource:
            # Do not cache a forced-OSS engine so the normal engine is still
            # available on the next call without force_opensource.
            from blockbt.engine.opensource_engine import OpenSourceEngine
            oss = OpenSourceEngine()
            logger.debug("EngineLoader: force_opensource=True → OpenSourceEngine")
            return oss

        if cls._instance is not None and not force_reload:
            return cls._instance

        cls._instance = cls._create_engine()
        logger.info(
            "EngineLoader: active engine → {} ({})",
            cls._instance.ENGINE_NAME,
            cls._instance.ENGINE_VERSION,
        )
        return cls._instance

    @classmethod
    def _create_engine(cls) -> BaseStrategyEngine:
        from blockbt.engine.opensource_engine import OpenSourceEngine
        from blockbt.engine.pro_engine import ProEngine

        # Attempt PRO path if the user has indicated they want it.
        if settings.PREFER_PRO_ENGINE or settings.effective_vbtpro_path():
            engine = ProEngine()
            if engine.is_available() or settings.PREFER_PRO_ENGINE:
                return engine
            # vbtpro path exists but couldn't be imported — log and fall back.
            logger.warning(
                "EngineLoader: ProEngine requested but vbtpro not importable. "
                "Falling back to OpenSourceEngine."
            )

        return OpenSourceEngine()

    @classmethod
    def info(cls) -> dict[str, str]:
        """Return info dict from the currently loaded engine."""
        return cls.load().get_engine_info()
