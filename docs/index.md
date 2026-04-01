# Wprowadzenie (Getting Started)

Witaj w dokumentacji technicznej **BlockBT** – lokalnego, wyizolowanego środowiska (air-gapped) do przeprowadzania backtestingu strategii algorytmicznych.

## O systemie
BlockBT to aplikacja zaprojektowana do szybkiej weryfikacji pomysłów inwestycyjnych z wykorzystaniem biblioteki w Pythonie. Jej głównym założeniem jest praca wyłącznie w środowisku lokalnym (lub w izolowanym kontenerze).

### Główne cechy
*   **Brak logowania i autoryzacji:** Aplikacja jest przeznaczona dla jednego, lokalnego użytkownika. Nie wdrażamy żadnych systemów logowania.
*   **Izolacja (Air-gapped):** Wszystkie dane historyczne zapisywane są lokalnie w formacie Parquet. Backend nie wysyła żadnych danych analitycznych ani telemetrii. Komunikacja (np. z LLM) odbywa się wyłącznie na żądanie użytkownika i jest w pełni opcjonalna, z wykorzystaniem lokalnych (Ollama) lub zewnętrznych usług (według jawnie podanego klucza API).
*   **Lokalne wykonanie:** Nie obsługujemy live tradingu, webhooków od brokerów, ani nie wspieramy infrastruktury chmurowej typu Kubernetes czy klastrów. Całość uruchamiana jest za pomocą Docker Compose.

## Stos technologiczny
*   **Frontend:** React, TypeScript, Vite. Architektura Single-Page Application z podziałem na moduły domenowe (Feature-Driven).
*   **Backend:** Python (FastAPI), Pydantic dla silnego typowania, SQLAlchemy (SQLite).
*   **Dane i wydajność:** Format Parquet do przechowywania danych historycznych giełdowych, `uv` do zarządzania pakietami w Pythonie. W fazie MVP wszystkie migracje bazy danych polegają na "skasowaniu pliku SQLite i utworzeniu na nowo", bez uciążliwych migracji (Alembic).
*   **Silnik obliczeniowy:** Oparty na open-source.

## Uruchomienie deweloperskie

Aplikacja może zostać uruchomiona w dwóch trybach:
1.  **Pełny stack z Docker Compose:**
    Wystarczy uruchomić `docker-compose up --build`. Architektura zakłada bindowanie wszystkich usług pod adresem `127.0.0.1` w celu zapewnienia maksymalnego bezpieczeństwa lokalnego.
2.  **Środowisko skryptowe lokalne (bez kontenerów):**
    Wykorzystaj narzędzie `uv` do zarządzania zależnościami:
    ```bash
    uv sync --extra dev
    uv run uvicorn backend.app.main:app --reload
    ```
    Frontend React wymaga standardowych komend `npm install` oraz `npm run dev`. Serwer deweloperski Vite proxykuje żądania `/api` do backendu na `http://127.0.0.1:8000`.
