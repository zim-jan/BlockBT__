# ADR-0001: Broadcasting multi-symbol (Faza 10)

- **Status:** Zaakceptowany
- **Data:** 2026-07-14
- **Faza:** 10 — Broadcasting i Multi-wymiarowość (Filar 1)

## Kontekst

Do Fazy 9.3 pipeline DAG (`OpenSourceEngine.run_dag_backtest`) obsługiwał **pojedynczy symbol** —
`data.index` był `DatetimeIndex`, a `data["close"]` pojedynczą `Series`. Cel Fazy 10 (roadmap
`AGENTS.md`): „Macierze. Brak pętli. Szybkość." — jeden DAG ma testować **wiele tickerów naraz**
w jednej zwektoryzowanej symulacji `vectorbt`, z wynikami zgrupowanymi per ticker.

Zacommitowany test TDD (red) `test_broadcasting_multiple_tickers` podaje wejście jako wierszowy
`MultiIndex [symbol, date]` i oczekuje `metrics["AAPL"]`, `metrics["MSFT"]`. Wymagania:

1. Test red zielony **bez modyfikacji**; wszystkie istniejące testy (60) pozostają zielone
   (pełna kompatybilność wsteczna single-symbol).
2. Brak pętli po symbolach w obliczeniach (wektoryzacja).
3. Model BYOL — wyłącznie darmowy `vectorbt` (zakaz `vectorbtpro`).

## Rozważane opcje

### A. Pętla po symbolach (per-symbol loop)
Iterować po symbolach, uruchamiać istniejący single-symbol pipeline dla każdego i sklejać wyniki.

- **Zysk:** minimalna zmiana, zero ryzyka misalignmentu kolumn w `vectorbt`.
- **Koszt:** łamie twardy cel fazy („Brak pętli"). Czas rośnie liniowo z liczbą symboli — brak
  korzyści z wektoryzacji, którą daje `vectorbt`. Niereprezentatywne dla pracy dyplomowej
  (Filar 1 = broadcasting).

### B. Pivot LONG→WIDE + broadcasting po kolumnach (wybrana)
`_prepare_close` robi `unstack` LONG→WIDE (kolumny = symbole); istniejący pipeline broadcastuje po
kolumnach natywnie; metryki czytane z wektorowych Series `vectorbt`.

- **Zysk:** realna wektoryzacja (jedna symulacja), spełnia cel fazy, wykorzystuje mocną stronę
  `vectorbt`. Wydajność potwierdzona testem (`t20 < max(0.5, 6·t1)`).
- **Koszt:** ryzyko doklejania poziomów parametrów do kolumn wskaźników (`ma_window`) — wymaga
  normalizacji. Trzeba omijać `stats()`/QuantStats (jednokolumnowe w OSS vbt).

### C. Natywne `vbt.YFData(list)` jako źródło macierzy
Pozwolić `vectorbt` pobrać i ułożyć macierz wielosymbolową samodzielnie.

- **Zysk:** mniej własnego kodu pivotu.
- **Koszt:** układ kolumn (`MultiIndex` pól × symboli) jest wersjozależny i kruchy; wiąże warstwę
  danych z konkretnym zachowaniem biblioteki; utrudnia cache per symbol i testowalność.

## Decyzja

Wybrano **opcję B** (pivot LONG→WIDE + broadcasting po kolumnach). Warstwa danych buduje format
LONG deterministyczną pętlą I/O per symbol + `pd.concat(keys=symbols, names=["symbol"])`
(**nie** `vbt.YFData(list)` — odrzucono opcję C dla stabilności i cache).

Decyzje szczegółowe:

- **Normalizacja kolumn:** `IndicatorService._align_to_symbols` ustawia `columns = close.columns`
  po `MA.run`/`MACD`/`RSI`, usuwając doklejony poziom `ma_window`.
- **Guard NaN/inf:** metryki per ticker przez `float(x) if np.isfinite(x) else 0.0`
  (stała cena → 0 transakcji → Sharpe = `inf`).
- **Zakres v1:** jednoczesna wektoryzacja parametrów **i** symboli → `ValueError`
  (świadome cięcie zakresu); raporty QuantStats/`stats()` pomijane w ścieżce multi.
- **Kontrakt:** multi zwraca `is_multi_symbol`, `symbols`, `metrics`/`equity_curve` per ticker;
  single pozostaje płaski (bajtowo zgodny).

## Konsekwencje

**Pozytywne**

- Cel Fazy 10 spełniony: jedna zwektoryzowana symulacja, brak pętli w obliczeniach.
- Pełna kompatybilność wsteczna — ścieżka single-symbol nietknięta; 60 istniejących testów zielone.
- 11 nowych testów (broadcasting + wydajność); łącznie 71 backend pass.
- Wiedza utrwalona w MCP `get_domain_context` (`core_engine`, `data_connector`).

**Negatywne / dług techniczny**

- Multi-symbol nie ma jeszcze tearsheetów QuantStats ani raportu MCP (odroczone; early-return
  zapobiega crashowi).
- Wektoryzacja parametry×symbole niewspierana — do rozważenia w kolejnych fazach.
- `ffill().dropna(how="any")` zawęża dane do wspólnego kalendarza wszystkich symboli
  (uproszczenie wyrównania).

## Powiązania

- Instrukcja użytkownika: [Optymalizacja wielu tickerów](../backend/multi_ticker_optimization.md).
- Commity: `feat(schemas)`, `feat(engine)`, `feat(runner)`, `feat(frontend)` na
  `feature/faza-10-broadcasting`.
