# Backend - Dual-Engine & Optimization

BlockBT wykorzystuje unikalną architekturę dwóch silników, która pozwala na elastyczne przełączanie się między rozwiązaniami Open-Source a wersjami komercyjnymi, przy jednoczesnym zachowaniu spójnego API dla reszty aplikacji.

!!! note "Zakres pracy dyplomowej"
    W ramach pracy rozwijany i testowany jest **wyłącznie `OpenSourceEngine`** (darmowy `vectorbt`).
    `ProEngine` to jedynie **hook BYOL działający w trybie mock** — nie jest zaimplementowany produkcyjnie
    (brak licencji `vectorbtpro`) i nie podlega ocenie funkcjonalnej. Opisany niżej wzorzec Dual-Engine
    to decyzja architektoniczna (rozszerzalność), nie działająca integracja komercyjna.

## Architektura Silników

Rdzeniem systemu jest abstrakcyjny interfejs `BaseStrategyEngine` (`backend/app/services/engine/base.py`), który definiuje standardowe metody dla każdego silnika backtestowego.

### EngineLoader (Fabryka Silników)
`EngineLoader` (`backend/app/services/engine/loader.py`) to klasa typu Factory, która w czasie uruchomienia decyduje, który silnik zostanie zainicjalizowany.
- **Logika wyboru**: Jeśli w konfiguracji ustawiono `PREFER_PRO_ENGINE=true` i wykryto obecność biblioteki `vectorbtpro` w zdefiniowanej ścieżce, system ładuje `ProEngine`. W przeciwnym razie domyślnie używany jest `OpenSourceEngine`.

---

## Implementacje Silników

### OpenSourceEngine
Wykorzystuje publiczną wersję biblioteki `vectorbt`.
- **Charakterystyka**: W pełni wspiera wektoryzację (przetwarzanie wielu parametrów jednocześnie na tablicach NumPy).
- **Silnik Rust (Nowość)**: Od wersji 1.0.0, silnik wspiera natywne kernele Rusta. Ustawienie `VBT_ENGINE=rust` pozwala na pominięcie kompilacji JIT (Numba) i natychmiastowe wykonywanie obliczeń z najwyższą wydajnością. W przypadku braku binariów, system automatycznie wraca do silnika Numba.
- **Zastosowanie**: Domyślny silnik dla instalacji bezlicencyjnych. Zapewnia wysoką wydajność dla standardowych strategii technicznych.

### ProEngine (BYOL - Bring Your Own License)
Silnik zaprojektowany do współpracy z komercyjną biblioteką `vectorbtpro`.
- **Dynamiczne Ładowanie**: Biblioteka `vectorbtpro` jest ładowana dynamicznie (lazy import). System nie zawiera jej kodu, a jedynie "adapter", który się z nią łączy, jeśli użytkownik dostarczy własną licencję/pliki.
- **Tryb Mock (Symulacja)**: Jeśli użytkownik nie posiada `vectorbtpro`, `ProEngine` przełącza się w tryb symulacji. Generuje on realistyczne (losowe) wyniki backtestu i krzywe kapitału, co pozwala na testowanie interfejsu UI i przepływów danych bez posiadania licencji.

---

## Usługi Optymalizacji

BlockBT udostępnia dwa zaawansowane mechanizmy szukania optymalnych parametrów strategii.

### Grid Search Optimizer
Wykonuje wyczerpujący przegląd kombinacji parametrów (iloczyn kartezjański).
- **Wektoryzacja**: Dzięki natywnym mechanizmom `vectorbt`, silnik potrafi przeliczyć tysiące kombinacji w jednym "przebiegu", co eliminuje konieczność używania pętli i drastycznie przyspiesza proces.

### Optuna Optimizer
Integracja z biblioteką **Optuna** dla inteligentnego przeszukiwania przestrzeni parametrów.
- **Algorytm TPE**: Wykorzystuje optymalizację bayesowską do przewidywania, które parametry mogą przynieść najlepsze rezultaty, zamiast sprawdzać wszystkie możliwe wartości.
- **Skalowalność**: Idealny dla strategii z dużą liczbą parametrów, gdzie Grid Search byłby zbyt czasochłonny.

### Walk-Forward Optimization (WFO)
Pełna implementacja testowania strategii na oknach przesuwnych (Faza 15, `WalkForwardOptimizer` w `backend/app/services/engine/optimizer.py`).

- **Podział na okna**: `split_windows()` dzieli oś czasu na okna in-sample (IS) / out-of-sample (OOS) na przedziałach półotwartych — IS = `[is_start, is_end)`, OOS = `[is_end, oos_end)`. OOS zaczyna się dokładnie tam, gdzie kończy się IS, więc **look-ahead jest wykluczony z konstrukcji**. `window_size` (np. `"365d"`) to długość IS, `step_size` (np. `"90d"`) to długość OOS i jednocześnie krok przesuwu — segmenty OOS przylegają do siebie bez nakładania.
- **Tryby okien**:
    - `rolling` (domyślny) — okno IS o stałej długości przesuwa się o `step_size`,
    - `anchored` — początek IS zakotwiczony na starcie danych, okno IS rośnie o `step_size`.
- **Optymalizacja in-sample**: gdy żądanie zawiera `param_bounds`, w każdym oknie parametry są optymalizowane na danych IS przez istniejący `OptunaOptimizer` (`n_trials` prób, metryka celu `metric`), a następnie wykonywany jest backtest OOS na najlepszych parametrach. Bez `param_bounds` wykonywana jest czysta ewaluacja walk-forward na stałych parametrach strategii.
- **Agregacja wyników**: raport zawiera metryki per okno (granice IS/OOS, `best_params`, `oos_metrics`) oraz łączne metryki OOS — zwrot całkowity składany geometrycznie z okien i uśredniony Sharpe Ratio; wartości NaN/inf są sprowadzane do `0.0` (konwencja silnika). Awaria backtestu pojedynczego okna nie przerywa całego WFO (okno dostaje metryki `0.0` i pole `error`).
- **API**: `POST /api/optimizer/wfo` (schemat `WalkForwardRequest` — pola `mode`, `param_bounds`, `n_trials`, `metric` są opcjonalne i addytywne względem starego kontraktu) oraz węzeł `WfoNode` na frontendzie; wyniki per okno trafiają do `trials_data.trials` w `OptimizationJob`.
- **Decyzje projektowe**: patrz [ADR-0006](../adr/0006-walk-forward-optimization.md).

---

## Rejestr Wskaźników (IndicatorRegistry)

BlockBT posiada dynamiczny rejestr wskaźników (`backend/app/services/engine/indicator_registry.py`), który unifikuje dostęp do bibliotek:
- **vectorbt**: Natywne, wektoryzowane wskaźniki (np. MA, RSI).
- **TA-Lib**: Ponad 150 sprawdzonych wskaźników analizy technicznej.
- **Custom**: Możliwość rejestracji własnych funkcji Pythonowych.

Rejestr automatycznie wystawia metadane (wymagane parametry, typy danych) przez API, co pozwala frontendowi na dynamiczne generowanie formularzy konfiguracyjnych w Visual Builderze.

---

## Przepływ Zadania (Runner)

Zadania backtestu i optymalizacji są wykonywane asynchronicznie przez `BacktestRunner` (`backend/app/services/engine/runner.py`):
1. Pobranie danych rynkowych przez `ConnectorRegistry` (DataFrame z `DatetimeIndex`).
2. Pobranie instancji silnika przez `EngineLoader`.
3. Wykonanie obliczeń poprzez metodę `engine.run_backtest(df, parameters)` – **uwaga**: dane OHLCV są przekazywane jako pierwszy argument.
4. Normalizacja wyników. Każdy silnik zwraca ujednolicony obiekt zawierający klucz `metrics` z podstawowymi danymi (Total Return, Sharpe Ratio, itp.).
5. Zapisanie wyników w bazie danych poprzez `JobService`.

---

## Zgodność z NumPy

W celu zachowania stabilności z otwartą wersją biblioteki `vectorbt`, projekt wymusza wersję **NumPy < 2.0**. Jest to kluczowe dla poprawnego działania wektoryzowanych operacji na tablicach.
