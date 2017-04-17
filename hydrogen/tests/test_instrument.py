import unittest
import logging
from hydrogen.instrument import InstrumentFactory
import pandas as pd
import numpy as np
from pandas.util.testing import assert_frame_equal
from numpy.testing import assert_array_equal

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class FXTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.instrument_factory = InstrumentFactory()

        self.aud_ticker = "AUDUSD Curncy"
        self.as_of_date = pd.datetime(year=2010, month=3, day=21)
        pass

    def test_init(self):
        aud_ticker = self.instrument_factory.create_instrument(self.aud_ticker, as_of_date=self.as_of_date)
        self.assertEqual(aud_ticker._as_of_date, self.as_of_date)

        target_price = 0.9225
        date_index = pd.datetime(2010, 3, 19)
        price = aud_ticker.unadjusted_ohlcv.ix[date_index, 'HIGH']
        self.assertEqual(price, target_price)
        adj_price = aud_ticker.ohlcv.ix[date_index, 'HIGH']
        self.assertEqual(adj_price, target_price)

        self.assertIsNone(aud_ticker.ccy)

    def tearDown(self):
        pass


class FutureTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        self.instrument_factory = InstrumentFactory()

        self.future_Z_1_Index_ticker = "Z 1 Index"
        self.future_CLH14_Comdty_ticker = "CLH14 Comdty"
        self.future_CLH15_Comdty_ticker = "CLH15 Comdty"
        self.as_of_date = pd.datetime(year=2010, month=3, day=21)
        pass

    def tearDown(self):
        pass

    def test_init(self):
        future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_Z_1_Index._as_of_date, self.as_of_date)
        #self.assertIsNotNone(future_Z_1_Index._ticker_pattern)

        future_CLH15_Comdty = self.instrument_factory.create_instrument(self.future_CLH15_Comdty_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_CLH15_Comdty._as_of_date, self.as_of_date)
        #self.assertIsNotNone(future_CLH15_Comdty._ticker_pattern)

    #def test_resolve_ticker(self):
    #    future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
    #    logging.debug('Future %s resolved to the following:', self.future_Z_1_Index_ticker)
    #    logging.debug(future_Z_1_Index._resolve_ticker(self.future_Z_1_Index_ticker))
    #    self.assertEqual(future_Z_1_Index._resolve_ticker(self.future_Z_1_Index_ticker), "Z [A-Z][0-9]+ Index")

    #    future_CLH15_Comdty = self.instrument_factory.create_instrument(self.future_CLH15_Comdty_ticker, as_of_date=self.as_of_date)
    #    self.assertEqual(future_CLH15_Comdty._resolve_ticker(self.future_CLH15_Comdty_ticker), "CLH15 Comdty")

    def test_read_static(self):
        future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_Z_1_Index._cont_size, np.array(10))
        self.assertEqual(future_Z_1_Index._tick_size, np.array(0.5))
        [self.assertRegex(text, "Z [A-Z][0-9]+ Index") for text in future_Z_1_Index._static_df.TICKER]

        future_CLH15_Comdty = self.instrument_factory.create_instrument(self.future_CLH15_Comdty_ticker, as_of_date=self.as_of_date)
        self.assertEqual(future_CLH15_Comdty._cont_size, np.array(1000))
        self.assertEqual(future_CLH15_Comdty._tick_size, np.array(0.01))
        self.assertEqual(future_CLH15_Comdty._static_df.TICKER.values, np.array(self.future_CLH15_Comdty_ticker))

        assert_frame_equal(future_CLH15_Comdty._static_df,
                           future_CLH15_Comdty._static_df.sort_values(by="FUT_NOTICE_FIRST"))

    def test_ticker_list(self):
        future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        tickers = future_Z_1_Index.ticker_list
        [self.assertRegex(text, "Z [A-Z][0-9]+ Index") for text in tickers]
        logging.debug(tickers)
        assert_array_equal(tickers, future_Z_1_Index._static_df.sort_values(by="FUT_NOTICE_FIRST").TICKER.values)

    def test_read_daily_csv(self):
        future_M6_Index = self.instrument_factory.create_instrument("Z M6 Index", as_of_date=pd.datetime(year=2016, month=3, day=21))
        logger.debug(future_M6_Index.ohlcv.index[0])
        self.assertEqual(future_M6_Index.ohlcv.index[0], pd.datetime(2015, 10, 28))
        self.assertEqual(future_M6_Index.ohlcv.index[-1], pd.datetime(2016, 3, 21))

    def test_get_panama_adj_dates(self):
        future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        adj_info = future_Z_1_Index._get_adj_info(-1)
        logging.debug(adj_info)
        self.assertEqual(adj_info.TICKER.iloc[0], 'Z H05 Index')
        self.assertEqual(adj_info.NEXT_TICKER.iloc[0], 'Z M05 Index')
        self.assertEqual(adj_info.FUT_NOTICE_FIRST.iloc[0], pd.to_datetime('20050318').date())
        self.assertEqual(adj_info.START_DATE.iloc[0], pd.to_datetime('20000101').date())
        self.assertEqual(adj_info.END_DATE.iloc[0], pd.datetime(2005, 3, 17).date())

    def test_roll_panama(self):
        future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        #df, adj = future_Z_1_Index.ohlcv(future_Z_1_Index._get_adj_dates(n_day=-1))
        self.assertEqual(future_Z_1_Index.ohlcv.CLOSE.ix[0], 3970.5)
        self.assertEqual(future_Z_1_Index._adj.ix['20050616'], -884.5)

    def test_roll_ratios(self):
        future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        _ , df, adj = future_Z_1_Index._calc_ohlcv(future_Z_1_Index._get_adj_info(), method='ratio')
        self.assertEqual(df.CLOSE.ix[0], 4164.0823710527939)
        self.assertEqual(adj.ix['20050616'], 0.85776142863478932)

    def test_roll_no_adj(self):
        future_Z_1_Index = self.instrument_factory.create_instrument(self.future_Z_1_Index_ticker, as_of_date=pd.datetime(year=2016, month=3, day=21))
        _ , df, adj = future_Z_1_Index._calc_ohlcv(future_Z_1_Index._get_adj_info(), method='no_adj')
        self.assertEqual(df.CLOSE.ix[0], 4834.5)
        self.assertEqual(adj.ix['20050616'], 0)


if __name__ == '__main__':
    unittest.main(warnings='ignore')
