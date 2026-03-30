# Class Reference — Core Hierarchies

Ten dokument opisuje kluczowe klasy Pythona, które sterują logiką BlockBT. Zrozumienie ich zależności jest niezbędne do poprawnego rozszerzania systemu.

## 🚀 Engine Layer (`src/blockbt/engine/`)

Silnik jest sercem obliczeniowym. Wszystkie silniki dziedziczą po wspólnej klasie bazowej.

### `StrategyEngine` (Abstract Base Class)
- **Lokalizacja**: `base.py`
- **Główne Metody**:
  - `run_backtest(data, params)`: Wejście dla symulacji. Zwraca słownik (`dict`) z wynikami.
  - `get_engine_info()`: Zwraca metadane (nazwa, wersja).
  - `is_available()`: Sprawdza czy wymagane biblioteki (np. vbt pro poprzez BYOL) są zainstalowane.

### `OpenSourceEngine`
- **Lokalizacja**: `opensource_engine.py`
- **Rola**: Wykorzystuje darmową wersję `vectorbt` oraz wbudowane wskaźniki natywne dla vectorbt.
- **Cechy**: Zawiera parser dla standardowych wskaźników generujących sygnały wejścia/wyjścia z możliwością podania w parametrach płaskiej siatki.

---

## 📡 Connector Layer (`src/blockbt/connectors/`)

Konektory odpowiadają za dostarczanie surowych danych OHLCV.

### `BaseDataConnector` (Abstract Base Class)
- **Metoda `fetch(...)`**: Publiczny punkt styku. Automatycznie obsługuje:
  - Sprawdzanie lokalnego cache w formacie Parquet.
  - Normalizację nazw kolumn (lowercasing).
  - Walidację dat.
- **Metoda `_download(...)`**: Musi zostać nadpisana w konkretnej implementacji (np. `YahooFinanceConnector`).

---

## 💾 Database Layer (`src/blockbt/db/`)

Modele SQLAlchemy definiujące strukturę SQLite.

### `Strategy`
- Przechowuje "przepis" na strategię.
- Pole `parameters`: JSON blob zawierający wszystkie parametry (interwał, symbol, wskaźniki).

### `BacktestJob`
- Wynik konkretnego przebiegu silnika. 
- Przechowuje relację do `Strategy`, pełne metryki w JSON oraz status wykonania.

---

## 🧩 Inne Kluczowe Klasy

- **`OllamaClient`** (`src/blockbt/mcp/llm_client.py`): Klient do komunikacji z lokalnym modelem AI (Llama/Qwen) przez Ollama.
- **`ReportBuilder`** (`src/blockbt/mcp/report_builder.py`): Przekształca surowe metryki Quant w czytelny dla LLM kontekst (Prompt Engineering).
