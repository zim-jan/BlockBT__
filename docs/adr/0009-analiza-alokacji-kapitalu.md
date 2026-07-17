# ADR-0009: Analiza alokacji kapitału po backteście

- **Status:** zaakceptowana
- **Data:** 2026-07-17

## Kontekst i problem

Po backteście (zwłaszcza multi-symbol, Faza 10) użytkownik widzi metryki
i krzywe equity per symbol, ale nie widzi, **jak kapitał był rozłożony
między aktywa i gotówkę w czasie** — czyli faktycznej struktury portfela.
Bez tego trudno ocenić np. czy strategia w ogóle „pracuje" kapitałem, czy
większość czasu stoi w gotówce, oraz który symbol dominuje w wyniku.

Ograniczenia architektoniczne:

1. Portfel multi-symbol w silniku to **niezależne kolumny** vectorbt
   (`Portfolio.from_signals` z 2D close, bez `cash_sharing`/`group_by`) —
   każdy symbol dostaje własny `init_cash`. „Wspólna pula kapitału dzielona
   między aktywa" nie istnieje w obecnej semantyce egzekucji.
2. Obiekt `Portfolio` **nie jest persystowany** — wyniki żyją jako JSON
   w `BacktestJob.metrics` (SQLite). Analizy po fakcie nie da się policzyć
   z bazy; trzeba ją wyliczyć w momencie backtestu.

## Rozważane opcje

### (A) Struktura łącznego kapitału z obecnego portfela — wybrana

Wagi liczone z akcesorów vbt w momencie backtestu:
`w_i(t) = asset_value_i(t) / Σ value(t)`, `cash(t) = Σ cash(t) / Σ value(t)`.
W vbt `value = cash + asset_value` per kolumna, więc wagi + cash sumują się
do 1 na każdym barze (naturalny wykres stacked-area 100%).

- **Zysk:** zero zmian semantyki egzekucji (wyniki backtestów niezmienione);
  działa dla single- (ekspozycja vs gotówka) i multi-symbol; tanie obliczeniowo.
- **Koszt:** to analiza **struktury sumy niezależnych portfeli**, nie realnej
  wspólnej alokacji — wymaga uczciwego opisu w UI/dokumentacji.

### (B) Prawdziwy wspólny portfel (`cash_sharing=True`, `group_by`)

- **Zysk:** realna konkurencja aktywów o jedną pulę kapitału.
- **Koszt:** **zmiana breaking** semantyki wszystkich wyników multi-symbol
  (metryki per symbol przestają być niezależne), rozjazd z kontraktem
  `is_multi_symbol` (Faza 10) i testami parytetu (ADR-0008). Odrzucona na
  tym etapie; odnotowana jako praca przyszła (osobny tryb egzekucji).

### (C) Endpoint liczący alokację on-demand

Odrzucona: portfel nie jest persystowany — endpoint musiałby powtórnie
wykonać cały backtest przy każdym odpytaniu.

## Decyzja

**Opcja (A)**, wyliczana w `run_dag_backtest` (obie gałęzie) i zapisywana
w `job.metrics["allocation"]`:

- `timeline`: daty + wagi (`symbol → [0..1]`, plus klucz `cash`),
  **downsampling do ≤ 500 punktów** (payload JSON w SQLite; ostatni bar
  zawsze obecny).
- `summary` per symbol: `avg_exposure_pct` / `max_exposure_pct` (ekspozycja
  w ramach kapitału kolumny: `asset_value_i / value_i`), `time_in_market_pct`
  (% barów z otwartą pozycją), `final_equity_share_pct` (udział w kapitale
  końcowym).
- Awaria akcesorów portfela → `allocation = None` z warning-iem (analiza
  dodatkowa nie może ubić backtestu).
- API: pole `allocation` w `BacktestJobResponse`, zwracane **tylko** w
  `GET /api/backtest/{id}` (lista jobów pozostaje lekka — jak `equity_curve`).
- Frontend: sekcja „Allocation" w `PortfolioNode` — wykres stacked-area 100%
  (Plotly, `stackgroup`) + tabela podsumowania; renderowana dla single i multi.

## Konsekwencje

- Wyniki liczbowe backtestów **bez zmian** — alokacja to warstwa czysto
  analityczna nad istniejącą egzekucją.
- Klucz `cash` jest zarezerwowany w `timeline.weights` — symbol o nazwie
  `cash` (lowercase) kolidowałby; realne tickery są uppercase, ryzyko
  pomijalne (odnotowane).
- Stare joby (sprzed 2026-07-17) nie mają bloku `allocation` — frontend
  ukrywa sekcję, brak migracji danych.
- Praca przyszła: tryb wspólnego portfela (opcja B) jako świadome
  rozszerzenie egzekucji, nie zamiana obecnej semantyki.

## Powiązania

- ADR-0001 (broadcasting multi-symbol), ADR-0008 (parytet egzekucji).
- Kod: `backend/app/services/engine/opensource_engine.py`
  (`_build_allocation_analysis`), `backend/app/api/backtest.py`,
  `frontend/src/features/visual_builder/nodes/PortfolioNode.tsx`
  (`AllocationSection`).
- Testy: `test_engine/test_allocation.py`, `test_api/test_allocation_api.py`,
  `PortfolioNode.test.tsx` (sekcja ADR-0009).
