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
    def create_instrument(self, ticker:str, as_of_date=pd.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)):
        prefix, suffix = ticker.rsplit(" ", maxsplit=1)
        class_map = {"Curncy": FX,
                     "Comdty": Future,
                     "Index": Future,
                     }
        return class_map[suffix](ticker, as_of_date)

class Instrument:
    _STATIC_FULL_PATH = os.path.join(settings.PROJECT_ROOT, 'data\static.csv')
    _OHLCV_PATH = os.path.join(settings.PROJECT_ROOT, 'data\ohlcv')
    _BBG_FIELD_MAP = {'PX_OPEN': 'OPEN', 'PX_LOW': 'LOW', 'PX_HIGH': 'HIGH', 'PX_LAST': 'CLOSE', 'PX_VOLUME': 'VOLUME',
                      'FUT_NOTICE_FIRST': 'FUT_NOTICE_FIRST', }

    def __init__(self, ticker: str, as_of_date):
        self._ticker = ticker
        self._as_of_date = as_of_date

    def __repr__(self):
        return str(self.__class__) + ":" + self.ticker + " as of " + str(self.as_of_date)

    @property
    def ccy(self):
        return self._ccy

    @property
    def ohlcv(self):
        return self._ohlcv_df

    @property
    def unadjusted_ohlcv(self):
        return self._unadjusted_ohlcv_df

    @property
    def vol(self):
        return hydrogen.analytics.vol(self.ohlcv, method='YZ', window=63, price_scale=False, annualised=True)

    def price_vol(self):
        return hydrogen.analytics.vol(self.ohlcv, method='YZ', window=63, price_scale=True, annualised=False)

    @property
    def cont_size(self):
        return self._cont_size

    @property
    def tick_size(self):
        return self._tick_size

    @property
    def daily_yield(self):
        return self._calc_daily_yield()

class FX(Instrument):

    def __init__(self, ticker: str, as_of_date):
        super().__init__(ticker, as_of_date)
        self._ccy = None
        self._ohlcv_df = self._read_ohlcv()
        self._unadjusted_ohlcv_df = self._ohlcv_df
        self._cr_ohlcv = self._read_carry_ohlcv()

    def _read_ohlcv(self):
        ohlcv_df = pd.DataFrame()

        filename = os.path.join(Future._OHLCV_PATH, self.ticker + '.csv')
        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._BBG_FIELD_MAP)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)

            # only see data up to t-1 from as of date (inclusively)
            ohlcv_df = ohlcv_df[:self.as_of_date]

        return ohlcv_df

    def _read_carry_ohlcv(self):
        ohlcv_df = pd.DataFrame()

        prefix, suffix = self.ticker.rsplit(" ", maxsplit=1)
        filename = os.path.join(Future._OHLCV_PATH, prefix + 'CR ' + suffix + '.csv')

        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._BBG_FIELD_MAP)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)

            # only see data up to t-1 from as of date (inclusively)
            ohlcv_df = ohlcv_df[:self.as_of_date]

        return ohlcv_df

    def _calc_daily_yield(self):
        return self._cr_ohlcv.CLOSE.pct_change().shift(1) -  self.ohlcv.CLOSE.pct_change().shift(1)

class Future(Instrument):

    def __init__(self, ticker: str, as_of_date):
        super().__init__(ticker, as_of_date)

        # self._exact_contract, self._ticker_pattern = self._resolve_ticker(ticker)
        #logger.debug('Ticker pattern: {}'.format(self._ticker_pattern))
        read_multiple_files, self._static_df = self._read_static_csv(self._ticker)

        logger.debug(self._static_df)
        self._cont_size = self._static_df.FUT_CONT_SIZE.values[0]
        self._tick_size = self._static_df.FUT_TICK_SIZE.values[0]
        self._ccy = self._static_df.CRNCY.values[0]

        if not read_multiple_files:
            self._adj_dates = self._get_adj_dates(n_day=-1)
            logger.debug(self._adj_dates)
            self._unadjusted_ohlcv_df = self._read_ohlcv(self._static_df.TICKER.iloc[0], self._adj_dates.START_DATE.iloc[0], self._adj_dates.END_DATE.iloc[0])
            self._ohlcv_df = self.unadjusted_ohlcv
            self.n_day_btw_contracts = np.nan

        else:
            self._adj_dates = self._get_adj_dates(n_day=-1)
            self._unadjusted_ohlcv_df = self._calc_ohlcv(self._adj_dates, method='no_adj')[0]
            self._ohlcv_df, self._adj = self._calc_ohlcv(self._adj_dates, method='panama')

            back_adj_dates = self._adj_dates.copy()[:-1]
            back_adj_dates.TICKER = back_adj_dates.NEXT_TICKER
            self._back_ohlcv_df = self._calc_ohlcv(back_adj_dates, method='no_adj')[0]

            self.n_day_btw_contracts = self._adj_dates.END_DATE[self._adj_dates.END_DATE > self._ohlcv_df.index[-1].date()][:2].diff().iloc[1].days

    @property
    def ticker_list(self):
        return self._static_df.TICKER.values

    def _get_adj_dates(self, n_day=-1):
        roll_dates = self._static_df[["TICKER", "FUT_NOTICE_FIRST"]].copy()
        roll_dates['START_DATE'] = roll_dates.FUT_NOTICE_FIRST.shift(1).fillna(pd.to_datetime('20000101').date())
        roll_dates['END_DATE'] = roll_dates.FUT_NOTICE_FIRST.apply(lambda x: x + n_day * BDay()).dt.date
        roll_dates['NEXT_TICKER'] = roll_dates.TICKER.shift(-1).fillna('')
        return roll_dates

    #def _resolve_ticker(self, ticker: str):
    #    prefix, suffix = ticker.rsplit(" ", maxsplit=1)
    #    regexp_double_digit = re.compile(r'[0-1][0-9]')
    #    # if it is format like ESH13 Index
    #    exact_contract = regexp_double_digit.search(prefix[-2:])
    #    if exact_contract:
    #        return exact_contract, ticker
    #    else:
    #        # relative: return a sorted list of tickers prior to the as of dates
    #        return exact_contract, prefix[:-1] + "[A-Z][0-9]+ " + suffix

    def _read_static_csv(self, ticker):
        static_df = pd.read_csv(Future._STATIC_FULL_PATH).rename(columns=self._BBG_FIELD_MAP)
        static_df.FUT_NOTICE_FIRST = pd.to_datetime(static_df.FUT_NOTICE_FIRST).dt.date

        static_df_filter = static_df[static_df.TICKER==ticker]
        read_multiple_files = False

        if static_df_filter.empty:
            prefix, suffix = ticker.rsplit(" ", maxsplit=1)
            ticker_pattern = prefix[:-1] + "[A-Z][0-9]+ "
            static_df_filter = static_df[static_df.TICKER.str.contains(ticker_pattern)]
            read_multiple_files = True

        static_df_filter = static_df_filter.sort_values(by='FUT_NOTICE_FIRST')

        return read_multiple_files, static_df_filter

    def _read_ohlcv(self, ticker, start_date, end_date):
        ohlcv_df = pd.DataFrame()
        filename = os.path.join(Future._OHLCV_PATH, ticker + '.csv')

        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._BBG_FIELD_MAP)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)
            ohlcv_df = ohlcv_df[start_date:end_date]
            # only see data up to t-1 from as of date (inclusively)
            ohlcv_df = ohlcv_df[:self._as_of_date]
            ohlcv_df = ohlcv_df[ohlcv_df.HIGH.notnull() & ohlcv_df.LOW.notnull() & ohlcv_df.VOLUME.notnull()]

        return ohlcv_df

    def _calc_ohlcv(self, adj_dates: pd.DataFrame = None, method='panama'):

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

    def _calc_daily_yield(self):
        return (self._back_ohlcv_df - self._unadjusted_ohlcv_df) / self.n_day_btw_contracts
