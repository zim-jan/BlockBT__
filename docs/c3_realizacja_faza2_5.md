# Realizacja Projektu: Rozbudowa Interfejsu, Integracja AI oraz Moduły Optymalizacyjne (Sekcja C3)

## Cel Etapów 2–5

Zasadniczym krokiem po implementacji warstwy dostępu do danych cyfrowych oraz abstrakcyjnego silnika wykonawczego, była budowa otwartego ekosystemu GUI i integracja kluczowych podzespołów badawczych dla środowiska Data Science i Quant Trading. Fazy projektowe podzielono na cztery zintegrowane gałęzie:

1. **Graficzny Interfejs Użytkownika (React)** — realizacja wzorca Single Page App.
2. **Monitorowanie Stanu i Architektury (Diagnostyka)** — widoki pozwalające na audyt środowiska BYOL w czasie rzeczywistym.
3. **Sztuczna Inteligencja (Ollama / MCP)** — adaptacja wzorca Model Context Protocol do delegowania analiz inwestycyjnych pod zewnętrzny model LLM.
4. **Podstawowy Backtesting** — optymalizacja parametrów strategii oraz wpieranie logiki decyzyjnej za pomocą natywnych wskaźników (np. SMA Crossover).

---

## 2.1 Architektura Interfejsu (React)

Aplikację oparto o framework **React**, stosując scentralizowany punkt wejścia i system nawigacji bocznej. Stan w kreatorze strategii przechowywany jest asynchronicznie po stronie klienta.

1. **Wizard (`1_Wizard.py`)**: Trzykrokowy formularz do konfiguracji założeń (dostawca, instrument, okno czasowe, kapitał początkowy i opis tekstowy). Jego wynikiem jest stan wstrzykiwany jako obiekt JSON (`wizard_state`) do encji ormowanej `StrategyTemplate`.
2. **Dashboard (`2_Dashboard.py`)**: Panel egzekucji zdefiniowanych szablonów. Wywołuje abstrakcję z warstwy pierwszej (`ConnectorRegistry` i `EngineLoader`), wizualizując stopy zwrotu oraz nakładając interaktywną krzywą kapitału na dedykowanym komponencie Plotly. Wyliczone skalary są transponowane na nowy rekord `SimulationResult`.

---

## 2.2 System Diagnostyczny z Weryfikacją BYOL

Istotną innowacją w inżynierskim podejściu do cyklu uruchomieniowego, jest **Eksplorator Stanu (`3_System_Status.py`)**. Ze względu na odcięte repozytorium VectorBT PRO ("Air-Gapped Logic"), zaszła potrzeba ciągłego inspekcjonowania wybranego trybu:

- Interfejs weryfikuje bez importowania modułów zastrzeżonych, rzutując tzw. *lazy evaluation*, czy ścieżka do wstrzykniętych pakietów PRO istnieje. Jeśli nie — awaryjnie przekierowuje zapytania do OpenSourceEngine.
- Możliwość tzw. "Toggle" (Zablokowania), gdzie pomimo licencji na maszynie deweloperskiej, wymuszany jest tryb Open Source.
- Zaimplementowano na tym samym ekranie rekursywny skaner lokalnych pre-kompilowanych magazynów Parquet połączony ze zbieraczem tzw. *garbage z danymi historycznymi*. Oszczędza to limit zapytań u brokerów bazowych (Rate Limiting).

---

## 2.3 Automatyczny Analityk jako klient LLM (Ollama & MCP)

Projekt wykorzystuje standard **MCP (Model Context Protocol)** przygotowując zestandaryzowany, odtwarzalny protokół do integracji modułu wykonawczego ze sztuczną inteligencją.

1. Wzór `ReportBuilder` przetwarza skomplikowaną architekturę krzywych kapitałowych `pandas.Series` dornsamplując jej próbki na precyzyjniej kontrolowany wektor o uciętej gęstości próbkowania w JSON (zabezpieczenie przed overflowing context window w LLM).
2. Wynik transponowany na *User Prompt* trafia poprzez synchronicznego klienta `OllamaClient` realizującego wyłącznie standardową bibliotekę natywną `urllib`. Weryfikacja serwera dokonuje się poprzez endpoint `/api/tags` serwera lokalnego.

Integracja pozwala wprost ze strony Dashboardu jednym kliknięciem uzyskać profesjonalną recenzję, wskazującą na luki w stopach zwrotu (np. błędy nadmiarowego win rate, bez wygenerowanego rzeczywistego profitu wskutek zjawisk drawdowns).

---

## 2.4 Eksploracja Danych Market Data i Nakładanie Algorytmów

Do podglądu zjawisk analitycznych zaimplementowano tzw. Eksplorator Rynku. Jest on samodzielnym oknem wizualizacyjnym renderującym diagramy świecowe (Plotly Candlesticks), rozbudowując aplikację o możliwość natychmiastowego nakładania metryk wskaźników m.in prostych i wykładniczych średnich kroczących jako podgląd przed uruchomieniem masowego backtestingu.

---

## 2.5 Obliczeniowa Skala Inżynierska: Optuna & Wskaźniki Natywne

Do warstwy analitycznej (silnik OpenSource) wstrzyknięto wsparcie dla bibliotek optymalizacji hiperparametrycznej stosowanej w Data Science / Quant Trading:

1. **Wskaźniki Natywne**: Architektura została zaprojektowana w oparciu o silnik open-source'owy wspierający podstawowe metody wektoryzacji. System pozwala na szybkie ewaluacje np. metody przecinania prostych średnich kroczących w pamięci.
2. **Optymalizator Parametrów (Optuna)**: Wdrożono osobną sekcję optymalizacyjną `5_Optimizer.py` która wykorzystuje estymatory _Tree-structured Parzen Estimator (TPE)_. Algorytm definiuje przedziały okien (np `sma_fast` 2-50, `sma_slow` 50-300). Każdy *trial* Optuny zamyka zapytanie na ułamek sekundy korzystając z cache wczytanego OHLCV, logując historię z punktem krytycznym dążącym do maksymalizacji Sharpe Ratio z jednoczesną penalizacją braku wejść w rynek (kara -99). Najlepszy parametr jest zwrotnie implementowany z automatycznym aliasem na nowej template'cie bazy danych. Została również naniesiona w pełni zintegrowana wizualizacja procesu z paczki `optuna.visualization`.
