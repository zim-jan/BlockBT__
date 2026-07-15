# ADR-0005: Dynamic Introspection Engine + `GET /api/v1/registry`

- Status: Zaakceptowany
- Data: 2026-07-15
- Faza: 14

## Kontekst

Frontend (Visual Builder) potrzebuje maszynowo-czytelnego opisu dostępnych wskaźników i reguł
łączenia węzłów DAG, aby dynamicznie budować paletę węzłów i formularze parametrów bez twardego
kodowania po stronie UI. Jednocześnie istniejący `IndicatorRegistry`
(`backend/app/services/engine/indicator_registry.py`) rejestruje wskaźniki w semantyce surowego
vectorbt (`vbt_MA`, `vbt_RSI`, parametr `window`), co:

- nie odpowiada natywnej semantyce BlockBT (`SMA`/`MACD` z `fast_window`/`slow_window`/`signal_window`),
- jest zależne od dostępności i wersji vectorbt (ryzyko dla trybu Air-Gapped / BYOL),
- ma niedeterministyczny wynik `get_all()` (zależny od discovery talib/vbt).

Kontrakt Fazy 14 (`backend/tests/test_api/test_registry.py`) wymaga, aby
`GET /api/v1/registry/indicators` zwracał **surowy** dict z kluczami `SMA`, `MACD`, gdzie
`SMA.parameters` zawiera `fast_window`.

## Rozważane opcje

1. **Proxy dla `IndicatorRegistry.get_all()`.**
   - Zysk: brak nowego kodu katalogu.
   - Koszt: zła semantyka (`vbt_MA`/`window`), niedeterminizm, zależność od vbt/talib, ryzyko
     złamania kontraktu (brak `SMA`/`fast_window`). Modyfikacja `indicator_registry.py` groziłaby
     regresją zielonego baseline `test_engine/test_indicator_registry.py`.

2. **Kuratorowany, deterministyczny katalog jako źródło prawdy + opcjonalne wzbogacenie vbt.**
   - Zysk: deterministyczny, BYOL-safe, zgodny z kontraktem i semantyką BlockBT; niezależny od
     obecności vbt; baseline `IndicatorRegistry` pozostaje nietknięty.
   - Koszt: ręczne utrzymanie rdzenia katalogu (niewielki — 3 wskaźniki dziś).

3. **Pełna dynamiczna introspekcja tylko z vbt (parsowanie sygnatur).**
   - Zysk: „za darmo" duży katalog.
   - Koszt: niedeterminizm, kruchość (zmiany API vbt), ryzyko dla Air-Gapped, brak natywnej
     semantyki BlockBT — sprzeczne z kontraktem.

## Decyzja

Wybrano **opcję 2**. Powstaje nowy `backend/app/services/engine/introspection.py`:

- `build_indicator_catalog(vbt=None)` — zwraca kuratorowany rdzeń (`SMA`/`MACD`/`RSI`), a gdy
  `vbt` jest dostępny, best-effort wzbogaca katalog wpisami `vbt_*` (odczyt `param_names`,
  wszystko w `try/except`).
- `build_node_catalog()` — importuje `GraphParser.COMPATIBILITY_MATRIX` (jedno źródło prawdy)
  i zwraca kategorie węzłów oraz macierz kompatybilności.

Endpointy `GET /api/v1/registry/{indicators,nodes,/}` zwracają odpowiedzi **surowo** (bez koperty
`ApiResponse`). `IndicatorRegistry` **nie jest modyfikowany**. Montaż w `main.py` jest append-only
(pierwszy prefiks `/api/v1/` w repo).

## Konsekwencje

**Pozytywne:**

- Kontrakt spełniony niezależnie od dostępności vbt (`runner.vbt is None` → zwracany rdzeń).
- BYOL/Air-Gapped bezpieczne: brak `eval`/`exec`, tylko statyczne metadane; zero vectorbtpro.
- Baseline `test_indicator_registry.py` pozostaje zielony (brak zmian w `indicator_registry.py`).
- Frontend zyskuje stabilny, wersjonowany kontrakt `/api/v1/`.

**Negatywne / do pilnowania:**

- Rdzeń katalogu wymaga ręcznej aktualizacji przy dodaniu nowego natywnego wskaźnika.
- Dwa równoległe „rejestry" (kuratorowany katalog vs. wykonawczy `IndicatorRegistry`) — role są
  rozłączne (opis kontraktu vs. wykonanie), ale należy to udokumentować, by uniknąć pomyłek.
