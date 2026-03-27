# Optimization Layer

W BlockBT warstwa optymalizacji pozwala na automatyczne znajdowanie optymalnych parametrów strategii finansowych za pomocą metody Grid Search (Przeszukiwanie siatki). Została ona zaimplementowana z naciskiem na maksymalną wydajność i wykorzystuje mechanizm wektoryzacji z darmowej wersji biblioteki `vectorbt`.

## Definiowanie siatki parametrów

Parametry do przetestowania definiuje się w formie słownika (`dict`), gdzie kluczem jest nazwa parametru, a wartością – lista (`list`) potencjalnych wartości do sprawdzenia.

Przykładowa siatka:
```python
param_grid = {
    "sma_fast": [10, 20, 30],
    "sma_slow": [50, 100, 200]
}
```

## Uruchamianie optymalizacji

Optymalizator `GridSearchOptimizer` funkcjonuje jako warstwa abstrakcji (wrapper) na istniejący silnik symulacyjny i warstwę wskaźników. Sam optymalizator wewnętrznie buduje iloczyn kartezjański przekazanych parametrów i generuje spłaszczone, precyzyjnie wyrównane wektory, które zostają w całości przekazane do wskaźników, unikając konieczności używania pętli w języku Python.

Poniżej znajduje się przykład, jak zintegrować i uruchomić optymalizację:

```python
import pandas as pd
from blockbt.engine.opensource_engine import OpenSourceEngine
from blockbt.engine.optimizer import GridSearchOptimizer

# 1. Przygotowanie danych historycznych (musi zawierać kolumnę "close")
data = pd.DataFrame({"close": [...]})

# 2. Definicja silnika wykonawczego
engine = OpenSourceEngine()

# 3. Definicja warstwy wskaźników
# Funkcja musi przyjmować data oraz przekazane parametry jako kwargs,
# a następnie zwracać tuplę wektorowych sygnałów (entries, exits)
def my_indicator_layer(data, **kwargs):
    import vectorbt as vbt
    close = data["close"]
    fast = kwargs.get("sma_fast", [10])
    slow = kwargs.get("sma_slow", [30])

    fast_ma = vbt.MA.run(close, window=fast).ma
    slow_ma = vbt.MA.run(close, window=slow).ma

    entries = fast_ma.vbt.crossed_above(slow_ma)
    exits = fast_ma.vbt.crossed_below(slow_ma)

    return entries, exits

# 4. Inicjalizacja optymalizatora
optimizer = GridSearchOptimizer(engine=engine, indicator_layer=my_indicator_layer)

# 5. Uruchomienie optymalizacji
result = optimizer.optimize(
    data=data,
    param_grid=param_grid,
    metric="Total Return [%]" # Metryka z vectorbt stats() używana do oceny
)

# 6. Wyniki
print("Najlepsze parametry:", result["best_params"])
print("Wartość metryki:", result["best_metric_value"])
print("Pełne statystyki:", result["stats"])
```

## Szczegóły implementacyjne

### Dlaczego płaskie listy (Złota zasada wektoryzacji)
Przekazywanie surowych zagnieżdżonych list parametrów (np. `fast=[10, 20]`, `slow=[50, 100]`) często prowadzi w Pandas/`vectorbt` do błędów dopasowania kształtu macierzy (ShapeError) lub konfliktów na wielopoziomowych indeksach (MultiIndex). Dlatego BlockBT w klasie `GridSearchOptimizer` wewnętrznie używa `itertools.product` w celu spłaszczenia wszystkich kombinacji w wektory równomierne. Pozwala to operować `vectorbt` na jednej płaskiej przestrzeni stanów na każdy wskaźnik, bez jakichkolwiek konfliktów.
