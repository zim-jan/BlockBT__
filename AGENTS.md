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
    1. **Optuna API:** Nowy endpoint `/api/optimizer/` obsługujący optymalizację bayesowską (TPE).
    2. **Native Vectorization:** Refaktor silnika `OpenSourceEngine` pod kątem natywnej wektoryzacji kombinacji parametrów (wyeliminowanie pętli w grid search).
    3. **Optimizer Node:** Nowy typ węzła we frontendowym Visual Builderze dedykowany do zadań optymalizacyjnych.
    4. **Wizualizacja:** Integracja wyników Optuna (Parallel Coordinate Plot) w interfejsie.
    5. **Error:** przy zamykaniu procesu make api ```INFO:     Stopping reloader process [61703]
     /home/przydan/.local/share/uv/python/cpython-3.13.12-linux-x86_64-gnu/lib/python3.13/multiprocessing/resource_tracker.py:400: UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown: {'/loky-61705-wwurfoft'}
       warnings.warn(```
       6. **ERROR2:** ``` 2026-05-11 13:36:21.538 | INFO     | app.main:lifespan:59 - Zamykanie API BlockBT.
      INFO:     Application shutdown complete.
      INFO:     Finished server process [123670]
      INFO:     Stopping reloader process [123668]
        /home/przydan/.local/share/uv/python/cpython-3.13.12-linux-x86_64-gnu/lib/python3.13/multiprocessing/resource_tracker.py:400: UserWarning: resource_tracker: There appear to be 1 leaked semaphore objects to clean up at shutdown: {'/loky-123670-asqlxoeb'}
      warnings.warn(
  ~/PycharmProjects/BlockBT-vm3-ai dev-przydan-improve* przydan@vm3-ai 2m 27s
  BlockBT-vm3-ai ❯ make api
  cd backend && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
  INFO:     Will watch for changes in these directories: ['/home/przydan/PycharmProjects/BlockBT-vm3-ai/backend']
  ERROR:    [Errno 98] Address already in use
  make: *** [Makefile:16: api] Błąd 1``` 