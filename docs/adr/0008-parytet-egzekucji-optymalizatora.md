# ADR-0008: Parytet egzekucji optymalizatora/WFO ze ścieżką DAG

- **Status:** zaakceptowana
- **Data:** 2026-07-17
- **Kontekst:** pełny audyt codebase (3 niezależne przeglądy: silnik, API+dane, frontend)

## Kontekst i problem

Audyt z 2026-07-17 wykazał dwa defekty klasy P1 podważające wiarygodność
wyników optymalizacji — kluczowego wkładu pracy (Fazy 5 i 15):

1. **Rozjazd semantyki egzekucji.** Grid Search, Optuna i Walk-Forward
   Optimization oceniały strategie przez legacy `run_backtest`, który — w
   odróżnieniu od ścieżki DAG (`run_dag_backtest`) — **nie przesuwał sygnałów
   o 1 bar** (look-ahead bias) i **nie naliczał slippage**. Parametry
   „najlepsze" według optymalizatora były wybierane w warunkach nierealnie
   optymistycznych: ta sama strategia uruchomiona właściwym backtestem DAG
   dawała istotnie gorszy wynik, a OOS Sharpe w WFO był systematycznie
   zawyżony.
2. **Cicho ignorowane fragmenty grafu.** `run_dag_backtest` wykonuje dokładnie
   jeden łańcuch DataIngestion → Indicators → Execution — drugi węzeł
   wskaźnika, drugie źródło danych czy aktywny operator logiczny (crossover,
   crossunder, typing_cast) były pomijane **bez żadnego sygnału**. Użytkownik
   budował strategię „SMA + RSI + crossover", walidacja przechodziła, a silnik
   liczył wyłącznie pierwszy wskaźnik.

Dodatkowo annualizacja metryk (Sharpe) zakładała na sztywno dane dzienne
(`freq="D"`, 252 okresy/rok) niezależnie od faktycznego timeframe'u danych.

## Rozważane opcje

### Problem 1 — semantyka egzekucji

- **(A) Ujednolicić `run_backtest` z DAG** (shift + slippage w legacy ścieżce).
  - Zysk: jedna semantyka w całym systemie; optymalizator ocenia dokładnie to,
    co użytkownik dostanie z backtestu; zmiana w jednym miejscu obejmuje
    Grid/Optunę/WFO naraz.
  - Koszt: zmiana wyników legacy endpointu (deprecated) i historycznych
    porównań; **zmiana breaking** — oznaczona `!` w commicie.
- **(B) Przepisać optymalizatory na `execute_dag_portfolio`.**
  - Zysk: legacy nietknięte. Koszt: duplikacja pipeline'u sygnałów w trzech
    miejscach, ryzyko ponownego rozjazdu w przyszłości.
- **(C) Zostawić i udokumentować różnicę.**
  - Odrzucone wprost: wyniki optymalizacji z look-ahead biasem są bezwartościowe
    merytorycznie — to nie jest „różnica konwencji", tylko błąd metodyczny.

### Problem 2 — nieobsługiwane topologie

- **(D) Pełna egzekucja grafu** (topo-sort, łączenie sygnałów wielu wskaźników).
  - Zysk: docelowa funkcjonalność. Koszt: duży zakres (algebra sygnałów,
    broadcasting po kombinacjach), poza budżetem bieżącej iteracji.
- **(E) Głośna walidacja:** `GraphParser` odrzuca (422) topologie, których
  silnik nie wykonuje. Zysk: natychmiastowa uczciwość wyników minimalnym
  kosztem; jasny komunikat dla użytkownika. Koszt: część grafów przestaje
  przechodzić walidację (słusznie).

## Decyzja

**Opcje (A) + (E)**, plus mapa `timeframe → (freq, okresy/rok)` jako jedno
źródło prawdy annualizacji:

- `run_backtest` bezwarunkowo aplikuje `fshift(1)` na entries/exits (obie
  gałęzie: skalarna i wektoryzowana Grid Search) oraz przekazuje `slippage`
  (domyślnie 0.001) do `Portfolio.from_signals`.
- `GraphParser._validate_supported_topology()` odrzuca: >1 węzła DataIngestion,
  >1 węzła Indicators oraz operatory `crossover`/`crossunder`/`typing_cast`.
  Pass-through pozostają: `time_shift` (no-op, ADR-0007) i `cross_validation`
  (marker walidatora Overfitting Trap).
- `freq_for_timeframe()` / `periods_per_year_for_timeframe()` (konwencja
  kalendarza giełdowego US: 252 sesje, sesja 6.5h) zasilają `from_signals`
  w obu ścieżkach oraz łączny Sharpe OOS w WFO.

## Konsekwencje

- **Test parytetu** pinuje kontrakt: identyczne dane + parametry ⇒ identyczny
  `total_return_pct`/`num_trades` w `run_backtest` i `run_dag_backtest`
  (`test_execution_parity.py`).
- Wyniki optymalizacji po zmianie są **niższe niż przed** — to oczekiwane
  (zniknęło systematyczne zawyżenie), istotne przy porównywaniu z wynikami
  sprzed 2026-07-17.
- Grafy z wieloma wskaźnikami przestają przechodzić walidację do czasu
  implementacji pełnej egzekucji grafu (opcja D — praca przyszła).
- Sharpe dla danych intraday zmienia wartość (poprawna skala annualizacji);
  dane dzienne bez zmian (252).

## Powiązania

- ADR-0006 (WFO), ADR-0007 (auto-shift) — niniejsza decyzja domyka spójność
  shiftu we WSZYSTKICH ścieżkach egzekucji.
- Kod: `backend/app/services/engine/opensource_engine.py` (`run_backtest`,
  `_TIMEFRAME_MAP`), `backend/app/core/utils/graph_parser.py`
  (`_validate_supported_topology`), `backend/app/services/engine/optimizer.py`
  (annualizacja WFO).
- Testy: `test_engine/test_execution_parity.py`, `test_engine/test_annualization.py`,
  `test_utils/test_graph_parser.py` (sekcja topologii).
