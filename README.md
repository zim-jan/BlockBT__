# BlockBT (Local Algorithmic Backtesting)

Projekt **BlockBT** to profesjonalne, w pełni lokalne środowisko do przeprowadzania backtestingu strategii algorytmicznych. Składa się z nowoczesnego interfejsu **React** (Vite) oraz szybkiego i asynchronicznego serwera **FastAPI**.

System jest tworzony zgodnie z zasadą "Air-Gapped": wszystkie Twoje dane giełdowe, strategie i integracje z LLM działają ściśle lokalnie lub w zamkniętym kontenerze Docker. Projekt nie posiada autoryzacji (zaprojektowany dla jednego użytkownika lokalnego).

## Stos Technologiczny

*   **Frontend**: React 18, TypeScript, Vite, Tailwind CSS, **React Flow 12 (@xyflow/react)**.
*   **Backend**: Python 3.14+, FastAPI, Pydantic, SQLAlchemy. Zarządzanie zależnościami przy użyciu `uv`.
*   **Silnik (Engine)**: Dwusilnikowa (Dual-Engine Ready) struktura z domyślnym silnikiem opartym na wektoryzowanym `vectorbt`.
*   **Baza i Dane**: SQLite i lokalne pliki Parquet w katalogu `local_data/`.
*   **Dokumentacja**: MkDocs (dostępna w `docs/` i budowana przez mkdocs-material).

## Narzędzia Makefile

Projekt zawiera `Makefile` ułatwiający codzienne zadania:

*   `make dev` - Uruchamia backend i frontend (wymaga dwóch terminali).
*   `make api` - Uruchamia tylko backend FastAPI.
*   `make build-api` - Buduje obraz Docker dla backendu.
*   `make rebuild-api` - Przebudowuje i restartuje kontener backendu.
*   `make test` - Uruchamia pełną suitę testową pytest.
*   `make clean` - Czyści cache i pliki tymczasowe.

## Szybki Start (Docker Compose)

Najprostsza metoda na uruchomienie pełnego środowiska z bazą danych, frontendem i backendem. Aplikacja mapuje wszystkie porty do bezpiecznego środowiska lokalnego (`127.0.0.1`).

```bash
docker-compose up --build
```
*   **Frontend React:** `http://127.0.0.1:3000`
*   **Backend API:** `http://127.0.0.1:8000/docs`

## Rozwój Lokalny (Development - Bez Kontenerów)

Do szybkiej pracy i uruchamiania testów zalecamy użycie `uv` na swoim hoście.

### Krok 1: Inicjalizacja Backendu
```bash
uv sync --extra dev
uv run uvicorn backend.app.main:app --reload
```
Aplikacja automatycznie utworzy pustą bazę danych SQLite przy uruchomieniu (Lifespan Context Manager).

### Krok 2: Uruchomienie Frontendu React
W oddzielnym terminalu:
```bash
cd frontend
npm install
npm run dev --host 0.0.0.0
```

### Krok 3: Budowanie Dokumentacji
Aby wygenerować i przeczytać profesjonalną dokumentację MkDocs w języku polskim:
```bash
uv run mkdocs serve
```

## Architektura DAG (Phase 9)

BlockBT używa skierowanego grafu acyklicznego (DAG) do opisu strategii backtestingowych. Frontend Visual Builder eksportuje graf jako JSON i wysyła go do backendu.

### Endpoint: `POST /api/backtest/dag`

Przyjmuje strukturę `DAGBacktestRequest`:
```json
{
  "strategy_id": 1,
  "dag": {
    "nodes": [...],
    "edges": [...],
    "meta_nodes": [...]
  }
}
```

### Kategorie Węzłów

| Kategoria | Rola | Dozwolone połączenia wychodzące |
|-----------|------|-------------------------------|
| **DataIngestion** | Źródło danych (vbt.YFData) | Indicators, Execution |
| **Indicators** | Transformacje (SMA, MACD) | LogicOperators, Execution |
| **LogicOperators** | Maski logiczne (entries/exits) oraz **TimeShift** (prewencja Look-ahead bias) | Execution |
| **Execution** | Portfel (vbt.Portfolio.from_signals) | — |
| **Meta** | Optymalizatory (parametry) | — (via target_nodes) |

### Walidacja

Backend `GraphParser` automatycznie sprawdza:
- Brak cykli (algorytm Kahna)
- Zgodność typów portów (COMPATIBILITY_MATRIX)
- Dokładnie jeden węzeł Execution
- Brak osieroconych węzłów (wszystkie ścieżki prowadzą do Execution)

## Wytyczne Deweloperskie (Skrót)
- Piszemy komentarze i docstringi po polsku (API i klucze JSON pozostają w języku angielskim).
- Utrzymujemy ścisłą walidację schematów Pydantic dla API FastAPI.
- Plik `.env` i konfiguracja `pydantic-settings` mają rygorystyczne wartości bezpieczne (np. zapobieganie wysyłaniu nieautoryzowanych zapytań do serwerów chmurowych).
- Ograniczenia `import sort` lintera dbają o kolejność, jeśli dodajesz import, dopisz go na końcu, `uv run ruff check --fix` naprawi to za Ciebie.
