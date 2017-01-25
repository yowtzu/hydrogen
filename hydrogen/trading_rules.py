import pandas as pd
import numpy as np


def MACD(price: pd.DataFrame, vol: pd.DataFrame, short_window=32, long_window=128):
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

    return (price.ewm(span=short_window).mean() - price.ewm(span=long_window).mean()) / vol


def breakout(price: pd.DataFrame, window: int, span: int = None):
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

    roll_max = price.rolling(window=window).max()
    roll_min = price.rolling(window=window).min()
    roll_mean = 0.5 * (roll_max + roll_min)
    forecast = 40.0 * ((price - roll_mean) / (roll_max - roll_min))
    smooth_forecast = forecast.ewm(span=span, min_periods=min_periods).mean()

    return smooth_forecast


def long_only(price: pd.DataFrame, short_only: bool = False):
    """
    Long or short only

    :param price: the price level time series
    :type price: pd.DataFrame

    :param short_only: short instead
    :type short_only: bool

    :return forecast time series
    :rtype pd.DataFrame
    """

    avg_abs_forecast = price.copy()
    avg_abs_forecast[:] = -10.0 if short_only else 10.0

    return avg_abs_forecast
