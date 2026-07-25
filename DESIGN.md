# BlockBT — System Projektowy (`DESIGN.md`)

**Wersja:** 2.0 · **Data:** 2026-07-25 · **Zastępuje:** wersję 1.x (Fazy 19–24)

Dokument opisuje **stan faktyczny** warstwy wizualnej po naprawie builda Tailwinda, nie stan pożądany. Każda reguła ma wskazanie źródła w kodzie — jeśli kod i ten dokument się rozejdą, kod jest prawdą, a dokument błędem do poprawienia.

> **Dlaczego wersja 2.0 pisana od zera:** wersja 1.x powstawała między majem a lipcem 2026, gdy build generował **20% klas Tailwinda** (patrz sekcja 1). Opisywała więc wygląd aplikacji pozbawionej większości stylów, a jej zalecenia — w szczególności „nakładki MUSZĄ mieć inline style, bo Tailwind v4 ich nie widzi" — były obejściami zepsutego builda, nie decyzjami projektowymi. Wszystkie takie zalecenia zostały usunięte.

---

## 1. Kontrakt builda — reguła nadrzędna

Frontend używa **Tailwind CSS 4.3** z konfiguracją w starym formacie JS. To wymaga dwóch rzeczy, których brak nie powoduje żadnego błędu — utilities po prostu cicho nie powstają:

```css
/* frontend/src/assets/index.css — pierwsze linie po importach fontów */
@import "tailwindcss";
@config "../../tailwind.config.js";
```

```js
// frontend/postcss.config.js — v4 prefiksuje samodzielnie (Lightning CSS)
export default { plugins: { '@tailwindcss/postcss': {} } }
```

**Zakazane:** dyrektywy `@tailwind base/components/utilities` (usunięte w v4) oraz `autoprefixer` i `postcss-import` w konfiguracji PostCSS.

### Weryfikacja przed każdym zgłoszeniem buga wizualnego

Historia z 2026-07-25: godzina debugowania Plotly, bo karta wykresu miała 0 px wysokości — klasa `h-96` nie istniała w CSS. Zanim zaczniesz szukać winy w komponencie albo bibliotece, sprawdź, czy klasa w ogóle powstała:

```bash
curl -s http://127.0.0.1:3000/src/assets/index.css | tr -d '\\' | grep -c '\.h-96'
npm run build   # rozmiar CSS: zdrowy build to ~75 kB, nie ~23 kB
```

Testy tego **nie wyłapią** — vitest przechodzi 47/47 i `npm run build` kończy się sukcesem przy 80% brakującego CSS, bo jsdom nie ładuje Tailwinda i nic nie asertuje wyglądu. Ostatni pomiar pokrycia: **399 z 409 klas użytych w kodzie (98%)**.

---

## 2. Dwa równoległe systemy tokenów — stan faktyczny

W repo współistnieją **dwie niezależne palety**. To nie jest zamierzone, ale jest realne i trzeba to wiedzieć, żeby nie mieszać:

| System | Źródło | Zasięg | Charakter |
|:--|:--|:--|:--|
| **Material 3 dark** | `frontend/tailwind.config.js` | wszystkie utilities Tailwinda (`bg-surface-container`, `text-on-surface`, `text-primary`…) | cyjan `#81ecff`, tła prawie czarne, **promienie 0 px** |
| **Legacy `:root`** | `frontend/src/assets/index.css` | wyłącznie klasy `.rf-*` kanwy React Flow | indygo `#6366f1`, tła granatowe, promienie 4/8/12/16 px |

**Reguła:** nowy kod używa **wyłącznie utilities Tailwinda** z palety M3. Zmienne `:root` są zamrożone — dotykamy ich tylko przy pracy nad kanwą React Flow. Nie definiuj nowych zmiennych `--*` dla komponentów Reactowych.

---

## 3. Paleta (Material 3 dark, `tailwind.config.js`)

| Token | Hex | Zastosowanie |
|:--|:--|:--|
| `background`, `surface` | `#0e0e0f` | tło aplikacji |
| `surface-container-lowest` | `#000000` | kanwa, obszary „wgłębione" |
| `surface-container-low` | `#131314` | paski nagłówków sekcji |
| `surface-container` | `#1a191b` | **domyślne tło kart i widżetów** |
| `surface-container-high` | `#201f21` | hover wierszy, kontrolki w kartach |
| `surface-container-highest`, `surface-variant` | `#262627` | modale, elementy wyniesione |
| `primary` | `#81ecff` | akcje, akcenty, aktywny stan |
| `secondary` | `#5cfd80` | wartości dodatnie, sukces |
| `error` | `#ff716c` | błędy, wartości ujemne |
| `on-surface` | `#ffffff` | tekst główny |
| `on-surface-variant` | `#adaaab` | tekst pomocniczy, etykiety |
| `outline-variant` | `#484849` | obramowania (zawsze z alfą, patrz §5) |

Wartości dodatnie/ujemne w tabelach i KPI: `text-green-400` / `text-error` (patrz `HistoryWidget.tsx`, `MetricCard.tsx`). Kolory kategorii węzłów kanwy — sekcja 8.

---

## 4. Typografia

| Klasa | Font | Zastosowanie |
|:--|:--|:--|
| `font-headline` | Space Grotesk | nagłówki stron, tytuły kart i modali |
| `font-body` | Inter | treść, tabele, akapity |
| `font-label` | Inter | etykiety, podpisy, opisy pól |

Fonty ładowane przez `@import url(...)` z Google Fonts w pierwszej linii `index.css`.

**Skala w praktyce:** `text-3xl` nagłówek strony · `text-xl` nagłówek sekcji · `text-base` tytuł modala · `text-sm` treść · `text-xs` etykiety i tabele (najczęstsza klasa w repo, 145 użyć) · `text-[10px]`/`text-[11px]` chipy i plakietki. Nagłówki: `font-bold` lub `font-semibold`; etykiety: `font-medium`.

---

## 5. Geometria, obramowania, cienie

1. **Promienie: 0 px.** `borderRadius` w configu nadpisuje `DEFAULT`, `lg` i `xl` na `0px` — `rounded`, `rounded-lg`, `rounded-xl` **nie zaokrąglają**. Ostre krawędzie są decyzją projektową. Wyjątek: `rounded-full` (9999 px) dla kropek statusu, plakietek pigułkowych i awatarów.
2. **Obramowania: 1 px z alfą.** Standard karty to `border border-outline-variant/30`; separatory wewnętrzne `border-outline-variant/20`; bardzo subtelne linie wierszy `border-outline-variant/10`. Nigdy nie używaj `border` bez klasy koloru — w v4 domyślnym kolorem jest `currentColor`, czyli obramowanie przyjmie barwę tekstu.
3. **Cienie:** wyłącznie dla elementów wyniesionych nad płaszczyznę — `shadow-2xl` dla modali, `shadow-lg` dla przycisków pływających, `shadow-inner` dla obszarów wgłębionych. Karty w treści są płaskie.

---

## 6. Architektura layoutu

Źródło: `frontend/src/components/layout/MainLayout.tsx`.

```
<div flex h-screen overflow-hidden>
  <Sidebar w-64 />                          ← nawigacja, flex sibling
  <div flex-1 flex flex-col min-w-0>
    <header px-6 py-5 border-b sticky />    ← tytuł + status API
    <main flex-1 flex flex-col p-6 gap-6>
      <div grid md:grid-cols-3 gap-6 />     ← karty KPI
      <div flex-1 border overflow-hidden /> ← obszar treści (children)
    </main>
  </div>
  <ChatPanel />                             ← panel boczny, flex sibling
  <InspectorPanel />                        ← panel boczny, flex sibling
</div>
```

### Reguły, od których nie ma odstępstw

1. **Panele boczne to flex-siblings, nie `fixed`.** `InspectorPanel` i `ChatPanel` są rodzeństwem głównego kontenera i używają `flex-none w-[szerokość] border-l`. Pozycjonowanie `fixed` dla panelu bocznego jest zakazane.
2. **Nakładki pełnoekranowe przez `createPortal(..., document.body)`** + `fixed inset-0 z-[9999]` klasami Tailwinda. Inline style **nie są** potrzebne (wersja 1.x tego wymagała — wyłącznie z powodu zepsutego builda).
3. **Nigdy `content-visibility`, `contain`, `transform`, `filter` ani `backdrop-filter` na kontenerach layoutu.** Każda z tych właściwości czyni element blokiem zawierającym dla potomków `position: fixed`, więc modal przestaje pokrywać rzutnię i zostaje przycięty do sekcji. To była przyczyna dwóch osobnych bugów Fazy 25 (`DashboardPage.tsx`, historia commitów 2026-07-25).
4. **Raporty HTML w `iframe` przez `srcDoc={html}`**, nigdy przez `src` z adresem API — inaczej użytkownik zobaczy surowy JSON.
5. **Zero `alert()`, `confirm()`, `prompt()`.** Powiadomienia idą przez `useToastStore`, potwierdzenia przez własne modale.

---

## 7. Wzorce komponentów

**Karta / widżet**
```tsx
<div className="bg-surface-container border border-outline-variant/30 p-6">
  <h3 className="font-headline font-semibold text-on-surface">Tytuł</h3>
</div>
```

**Pasek nagłówka wewnątrz karty** — `p-4 border-b border-outline-variant/20 bg-surface-container-low shrink-0`.

**Plakietka statusu** — `text-xs px-2 py-1 rounded-full font-medium` + para kolorów: sukces `bg-green-500/10 text-green-400`, błąd `bg-error/10 text-error`, w toku `bg-yellow-500/10 text-yellow-400`.

**Przycisk akcji** — `bg-primary/20 text-primary hover:bg-primary/30 transition-colors`. Przycisk ikonowy — `p-2 bg-surface-container-high text-on-surface-variant hover:text-on-surface`; stan aktywny `bg-primary/20 text-primary`.

**Formularze** — `bg-surface-container border border-outline-variant/40 px-2 py-1 text-xs focus:border-primary focus:outline-hidden`. Dark mode dla kontrolek natywnych wymusza `index.css`:
```css
select option { background-color: #131722 !important; color: #f9fafb !important; }
input, select, textarea { color-scheme: dark; }
```

**Tabela** — `w-full text-left border-collapse`; nagłówek `text-on-surface-variant font-label text-xs uppercase`; wiersz `border-b border-outline-variant/10 hover:bg-surface-container-high`.

**Odstępy** — kontenery stron `p-6 gap-6`; karty `p-4`–`p-6`; listy `space-y-2`…`space-y-4`. Żaden nagłówek, podtytuł ani przycisk nie styka się z krawędzią kontenera.

---

## 8. Kanwa React Flow

Jedyny obszar rządzony paletą `:root` z `index.css`.

| Kategoria węzła | Zmienna | Kolor | Obramowanie karty |
|:--|:--|:--|:--|
| Data Source | `--node-data` | `#2563eb` | `border-blue-500/30` |
| Indicators | `--node-indicator` | `#7c3aed` | `border-purple-500/30` |
| Signal / Logic | `--node-logic` | `#d97706` | `border-amber-500/30` |
| Portfolio / Execution | `--node-execution` | `#059669` | `border-emerald-500/30` |
| Optimizer / WFO | `--node-optimizer` | `#ec4899` | `border-pink-500/30` |

1. **Uchwyty połączeń** (`.react-flow__handle`, `.easy-connect-handle`): stały rozmiar, `z-index: 25`, ujemne przesunięcia `left/right`, środek na linii obramowania. Bez animacji `scale()` na hover.
2. **Węzły:** obramowanie 1 px w kolorze kategorii z alfą, padding `p-4`, bloki parametrów `px-3 py-1.5`, odstępy `space-y-2`/`space-y-2.5`.
3. **Bez emoji w nagłówkach węzłów** (decyzja z commita `a1ddda1`).
4. Formularze i wykresy **nie** mieszkają w węzłach — trafiają do `InspectorPanel`.

---

## 9. Dashboard (Faza 25)

Źródło: `DashboardPage.tsx`, `RealtimeChartWidget.tsx`, `HistoryWidget.tsx`, `NotesWidget.tsx`, `FullJobViewModal.tsx`.

1. **Karta wykresu:** `w-full h-96 bg-surface-container border border-outline-variant/30 shrink-0 relative overflow-hidden`. `overflow-hidden` jest obowiązkowe — trzyma płótno Plotly w granicach karty.
2. **Plotly dostaje jawne wymiary w pikselach**, mierzone `ResizeObserver` na kontenerze. Zakaz polegania na `autosize`/`responsive: true` — te mechanizmy mierzą kontener tylko przy montowaniu i na `resize` **okna**; przy pomiarze 0×0 Plotly wpada w domyślne 700×450 i wychodzi poza kartę.
3. **`layout.uirevision`** ustawione na `symbol-interwał` — zachowuje zoom przy odświeżeniu danych co 60 s, resetuje po zmianie instrumentu.
4. **Brak cichych awarii wykresu:** gdy pomiar kontenera zwróci 0, komponent renderuje widoczny komunikat błędu z odczytanymi wymiarami, nie puste miejsce.
5. **Wskaźniki:** na wykresie OHLC nakładane są wyłącznie SMA i EMA. RSI i MACD backend liczy, ale UI ich nie oferuje — wymagałyby subplotów z osobną osią Y (decyzja odłożona, warunek wstępny: rozstrzygnięcie, czy `/api/data/realtime` przechodzi na `ConnectorRegistry`).
6. **Modal szczegółów joba:** tearsheet QuantStats w `iframe srcDoc` po lewej, przełączane panele Notes/AI Chat po prawej, przycisk zamknięcia poza panelem.

---

## 10. Język i treść

- **UI wyłącznie po angielsku** (decyzja z commita `4cd2855`). Dokumentacja i komentarze w kodzie — po polsku.
- Emoji w interfejsie: tylko w plakietce statusu API. Poza tym nie.
- Komunikaty błędów mówią, **co** się stało i **co zrobić**, nie „Error occurred".

---

## 11. Martwe klasy — nie używać

Te klasy występują w kodzie, ale **nie mają żadnej definicji** i nic nie robią. Przy okazji pracy w tych plikach należy je usunąć:

| Klasa | Gdzie | Dlaczego martwa |
|:--|:--|:--|
| `prose`, `prose-invert`, `prose-xs` | `ChatPanel.tsx:140` | brak `@tailwindcss/typography`; `plugins: []` w configu |
| `modal-overlay`, `modal-content` | modale Visual Buildera | brak definicji w `index.css` |
| `strategy-item` | `StrategyListModal.tsx` | brak definicji w `index.css` |

---

## 12. Jak sprawdzić zgodność zmiany

```bash
cd frontend
npx tsc --noEmit          # typy
npx vitest run            # 47 testów
npm run build             # CSS ~75 kB — spadek do ~23 kB oznacza zepsuty build Tailwinda
```

Testy **nie sprawdzają wyglądu**. Zmiana wizualna wymaga obejrzenia w przeglądarce; przy podejrzeniu, że klasa nie działa — najpierw pomiar z sekcji 1, potem debugowanie komponentu.
