# Przewodnik: Wzorce Backtestingu (VectorBT + pandas-ta)

Wersja OpenSource BlockBT opiera się na elastyczności `pandas-ta` do generowania sygnałów oraz na szybkości `vectorbt` do symulacji portfela. Ten dokument pokazuje, jak pisać strategię, która będzie działać z naszym silnikiem.

## 🛠️ Cykl Życia Obliczeń

Kiedy użytkownik klika "Run", `OpenSourceEngine` wykonuje następujące kroki:
1. **Pobranie Danych**: Za pomocą konektora (np. Yahoo).
2. **Generowanie Sygnałów**: Przekształcenie cen OHLCV na binary series (True/False).
3. **Symulacja Portfolio**: Wywołanie `vbt.Portfolio.from_signals`.

## 🧬 Przykład: Sygnał z pandas-ta

`pandas-ta` integruje się bezpośrednio z DataFrame. Wewnątrz silnika robimy tak:

```python
import pandas_ta as ta

# Generowanie MACD
macd = df.ta.macd(fast=12, slow=26, signal=9)
# logiczne punkty wejścia (crossover)
entries = (macd['MACD_12_26_9'] > macd['MACDS_12_26_9']) & \
          (macd['MACD_12_26_9'].shift(1) <= macd['MACDS_12_26_9'].shift(1))
```

## 🚀 Uruchomienie VectorBT

Po wyznaczeniu serii `entries` (Kup) i `exits` (Sprzedaj), przekazujemy je do silnika:

```python
import vectorbt as vbt

pf = vbt.Portfolio.from_signals(
    df.close, 
    entries, 
    exits, 
    init_cash=10000,
    fees=0.001 # 0.1% prowizji
)

# Wyniki:
print(pf.total_return())
```

## 🔀 Translacja z Grafu (AST)

Wizualny Kreator przesyła nam listę połączeń. Nasz parser w `opensource_engine.py` musi "odwinąć" ten graf. 
- Jeśli węzeł to `SMA`, silnik wywołuje `df.ta.sma`.
- Jeśli węzeł to `CrossOver`, silnik porównuje dwie serie danych.
- Wynik końcowy zawsze musi być serią Boole'owską (True/False) akceptowalną przez `vectorbt`.

## 📉 Porada Wydajnościowa

- Unikaj pętli `for` po wierszach DataFrame. Zawsze używaj operacji wektorowych (Vectorization).
- Dane wejściowe OHLCV są normalizowane do małych liter (`open`, `high`, `low`, `close`, `volume`) przez bazową klasę konektora.

---
### Zobacz też:
- [opensource_engine.py](file:///home/przydan/my_project/src/blockbt/engine/opensource_engine.py) — serce logiki obliczeniowej.
