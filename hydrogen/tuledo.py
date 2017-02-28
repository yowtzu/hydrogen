from hydrogen.instrument import Future
import matplotlib.pyplot as plt
import hydrogen.analytics
import hydrogen.trading_rules

VOL_WINDOW_SIZE= 21

cl1 = Future('JPY 1 Index')
ohlcv = cl1.ohlcv(cl1.get_adj_dates(-1), method='panama')[0]
plt.plot(ohlcv["2013":"20141125"].CLOSE)

bla = hydrogen.analytics.vol(ohlcv, method='YZ', window=VOL_WINDOW_SIZE)

ohlcv.CLOSE["20080701":"20090701"].plot()
ohlcv.CLOSE.ewm(span=16).mean()["20080701":"20090701"].plot()
ohlcv.CLOSE.ewm(span=64).mean()["20080701":"20090701"].plot()

cl1.carry().plot()
hydrogen.trading_rules.MACD(ohlcv.CLOSE, 16, 32)["20080701":"20090701"].plot()
