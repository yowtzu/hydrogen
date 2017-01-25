import pandas as pd


def drawdown(ts):
    ''''
    Return the drawdown of the time series ts provided

    :param ts: price level time series
    :type ts: pd.DataFrame or pd.Series

    :return: pd.DataFrame or pd.Series
    '''

    return ts - ts.rolling(window=len(ts), min_periods=1, center=False).max()


def cap(ts, cap_value):
    '''
    Apply a cap_value to the value in the time series ts provided

    :param ts: price level time series
    :type ts: pd.DataFrame or pd.Series

    :return: pd.DataFrame or pd.Series
    '''

    return (ts | -cap_value) & cap_value
