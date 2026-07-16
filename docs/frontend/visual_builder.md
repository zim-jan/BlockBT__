# Frontend - Visual Builder (React Flow)

Visual Builder to serce interfejsu BlockBT, umożliwiające projektowanie strategii handlowych za pomocą intuicyjnego edytora graficznego. Moduł ten opiera się na najnowszej bibliotece **React Flow 12 (@xyflow/react)** i implementuje model skierowanego grafu acyklicznego (DAG).

## Architektura i Przepływ

Edytor wizualny pozwala na budowanie przepływów, w których dane rynkowe są przetwarzane przez wskaźniki techniczne, generując sygnały, które ostatecznie trafiają do modułów wykonawczych (Portfolio lub Optimizer).

- **`WorkflowEditor.tsx`**: Główny komponent zarządzający płótnem edytora.
- **`workflowStore.ts`**: Sklep Zustand przechowujący stan wszystkich węzłów (`nodes`) i krawędzi (`edges`).
- **Easy Connect**: Funkcjonalność ułatwiająca tworzenie połączeń. Cały obszar węzła działa jako aktywny uchwyt (`Handle`), co pozwala na przeciąganie krawędzi z dowolnego punktu ciała węzła.

---

## Interakcja z Węzłami

Wraz z przejściem na React Flow 12 i implementacją Easy Connect, interakcja z węzłami została zoptymalizowana:

*   **Przesuwanie**: Odbywa się poprzez chwycenie za nagłówek węzła (wykorzystanie klasy `.react-flow__node-drag-handle`).
*   **Łączenie**: Odbywa się poprzez kliknięcie i przeciągnięcie z dowolnego miejsca wewnątrz węzła (oprócz interaktywnych pól wejściowych). Wykorzystuje to niewidzialne uchwyty `.easy-connect-handle`.
*   **Z-Index**: Elementy formularzy (inputy, selecty) są umieszczone powyżej uchwytów łączenia, aby zachować pełną interaktywność.

---

## Referencja Węzłów (Nodes)

Każdy węzeł w BlockBT pełni określoną funkcję i posiada dedykowany interfejs konfiguracji.

### 1. Data Node (Źródło Danych)
Definiuje parametry wejściowe dla danych rynkowych.
- **Źródła**: Yahoo Finance, Alpaca, Synthetic (dane losowe).
- **Parametry**: Symbol, Interwał (Timeframe), Zakres dat (Start/End).

### 2. Indicator Node (Logika Strategii)
Główny węzeł decyzyjny strategii.
- **Typy**: SMA Crossover, MACD, Custom Code oraz **wskaźniki dynamiczne**.
- **Dynamiczne Parametry**: Węzeł automatycznie pobiera listę dostępnych wskaźników z backendowego rejestru (np. TA-Lib). Po wyborze wskaźnika, interfejs dynamicznie generuje pola wejściowe dla wszystkich wymaganych parametrów (np. `window`, `timeperiod`).
- **Custom Code**: Umożliwia wpisanie własnego kodu Python/vectorbt bezpośrednio w edytorze.
- **Parametry**: Okresy wskaźników, Kapitał początkowy.

### 3. Signal Node (Logika Sygnałów)
Pozwala na wizualizację i wybór akcji wektoryzowanych:
- **Crossover**: Standardowe przecięcia średnich.
- **Ranking**: Sortowanie aktywów na podstawie wartości wskaźnika (multi-symbol).
- **Mapping**: Mapowanie sygnałów w poprzek parametrów przy użyciu `FlexArray`.

### 4. Portfolio Node (Wyniki Backtestu)
Punkt końcowy standardowego przepływu backtestu.
- **Metryki**: Total Return, Sharpe Ratio, Max Drawdown, Win Rate, Total Trades.
- **Krzywa Kapitału (Plotly)**: Interaktywny wykres liniowy z obszarem pod krzywą, umożliwiający szczegółową analizę zmian wartości portfela w czasie.
- **Analiza AI**: Przycisk "Analyze Results" otwiera panel czatu AI.

### 5. Optimizer Node (Optymalizacja Optuna)
Specjalistyczny węzeł do szukania najlepszych parametrów.
- **Funkcje**:
    - **Sync Bounds**: Automatycznie pobiera parametry z połączonego Indicator Node i sugeruje domyślne zakresy poszukiwań.
    - **Optimize**: Uruchamia zadanie optymalizacji bayesowskiej (Optuna).
    - **Apply Results**: Pozwala wstrzyknąć najlepsze znalezione parametry z powrotem do Indicator Node jednym kliknięciem.
- **Wizualizacja**: Zawiera wbudowany wykres postępu optymalizacji.

### 6. Walk-Forward Node (WFO)
Węzeł dedykowany do testowania strategii na oknach kroczących.
- **Parametry**: Window Size (rozmiar okna treningowego, np. `365d`), Step Size (skok okna, np. `90d`).
- **Zastosowanie**: Weryfikacja stabilności strategii i odporności na zmiany rynkowe.

---

## Walidacja i Wykonanie

Uruchomienie strategii odbywa się bezpośrednio z poziomu węzłów wynikowych. Logika ta jest enkapsulowana w hookach `useWorkflowExecution` oraz `useWorkflowOptimization`.

### Przyciski Wykonania (Inline Execution)
W wersji 3.0 przyciski sterujące zostały przeniesione z globalnego paska narzędzi bezpośrednio do węzłów, które generują wyniki:
- **Portfolio Node**: Zawiera przycisk **"Run Backtest"**.
- **Optimizer Node**: Zawiera przycisk **"🚀 Optimize"** oraz **"🔄 Sync"**.
- **Walk-Forward Node**: Zawiera przycisk **"Run WFO"**.

Dzięki temu użytkownik wyzwala akcję w miejscu, w którym spodziewa się zobaczyć wyniki, co poprawia czytelność interfejsu.

### Reguły Połączeń
- **Standard**: `Data Node` → `Indicator Node` → `Portfolio Node`.
- **Optimization**: `Data Node` → `Indicator Node` → `Optimizer Node`.
- **Walk-Forward**: `Data Node` → `Indicator Node` → `Walk-Forward Node`.

### Cykl Życia Wykonania (Lifecycle)
1. **Walidacja**: Sprawdzenie, czy graf jest kompletny i czy parametry są poprawne (np. `sma_fast < sma_slow`).
2. **Tworzenie Strategii**: Wysłanie parametrów do backendu (`POST /api/strategies/`) w celu utworzenia lub pobrania identyfikatora strategii.
3. **Uruchomienie Zadania**: Wysłanie żądania `POST /api/backtest/` (lub `/api/optimizer/`).
4. **Polling**: System co 2.5 sekundy odpytuje backend o status zadania.
5. **Wstrzyknięcie Wyników**: Po zakończeniu zadania (`COMPLETED`), wyniki są mapowane i zapisywane bezpośrednio w stanie `data` odpowiedniego węzła (`Portfolio` lub `Optimizer`), co powoduje natychmiastową aktualizację interfejsu.
