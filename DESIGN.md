# 🎨 BlockBT - Design System & UI/UX Guidelines (`DESIGN.md`)

> **Wersja:** 1.0.0  
> **Status:** Obowiązująca dla Fazy 19 (Refaktoryzacja Interfejsu GUI)  
> **Cel:** Przekształcenie surowego interfejsu prototypowego BlockBT w nowoczesną, ergonomiczną platformę klasy Enterprise FinTech / SaaS.

---

## 1. 🌟 Core Vision & Design Principles

1. **Elevation & Depth Layering:** Odchodzimy od płaskiego kontrastu `#000000` / `#FFFFFF`. Używamy wielowarstwowych cieni (`elevation-1` do `elevation-3`), łagodnych ramek z alfanumerycznym kryciem oraz subtelnych poświat (glow) dla wyróżnienia aktywnych elementów.
2. **Kanwa wolna od szumu (Clean Canvas First):** Węzły DAG służą do szybkiego podglądu przepływu i kluczowych wskaźników. Pełne formularze edycyjne przenosimy do wysuwanego **Inspector Panel** po prawej stronie.
3. **Dedykowany Panel Wyników (Bottom Drawer Strategy):** Interaktywne wykresy Plotly oraz QuantStats tearsheety renderujemy w dolnym rozsuwanym panelu (Bottom Drawer), eliminując ciasne wykresy i konflikty myszy wewnątrz węzłów.
4. **Human-Centric Error Handling:** Żadnych surowych zrzutów JSON (błędy 422)! Każdy błąd walidacji i API jest tłumaczony na zwięzły komunikat w języku naturalnym.
5. **Zero Native Browser Popups:** Bezwzględny zakaz używania `window.prompt()` oraz `window.alert()`. Wyszukiwanie, zapis i potwierdzenia odbywają się wyłącznie przez komponenty React Dialog / Modal z systemem Toast powiadomień.

---

## 2. 🎨 Color Palette & CSS Design Tokens

Wszystkie tokeny kolorów należy umieścić w głównym pliku arkusza stylów `frontend/src/assets/index.css`:

```css
:root {
  /* Tła i Powierzchnie (Elevation Layering) */
  --bg-app: #0b0d14;           /* Deep Midnight Black/Blue - Główne tło aplikacji */
  --bg-surface-1: #131722;     /* Topbar, Sidebar, Panel boczny, Modale */
  --bg-surface-2: #1c2130;     /* Węzły kanwy, podświetlone karty, sekcje wejściowe */
  --bg-surface-hover: #262c3e; /* Stan hover przycisków i wierszy */
  --bg-surface-active: #31384e;/* Stan active/pressed */

  /* Obramowania i Linie (Subtle Borders) */
  --border-subtle: rgba(255, 255, 255, 0.08); /* Domyślne ramki kart */
  --border-medium: rgba(255, 255, 255, 0.16); /* Obramowania wierszy i sekcji */
  --border-strong: #4f5875;                   /* Hover/Focus na obramowaniu */
  --border-accent: #6366f1;                   /* Ramka aktywnego węzła / wybranego elementu */

  /* Kolory Semantyczne Węzłów DAG */
  --node-data: #2563eb;        /* Data Source (Niebieski) */
  --node-indicator: #7c3aed;   /* Indicators (Fioletowy) */
  --node-logic: #d97706;       /* Signal Logic / Operators (Bursztynowy) */
  --node-execution: #059669;   /* Portfolio / Execution (Szmaragdowy) */
  --node-optimizer: #ec4899;   /* Optuna / WFO Optimizer (Różowy) */

  /* Akcenty i Stany Aplikacji */
  --accent-primary: #6366f1;   /* Indigo - Główny kolor akcji (Buttons, Active Tabs) */
  --accent-primary-hover: #4f46e5;
  --accent-success: #10b981;   /* Zyski, sukces, aktywne połączenie */
  --accent-warning: #f59e0b;   /* Ostrzeżenia, przestarzały stan węzła */
  --accent-danger: #ef4444;    /* Straty, błędy validation, usuwanie */

  /* Typografia */
  --text-main: #f9fafb;        /* Główny jasny tekst */
  --text-muted: #9ca3af;       /* Podpis, etykiety pól, szary tekst */
  --text-disabled: #4b5563;    /* Wyłączone opcje */

  /* Promienie Zaokrągleń (Border Radius Consistency) */
  --radius-sm: 4px;            /* Małe tagi, uchwyty, badge */
  --radius-md: 8px;            /* Przyciski, pola edycyjne, węzły DAG */
  --radius-lg: 12px;           /* Modale, Karty KPI, Inspector Panel */
  --radius-xl: 16px;           /* Glówne kontenery dialogów */

  /* Cienie i Efekty Głębokości */
  --shadow-sm: 0 1px 2px 0 rgba(0, 0, 0, 0.4);
  --shadow-md: 0 4px 6px -1px rgba(0, 0, 0, 0.5), 0 2px 4px -1px rgba(0, 0, 0, 0.3);
  --shadow-lg: 0 10px 25px -5px rgba(0, 0, 0, 0.6), 0 8px 10px -6px rgba(0, 0, 0, 0.4);
  --glow-accent: 0 0 15px rgba(99, 102, 241, 0.35);
  --glow-success: 0 0 12px rgba(16, 185, 129, 0.35);
}
```

---

## 3. 📐 Layout Architecture & Component Redesign

### A. Topbar Header (Górny Pasek & KPI Cards)
* **Karty Wyników (KPI Metrics Cards):** Zastąpić białe obramowania surowych pól tekstu czytelnymi minikartami:
  - Tło: `--bg-surface-1`, obramowanie: `--border-subtle`, zaokrąglenie: `--radius-md`.
  - Wartość metryki (np. `+22.85%` lub `1.84` Sharpe) wyrenderowana dużą pogrubioną czcionką (`Font-weight: 700`), kolor zielony dla zysków, czerwony dla strat.
  - Mała etykieta pod wartością: `--text-muted` (np. *Total Return*, *Sharpe Ratio*, *Max Drawdown*).
* **Global Action Toolbar:**
  - Przyciski akcji: `Run Backtest`, `Run Optimization`, `Clear Canvas`, `Save Strategy`, `Load Strategy`.
  - Przycisk `Run Backtest` na górnym pasku jest wyróżniony z gradientem akcentującym (`--accent-primary`) i ikoną Play (`Lucide Play`).

### B. Visual Builder & Node Canvas
* **Siatka Tła (Background Grid):** Wdrożyć tło kropkowane (Dot Grid) z tonacją `--border-subtle`, ułatwiające Pan & Zoom i orientację przestrzenną.
* **Kompaktowe Węzły DAG:**
  - Zmniejszyć bazowy gabaryt węzłów o ~40%.
  - Na kanwie prezentować tylko: Nagłówek (Nazwa + Ikona kategorii + Kropka statusu), zwięzłe podsumowanie parametrów (np. `SMA (14, 50)`) oraz mały wskaźnik statusu (zaznaczony na zielono po wyliczeniu, na żółto po zmianie parametrów).
  - Usunąć rozbudowane selektory dat, suwaki i wykresy bezpośrednio z wewnątrz węzła!
* **Porty i Połączenia (Handles & Edges):**
  - Uchwyty połączeń (Handles) o minimalnej strefie trafienia `20px` z delikatną poświatą przy najechaniu myszą.
  - Linie połączeń (Edges) z animacją przepływu (`animated: true`) podczas wykonywania obliczeń.
  - Wizualny feedback przy przeciąganiu połączenia (podświetlanie kompatybilnych portów docelowych).

### C. Inspector Panel (Wysuwany Panel Edycji Węzła)
* Po kliknięciu dowolnego węzła na kanwie, po prawej stronie otwierany jest **Inspector Panel**:
  - Nagłówek panelu zawiera typ węzła, jego identyfikator i krótki opis.
  - Wszystkie formularze edycji parametrów (daty, selektory tickerów, okna czasowe wskaźników, stop loss/take profit, budowanie custom kodu Numba JIT) znajdują się w tym panelu.
  - Zmiany w panelu natychmiast aktualizują stan węzła na kanwie.

### D. Results Panel (Bottom Drawer Strategy)
* Wyniki po uruchomieniu symulacji wyświetlane są w **Bottom Drawer**:
  - Wysuwany panel z dolnej krawędzi ekranu z możliwością zwijania/rozwijania i pełnego ekranu.
  - Zakładki panelu: `Overview Metrics`, `Plotly Equity Curve & Trades`, `QuantStats Tearsheet`, `Execution Logs`.
  - Wykresy Plotly mają zapewnioną odpowiednią przestrzeń, responsywność i obsługę zdarzeń bez nakładania się na przewijanie kanwy.

### E. System Powiadomień (Toasts) & Modale Zapisywania
* **Brak `window.prompt()`:** Zapisywanie nowej strategii otwiera elegancki modal React ze słownikiem nazw, tagami oraz podglądem struktury DAG.
* **Wyszukiwarka Strategii:** Popup wczytywania strategii posiada wbudowany input filtrowania po nazwie, datach utworzenia oraz przyciski szybkiego usuwania/wczytania z czytelnym kontrastem.
* **Toast Notifications:** Powiadomienia w prawym dolnym rogu (np. *"Strategia 'Momentum SMA' została pomyślnie zapisana"*, *"Błąd połączenia z serwerem"*).

### F. Chat AI Analyst (Ollama Integration)
* Przełączany panel czatu AI po prawej stronie ekranu z płynnym podglądem generowanego tekstu.
* Czytelny wskaźnik stanu ładowania (animowane kroki: *Pobieranie metryk* ➔ *Analiza wskaźników Sharpe/Drawdown* ➔ *Generowanie raportu*).

---

## 4. 🛠️ Guideline dla Zespołu Programistycznego (Faza 19 Roadmap)

Podczas wdrożenia w Fazie 19 postępujemy według kroków:
1. **Zmienne i style bazowe:** Aktualizacja `frontend/src/assets/index.css` o zaktualizowane tokeny `:root` i style kart/przycisków.
2. **Topbar & KPI Metrics:** Przebudowa nagłówka aplikacji z nowymi kartami KPI i globalnym przyciskiem Run.
3. **Inspector Panel & Odchudzenie Węzłów:** Stworzenie `InspectorPanel.tsx`, usunięcie formularzy i wykresów z wnętrza węzłów (`*Node.tsx`).
4. **Bottom Drawer dla Wyników:** Utworzenie `ResultsDrawer.tsx` dla wykresów Plotly i QuantStats.
5. **System Powiadomień & Modale:** Usunięcie native `prompt()` i `alert()`, wdrożenie toasta i modalu zapisu.

## 7. 📏 Architektura i Pozycjonowanie Paneli Bocznych (Sidebars) i Nakładek (Overlays)

Aby uniknąć problemów z ucinaniem zawartości (clipping) przez kontenery z `overflow-hidden` (np. `MainLayout`) oraz problemów z brakiem widoczności w Tailwind v4, należy bezwzględnie stosować poniższe reguły architektoniczne:

1. **Boczne Panele (InspectorPanel, ChatPanel):**
   - **Zakaz pozycjonowania `fixed`:** Nigdy nie używaj `fixed right-0` dla elementów, które mają działać jako sidebar obok głównej treści. 
   - **Zawsze używaj Flexbox:** Panel boczny musi być naturalnym bratem (sibling) głównego kontenera w układzie flex. Należy stosować klasy `flex-none w-[szerokość] border-l` i umieszczać go na tym samym poziomie drzewa co `<main className="flex-1">`.
   - **Przykład w `MainLayout.tsx`:**
     ```tsx
     <div className="flex h-screen overflow-hidden">
       <Sidebar />
       <div className="flex-1 overflow-hidden"> ... GŁÓWNA ZAWARTOŚĆ ... </div>
       <ChatPanel />      {/* Flex sibling na prawej stronie */}
       <InspectorPanel /> {/* Flex sibling na prawej stronie */}
     </div>
     ```

2. **Modale i Full-Screen Overlays (ResultsOverlay, SaveStrategyModal, itp.):**
   - **Gwarancja Portali (`createPortal`):** Wszystkie nakładki pełnoekranowe i dialogi muszą renderować się w `document.body` poprzez `createPortal(..., document.body)`.
   - **Jawne Inline Fixed Styles:** Ze względu na specyfikę kompilacji Tailwind v4, kontenery nakładek MUSZĄ posiadać natywne style inline dla pełnego pokrycia rzutni:
     ```tsx
     style={{
       position: 'fixed',
       top: 0,
       left: 0,
       right: 0,
       bottom: 0,
       backgroundColor: 'rgba(11, 13, 20, 0.96)',
       backdropFilter: 'blur(8px)',
       zIndex: 100000,
       display: 'flex',
       flexDirection: 'column'
     }}
     ```
   - **Zarządzanie Stanem:** Stan widoczności (`isSaveModalOpen`, `isResultsOpen`) musi pochodzić z `useWorkflowStore` z użyciem atomowych selektorów `useWorkflowStore((s) => s.isSaveModalOpen)`.

3. **Renderowanie Raportów HTML w `iframe`:**
   - Ekrany z raportami (np. QuantStats Tearsheet) należy pobierać via API (`fetch`) i przekazywać do elementu `iframe` za pomocą `srcDoc={html}`. Bezwzględny zakaz podawania URL API bezpośrednio w `src` iframe (zapobiega to wyświetlaniu surowej odpowiedzi JSON).

4. **Kontrast Formularzy w Dark Mode:**
   - Wszystkie listy rozwijane `<select>` i polecenia wyboru muszą posiadać reguły CSS zapewniające jasny tekst (`#f9fafb`) na ciemnym tle (`#131722`):
     ```css
     select option {
       background-color: #131722 !important;
       color: #f9fafb !important;
     }
     input, select, textarea {
       color-scheme: dark;
     }
     ```

