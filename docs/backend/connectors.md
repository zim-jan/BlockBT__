# Backend - Data Connectors

Warstwa Data Connectors odpowiada za pobieranie, normalizację i cache'owanie danych rynkowych. System został zaprojektowany w oparciu o wzorzec wtyczek (plugin architecture), co ułatwia dodawanie nowych źródeł danych.

## Architektura: Data Connector Pattern

Głównym założeniem jest odizolowanie logiki specyficznej dla dostawcy (np. API sieciowe, autoryzacja) od logiki biznesowej aplikacji. Każdy konektor dziedziczy po klasie bazowej, która dostarcza gotowe mechanizmy przetwarzania danych.

### BaseDataConnector
Klasa `backend/app/services/connectors/base.py` definiuje kontrakt dla wszystkich dostawców:

- **`fetch()`**: Publiczna metoda będąca punktem wejścia. Implementuje logikę "Cache-Aside":
  1. Sprawdza, czy dane są w lokalnym cache'u Parquet.
  2. Jeśli są i są aktualne (TTL) -> zwraca dane z dysku.
  3. Jeśli brak danych lub są przestarzałe -> wywołuje `_download()`.
  4. Normalizuje pobrane dane i zapisuje do cache'u.
- **`_download()`**: Metoda abstrakcyjna, którą musi zaimplementować każdy konektor. Odpowiada za fizyczne pobranie danych z serwerów dostawcy.
- **`_normalise()`**: Standardyzuje dane wejściowe:
  - Nazwy kolumn są zamieniane na małe litery.
  - Wymagany standard OHLCV (`open`, `high`, `low`, `close`, `volume`).
  - Indeks jest konwertowany na `DatetimeIndex` (tz-naive).
  - Typ danych jest wymuszany jako `float`.

---

## System Cache (Parquet)

BlockBT wykorzystuje format **Apache Parquet** do przechowywania pobranych danych rynkowych. Wybór tego formatu zapewnia wysoką kompresję oraz szybki odczyt kolumnowy przez bibliotekę `pandas`.

- **Lokalizacja**: `/backend/data/parquet/` (lub ścieżka zdefiniowana w `PARQUET_DIR`).
- **Struktura**: Dane są partycjonowane według symbolu: `.../parquet/{SYMBOL}/{START}_{END}_{TIMEFRAME}.parquet`.
- **TTL (Time To Live)**: Czas ważności cache'u jest konfigurowalny poprzez `PARQUET_CACHE_TTL_HOURS`. Po tym czasie system automatycznie pobierze świeże dane.

---

## Connector Registry

Moduł `backend/app/services/connectors/registry.py` pełni rolę fabryki konektorów. Umożliwia dynamiczne pobieranie instancji dostawcy na podstawie klucza (np. "yahoo", "alpaca").

---

## Implementacje Dostawców

### Yahoo Finance (Domyślny)
- **Klucz**: `yahoo`.
- **Biblioteka**: `yfinance`.
- **Charakterystyka**: Nie wymaga klucza API. Idealny do testowania i pobierania danych historycznych dla akcji i kryptowalut.
- **Mapowanie**: Automatycznie tłumaczy standardowe interwały BlockBT na kody akceptowane przez Yahoo (np. `1h` -> `60m`, `1w` -> `1wk`).

### Alpaca
- **Klucz**: `alpaca`.
- **Charakterystyka**: Wymaga autoryzacji (`ALPACA_API_KEY`, `ALPACA_SECRET_KEY`). Zapewnia dostęp do danych w czasie rzeczywistym i precyzyjniejszych danych intraday dla giełdy US.
