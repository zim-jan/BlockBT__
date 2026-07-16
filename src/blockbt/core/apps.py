"""Konfiguracja aplikacji core."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Konfiguracja aplikacji core."""

    default_auto_field = "django.db.models.BigAutoField"  # type: ignore[assignment]
    name = "blockbt.core"
