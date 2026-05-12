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
- **Typy**: SMA Crossover (Srednie kroczące), MACD, Custom Code.
- **Custom Code**: Umożliwia wpisanie własnego kodu Python/vectorbt bezpośrednio w edytorze (wymaga zdefiniowania zmiennych `entries` i `exits`).
- **Parametry**: Okresy wskaźników, Kapitał początkowy.

### 3. Signal Node (Logika Sygnałów)
Pełni rolę informacyjną i walidacyjną, wizualizując logikę sygnałów generowanych przez Indicator Node (np. "Fast crosses above Slow").

### 4. Portfolio Node (Wyniki Backtestu)
Punkt końcowy standardowego przepływu backtestu.
- **Metryki**: Total Return, Sharpe Ratio, Max Drawdown, Win Rate, Total Trades.
- **Analiza AI**: Przycisk "Analyze Results" otwiera panel czatu AI i generuje raport na podstawie danych z tego węzła.

### 5. Optimizer Node (Optymalizacja Optuna)
Specjalistyczny węzeł do szukania najlepszych parametrów.
- **Funkcje**:
    - **Sync Bounds**: Automatycznie pobiera parametry z połączonego Indicator Node i sugeruje domyślne zakresy poszukiwań.
    - **Optimize**: Uruchamia zadanie optymalizacji bayesowskiej (Optuna).
    - **Apply Results**: Pozwala wstrzyknąć najlepsze znalezione parametry z powrotem do Indicator Node jednym kliknięciem.
- **Wizualizacja**: Zawiera wbudowany wykres postępu optymalizacji.

---

## Walidacja i Wykonanie

Uruchomienie strategii wymaga poprawnego połączenia węzłów. Logika ta jest enkapsulowana w hookach `useWorkflowExecution` oraz `useWorkflowOptimization`.

### Reguły Połączeń
- **Standard**: `Data Node` → `Indicator Node` → `Portfolio Node`.
- **Optimization**: `Data Node` → `Indicator Node` → `Optimizer Node`.

### Cykl Życia Wykonania (Lifecycle)
1. **Walidacja**: Sprawdzenie, czy graf jest kompletny i czy parametry są poprawne (np. `sma_fast < sma_slow`).
2. **Tworzenie Strategii**: Wysłanie parametrów do backendu (`POST /api/strategies/`) w celu utworzenia lub pobrania identyfikatora strategii.
3. **Uruchomienie Zadania**: Wysłanie żądania `POST /api/backtest/` (lub `/api/optimizer/`).
4. **Polling**: System co 2.5 sekundy odpytuje backend o status zadania.
5. **Wstrzyknięcie Wyników**: Po zakończeniu zadania (`COMPLETED`), wyniki są mapowane i zapisywane bezpośrednio w stanie `data` odpowiedniego węzła (`Portfolio` lub `Optimizer`), co powoduje natychmiastową aktualizację interfejsu.
