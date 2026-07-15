# ADR-0004: QSAdapter — Analityka i tearsheety (Faza 13)

- **Status:** Zaakceptowany
- **Data:** 2026-07-15
- **Faza:** 13 — QSAdapter Analytics / Tearsheets (Filar analityczny)

## Kontekst

Cel Fazy 13: udostępnić warstwę analityczną prezentującą wyniki backtestu w postaci
czytelnego raportu (**tearsheet**). Test TDD (red)
`test_qsadapter.py::test_generate_html_tearsheet` wymaga:

- importu `from app.services.engine.qsadapter import QSAdapterService`,
- statycznej metody `QSAdapterService.generate_tearsheet(pf)`,
- gdzie `pf` udostępnia **wyłącznie** `pf.stats()` (mock zwraca `{"Sharpe Ratio": 1.5}`,
  brak `.returns()`),
- a wynik to `str` HTML zawierający `"<html>"` oraz `"Sharpe Ratio"`.

BlockBT działa w modelu Self-Hosted / Air-Gapped — raport nie może zależeć od
zasobów sieciowych ani od dostępnego backendu graficznego.

## Rozważane opcje

### Sposób generowania HTML

#### A. Samodzielny HTML z `pf.stats()` — wybrana
Adapter normalizuje `pf.stats()` (`Series`/`dict`) do płaskiego słownika i składa
kompletny dokument HTML z tabelą metryk (inline CSS, bez zasobów zewnętrznych).

- **Zysk:** spełnia kontrakt testu (portfel udostępnia tylko `stats()`),
  w pełni air-gapped, deterministyczny, testowalny w izolacji, brak zależności od
  display/matplotlib. Odporność: przy błędzie `stats()` degraduje do HTML z
  komunikatem o braku metryk (wzorzec `_extract_qs_metrics` z `OpenSourceEngine`).
- **Koszt:** brak wykresów w wariancie MVP (tabela metryk zamiast pełnego
  wizualnego tearsheetu QuantStats).

#### B. `qs.reports.html(returns)`
Natywny generator pełnego raportu QuantStats.

- **Koszt (odrzucona jako MVP):** funkcja **zwraca `None`** (pisze wynik do pliku,
  nie do stringa), wymaga pełnej **serii zwrotów** `returns` (której kontrakt testu
  nie udostępnia — mock ma tylko `stats()`), oraz backendu graficznego (display) do
  renderowania wykresów. Sprzeczne z kontraktem testu i z modelem air-gapped bez
  dodatkowej obudowy.

**Decyzja cząstkowa:** opcja A jako rdzeń. Opcja B dostępna jako **opcjonalne**
rozszerzenie `generate_full_tearsheet` (backend `Agg`, graceful fallback do A) —
poza MVP fazy.

### Źródło metryk dla endpointu REST

#### A. Adapter `stats()` z zapisanych metryk `BacktestJob` — wybrana
`BacktestJob` przechowuje skalarne metryki (`total_return_pct`, `sharpe_ratio`,
`max_drawdown_pct`, `num_trades`, `final_capital`) + elastyczny słownik `metrics`,
ale **nie** trzyma żywego obiektu vbt `Portfolio`. Endpoint buduje lekki obiekt
adaptera udostępniający `stats()` z tych metryk i przekazuje go do
`generate_tearsheet`.

- **Zysk:** reużycie tej samej ścieżki renderowania co dla portfela; brak potrzeby
  re-egzekucji backtestu; spójne z istniejącym schematem persystencji.
- **Koszt:** raport ograniczony do metryk zapisanych w jobie (bez per-bar equity
  curve w tabeli).

#### B. Re-egzekucja backtestu i pełny portfel vbt
Odtworzenie portfela w locie na potrzeby raportu.

- **Koszt (odrzucona):** kosztowne (ponowna symulacja), duplikacja logiki runnera,
  ryzyko niespójności z pierwotnym wynikiem. Nieproporcjonalne do zakresu.

**Decyzja cząstkowa:** opcja A.

## Decyzja

- **Serwis:** `QSAdapterService.generate_tearsheet(pf) -> str`
  (`backend/app/services/engine/qsadapter.py`) — staticmethod, normalizacja
  `Series`/`dict`, escaping wartości (`html.escape`), guard `try/except` +
  `logger.warning`, samodzielny HTML (inline CSS, air-gapped).
- **Rozszerzenie:** `generate_full_tearsheet(returns, title)` —
  `matplotlib.use("Agg")` przed importem plottingu, fallback do prostego tearsheetu;
  poza MVP.
- **Schemat:** `TearsheetResponse` (`job_id: int`, `html: str`,
  `format: Literal["html"]="html"`, `generated_at: datetime`) w
  `backend/app/schemas/results.py`.
- **Endpoint:** `GET /api/results/{job_id}/tearsheet` →
  `ApiResponse[TearsheetResponse]` (`backend/app/api/results.py`); 404 (brak joba),
  400 (`status != COMPLETED`), 200 (OK); adapter `stats()` z metryk joba.

## Konsekwencje

**Pozytywne**

- Tearsheet działa end-to-end (portfel/job → HTML), w pełni air-gapped, bez
  zależności od display/sieci.
- Ścieżka renderowania współdzielona między bezpośrednim wywołaniem na portfelu a
  endpointem REST (jeden punkt prawdy dla formatu raportu).
- Odporność na kruchość `stats()`/QuantStats (graceful degradation, brak twardych
  wyjątków w ścieżce raportowania).

**Negatywne / ryzyko rezydualne**

- Wariant MVP to tabela metryk — brak wykresów (equity curve, drawdown) do czasu
  włączenia `generate_full_tearsheet` do przepływu (świadome cięcie zakresu).
- Endpoint raportuje metryki zapisane w jobie — zakres metryk ograniczony do tego,
  co runner utrwala w `BacktestJob.metrics` / kolumnach nagłówkowych.

## Powiązania

- Poradnik: [Analityka i tearsheety](../backend/analytics_tearsheets.md).
- Kod: `backend/app/services/engine/qsadapter.py`,
  `backend/app/api/results.py`, `backend/app/schemas/results.py`.
- Testy: `backend/tests/test_engine/test_qsadapter.py`,
  `backend/tests/test_api/test_tearsheet.py`.
