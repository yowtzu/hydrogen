import pandas as pd


def nearest_date_after(dates: pd.Series, pivot_date: pd.tslib.Timestamp):
    res = dates[pivot_date < dates]
    return res[0] if not res.empty else None


def nearest_date_before(dates: pd.Series, pivot_date: pd.tslib.Timestamp):
    res = dates[dates < pivot_date]
    return res.iloc[-1] if not res.empty else None
