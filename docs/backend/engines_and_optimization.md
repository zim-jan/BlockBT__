# Backend - Dual-Engine & Optimization

BlockBT wykorzystuje unikalną architekturę dwóch silników, która pozwala na elastyczne przełączanie się między rozwiązaniami Open-Source a wersjami komercyjnymi, przy jednoczesnym zachowaniu spójnego API dla reszty aplikacji.

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

---

## Przepływ Zadania (Runner)

Zadania backtestu i optymalizacji są wykonywane asynchronicznie przez `BacktestRunner` (`backend/app/services/engine/runner.py`):
1. Pobranie danych rynkowych przez `ConnectorRegistry`.
2. Pobranie instancji silnika przez `EngineLoader`.
3. Wykonanie obliczeń (Backtest lub Optuna).
4. Normalizacja wyników do formatu JSON.
5. Zapisanie wyników w bazie danych poprzez `JobService`.
