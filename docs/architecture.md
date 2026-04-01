# Architektura Systemu

System BlockBT to aplikacja dwuwarstwowa (Frontend React + Backend FastAPI), która komunikuje się w lokalnym środowisku bez autoryzacji. Odrzucono starsze koncepcje takie jak Streamlit na rzecz wydajnego i elastycznego stosu.

## Kluczowe założenia (Guidelines)

### Odrzucenie starszych wzorców
1.  **Ze Streamlit na React:** Cały interfejs to SPA (Single Page Application) na bazie Reacta z wykorzystaniem Vite. Plik `App.tsx` pełni tylko rolę "orchestratora" dostarczającego globalne konteksty.
2.  **Odseparowany rozwój danych (Zasada Air-gapped):** Nikt w BlockBT nie wysyła danych do chmury. Przechowywanie wyników, optymalizacji oraz ticków to lokalne operacje I/O w kontenerze.
3.  **Metoda "Wipe and Recreate" (Zamiast Alembic):** W MVP aplikacja z założenia kasuje plik `local_data/blockbt.db` i wywołuje `Base.metadata.create_all(bind=engine)` z Pydantic, co przyspiesza iteracje kodu w fazie rozwoju i uniknięcia konfliktów stanu.

## Diagram Modułów
System składa się z trzech dużych warstw.

### 1. Warstwa Prezentacji (React / Vite)
*   **Feature-Driven Architecture:** Katalog `src/features/` grupuje kod po obszarach domenowych (np. Backtesting, Konfiguracja).
*   **Katalogi "Infrastructure":** `hooks`, `services`, `store` umieszczane są w korzeniu `src/`.
*   **Zarządzanie stanem i UI:** Frontend dba o cykl życia zapytań API oraz lokalny stan komponentów, nie narzucając żadnych obciążeń logiką domenową – tę wykonuje Backend.

### 2. Warstwa API (FastAPI)
*   Dostarcza w 100% zdefiniowane endpointy (REST) w zgodzie ze specyfikacją OpenAPI.
*   Każdy endpoint (np. `/api/backtest`) jest silnie typowany, posługując się lekkimi modelami Pydantic w operacjach wejścia (request) i wyjścia (response), by zapewnić stabilną walidację w TypeScript na froncie.
*   Bezpieczeństwo operacji z LLM zabezpiecza się na poziomie bazy danych: błędy z zapytania sieciowego do usług LLM wywołują Rollback transakcji (np. `session.rollback()`), aby usunąć powiązane "dangling records".
*   Wszystkie ustawienia globalne (środowiska deweloperskie, LLM itp.) zarządzane są przy pomocy `pydantic-settings` (w kodzie np. w `app.core.config`), zapewniając obsługę plików `.env` z zachowaniem bezpiecznych, lokalnych wartości domyślnych (`http://localhost:11434` dla Ollama).

### 3. Warstwa Obliczeniowa (Silniki i Dane)
*   Wykonanie backtestów realizowane jest za pośrednictwem wzorca "Dual-Engine Ready", który dostarcza zdefiniowane interfejsy dla różnych "silników" opartych na pakiecie *vectorbt*.
*   Skrypty giełdowe i zasoby systemowe ładują pliki **Parquet**, które zapisują się w katalogu `./local_data` (odpowiednio mapowane przez woluminy w konfiguracji Docker).
