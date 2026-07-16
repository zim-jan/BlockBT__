# BlockBT -- Instrukcje dla AI

## Opis projektu

BlockBT -- aplikacja webowa Django do backtestingu strategii algorytmicznych.
Cala strona to jedna aplikacja Django (`core`), bedaca glowna funkcjonalnoscia projektu.

## Stack technologiczny

- **Python**: 3.12
- **Framework**: Django 6.0
- **Package manager**: uv
- **Testy**: pytest + pytest-django
- **Linter/Formatter**: ruff
- **Type checker**: pyright
- **Dokumentacja**: pdoc
- **Build backend**: uv_build

## Struktura projektu

```
src/blockbt/                  # glowny pakiet (src layout)
    settings.py               # konfiguracja Django
    urls.py                   # glowny routing
    wsgi.py / asgi.py
    core/                     # jedyna aplikacja Django
        apps.py
        urls.py
        views/                # pakiet -- jeden plik per logiczny obszar
            __init__.py
        models/               # pakiet -- jeden plik per model lub grupe modeli
            __init__.py       # re-eksportuje wszystkie modele
        services/             # logika biznesowa, oddzielona od widokow
            __init__.py
        forms/                # formularze Django
            __init__.py
        admin.py
        templates/core/       # szablony HTML
        static/core/          # pliki statyczne
        tests/                # testy pytest
            __init__.py
            conftest.py       # fixtures wspoldzielone
            test_models.py
            test_views.py
            test_services.py
```

### Zasady struktury

- Modele: zawsze pakiet `models/` -- jeden plik per model lub logiczna grupe. `__init__.py` re-eksportuje wszystkie modele.
- Widoki: pakiet `views/` -- jeden plik per logiczny obszar.
- Serwisy: logika biznesowa w `services/` -- nie w widokach ani modelach.
- Formularze: pakiet `forms/` gdy jest wiecej niz 2-3 formularze.
- Testy: pakiet `tests/` z `conftest.py` i plikami per warstwa (models, views, services).
- Kazdy katalog musi miec `__init__.py`.

## Komendy

```bash
# Uruchomienie serwera deweloperskiego
uv run python manage.py runserver

# Migracje
uv run python manage.py makemigrations
uv run python manage.py migrate

# Testy
uv run pytest

# Linting i formatowanie
uv run ruff check .
uv run ruff format .

# Type checking
uv run pyright

# Instalacja zależności
uv add <pakiet>
uv add --dev <pakiet>

# Generowanie dokumentacji
uv run pdoc blockbt
```

## Konwencje kodu

### Python / Django

- Typowanie: używaj type hints wszędzie gdzie to sensowne.
- Formatowanie: ruff format (domyślne ustawienia).
- Linting: ruff check — kod musi przechodzić bez błędów.
- Type checking: pyright w trybie basic — kod musi przechodzić.
- Importy: sortowane przez ruff (isort-kompatybilne).
- Nazewnictwo:
  - klasy: `PascalCase`
  - funkcje/zmienne: `snake_case`
  - stałe: `UPPER_SNAKE_CASE`
- Nigdy nie uzywaj emotek w kodzie, komentarzach, commitach ani dokumentacji.

### Docstringi

- Styl: **NumPy**.
- Dodawaj docstringi tylko dla publicznego API (funkcje, metody, moduły).
- **NIE** dodawaj docstringow dla klas ani metod `__init__`.
- Przyklad:

```python
def calculate_profit(trades: list[Trade], fees: float = 0.001) -> Decimal:
    """Oblicz zysk netto z listy transakcji.

    Parameters
    ----------
    trades : list[Trade]
        Lista zamknietych transakcji.
    fees : float, optional
        Prowizja jako ulamek (domyslnie 0.001).

    Returns
    -------
    Decimal
        Zysk netto po odliczeniu prowizji.

    Raises
    ------
    ValueError
        Jesli lista transakcji jest pusta.
    """
```

### Django-specific

- Jedna aplikacja: `core`. Nie tworzmy dodatkowych aplikacji bez uzgodnienia.
- Modele: pakiet `models/` -- kazdy model w osobnym pliku. `__init__.py` re-eksportuje modele.
- Widoki: preferuj class-based views (CBV) dla CRUD, function-based views (FBV) dla prostej logiki.
- URL-e: `core/urls.py` inkludowany w glownym `urls.py`.
- Szablony: `templates/core/`.
- Statyczne pliki: `static/core/`.
- Migracje: zawsze commituj migracje. Nie edytuj recznie, chyba ze konieczne.

### Testy

- Framework: **pytest** + **pytest-django**.
- Testy w `core/tests/` -- nie uzywaj `django.test.TestCase` (chyba ze potrzebna jest transakcja).
- Fixtures w `conftest.py`.
- Nazewnictwo: `test_<co_testujemy>.py`, funkcje `test_<scenariusz>()`.
- Uruchamianie: `uv run pytest`.

### Git

- Commity: konwencja Conventional Commits (`feat:`, `fix:`, `refactor:`, `docs:`, `test:`, `chore:`).
- Język commitów: Polski.
- Branch: `main` jako branch produkcyjny.

## Zasady pracy

- **Zawsze uzywaj `uv`** do uruchamiania komend Pythona (`uv run ...`), instalacji zaleznosci (`uv add ...`) i zarzadzania srodowiskiem. Nigdy nie uzywaj `pip`, `python` ani `pytest` bezposrednio.
- Przed zmiana kodu -- przeczytaj istniejacy plik.
- Nie dodawaj funkcjonalnosci, ktore nie byly zamowione.
- Nie refaktoryzuj kodu, ktory nie jest czescia zadania.
- Uruchom `uv run ruff check` i `uv run ruff format` po zmianach w kodzie.
- Uruchom `uv run pyright` po zmianach typow lub sygnatur.

## Aktualizacja CLAUDE.md

**WAZNE**: Jesli w trakcie pracy uzytkownik doda, zmieni lub usunie jakies zalozenia projektowe, decyzje architektoniczne, konwencje lub reguly -- **natychmiast zaktualizuj odpowiedni fragment tego pliku (CLAUDE.md)**.

Przykłady sytuacji wymagajacych aktualizacji:
- Dodanie nowej biblioteki do stacku technologicznego
- Zmiana konwencji nazewnictwa lub struktury plikow
- Nowe zasady dotyczace testow, dokumentacji lub code review
- Decyzje o architekturze (np. dodanie nowej aplikacji Django)
- Zmiana narzedzi developmentu (linter, formatter, type checker)
- Nowe workflow lub procedury

Po kazdej takiej zmianie:
1. Zaktualizuj odpowiednia sekcje w CLAUDE.md
2. Upewnij sie, ze zmiany sa spójne z reszta dokumentu
3. Poinformuj uzytkownika o dokonanej aktualizacji