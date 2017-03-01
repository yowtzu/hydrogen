from hydrogen.instrument import Future
import matplotlib.pyplot as plt
import hydrogen.analytics
import hydrogen.trading_rules
import seaborn as sns
import numpy as np
import pandas as pd

cl1 = Future('CL1 Comdty')

hydrogen.trading_rules.EWMAC(cl1).plot()
hydrogen.trading_rules.carry(cl1, span=63).plot()
hydrogen.trading_rules.breakout(cl1, window=20, span=10).plot()
hydrogen.trading_rules.long_only(cl1).plot()

cl1 = Future('CL1 Comdty', as_of_date='20140801')

xx = pd.concat([cl1.ohlcv_unadjusted_df.CLOSE, cl1.back_ohlcv_df.CLOSE], axis=1)['20080701':'20111201']

