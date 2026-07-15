# ADR-0003: Advanced Portfolio i Risk Management (Faza 12)

- **Status:** Zaakceptowany
- **Data:** 2026-07-14
- **Faza:** 12 — Advanced Portfolio i Risk Management (Filar 4)

## Kontekst

Cel Fazy 12 (roadmap `AGENTS.md`): „Złożona egzekucja. Symulacja zdarzeniowa."
Do tej pory węzeł Execution (Portfolio) egzekwował tylko wejścia/wyjścia z sygnałów
(`entries`/`exits`) bez żadnej logiki zarządzania ryzykiem — brak stop-loss,
take-profit i kontroli wielkości pozycji. Test TDD (red) `test_portfolio_risk.py`
wymagał, by ustawienie `sl_stop`/`tp_stop` w węźle Portfolio realnie wpływało na
egzekucję (wyjście z pozycji przy przebiciu poziomu stopu) i by liczba takich
wyjść była widoczna w wyniku backtestu.

## Rozważane opcje

### Mechanizm egzekucji stopów

#### A. `vbt.Portfolio.from_signals` z parametrami `sl_stop`/`tp_stop`/`sl_trail` — wybrana
Natywne parametry stopów przekazywane bezpośrednio do `from_signals`; silnik vbt
(Numba/Rust) sam ewaluuje przebicie poziomu na każdym barze i generuje wyjście.

- **Zysk:** idiomatyczne dla vectorbt, zerowy dodatkowy kod pętli, pełna prędkość
  wektorowa/JIT, spójne z istniejącą ścieżką `execute_dag_portfolio` (Faza 10).
  Trailing stop (`sl_trail=True`) „za darmo" — bez ręcznej logiki max-high trackingu.
- **Koszt:** kontrakt sztywny — nie obsłużymy niestandardowych reguł wyjścia
  (np. stop zależny od zmienności/ATR) bez rozszerzenia poza proste `sl_stop`/`tp_stop`.

#### B. `vbt.Portfolio.from_orders` + własna order-func z ręcznym stopem
Pełna kontrola nad egzekucją zdarzeniową (`order_func_nb`), stop liczony ręcznie
bar-po-barze w funkcji Numba.

- **Zysk:** maksymalna elastyczność — dowolna logika egzekucji, w tym event-driven
  (dokładniej odpowiada nazwie „symulacja zdarzeniowa" z celu fazy).
  Otwiera drogę do złożonych reguł (np. pyramiding, partial exits) w przyszłości.
- **Koszt:** znacznie większa złożoność implementacji i utrzymania (własny kod
  Numba, ręczne zarządzanie stanem pozycji), wyższe ryzyko błędów, dłuższy czas
  developmentu. Poza proporcją do zakresu jednej fazy pracy dyplomowej.

**Decyzja cząstkowa:** opcja A. `from_orders` + własna order-func to świadomie
odłożona praca przyszła (patrz „Poza zakresem" niżej) — obecny zakres (SL/TP/trailing
+ sizing) w pełni pokrywa `from_signals`.

### Wymóg węzła Indicators w DAG

#### A. Twardy wymóg — DAG bez węzła Indicators rzuca `GraphValidationError` — wybrana
`run_dag_backtest` sprawdza obecność węzła kategorii `Indicators`; brak → błąd
walidacji zamiast cichego fallbacku.

- **Zysk:** jawny błąd zamiast milczącego „no-op" portfela (bez sygnałów SL/TP
  nie ma na czym zadziałać — pozycja nigdy się nie otwiera). Spójne z filozofią
  `GraphParser` (Kahn + `COMPATIBILITY_MATRIX`) — DAG bez źródła sygnału to DAG
  niepoprawny semantycznie, nie tylko strukturalnie.
- **Koszt:** **wymusił modyfikację zamrożonego testu RED** `test_portfolio_risk.py`
  (patrz „Konsekwencje").

#### B. Domyślny buy & hold (brak Indicators → wejście na barze 0, brak exitów)
Cichy fallback zamiast błędu.

- **Zysk:** brak wymogu modyfikacji istniejącego testu; zawsze zwraca jakiś wynik.
- **Koszt:** maskuje błąd użytkownika (DAG bez logiki sygnałowej to prawie zawsze
  pomyłka w Visual Builderze); SL/TP i tak wymagają jakiegoś wejścia, więc problem
  tylko się przesuwa — ostatecznie i tak trzeba framework do sztucznego entry (jak
  w opcji A, tylko ukryty w silniku zamiast w teście).

**Decyzja cząstkowa:** opcja A.

### Surfacing liczby wyjść SL/TP

#### A. Klasyfikacja zamkniętych transakcji po cenie (`_count_stop_exits`) — wybrana
Po egzekucji silnik iteruje `portfolio.trades.records_readable`, klasyfikuje każdą
zamkniętą transakcję na podstawie relacji `Avg Exit Price` do `Avg Entry Price`
względem poziomu stopu (z tolerancją `eps=1e-3`), osobno dla long/short.

- **Zysk:** działa niezależnie od wersji vbt/API — nie polega na wewnętrznym
  enumie ani na kolumnach, których obecność/nazewnictwo może się zmieniać między
  wydaniami. Czytelne, testowalne w izolacji.
- **Koszt:** heurystyka na tolerancji `eps` — przy bardzo bliskich sobie poziomach
  SL/TP i szumie cenowym możliwa błędna klasyfikacja na granicy; nie rozróżnia
  „zamknięcia z innego powodu, które przypadkiem trafiło w okolicę poziomu stopu".

#### B. Enum `StopType` z rekordów transakcji vbt
Odczyt typu wyjścia wprost z wewnętrznego enuma vectorbt.

- **Koszt (odrzucona, potwierdzone empirycznie):** rekordy transakcji vbt **nie
  etykietują typu stopu** wprost w publicznym API `records_readable`, a sam enum
  `StopType` ma `TP=2` (nie `1`, jak można by intuicyjnie założyć) — pułapka przy
  ręcznym mapowaniu. Krucha zależność od wewnętrznej struktury biblioteki.

#### C. `vbt.ohlcstx.generate_ohlc_stop_exits` (natywny generator masek stopów)
Osobna, natywna funkcja vbt do generowania masek wyjść SL/TP przed `from_signals`.

- **Koszt (odrzucona):** wymaga przebudowy przepływu egzekucji (osobny krok
  generowania masek zamiast przekazania `sl_stop`/`tp_stop` bezpośrednio do
  `from_signals`) bez wyraźnej korzyści nad prostszą klasyfikacją post-hoc;
  dodatkowa złożoność dla single-symbol ścieżki, gdzie `_count_stop_exits`
  wystarcza.

**Decyzja cząstkowa:** opcja A.

## Decyzja

- **Egzekucja stopów:** `vbt.Portfolio.from_signals(..., sl_stop, tp_stop, sl_trail,
  size, size_type)` w `execute_dag_portfolio` — parametry dokładane do `kwargs`
  **tylko gdy ustawione** (brak wpływu na istniejące DAG-i bez ryzyka/sizingu,
  zero regresji Faz 10/11). `size_type` przyjmowany jako string wprost
  (`"amount" | "value" | "percent"`) — vbt 1.0.0 akceptuje to bez konwersji na enum.
- **Wymóg Indicators:** `run_dag_backtest` rzuca `GraphValidationError("DAG musi
  zawierać węzeł Indicators.")`, gdy w `dag["nodes"]` nie ma węzła kategorii
  `Indicators`.
- **Surfacing SL/TP:** `_count_stop_exits` — klasyfikacja zamkniętych transakcji
  po cenie wyjścia vs poziom stopu (long/short symetrycznie, `eps=1e-3`). Wynik
  trafia do `result["raw"]["Stop Loss Exits"]` / `["Take Profit Exits"]`
  **tylko gdy dany stop był ustawiony** w węźle Execution.
- **Schema:** `ExecutionParams` (`backend/app/schemas/dag.py`) — nowe pola
  `sl_stop: float | None` (0..1), `tp_stop: float | None` (0..1),
  `sl_trail: bool = False`, `size: float | None` (>0),
  `size_type: Literal["amount","value","percent"] = "amount"`.
- **Frontend:** pola Stop Loss / Take Profit / Position Size w `PortfolioNode.tsx`
  — UI operuje na procentach, zapis do DAG jako frakcja `0..1`.

## Konsekwencje

**Pozytywne**

- SL/TP/trailing/sizing działają end-to-end (DAG JSON → `from_signals` → wynik),
  bez własnej pętli egzekucyjnej — pełna prędkość wektorowa vbt.
- Liczby wyjść SL/TP widoczne w `raw` niezależnie od wersji vbt (odporność na
  zmiany wewnętrznego API biblioteki).
- Wymóg węzła Indicators zamyka klasę błędów „DAG bez logiki sygnałowej cicho
  zwraca pusty portfel" — błąd jest jawny i wczesny (walidacja przed egzekucją).

**Negatywne / ryzyko rezydualne**

- **Modyfikacja zamrożonego testu RED.** Test `test_portfolio_risk.py` pierwotnie
  budował DAG z samym węzłem Execution (bez Indicators), licząc na cichy fallback
  silnika. Wymóg Indicators (decyzja świadoma, patrz wyżej) uczyniłby taki DAG
  niepoprawnym już na etapie walidacji, więc test nigdy nie dotarłby do właściwej
  asercji SL/TP. **Za zgodą Janka** test przebudowano: dodano węzeł Indicators w
  trybie custom code (ścieżka Fazy 11) generujący wejście na barze 0 i puste
  exity — dzięki temu SL na ruchu 100→90 (-10%) faktycznie ma się o co odbić.
  Zamrożenie testów RED nie jest więc bezwzględne — modyfikacja wymaga jawnej
  zgody użytkownika i jest udokumentowana (patrz też hygiene: usunięte z testu
  nieaktualne komentarze sugerujące brak implementacji).
- **Klasyfikacja po cenie ma tolerancję `eps`** — przy poziomach stopów bardzo
  blisko siebie lub przy szumie cenowym granicznym możliwa błędna klasyfikacja
  pojedynczej transakcji; nie wpływa na poprawność samej egzekucji SL/TP przez
  vbt, tylko na dokładność raportowanego licznika.
- **Multi-symbol surfacing poza zakresem.** `_count_stop_exits` operuje na
  ścieżce single-symbol (`portfolio.trades.records_readable` jako płaski
  DataFrame). Gałąź multi-symbol (`_build_multi_symbol_result`, Faza 10) SL/TP
  egzekwuje poprawnie (parametry broadcastują się po kolumnach w `from_signals`),
  ale **nie zwraca per-symbol liczników wyjść SL/TP** — świadome cięcie zakresu
  tej fazy, odłożone na przyszłą pracę.
- **`from_orders`/event-driven order-func poza zakresem** — patrz opcja B wyżej;
  obecne pokrycie (`from_signals`) wystarcza dla wymagań fazy, pełna symulacja
  zdarzeniowa z niestandardowymi regułami wyjścia to praca przyszła.

## Powiązania

- Poradnik użytkownika: [Zarządzanie ryzykiem](../backend/risk_management.md).
- Kod: `backend/app/services/engine/opensource_engine.py`
  (`execute_dag_portfolio`, `run_dag_backtest`, `_count_stop_exits`).
- Schema: `backend/app/schemas/dag.py` (`ExecutionParams`).
- Frontend: `frontend/src/components/nodes/PortfolioNode.tsx`.
- Test: `backend/tests/test_engine/test_portfolio_risk.py`.
