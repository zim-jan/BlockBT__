# Zarządzanie ryzykiem — Stop Loss / Take Profit / Sizing (Faza 12)

Faza 12 dodaje do węzła **Portfolio** (Execution) parametry zarządzania ryzykiem:
stop-loss, take-profit, trailing stop oraz kontrolę wielkości pozycji (sizing).
Parametry przekazywane są wprost do `vbt.Portfolio.from_signals`, bez własnej pętli
egzekucyjnej — silnik `vectorbt` (Numba/Rust) sam ewaluuje przebicie poziomu na
każdym barze.

## Parametry

| Parametr | Typ | Zakres | Domyślnie | Znaczenie |
|---|---|---|---|---|
| `sl_stop` | `float \| null` | `0.0`–`1.0` | `null` (wyłączony) | Stop-loss jako frakcja ceny wejścia. `0.05` = wyjście przy stracie 5%. |
| `tp_stop` | `float \| null` | `0.0`–`1.0` | `null` (wyłączony) | Take-profit jako frakcja ceny wejścia. `0.10` = wyjście przy zysku 10%. |
| `sl_trail` | `bool` | — | `false` | Gdy `true` i `sl_stop` ustawiony: stop-loss **trailing** — poziom podąża za maksimum ceny od wejścia (long) zamiast być zafiksowany na cenie wejścia. |
| `size` | `float \| null` | `> 0` | `null` (całość kapitału) | Wielkość pozycji na wejście, interpretowana wg `size_type`. |
| `size_type` | `"amount" \| "value" \| "percent"` | — | `"amount"` | Jednostka `size`: `amount` = liczba jednostek instrumentu, `value` = wartość pieniężna, `percent` = frakcja dostępnego kapitału. |

**Uwaga:** `sl_stop`/`tp_stop`/`size` są dokładane do wywołania `from_signals`
**tylko gdy ustawione** (nie `None`) — DAG bez tych pól działa dokładnie jak przed
Fazą 12 (pełna kompatybilność wsteczna z Fazami 10–11).

## Wymóg węzła Indicators

Od Fazy 12 DAG **musi** zawierać węzeł kategorii `Indicators` — bez źródła sygnału
(`entries`/`exits`) SL/TP nie ma na czym zadziałać (pozycja nigdy by się nie
otworzyła). Brak węzła Indicators → `GraphValidationError("DAG musi zawierać
węzeł Indicators.")` zamiast cichego pustego wyniku.

## Jak to działa (backend)

`OpenSourceEngine.execute_dag_portfolio` buduje `kwargs` dla `Portfolio.from_signals`
przyrostowo:

```python
kwargs: dict[str, Any] = {
    "close": price_data, "entries": entries, "exits": exits,
    "init_cash": init_cash, "fees": fees, "slippage": slippage, "freq": "D",
}
if sl_stop is not None:
    kwargs["sl_stop"] = float(sl_stop)
    kwargs["sl_trail"] = bool(params.get("sl_trail", False))
if tp_stop is not None:
    kwargs["tp_stop"] = float(tp_stop)
if size is not None:
    kwargs["size"] = float(size)
    kwargs["size_type"] = str(params.get("size_type", "amount"))
```

`vbt.Portfolio.from_signals` akceptuje `size_type` jako string wprost
(`"amount" | "value" | "percent"`) w vbt 1.0.0 — bez konwersji na enum.

### Surfacing liczby wyjść SL/TP

`vectorbt` **nie eksponuje** liczby wyjść typu Stop Loss / Take Profit w
`portfolio.stats()` ani w rekordach transakcji (`records_readable`) w sposób
niezależny od wersji — wewnętrzny enum `StopType` (`TP=2`) nie jest publicznym,
stabilnym API. Dlatego silnik **rekonstruuje** liczniki po fakcie:

`_classify_stop_exits` (wspólny rdzeń `_count_stop_exits` /
`_count_stop_exits_multi`) iteruje zamknięte transakcje
(`portfolio.trades.records_readable`) i klasyfikuje każdą po **warunku
uruchomienia stopu**: przy danych close-only vbt fill-uje każde wyjście (stop
i sygnał) na close bara, więc cena fill-a nie rozróżnia stopu od wyjścia
sygnałowego — rozróżnia je trigger, bo vbt sprawdza stopy na każdym barze
(close bara wyjścia za poziomem ⇔ stop zadziałał):

- **Long, Stop Loss:** `close_bara_wyjścia <= poziom`, gdzie poziom = `entry * (1 - sl_stop)`
  (dla `sl_trail=True` — od biegnącego ekstremum ceny w oknie pozycji),
- **Long, Take Profit:** `close_bara_wyjścia >= entry * (1 + tp_stop)`,
- **Short:** symetrycznie (znaki odwrócone).

Wynik trafia do `result["raw"]["Stop Loss Exits"]` / `["Take Profit Exits"]`
**tylko gdy dany stop był ustawiony** w węźle Execution; na gałęzi multi-symbol
(review 2026-07-15) liczniki są per symbol w zagnieżdżonym
`result["raw"][symbol][...]`. Runner kopiuje `raw` do payloadu jobu
(review 2026-07-16), więc liczniki są widoczne w `GET /api/backtest/{id}`
pod kluczem `metrics.raw`.

!!! note "Ograniczenie rezydualne"
    Sygnał exit na barze, którego close przekroczył poziom stopu, jest liczony
    jako stop (oba warunki spełnione naraz — rozstrzygnięcie deterministyczne).
    Dokładne etykiety dałyby dopiero rekordy `OHLCSTX`/`StopType` vbt, które
    wymagają pełnego OHLC w całym pipeline (patrz ADR-0003).

## Schema (`ExecutionParams`)

```python
class ExecutionParams(BaseModel):
    initialCapital: float = 10000.0
    init_cash: float = 10000.0
    fees: float = Field(default=0.001, gt=0.0)
    slippage: float = Field(default=0.001, gt=0.0)
    sl_stop: float | None = Field(default=None, ge=0.0, le=1.0)
    tp_stop: float | None = Field(default=None, ge=0.0, le=1.0)
    sl_trail: bool = False
    size: float | None = Field(default=None, gt=0.0)
    size_type: Literal["amount", "value", "percent"] = "amount"
```

## Jak z tego korzystać (UI)

W węźle **Portfolio** (Execution) dostępne są pola: **Stop Loss [%]**,
**Take Profit [%]**, **Trailing Stop** (checkbox), **Position Size** i **Size Type**.
UI operuje na procentach (np. `5` = 5%); przy zapisie do DAG JSON wartość jest
konwertowana na frakcję `0..1` (`5%` → `0.05`).

## Przykładowy DAG JSON

Minimalny DAG z SL 5% i TP 10% (wymaga węzła Indicators — tu: SMA crossover):

```json
{
  "nodes": [
    {
      "id": "d1",
      "category": "DataIngestion",
      "type": "dataNode",
      "params": { "symbol": "AAPL", "timeframe": "1d" }
    },
    {
      "id": "i1",
      "category": "Indicators",
      "type": "indicatorNode",
      "params": {
        "indicatorType": "sma_crossover",
        "smaFast": 10,
        "smaSlow": 30
      }
    },
    {
      "id": "p1",
      "category": "Execution",
      "type": "portfolioNode",
      "params": {
        "init_cash": 10000.0,
        "fees": 0.001,
        "slippage": 0.001,
        "sl_stop": 0.05,
        "tp_stop": 0.10,
        "sl_trail": false,
        "size": 100.0,
        "size_type": "amount"
      }
    }
  ],
  "edges": [
    { "source": "d1", "target": "i1" },
    { "source": "i1", "target": "p1" }
  ]
}
```

Wynik (`raw`) zawiera dodatkowo, jeśli stopy ustawione:

```json
{
  "raw": {
    "Stop Loss Exits": 2,
    "Take Profit Exits": 1
  }
}
```

## Powiązania

- ADR: [ADR-0003 Advanced Portfolio + Risk](../adr/0003-advanced-portfolio-risk.md).
- Kod: `backend/app/services/engine/opensource_engine.py`
  (`execute_dag_portfolio`, `run_dag_backtest`, `_count_stop_exits`).
- Schema: `backend/app/schemas/dag.py` (`ExecutionParams`).
- Frontend: `frontend/src/components/nodes/PortfolioNode.tsx`.
- Test: `backend/tests/test_engine/test_portfolio_risk.py`.
