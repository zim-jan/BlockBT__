# Optymalizacja wielu tickerów naraz (Faza 10)

Faza 10 wprowadza **broadcasting** — jeden backtest DAG uruchamiany jednocześnie na wielu
instrumentach w **jednej zwektoryzowanej symulacji** `vectorbt` (kolumny = symbole), bez pętli
po symbolach w Pythonie. Wyniki są zgrupowane per ticker.

## Jak z tego korzystać (UI)

1. W węźle **Data** wpisz kilka tickerów rozdzielonych przecinkami, np. `AAPL, MSFT, NVDA`.
   Podpowiedź pod polem: *„Wiele tickerów: rozdziel przecinkami"*.
2. Zbuduj resztę grafu jak zwykle: Data → Indicators → (opcjonalnie LogicOperators) → Execution.
3. Uruchom backtest. Węzeł **Portfolio** pokaże:
   - **rozwijaną sekcję (accordion) per ticker** z kompletem metryk,
   - **jeden wykres krzywej kapitału** z osobną serią dla każdego symbolu.

Pojedynczy ticker (`AAPL`) działa dokładnie jak wcześniej — płaski widok metryk i pojedyncza
krzywa kapitału (pełna kompatybilność wsteczna).

## Jak to działa (backend)

### 1. Format danych: LONG → WIDE

Konektory zwracają dane w formacie **LONG** — wierszowy `MultiIndex [symbol, date]` z kolumną
`close`. Metoda `OpenSourceEngine._prepare_close` wykrywa ten układ i przez `unstack` zamienia go
na macierz **WIDE**: indeks = daty, kolumny = symbole.

```
LONG (wejście)                          WIDE (do wektoryzacji)
[symbol, date]  close                   date        AAPL    MSFT
(AAPL, 2020-01-01)  100.0     →         2020-01-01  100.0   200.0
(AAPL, 2020-01-02)  101.0               2020-01-02  101.0   199.0
(MSFT, 2020-01-01)  200.0               ...
```

Wyrównanie kalendarzy: `ffill().dropna(how="any")` (udokumentowane uproszczenie — wspólny zakres
dat dla wszystkich symboli). Dane rzutowane na `float64` (wymóg silnika Rust).

### 2. Broadcasting bez pętli

Cały istniejący pipeline (`MA.run`, `crossed_above`, `Portfolio.from_signals`) operuje na macierzy
WIDE i **broadcastuje po kolumnach** natywnie w `vectorbt`. Nie ma pętli po symbolach w obliczeniach
— pętle występują tylko w I/O (pobieranie per symbol) i w serializacji wyniku do JSON.

!!! warning "Normalizacja kolumn wskaźników"
    `vbt.MA.run(df, window=10)` dokleja do kolumn poziom `ma_window` (np. `(10, 'AAPL')`).
    `IndicatorService._align_to_symbols` sprowadza kolumny z powrotem do czystych symboli, aby
    `crossed_above` i portfel operowały na jednoznacznych kluczach per ticker.

### 3. Metryki per ticker

Metryki `vectorbt` przy wejściu WIDE zwracają **Series indeksowane symbolem**
(`total_return()`, `sharpe_ratio()`, `max_drawdown()`, `trades.count()`, `trades.win_rate()`,
`value()`). `_build_multi_symbol_result` przepisuje je do słownika per ticker z guardem
`np.isfinite(x) else 0.0` (stała cena → 0 transakcji → Sharpe = `inf`, Win Rate = `NaN`).

## Kontrakt wyniku

Wynik **multi-symbol**:

```json
{
  "symbol": ["AAPL", "MSFT"],
  "symbols": ["AAPL", "MSFT"],
  "is_multi_symbol": true,
  "timeframe": "1d",
  "engine_name": "opensource",
  "status": "COMPLETED",
  "metrics": {
    "AAPL": {"Total Return [%]": 8.78, "Sharpe Ratio": 2.23, "Max Drawdown [%]": -3.1,
             "Total Trades": 1, "Final Value": 10878.26, "Win Rate [%]": 100.0},
    "MSFT": { "...": "..." }
  },
  "equity_curve": {
    "AAPL": [{"date": "2020-01-01 00:00:00", "value": 10000.0}, "..."],
    "MSFT": [ "..." ]
  }
}
```

Wynik **single-symbol** pozostaje płaski (bez klucza `is_multi_symbol`; `metrics` jako płaski
słownik; `equity_curve` jako lista).

## Ograniczenia (v1)

- **Parametry × symbole** — jednoczesna wektoryzacja listy parametrów (np. `smaFast=[10, 20]`)
  i wielu tickerów rzuca `ValueError`. Wektoryzuj albo parametry, albo symbole.
- **Raporty QuantStats / `stats()`** — ścieżka multi-symbol je pomija (są zorientowane
  jednokolumnowo w otwartym `vectorbt`); metryki liczone są wprost, wektorowo.
- Raportowanie MCP (tearsheety) dla multi-symbol — odroczone; brak crasha (early-return).

## Wydajność

Test `test_broadcasting_perf.py::test_tensor_perf_scaling` weryfikuje, że backtest 20 symboli jest
istotnie szybszy niż 20× pojedynczy (dowód wektoryzacji, nie pętli): `t20 < max(0.5, 6·t1)` oraz
`t20 < 5.0 s` (po rozgrzaniu JIT poza pomiarem).

Szczegóły decyzji projektowej: [ADR-0001](../adr/0001-broadcasting-multi-symbol.md).
