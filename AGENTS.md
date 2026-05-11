# BlockBT - System Instructions & Agent Workflow

## [ROLE & DIRECTIVES]
Jesteś Głównym Architektem i Programistą w projekcie BlockBT. Pracujesz w rygorystycznym środowisku (Air-Gapped Logic). Zanim wygenerujesz lub zmienisz jakikolwiek kod:
1. Zawsze sprawdzaj, w której fazie projektu się znajdujemy (patrz sekcja PHASES).
2. Jeśli faza jest zamknięta - NIE MODYFIKUJ jej core'owego kodu bez wyraźnej zgody użytkownika.
3. Masz bezwzględny zakaz włączania ścieżek `vectorbtpro` do otwartego repozytorium (reguła BYOL).
4. Zanim zaczniesz pisać nowy kod, masz OBOWIĄZEK użyć narzędzia MCP `get_domain_context`, aby dowiedzieć się, w którym katalogu pracować i jakich klas bazowych użyć.

## [ARCHITECTURE CONSTRAINTS]
* **Dual-Engine Pattern:** Logika musi zawsze posiadać fallback na darmowy `vectorbt`.
* **Data Layer:** Pobieranie danych (np. Yahoo) musi być izolowane i zapisywane do formatu Parquet przed przetworzeniem.
* **Frontend:** Używamy React + FastAPI.

---

## [PHASES & CURRENT STATE]
> INSTUKCJA DLA MNIE (USERA): Oznaczaj zakończone fazy jako [DONE], a trwające jako [IN PROGRESS].

* **Phase 1: Database & ORM Scaffolding** * Status: [DONE]
  * Notatka: Modele w SQLAlchemy są gotowe. Struktura pyproject.toml działa.

* **Phase 2: Base Engine & Data Connectors**
  * Status: [DONE]
  * Cel: Implementacja `yahoo_finance.py` i struktury `BaseDataConnector`.
  * Wymagane narzędzia MCP: Serwer `BlockBT-Architectural-Router`.

* **Phase 3: Frontend Flow & Optuna Integration**
  * Status: [DONE]
  * Cel: Weryfikacja aktualnej implementacji (manual test flow) oraz przygotowanie planu rozszerzenia o Optunę. 
  * Wynik: Utworzono `TESTY_MANUALNE/01_frontend_backtest_flow.md`.

* **Repair Phase: Test Failure Fixes**
  * Status: [DONE]
  * Cel: Naprawa błędów wykrytych podczas testów manualnych.
  * Wynik: 
    - Naprawiono `AttributeError` w backendzie (benchmark_return oraz win_rate).
    - Naprawiono `NameError` (brakujące importy np, pd w runner.py).
    - Wprowadzono „pancerną” serializację metryk i mapowanie API (z wymuszeniem typów int/float).
    - Zaktualizowano schematy Pydantic o brakujące pola root-level.
    - Dodano logowanie diagnostyczne w backendzie i frontendzie (console.log).
    - Zresetowano początkowy stan frontendu (puste canvas).
    - 
* **Veryfy Phase 1:** Nodes connectors validate
  * Status: [PENDING]
  * Cel: Walidacja połączeń miedzy node'mi. aktuanie można uruchomic backtest bez łaczenia i da nam wynik 

* **Phase 4: Optimization Engine & Advanced Vectorization**
  * Status: [IN PROGRESS]
  * Cel: Pełne wykorzystanie biblioteki vectorbt opensource poprzez implementację zaawansowanej optymalizacji.
  * Kamienie Milowe:
    1. **Optuna API:** Nowy endpoint `/api/optimizer/` obsługujący optymalizację bayesowską (TPE). [DONE - Backend Integration]
    2. **Native Vectorization:** Refaktor silnika `OpenSourceEngine` pod kątem natywnej wektoryzacji kombinacji parametrów (wyeliminowanie pętli w grid search). [DONE]
    3. **Optimizer Node:** Nowy typ węzła we frontendowym Visual Builderze dedykowany do zadań optymalizacyjnych. [DONE]
    4. **Wizualizacja:** Integracja wyników Optuna (Parallel Coordinate Plot) w interfejsie.
    5. **Usuwanie wezłów:** funcjonalnosc usuwania wezłow [DONE]
    6. **Zapisywanie strategii:** mozliwosc zapisania [DONE]
    7. **Wczytanie zapisanej strategii:** popup z listą zapisanych strategii razem z wyszukiwarka, mozliwoscia usuniecia, wczytania [DONE]
    8. **Poprawa procesu:** Dodano `make kill-api` i `make clean` dla lepszego zarządzania procesami i czyszczenia zasobów. [DONE]
 