# ADR-0007: Usunięcie bloku TimeShift — automatyczny shift sygnałów w silniku

* Status: zaakceptowany
* Data: 2026-07-17
* Decydenci: Jan Zimny (decyzja z review 2026-07-16), implementacja: sesja Claude Code

## Kontekst i problem

Ochrona przed Look-ahead Bias (Faza 9.3) była zrealizowana jako **obowiązkowy
węzeł TimeShift** na kanwie: `GraphParser._validate_financial_traps` odrzucał
(HTTP 422) każdy DAG, w którym węzeł Execution nie był bezpośrednio poprzedzony
węzłem `LogicOperators` z `operator_type == "time_shift"`, a silnik aplikował
`fshift(shift_periods)` iterując po wszystkich takich węzłach.

Problemy zgłoszone w review użytkownika (2026-07-16):

1. **UX:** użytkownik musiał ręcznie stawiać techniczny blok, bez którego każdy
   prosty graf `Data → Indicator → Portfolio` kończył się kryptycznym 422 —
   mimo że przesunięcie sygnałów to inwariant poprawności, nie decyzja
   projektowa użytkownika.
2. **Ukryty podwójny shift:** `signalNode` dostawał w defaultach store'a
   `operator_type: "time_shift"`, więc graf zawierający `signalNode` **oraz**
   `timeShiftNode` był przesuwany dwukrotnie (pętla w `run_dag_backtest`
   iterowała po wszystkich węzłach LogicOperators z time_shift).
3. Ścieżka legacy (`run_backtest`, nie-DAG) nigdy nie miała żadnego shiftu —
   ochrona była niespójna między ścieżkami.

## Rozważane opcje

1. **Auto-shift w silniku, jawne węzły time_shift jako no-op** (wybrana)
   — silnik bezwarunkowo przesuwa `entries`/`exits` o 1 okres zaraz po
   `IndicatorService.generate_signals()`; kod reagujący na
   `operator_type == "time_shift"` znika całkowicie.
   * Zysk: zero konfiguracji użytkownika; podwójny shift niemożliwy
     z konstrukcji (jedno miejsce aplikacji); stare zapisy DAG działają
     (węzeł jest ignorowany, schemat `LogicOperatorsParams` nadal go
     przyjmuje). Prostszy walidator i UI.
   * Koszt: utrata per-węzłowej konfiguracji `shift_periods` (1..10);
     wartość inna niż 1 była praktycznie nieużywana (default wszędzie = 1).
2. **Auto-shift z odczytem `shift_periods` z reliktowego węzła** — zachowuje
   konfigurowalność, ale utrzymuje ukrytą zależność od węzła, który ma
   zniknąć z UI; ryzyko regresji podwójnego shiftu wraca.
3. **Pozostawienie stanu obecnego** — sprzeczne z decyzją produktową.

## Decyzja

Opcja 1. Zakres zmian:

* **Silnik** (`opensource_engine.py`): bezwarunkowe
  `apply_time_shift(entries/exits, 1)` po `generate_signals()`; usunięta
  pętla po węzłach LogicOperators z `time_shift`.
* **Walidator** (`graph_parser.py`): usunięty check „Look-ahead Bias …
  wymaga węzła TimeShift"; `COMPATIBILITY_MATRIX` bez zmian (już wcześniej
  dopuszczała `Indicators → Execution`).
* **Frontend:** usunięte `TimeShiftNode.tsx`, przycisk toolbara, wpisy
  w `nodeTypes`/`NODE_TYPE_CATEGORY_MAP`/defaultach store'a i CSS;
  `signalNode` nie niesie już `operator_type`/`shift_periods`.
* **Schemat** `LogicOperatorsParams` pozostaje bez zmian (Literal z
  `time_shift` zostaje) — stare rekordy `Strategy`/`BacktestJob` w SQLite
  z zapisanym `operator_type: "time_shift"` dalej przechodzą walidację
  Pydantic przy odczycie; silnik po prostu na nie nie reaguje.

## Konsekwencje

* Prosty graf `Data → Indicator → Portfolio` jest teraz poprawny i wolny
  od look-ahead — inwariant egzekwuje silnik, nie użytkownik.
* Stare strategie z jawnym TimeShift dają **identyczny wynik** jak te bez
  niego (pinowane testem `test_legacy_time_shift_node_is_noop`).
* `shift_periods != 1` przestaje mieć jakikolwiek efekt — świadoma utrata
  funkcji; ewentualny globalny parametr przesunięcia może w przyszłości
  trafić do węzła Portfolio/ustawień silnika.
* Ścieżka legacy `run_backtest` nadal bez shiftu — odnotowane jako dług
  techniczny (nie regresja tej zmiany); ścieżką produktową jest DAG.
* Testy: `test_engine/test_auto_shift.py` (auto-shift bez węzła, no-op dla
  legacy `timeShiftNode` i `signalNode`), odwrócone testy walidatora
  (`test_graph_parser.py`, `test_dag_traps.py`).
