"""Testy widokow aplikacji core."""

from http import HTTPStatus

from django.test import Client
from django.urls import reverse


def test_index_view_returns_200() -> None:
    """Test sprawdzajacy czy strona glowna zwraca kod 200."""
    client = Client()
    response = client.get(reverse("core:index"))
    assert response.status_code == HTTPStatus.OK


def test_index_view_contains_title() -> None:
    """Test sprawdzajacy czy strona glowna zawiera tytul BlockBT."""
    client = Client()
    response = client.get(reverse("core:index"))
    assert b"BlockBT" in response.content
