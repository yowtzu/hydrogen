import numpy as np
import pandas as pd


'''' Some date constants '''

N_DAYS_IN_YEAR = 365.25

N_BDAYS_IN_YEAR = 256.0
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
