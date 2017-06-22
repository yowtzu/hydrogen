import logging
import numpy as np
import pandas as pd
import hydrogen.system as system

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def vol(price_df: pd.DataFrame, annualised, method: str = 'YZ', **kwargs) -> pd.Series:
    """
    
    Args:
        price_df: OHLC(V) Price Data Frame with regular interval
        calc: The type of volatility calculation. At the moment, it supports SD, EWMA or ATR

    Returns:
        The volatility time series with the same length, with padded NA at the initial rows if necessary.

    """

    res = {
        'SD': _vol_std_dev,
        'ATR': _vol_atr,
        'RS': _vol_rs,
        'YZ': _vol_yz
    }.get(method)(price_df, **kwargs)

    if annualised:
        res *= system.root_n_bday_in_year

    return res


def _vol_std_dev(price_df: pd.DataFrame, ewm=False, **kwargs) -> pd.Series:
    price_df["CLOSE_PREV"] = price_df.CLOSE.shift(1)
    log_return = np.log(price_df.CLOSE / price_df.CLOSE_PREV)

    if ewm:
        res = log_return.ewm(**kwargs).std()
    else:
        res = log_return.rolling(**kwargs).std()

    return res


def _vol_atr(price_df: pd.DataFrame, ewm=False, **kwargs):
    price_df["CLOSE_PREV"] = price_df.CLOSE.shift(1)
    true_range_series = np.maximum(np.maximum(
        price_df.HIGH - price_df.LOW,
        np.abs(price_df.HIGH - price_df.CLOSE_PREV)),
        np.abs(price_df.CLOSE - price_df.CLOSE_PREV))

    if ewm:
        average_true_range_series = true_range_series.ewm(**kwargs).mean()  # i.e., span=27, alpha=1/14
    else:
        average_true_range_series = true_range_series.rolling(**kwargs).mean()  # i.e., span=27, alpha=1/14

    return average_true_range_series #/ price_df.CLOSE / 1.645


def _vol_rs(price_df: pd.DataFrame, ewm=False, **kwargs):
    a = np.log(price_df.HIGH / price_df.CLOSE) * np.log(price_df.HIGH / price_df.OPEN)
    b = np.log(price_df.LOW / price_df.CLOSE) * np.log(price_df.LOW / price_df.OPEN)

    if ewm:
        res = np.sqrt((a + b).ewm(**kwargs).mean())
    else:
        res = np.sqrt((a + b).rolling(**kwargs).mean())

    return res


def _vol_yz(price_df: pd.DataFrame, ewm=False, **kwargs):
    price_df["CLOSE_PREV"] = price_df.CLOSE.shift(1)

    rs_vol = _vol_rs(price_df, ewm, **kwargs)
    #rs_vol = _vol_rs(price_df, ewm, window=66)

    rs_var = rs_vol * rs_vol

    if ewm:
        overnight_var = np.log(price_df.OPEN / price_df.CLOSE_PREV).ewm(**kwargs).var()
        open_close_var = np.log(price_df.CLOSE / price_df.OPEN).ewm(**kwargs).var()
        window = kwargs['span']
    else:
        overnight_var = np.log(price_df.OPEN / price_df.CLOSE_PREV).rolling(**kwargs).var()
        open_close_var = np.log(price_df.CLOSE / price_df.OPEN).rolling(**kwargs).var()
        window = kwargs['window']

        #overnight_var = np.log(price_df.OPEN / price_df.CLOSE_PREV).rolling(window=66).var()
        #pen_close_var = np.log(price_df.CLOSE / price_df.OPEN).rolling(window=66).var()
        #window = 66

    k = 0.34 / (1.34 + (window + 1) / (window - 1))

    res =  np.sqrt(overnight_var + k * open_close_var + (1 - k) * rs_var)
    return res
