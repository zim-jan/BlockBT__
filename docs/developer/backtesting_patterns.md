# Przewodnik: Wzorce Backtestingu (VectorBT)

Wersja OpenSource BlockBT opiera się na wydajności `vectorbt` do generowania sygnałów i symulacji portfela. Ten dokument pokazuje, jak pisać strategię, która będzie działać z naszym silnikiem.

## 🛠️ Cykl Życia Obliczeń

Kiedy proces zleca "Run" (`OpenSourceEngine`), silnik wykonuje następujące kroki:
1. **Pobranie Danych**: Za pomocą konektora (np. Yahoo Finance).
2. **Generowanie Sygnałów**: Wykorzystanie metod wektorowych (np. `vbt.MA.run`).
3. **Symulacja Portfolio**: Wywołanie `vbt.Portfolio.from_signals`.

## 🧬 Przykład: Sygnał przy użyciu vectorbt

Aby stworzyć symulację dla np. MACD w `vectorbt`, tworzymy kalkulacje wektorowe bezpośrednio:

```python
import vectorbt as vbt

# Generowanie MACD w jednym kroku z DataFrame
macd = vbt.MACD.run(df['close'], fast_window=12, slow_window=26, signal_window=9)

macd_line = macd.macd
sig_line = macd.signal

# Wyznaczenie punktów wejścia i wyjścia
entries = macd_line.vbt.crossed_above(sig_line)
exits = macd_line.vbt.crossed_below(sig_line)
```

## 🚀 Uruchomienie VectorBT

Po wyznaczeniu serii `entries` (Kup) i `exits` (Sprzedaj), przekazujemy je do silnika portfela:

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

## 📉 Porada Wydajnościowa

- Unikaj pętli `for` po wierszach DataFrame. Zawsze używaj operacji wektorowych (Vectorization).
- Dane wejściowe OHLCV są normalizowane do małych liter (`open`, `high`, `low`, `close`, `volume`) przez bazową klasę konektora.
- Wykorzystuj metody `.vbt.crossed_above()` lub iteruj za pomocą `itertools.product` przy siatkach optymalizacyjnych.

---
### Zobacz też:
- `opensource_engine.py` — serce logiki obliczeniowej.
