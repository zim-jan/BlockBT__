import pandas as pd
import numpy as np
import vectorbt as vbt

close = pd.Series(np.random.normal(0, 1, 100).cumsum() + 100)
try:
    macd = vbt.MACD.run(close, fast_window=[12, 12], slow_window=[26, 26], signal_window=[9, 9])
    print(macd.macd.shape)
except Exception as e:
    print(e)
