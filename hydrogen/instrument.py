import logging
import pandas as pd
import os
import re
import settings

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Future:
    _STATIC_FULL_PATH = os.path.join(settings.PROJECT_ROOT, 'data\static.csv')
    _OHLCV_PATH = os.path.join(settings.PROJECT_ROOT, 'data\ohlcv')

    def __init__(self, ticker: str, as_of_date=pd.datetime.today()):
        self.as_of_date = as_of_date
        self._ticker_pattern = self._resolve_ticker(ticker)
        self.static_df = self.read_static(self._ticker_pattern)
        self.cont_size = self.static_df.FUT_CONT_SIZE.unique()
        self.tick_size = self.static_df.FUT_TICK_SIZE.unique()

        self.ohlcv = self.read_daily_csv()
        self.ohlcv_adj = self.roll_adj(self.ohlcv, method='panama')

    def _resolve_ticker(self, ticker: str):
        prefix, suffix = ticker.rsplit(" ", maxsplit=1)
        regexp_double_digit = re.compile(r'[0-1][0-9]')
        if regexp_double_digit.search(prefix[-2:]):
            return ticker
        else:
            # relative: return a sorted list of tickers prior to the as of dates
            return prefix[:-1] + "[A-Z][0-9]+ " + suffix

    def read_static(self, ticker_patterns):
        static_df = pd.read_csv(Future._STATIC_FULL_PATH, infer_datetime_format=True)
        static_df = static_df[static_df.TICKER.str.contains(ticker_patterns)]
        static_df = static_df.sort(columns="FUT_NOTICE_FIRST")
        return static_df

    def ticker_list(self):
        return self.static_df.TICKER.values.copy()

    def read_daily_csv(self):
        ohlcv_df = pd.DataFrame()

        for ticker in self.ticker_list():
            full_path = os.path.join(Future._OHLCV_PATH, ticker)
            if os.path.exists(full_path):
                df = pd.read_csv(full_path, infer_datetime_format=True).rename(columns=str.upper)
                df.insert(0, "TICKER", ticker)
                ohlcv_df = ohlcv_df.append(df)

        # only see data up to t-1 from as of date
        # ohlcv_df = ohlcv_df[ohlcv_df.DATE < self.as_of_date]
        return ohlcv_df

    def roll_adj(self, ohlcv, method='panama'):
        return {'panama': self._adj_panama,
                }[method](ohlcv)

    def _adj_panama(self, ohlcv):
        # roll_dates = self.static_df.FUT_NOTICE_FIRST.values
        # front_prices_on_roll_dates = ohlcv_df.CLOSE[ ohlcv_df.DATE roll_dates ]
        # back_prices_on_roll_dates = ohlcv_df.CLOSE[ohlcv_df.DATE      roll_dates]
        # diff_to_apply = (front_prices_on_roll_dates - back_prices_on_roll_dates).reversed.cumsum().reversed()
        pass
