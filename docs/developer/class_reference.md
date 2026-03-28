# Class Reference — Core Hierarchies

Ten dokument opisuje kluczowe klasy Pythona, które sterują logiką BlockBT. Zrozumienie ich zależności jest niezbędne do poprawnego rozszerzania systemu.

## 🚀 Engine Layer (`src/blockbt/engine/`)

Silnik jest sercem obliczeniowym. Wszystkie silniki dziedziczą po wspólnej klasie bazowej.

### `StrategyEngine` (Abstract Base Class)
- **Lokalizacja**: `base.py`
- **Główne Metody**:
  - `run_backtest(data, params)`: Wejście dla symulacji. Zwraca `BacktestResult`.
  - `get_engine_info()`: Zwraca metadane (nazwa, wersja).
  - `is_available()`: Sprawdza czy wymagane biblioteki (np. vbt pro) są zainstalowane.

### `OpenSourceEngine`
- **Lokalizacja**: `opensource_engine.py`
- **Rola**: Wykorzystuje darmową wersję `vectorbt` oraz `pandas-ta`. 
- **Cechy**: Zawiera parser wizualnego grafu AST, który zamienia połączenia węzłów na ciągi obliczeniowe sygnałów Kup/Sprzedaj.

### `BacktestResult` (Data Class)
- Zunifikowany kontener na wyniki. Przechowuje `total_return_pct`, `sharpe_ratio`, oraz krzywą kapitału (`equity_curve`).

---

## 📡 Connector Layer (`src/blockbt/connectors/`)

Konektory odpowiadają za dostarczanie surowych danych OHLCV.

### `BaseDataConnector` (Abstract Base Class)
- **Metoda `fetch(...)`**: Publiczny punkt styku. Automatycznie obsługuje:
  - Sprawdzanie cache Parquet.
  - Normalizację nazw kolumn (lowercasing).
  - Walidację dat.
- **Metoda `_download(...)`**: Musi zostać nadpisana w konkretnej implementacji (np. `YahooFinanceConnector`, `AlpacaConnector`).

---

## 💾 Database Layer (`src/blockbt/db/`)

Modele SQLAlchemy definiujące strukturę SQLite.

### `User`
- Zarządzanie tożsamością, hashowanie bcrypt.
- Relacja: `strategy_templates`.

### `StrategyTemplate`
- Przechowuje "przepis" na strategię.
- Pole `wizard_state`: JSON blob zawierający wszystkie parametry (interwał, symbol, wskaźniki) lub graf AST.

### `SimulationResult`
- Wynik konkretnego przebiegu silnika. 
- Przechowuje unikalne ID szablonu, pełne metryki w JSON oraz zbuforowany raport AI Analyst.

---

## 🧩 Inne Kluczowe Klasy

- **`OllamaClient`** (`src/blockbt/mcp/llm_client.py`): Klient do komunikacji z lokalnym modelem AI (Llama/Qwen) przez Ollama.
- **`ReportBuilder`** (`src/blockbt/mcp/report_builder.py`): Przekształca surowe metryki Quant w czytelny dla LLM kontekst (Prompt Engineering).
- **`CookieController`** (używane w `auth.py`): Zarządzanie stanem sesji w przeglądarce.
