import numpy as np
import pandas as pd
import vectorbt as vbt

# Create dummy data
np.random.seed(42)
price = pd.Series(np.random.normal(0, 1, 100).cumsum() + 100)

# Create combinations
fast = [10, 10, 20, 20]
slow = [50, 100, 50, 100]

fast_ma = vbt.MA.run(price, window=fast).ma
slow_ma = vbt.MA.run(price, window=slow).ma

entries = fast_ma.vbt.crossed_above(slow_ma)
exits = fast_ma.vbt.crossed_below(slow_ma)

portfolio = vbt.Portfolio.from_signals(price, entries=entries, exits=exits, freq="D")

print(portfolio.stats())
