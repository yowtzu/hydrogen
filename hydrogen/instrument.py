import logging
import numpy as np
import pandas as pd
import os
import re
import settings
from pandas.tseries.offsets import BDay

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FX:
    _STATIC_FULL_PATH = os.path.join(settings.PROJECT_ROOT, 'data\static.csv')
    _OHLCV_PATH = os.path.join(settings.PROJECT_ROOT, 'data\ohlcv')
    _bbg_field_map = {'PX_OPEN': 'OPEN', 'PX_LOW': 'LOW', 'PX_HIGH': 'HIGH', 'PX_LAST': 'CLOSE', 'PX_VOLUME': 'VOLUME'}

    def __init__(self, ticker: str, as_of_date=pd.datetime.today()):
        self.ticker = ticker
        self.as_of_date = as_of_date
        self.cont_size = self.static_df.FUT_CONT_SIZE.unique()
        self.tick_size = self.static_df.FUT_TICK_SIZE.unique()

    def _read_ohlcv(self, start_date, end_date):
        ohlcv_df = pd.DataFrame()

        filename = os.path.join(Future._OHLCV_PATH, self.ticker + '.csv')
        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._bbg_field_map)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)
            ohlcv_df = ohlcv_df[start_date:end_date]
            # only see data up to t-1 from as of date (inclusively)
            ohlcv_df = ohlcv_df[:self.as_of_date]

        return ohlcv_df

    def close_price(self):
        return self._read_ohlcv.CLOSE


class Future:
    _STATIC_FULL_PATH = os.path.join(settings.PROJECT_ROOT, 'data\static.csv')
    _OHLCV_PATH = os.path.join(settings.PROJECT_ROOT, 'data\ohlcv')
    _bbg_field_map = {'PX_OPEN': 'OPEN', 'PX_LOW': 'LOW', 'PX_HIGH': 'HIGH', 'PX_LAST': 'CLOSE', 'PX_VOLUME': 'VOLUME',
                      'FUT_NOTICE_FIRST': 'FUT_NOTICE_FIRST',}

    def __init__(self, ticker: str, as_of_date=pd.datetime.today()):
        self.as_of_date = as_of_date
        self._ticker_pattern = self._resolve_ticker(ticker)
        self.static_df = self._read_static_csv(self._ticker_pattern)
        self.cont_size = self.static_df.FUT_CONT_SIZE.unique()
        self.tick_size = self.static_df.FUT_TICK_SIZE.unique()

        # self.ohlcv = self._read_daily_csv()
        # self.ohlcv_adj = self.roll_adj(self.ohlcv, method='panama',  adj_values=False)

    def _resolve_ticker(self, ticker: str):
        prefix, suffix = ticker.rsplit(" ", maxsplit=1)
        regexp_double_digit = re.compile(r'[0-1][0-9]')
        # if it is format like ES01 Index
        if regexp_double_digit.search(prefix[-2:]):
            return ticker
        else:
            # relative: return a sorted list of tickers prior to the as of dates
            return prefix[:-1] + "[A-Z][0-9]+ " + suffix

    def ticker_list(self):
        return self.static_df.TICKER.values.copy()

    def _read_static_csv(self, ticker_patterns):
        static_df = pd.read_csv(Future._STATIC_FULL_PATH).rename(columns=self._bbg_field_map)
        static_df.FUT_NOTICE_FIRST = pd.to_datetime(static_df.FUT_NOTICE_FIRST)
        static_df = static_df[static_df.TICKER.str.contains(ticker_patterns)]
        static_df = static_df.sort_values(by='FUT_NOTICE_FIRST')

        return static_df

    def _read_ohlcv(self, ticker, start_date, end_date):
        ohlcv_df = pd.DataFrame()

        filename = os.path.join(Future._OHLCV_PATH, ticker + '.csv')
        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._bbg_field_map)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)
            ohlcv_df = ohlcv_df[start_date:end_date]
            # only see data up to t-1 from as of date (inclusively)
            ohlcv_df = ohlcv_df[:self.as_of_date]

        return ohlcv_df

    def get_adj_dates(self, n_day=-1):
        roll_dates = self.static_df[["TICKER", "FUT_NOTICE_FIRST"]].copy()
        roll_dates['START_DATE'] = roll_dates.FUT_NOTICE_FIRST.shift(1).fillna(pd.tslib.Timestamp.min)
        roll_dates['END_DATE'] = roll_dates.FUT_NOTICE_FIRST.apply(lambda x: x + n_day * BDay())
        roll_dates['NEXT_TICKER'] = roll_dates.TICKER.shift(-1).fillna('')
        return roll_dates

    def close_price(self, adj_dates: pd.DataFrame = None, method='panama'):

        if method not in ['ratio', 'panama', 'no_adj']:
            raise ValueError('method is not valid: ' + method)

        if method == 'no_adj':
            adj_dates = pd.DataFrame(columns=['Date', 'Adjustment'])

        if not isinstance(adj_dates, pd.DataFrame):
            raise ValueError('Calendar must be pandas DataFrame')

        df = pd.concat([self._read_ohlcv(row.TICKER, row.START_DATE, row.END_DATE)
                        for _, row in adj_dates.iterrows()])
        df = df.CLOSE

        adj = pd.concat([self._read_ohlcv(row.NEXT_TICKER, row.END_DATE, row.END_DATE)
                         for _, row in adj_dates.iterrows()])
        adj = adj.CLOSE

        if method == 'panama':
            adj = (adj - df.asof(adj.index))
            adj = adj[::-1].cumsum()[::-1].reindex(df.index, method='bfill').fillna(0)
            df = (df + adj)
        elif method == 'ratio':
            adj = (adj / df.asof(adj.index))
            adj = adj[::-1].cumprod()[::-1].reindex(df.index, method='bfill').fillna(1)
            df = (df * adj)
        elif method == 'none':
            adj[:] = np.nan
            df = df

        logging.debug(adj)
        return df, adj


    def carry(self):
        front_adj_dates = self.get_adj_dates(n_day=-1)
        front = self.close_price(front_adj_dates, method = 'no_adj')

        back_adj_dates = front_adj_dates.copy()
        back_adj_dates.TICKER = back_adj_dates.DATE.NEXT_TICKER
        back = self.close_price(back_adj_dates, method = 'no_adj')

        n_day_btw_contracts = front_adj_dates.index.diff().mean()

        return (back - front) / n_day_btw_contracts

    def term_structure(self):
        adj_dates = self.get_adj_dates(n_day=-1)

        df = pd.concat([self._read_ohlcv(row.TICKER, self.as_of_date, self.as_of_date)
                   for _, row in adj_dates.iterrows()])

        return df

