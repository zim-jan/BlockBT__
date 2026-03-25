import numpy as np
import pandas as pd
import vectorbt as vbt
from blockbt.engine.optimizer import GridSearchOptimizer

np.random.seed(42)
price_df = pd.DataFrame({"close": np.random.normal(0, 1, 100).cumsum() + 100})

def sma_indicator(data, fast, slow):
    close = data["close"]
    fast_ma = vbt.MA.run(close, window=fast).ma
    slow_ma = vbt.MA.run(close, window=slow).ma
    entries = fast_ma.vbt.crossed_above(slow_ma)
    exits = fast_ma.vbt.crossed_below(slow_ma)
    return entries, exits

class DummyEngine:
    pass

optimizer = GridSearchOptimizer(engine=DummyEngine(), indicator_layer=sma_indicator)
result = optimizer.optimize(price_df, {"fast": [10, 20], "slow": [50, 100]}, metric='Total Return [%]')
print(result["best_params"])
print(result["best_metric_value"])
