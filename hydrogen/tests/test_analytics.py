import unittest
import logging
from hydrogen.instrument import InstrumentFactory
import pandas as pd
import numpy as np
from pandas.util.testing import assert_frame_equal
from numpy.testing import assert_array_equal
import hydrogen.analytics

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class AnalyticsTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        future_Z_1_Index_ticker = "Z 1 Index"
        as_of_date = pd.datetime(year=2010, month=3, day=21)
        instrument_factory = InstrumentFactory()
        future_Z_1_Index = instrument_factory.create_instrument(future_Z_1_Index_ticker, as_of_date=as_of_date)
        self.ohlcv = future_Z_1_Index.ohlcv
        pass

    def tearDown(self):
        pass

    def test_price_vol(self):
        a = (hydrogen.analytics.vol(self.ohlcv, method='SD', window=21))
        b = (hydrogen.analytics.vol(self.ohlcv, method='ATR', window=21))
        c = (hydrogen.analytics.vol(self.ohlcv, method='YZ', window=21))
        d = (hydrogen.analytics.vol(self.ohlcv, method='RS', window=21))
        res = pd.concat([a, b, c, d], axis=1)
        logger.debug(res)

    def test_adj(self):
        pass

    def test_combined_forecast_to_position(self):
        pass


if __name__ == '__main__':
    unittest.main(warnings='ignore')
