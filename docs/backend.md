# Backend API (FastAPI)

Architektura serwera **BlockBT** opiera się na **FastAPI** w wersji dla Pythona 3.12+ (zarządzanego poprzez `uv`). Kod źródłowy zlokalizowany jest w całości w katalogu `backend/app/`, a testy automatyczne w `backend/tests/`. Całość działa wyłącznie w środowisku lokalnym, co narzuca specyficzne rygory bezpieczeństwa i wydajności.

## Główne Zasady Budowy API

1.  **Strict Pydantic Validation (Ścisła Walidacja)**: Wszystkie endpointy REST API muszą posiadać jasno zdefiniowane, wejściowe oraz wyjściowe modele Pydantic w celach weryfikacji danych i automatycznej generacji poprawnej specyfikacji OpenAPI. Nie zwracamy z API surowych słowników, lecz sformatowane, przewidywalne schematy.
2.  **Lekkie Modele ORM w Trasach API**: Zgodnie z wytycznymi Faz 2+, endpointy API powinny importować bezpośrednio lekkie modele SQLAlchemy (z `backend/app/models/orm.py`) i korzystać z wstrzykiwania zależności dla sesji bazy danych (z `backend/app/db/session.py`). Stare, rozbudowane moduły bazodanowe są uznane za przestarzałe i nie powinny być stosowane dla nowych tras.
3.  **Transakcyjność Zewnętrznych Wywołań (LLM)**: Każda interakcja z modelem LLM musi odbywać się w bloku transakcyjnym bazy danych. W przypadku niepowodzenia (np. błąd połączenia z lokalnym Ollama, błąd API zewnętrznego dostawcy), sesja musi bezwzględnie wywołać `session.rollback()`. Taka konstrukcja zapobiega powstawaniu w systemie "dangling records" (np. pytań użytkownika bez odpowiadającej im wygenerowanej analizy/kodu), utrzymując stan aplikacji w całkowitej spójności.
4.  **Konfiguracja Zależna od Środowiska (Pydantic Settings)**: Centralne zarządzanie ustawieniami odbywa się w pliku `backend/app/core/config.py` z wykorzystaniem klasy `BaseSettings`. Mechanizm ten dostarcza bezpieczne wartości domyślne dla środowiska deweloperskiego (np. endpoint Ollama to standardowo `http://localhost:11434`), z możliwością nadpisania ich zmiennymi środowiskowymi w środowisku produkcyjnym/wdrożeniowym.
5.  **Brak Zewnętrznych Reverse Proxy (Nginx/Traefik)**: Z racji na charakter "air-gapped", projekt nie przewiduje i nie dopuszcza wdrażania zaawansowanej infrastruktury obwodowej. Kontenery Docker dla backendu udostępniają porty bezpośrednio na `127.0.0.1` (np. `127.0.0.1:8000:8000`).

## Architektura Połączeń Danych (Connectors)

Pobieranie historycznych danych rynkowych obsługiwane jest przez konektory dziedziczące z `app.services.connectors.base.BaseDataConnector`.

Wzorzec ten gwarantuje, że podklasa dostawcy (np. konektor dla Yahoo Finance lub Alpaca) musi zaimplementować jedynie metodę pobierania sieciowego (np. `_download()`). Pozostała logika, w tym buforowanie, normalizacja schematu danych, zapis/odczyt w formacie Parquet oraz zapytań (metoda `fetch()`), jest współdzielona i zarządzana przez klasę bazową, redukując ryzyko błędów duplikacji kodu.

## Wzorzec Bazy Danych "Wipe and Recreate"

Na obecnym etapie MVP, z uwagi na potrzebę utrzymania maksymalnej prędkości rozwoju, w projekcie **nie stosuje się narzędzi migracyjnych takich jak Alembic**. Ewolucja schematu bazy danych SQLite opiera się wyłącznie na wzorcu "kasowania i odtworzenia" (Wipe and Recreate):

*   Przy zmianie struktury tabel usuwany jest plik z danymi (`local_data/blockbt.db`).
*   Inicjalizacja aplikacji korzysta z metody SQLAlchemy `Base.metadata.create_all()` do stworzenia świeżego schematu.

Modyfikacja konfiguracji i kluczy tajnych: Zabrania się modyfikacji pliku konfiguracyjnego w celu tworzenia domyślnych wartości dla krytycznych zmiennych środowiskowych, np. `SECRET_KEY`. W przypadku braku tego klucza w środowisku, aplikacja musi zgłosić błąd walidacji, aby wymusić świadome dostarczenie go przez użytkownika w pliku `.env`.
