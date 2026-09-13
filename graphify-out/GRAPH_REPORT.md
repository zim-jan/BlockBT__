# Graph Report - .  (2026-09-13)

## Corpus Check
- 222 files · ~109,300 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 1904 nodes · 3659 edges · 145 communities (106 shown, 39 thin omitted)
- Extraction: 97% EXTRACTED · 3% INFERRED · 0% AMBIGUOUS · INFERRED: 125 edges (avg confidence: 0.74)
- Token cost: 233,810 input · 0 output

## Community Hubs (Navigation)
- Walidacja DAG i schematy
- Migracje Alembic i modele ORM
- Sesja bazy i testy API
- Inspektor węzłów i typy frontendu
- Sandbox AST i Numba (ADR-0002)
- Zależności npm frontendu
- Egzekucja portfela w silniku
- Walk-Forward Optimization
- API danych i workflow
- API rejestru węzłów
- API uwierzytelniania
- Protokół MCP i raporty AI
- API zadań backtestu
- Inicjalizacja i migracja bazy
- Model strategii i API alokacji
- API optymalizatora
- API ustawień i promptów
- Dashboard: notatki i podgląd zadań
- Testy broadcastingu
- Nakładka wyników edytora
- Middleware autoryzacji JWT
- Rejestr wskaźników
- Serwis wskaźników
- Konfiguracja TypeScript aplikacji
- Bazowy kontrakt silnika
- Testy okien WFO
- Testy backtestu DAG
- Testy API WFO
- API wyników i czatu AI
- Konektor Yahoo Finance
- Testy ryzyka portfela
- Konfiguracja TypeScript Node
- Skrypt smoke testów
- Konta użytkowników i hasła
- Optymalizatory i kolejka zadań (ADR-0006)
- API strategii
- Silnik OpenSource vectorbt
- Optymalizator Optuna
- Węzły optymalizacji w edytorze
- Klient Ollama
- Wiadomości czatu i testy LLM
- Custom Factory wskaźników
- Tearsheety QSAdapter
- Bazowy konektor danych
- Częstotliwości i roczne okresy
- Architektura frontendu (dokumentacja)
- Routing i nawigacja aplikacji
- API notatek
- Konektor Alpaca
- Loader silnika
- Runner zadań backtestu
- Węzły edytora i kategorie
- Grid Search
- Testy alokacji kapitału
- Widżet historii zadań
- Cache Parquet
- Testy auto-shift sygnałów
- Testy payloadu runnera
- Broadcasting multi-symbol (ADR-0001)
- ProEngine (BYOL)
- Testy wydajności broadcastingu
- Historia faz projektu
- Rejestr konektorów
- Testy parytetu egzekucji
- Testy ryzyka multi-symbol
- Usunięcie TimeShift (ADR-0007)
- Przepływ danych i BYOL
- Konektor syntetyczny
- Bezpieczeństwo sandboxa
- Ryzyko portfela SL/TP (ADR-0003)
- Wykres realtime i setup testów
- Obsługa błędów UI
- Inicjalizacja vectorbt
- Algorytmy walidacji grafu
- System projektowy UI
- Warstwa API i MCP (dokumentacja)
- Konfiguracja backendu
- Egzekucja ProEngine
- Docker Compose i hardening auth
- Introspekcja rejestru (ADR-0005)
- Powiadomienia toast
- Krawędzie edytora
- Pipeline CI
- Serwis powiadomień
- Zasady dla agentów i kontrybutorów
- Migracja user scoping
- Testy konektora syntetycznego
- Pułapki backtestingu i przepływ DAG
- Konektory danych (dokumentacja)
- Narzędzia ESLint
- Layout i karty metryk
- Dane realtime
- Testy API rejestru
- Custom Factory w kontrybucji
- Router kontekstu domenowego
- Wykres optymalizacji
- Typy react-plotly
- Skrypt uruchomienia lokalnego
- Lista wskaźników
- Logowanie loguru
- Współbieżność SQLite
- Karta metryki dashboardu
- Referencje tsconfig
- autoprefixer
- Pakiet utils
- Pakiet konektorów
- Pakiet silnika
- Pakiet MCP
- Pakiet strategii
- Pakiet testów konektorów
- Pakiet testów bazy
- Pakiet testów silnika
- Regresja zerowej ceny w WFO
- @eslint/js
- eslint-plugin-react-refresh
- Punkt montowania SPA
- globals
- jsdom
- openapi-typescript
- postcss
- tailwindcss
- @tailwindcss/postcss
- @testing-library/dom
- @testing-library/jest-dom
- @testing-library/react
- @testing-library/user-event
- @types/node
- @types/plotly.js
- @types/react
- @types/react-plotly.js
- typescript
- typescript-eslint
- vite
- @vitejs/plugin-react
- vitest
- Projekt blockbt

## God Nodes (most connected - your core abstractions)
1. `get_session()` - 91 edges
2. `OpenSourceEngine` - 90 edges
3. `useWorkflowStore` - 35 edges
4. `GraphParser` - 32 edges
5. `Strategy` - 31 edges
6. `BacktestJob` - 29 edges
7. `WalkForwardOptimizer` - 29 edges
8. `WfoConfig` - 27 edges
9. `make_node()` - 25 edges
10. `IndicatorService` - 24 edges

## Surprising Connections (you probably didn't know these)
- `Regula komentarzy: zachowaj powod, usun ceremonie procesu` --semantically_similar_to--> `CONTRIBUTING.md - przewodnik wspoltworzenia`  [INFERRED] [semantically similar]
  AGENTS.md → CONTRIBUTING.md
- `Mapowanie komponentow vectorbt na typy wezlow` --semantically_similar_to--> `Kategorie wezlow DAG (DataIngestion, Indicators, LogicOperators, Execution, Meta)`  [INFERRED] [semantically similar]
  docs/architecture/02_Analiza VectorBT i React Flow.md → README.md
- `Referencja wezlow (Data, Indicator, Signal, Portfolio, Optimizer, WFO)` --semantically_similar_to--> `Kategorie wezlow DAG (DataIngestion, Indicators, LogicOperators, Execution, Meta)`  [INFERRED] [semantically similar]
  docs/frontend/visual_builder.md → README.md
- `Sortowanie topologiczne algorytmem Kahna O(V+E)` --semantically_similar_to--> `GraphParser (Kahn, zgodnosc portow, jeden Execution)`  [INFERRED] [semantically similar]
  docs/architecture/02_Analiza VectorBT i React Flow.md → README.md
- `CI job: docs (mkdocs build --strict)` --references--> `MkDocs site - Dokumentacja Techniczna BlockBT`  [INFERRED]
  .github/workflows/ci.yml → mkdocs.yml

## Import Cycles
- None detected.

## Hyperedges (group relationships)
- **Walidacja i wykonanie DAG strategii** — readme_dag_backtest_flow, readme_graphparser, readme_node_categories, docs_architecture_02_analiza_vectorbt_i_react_flow_kahn_topological_sort, readme_lookahead_auto_shift, docs_frontend_visual_builder_execution_lifecycle [INFERRED 0.85]
- **Bezpieczenstwo kodu uzytkownika (sandbox AST)** — security_indicator_sandbox, docs_frontend_custom_indicators_ast_validator, contributing_rejected_contributions, changelog_phase11_custom_factory [INFERRED 0.85]
- **Model zaufania oparty o loopback** — readme_loopback_trust_boundary, docker_compose_docker_compose_stack, changelog_phase_p0_auth_hardening, security_security_policy [INFERRED 0.85]
- **Ochrona przed look-ahead we wszystkich sciezkach egzekucji** — docs_adr_0007_usuniecie_bloku_timeshift_auto_shift_auto_shift_in_engine, docs_adr_0007_usuniecie_bloku_timeshift_auto_shift_apply_time_shift, docs_adr_0008_parytet_egzekucji_optymalizatora_execution_parity, docs_adr_0008_parytet_egzekucji_optymalizatora_run_backtest, docs_adr_0006_walk_forward_optimization_is_oos_half_open_windows, docs_adr_0007_usuniecie_bloku_timeshift_auto_shift_look_ahead_bias [INFERRED 0.85]
- **Przeplyw autoryzacji i granicy zaufania** — docs_adr_0010_zarzadzanie_uzytkownikami_auth_jwt_authmiddleware, docs_adr_0011_loopback_jako_granica_zaufania_require_admin, docs_adr_0011_loopback_jako_granica_zaufania_is_loopback, docs_adr_0010_zarzadzanie_uzytkownikami_auth_jwt_scoped_query, docs_adr_0011_loopback_jako_granica_zaufania_verify_resource_access, docs_adr_0011_loopback_jako_granica_zaufania_ensure_admin_user [EXTRACTED 1.00]
- **Pipeline zadania backtestu (Runner)** — docs_backend_engines_and_optimization_backtestrunner, docs_backend_connectors_connectorregistry, docs_backend_engines_and_optimization_engineloader, docs_backend_engines_and_optimization_opensourceengine, docs_adr_0006_walk_forward_optimization_jobservice [EXTRACTED 1.00]

## Communities (145 total, 39 thin omitted)

### Community 0 - "Walidacja DAG i schematy"
Cohesion: 0.06
Nodes (74): GraphParser, GraphValidationError, DAGEdge, Exception, No orphan nodes. All paths must eventually reach Execution., Wymusza zasady inżynierii finansowej (Prewencja Pułapek)., Odrzuca topologie, których silnik nie wykonuje (audyt 2026-07-17).          ``ru, Runs all validations on the graph. (+66 more)

### Community 1 - "Migracje Alembic i modele ORM"
Cohesion: 0.06
Nodes (46): Środowisko Alembic dla BlockBT.  URL bazy rozwiązywany jest **dokładnie tak samo, Powiel logikę ``app.db.session._resolve_db_url`` (bez importu silnika)., Tryb offline — generuje SQL bez łączenia się z bazą., Tryb online — wykonuje migracje na żywym połączeniu., _resolve_db_url(), run_migrations_offline(), run_migrations_online(), BacktestJob (+38 more)

### Community 2 - "Sesja bazy i testy API"
Cohesion: 0.07
Nodes (43): drop_db(), get_engine(), init_db(), Return the active engine. Używaj zamiast importowania `_engine` —     testy prze, Create all Phase 2 tables (idempotent — safe to call on every startup)., Drop all Phase 2 tables., db_session(), isolate_test_db() (+35 more)

### Community 3 - "Inspektor węzłów i typy frontendu"
Cohesion: 0.09
Nodes (32): ADR-0009, PortfolioNodeProps, EXECUTION_NODE_TYPES, initialEdges, initialNodes, invalidateAfterTopologyChange(), WorkflowState, AllocationAnalysis (+24 more)

### Community 4 - "Sandbox AST i Numba (ADR-0002)"
Cohesion: 0.09
Nodes (42): ADR-0002: Custom Factory sandbox AST + Numba, Model Self-Hosted / Air-Gapped, Walidator AST allowlist (sandbox), IndicatorService.compile_custom_indicator, generate_custom (sciezka DAG custom), Numba @njit kontrakt 1D-per-kolumna, Model zagrozen: lokalny jednoosobowy Self-Hosted, _validate_code_safety (+34 more)

### Community 5 - "Zależności npm frontendu"
Cohesion: 0.05
Nodes (38): dependencies, lucide-react, plotly.js, react, react-dom, react-markdown, react-plotly.js, react-router-dom (+30 more)

### Community 6 - "Egzekucja portfela w silniku"
Cohesion: 0.10
Nodes (21): finite_or_zero(), Any, DataFrame, ndarray, Series, Run a vectorbt-powered backtest.         Supports both single-run and vectorized, Review Fazy 10: wspolny ekstraktor metryk QuantStats (deduplikacja run_backtest/, Faza 10: przygotowuje ceny zamknięcia do wektoryzacji broadcastingiem. (+13 more)

### Community 7 - "Walk-Forward Optimization"
Cohesion: 0.10
Nodes (31): Konfiguracja przebiegu Walk-Forward Optimization (Faza 15).      Jeden obiekt za, Realna Walk-Forward Optimization (Faza 15).      Dzieli szereg czasowy na sekwen, WalkForwardOptimizer, WfoConfig, Łączny Sharpe OOS w WFO annualizowany wg timeframe'u z parametrów., test_wfo_overall_sharpe_respects_timeframe(), FakeEngine, Metryki NaN/inf z silnika -> 0.0 w metrykach okna i skończone metryki łączne. (+23 more)

### Community 8 - "API danych i workflow"
Cohesion: 0.08
Nodes (20): get_workflow(), list_workflows(), ApiResponse, Return all saved workflow definitions., Return a single workflow by ID., Save a new React Flow workflow definition., save_workflow(), health_check() (+12 more)

### Community 9 - "API rejestru węzłów"
Cohesion: 0.11
Nodes (30): get_indicators(), get_nodes(), get_snapshot(), _get_vbt(), Any, Endpointy Dynamic Introspection Engine (Faza 14): ``GET /api/v1/registry/*``.  P, Leniwie pobiera singleton vbt z runnera; zwraca ``None``, gdy niedostępny., Zwraca surowy katalog wskaźników (klucze top-level = nazwy wskaźników). (+22 more)

### Community 10 - "API uwierzytelniania"
Cohesion: 0.13
Nodes (30): create_user(), delete_user(), _enforce_login_rate_limit(), get_auth_status(), get_current_user(), list_users(), login(), ApiResponse (+22 more)

### Community 11 - "Protokół MCP i raporty AI"
Cohesion: 0.12
Nodes (18): MCPContext, MCPMetrics, MCPPayload, MCPPeriod, Any, Versioned, serialisable context payload for LLM analysis.      Schema is intenti, Return a JSON-serialisable dict representation., Serialise to pretty-printed JSON string. (+10 more)

### Community 12 - "API zadań backtestu"
Cohesion: 0.13
Nodes (27): _dag_view_params(), get_backtest_status(), _job_to_schema(), list_jobs(), Any, ApiResponse, BackgroundTasks, Request (+19 more)

### Community 13 - "Inicjalizacja i migracja bazy"
Cohesion: 0.10
Nodes (26): _alembic_config(), init_or_migrate_db(), _is_fresh_database(), Config, Engine, Uruchamianie migracji Alembic przy starcie aplikacji.  Problem, który to rozwiąz, True, gdy w bazie nie ma jeszcze żadnej tabeli domenowej., Doprowadź schemat bazy do stanu zgodnego z modelami i migracjami. (+18 more)

### Community 14 - "Model strategii i API alokacji"
Cohesion: 0.10
Nodes (21): A user-defined trading strategy configuration.      Parameters are stored as a J, Strategy, _create_job(), Przepływ bloku ``allocation`` przez API (ADR-0009).  Silnik zapisuje analizę alo, test_get_job_returns_allocation(), test_get_multi_symbol_job_returns_allocation(), test_list_jobs_omits_allocation(), test_trigger_backtest_success() (+13 more)

### Community 15 - "API optymalizatora"
Cohesion: 0.14
Nodes (22): get_optimization_status(), list_optimization_jobs(), _opt_job_to_schema(), ApiResponse, BackgroundTasks, Request, Create an OptimizationJob and enqueue the Walk-Forward Optimization in the backg, Return the current status and results of an optimization job. (+14 more)

### Community 16 - "API ustawień i promptów"
Cohesion: 0.17
Nodes (25): create_system_prompt(), delete_system_prompt(), get_all_settings(), list_system_prompts(), ApiResponse, Request, Delete a system prompt (admin only)., Mark a system prompt as the default (admin only). (+17 more)

### Community 17 - "Dashboard: notatki i podgląd zadań"
Cohesion: 0.12
Nodes (19): FullJobViewModalProps, Note, NotesWidget(), NotesWidgetProps, ChatPanel(), ChatPanelProps, StrategyListModalProps, ChatMessage (+11 more)

### Community 18 - "Testy broadcastingu"
Cohesion: 0.12
Nodes (25): _dag(), _make_long_df(), DataFrame, ndarray, _random_walk(), Single-symbol DataFrame → płaskie metryki, brak 'is_multi_symbol', equity_curve, Dwa symbole z częściowo nie pokrywającymi się datami → brak crasha, oba w metryk, DAG z węzłem LogicOperators time_shift + multi-symbol → brak crasha, oba symbole (+17 more)

### Community 19 - "Nakładka wyników edytora"
Cohesion: 0.18
Nodes (16): MainLayout(), parseEquityCurve(), ResultsOverlay(), PortfolioNode(), SignalNode, SaveStrategyModal(), SaveStrategyModalProps, StrategyListModal() (+8 more)

### Community 20 - "Middleware autoryzacji JWT"
Cohesion: 0.09
Nodes (20): AuthMiddleware, Request, Conditional JWT auth. Skip entirely when auth_enabled=false., AppSetting, Key-value store for application-wide configuration.      Known keys: data_connec, decode_access_token(), Any, Decode and validate JWT. Raises jwt.InvalidTokenError on failure. (+12 more)

### Community 21 - "Rejestr wskaźników"
Cohesion: 0.14
Nodes (15): IndicatorRegistry, initialize_registry(), Any, Series, Registry for technical indicators from various libraries (vbt, TA-Lib, etc.)., Register a new indicator., Return metadata for all registered indicators., Get indicator by name. (+7 more)

### Community 22 - "Serwis wskaźników"
Cohesion: 0.20
Nodes (14): IndicatorService, Any, DataFrame, Series, Faza 11: buduje słownik dozwolonych wbudowanych funkcji dla sandboxa., Service for generating entry and exit signals (entries/exits) based on OHLCV dat, Helper to extract a parameter value, supporting lists for vectorization., Faza 10: wykrywa wektoryzację parametrów (lista/tablica okien). (+6 more)

### Community 23 - "Konfiguracja TypeScript aplikacji"
Cohesion: 0.09
Nodes (22): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, jsx, lib, module, moduleDetection, moduleResolution (+14 more)

### Community 24 - "Bazowy kontrakt silnika"
Cohesion: 0.11
Nodes (13): BacktestResult, BaseStrategyEngine, ABC, Any, DataFrame, Return metadata about this engine installation.          Must include at least `, Return True if the engine's underlying library is importable.          Default i, Validate strategy parameters.  Returns a list of error strings.          Default (+5 more)

### Community 25 - "Testy okien WFO"
Cohesion: 0.12
Nodes (20): Podziel oś czasu na okna ``(is_start, is_end, oos_start, oos_end)``.          Ko, dummy_data(), DataFrame, Testy Walk-Forward Optimization (Faza 15 + poprawki review 2026-07-16).  Obejmuj, Dane krótsze niż jedno okno IS+OOS -> brak okien., searchsorted wymaga posortowanego indeksu — jawny błąd zamiast cichych bzdur., Syntetyczne dane sinusoidalne — 730 dni, bez zer w cenie., E2E na realnym OpenSourceEngine — kontrakt odpowiedzi zachowany. (+12 more)

### Community 26 - "Testy backtestu DAG"
Cohesion: 0.14
Nodes (21): _create_strategy(), Tests for the /api/backtest/dag endpoint — Phase 9 Krok 5.  Validates that DAG p, Review Janka 2026-07-16: kapitał początkowy ustawiany wyłącznie w bloku     Port, Review Janka 2026-07-16: źródło synthetic nie działało w ogóle     (Unknown conn, DAG without Execution node → 422 Unprocessable., Helper to create a strategy and return its ID., DAG with invalid edge (DataIngestion → LogicOperators) → 422., DAG with nonexistent strategy_id → 404. (+13 more)

### Community 27 - "Testy API WFO"
Cohesion: 0.14
Nodes (20): _create_strategy(), _mock_market_data(), DataFrame, Testy E2E endpointu Walk-Forward Optimization (Faza 15).  POST /api/optimizer/wf, Review Janka 2026-07-16: UI (WfoNode) nie miał czego wyświetlić — JobService, Review 2026-07-16: payload.parameters nie nadpisuje kluczy infrastrukturalnych, Review 2026-07-16: min>max w param_bounds -> 422 na wejściu, zamiast     kryptyc, Ścisła walidacja Pydantic: nieznany tryb -> 422. (+12 more)

### Community 28 - "API wyników i czatu AI"
Cohesion: 0.19
Nodes (19): add_chat_message(), analyze_simulation_result(), get_chat_history(), get_simulation_result(), get_tearsheet(), Any, ApiResponse, Request (+11 more)

### Community 29 - "Konektor Yahoo Finance"
Cohesion: 0.17
Nodes (12): DataFrame, Map generic BlockBT timeframe strings to yfinance ``interval`` codes., Market data connector backed by Yahoo Finance via yfinance.      Characteristics, Check if start date exceeds Yahoo Finance intraday lookback limits., YahooFinanceConnector, _make_ohlcv(), DataFrame, Tests mock at the _download boundary — the lowest-level method that     calls vb (+4 more)

### Community 30 - "Testy ryzyka portfela"
Cohesion: 0.13
Nodes (20): _dag(), Faza 12: dodatkowe testy zarządzania ryzykiem i sizingu portfela., Review 2026-07-15: wyjście sygnałowe w pasie eps NAD poziomem SL nie jest liczon, Głębokie przebicie poziomu SL (gap 100→90) liczy się jako stop nawet przy     ko, Review 2026-07-16: realne trafienie stopu przy STREFOWEJ masce exits.      Close, Trailing stop (sl_trail=True) — ścieżka wykonuje się i zwraca wynik., H2: trailing SL liczony względem biegnącego szczytu, nie ceny wejścia.      Ruch, Sizing: większy size => inna (wyższa na rosnącej serii) wartość końcowa. (+12 more)

### Community 31 - "Konfiguracja TypeScript Node"
Cohesion: 0.10
Nodes (20): compilerOptions, allowImportingTsExtensions, erasableSyntaxOnly, lib, module, moduleDetection, moduleResolution, noEmit (+12 more)

### Community 32 - "Skrypt smoke testów"
Cohesion: 0.24
Nodes (16): check_health(), check_jobs(), check_notes(), check_realtime(), check_tearsheet(), http(), main(), Any (+8 more)

### Community 33 - "Konta użytkowników i hasła"
Cohesion: 0.16
Nodes (14): BlockBT user account., User, ensure_admin_user(), hash_password(), Session, Hash password with bcrypt., Zaseeduj pierwsze konto admina, jeśli w bazie nie ma żadnego użytkownika.      W, Verify admin can disable auth_enabled via PUT /api/settings/ and unauthenticated (+6 more)

### Community 34 - "Optymalizatory i kolejka zadań (ADR-0006)"
Cohesion: 0.22
Nodes (20): ADR-0006: Walk-Forward Optimization, GridSearchOptimizer, Okna IS/OOS polotwarte (rolling/anchored), JobService, OptimizationJob, OptunaOptimizer, WalkForwardOptimizer.run_wfo, WalkForwardOptimizer.split_windows (+12 more)

### Community 35 - "API strategii"
Cohesion: 0.22
Nodes (17): create_strategy(), delete_strategy(), get_strategy(), list_strategies(), ApiResponse, Request, Remove a strategy record from SQLite., Return all strategy records from SQLite (scoped to user when auth is enabled). (+9 more)

### Community 36 - "Silnik OpenSource vectorbt"
Cohesion: 0.13
Nodes (10): OpenSourceEngine, Backtest engine using the public open-source ``vectorbt`` library.      Supports, Check if vectorbt can be imported (legacy, kept for compatibility)., Return metadata about this engine installation., Faza 10: poziom kolumnowego MultiIndex z polem 'close' (case-insensitive)., Liczniki tylko dla stopów faktycznie ustawionych — wspólna reguła obu         śc, Weryfikuje, czy przy braku zainstalowanej paczki vectorbt silnik poprawnie ładuj, TestOpenSourceEngine (+2 more)

### Community 37 - "Optymalizator Optuna"
Cohesion: 0.16
Nodes (12): OptunaOptimizer, Any, DataFrame, Uses Optuna (TPE) to find optimal parameters efficiently., Run Bayesian optimization.          param_bounds: dict mapping param_name -> {mi, Zwroty procentowe z krzywej kapitału silnika (lista ``{"date", "value"}``)., Przetwórz jedno okno WFO: optymalizacja IS (opcjonalna) + backtest OOS., Sharpe (rf=0) ze sklejonych zwrotów OOS; ``None`` gdy nieobliczalny.          Do (+4 more)

### Community 38 - "Węzły optymalizacji w edytorze"
Cohesion: 0.13
Nodes (8): OptimizerNode, baseData, baseData, completedResults, mockRunWfo, WfoNode, mockStatus, useWorkflowOptimization()

### Community 39 - "Klient Ollama"
Cohesion: 0.13
Nodes (11): get_ollama_status(), Any, Check Ollama connection health and model availability., OllamaClient, Any, Send *prompt* to Ollama and return the generated text., Wysyła historię czatu do punktu końcowego /api/chat serwera Ollama., Return detailed status dict for Ollama server connection and configured model. (+3 more)

### Community 40 - "Wiadomości czatu i testy LLM"
Cohesion: 0.17
Nodes (16): ChatMessage, Model reprezentujący pojedynczą wiadomość czatu dla zadania backtestu.      Służ, _assert_session_released(), _checked_out(), _create_job(), Sesja DB × wywołania LLM (audyt 2026-07-17, P1).  Endpointy ``/analyze`` i ``/ch, Błąd LLM w analyze -> 503 i brak zapisu w bazie danych., Weryfikacja wstrzykiwania roli 'system' oraz zwrotu 503 przy błędzie Ollama. (+8 more)

### Community 41 - "Custom Factory wskaźników"
Cohesion: 0.15
Nodes (15): Faza 11 (Filary 2 i 3): kompiluje wskaźnik zdefiniowany przez użytkownika., ndarray, Faza 11 — dowód działania Custom Factory + numba JIT (Filary 2 i 3).  Testy uzup, Regresja #8: dawniej brano ostatnią funkcję (`funcs[-1]`) → zły rdzeń., #1: rdzeń wołający funkcję pomocniczą liczy poprawnie (brak NameError)., Referencyjna implementacja w czystym Pythonie (bez JIT) do porównań., Fabryka nie tylko się buduje — `.run()` liczy poprawny wynik na numpy., Filar 3 („Prędkość C"): rdzeń @njit po rozgrzewce jest istotnie szybszy niż (+7 more)

### Community 42 - "Tearsheety QSAdapter"
Cohesion: 0.16
Nodes (13): Any, datetime, QSAdapterService, QSAdapter — Faza 13: generowanie tearsheetów analitycznych (Analytics/Tearsheets, Serwis budujący tearsheety HTML z metryk portfela (QuantStats-friendly)., Normalizuje wynik ``pf.stats()`` do płaskiego słownika ``{nazwa: wartość}``., Formatuje wartość metryki do czytelnej postaci tekstowej (bezpiecznej dla HTML)., Buduje samodzielny raport HTML (tearsheet) z metryk ``pf.stats()``.          Arg (+5 more)

### Community 43 - "Bazowy konektor danych"
Cohesion: 0.18
Nodes (9): BaseDataConnector, DataFrame, Path, Fetch raw data from the upstream source.          Must return a DataFrame with a, Return connector health / authorization status for diagnostics., Standardise column names and index type., Return True if the cached file is fresh enough to use., Abstract data provider plugin.      Subclasses override ``_download()`` to fetch (+1 more)

### Community 44 - "Częstotliwości i roczne okresy"
Cohesion: 0.16
Nodes (14): freq_for_timeframe(), periods_per_year_for_timeframe(), OpenSourceEngine — BackBT engine backed by the public vectorbt library.  The ven, Pandas ``freq`` dla vectorbt odpowiadający timeframe'owi danych., Liczba okresów w roku do annualizacji (Sharpe) dla danego timeframe'u., _EquityCurveEngine, DataFrame, Annualizacja wg timeframe (audyt 2026-07-17, P2).  Silnik przekazywał zawsze ``f (+6 more)

### Community 45 - "Architektura frontendu (dokumentacja)"
Cohesion: 0.14
Nodes (17): Faza 15: Realny Walk-Forward Optimization (ADR-0006), Kanwa React Flow - kolory kategorii wezlow i uchwyty, services/api.ts (typowany klient OpenAPI), Frontend - Architecture & State, TanStack Query (server state, staleTime 30 s), useWorkflowExecution (orkiestrator zadan), workflowStore.ts (Zustand), Kontrakt Custom Code: zmienne entries i exits (+9 more)

### Community 46 - "Routing i nawigacja aplikacji"
Cohesion: 0.20
Nodes (7): Sidebar(), ProtectedRoute(), LoginPage(), SettingsPage(), AuthState, useAuthStore, UserInfo

### Community 47 - "API notatek"
Cohesion: 0.26
Nodes (14): create_note(), delete_note(), get_notes_for_strategy(), ApiResponse, Request, Return all notes for a specific strategy, ordered by pinned first, then by creat, Create a new note attached to a strategy., Update content or pin status of a note. (+6 more)

### Community 48 - "Konektor Alpaca"
Cohesion: 0.15
Nodes (10): AlpacaConnector, AuthenticationError, Any, DataFrame, Exception, Path, Verify credentials are configured (does not make a live API call)., Map BlockBT timeframe strings to Alpaca SDK TimeFrame objects. (+2 more)

### Community 49 - "Loader silnika"
Cohesion: 0.18
Nodes (7): EngineLoader, Singleton-style factory for the active BlockBT engine., Return the appropriate engine, caching the result.          Parameters         -, Return info dict from the currently loaded engine., Tests the integration between the runner and the engines., TestBacktestRunnerIntegration, TestEngineLoader

### Community 50 - "Runner zadań backtestu"
Cohesion: 0.24
Nodes (15): _execute_backtest(), _execute_dag_backtest(), _fetch_market_data(), Any, run_vectorbt_backtest — Phase 3 background task entry-point.  This is the main o, Background worker for executing an Optuna optimization study., Background worker for executing Walk-Forward Optimization.      Faza 15: realny, Faza 10: pojedyncza metryka → typ JSON-safe (skalar/np/pd → python; NaN/inf → No (+7 more)

### Community 51 - "Węzły edytora i kategorie"
Cohesion: 0.17
Nodes (9): CATEGORY_STYLES, CategoryBadge(), Props, DataNode, baseData, setSelectedNodeId, updateNodeData, IndicatorNode (+1 more)

### Community 52 - "Grid Search"
Cohesion: 0.17
Nodes (10): GridSearchOptimizer, Phase 5 — Grid Search Optimizer for parameters.  Allows exhaustive Cartesian-pro, Helper to extract the parameters from the best performing result.          Param, Explores exhaustive combinations of strategy parameters to find optimal variable, Initialize the optimizer with a compatible BaseStrategyEngine instance., indicator_layer(), Test that GridSearchOptimizer correctly evaluates a grid of parameters     and r, Test that an empty param grid is handled gracefully. (+2 more)

### Community 53 - "Testy alokacji kapitału"
Cohesion: 0.26
Nodes (14): _dag(), engine(), _long_df(), DataFrame, ndarray, _random_walk(), Analiza alokacji kapitału po backteście (ADR-0009).  Silnik dokłada do wyniku ``, Sanity: SMA crossover na random-walku wchodzi w rynek — ekspozycja > 0. (+6 more)

### Community 54 - "Widżet historii zadań"
Cohesion: 0.17
Nodes (11): FullJobViewModal(), formatSymbol(), HistoryWidget(), HistoryWidgetProps, jobReturns(), ChartConfig, DEFAULT_CONFIG, Indicator (+3 more)

### Community 55 - "Cache Parquet"
Cohesion: 0.21
Nodes (11): list_cached_symbols(), load_parquet(), purge_cache(), DataFrame, Path, Write a DataFrame to Parquet, creating parent directories as needed.      Parame, Read a Parquet file into a DataFrame.      Parameters     ----------     path: F, Return a list of symbols that have at least one cached Parquet file. (+3 more)

### Community 56 - "Testy auto-shift sygnałów"
Cohesion: 0.25
Nodes (13): _close_df(), _dag(), DataFrame, Auto-shift sygnałów w silniku DAG (review Janka 2026-07-16).  Blok TimeShift zni, Deterministyczny random-walk — niestały, więc crossovery generują trade'y., Oczekiwany Total Return [%] dla sygnałów przesuniętych ręcznie o ``periods``., DAG Data→Indicators→Execution (bez węzła shiftu) musi być shiftowany o 1., Stary DAG z jawnym timeShiftNode — wynik identyczny jak bez węzła (1× shift). (+5 more)

### Community 57 - "Testy payloadu runnera"
Cohesion: 0.22
Nodes (11): FakeDagEngine, _mock_fetch(), DataFrame, Review 2026-07-16: payload jobu z ``_execute_dag_backtest`` musi zawierać ``raw`, Atrapa silnika DAG — zwraca kontrakt run_dag_backtest z licznikami w raw., Single-symbol: raw (w tym liczniki SL/TP) trafia do payloadu jobu., Multi-symbol: zagnieżdżone raw per ticker zachowuje strukturę (serializacja, ADR-0009: blok allocation z wyniku silnika trafia do payloadu jobu. (+3 more)

### Community 58 - "Broadcasting multi-symbol (ADR-0001)"
Cohesion: 0.26
Nodes (14): ADR-0001: Broadcasting multi-symbol, IndicatorService._align_to_symbols, Kontrakt wyniku is_multi_symbol, Pivot LONG->WIDE + broadcasting po kolumnach, Guard NaN/inf -> 0.0, OpenSourceEngine._prepare_close, OpenSourceEngine.run_dag_backtest, ADR-0009: Analiza alokacji kapitalu (+6 more)

### Community 59 - "ProEngine (BYOL)"
Cohesion: 0.21
Nodes (5): ProEngine, Engine that wraps vectorbtpro via BYOL dynamic import.      When the user has NO, Attempt to import vectorbtpro.  Sets ``_mock_mode`` on failure., ProEngine MUSI działać nawet bez zainstalowanego vbtpro (tryb mock)., TestProEngineMock

### Community 60 - "Testy wydajności broadcastingu"
Cohesion: 0.22
Nodes (12): _dag(), _make_long_df(), DataFrame, ndarray, _random_walk(), Faza 10: testy wydajności/wektoryzacji broadcastingu multi-symbol.  Weryfikują,, Deterministyczny random-walk cen zamknięcia., Ramka LONG: wierszowy MultiIndex [symbol, date], kolumna 'close'. (+4 more)

### Community 61 - "Historia faz projektu"
Cohesion: 0.17
Nodes (13): Faza 10: Broadcasting multi-symbol (ADR-0001), Faza 13: QSAdapter tearsheets (ADR-0004), Faza 14: Dynamic Introspection Registry (ADR-0005), Faza 16: Zarzadzanie uzytkownikami JWT, Faza 26: Tryb portfelowy (group_by, cash_sharing) i realny rejestr TA-Lib, Faza 9.2: Poprawki EasyConnect (martwy arkusz CSS, floating edges), Faza 9: Kategoryzacja wezlow i walidacja DAG (GraphParser, COMPATIBILITY_MATRIX), CHANGELOG - historia faz projektu (+5 more)

### Community 62 - "Rejestr konektorów"
Cohesion: 0.23
Nodes (7): ConnectorRegistry, Central registry for all registered data connectors.      Connectors are registe, Register a connector class under the given key., Instantiate and return a connector by key.          Falls back to the default co, Return list of registered connector keys., Register built-in connectors if they haven't been yet., test_registered_in_registry()

### Community 63 - "Testy parytetu egzekucji"
Cohesion: 0.18
Nodes (11): _dag(), DataFrame, Parytet egzekucji legacy vs DAG (audyt 2026-07-17, P1).  Grid Search, Optuna i W, Gałąź wektoryzowana (Grid Search) — wynik kombinacji == wynik pojedynczy.      P, Deterministyczny random-walk (seed) — SMA crossover generuje transakcje., Ta sama strategia, te same dane, te same koszty → identyczny wynik obu ścieżek., Wyższy slippage MUSI pogarszać wynik — parametr nie może być ignorowany., test_run_backtest_applies_slippage() (+3 more)

### Community 64 - "Testy ryzyka multi-symbol"
Cohesion: 0.26
Nodes (11): _dag(), _long_df(), DataFrame, Review-backlog 2026-07-15: multi-symbol surfacing liczników wyjść SL/TP.  Cięcie, Ramka LONG (wierszowy MultiIndex [symbol, date]) — format wejścia Fazy 10., AAPL łamie SL (100→90), MSFT łamie TP (100→112) — liczniki rozdzielone per symbo, Bez sl_stop/tp_stop gałąź multi nie dokłada liczników (spójnie z single-symbol)., Tylko sl_stop ustawiony → w raw per symbol jest wyłącznie licznik SL. (+3 more)

### Community 65 - "Usunięcie TimeShift (ADR-0007)"
Cohesion: 0.24
Nodes (12): ADR-0007: Usuniecie bloku TimeShift, apply_time_shift, Automatyczny shift sygnalow w silniku, LogicOperatorsParams, Look-ahead Bias, TimeShiftNode (usuniety), ADR-0008: Parytet egzekucji optymalizatora, Parytet egzekucji run_backtest z DAG (+4 more)

### Community 66 - "Przepływ danych i BYOL"
Cohesion: 0.26
Nodes (12): BYOL (Bring Your Own License) - lazy loading + adapter, Przeplyw danych (definicja -> zadanie -> dane -> egzekucja -> persystencja -> AI), EngineLoader, OllamaClient + ReportBuilder (analiza AI), OpenSourceEngine, Parquet Cache, Architektura systemu (4 warstwy), Strona glowna dokumentacji BlockBT (+4 more)

### Community 67 - "Konektor syntetyczny"
Cohesion: 0.20
Nodes (5): DataFrame, Deterministyczny random-walk OHLCV — bez sieci, bez uwierzytelniania., SyntheticConnector, connector(), Sanityzacja ścieżek cache Parquet (audyt 2026-07-17, P2 — path traversal).  ``st

### Community 68 - "Bezpieczeństwo sandboxa"
Cohesion: 0.20
Nodes (9): Faza 11 (bezpieczeństwo eval/exec): statyczna analiza AST kodu użytkownika., Faza 11 — testy bezpieczeństwa sandboxa AST (`IndicatorService._validate_code_sa, Każdy złośliwy fragment podnosi ValueError('Unsafe code detected')., Legalne wskaźniki przechodzą walidację (zwracany jest ast.Module)., Regresja: benign pętla numpy nadal buduje fabrykę (nie przeblokowaliśmy)., test_benign_code_allowed(), test_benign_indicator_still_compiles(), test_malicious_code_blocked() (+1 more)

### Community 69 - "Ryzyko portfela SL/TP (ADR-0003)"
Cohesion: 0.44
Nodes (11): ADR-0003: Advanced Portfolio i Risk Management, _count_stop_exits / _classify_stop_exits, _count_stop_exits_multi, OpenSourceEngine.execute_dag_portfolio, ExecutionParams (schema DAG), vbt.Portfolio.from_signals z sl_stop/tp_stop/sl_trail, GraphParser (Kahn + COMPATIBILITY_MATRIX), Wymog wezla Indicators (GraphValidationError) (+3 more)

### Community 70 - "Wykres realtime i setup testów"
Cohesion: 0.22
Nodes (4): RealtimeChartWidget(), DOMMatrixReadOnly, makeResizeObserverEntry(), ResizeObserver

### Community 71 - "Obsługa błędów UI"
Cohesion: 0.22
Nodes (4): ErrorBoundary, Props, State, queryClient

### Community 72 - "Inicjalizacja vectorbt"
Cohesion: 0.20
Nodes (6): Initialize the OpenSource engine, verifying dependencies are present., Import vectorbt and configure the engine., _setup_vbt(), vbt(), test_indicator_service_sma_fallback(), test_opensource_engine_run_backtest()

### Community 73 - "Algorytmy walidacji grafu"
Cohesion: 0.31
Nodes (10): Faza 12: Advanced Portfolio i Risk Management SL/TP (ADR-0003), Walidacja cykli DFS w isValidConnection (getOutgoers), vbt.IndicatorFactory (input_names, param_names, output_names), Sortowanie topologiczne algorytmem Kahna O(V+E), Numba JIT nopython (LLVM), vbt.Portfolio.from_signals, vectorbt Records (structured arrays), Mapowanie komponentow vectorbt na typy wezlow (+2 more)

### Community 74 - "System projektowy UI"
Cohesion: 0.31
Nodes (10): Faza 21: Panele boczne, overlays, tearsheet srcDoc, Dashboard: Plotly z jawnymi wymiarami przez ResizeObserver, Martwe klasy CSS (prose, modal-overlay, strategy-item), DESIGN.md - system projektowy v2.0, Dwa rownolegle systemy tokenow (Material 3 dark vs legacy :root), Architektura layoutu MainLayout (panele boczne jako flex siblings), Paleta Material 3 dark (tailwind.config.js), Nakladki pelnoekranowe przez createPortal(document.body) (+2 more)

### Community 75 - "Warstwa API i MCP (dokumentacja)"
Cohesion: 0.29
Nodes (10): Model BYOL (tylko darmowy vectorbt), Backend API Layer i MCP, ApiResponse (koperta success/data/error), get_domain_context, Wzorzec Job Queue (BackgroundTasks), Serwery MCP (Architectural Router, Code Knowledge Base), OllamaClient, read_safe_file (+2 more)

### Community 76 - "Konfiguracja backendu"
Cohesion: 0.22
Nodes (6): Path, Create runtime directories if they don't exist., Central configuration object. Override any value via environment variable., Return the resolved vectorbtpro path, checking the well-known sibling dir., Settings, BaseSettings

### Community 77 - "Egzekucja ProEngine"
Cohesion: 0.39
Nodes (4): Any, DataFrame, Delegate backtest to the real vectorbtpro API.          This method intentionall, Return a clearly-labelled stub result when vbtpro is absent.          Mock value

### Community 78 - "Docker Compose i hardening auth"
Cohesion: 0.28
Nodes (9): Faza P0-Auth: hardening autoryzacji + migracje Alembic (ADR-0011), Serwis blockbt-api (FastAPI, healthcheck /api/health), Serwis blockbt-frontend (Vite dev server), Docker Compose: blockbt-api + blockbt-frontend, Vite Proxy /api -> 127.0.0.1:8000, Loopback jako granica zaufania (ADR-0011), Zglaszanie podatnosci przez GitHub Private Vulnerability Reporting, SECRET_KEY (szyfrowanie Fernet, brak wartosci domyslnej) (+1 more)

### Community 79 - "Introspekcja rejestru (ADR-0005)"
Cohesion: 0.47
Nodes (9): ADR-0005: Dynamic Introspection Registry, build_indicator_catalog, build_node_catalog, GraphParser.COMPATIBILITY_MATRIX, Kuratorowany deterministyczny katalog wskaznikow, IndicatorRegistry, GET /api/v1/registry (surowe odpowiedzi), Rejestr introspekcji (Faza 14) (+1 more)

### Community 80 - "Powiadomienia toast"
Cohesion: 0.31
Nodes (6): ToastContainer(), showToast, ToastMessage, ToastState, ToastType, useToastStore

### Community 81 - "Krawędzie edytora"
Cohesion: 0.44
Nodes (6): FloatingConnectionLine(), FloatingEdge(), getEdgeParams(), getHandleCoordsByPosition(), getNodeCenter(), getParams()

### Community 82 - "Pipeline CI"
Cohesion: 0.25
Nodes (8): CI job: backend (ruff + pytest, TA-Lib build), CI Workflow (backend, frontend, docs), CSS bundle size assertion (>= 60 kB), CI job: docs (mkdocs build --strict), CI job: frontend (tsc, vitest, build), Zasady na kazde zadanie (jeden temat na PR, zakaz nowych zaleznosci), Kontrakt builda Tailwind v4 (@import tailwindcss + @config), TA-Lib (biblioteka C)

### Community 83 - "Serwis powiadomień"
Cohesion: 0.29
Nodes (5): NotificationService, Any, Send a notification to the user., Specific helper for job completion., Handles notifications for long-running tasks like optimization or WFO.     Suppo

### Community 84 - "Zasady dla agentów i kontrybutorów"
Cohesion: 0.38
Nodes (7): AGENTS.md - instrukcje dla agentow, Regula komentarzy: zachowaj powod, usun ceremonie procesu, Graf wiedzy graphify-out, Polityka jezykowa (docs PL, kod/UI EN), Decyzje architektoniczne trafiaja do ADR, CONTRIBUTING.md - przewodnik wspoltworzenia, Conventional Commits z opisem po polsku

### Community 85 - "Migracja user scoping"
Cohesion: 0.67
Nodes (6): downgrade(), _has_column(), _has_index(), _has_table(), upgrade(), Inspector

### Community 86 - "Testy konektora syntetycznego"
Cohesion: 0.48
Nodes (6): _connector(), Testy SyntheticConnector (review Janka 2026-07-16).  Źródło 'synthetic' nie istn, test_deterministic_same_call(), test_different_symbols_differ(), test_multi_symbol_long_format(), test_single_symbol_ohlcv()

### Community 87 - "Pułapki backtestingu i przepływ DAG"
Cohesion: 0.38
Nodes (7): Faza 9.3: Stabilizacja DAG i usuniecie bloku TimeShift (ADR-0007), Pulapki backtestingu (look-ahead, survivorship, overfitting, koszty, typowanie Numba), Przeplyw DAG: POST /api/backtest/dag, GraphParser (Kahn, zgodnosc portow, jeden Execution), Auto-shift sygnalow (fshift) przeciw look-ahead bias - ADR-0007, Kategorie wezlow DAG (DataIngestion, Indicators, LogicOperators, Execution, Meta), README - BlockBT

### Community 88 - "Konektory danych (dokumentacja)"
Cohesion: 0.57
Nodes (7): Backend Data Connectors, Alpaca connector, BaseDataConnector, Cache-Aside z cache Parquet (TTL), ConnectorRegistry, BaseDataConnector._normalise (OHLCV), Yahoo Finance connector

### Community 89 - "Narzędzia ESLint"
Cohesion: 0.29
Nodes (7): eslint, eslint-plugin-react-hooks, devDependencies, eslint, eslint-plugin-react-hooks, @types/react-dom, @types/react-dom

### Community 90 - "Layout i karty metryk"
Cohesion: 0.33
Nodes (5): InspectorPanel(), HealthResponse, MainLayoutProps, MetricCard(), MetricCardProps

### Community 91 - "Dane realtime"
Cohesion: 0.40
Nodes (6): get_realtime_data(), _json_safe(), Any, ApiResponse, Zamienia wartości niereprezentowalne w JSON (NaN, ±inf) na ``None``.      Wskaźn, Pobiera świeczki intraday za pomocą yfinance do celów demonstracyjnych na Dashbo

### Community 92 - "Testy API rejestru"
Cohesion: 0.33
Nodes (4): GET /api/v1/registry/nodes zwraca niepusty katalog kategorii węzłów DAG., GET /api/v1/registry/ zwraca pełny zrzut: wskaźniki + kategorie + macierz kompat, test_get_registry_nodes(), test_get_registry_snapshot()

### Community 93 - "Custom Factory w kontrybucji"
Cohesion: 0.47
Nodes (6): Faza 11: Custom Factory, sandbox AST i Numba JIT (ADR-0002), Czego nie przyjmiemy (vectorbtpro, luzowanie walidatora AST, nowe zaleznosci), ADR-0002 Custom Factory + sandbox + Numba, Walidator AST deny-by-default, Pisanie wlasnych wskaznikow (Custom Code), Piaskownica wskaznikow (walidator AST)

### Community 94 - "Router kontekstu domenowego"
Cohesion: 0.40
Nodes (4): get_domain_context(), Reads the content of a file safely.     Strictly blocks any access to paths cont, Returns architectural guidelines and constraints for a specific BlockBT domain., read_safe_file()

### Community 96 - "Typy react-plotly"
Cohesion: 0.50
Nodes (3): Plot, PlotParams, react-plotly.js

### Community 98 - "Lista wskaźników"
Cohesion: 0.67
Nodes (3): list_indicators(), ApiResponse, Return all technical indicators available in the registry.

## Ambiguous Edges - Review These
- `AGENTS.md - instrukcje dla agentow` → `MCP Integration (Model Context Protocol)`  [AMBIGUOUS]
  AGENTS.md · relation: conceptually_related_to
- `Przeplyw DAG: POST /api/backtest/dag` → `Przeplyw danych (definicja -> zadanie -> dane -> egzekucja -> persystencja -> AI)`  [AMBIGUOUS]
  docs/architecture/overview.md · relation: conceptually_related_to
- `Stos technologiczny (React 19, FastAPI, vectorbt, Optuna, QuantStats)` → `Frontend - Architecture & State`  [AMBIGUOUS]
  docs/frontend/architecture.md · relation: conceptually_related_to

## Knowledge Gaps
- **157 isolated node(s):** `name`, `private`, `version`, `type`, `dev` (+152 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **39 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **What is the exact relationship between `AGENTS.md - instrukcje dla agentow` and `MCP Integration (Model Context Protocol)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Przeplyw DAG: POST /api/backtest/dag` and `Przeplyw danych (definicja -> zadanie -> dane -> egzekucja -> persystencja -> AI)`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **What is the exact relationship between `Stos technologiczny (React 19, FastAPI, vectorbt, Optuna, QuantStats)` and `Frontend - Architecture & State`?**
  _Edge tagged AMBIGUOUS (relation: conceptually_related_to) - confidence is low._
- **Why does `OpenSourceEngine` connect `Silnik OpenSource vectorbt` to `Walidacja DAG i schematy`, `Egzekucja portfela w silniku`, `Walk-Forward Optimization`, `Testy broadcastingu`, `Serwis wskaźników`, `Bazowy kontrakt silnika`, `Testy okien WFO`, `Testy ryzyka portfela`, `Częstotliwości i roczne okresy`, `Loader silnika`, `Grid Search`, `Testy alokacji kapitału`, `Testy auto-shift sygnałów`, `ProEngine (BYOL)`, `Testy wydajności broadcastingu`, `Testy parytetu egzekucji`, `Testy ryzyka multi-symbol`, `Inicjalizacja vectorbt`, `Regresja zerowej ceny w WFO`?**
  _High betweenness centrality (0.112) - this node is a cross-community bridge._
- **Why does `get_session()` connect `API ustawień i promptów` to `Konta użytkowników i hasła`, `Sesja bazy i testy API`, `API strategii`, `Klient Ollama`, `API danych i workflow`, `Wiadomości czatu i testy LLM`, `API uwierzytelniania`, `API zadań backtestu`, `Model strategii i API alokacji`, `API optymalizatora`, `API notatek`, `Runner zadań backtestu`, `Middleware autoryzacji JWT`, `Testy backtestu DAG`, `Testy API WFO`, `API wyników i czatu AI`?**
  _High betweenness centrality (0.107) - this node is a cross-community bridge._
- **Why does `GraphValidationError` connect `Walidacja DAG i schematy` to `Silnik OpenSource vectorbt`, `Egzekucja portfela w silniku`, `API zadań backtestu`, `Częstotliwości i roczne okresy`, `Testy ryzyka portfela`?**
  _High betweenness centrality (0.062) - this node is a cross-community bridge._
- **Are the 9 inferred relationships involving `OpenSourceEngine` (e.g. with `EngineLoader` and `GraphValidationError`) actually correct?**
  _`OpenSourceEngine` has 9 INFERRED edges - model-reasoned connections that need verification._