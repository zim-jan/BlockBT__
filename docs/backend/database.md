# Backend - Core & Database

Ten dokument opisuje warstwę dostępu do danych oraz modele ORM wykorzystywane w systemie BlockBT.

## Zarządzanie Sesją i Konfiguracja Bazy Danych

Głównym modułem zarządzającym połączeniem z bazą danych jest `backend/app/db/session.py`.

### Charakterystyka połączenia
- **Silnik**: SQLite.
- **Tryb WAL (Write-Ahead Logging)**: Włączony automatycznie przy każdym połączeniu (`PRAGMA journal_mode=WAL`), co zapewnia lepszą wydajność przy jednoczesnych zapisach i odczytach.
- **Klucze Obce**: Włączone (`PRAGMA foreign_keys=ON`).
- **Lokalizacja bazy**:
  - Priorytet 1: Zmienna środowiskowa `BLOCKBT_DB_PATH`.
  - Priorytet 2: Zmienna środowiskowa `BLOCKBT_DB_URL`.
  - Fallback: `backend/data/db/blockbt.db`.

### Kluczowe Funkcje
- `get_session()`: Menedżer kontekstu (context manager) zapewniający bezpieczną obsługę sesji SQLAlchemy, automatyczny commit przy sukcesie i rollback przy błędzie.
- `init_db()`: Inicjalizuje schemat bazy danych (tworzy tabele).

---

## Modele ORM

Wszystkie modele zdefiniowane są w `backend/app/models/orm.py` przy użyciu SQLAlchemy 2.0 (`Mapped`/`mapped_column`).

### Strategy
Model reprezentujący konfigurację strategii handlowej zdefiniowaną przez użytkownika.
- `id`: Klucz główny.
- `name`: Nazwa strategii.
- `parameters`: Słownik JSON przechowujący wszystkie parametry wejściowe (symbol, interwał, wskaźniki). Zapewnia to elastyczność bez konieczności zmiany schematu bazy danych.
- `code_content`: Treść kodu skryptu strategii.

### BacktestJob (Simulation Result)
Model reprezentujący pojedyncze wykonanie backtestu. W logice biznesowej często określany jako **Simulation Result**.
- **Lifecycle**: Statusy `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`.
- **Parametry**: `parameters_snapshot` (JSON) – kopia parametrów strategii w momencie uruchomienia zadania.
- **Wyniki (Metrics)**:
  - `metrics`: Pełny słownik JSON z wynikami silnika (np. `win_rate_pct`, `equity_curve_json`).
  - **Pola Skalarne**: Główne wskaźniki (Sharpe, MaxDD, Total Return) są wyciągnięte do osobnych kolumn `Float` dla szybkiego filtrowania i sortowania.
- `ai_analysis_report`: Tekstowy raport wygenerowany przez LLM.

### OptimizationJob
Zadanie optymalizacji parametrów (np. przez Optuna).
- `bounds_definition`: Zakresy parametrów do przeszukania (JSON).
- `best_parameters`: Najlepsza znaleziona kombinacja (JSON).
- `trials_data`: Pełna historia prób (JSON).

### ChatMessage
Historia rozmowy z asystentem AI dotycząca konkretnego wyniku backtestu.
- `role`: `user` lub `assistant`.
- `content`: Treść wiadomości.
- `job_id`: Powiązanie z `BacktestJob`.

### SystemPrompt
Zarządzanie promptami systemowymi dla modułu analizy AI.
- `content`: Treść promptu.
- `is_default`: Flaga określająca domyślny prompt dla raportów.

### AppSetting
Magazyn klucz-wartość dla globalnych ustawień aplikacji.
- Przykładowe klucze: `data_connector`, `vbtpro_path`, `ollama_model`.
