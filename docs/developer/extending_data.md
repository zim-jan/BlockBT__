# Przewodnik: Dodawanie Nowego Źródła Danych (API)

BlockBT jest zaprojektowany tak, aby dodanie nowego brokera lub giełdy (np. Binance, Interactive Brokers, IEX) wymagało edycji tylko jednego pliku.

## 🏗️ Proces Krok po Kroku

### 1. Stwórz nowy plik konektora
W folderze `src/blockbt/connectors/` stwórz plik, np. `binance.py`.

### 2. Zaimplementuj klasę dziedziczącą po `BaseDataConnector`
Musisz nadpisać chronioną metodę `_download`. Klasa bazowa zajmie się za Ciebie cache'owaniem w plikach Parquet i czyszczeniem dat.

```python
from blockbt.connectors.base import BaseDataConnector
import pandas as pd
# import binance_library

class BinanceConnector(BaseDataConnector):
    CONNECTOR_KEY = "binance"
    REQUIRES_AUTH = True  # Jeśli wymaga API Key

    def _download(self, symbol: str, start: str, end: str, timeframe: str) -> pd.DataFrame:
        # 1. Tu wywołaj API zewnętrznego serwisu
        # 2. Musisz zwrócić DataFrame z kolumnami: open, high, low, close, volume
        # 3. Indeks musi być typu DatetimeIndex
        
        # Przykład (pseudokod):
        # raw_data = binance.get_historical_klines(symbol, timeframe, start, end)
        # df = pd.DataFrame(raw_data)
        return df
```

### 3. Zarejestruj konektor w `Settings`
Jeśli Twój konektor wymaga nowych kluczy API, dodaj je do `src/blockbt/config.py` w klasie `Settings`.

### 4. Dodaj opcję do interfejsu (Opcjonalnie)
W pliku `pages/4_Market_Data.py` lub `pages/1_Wizard.py` dodaj nazwę swojego konektora do listy rozwijanej `st.selectbox`.

## 💡 Dobre Praktyki

- **Normalizacja Symboli**: Upewnij się, że Twój konektor radzi sobie z formatem symboli (np. zamiana `BTC/USD` na `BTCUSDT` dla Binance).
- **Rate Limiting**: Staraj się nie uderzać w API zbyt często — metoda `fetch()` w klasie bazowej domyślnie używa cache, co chroni Cię przed banem IP.
- **Timeframes**: Zmapuj standardowe interwały BlockBT (`1m`, `1h`, `1d`) na format wymagany przez API dostawcy.

---
### Zobacz też:
- [class_reference.md](class_reference.md) — sekcja Connector Layer.
- [YahooFinanceConnector](file:///home/przydan/my_project/src/blockbt/connectors/yahoo_finance.py) — kompletny przykład działającej implementacji.
