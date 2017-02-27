import logging
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

'''' Some date constants '''

N_DAYS_IN_YEAR = 365.25
N_BDAYS_IN_YEAR = 252.0

ROOT_N_BDAYS_IN_YEAR = np.sqrt(N_BDAYS_IN_YEAR)

N_WEEKS_IN_YEAR = N_DAYS_IN_YEAR / 7.0
ROOT_N_WEEKS_IN_YEAR = np.sqrt(N_WEEKS_IN_YEAR)

N_MONTHS_IN_YEAR = 12.0
ROOT_N_MONTHS_IN_YEAR = np.sqrt(N_MONTHS_IN_YEAR)

EPOCH=pd.datetime(2000,1,1)

def nearest_date_after(dates: pd.Series, pivot_date: pd.tslib.Timestamp):
    res = dates[pivot_date < dates]
    return res[0] if not res.empty else None


def nearest_date_before(dates: pd.Series, pivot_date: pd.tslib.Timestamp):
    res = dates[dates < pivot_date]
    return res.iloc[-1] if not res.empty else None


def vol(price_df: pd.DataFrame, method: str = 'YZ', price_scale = True, annualised=False, **kwargs) -> pd.TimeSeries:
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
        'YZ':_vol_yz
    }.get(method)(price_df, **kwargs)

    if price_scale:
        res *= price_df.CLOSE

    if annualised:
        res *= ROOT_N_BDAYS_IN_YEAR

    return res

def _vol_std_dev(price_df: pd.DataFrame, ewm=False, **kwargs) -> pd.TimeSeries:
    price_df["CLOSE_PREV"] = price_df.CLOSE.shift(1)

    if ewm:
        res = np.log(price_df.CLOSE / price_df.CLOSE_PREV).ewm(**kwargs).std()
    else:
        res = np.log(price_df.CLOSE/price_df.CLOSE_PREV).rolling(**kwargs).std()

    return res

def _vol_atr(price_df: pd.DataFrame,  ewm=False, **kwargs):
    price_df["CLOSE_PREV"] = price_df.CLOSE.shift(1)

    true_range_series = np.maximum(np.maximum(
        price_df.HIGH - price_df.LOW,
        np.abs(price_df.HIGH - price_df.CLOSE_PREV)),
        np.abs(price_df.CLOSE - price_df.CLOSE_PREV))
    if ewm:
        average_true_range_series = true_range_series.ewm(**kwargs).mean()  # i.e., span=27, alpha=1/14
    else:
        average_true_range_series = true_range_series.rolling(**kwargs).mean()  # i.e., span=27, alpha=1/14

    return average_true_range_series / price_df.CLOSE / 1.645


def _vol_rs(price_df: pd.DataFrame, ewm=False, **kwargs):
    a = np.log(price_df.HIGH/price_df.CLOSE)*np.log(price_df.HIGH/price_df.OPEN)
    b = np.log(price_df.LOW/price_df.CLOSE)*np.log(price_df.LOW/price_df.OPEN)

    if ewm:
        res = np.sqrt((a + b).ewm(**kwargs).mean())
    else:
        res = np.sqrt((a + b).rolling(**kwargs).mean())

    return res


def _vol_yz(price_df: pd.DataFrame, ewm=False, **kwargs):
    price_df["CLOSE_PREV"] = price_df.CLOSE.shift(1)

    rs_vol = _vol_rs(price_df, ewm, **kwargs)
    rs_var = rs_vol*rs_vol

    if ewm:
        overnight_var = np.log(price_df.OPEN / price_df.CLOSE_PREV).ewm(**kwargs).var()
        open_close_var = np.log(price_df.CLOSE / price_df.OPEN).ewm(**kwargs).var()
        window = kwargs['span']
    else:
        overnight_var = np.log(price_df.OPEN / price_df.CLOSE_PREV).rolling(**kwargs).var()
        open_close_var = np.log(price_df.CLOSE / price_df.OPEN).rolling(**kwargs).var()
        window = kwargs['window']

    k = 0.34 / (1.34 + (window+1)/(window-1))

    return np.sqrt(overnight_var + k*open_close_var + (1-k)*rs_var)


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

