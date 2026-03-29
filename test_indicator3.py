import pandas as pd
import numpy as np
import pandas_ta as ta

close = pd.Series(np.random.normal(0, 1, 100).cumsum() + 100)
try:
    macd_df = ta.macd(close, fast=[12, 12], slow=[26, 26], signal=[9, 9])
    print(macd_df)
except Exception as e:
    print(e)
