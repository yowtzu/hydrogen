import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def price_vol(price_df: pd.DataFrame, calc: str = 'SD', **kwrgs) -> pd.TimeSeries:
    """

    Args:
        price_df: OHLC(V) Price Data Frame with regular interval
        calc: The type of volatility calculation. At the moment, it supports SD, EWMA or ATR

    Returns:
        The volatility time series with the same length, with padded NA at the initial rows if necessary.
    """
    return {
        'SD': _vol_std_dev,
        'EWMA': _vol_ewma,
        'ATR': _vol_atr,
    }.get(calc)(price_df, **kwrgs)


def _vol_std_dev(price_df: pd.DataFrame, **kwrgs) -> pd.TimeSeries:
    return_ts = np.log(price_df.CLOSE).diff(period=1)
    vol_ts = pd.rolling_std(return_ts, **kwrgs)
    return np.dev(vol_ts)


def _vol_ewma(price_df: pd.DataFrame, **kwrgs) -> pd.TimeSeries:
    return_ts = np.log(price_df.CLOSE).diff(period=1)
    vol_ts = pd.ewmstd(return_ts, **kwrgs)
    return np.dev(vol_ts)


def _vol_atr(price_df: pd.DataFrame, **kwargs):
    true_range_series = np.maximum(np.maximum(
        price_df.HIGH - price_df.LOW,
        np.abs(price_df.HIGH - price_df.CLOSE_PREV)),
        np.abs(price_df.CLOSE - price_df.CLOSE_PREV))
    average_true_range_series = pd.ewma(true_range_series, **kwargs)  # i.e., span=27, alpha=1/14
    return average_true_range_series


def summary(df: pd.DataFrame, **kwargs):
    stats = df.describe()

    median = df.median()
    median.name = 'median'

    skew = df.skew()
    skew.name = 'skew'

    kurtosis = df.kurtosis()
    kurtosis.name = 'kurtosis'

    corr = df.corr()

    return stats.append(median).append(skew).append(kurtosis), corr


def bootstrap(price_df: pd.DataFrame, period=1):
    return_ts = np.log(price_df.CLOSE).diff(period=period)
    # sample from return_ts
