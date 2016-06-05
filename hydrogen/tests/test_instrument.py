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
                           future_CLH15_Comdty.static_df.sort(columns="FUT_NOTICE_FIRST"))

    def test_ticker_list(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        tickers = future_Z_1_Index.ticker_list()
        [self.assertRegex(text, "Z [A-Z][0-9]+ Index") for text in tickers]
        assert_array_equal(tickers, future_Z_1_Index.static_df.sort(columns="FUT_NOTICE_FIRST").TICKER.values)

    def test_read_daily_csv(self):
        future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        ohlcv_df = future_Z_1_Index.read_daily_csv()
        self.assertEquals(len(ohlcv_df), 9821)

        future_CLH14_Comdty = Future(self.future_CLH14_Comdty_ticker, as_of_date=self.as_of_date)
        ohlcv_df = future_CLH14_Comdty.read_daily_csv()
        self.assertEquals(len(ohlcv_df), 1321)

    def test_adj(self):
        pass


if __name__ == '__main__':
    unittest.main(warnings='ignore')
