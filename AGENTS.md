``# BlockBT - System Instructions & Agent Workflow

## [ROLE & DIRECTIVES]
Jesteś Głównym Architektem i Programistą w projekcie BlockBT. Pracujesz w rygorystycznym środowisku (Air-Gapped Logic). Zanim wygenerujesz lub zmienisz jakikolwiek kod:
1. Zawsze sprawdzaj, w której fazie projektu się znajdujemy (patrz sekcja PHASES).
2. Jeśli faza jest zamknięta - NIE MODYFIKUJ jej core'owego kodu bez wyraźnej zgody użytkownika.
3. Masz bezwzględny zakaz włączania ścieżek `vectorbtpro` do otwartego repozytorium (reguła BYOL).
4. Zanim zaczniesz pisać nowy kod, masz OBOWIĄZEK użyć narzędzia MCP `get_domain_context`, aby dowiedzieć się, w którym katalogu pracować i jakich klas bazowych użyć.
5. Jeśli dana faza jest zakończona, czyli potwierdzona testami, razem z manualnymi, dokumentacja projektu jest też aktualna. Oznacz sekcje statusem DONE, i uaktualnij domain_context w backend/app/services/mcp/router.py
6. ~~ZADANIA ZDELEGOWANE: Jeśli jakikolwiek punkt planu lub faza ma status [JULES]...~~ **[WYCOFANE — decyzja Janka 2026-07-13]:** reguła [JULES] NIE obowiązuje. Ignoruj wszelkie oznaczenia [JULES]; nie ma zadań delegowanych do agenta asynchronicznego. (Spójne z głównym CLAUDE.md.)

## [ARCHITECTURE CONSTRAINTS]
* **Dual-Engine Pattern:** Logika musi zawsze posiadać fallback na darmowy `vectorbt`.
* **Data Layer:** Pobieranie danych (np. Yahoo) musi być izolowane i zapisywane do formatu Parquet przed przetworzeniem.
* **Frontend:** Używamy React + FastAPI.

---

## [PHASES & CURRENT STATE]
> INSTRUKCJA DLA MNIE (USERA): Oznaczaj zakończone fazy jako [DONE], trwające w głównej sesji jako [IN PROGRESS]. (Status [JULES] wycofany 2026-07-13 — patrz pkt 6 wyżej.)

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
  * Status: [DONE]
  * Cel: Walidacja połączeń miedzy node'mi. aktuanie można uruchomic backtest bez łaczenia i da nam wynik 
  * Wynik: GraphParser + COMPATIBILITY_MATRIX wymusza walidację krawędzi DAG. Endpoint `/api/backtest/dag` zwraca 422 przy nieprawidłowych połączeniach.

* **Phase 4: Optimization Engine & Advanced Vectorization**
  * Status: [DONE]
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
  * Status: [DONE]
  * Cel: Ustandaryzowanie struktury danych i architektury węzłów dla spójnej implementacji i łatwego mapowania na kod vectorbt.
  * Kamienie milowe:
    1. **Krok 1: Kategorie Węzłów** [DONE]
        Pydantic models w `dag.py`: DataIngestionNode, IndicatorsNode, LogicOperatorsNode, ExecutionNode, MetaNode.
        Discriminator-based AnyNode union. 5 kategorii wymuszone.
    2. **Krok 2: Walidacja DAG (Backend)** [DONE]
        GraphParser w `graph_parser.py`: Algorytm Kahna (wykrywanie cykli), COMPATIBILITY_MATRIX (walidacja typów portów), analiza osiągalności.
    3. **Krok 3: Aktualizacja Stanu (Frontend)** [DONE]
        workflowStore.ts: exportDAG() serializuje graf do schematu DAG. CategoryBadge.tsx taguje węzły.
        useWorkflowExecution.ts: wysyła DAG payload do `/api/backtest/dag`.
    4. **Krok 4: Translacja vectorbt (Silnik)** [DONE]
        OpenSourceEngine.run_dag_backtest(): DataIngestion→vbt.YFData, Indicators→IndicatorService, Execution→vbt.Portfolio.from_signals.
        runner.py: automatyczny routing DAG vs legacy.
    5. **Krok 5: Integracja i Weryfikacja E2E** [DONE]
        Naprawiono Yahoo connector testy (mock `_download` zamiast `yfinance.download`).
        Dodano testy API dla `/api/backtest/dag` (5 test cases).
        Naprawiono COMPATIBILITY_MATRIX: Indicators→Execution dozwolone (Signal node opcjonalny).
        Usunięto hardkodowaną walidację krawędzi z frontendu (delegacja do GraphParser).
        Zaktualizowano README z dokumentacją DAG.

* **Faza 9.1: Poprawki:**
  * Status: [DONE]
  * Cel: Rozwiązanie znalezionych problemów
    * Krok 1: Brak możliwości ponownego wywołania backtestu, dodanie resetu węzła portfolioNode by po zmianie parametrów moć ponownie wykonać backtest [DONE]
      *  2. Reset Stanu Portfolio (isOutdated)
    * Krok 2: BUG: przy DAG {{DataNode --> IndicatorNode --> SignalNode --> PortfolioNode}} pojawia się błąd [DONE]
    ```
    ❌ API Error 422: POST /api/backtest/dag {"detail":[{"type":"missing","loc":["body","dag","nodes",2,"LogicOperators","params","condition"],"msg":"Field required","input":{"signalType":"sma_crossover"}}]} api.ts:38:17
    request api.ts:38
    💥 API Request Failed: POST /api/backtest/dag Error: API 422: {"detail":[{"type":"missing","loc":["body","dag","nodes",2,"LogicOperators","params","condition"],"msg":"Field required","input":{"signalType":"sma_crossover"}}]}
    request api.ts:40
    api.ts:55:15
    request api.ts:55
    ```
    * Krok 3: Upewnienie się, czy w bazie zapisują się strategie wg nowego standardu DAG w formacie json [DONE]
    * Krok 4: Usunięcie logiki legacy [DONE]
    * Krok 5: Powiększenie uchwytów w węzłach do połączeń dla ułatwienia trafienia myszką [DONE]
      * **Root cause wcześniejszego FAIL-a:** style easy-connect (w tym 40px handle) były dopisane
        do `frontend/src/index.css`, którego aplikacja **w ogóle nie importuje** — aktywny arkusz to
        `frontend/src/assets/index.css` (import w `main.tsx`). Zmiany CSS nie miały żadnego efektu.
      * **Fix (branch fix/review-backlog):** `connectionRadius={40}` na `<ReactFlow>` w
        `WorkflowEditor.tsx` (promień "przyciągania" końca połączenia do uchwytu; default 20)
        + `.react-flow__handle { min-width: 20px; min-height: 20px; }` w **aktywnym**
        `assets/index.css` (obszar startu przeciągania; default 6x6px).
        Ref: https://reactflow.dev/api-reference/react-flow#connectionradius
* **Faza 9.2: Poprawki 2 (EasyConnect):**
  * Status: [PARTIAL] — oczywiste bugi naprawione (branch fix/review-backlog, 2026-07-15); pełny wzorzec easy-connect świadomie odłożony
  * Cel: Rozwiązanie znalezionych problemów z easyconnect
  * Diagnoza (code review 2026-07-15) — zidentyfikowane problemy i ich stan:
    1. **Martwy arkusz stylów [NAPRAWIONE]:** cały CSS easy-connect (ukrywanie standardowych
       uchwytów, niewidzialne 40px strefy `easy-connect-handle`, z-index dla treści węzłów)
       żył w `src/index.css`, którego aplikacja nie importuje (aktywny arkusz: `assets/index.css`).
       Klasa `easy-connect-active` nie miała więc ŻADNEGO efektu wizualnego — tryb EasyConnect
       realnie zmieniał tylko komponent linii połączenia (FloatingConnectionLine) i typ nowych
       krawędzi (floating). Martwy plik usunięty; jego CSS celowo NIE przeniesiony (patrz „Odłożone").
    2. **Kotwiczenie krawędzi floating [NAPRAWIONE]:** `edges/utils.ts` szukał uchwytów wyłącznie
       w `handleBounds.source`; węzeł Portfolio ma tylko uchwyt `target`, więc krawędź floating
       zawsze spadała do fallbacku i kończyła się w ŚRODKU węzła (pod jego bryłą).
       Fix: wyszukiwanie source → target.
    3. **Fallbacki `||` na współrzędnych [NAPRAWIONE]:** `FloatingConnectionLine` traktował
       współrzędną 0 jak brak wartości (`tx || toX`). Fix: `??`.
    4. **Mieszane typy krawędzi po przełączeniu trybu [NAPRAWIONE]:** typ (`floating`/`default`)
       zapisywał się w krawędzi w momencie utworzenia (`defaultEdgeOptions`), więc po zmianie
       trybu graf renderował mieszankę typów. Fix: typ krawędzi jest pochodną aktualnego trybu
       (mapowanie w render `WorkflowEditor`), store przechowuje krawędzie bez zmian.
  * Odłożone (świadomie — wyższe ryzyko, do decyzji przy powrocie do fazy):
    * Pełny wzorzec easy-connect z oficjalnego przykładu React Flow
      (`docs/external_libs/react_flow/examples_easy-connect.md`): pełnowymiarowe uchwyty
      source+target przełączane przez `useConnection()` + `isConnectableStart={false}` na target.
      Wymaga przebudowy wszystkich 7 węzłów. Stary CSS (ukrywanie uchwytów target + niewidzialne
      40px strefy) NIE został przeniesiony do aktywnego arkusza, bo ukrycie uchwytów target
      utrudnia/psuje kończenie połączeń w trybie strict (drop polega wtedy na przyciąganiu do
      nieaktualnych bounds ukrytych uchwytów — kruche).
    * Klasa `react-flow__node-drag-handle` na nagłówkach węzłów nie działa bez ustawienia
      właściwości `dragHandle` na węźle (dziś cały węzeł jest draggable; przy pełnowymiarowych
      uchwytach trzeba to domknąć).
  * Uwaga: po fixie Kroku 5 Fazy 9.1 (`connectionRadius={40}` + min 20px uchwyty) łączenie
    węzłów jest wygodne również bez trybu EasyConnect.

* **Faza 9.3: Stabilizacja Pipeline DAG (Filar 0)**
  * Status: [DONE]
  * Cel: Eliminacja błędów wykonawczych i zapewnienie kompatybilności z silnikiem Rust.
  * Kamienie Milowe:
    1. **Pydantic Validation Fix:** Naprawiono błąd 422 poprzez opcjonalność `signalType` w `LogicOperatorsParams` (wymagane dla TimeShift). [DONE]
    2. **Rust Engine Compatibility:** Wdrożono jawne rzutowanie `bool -> float64` w operacjach `fshift` (TimeShift) oraz w progach RSI, eliminując błędy castingu w backendzie Rust. [DONE]
    3. **Indicator Bridges:** Zaimplementowano mosty dla `vbt_MA` i `vbt_RSI`, umożliwiające poprawne mapowanie parametrów DAG na natywne wywołania `vectorbt` i konwersję na sygnały logiczne. [DONE]
    4. **TDD Verification:** Wszystkie 60 testów backendowych przechodzi, weryfikacja manualna potwierdza stabilność przepływu Data -> Indicator -> Signal -> TimeShift -> Portfolio. [DONE]

* **Faza 10: Broadcasting i Multi-wymiarowość (Filar 1)** [DONE]
    Cel: Macierze. Brak pętli. Szybkość. [DONE]
    1. **Pivot LONG→WIDE:** `_prepare_close` wykrywa wierszowy MultiIndex `[symbol, date]` i przez `unstack` buduje macierz WIDE (index=daty, kolumny=symbole); silnik wektoryzuje po kolumnach bez pętli. [DONE]
    2. **Metryki per ticker:** gałąź multi w `run_dag_backtest` liczy metryki z wektorowych Series vectorbt (guard NaN/inf → 0.0) i zwraca `metrics`/`equity_curve` zgrupowane per symbol (kontrakt `is_multi_symbol`). [DONE]
    3. **Normalizacja kolumn:** `IndicatorService._align_to_symbols` usuwa doklejony poziom `ma_window`; blokada wektoryzacji parametry×symbole (`ValueError`). [DONE]
    4. **Warstwa danych + runner:** `fetch(str|list)` → LONG concat; rekurencyjna serializacja metryk bez spłaszczania nested per-symbol. [DONE]
    5. **Frontend:** DataNode (przecinki), PortfolioNode (accordion per ticker + jeden wykres multi-trace). [DONE]
    Testy: Wydajność tensorów. Poprawność sortowania MultiIndex. [DONE] — `test_broadcasting.py` (9 testów) + `test_broadcasting_perf.py` (2 testy), 71 backend pass.
    Dokumentacja: Instrukcja optymalizacji wielu tickerów naraz. [DONE] — patrz `docs/backend/multi_ticker_optimization.md` + ADR-0001.

* **Faza 11: Custom Factory i Numba JIT (Filary 2 i 3)** [DONE]
  Cel: Własna matematyka. Prędkość C. [DONE]
    1. **Sandbox AST (deny-by-default):** `IndicatorService._validate_code_safety` — allowlista węzłów (`_ALLOWED_AST_NODES`), denylista nazw (`_FORBIDDEN_NAMES`) i atrybutów (`_FORBIDDEN_ATTRIBUTES`: dunder + ramki + `ctypes`/`tobytes` + serializatory `to_csv`/`tofile`/... + `system`/`popen`). Naruszenie → `ValueError("Unsafe code detected: ...")`. Zero zależności zewnętrznych (Air-Gapped/BYOL). [DONE]
    2. **`compile_custom_indicator` + Numba `@njit`:** kontrakt funkcji 1D `np.ndarray → np.ndarray`, kompilacja `@njit` leniwa (pierwszy `.run()`), wektoryzacja per kolumnę w `apply_func`, opakowanie w `vbt.IndicatorFactory` → klasa z `.run()`. „Prędkość C". [DONE]
    3. **Hardening `generate_custom`:** ścieżka DAG `indicatorType=="custom"` — walidacja AST + zamknięte `__builtins__` (`_safe_builtins`) przed `exec`; użytkownik definiuje `entries`/`exits` (dostępne: `close`, `vbt`, `np`, `pd`). [DONE]
    4. **Frontend:** węzeł Indicators tryb „Custom Code" (`IndicatorNode.tsx`) — textarea + hint o sandboxie + wyświetlanie błędu walidacji (`data.error`). [DONE]
  Testy: Kompilacja JIT (@njit). Izolacja kodu (bezpieczeństwo eval/exec). [DONE] — 48 testów sandboxa.
  Dokumentacja: Poradnik pisania własnych wskaźników w UI. [DONE] — `docs/frontend/custom_indicators.md` + ADR-0002.

* **Faza 12: Advanced Portfolio i Risk Management (Filar 4)** [DONE]
  Cel: Złożona egzekucja. Symulacja zdarzeniowa. [DONE]
    1. **Schema ryzyka:** `ExecutionParams` (`schemas/dag.py`) — `sl_stop`/`tp_stop` (0..1), `sl_trail` (bool), `size` (>0), `size_type` (`amount|value|percent`). [DONE]
    2. **Egzekucja:** `execute_dag_portfolio` przekazuje parametry do `vbt.Portfolio.from_signals` tylko gdy ustawione (zero regresji Faz 10/11); `size_type` przyjęty jako string wprost (vbt 1.0.0). [DONE]
    3. **Wymóg Indicators:** `run_dag_backtest` rzuca `GraphValidationError`, gdy DAG nie ma węzła Indicators (bez sygnału SL/TP nie ma na czym zadziałać). [DONE]
    4. **Surfacing SL/TP:** vbt nie eksponuje liczników wyjść SL/TP w `stats()`/enumie w sposób niezależny od wersji — `_count_stop_exits` klasyfikuje zamknięte transakcje po cenie wyjścia vs poziom stopu (long/short, `eps=1e-3`); trafia do `raw` tylko gdy dany stop ustawiony. Multi-symbol surfacing poza zakresem. [DONE]
    5. **Frontend:** pola Stop Loss/Take Profit/Position Size w `PortfolioNode.tsx` (UI w %, zapis jako frakcja 0..1). [DONE]
  Testy: Logika from_orders (odłożona, poza zakresem — patrz ADR-0003). Logika stopów `from_signals` zielona (zamrożony RED test przebudowany za zgodą Janka: wymóg Indicators wymusił dodanie węzła custom-indicator generującego wejście). [DONE]
  Dokumentacja: Opis trybów portfela i zarządzania ryzykiem. [DONE] — `docs/backend/risk_management.md` + ADR-0003.

* **Faza 13: QSAdapter Analytics (Raportowanie)** [DONE]
  Cel: Profesjonalne łzy (Tearsheets). Wykresy. [DONE]
    1. **`QSAdapterService.generate_tearsheet(pf)`:** samodzielny, air-gapped HTML tearsheet budowany z `pf.stats()` (świadomie NIE przez `qs.reports.html` — zwraca None/wymaga displaya); wzorzec `_extract_qs_metrics`. [DONE]
    2. **Endpoint `GET /api/results/{job_id}/tearsheet`:** `ApiResponse[TearsheetResponse]` (404/400); adapter `stats()` z metryk `BacktestJob` (job nie trzyma żywego obiektu Portfolio). [DONE]
  Testy: Generowanie HTML. Poprawność matematyczna metryk (CVaR, Omega). [DONE] — 7/7 testów tearsheet, regresja zielona.
  Dokumentacja: Lista dostępnych raportów i wykresów. [DONE] — `docs/backend/analytics_tearsheets.md` + ADR-0004.

* **Faza 14: Dynamic Introspection Engine (Silnik Refleksji)** [DONE — backend; Krok 2 UI odłożony]
  Cel: Zero hardkodowania. Backend dyktuje kształt UI na podstawie wersji vectorbt.
  Krok 1 (Backend): Napisać endpoint /api/v1/registry. Używa modułu inspect w Pythonie. Zwraca wielki JSON z dostępnymi klasami, parametrami i typami. [DONE] — `GET /api/v1/registry/indicators` (surowy `dict[str, IndicatorSpec]`, bez koperty `ApiResponse` — patrz ADR-0005) + `/nodes` + `/`; kuratorowany katalog (`introspection.py`) + opcjonalne wzbogacenie żywą introspekcją vbt; kategorie i `COMPATIBILITY_MATRIX` z `GraphParser`. Pierwszy prefiks `/api/v1/` w repo.
  Krok 2 (Frontend): Przebudować Visual Builder. Zamiast statycznej palety węzłów, UI buduje menu z JSON-a z /registry. [ODŁOŻONE — paleta węzłów nadal statyczna]
  Testy: Sprawdzić, czy aktualizacja vectorbt (np. pip install vectorbt --upgrade) automatycznie dodaje nowe węzły w UI bez zmiany kodu BlockBT. [DONE dla backendu] — testy registry 3/3 + baseline `indicator_registry` 4/4 nietknięty.
  Dokumentacja: Opis struktury JSON z /registry. [DONE] — `docs/backend/registry.md` + ADR-0005.
  Respond terse like smart caveman. All technical substance stay. Only fluff die.

* **Faza xx: Konteneryzacja, docker i docker compose**
  * STATUS : [PENDING]

    

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
