from collections import OrderedDict
import numpy as np
import pandas as pd
import hydrogen.system as system
import hydrogen.analytics
from hydrogen.portopt import port_opt
from hydrogen.instrument import Instrument

def EWMAC(rulename: str, inst: Instrument, fast_span, slow_span):#w_span_pair=[(2, 8), (4, 16), (8, 32), (16, 64), (32, 128), (64, 256)]):
    """
    :param price: the price level time series
    :type price: pd.DataFrame

    :param vol: the vol of the price level time series
    :type vol: pd.DataFrame

    :param short_window: the short lookup window size
    :type short_window: int

    :param long_window : the long lookup window size
    :type long_window: int

    :return forecast time series
    :rtype pd.Series
    """

    signal = (inst.ohlcv.CLOSE.ewm(span=fast_span).mean() - inst.ohlcv.CLOSE.ewm(span=slow_span).mean()) / (inst.daily_price_vol * inst.ohlcv.CLOSE)
    #signal = signal.rename('S_EWMAC_{fast}_{slow}'.format(fast_span, slow_span))
    signal = signal.rename(rulename)
    return signal


def carry(rulename: str, inst: Instrument, span):
    signal = (inst.calc_annual_yield())
    signal = signal.ewm(span=span).mean()
    signal = signal.rename(rulename)
    return signal


def signal_scalar(signal: pd.Series, target_abs_forecast=system.target_abs_forecast):
    """
    
    :param signal: the input signal to be scaled with to scale with median(abs(signal)) = target_abs_forecast 
    :param target_abs_forecast: scalar 
    :return: pd.Series
    """
    # time series average
    scaling_factor = target_abs_forecast / signal.abs().ewm(span=system.n_bday_in_year).mean()
    signal = scaling_factor * signal
    return signal

def signal_clipper(signal: pd.Series, lower_limit=-20, upper_limit=20):
    """
    
    :param signal: clip the signal to be  with [lower_limit, upper_limit]
    :param lower_limit: scalar
    :param upper_limit: scalr
    :return: pd.Series
    """
    return signal.clip(lower=lower_limit, upper=upper_limit)

def forecast_to_position(inst: Instrument, forecast: pd.Series):
    volatility_scalar = system.vol_target_cash_daily / inst.instrument_value_vol
    position = forecast * volatility_scalar / system.avg_abs_forecast
    position = position.rename('P_%s'.format(forecast))
    return position

def turnover(series:pd.Series):
    ratios = series.diff().abs() / series.abs().rolling(window=system.n_bday_in_3m).mean() * system.n_bday_in_year
    return ratios

def cost_turnover(turnover: pd.Series, inst:Instrument):
    return turnover*inst.cost_in_SR

def bla(inst: Instrument, position: pd.Series):
    ''' Number of trade block per year / ( 2 * average absolute number of blocks held ) '''

    no_trade_per_year = position.ffill().diff().abs().rolling(window=system.n_bday_in_3m).sum() * 4
    avg_abs_no_trade = position.abs().rolling(window=system.n_bday_in_3m).sum() * 4
    # no_trade_per_year = positions.ffill().diff().abs()
    # avg_abs_no_trade = positions.abs()
    t = no_trade_per_year / avg_abs_no_trade
    # print(t.sum())
    return t

def signal_mixer(signal: pd.DataFrame):
    return port_opt(signal, 'bootstrap', 'expanding', use_standardise_vol=True, n_bootstrap_run=1024)


def breakout(instrument: hydrogen.instrument.Instrument, window: int, span: int = None):
    """
    :param price: the price level time series
    :type price: pd.DataFrame

    :param window: window size to look back
    :type window: int

    :param span : smoothing windows parameter
    :type span: int

    :return forecast time series
    :rtype pd.DataFrame
    """

    assert span < window

    if span is None:
        span = max(int(window / 4.0, 1))

    assert (span < window)

    min_periods = np.ceil(span / 2.0)

    price = instrument.ohlcv.CLOSE
    roll_max = price.rolling(window=window).max()
    roll_min = price.rolling(window=window).min()
    roll_mean = 0.5 * (roll_max + roll_min)
    forecast = 40.0 * ((price - roll_mean) / (roll_max - roll_min))
    smooth_forecast = forecast.ewm(span=span, min_periods=min_periods).mean()

    return smooth_forecast


def long_only(instrument: hydrogen.instrument.Instrument):
    """
    Long or short only

    :param price: the price level time series
    :type price: pd.DataFrame

    :param short_only: short instead
    :type short_only: bool

    :return forecast time series
    :rtype pd.DataFrame
    """

    price = instrument.ohlcv.CLOSE
    avg_abs_forecast = price.copy()
    avg_abs_forecast[:] = 10.0

    return avg_abs_forecast
