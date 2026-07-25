# BlockBT — Changelog / Historia Faz

> Archiwum zakończonych faz projektu. Aktywna faza i zasady pracy agenta
> są w AGENTS.md. Ten plik NIE jest ładowany automatycznie do kontekstu
> sesji — czytaj go tylko gdy potrzebujesz historii konkretnej fazy
> (np. `graphify query` nie wystarcza, albo user pyta "dlaczego X zrobiono tak").

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
* **Phase 21: Architektura UI - Panele Boczne, Overlays i Kontrast**
  * Status: [DONE]
  * Cel: Naprawa błędów z ucinanym UI (`overflow-hidden`), niedziałającymi modalami, brakującymi danymi na wykresie equity, błędnym renderowaniem QuantStats Tearsheet oraz nieczytelnym kontrastem formularzy.
  * Wynik:
    - **Sidebary Flexbox:** `InspectorPanel` i `ChatPanel` osadzone w `MainLayout.tsx` jako Flex Children obok kanwy (eliminacja ucinania przez `overflow-hidden`).
    - **Portale i Pozycjonowanie Inline:** `SaveStrategyModal`, `StrategyListModal` oraz `ResultsOverlay` osadzone bezpośrednio w `document.body` przez `createPortal` z natywnym inline CSS (`position: fixed`, `top: 0`, `left: 0`, `right: 0`, `bottom: 0`, `zIndex: 99999/100000`). Gwarantuje to odporność na brak klas `inset-0` w Tailwind v4.
    - **Universal Equity Curve Adapter:** `ResultsOverlay.tsx` wyposażony w parser `parseEquityCurve` do obsługi tablic obiektów `[{ date, value }]`, słowników pojedynczych symboli oraz Multi-Symbol.
    - **QuantStats Tearsheet `srcDoc`:** Endpoint `/api/results/{id}/tearsheet` pobierany przez `fetch` i renderowany w `iframe` przez `srcDoc={html}` (eliminacja wyświetlania surowego JSON-a).
    - **Kontrast & Stylizacja Dropdownów:** Dodano `color-scheme: dark;` oraz regułę `select option { background-color: #131722 !important; color: #f9fafb !important; }` w `index.css` dla czytelnych opcji na ciemnym tle.
  * ZASADY DO PRZESTRZEGANIA PRZEZ AGENTA PRZY ZMIANACH NA FRONCIE:
    1. **Żadnych paneli bocznych z `fixed`:** Nowe panele boczne muszą być zawsze renderowane wewnątrz `MainLayout` jako flex children (bracia dla `flex-1`), bez pozycjonowania `fixed` (patrz DESIGN.md sekcja 7).
    2. **Portale i Inline Fixed:** Wszystkie dialogi, modale i overlaye pełnoekranowe MUSZĄ używać `createPortal(..., document.body)` ORAZ jawnego stylizowania inline CSS (`position: fixed; top: 0; left: 0; right: 0; bottom: 0; zIndex: 99999`) zamiast wyłącznego polegania na klasach pomocniczych Tailwinda (`inset-0`).
    3. **Tearsheet w `iframe`:** HTML z QuantStats pobieraj via API i wstawiaj przez `srcDoc={html}`, nigdy przez surowy URL w `src`.

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
  * AKTUALIZACJA (2026-07-17, decyzja Janka z review 2026-07-16, ADR-0007): blok
    TimeShift usunięty z kanwy — silnik bezwarunkowo auto-shiftuje entries/exits
    o 1 okres po generate_signals(); walidator nie wymaga już węzła TimeShift,
    a jawne węzły time_shift w starych DAG-ach są no-op (brak podwójnego shiftu).
    Poprawny minimalny przepływ: Data -> Indicator -> Portfolio.

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

* **Faza 15: Realny Walk-Forward Optimization** [DONE]
  Cel: Zastąpić stub `WalkForwardOptimizer.run_wfo` (pojedynczy backtest, review 2026-07-15 MED) realnym walk-forward. [DONE]
    1. **Podział okien:** `split_windows(index, window_size, step_size, mode)` — przedziały półotwarte IS `[is_start, is_end)` / OOS `[is_end, oos_end)`, `oos_start == is_end` → brak look-ahead z konstrukcji; tryby `rolling` (IS stałej długości, przesuw o step) i `anchored` (IS rośnie od startu danych); `step_size` = długość OOS i krok (segmenty OOS przylegają, bez nakładania). [DONE]
    2. **Per okno:** opcjonalna optymalizacja in-sample przez reuse `OptunaOptimizer` (`param_bounds`/`n_trials`/`metric`), potem backtest OOS na `{**parameters, **best_params}`; bez `param_bounds` — czysta ewaluacja WFO na stałych parametrach (stara ścieżka `WfoNode`). Awaria okna nie zrywa WFO (metryki 0.0 + `error`). [DONE]
    3. **Agregacja:** metryki per okno + łączne OOS — zwrot składany geometrycznie, Sharpe uśredniony, guard NaN/inf → 0.0 (`_finite_or_zero`); `best_params`/`best_value`/`trials` w wyniku = kontrakt `JobService` → kolumny `OptimizationJob`, okna w `trials_data.trials` (czyta `WfoNode`). [DONE]
    4. **API:** `WalkForwardRequest` rozszerzony ADDYTYWNIE o opcjonalne `mode` (`Literal["rolling","anchored"]`), `param_bounds`, `n_trials` (1..500), `metric`; `POST /api/optimizer/wfo` i `run_walk_forward` przekazują nowe opcje (defaulty = stary kontrakt, frontend niezłamany). [DONE]
  Testy: 15/15 (podział okien rolling/anchored + brak look-ahead, agregacja i guardy NaN/inf na FakeEngine, Optuna in-sample, E2E endpointu na danych syntetycznych z mockiem `_fetch_market_data`, walidacja 422/404). Pełna suita 165 pass / 0 fail (baseline 152, 2 stare testy stubu zastąpione). [DONE]
  Dokumentacja: `docs/backend/engines_and_optimization.md` (sekcja WFO bez wzmianek o stubie) + ADR-0006. [DONE]

* **Faza 16: Implementacja zarządzania użytkownikami** [DONE]
  Cel: Zaplanować i stworzyć logikę odpowiedzialną za zarządzanie użytkownikami.
  1. **Model & Schema:** Model `User` w ORM (`app/models/user.py`), FK `user_id` w `strategies`, `backtest_jobs`, `optimization_jobs`. [DONE]
  2. **Auth Service & JWT:** `app/services/auth.py` (bcrypt hashing, JWT token HS256 24h). [DONE]
  3. **Conditional Middleware:** `app/core/auth_middleware.py` (pomija gdy `auth_enabled=false`, weryfikuje Bearer JWT gdy `true`). [DONE]
  4. **User Scoping:** `app/core/user_scope.py` (filtrowanie SQL `user_id`, weryfikacja ról admin/user). [DONE]
  5. **API Auth & CRUD:** `app/api/auth.py` (`POST /login`, `GET /me`, `GET /users`, `POST /users`, `PUT /users/{id}`, `DELETE /users/{id}`, `GET /auth-status`). [DONE]
  6. **Frontend Auth Store & Guard:** `authStore.ts` (Zustand persist), `ProtectedRoute.tsx` (guard tras), `api.ts` (wstrzykiwanie Bearer + 401 redirect). [DONE]
  7. **Frontend UI:** `LoginPage.tsx` (ekran logowania w ciemnym motywie MD3), `SettingsPage.tsx` (zakładka User Management + switch auth_enabled + tabela CRUD z TanStack Query), `Sidebar.tsx` (awatar, nazwa użytkownika, przycisk wylogowania). [DONE]
  8. **Testy & Build:** backend 243 testy przechodzą, frontend `tsc -b && vite build` bez błędów. [DONE]

* **Faza 17: Weryfikacja i stabilizacja analizy AI z Ollama** [DONE]
  Cel: Naprawa zawieszania się aplikacji przy braku połączenia z Ollama, wstrzykiwanie ról systemowych do czatu oraz health check.
  1. **Health Check & Dynamic Config:** Endpoint `GET /api/settings/ollama/status` + dynamiczne pobieranie `ollama_base_url`/`ollama_model` z `AppSetting` z fallbackiem do env vars. [DONE]
  2. **Error Handling & Non-persistence:** Błędy połączenia/LLM w `/analyze` i `/chat` nie utrwalają tekstów `[ERROR]` w DB, zwracają HTTP 503 Service Unavailable. [DONE]
  3. **System Prompt Chat Context:** Domyślny `SystemPrompt` dodawany jako wiadomość `role: "system"` do konwersacji wieloturowych (`add_chat_message`). [DONE]
  4. **Frontend Error & Status UI:** Dedykowany widget statusu Ollama w `SettingsPage.tsx`, obsługa błędów, unwrap wyników API oraz przycisk "Retry Analysis" w `ChatPanel.tsx`. [DONE]
  5. **Testy & Dokumentacja:** 8 testów automatycznych Ollamy (253 łączna suita backendu pass), instrukcja testów manualnych w `TESTY_MANUALNE/17_ollama_ai_analysis.md`. [DONE]

* **Faza 18: Audit GUI/UX, Analiza Wideo & Stworzenie DESIGN.md** [DONE]
  Cel: Przeprowadzenie analizy nagrania wideo w modelu multimodalnym i utworzenie dokumentu wytycznych UX/UI.
  1. **Prompt & Video Audit:** Analiza wideo aplikacji zapisana w `TESTY_MANUALNE/audyt ux ui design.md`. [DONE]
  2. **System Wytycznych Designu:** Stworzenie `DESIGN.md` zawierającego tokeny stylów CSS, koncepcję Inspector Panel, Bottom Drawer dla wyników, usunięcie native prompt() oraz zasady ergonomii DAG. [DONE]

* **Faza 19: Przeprojektowanie i Refaktoryzacja Interfejsu GUI (UI/UX Transformation)** [DONE]
  Cel: Wdrożenie nowej architektury interfejsu i wytycznych z `DESIGN.md` w kodzie frontendu.
  1. **Tokeny i Arkusz Stylów (`index.css`):** Zmienne `:root` (Elevation layering, sub-borders, kolory węzłów, akcenty). [DONE]
  2. **System Powiadomień & Modale:** ToastContainer, human-readable API error formatting, SaveStrategyModal zastępujący window.prompt(). [DONE]
  3. **Inspector Panel (Side Drawer):** Edycja parametrów dowolnego węzła DAG w dedykowanym panelu bocznym. [DONE]
  4. **Kompaktowe Węzły DAG & Kanwa:** Odchudzone karty dla DataNode, IndicatorNode, SignalNode, PortfolioNode, OptimizerNode i WfoNode. [DONE]
  5. **Results Drawer (Bottom Drawer):** Rozsuwany dolny panel z pełnowymiarowymi wykresami Plotly, tearsheetem QuantStats i czatem AI Analyst. [DONE]
  6. **Weryfikacja:** `npm run build` pass (0 błędów), suita testów backendowych 254/254 pass. [DONE]

* **Faza 22: Refaktoryzacja Frontendu & Język Angielski jako Domyślny** [DONE]
  Cel: Przełączenie domyślnego języka frontendu na angielski, bez modyfikacji komentarzy deweloperskich.
  1. **Internacjonalizacja UI:** Przetłumaczenie wszystkich etykiet, nagłówków, przycisków, powiadomień toast oraz modali z języka polskiego na angielski.
  2. **Zachowanie Komentarzy:** Wszystkie komentarze deweloperskie w kodzie źródłowym pozostały w formie oryginalnej.
  3. **Aktualizacja Testów:** Dostosowanie matcherów tekstowych w testach Vitest do angielskich fraz UI.
  4. **Dokumentacja Środowiska w AGENTS.md:** Dodanie wytycznych dotyczących komend `Makefile` oraz narzędzia `uv`.

* **Faza 23: Poprawki Makefile, Czyszczenie UI oraz Motyw Ciemny Tearsheetu QuantStats** [DONE]
  Cel: Poprawa komend Makefile, usunięcie niepotrzebnych przycisków z nagłówka, ciemny motyw i anglojęzyczny szablon QuantStats Tearsheet oraz przycisk AI Analyst na kanwie.
  1. **Makefile & Linter:** Usunięcie nieaktywnych celów dockera, usunięcie 100% błędów lintera ruff w backendzie, aktualizacja `make lint` do `uv run ruff check backend/ --ignore E501 && cd frontend && npx tsc --noEmit`.
  2. **Czyszczenie UI:** Usunięcie przycisków `Load Template` i `Deploy Strategy` z nagłówka `MainLayout.tsx`.
  3. **Tearsheet w Języku Angielskim:** Zmiana `BlockBT — Tearsheet analityczny` na `BlockBT - Analytics Tearsheet` (półpauza zastąpiona przez `-`), przetłumaczenie napisów w `qsadapter.py`.
  4. **Przycisk AI Analyst:** Usunięcie emotek i umieszczenie przycisku `Chat with AI Analyst` (ikona Lucide `Bot`) bezpośrednio w panelu kanwy `WorkflowEditor.tsx` po wykonaniu backtestu.
  5. **QuantStats Tearsheet Dark Mode:** Dostosowanie stylów CSS w `qsadapter.py` oraz kontenera iframe w `ResultsOverlay.tsx` do ciemnej palety barw (`#0b0d14`, `#131722`) zgodnie z `DESIGN.md`.
  6. **Weryfikacja:** `make lint` pass (0 błędów), testy Vitest 47/47 pass, testy pytest 256/256 pass.

* **Faza 24: Refaktoryzacja Wyglądu, Ujednolicenie Układu & Zacementowanie w DESIGN.md** [DONE]
  Cel: Naprawa nachodzenia uchwytów połączeń React Flow na tekst węzłów, wyraziste obramowanie węzłów `border-2`, znormalizowanie wcięć kontenerów oraz dodanie Sekcji 8 w DESIGN.md.
  1. **React Flow Handles:** Precyzyjne pozycjonowanie uchwytów w `index.css` (`left: -8px`, `right: -8px`, `z-index: 25`, średnica 14px centered na ramce) zapobiegające nachodzeniu na tekst karty.
  2. **Pogrubione Obramowanie Węzłów:** Zastosowanie `border-2` (2px) oraz min. inner paddingu `p-3.5` we wszystkich węzłach (`DataNode`, `IndicatorNode`, `SignalNode`, `PortfolioNode`, `OptimizerNode`, `WfoNode`).
  3. **Normalizacja Spacingu:** Ujednolicenie marginesów i wcięć w nagłówkach stron (`MainLayout.tsx`, `SettingsPage.tsx`, `InspectorPanel.tsx`).
  4. **Zacementowanie w DESIGN.md:** Dodanie Sekcji 8 (**Reguły Odstępów, Obramowań Węzłów i Uchwytów Połączeń**) do `DESIGN.md`.
  5. **Weryfikacja:** `make lint` pass (0 błędów), testy Vitest 47/47 pass, `npm run build` pass.

* **Phase 25: Implementacja modułu Dashboard & Integracja Plotly**
  * Status: [IN_PROGRESS]
  * Cel: Zaprojektowanie i wdrożenie panelu Dashboard (wykresy Realtime, widget historii, modal szczegółów zadań).
  * Aktualne problemy: Faza wstrzymana z powodu wciąż występujących problemów wizualnych po stronie wykresów Plotly (ucina się, wycieka na historię) oraz z-indexów ukrywających Modal. Do poprawy czytelność UI (prześwitujące tła, kontrast okien modali). Błędy kompilacji TypeScript z powodu HMR. Do debugowania w przyszłości.

* **Faza P0-Auth: Hardening warstwy autoryzacji + migracje Alembic** [IN_PROGRESS]
  Cel: usunięcie blokerów merge'a `przydan-dev` → `main` z review pod PR #5. Plan: `docs/PLAN_P0_AUTH_ALEMBIC.md`, decyzja architektoniczna: `docs/adr/0011-loopback-jako-granica-zaufania.md`.
  1. **ZMIANA KONTRAKTU API (P0-1):** przy `auth_enabled = false` operacje uprzywilejowane (`/api/auth/users`, `PUT /api/settings/`, CRUD promptów) są dostępne **wyłącznie z loopbacku** (`127.0.0.0/8`, `::1`); z LAN-u zwracają `403`. Wcześniej `require_admin` przy braku roli nie sprawdzał niczego, co pozwalało dowolnemu klientowi założyć konto admina i włączyć auth, blokując właściciela instancji.
  2. **Anti-lockout (P0-1b):** seed pierwszego admina wydzielony do `app.services.auth.ensure_admin_user()` i wywoływany także przy włączaniu `auth_enabled` przez `PUT /api/settings/` — nie tylko w `lifespan`.
  3. **Kontrola właściciela strategii (P0-2):** `verify_resource_access` w `POST /api/backtest/`, `POST /api/backtest/dag`, `POST /api/optimizer/` i `POST /api/optimizer/wfo`. Endpoint DAG bezwarunkowo nadpisywał `strategy.parameters` cudzej strategii.
  4. **Zasoby bez właściciela (P0-3):** `user_id IS NULL` (baza sprzed Fazy 16) widzi wyłącznie admin. Zduplikowane, dziurawe kopie tej kontroli w `strategies.py` (3×) i `notes.py` (2×) zastąpione wywołaniem `verify_resource_access`.
  5. **Fail-closed (P1-1):** błąd odczytu `auth_enabled` (np. `database is locked`) zwraca `True` zamiast `False` — awaria SQLite nie wyłącza już autoryzacji.
  6. **Prompty AI tylko dla admina (P1-2):** `require_admin` w czterech endpointach `/api/settings/prompts*` (wektor prompt injection na globalny prompt systemowy).
  7. **Hasło administratora (P1-3):** `ADMIN_PASSWORD` bez wartości domyślnej (było `"blockbt"`); przy braku konfiguracji generowane przez `secrets.token_urlsafe(16)` i jednorazowo wypisywane do logu.
  8. **Logi bez treści żądań (P1-4):** `log_requests` przestał czytać i logować body — hasła z `POST /api/auth/login` trafiały plaintextem do `backend/data/logs`. Zostają metoda, ścieżka, IP, status, czas i query params.
  9. **Rate limiting logowania (P1-5):** 5 prób / 60 s na parę (IP, username) → `429` z nagłówkiem `Retry-After`. Licznik w pamięci procesu, bez nowych zależności.
  10a. **Migracje przy starcie:** `lifespan` wywołuje `init_or_migrate_db()` zamiast samego `init_db()` — wzorzec „stamp albo upgrade" (pusta baza: `create_all()` + `alembic stamp head`; istniejąca: `alembic upgrade head`). Bez stempla kolejna migracja odtwarzałaby historię na bazie, która ma już wszystko. Błąd migracji przerywa start.
  10b. **`.env.example`:** `ADMIN_PASSWORD=change_me_in_production` zakomentowane — zostawione, niweczyło P1-3, bo każda instalacja kopiująca ten plik dostawała to samo znane hasło.
  10. **Alembic (P1-6):** `script_location` naprawiony na `backend/alembic` (wskazywał na nieistniejący katalog po starej strukturze), `sqlalchemy.url` usunięty z `alembic.ini` na rzecz rozwiązywania URL w `env.py` identycznie jak w `app/db/session.py`. Migracja `0001_user_scoping` — idempotentna, tworzy `users`, dokłada kolumny `user_id` i przypisuje osierocone wiersze pierwszemu adminowi. Nowe cele: `make migrate`, `make migrate-down`.

* **Faza 26: Tryb portfelowy i realny rejestr wskaźników** [TODO]
  Cel: dwie luki wykryte przy przygotowaniu materiałów demonstracyjnych (2026-07-25) — obie dotyczą rzeczy, które w interfejsie wyglądają na dostępne, a nie są.

  1. **Tryb portfelowy multi-symbol (`group_by` + `cash_sharing`).** Obecnie multi-symbol to N niezależnych kolumn bez współdzielenia kapitału (`opensource_engine.py:797`), więc job na `AAPL, GOOG` z `init_cash: 10000` angażuje realnie 20 000 zł, a nie 10 000 podzielone na dwa. Nie istnieją zagregowane Total Return, Sharpe ani Max Drawdown — dlatego karty KPI pokazują `--` (`MainLayout.tsx:25`). **Nie wolno ich zastąpić średnimi:** Sharpe portfela zależy od korelacji składników, a Max Drawdown od tego, że obsunięcia nie zachodzą jednocześnie; średnia dałaby ładny zrzut i fałszywą tezę.
     Rozwiązanie zgodne z idiomem vectorbt (potwierdzone w dokumentacji biblioteki): `group_by` jako **parametr węzła portfela**, nie ukryta decyzja silnika. Jeden przebieg symulacji obsługuje oba poziomy odczytu — `pf.stats(group_by=True)` daje metryki portfela na wspólnej krzywej kapitału, `pf.total_profit(group_by=False)` rozbicie per instrument. Tryb badania sygnału (kolumny niezależne) zostaje domyślnym; tryb portfelowy dochodzi obok.
     Do sprawdzenia przed wyceną: zachowanie `_build_allocation_analysis` i liczników wyjść SL/TP per symbol po zgrupowaniu.
     Wartość badawcza: różnica między sumą niezależnych wyników a wynikiem portfela ze wspólnym kapitałem **jest zmierzoną dywersyfikacją** — wynik, nie deklaracja.
     Konsekwencja: wyniki multi-symbol sprzed zmiany przestaną być porównywalne z nowymi. Decyzja przed sesją zrzutów do pracy dyplomowej.
     Krok pośredni (~30 min, niezależny): karty KPI pokazują wartości per instrument z podpisami tickerów zamiast `--`.

  2. **Rejestracja wskaźników TA-Lib w `IndicatorRegistry`.** `discover_talib_indicators` (`indicator_registry.py:71`) iteruje po 158 funkcjach TA-Lib, ale ciało pętli to `pass` — do rejestru nie trafia nic. Log `Discovered 158 indicators from TA-Lib` podaje liczbę funkcji dostępnych w bibliotece, nie zarejestrowanych, i wygląda jak funkcja, której nie ma. `discover_vbt_indicators` ma analogiczną martwą pętlę i rejestruje ręcznie tylko `vbt_MA` i `vbt_RSI`.
     Skutek: grupa `Registry Indicators (Introspection)` w `InspectorPanel` ma dwie pozycje. Mechanizm generowania formularzy z metadanych (Faza 14) działa poprawnie, brakuje mu treści.
     Rozwiązanie: rejestracja przez `talib.abstract.Function(name)` — metadane (`parameters`, `info`) dają nazwy parametrów i wartości domyślne. Potrzebny adapter wywołania, bo `IndicatorRegistry.execute` woła `func(data, **kwargs)`, a abstrakcyjne funkcje TA-Lib przyjmują inny kształt wejścia. Naprawić też komunikat logu, żeby raportował liczbę faktycznie zarejestrowanych wskaźników.
