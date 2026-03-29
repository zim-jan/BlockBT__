from blockbt.engine.opensource_engine import OpenSourceEngine
import pandas as pd
import numpy as np
import vectorbt as vbt

close = pd.Series(np.random.normal(0, 1, 100).cumsum() + 100)
engine = OpenSourceEngine()

params = {"sma_fast": [10, 10], "sma_slow": [50, 100]}
entries, exits = engine._build_entries_exits(close, params, vbt)
print(entries.shape)
