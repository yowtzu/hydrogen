from hydrogen.instrument import Future
import matplotlib.pyplot as plt
import hydrogen.analytics

VOL_WINDOW_SIZE= 21

cl1 = Future('CL1 Comdty')
ohlcv = cl1.ohlcv(cl1.get_adj_dates(-1), method='panama')[0]
plt.plot(ohlcv["2013":"20141125"].CLOSE)

bla = hydrogen.analytics.vol(ohlcv, method='YZ', window=VOL_WINDOW_SIZE)
