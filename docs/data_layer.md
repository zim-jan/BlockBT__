# Data Layer: OHLCV Connectors

Moduł pozyskiwania i cache'owania historycznych danych giełdowych / krypto dla środowiska BlockBT. Ten moduł obsługuje pobieranie danych i zapis lokalny (cache) w formacie `.parquet`, co drastycznie skraca czas ładowania danych w procesie backtestingu.

## Klasa Bazowa `BaseDataConnector`

Główny interfejs zdefiniowany w `src/blockbt/data/base.py` określa, że każdy nowy konektor danych w BlockBT musi dziedziczyć z `BaseDataConnector` i implementować metodę `fetch_data`.

### Przykład Interfejsu
```python
import abc
import pandas as pd

class BaseDataConnector(abc.ABC):
    @abc.abstractmethod
    def fetch_data(self, symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
        pass
```

## Yahoo Finance Connector (`YFDataConnector`)

Klasa odpowiedzialna za pobieranie danych za pomocą darmowego API Yahoo Finance (przy użyciu biblioteki `yfinance`), zlokalizowana w `src/blockbt/data/yahoo.py`.

### Główne Cechy:
- **Inteligentne Cache'owanie w formacie Parquet:** Dane są zapisywane lokalnie (np. w `data/cache/AAPL.parquet`).
- **Ograniczanie zbędnych zapytań:** Jeśli żądany zakres jest w pełni dostępny w lokalnym pliku `.parquet`, biblioteka go odczyta bez nawiązywania połączenia z internetem.
- **Automatyczne Merge'owanie:** W przypadku częściowego braku danych w cache'u (np. nowsze dni), konektor automatycznie dogra brakujące dane, zaktualizuje lokalny cache, uniemożliwiając duplikację indeksów i posortuje daty.
- **Standaryzacja pod VectorBT:** Otrzymany DataFrame posiada odpowiednio sformatowany index `DatetimeIndex` (bez offsetów czasowych) i sformatowane nagłówki kolumn (`Open`, `High`, `Low`, `Close`, `Volume`), które są natywnie kompatybilne z biblioteką `vectorbt`.

### Konfiguracja Katalogu Cache
Ścieżka dla lokalnego Cache może być przekazana w konstruktorze lub zdefiniowana w zmiennej środowiskowej `BLOCKBT_DATA_CACHE_DIR`. Jeśli żadna wartość nie jest podana, system ustawi ją na `data/cache`. Ta ścieżka powinna być odpowiednio zmapowana jako volume w środowisku Docker.

### Przykład Użycia

```python
import pandas as pd
from blockbt.data.yahoo import YFDataConnector

# Inicjalizacja konektora
connector = YFDataConnector()

# Alternatywnie: customowa ścieżka dla cache'u
# connector = YFDataConnector(cache_dir="/custom/cache/path")

# Pierwsze pobranie (dane zostaną zassane z Yahoo Finance i zapisane do AAPL.parquet)
df = connector.fetch_data("AAPL", "2023-01-01", "2023-12-31")
print(df.head())

# Kolejne pobranie z tego samego lub węższego zakresu dat zadziała natychmiastowo z dysku
df_cached = connector.fetch_data("AAPL", "2023-06-01", "2023-06-30")
```