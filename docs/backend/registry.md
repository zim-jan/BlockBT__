# Rejestr introspekcji (Dynamic Introspection Engine) — Faza 14

Moduł udostępnia **deterministyczny, BYOL-safe katalog** wskaźników oraz kategorii węzłów DAG
poprzez endpointy `GET /api/v1/registry/*`. Służy frontendowi (Visual Builder) do dynamicznego
budowania palety węzłów i formularzy parametrów bez twardego kodowania po stronie UI.

## Zasady architektoniczne

1. **Kuratorowany katalog jako źródło prawdy.** Rdzeń (`SMA`, `MACD`, `RSI`) używa natywnej
   semantyki BlockBT (`fast_window`, `slow_window`, `signal_window`, `window`), a nie surowej
   semantyki `vbt.MA` (parametr `window`). Katalog nie jest proxy dla `IndicatorRegistry.get_all()`.
2. **Żywa introspekcja vectorbt jest opcjonalna.** Wpisy wzbogacone trafiają pod prefiks `vbt_*`
   i są w pełni owinięte w `try/except`. Brak vbt (`runner.vbt is None`) nie psuje odpowiedzi —
   zwracany jest sam rdzeń kuratorowany.
3. **Jedno źródło macierzy kompatybilności.** Kategorie węzłów i `compatibility_matrix` pochodzą
   bezpośrednio z `GraphParser.COMPATIBILITY_MATRIX` (bez duplikacji logiki).
4. **Budowa leniwa.** Katalog jest budowany w handlerze żądania, nie przy imporcie modułu.

## Endpointy

| Metoda | Ścieżka | `response_model` | Kształt odpowiedzi |
|---|---|---|---|
| GET | `/api/v1/registry/indicators` | `dict[str, IndicatorSpec]` | surowy dict: `nazwa -> spec` |
| GET | `/api/v1/registry/nodes` | `dict[str, NodeCategorySpec]` | surowy dict: `kategoria -> spec` |
| GET | `/api/v1/registry/` | `RegistrySnapshot` | pełny zrzut rejestru |

Odpowiedzi są **surowe** — nie owinięte w kopertę `ApiResponse{success,data,error}`. Klucze
top-level odpowiedzi `/indicators` to nazwy wskaźników (np. `SMA`, `MACD`, `RSI`).

### Przykład: `GET /api/v1/registry/indicators`

```json
{
  "SMA": {
    "name": "SMA",
    "library": "blockbt",
    "parameters": {
      "fast_window": {"type": "int", "default": 10, "min": 1, "max": null, "options": null},
      "slow_window": {"type": "int", "default": 30, "min": 1, "max": null, "options": null}
    }
  },
  "MACD": {
    "name": "MACD",
    "library": "blockbt",
    "parameters": {
      "fast_window": {"type": "int", "default": 12, "min": 1},
      "slow_window": {"type": "int", "default": 26, "min": 1},
      "signal_window": {"type": "int", "default": 9, "min": 1}
    }
  },
  "RSI": {
    "name": "RSI",
    "library": "blockbt",
    "parameters": {"window": {"type": "int", "default": 14, "min": 1}}
  }
}
```

## Schematy

- `ParameterSpec` — `type`, `default`, opcjonalne `min`/`max`/`options`.
- `IndicatorSpec` — `name`, `library`, `parameters: dict[str, ParameterSpec]`.
- `NodeCategorySpec` — `category`, `allowed_targets`.
- `RegistrySnapshot` — `indicators`, `node_categories`, `compatibility_matrix`.

## Bezpieczeństwo (BYOL / Air-Gapped)

- Introspekcja odczytuje wyłącznie **statyczne metadane** (`param_names` fabryk vbt). Brak
  `eval`/`exec` i brak wykonywania kodu na danych zewnętrznych.
- Zero odwołań do vectorbtpro — katalog rdzeniowy jest niezależny od jakiejkolwiek biblioteki
  komercyjnej.
- `try/except` wokół wzbogacenia loguje na poziomie `debug` i nie połyka błędów krytycznych
  z rdzenia (rdzeń nie jest owinięty defensywnie — jego niepowodzenie musi być widoczne).

Szczegóły decyzji: [ADR-0005](../adr/0005-dynamic-introspection-registry.md).
