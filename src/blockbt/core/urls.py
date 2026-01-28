"""Routing URL dla aplikacji core."""

from django.urls import path

from blockbt.core.views import index

app_name = "core"

urlpatterns = [
    path("", index, name="index"),
]
