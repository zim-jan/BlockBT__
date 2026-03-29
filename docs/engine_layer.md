# Warstwa Silnika (Engine Layer)

Ten dokument opisuje warstwę silnika w systemie BlockBT, przygotowaną zgodnie z założeniami MVP oraz architekturą "Dual-Engine Ready".

## Inicjalizacja silnika

System BlockBT wykorzystuje wzorzec Factory/Adapter do wyboru odpowiedniego silnika backtestingu. Za ładowanie odpowiedniego silnika odpowiada klasa `EngineLoader` (`backend/app/services/engine/loader.py`).

```python
from blockbt.engine.loader import EngineLoader

# Załadowanie odpowiedniego silnika (wersja OpenSource dla MVP)
engine = EngineLoader.load(force_opensource=True)
```

Silnik implementuje abstrakcyjny interfejs `BaseStrategyEngine`, z główną metodą do uruchamiania backtestów:
```python
def run_backtest(self, data: pd.DataFrame, params: dict[str, Any]) -> dict[str, Any]:
    ...
```

Zgodnie z wymogami MVP, metoda `run_backtest` zwraca znormalizowany słownik (`dict`) zawierający podstawowe metryki, takie jak m.in. `total_return_pct`, `sharpe_ratio`, `max_drawdown_pct`, `num_trades` oraz krzywą kapitału w postaci obiektu `pd.Series`.

## Przekazywanie Danych i Wskaźniki

Zanim wywołany zostanie backtest, do metody `run_backtest` należy przekazać obiekt `pandas.DataFrame` reprezentujący świece OHLCV (open, high, low, close, volume) oraz słownik `params` przechowujący parametry konfiguracyjne ze stanu `wizard_state`.

Silnik współpracuje z `IndicatorService`, który na podstawie dostarczonego szeregu cen zamknięcia (close) oraz parametrów, generuje wektory z sygnałami wejścia (entries) i wyjścia (exits). W ramach MVP, logikę dla tych sygnałów bazuje na przecinaniu się dwóch średnich kroczących (SMA Cross), wykorzystując wyłącznie darmową wersję biblioteki `vectorbt`.

```python
import pandas as pd

# 1. Pobierz lub wygeneruj dane OHLCV
ohlcv_data = pd.DataFrame(...)

# 2. Skonfiguruj parametry strategii
params = {
    "initial_capital": 10000.0,
    "sma_fast": 10,
    "sma_slow": 30
}

# 3. Uruchom backtest
result_dict = engine.run_backtest(ohlcv_data, params)

print("Zwrot całkowity (%):", result_dict["total_return_pct"])
```
