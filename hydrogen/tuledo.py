import matplotlib.pyplot as plt
import hydrogen.analytics
import seaborn as sns
import numpy as np
import pandas as pd

from hydrogen.instrument import Future, InstrumentFactory
from hydrogen.trading_rules import EWMAC, carry, breakout, long_only, signal_mixer, signal_capper, signal_scalar



TICKERS = ["ED1 Comdty", "FV1 Comdty", "VG1 Comdty", "FVS1 Index", "MXNUSD Curncy", "C 1 Comdty"]
#TICKERS = ["VG1 Comdty"]

instrument_factory = InstrumentFactory()

instruments = { ticker:instrument_factory.create_instrument(ticker, as_of_date='20151230') for ticker in TICKERS }

inst = instruments["C 1 Comdty"]

signal = EWMAC(inst)
signal
res = signal_mixer(signal)
res
inst.ohlcv["20060401":]


x = signal["EWMAC_32_128"].to_frame()
x[400:].plot()
x
scale_signal(x)
x.mul(scale_signal(x), axis=0)[400:].plot()
    .plot()
scale_signal(signal["EWMAC_32_128"].to_frame().iloc[:, 300:]).plot()
s = carry(inst)

signal[2006:3000].plot()
(s/s.ewm(span=63).std())[300:].plot()
s.abs().median()
plt.plot(inst.ohlcv.CLOSE)
s.plot()
s = carry(inst)
s.mean()
s.hist()
signal[:"20151211"].plot()
ewmac8 = signal.ix[:,1].to_frame()
ewmac8.ewm(span=63).std()

b = ((ewmac8)/ewmac8.ewm(span=63).std())
b
10/b.abs().median()
[300:700].plot()
ewmac8.plot()
scale_signal(ewmac8)
plt.plot(ewmac8)
bla = ( (inst.ohlcv.CLOSE.ewm(span=8).mean() - inst.ohlcv.CLOSE.ewm(span=32).mean())/ inst.ohlcv.CLOSE.pct_change().ewm(span=25).std()  ) / inst.ohlcv.CLOSE
bla[:"20151211"]
scale_signal(ewmac8).ix[:"20151211"]

ewmac8.plot()
inst.ohlcv
inst.ohlcv.CLOSE.plot()
inst.ohlcv.CLOSE.ewm(span=63).mean().plot()
inst.ohlcv.CLOSE.ewm(span=63*2).mean().plot()
plt.plot()
plt.plot(signal.ix[:, 5], hold=False)
signal.ix[:,0].plot()
signal.abs().median()
signal.plot()
(signal.corr())


carry(inst, span=63, scale=False).plot()
carry(inst, span=63, scale=True).plot()
breakout(inst, window=50, span=20).median()
long_only(inst).plot()

print(inst.ccy)


def si