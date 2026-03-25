from blockbt.engine.opensource_engine import OpenSourceEngine
import pandas as pd
import numpy as np
import vectorbt as vbt

close = pd.Series(np.random.normal(0, 1, 100).cumsum() + 100)
engine = OpenSourceEngine()

params = {"strategy_type": "macd", "macd_fast": [12, 12], "macd_slow": [26, 26], "macd_signal": [9, 9]}
entries, exits = engine._build_entries_exits(close, params, vbt)
print(entries.shape)
