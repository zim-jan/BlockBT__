# Zarządzanie Danymi (Parquet & SQLite)

Wymaganiem kluczowym środowiska deweloperskiego **BlockBT** (MVP) jest utrzymanie pełnej izolacji (air-gapped) bez użycia chmury i zewnętrznych procesów logujących. Architektura persystencji w pełni opiera się na prostych formatach lokalnych.

## 1. Relacyjna Baza Danych (SQLite)

Do przechowywania podstawowych metadanych aplikacji (takich jak: konfiguracje strategii, opisy modeli LLM, logi wykonywania optymalizacji, joby do przetworzenia w tle i inne obiekty użytkowe), BlockBT wykorzystuje standardowy silnik SQLite.

*   W modelu MVP do utrzymania dynamiki tworzenia aplikacji stosuje się wzorzec **"Wipe and Recreate"**, bez konieczności utrzymania plików śledzenia zmian bazy danych i narzutu środowiska produkcyjnego takich jak Alembic, które prowadziły do problemów podczas sortowania bibliotek (Ruff/isort).
*   Główny schemat bazodanowy opisany jest w modelach ORM wewnątrz katalogu `backend/app/models/orm.py`.
*   Przy restarcie i czyszczeniu stanu tworzone są od podstaw (użycie wbudowanych operacji `SQLAlchemy`, by zdefiniować struktury `Base.metadata.create_all`).
*   Brak migracji pozwala na błyskawiczne prototypowanie nowych modeli w środowisku lokalnym.
*   Stan bazy jest widoczny z poziomu Reacta przez API. Wykonane żądania obsługiwane są przez wstrzyknięcie asynchronicznych sesji w modelach `router`/`endpoint`.
*   Transakcje związane z zewnętrznymi wywołaniami do modeli LLM muszą dbać o wywołanie poleceń `session.rollback()`, minimalizując ryzyko powstania zawieszonych "osieroconych" wpisów (dangling records) przy zerwaniu komunikacji z LLMem (Ollama/OpenAI).

## 2. Pamięć Podręczna Danych Historycznych (Parquet)

Zamiast tradycyjnego modelu relacyjnego, zarządzanie długoterminowymi (setki milionów rekordów) i szerokimi szeregami czasowymi danych finansowych opiera się o format **Parquet**.

Jest on wprost niezbędny w procesie wydajnych, wektoryzowanych kalkulacji dla Pandas i silnika "vectorbt". Wszystkie dane (z takich źródeł jak integracje brokerów, Yahoo Finance, Alpaca) są znormalizowane i zrzucane na dysk przy pierwszym pobraniu w celu ich długotrwałego i natychmiastowego wykorzystania.

*   Dane przechowywane są lokalnie na ścieżce wyznaczonej w zmiennej środowiskowej z `.env` z założenia w folderze `./local_data/`.
*   Strategia zakłada wykorzystanie wzorca struktury "jednego pliku per symbol giełdowy" (na przykład plik o nazwie `AAPL.parquet`), aby zapobiec niepotrzebnej fragmentacji podczas częstych symulacji parametrów rynkowych. Unika się tym samym przeciążenia bazy danych SQLite i oszczędza na czasie odczytu do pamięci w Pandas.
*   Odczytywanie ich jest całkowicie ukryte przez klasę abstrakcyjną typu "Connector" (`BaseDataConnector`).

## Konfiguracja Kontenerów Docker (Infrastruktura Uprawnień)

Ponieważ dane Parquet i baza SQLite to bezpośrednie operacje na plikach we wspólnym woluminie deweloperskim, wymagane jest zachowanie rygoru uprawnień plików kontenerów Docker Compose, unikając błędów typowych dla używania podmontowanych folderów za pośrednictwem "użytkownika root":
*   Skonfigurowane warstwy dla bazodanowego systemu przechowującego zapisy plików wymagają rygorystycznego mapowania w pliku `docker-compose.yml` (parametry konfiguracyjne np. `user: "${UID:-1000}:${GID:-1000}"`).
