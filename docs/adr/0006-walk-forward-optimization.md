# ADR-0006: Realna Walk-Forward Optimization (okna IS/OOS, reuse Optuny)

- Status: Zaakceptowany
- Data: 2026-07-15
- Faza: 15

## Kontekst

`WalkForwardOptimizer.run_wfo` (`backend/app/services/engine/optimizer.py`) był stubem:
wykonywał pojedynczy backtest na całym zakresie danych, a `window_size`/`step_size` były
jedynie echem w odpowiedzi (odnotowane w review 2026-07-15 jako dług MED — „nie prezentować
jako pełne WFO"). Aplikacja miała już kompletną obudowę: endpoint `POST /api/optimizer/wfo`,
worker `run_walk_forward` (runner), zapis wyników przez `JobService`
(`best_params`/`best_value`/`trials` → kolumny `OptimizationJob`) oraz frontendowy `WfoNode`
czytający `trials_data`. Brakowało wyłącznie realnej logiki walk-forward: podziału szeregu
na okna in-sample (IS) / out-of-sample (OOS), optymalizacji per okno i agregacji metryk OOS.

Ograniczenia: kontrakt API `/api/optimizer/` musi pozostać niezłamany (rozszerzenia schematów
wyłącznie addytywne/opcjonalne), wyłącznie darmowy `vectorbt` (BYOL), reuse istniejących
optymalizatorów zamiast duplikacji, zero regresji względem baseline 152 testów.

## Rozważane opcje

### 1. Parametryzacja liczbą okien (`n_windows`) + procentowy podział IS/OOS

- Zysk: użytkownik nie musi znać długości danych; podział zawsze „się mieści".
- Koszt: **łamie istniejący kontrakt** — `WalkForwardRequest`, frontendowy `WfoNode`
  (pola `windowSize`/`stepSize`) i snapshot parametrów w DB operują już na długościach
  (`"365d"`/`"90d"`). Wymagałoby migracji UI i schematów; semantyka okien zależna od
  gęstości danych (inna liczba obserwacji przy lukach).

### 2. Długości `window_size` (IS) i `step_size` (OOS = krok) + tryby `rolling`/`anchored` — minimalny zestaw

- Zysk: w pełni zgodne wstecz (te same dwa parametry, które API i UI już przesyłają);
  `step_size` pełni podwójną rolę (długość OOS i krok przesuwu), więc segmenty OOS
  **przylegają do siebie bez nakładania** — łączny wynik OOS pokrywa dane dokładnie raz,
  co czyni agregację (zwrot składany) matematycznie poprawną. Dwa tryby (`rolling` — stała
  długość IS, `anchored` — IS rośnie od początku danych) to kanoniczny, minimalny zestaw
  wariantów WFO opisywany w literaturze; oba realizowane jednym generatorem okien.
- Koszt: brak niezależnej długości OOS ≠ krok (nakładające się OOS) — świadome cięcie,
  bo nakładający się OOS podwójnie liczy te same okresy w agregacie.

### 3. Splittery `vectorbt` (`rolling_split`/`range_split`)

- Zysk: mniej własnego kodu podziału.
- Koszt: splittery vbt operują pozycyjnie (liczba wierszy), a kontrakt BlockBT jest
  czasowy (`"365d"`); API splitterów różni się między wersjami vbt (ryzyko dla trybu
  Air-Gapped i ewentualnych aktualizacji); trudniej zagwarantować i przetestować własność
  „OOS ściśle po IS" na poziomie znaczników czasu. Podział to ~40 linii czystej arytmetyki
  na `pd.Timedelta` — koszt utrzymania własnej implementacji jest niski, a testowalność wysoka.

### Optymalizator in-sample: Optuna vs Grid Search

- `OptunaOptimizer.run_optimization` przyjmuje dokładnie ten format zakresów
  (`ParameterBounds`: `min`/`max`/`type`/`step`/`choices`), który już istnieje w schematach
  `/api/optimizer/`; ma też wbudowany guard `-inf` dla nieudanych triali.
- `GridSearchOptimizer` wymaga jawnych list wartości i ścieżki wektorowej silnika —
  niekompatybilne z `ParameterBounds` bez konwersji; per krótkie okno IS przewaga
  wektoryzacji jest niewielka.
- Wybrano **reuse `OptunaOptimizer`** (kompozycja per okno, zero duplikacji logiki).

## Decyzja

Wybrano **opcję 2** z optymalizacją in-sample przez **Optunę**:

- `WalkForwardOptimizer.split_windows(index, window_size, step_size, mode)` — czasowy
  generator okien `(is_start, is_end, oos_start, oos_end)` na przedziałach półotwartych:
  IS = `[is_start, is_end)`, OOS = `[oos_start, oos_end)`, `oos_start == is_end`
  (**brak look-ahead z konstrukcji**). Tryby: `rolling` (IS stałej długości, przesuw o
  `step_size`) i `anchored` (początek IS zakotwiczony, IS rośnie o `step_size`).
- `run_wfo(...)` per okno: opcjonalna optymalizacja IS (`param_bounds` → `OptunaOptimizer`,
  `n_trials`, `metric`), następnie backtest OOS na najlepszych parametrach
  (`{**parameters, **best_params}`). Bez `param_bounds` — czysta ewaluacja walk-forward na
  stałych parametrach (ścieżka zgodna z dotychczasowym wywołaniem z `WfoNode`).
- Agregacja OOS: zwrot całkowity składany geometrycznie z okien, Sharpe uśredniony;
  wszystkie metryki z guardem NaN/inf → `0.0` (konwencja silnika). Awaria backtestu
  jednego okna nie zrywa całego WFO (metryki `0.0` + pole `error` w raporcie okna).
- Kontrakt: `WalkForwardRequest` rozszerzony **addytywnie** o opcjonalne
  `mode` (`Literal["rolling","anchored"]`, domyślnie `rolling`), `param_bounds`,
  `n_trials`, `metric`. Wynik zawiera `best_params`/`best_value`/`trials`
  (kontrakt `JobService` → kolumny `OptimizationJob`), a raporty okien trafiają do
  `trials_data.trials` czytanego przez `WfoNode`.

### Aktualizacja po review integracyjnym (2026-07-16)

- **Konfiguracja przebiegu jako obiekt `WfoConfig`** (okna, tryb, `param_bounds`,
  `n_trials`, `metric`) — jedna wartość zamiast 6 parametrów przewlekanych przez
  sygnatury API → runner → `run_wfo` → `_evaluate_window`; `asdict(config)` jest
  wprost zawartością kolumny `bounds_definition` (koniec duplikacji `mode` /
  `window_size` w `parameters_snapshot`).
- **Odporność na awarie okien:** błąd optymalizacji IS **lub** backtestu OOS
  trafia do raportu okna (`error`, metryki `0.0`); okna z błędem są **wykluczane
  z agregatów**; awaria wszystkich okien → `RuntimeError` → job `FAILED`
  (wcześniej: `COMPLETED` z `best_value=0.0`).
- **Metryka celu honorowana end-to-end:** zawsze obecna w `oos_metrics` okna,
  steruje wyborem najlepszego okna; `best_value` = wartość metryki celu
  w najlepszym oknie OOS (spójnie z kontraktem `OptunaOptimizer`, gdzie
  `best_value` to wynik najlepszego triala — wcześniej zawsze łączny Total
  Return, niezależnie od `metric`).
- **Łączny Sharpe ze sklejonych zwrotów OOS** (annualizowany, `ddof=1`,
  zwroty liczone wewnątrz okien z `equity_curve` silnika — bez artefaktu na
  granicach okien); fallback do średniej per okno, gdy silnik nie zwraca
  krzywej kapitału.
- **Walidacje wejścia:** parametry-listy (tryb wektoryzowany silnika) odrzucane
  jawnie; wynik silnika bez klucza `metrics` = błąd okna (koniec cichych
  raportów all-zero); `ParameterBounds` walidowane na schemacie (min≤max,
  `step>0`, `choices` dla categorical) → `422` zamiast awarii Optuny w tle.
- **Wydajność:** okna wycinane `searchsorted`/`iloc` na posortowanym indeksie
  (guard monotoniczności) zamiast masek O(N) per okno; `is_df` materializowane
  tylko przy optymalizacji IS; Optuna dostaje **warm start** z najlepszych
  parametrów poprzedniego okna (`enqueue_trial`).
- **Zmiana zachowania (świadoma):** dane krótsze niż `window_size` + 1 obserwacja
  OOS → `ValueError` z zakresem dat i liczbą wierszy → job `FAILED`; stub
  poprzedniej wersji kończył się `COMPLETED`. Domyślne `365d` w `WfoNode` przy
  ≤ roku danych wymaga krótszego okna — komunikat błędu prowadzi użytkownika.
- **Raportowane `best_params` bez kluczy infrastrukturalnych** (`symbol`,
  `data_source`, `timeframe`, `initial_capital`, daty, konfiguracja okien) —
  silnik nadal dostaje pełny snapshot; snapshot w DB budowany z kluczami infra
  **po** `payload.parameters` (użytkownik nie nadpisze `symbol`/kapitału).

## Konsekwencje

**Pozytywne:**

- Realny WFO bez zmiany kontraktu API i frontendu — stare wywołania (`window_size`,
  `step_size`, `parameters`) działają bez modyfikacji, nowe pola są opcjonalne.
- Brak look-ahead gwarantowany konwencją przedziałów i pokryty testami
  (`is_slice.max() < oos_slice.min()` per okno, rolling i anchored).
- Reuse `OptunaOptimizer` — jedna implementacja logiki optymalizacji w repo.
- Raport per okno (granice IS/OOS w ISO, liczności, `best_params`, `oos_metrics`)
  audytowalny w DB i UI.

**Negatywne / do pilnowania:**

- Sekwencyjna pętla po oknach (bez wektoryzacji między oknami) — akceptowalne dla
  interwałów dziennych; przy dużych `n_trials` × liczbie okien czas rośnie liniowo
  (warm start Optuny z poprzedniego okna skraca zbieżność).
- Łączny Sharpe liczony ze sklejonych zwrotów OOS (patrz aktualizacja 2026-07-16);
  przybliżeniem pozostaje tylko fallback (średnia per okno) dla silników bez
  `equity_curve`.
- Brak niezależnej długości OOS ≠ krok (świadome cięcie — patrz opcja 2).
- `step_size` interpretowany kalendarzowo (`pd.Timedelta`), nie sesyjnie — przy danych
  z lukami okna mają różną liczbę obserwacji (raportowane w `is_rows`/`oos_rows`).
