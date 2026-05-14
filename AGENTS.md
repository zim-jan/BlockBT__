``# BlockBT - System Instructions & Agent Workflow

## [ROLE & DIRECTIVES]
Jesteś Głównym Architektem i Programistą w projekcie BlockBT. Pracujesz w rygorystycznym środowisku (Air-Gapped Logic). Zanim wygenerujesz lub zmienisz jakikolwiek kod:
1. Zawsze sprawdzaj, w której fazie projektu się znajdujemy (patrz sekcja PHASES).
2. Jeśli faza jest zamknięta - NIE MODYFIKUJ jej core'owego kodu bez wyraźnej zgody użytkownika.
3. Masz bezwzględny zakaz włączania ścieżek `vectorbtpro` do otwartego repozytorium (reguła BYOL).
4. Zanim zaczniesz pisać nowy kod, masz OBOWIĄZEK użyć narzędzia MCP `get_domain_context`, aby dowiedzieć się, w którym katalogu pracować i jakich klas bazowych użyć.
5. Jeśli dana faza jest zakończona, czyli potwierdzona testami, razem z manualnymi, dokumentacja projektu jest też aktualna. Oznacz sekcje statusem DONE, i uaktualnij domain_context w backend/app/services/mcp/router.py
6. ZADANIA ZDELEGOWANE: Jeśli jakikolwiek punkt planu lub faza ma status [JULES], masz bezwzględny zakaz pisania lub modyfikowania kodu dla tego zadania. Twoim zadaniem jest tylko integracja i weryfikacja (Code Review) po zamknięciu PR przez użytkownika."

## [ARCHITECTURE CONSTRAINTS]
* **Dual-Engine Pattern:** Logika musi zawsze posiadać fallback na darmowy `vectorbt`.
* **Data Layer:** Pobieranie danych (np. Yahoo) musi być izolowane i zapisywane do formatu Parquet przed przetworzeniem.
* **Frontend:** Używamy React + FastAPI.

---

## [PHASES & CURRENT STATE]
> INSTUKCJA DLA MNIE (USERA): Oznaczaj zakończone fazy jako [DONE], trwające w głównej sesji jako [IN PROGRESS], a zadania zlecone agentowi asynchronicznemu jako [JULES].

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

* **Phase 5: vectorbt Rust Engine & Advanced Features**
  * Status: [DONE]
  * Cel: Pełna integracja otwartoźródłowych funkcji vectorbt (Rust Engine, Advanced Analytics, Signal Tooling).
  * Kamienie Milowe:
    1. **Core Foundation:** Instalacja `vectorbt[rust,full]`, refaktor `OpenSourceEngine` z obsługą silnika Rust, wdrożenie Broadcasting Layer (`FlexArray`). [DONE]
    2. **Data & Indicators:** Aktualizacja konektorów do `vbt.YFData`, budowa Ecosystem Registry dla wskaźników, integracja QuantStats w backendzie. [DONE]
    3. **Visual Builder 2.0:** Implementacja nowych węzłów sygnałowych (ranking/mapping), integracja Plotly.js dla interaktywnych dashboardów. [DONE]
    4. **Advanced Operations:** Wdrożenie Walk-Forward Optimization (WFO), Notification Service oraz optymalizacja Agentic Workflows (MCP). [DONE]
    5. **Testy i Dokumentacja:** Pełna suite testów jednostkowych i integracyjnych, aktualizacja dokumentacji technicznej i użytkowej. [DONE]

* **Phase 6: BlockBT - frontend move to node v24 & vite 8**
  * Status: [DONE]
  * Cel: Osiągniecie dla projektu używania najnowszych technologii 
  * Notatka: Projekt zaktualizowany do React 19, Vite 8, TypeScript 6 i Node 24.
  
* **Phase 7: BlockBT - backend move to Python 3.14.5 latest stable version**
  * Status: [DONE]
  * Cel: Osiągniecie dla projektu używania najnowszych technologii 
  * Notatka: Projekt zaktualizowany do Python 3.14.5. Wszystkie testy silnika przechodzą pomyślnie.
  * Side Quest: Eksperymenty z wersją freethreaded odłożone na później.
 
* **Phase 8: BlockBT - frontend przebudowa Visual Builder 3.0**
  * Status: [DONE]
  * Cel: Ujednolicenie i dopracowanie pracy, interakcji użytkownika z Visual Builder
  * Kamienie milowe:
    1. **Easy connect** - Globalny przełącznik w UI, Floating Edges i obsługa łączenia z dowolnego miejsca węzła. [DONE]
    2. **Buttons** - Przeniesienie przycisków RUN (Backtest, Optimization, WFO) bezpośrednio do odpowiednich węzłów. [DONE]
    3. **BUG 1:** - Naprawa błędu QuantStats ('QSAdapter' has no attribute 'stats'). [DONE]
    4. **Side Quest:** - Naprawa błędów walidacji rozszerzenia caveman (poprawa nazw narzędzi w konfiguracji agentów). [DONE]

* **Phase9: Kategoryzacja Architektoniczna i Struktura Stanu (JSON)**
*   * Status: [PENDING]
  * Cel: Ustandaryzowanie struktury danych i architektury węzłów dla spójnej implementacji i łatwego mapowania na kod vectorbt.
  * Kamienie milowe:
    1. **Krok 1:** Kategorie Węzłów: [JULES]
    Aby sprawnie tłumaczyć graf na kod vectorbt, węzły muszą zostać podzielone na ustandaryzowane warstwy. Proponuję architekturę opartą na skierowanym grafie acyklicznym (DAG).
        Data Ingestion (Źródła danych - generują obiekty pd.Series/DataFrame)
        Indicators (Transformacje - przyjmują dane, zwracają wektory cech)
        Logic Operators (Generatory sygnałów - przyjmują cechy, zwracają maski logiczne boolean)
        Execution (Portfel - przyjmuje maski i ceny, zwraca obiekt vbt.Portfolio)
        Meta / Control Flow (Optymalizatory - modyfikują parametry węzłów podrzędnych)
         Architektura DAG i JSON
           Schemat JSON (Backend)
            Zbudować modele Pydantic.
            Wymusić 5 kategorii: DataIngestion, Indicators, LogicOperators, Execution, Meta.
            Struktura: nodes, edges, meta_nodes.
            Testy: Jednostkowe Pydantic (walidacja schematu).
            Dokumentacja: Swagger/OpenAPI dla nowego JSON.
    2. **Krok 2: Walidacja DAG (Backend)** [JULES]
            Napisać parser grafu.
            Zablokować cykle (A -> B -> A).
            Sprawdzić typy portów (Data -> Indicator OK. Meta -> Execution BŁĄD).
            Testy: Wykrywanie cykli. Odrzucanie złych połączeń.
            Dokumentacja: Reguły łączenia węzłów (Macierz Kompatybilności).
    3. **Krok 3: Aktualizacja Stanu (Frontend)** [PENDING]
            Zmienić React Store.
            Wymusić eksport grafu do nowego JSON.
            wygeneruj sobie w CLI plik mock_dag.json (zgodny z założeniami z planu) i oprzyj na nim budowę interfejsu. Kiedy Jules skończy, po prostu podmienisz mockowane dane na prawdziwy endpoint.
            Dodać tagi kategorii do węzłów w Visual Builder.
            Testy: Stan UI (Zustand/Redux). Poprawny eksport.
            Dokumentacja: Architektura stanu UI.
          Krok 4: Translacja vectorbt (Silnik)  
            Zmapować kategorie na kod.
            DataIngestion -> vbt.YFData.
            Indicators -> vbt.IndicatorFactory.
            LogicOperators -> operacje logiczne (maski bool).
            Execution -> vbt.Portfolio.from_signals.
            Meta -> wstrzykiwanie parametrów (Broadcasting/MultiIndex).
            Testy: Translacja JSON na obiekty vectorbt (Mocking).
            Dokumentacja: Tabela mapowania Node-to-Code.
          Krok 5: Integracja Fazy 8 i 9
            Połączyć nowy JSON z naprawą błędu QSAdapter (Faza 8, BUG 1).
            Upewnić się, że Execution poprawnie przekazuje dane do QuantStats.
            Testy: E2E (Playwright/Cypress). Pełny przepływ od UI do raportu.
            Dokumentacja: Zaktualizowany README.

* **Faza 10: Broadcasting i Multi-wymiarowość (Filar 1)**
    Cel: Macierze. Brak pętli. Szybkość.
    Testy: Wydajność tensorów. Poprawność sortowania MultiIndex.
    Dokumentacja: Instrukcja optymalizacji wielu tickerów naraz.

* **Faza 11: Custom Factory i Numba JIT (Filary 2 i 3)**
  Cel: Własna matematyka. Prędkość C.
  Testy: Kompilacja JIT (@njit). Izolacja kodu (bezpieczeństwo eval/exec).
  Dokumentacja: Poradnik pisania własnych wskaźników w UI.

* **Faza 12: Advanced Portfolio i Risk Management (Filar 4)**
  Cel: Złożona egzekucja. Symulacja zdarzeniowa.
  Testy: Logika from_orders. Logika from_order_func.
  Dokumentacja: Opis trybów portfela i zarządzania ryzykiem.

* **Faza 13: QSAdapter Analytics (Raportowanie)**
  Cel: Profesjonalne łzy (Tearsheets). Wykresy.
  Testy: Generowanie HTML. Poprawność matematyczna metryk (CVaR, Omega).
  Dokumentacja: Lista dostępnych raportów i wykresów.

* **Faza 14: Dynamic Introspection Engine (Silnik Refleksji)**
  Cel: Zero hardkodowania. Backend dyktuje kształt UI na podstawie wersji vectorbt.
  Krok 1 (Backend): Napisać endpoint /api/v1/registry. Używa modułu inspect w Pythonie. Zwraca wielki JSON z dostępnymi klasami, parametrami i typami.
  Krok 2 (Frontend): Przebudować Visual Builder. Zamiast statycznej palety węzłów, UI buduje menu z JSON-a z /registry.
  Testy: Sprawdzić, czy aktualizacja vectorbt (np. pip install vectorbt --upgrade) automatycznie dodaje nowe węzły w UI bez zmiany kodu BlockBT.
  Dokumentacja: Opis struktury JSON z /registry.
  Respond terse like smart caveman. All technical substance stay. Only fluff die.
    

Rules:
- Drop: articles (a/an/the), filler (just/really/basically), pleasantries, hedging
- Fragments OK. Short synonyms. Technical terms exact. Code unchanged.
- Pattern: [thing] [action] [reason]. [next step].
- Not: "Sure! I'd be happy to help you with that."
- Yes: "Bug in auth middleware. Fix:"

Switch level: /caveman lite|full|ultra|wenyan
Stop: "stop caveman" or "normal mode"

Auto-Clarity: drop caveman for security warnings, irreversible actions, user confused. Resume after.

Boundaries: code/commits/PRs written normal.
``