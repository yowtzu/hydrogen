import matplotlib.pyplot as plt
import hydrogen.system as system
import seaborn as sns
import numpy as np
import pandas as pd
from hydrogen.instrument import Future, InstrumentFactory, Instrument
from hydrogen.trading_rules import EWMAC, carry, breakout, long_only, signal_mixer, signal_capper, signal_scalar

TICKERS = ["TY1 Comdty", "FV1 Comdty", "VG1 Comdty", "FVS1 Index", "MXNUSD Curncy", "C 1 Comdty"]

instrument_factory = InstrumentFactory()

instruments = { ticker:instrument_factory.create_instrument(ticker, as_of_date='20161111') for ticker in TICKERS }

inst = instruments["C 1 Comdty"]


def forecast_to_position(inst: Instrument, forecast: pd.Series):
    volatility_scalar = system.vol_target_cash_daily / inst.instrument_value_vol
    return forecast * volatility_scalar / system.avg_abs_forecast

rules = [ (EWMAC, {"fast_span": 2, "slow_span": 8} ) ,
          (EWMAC, {"fast_span": 4, "slow_span": 16} ) ,
          (EWMAC, {"fast_span": 8, "slow_span": 32} ) ,
          (EWMAC, {"fast_span": 16, "slow_span": 64} ) ,
          (EWMAC, {"fast_span": 32, "slow_span": 128}),
          (EWMAC, {"fast_span": 64, "slow_span": 256}),
          (carry, {})]

forecasts = [ signal_scalar(rule(inst, **kargs)) for rule, kargs in rules ]
(forecasts[6]/9).plot()

inst._adj_dates
inst.ohlcv
import hydrogen.analytics
import hydrogen.system as s
inst._adj_dates
inst._back_ohlcv_df.CLOSE
pd.concat([inst._unadjusted_ohlcv.CLOSE, inst._back_ohlcv_df.CLOSE], axis=1)
((inst._back_ohlcv_df.CLOSE-inst._unadjusted_ohlcv.CLOSE).ewm(22).mean()*0.25).plot()
inst._back_ohlcv_df.CLOSE.plot()

inst._back_ohlcv_df.CLOSE
inst._adj_dates
    ohlcv.CLOSE.plot()

((inst.ohlcv.CLOSE.ewm(span=64).mean() - inst.ohlcv.CLOSE.ewm(span=256).mean())/hydrogen.analytics.vol(inst.ohlcv, method='YZ', window=63, price_scale=True, annualised=False)).plot()
pnls = forecasts
#positions = [ forecast_to_position(inst, forecast) for forecast in forecasts ]
(forecasts[6])['2008-01-01':].plot()
def position_to_return(inst: Instrument, position: pd.Series):
    return position.shift(1) * inst.ohlcv.CLOSE.diff(1)

pnls = [ position_to_return(inst, position) for position in positions ]
daily_df = pd.concat(pnls, axis=1)
daily_df.plot()

from hydrogen.portopt import port_opt
weights = port_opt(daily_df, 'bootstrap', 'expanding')
weights.plot()

weights_filled = weights.asof(daily_df.index)
portfolio_pnl = (weights_filled * daily_df).sum(axis=1)
portfolio_pnl.cumsum().plot()


diversification_multiplier = pd.Series(np.diag(1/np.array(weights_filled).dot(daily_df.corr()).dot(np.array(weights_filled.T))), index=weights_filled.index)

combined = weights_filled.mul(diversification_multiplier, axis=0)*pd.concat(forecasts, axis=1)
combined_forecast = combined.sum(axis=1)

combined_position = forecast_to_position(inst, combined_forecast)

pnl= position_to_return(inst, combined_position)
pnl.cumsum().plot()

# now I need to it for many instruments

# then portfolio optimisation

# then including cost

#########################################
pnl.cumsum().plot()

##############################################################

##############################################################

signal[:"20151211"].plot()
ewmac8 = signal.ix[:,1].to_frame()
ewmac8.ewm(span=63).std()

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
