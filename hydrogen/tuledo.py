import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from hydrogen.instrument import Future, InstrumentFactory, Instrument
from hydrogen.portfolio import Portfolio
from hydrogen.portfoliooptimiser import Optimiser
from hydrogen.trading_rules import EWMAC, carry, breakout, long_only, signal_mixer, signal_clipper, signal_scalar, forecast_to_position
from hydrogen.portopt import port_opt
import hydrogen.system as system

TICKERS = [ "S 1 Comdty", "TY1 Comdty", "LH1 Comdty", "CL1 Comdty", "ES1 Index", "UX1 Index", "W 1 Comdty", 'Z 1 Index', "VG1 Index", "C 1 Comdty" ]

port = Portfolio('Test Portfolio')
port.set_instruments(TICKERS, as_of_date='20150701')
f = port.forecast()
f['S 1 Comdty'].ix[:, 3:7].plot()
f['S 1 Comdty'].abs().mean() # approx 10
f['S 1 Comdty'].isnull()["20060101":].sum() # should be zero

###################### forecast
ticker = port.ticker_instrument_map['TY1 Comdty']
ticker.unadjusted_ohlcv.CLOSE['20150101':].plot()
ticker._back_ohlcv_df.CLOSE['20150101':].plot()

ticker = port.ticker_instrument_map['S 1 Comdty']
(carry('carry_3m', inst=ticker, span=22))["201504"".plot()
(ticker.unadjusted_ohlcv.CLOSE["20160101":]-ticker._back_ohlcv_df.CLOSE["20160101":]).ewm(1).mean().plot()

(ticker.unadjusted_ohlcv.CLOSE["20160101":]-ticker._back_ohlcv_df.CLOSE["20160101":]).ewm(22).mean().plot()

ticker = port.ticker_instrument_map['CL1 Comdty']
signal_scalar(carry('carry_3m', inst=ticker, span=64)).plot()
ticker = port.ticker_instrument_map['TY1 Comdty']
signal_scalar(carry('carry_3m', inst=ticker)['20150101':].plot()

f['C 1 Comdty']['20150501':].ix[:,3:6].plot()
    .plot()
f['S 1 Comdty']["EWMAC_16_64"]['20150101':].plot()
ticker = port.ticker_instrument_map['C 1 Comdty']
ticker.unadjusted_ohlcv.CLOSE['20150101':].plot()
ticker.unadjusted_ohlcv.CLOSE.plot()

ticker._adj_info

opt = Optimiser('None')

x = port.forecast('C 1 Comdty')

ticker.ohlcv[:'20121203']
ticker.ohlcv.CLOSE.plot()
bla = x['TY1 Comdty']
port.pnl()['ES1 Index'].cumsum().plot()



bla
### missout cont size
cost_in_SR = pd.concat([ i.cost_in_SR for i in subset ], axis=1)

pd.concat([ i.daily_price_vol for i in subset ], axis=1)[:'20150701'].plot()
pd.concat([ i.unadjusted_ohlcv.CLOSE for i in subset ], axis=1)[:'20150701'].plot()

rules = [# (EWMAC, {"fast_span": 2, "slow_span": 8} ) ,
        #  (EWMAC, {"fast_span": 4, "slow_span": 16} ) ,
          (EWMAC, {"fast_span": 8, "slow_span": 32} ) ,
        #  (EWMAC, {"fast_span": 16, "slow_span": 64} ) ,
          (EWMAC, {"fast_span": 32, "slow_span": 128}),
          (EWMAC, {"fast_span": 64, "slow_span": 256})]
          #(carry, {"span":system.n_bday_in_3m}) ]

forecasts = [ rule(inst, **kargs) for rule, kargs in rules ]
scaled_forecasts = [ (signal_scalar(forecast)) for forecast in forecasts ]
forecasts_df = pd.concat(scaled_forecasts, axis=1)
forecasts_df.plot()


#### combine forecasts to forecast, based on the correlation and the return of each forecast
positions = forecasts_df.apply(lambda x: forecast_to_position(inst, x))
positions.plot()

##################

costs = positions.apply(lambda x: cost(inst, x))

scaled_forecasts.apply()

  ################################################

def position_to_return(inst: Instrument, position : pd.Series, include_cost: bool = True):
    cost_in_SR = inst.cost_in_SR
    if include_cost:
        cost = 2 * positions.diff().abs() * inst.tick_size * inst.cont_size
    return position * inst.unadjusted_ohlcv.CLOSE.diff() * inst.block_value - cost

returns = positions.apply(lambda x: position_to_return(inst, x))

returns.cumsum().plot()

positions[1].diff().abs()
returns.plot()

16*pnls.mean()/pnls.std()
pnls.cumsum().plot()

weights = port_opt(pnls, 'bootstrap', 'expanding', step=66)
weights = weights.asof(forecasts.index)
forecast_corr = forecasts.expanding().corr()
ww = np.vstack([ weights.ix[t,:].dot(forecast_corr[t,:,:]).dot(weights.ix[t,:].T) for t in np.arange(weights.shape[0])])
ww=pd.Series(ww[:,0], index=weights.index)
ww.plot()
weights*forecasts.mul(ww, axis=0)
single_forecast=((forecasts*weights).sum(axis=1)*ww)

single_position = forecast_to_position(inst, single_forecast).shift(1)
single_pnl = single_position.mul(inst.ohlcv.CLOSE.diff(1), axis=0).mul(inst.block_value, axis=0)
single_pnl.cumsum().plot()
16*single_pnl.mean()/single_pnl.std()




########################

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
