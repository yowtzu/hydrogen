import logging
import numpy as np
import pandas as pd
import os
import re
import settings
from pandas.tseries.offsets import BDay
import hydrogen.analytics

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class InstrumentFactory():
    def create_instrument(self, ticker:str):
        prefix, suffix = ticker.rsplit(" ", maxsplit=1)
        class_map = {"Curncy": FX,
                     "Comdty": Future,
                     "Index": Future,
                     }
        return class_map[suffix](ticker)

class Instrument:

    def __init__(self, ticker: str, as_of_date):
        self.ticker = ticker
        self.as_of_date = as_of_date

    def __repr__(self):
        return str(self.__class__) + ":" + self.ticker + " as of " + str(self.as_of_date)

class FX(Instrument):
    _STATIC_FULL_PATH = os.path.join(settings.PROJECT_ROOT, 'data\static.csv')
    _OHLCV_PATH = os.path.join(settings.PROJECT_ROOT, 'data\ohlcv')
    _BBG_FIELD_MAP = {'PX_OPEN': 'OPEN', 'PX_LOW': 'LOW', 'PX_HIGH': 'HIGH', 'PX_LAST': 'CLOSE', 'PX_VOLUME': 'VOLUME'}

    def _read_ohlcv(self, start_date, end_date):
        ohlcv_df = pd.DataFrame()

        filename = os.path.join(Future._OHLCV_PATH, self.ticker + '.csv')
        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._BBG_FIELD_MAP)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)
            ohlcv_df = ohlcv_df[start_date:end_date]
            # only see data up to t-1 from as of date (inclusively)
            ohlcv_df = ohlcv_df[:self.as_of_date]

        return ohlcv_df

    def close_price(self):
        return self._read_ohlcv.CLOSE

class Future(Instrument):
    _STATIC_FULL_PATH = os.path.join(settings.PROJECT_ROOT, 'data\static.csv')
    _OHLCV_PATH = os.path.join(settings.PROJECT_ROOT, 'data\ohlcv')
    _BBG_FIELD_MAP = {'PX_OPEN': 'OPEN', 'PX_LOW': 'LOW', 'PX_HIGH': 'HIGH', 'PX_LAST': 'CLOSE', 'PX_VOLUME': 'VOLUME',
                      'FUT_NOTICE_FIRST': 'FUT_NOTICE_FIRST', }

    def __init__(self, ticker: str, as_of_date=pd.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)):
        super().__init__(ticker, as_of_date)
        self._ticker_pattern = self._resolve_ticker(ticker)
        self.static_df = self._read_static_csv(self._ticker_pattern)
        self.cont_size = self.static_df.FUT_CONT_SIZE.values[0]
        self.tick_size = self.static_df.FUT_TICK_SIZE.values[0]

        self.adj_dates = self.get_adj_dates(n_day=0)
        self.ohlcv_unadjusted_df = self.ohlcv(self.adj_dates, method='no_adj')[0]
        self.ohlcv_df = self.ohlcv(self.adj_dates, method='panama')[0]

        back_adj_dates = self.adj_dates.copy()[:-1]
        back_adj_dates.TICKER = back_adj_dates.NEXT_TICKER
        self.back_ohlcv_df = self.ohlcv(back_adj_dates, method='no_adj')[0]

        self.vol = hydrogen.analytics.vol(self.ohlcv_df, method='YZ', window=63, price_scale=True, annualised=False)

        self.n_day_btw_contracts = self.adj_dates.END_DATE[self.adj_dates.END_DATE > self.ohlcv_df.index[-1]][:2].diff().iloc[1].days

    def _resolve_ticker(self, ticker: str):
        prefix, suffix = ticker.rsplit(" ", maxsplit=1)
        regexp_double_digit = re.compile(r'[0-1][0-9]')
        # if it is format like ESH13 Index
        if regexp_double_digit.search(prefix[-2:]):
            return ticker
        else:
            # relative: return a sorted list of tickers prior to the as of dates
            return prefix[:-1] + "[A-Z][0-9]+ " + suffix

    def ticker_list(self):
        return self.static_df.TICKER.values.copy()

    def _read_static_csv(self, ticker_patterns):
        static_df = pd.read_csv(Future._STATIC_FULL_PATH).rename(columns=self._BBG_FIELD_MAP)
        static_df.FUT_NOTICE_FIRST = pd.to_datetime(static_df.FUT_NOTICE_FIRST)
        static_df = static_df[static_df.TICKER.str.contains(ticker_patterns)]
        static_df = static_df.sort_values(by='FUT_NOTICE_FIRST')

        return static_df

    def _read_ohlcv(self, ticker, start_date, end_date):
        ohlcv_df = pd.DataFrame()

        filename = os.path.join(Future._OHLCV_PATH, ticker + '.csv')
        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._BBG_FIELD_MAP)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)
            ohlcv_df = ohlcv_df[start_date:end_date]
            # only see data up to t-1 from as of date (inclusively)
            ohlcv_df = ohlcv_df[:self.as_of_date]
            ohlcv_df = ohlcv_df[ohlcv_df.HIGH.notnull() & ohlcv_df.LOW.notnull() & ohlcv_df.VOLUME.notnull()]

        return ohlcv_df

    def get_adj_dates(self, n_day=-1):
        roll_dates = self.static_df[["TICKER", "FUT_NOTICE_FIRST"]].copy()
        roll_dates['START_DATE'] = roll_dates.FUT_NOTICE_FIRST.shift(1).fillna(pd.tslib.Timestamp.min)
        roll_dates['END_DATE'] = roll_dates.FUT_NOTICE_FIRST.apply(lambda x: x + n_day * BDay())
        roll_dates['NEXT_TICKER'] = roll_dates.TICKER.shift(-1).fillna('')
        return roll_dates

    def ohlcv(self, adj_dates: pd.DataFrame = None, method='panama'):

        if method not in ['ratio', 'panama', 'no_adj']:
            raise ValueError('method is not valid: ' + method)

        if not isinstance(adj_dates, pd.DataFrame):
            raise ValueError('Calendar must be pandas DataFrame')

        df = pd.concat([self._read_ohlcv(row.TICKER, row.START_DATE, row.END_DATE)
                        for _, row in adj_dates.iterrows()])
        close = df.CLOSE

        next_df = pd.concat([self._read_ohlcv(row.NEXT_TICKER, row.END_DATE, row.END_DATE)
                         for _, row in adj_dates.iterrows()])
        next_close = next_df.CLOSE

        if method == 'panama':
            adj = (next_close - close.asof(next_close.index))
            adj = adj[::-1].cumsum()[::-1].reindex(df.index, method='bfill').fillna(0)
            df.OPEN = (df.OPEN + adj)
            df.HIGH = (df.HIGH + adj)
            df.LOW = (df.LOW + adj)
            df.CLOSE = (df.CLOSE + adj)
        elif method == 'ratio':
            adj = (next_close / close.asof(next_close.index))
            adj = adj[::-1].cumprod()[::-1].reindex(df.index, method='bfill').fillna(1)
            df.OPEN = (df.OPEN * adj)
            df.HIGH = (df.HIGH * adj)
            df.LOW = (df.LOW * adj)
            df.CLOSE = (df.CLOSE * adj)
        elif method == 'no_adj':
            adj = next_close # to get the data frame shape
            adj[:] = 0

        return df, adj

    def daily_ann_roll(self):
        res = (self.back_ohlcv_df - self.ohlcv_unadjusted_df) / self.n_day_btw_contracts
        return res

    def term_structure(self):
        adj_dates = self.get_adj_dates(n_day=-1)

        df = pd.concat([self._read_ohlcv(row.TICKER, self.as_of_date, self.as_of_date)
                   for _, row in adj_dates.iterrows()])

        return df

