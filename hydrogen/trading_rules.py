import pandas as pd
import numpy as np
import hydrogen.analytics

def EWMAC(instrument: hydrogen.instrument.Future, fast_slow_span_pair=[(2, 8), (4, 16), (8, 32), (16, 34), (32, 128), (62, 256)]):
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
    ts_list = [ (instrument.ohlcv_df.CLOSE.ewm(span=fast_span).mean() - instrument.ohlcv_df.CLOSE.ewm(span=slow_span).mean()) / instrument.vol for fast_span, slow_span in fast_slow_span_pair ]
    df = pd.concat(ts_list, axis=1)
    df.columns = ['EWMAC_' + str(x) + '_' + str(y) for x, y in fast_slow_span_pair ]
    return df

def carry(instrument: hydrogen.instrument.Future, span=63):

    ts = instrument._calc_daily_yield().CLOSE / instrument.vol
    smooth_ts = ts.ewm(span = span).mean()
    return smooth_ts.to_frame('carry')

def breakout(instrument: hydrogen.instrument.Future, window: int, span: int = None):
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

    price = instrument.ohlcv_df.CLOSE
    roll_max = price.rolling(window=window).max()
    roll_min = price.rolling(window=window).min()
    roll_mean = 0.5 * (roll_max + roll_min)
    forecast = 40.0 * ((price - roll_mean) / (roll_max - roll_min))
    smooth_forecast = forecast.ewm(span=span, min_periods=min_periods).mean()

    return smooth_forecast.to_frame('breakout')


def long_only(instrument: hydrogen.instrument.Future):
    """
    Long or short only

    :param price: the price level time series
    :type price: pd.DataFrame

    :param short_only: short instead
    :type short_only: bool

    :return forecast time series
    :rtype pd.DataFrame
    """

    price = instrument.ohlcv_df.CLOSE
    avg_abs_forecast = price.copy()
    avg_abs_forecast[:] = 10.0

    return avg_abs_forecast.to_frame('long_only')
