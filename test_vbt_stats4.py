import numpy as np
import pandas as pd
import vectorbt as vbt

# Create dummy data
np.random.seed(42)
price = pd.Series(np.random.normal(0, 1, 100).cumsum() + 100)

fast = [10, 10, 20, 20]
slow = [50, 100, 50, 100]

fast_ma = vbt.MA.run(price, window=fast).ma
slow_ma = vbt.MA.run(price, window=slow).ma

entries = fast_ma.vbt.crossed_above(slow_ma)
exits = fast_ma.vbt.crossed_below(slow_ma)

portfolio = vbt.Portfolio.from_signals(price, entries=entries, exits=exits, freq="D")

# The column is a MultiIndex or tuple. We can use portfolio.stats(agg_func=None) maybe?
try:
    print(portfolio.stats(agg_func=None))
except Exception as e:
    print("Error with agg_func=None:", e)

# Or we can iterate over the integer columns?
metrics = []
for i in range(portfolio.wrapper.shape[1]):
    # Use `.iloc` wrapper to index portfolio columns
    port_c = portfolio.iloc[:, i]
    stats_c = port_c.stats()
    metrics.append(stats_c['Total Return [%]'])

print(metrics)
