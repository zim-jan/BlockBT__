# Analityka i tearsheety (Faza 13)

Faza 13 wprowadza warstwę analityczną BlockBT: generowanie **tearsheetów** — raportów
HTML podsumowujących wyniki backtestu na podstawie metryk portfela.

## Cel i założenia

- **Air-gapped:** raport to samodzielny dokument HTML bez odwołań do zasobów
  zewnętrznych (brak CDN, czcionek online, zewnętrznych obrazów). Zgodne z modelem
  Self-Hosted BlockBT.
- **Źródło danych:** metryki z `pf.stats()` (portfel vectorbt) lub — dla endpointu —
  metryki zapisane w rekordzie `BacktestJob`.

## `QSAdapterService`

Plik: `backend/app/services/engine/qsadapter.py`.

### `generate_tearsheet(pf) -> str`

Metoda statyczna. Przyjmuje obiekt udostępniający `stats()` (zwracające
`pandas.Series` lub `dict`), normalizuje metryki do płaskiego słownika i renderuje
kompletny dokument HTML z tabelą metryk.

- Odporność: przy błędzie `stats()` loguje ostrzeżenie (`logger.warning`) i zwraca
  HTML z komunikatem o braku metryk zamiast rzucać wyjątek.
- Normalizacja: `pandas.Series` → `dict`; wartości `float` formatowane z 4 miejscami
  po przecinku; wszystkie wartości escapowane (`html.escape`) — brak ryzyka XSS.

!!! note "Dlaczego nie `qs.reports.html()`"
    Świadomie **nie** korzystamy z `quantstats.reports.html()`, ponieważ ta funkcja
    zwraca `None` (pisze do pliku), wymaga pełnej serii zwrotów oraz backendu
    graficznego (display). Budujemy HTML samodzielnie z `pf.stats()` — patrz
    [ADR-0004](../adr/0004-qsadapter-analytics-tearsheets.md).

### `generate_full_tearsheet(returns, title) -> str` (opcjonalne)

Rozszerzenie renderujące pełny raport QuantStats z wykresami. Ustawia backend
`matplotlib` na `Agg` **przed** importem warstwy plottingu (praca headless).
Przy dowolnym błędzie degraduje gracefully do prostego tearsheetu z metryk
(`qs.reports.metrics`). Nie jest częścią MVP fazy.

## Endpoint REST

```
GET /api/results/{job_id}/tearsheet
```

Zwraca `ApiResponse[TearsheetResponse]`.

- **404** — brak joba o danym `job_id`.
- **400** — job istnieje, ale `status != COMPLETED`.
- **200** — tearsheet wygenerowany.

`BacktestJob` nie przechowuje żywego obiektu vbt `Portfolio`, dlatego endpoint buduje
lekki adapter udostępniający `stats()` z zapisanych metryk joba (kolumny nagłówkowe:
`Total Return [%]`, `Sharpe Ratio`, `Max Drawdown [%]`, `Total Trades`, `Final Value`
oraz skalary ze słownika `metrics`).

### Schemat `TearsheetResponse`

Plik: `backend/app/schemas/results.py`.

| Pole | Typ | Opis |
|---|---|---|
| `job_id` | `int` | ID backtestu |
| `html` | `str` | Kompletny dokument HTML tearsheetu |
| `format` | `Literal["html"]` | Format (domyślnie `"html"`) |
| `generated_at` | `datetime` | Znacznik czasu generacji (UTC) |

## Testy

- `backend/tests/test_engine/test_qsadapter.py` — kontrakt `generate_tearsheet`
  (dict, Series, pusty/kruchy portfel).
- `backend/tests/test_api/test_tearsheet.py` — endpoint (200 / 404 / 400).

## Analiza alokacji kapitału (ADR-0009)

Każdy backtest DAG dokłada do wyniku blok `allocation` — strukturę łącznego
kapitału w czasie, liczoną z akcesorów vbt (`value`, `asset_value`, `cash`)
w momencie egzekucji (portfel nie jest persystowany):

```json
{
  "timeline": {
    "dates": ["2024-01-01", "..."],
    "weights": {"AAPL": [0.0, 0.6], "MSFT": [0.0, 0.2], "cash": [1.0, 0.2]}
  },
  "summary": {
    "AAPL": {
      "avg_exposure_pct": 42.5,
      "max_exposure_pct": 100.0,
      "time_in_market_pct": 61.3,
      "final_equity_share_pct": 55.1
    }
  }
}
```

- Wagi (`asset_value_i / Σ value` + `cash`) sumują się do 1 na każdym punkcie;
  timeline jest downsamplowany do ≤ 500 punktów (ostatni bar zawsze obecny).
- Portfel multi-symbol to niezależne kolumny (bez `cash_sharing`) — analiza
  pokazuje strukturę **sumy** portfeli, nie realną wspólną alokację (ADR-0009).
- API: pole `allocation` tylko w `GET /api/backtest/{id}` (lista jobów lekka).
- UI: sekcja „Allocation" w węźle Portfolio — stacked-area 100% + tabela
  (średnia ekspozycja, % czasu w rynku, udział w kapitale końcowym).
- Testy: `test_engine/test_allocation.py`, `test_api/test_allocation_api.py`.
