import numpy as np
import pandas as pd

import hydrogen.analytics
from hydrogen.portopt import port_opt


def signal_scalar(signal: pd.DataFrame, target_abs_forecast=10):
    # cross sectional average
    if len(signal.columns) == 1:
        cross_sessional_avg = signal.ix[:, 0].abs()
    else:
        cross_sessional_avg = signal.abs().median(axis=1)

    # time series average
    scaling_factor = target_abs_forecast / cross_sessional_avg.expanding().mean()

    return signal.mul(scaling_factor, axis=1)

def signal_capper(signal: pd.DataFrame, lower_limit=-20, upper_limit=20):
    return signal.clip(lower=lower_limit, upper=upper_limit)

def signal_mixer(signal: pd.DataFrame):
    return port_opt(signal, 'bootstrap', 'expanding', use_standardise_vol=True, n_bootstrap_run=1024)

def EWMAC(instrument: hydrogen.instrument.Instrument, fast_slow_span_pair=[(2, 8), (4, 16), (8, 32), (16, 64), (32, 128), (64, 256)]):
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
    :rtype pd.DataFrame
    """
    ts_list = [ (instrument.ohlcv.CLOSE.ewm(span=fast_span).mean() - instrument.ohlcv.CLOSE.ewm(span=slow_span).mean()) / instrument.price_vol for fast_span, slow_span in fast_slow_span_pair ]
    signal = pd.concat(ts_list, axis=1)
    signal.columns = ['EWMAC_' + str(x) + '_' + str(y) for x, y in fast_slow_span_pair ]

    return signal

def carry(instrument: hydrogen.instrument.Instrument, span=63):

    ts = instrument._calc_daily_yield().CLOSE / instrument.vol
    signal = ts.ewm(span = span).mean().to_frame('carry')

    return signal


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

    return smooth_forecast.to_frame('breakout')


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

    return avg_abs_forecast.to_frame('long_only')
