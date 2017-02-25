import unittest
import logging
from hydrogen.instrument import Future
import pandas as pd
import numpy as np
from pandas.util.testing import assert_frame_equal
from numpy.testing import assert_array_equal

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class FutureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.future_Z_1_Index_ticker = "Z 1 Index"
        self.future_CLH14_Comdty_ticker = "CLH14 Comdty"
        self.future_CLH15_Comdty_ticker = "CLH15 Comdty"
        self.as_of_date = pd.datetime(year=2010, month=3, day=21)
        pass

    def tearDown(self):
        pass

    def test_init(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_Z_1_Index.as_of_date, self.as_of_date)
        self.assertIsNotNone(future_Z_1_Index._ticker_pattern)

        future_CLH15_Comdty = Future(self.future_CLH15_Comdty_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_CLH15_Comdty.as_of_date, self.as_of_date)
        self.assertIsNotNone(future_CLH15_Comdty._ticker_pattern)

    def test_resolve_ticker(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        logging.debug('Future %s resolved to the following:', self.future_Z_1_Index_ticker)
        logging.debug(future_Z_1_Index._resolve_ticker(self.future_Z_1_Index_ticker))
        self.assertEqual(future_Z_1_Index._resolve_ticker(self.future_Z_1_Index_ticker), "Z [A-Z][0-9]+ Index")

        future_CLH15_Comdty = Future(self.future_CLH15_Comdty_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_CLH15_Comdty._resolve_ticker(self.future_CLH15_Comdty_ticker), "CLH15 Comdty")

    def test_read_static(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_Z_1_Index.cont_size, np.array(10))
        self.assertEqual(future_Z_1_Index.tick_size, np.array(0.5))
        [self.assertRegex(text, "Z [A-Z][0-9]+ Index") for text in future_Z_1_Index.static_df.TICKER]

        future_CLH15_Comdty = Future(self.future_CLH15_Comdty_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_CLH15_Comdty.cont_size, np.array(1000))
        self.assertEqual(future_CLH15_Comdty.tick_size, np.array(0.01))
        self.assertEqual(future_CLH15_Comdty.static_df.TICKER.values, np.array(self.future_CLH15_Comdty_ticker))

        assert_frame_equal(future_CLH15_Comdty.static_df,
                           future_CLH15_Comdty.static_df.sort_values(by="FUT_NOTICE_FIRST"))

    def test_ticker_list(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        tickers = future_Z_1_Index.ticker_list()
        [self.assertRegex(text, "Z [A-Z][0-9]+ Index") for text in tickers]
        logging.debug(tickers)
        assert_array_equal(tickers, future_Z_1_Index.static_df.sort_values(by="FUT_NOTICE_FIRST").TICKER.values)

    def test_read_daily_csv(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        df = future_Z_1_Index._read_ohlcv('Z M6 Index', pd.tslib.Timestamp.min, pd.tslib.Timestamp.max)
        self.assertEqual(df.index[0], pd.datetime(2015, 6, 22))
        self.assertEqual(df.index[-1], pd.datetime(2016, 3, 21))

    def test_get_panama_adj_dates(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        adj_dates = future_Z_1_Index.get_adj_dates(-1)
        logging.debug(adj_dates)
        self.assertEqual(adj_dates.TICKER.iloc[0], 'Z H05 Index')
        self.assertEqual(adj_dates.FUT_NOTICE_FIRST.iloc[0], pd.datetime(2005, 3, 18))
        self.assertEqual(adj_dates.START_DATE.iloc[0], pd.tslib.Timestamp.min)
        self.assertEqual(adj_dates.END_DATE.iloc[0], pd.datetime(2005, 3, 17))

    def test_roll_panama(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        df, adj = future_Z_1_Index.ohlcv(future_Z_1_Index.get_adj_dates(n_day=-1))
        self.assertEqual(df.CLOSE.ix[0], 3970.5)
        self.assertEqual(adj.ix['20050616'], -884.5)

    def test_roll_ratios(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        df, adj = future_Z_1_Index.ohlcv(future_Z_1_Index.get_adj_dates(n_day=-1), method='ratio')
        self.assertEqual(df.CLOSE.ix[0], 4164.0823710527939)
        self.assertEqual(adj.ix['20050616'], 0.85776142863478932)

    def test_roll_no_adj(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        df, adj = future_Z_1_Index.ohlcv(future_Z_1_Index.get_adj_dates(n_day=-1), method='no_adj')
        self.assertEqual(df.CLOSE.ix[0], 4834.5)
        self.assertEqual(0 == adj.ix['20050616'], True)

    def test_vol_standardised_close_price(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        future_Z_1_Index.vol_standardised_close_price()


if __name__ == '__main__':
    unittest.main(warnings='ignore')
