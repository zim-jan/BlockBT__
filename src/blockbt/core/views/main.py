"""Glowne widoki aplikacji core."""

from django.http import HttpRequest, HttpResponse
from django.shortcuts import render


def index(request: HttpRequest) -> HttpResponse:
    """Strona glowna aplikacji.

    Parameters
    ----------
    request : HttpRequest
        Obiekt zapytania HTTP.

    Returns
    -------
    HttpResponse
        Renderowany szablon strony glownej.
    """
    return render(request, "core/index.html")
