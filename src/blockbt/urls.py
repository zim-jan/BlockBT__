"""Glowny routing URL dla projektu BlockBT."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("blockbt.core.urls")),
]
