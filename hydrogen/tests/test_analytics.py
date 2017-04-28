import unittest
import logging
from hydrogen.instrument import InstrumentFactory
import pandas as pd
import numpy as np
import hydrogen.analytics
import hydrogen.system as system

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

    def tearDown(self):
        pass

    def test_price_vol(self):
        logger.debug(system.n_bday_in_3m)
        a = (hydrogen.analytics.vol(self.ohlcv, method='SD', window=system.n_bday_in_3m, annualised=False))
        b = (hydrogen.analytics.vol(self.ohlcv, method='ATR', window=system.n_bday_in_3m, annualised=False))
        c = (hydrogen.analytics.vol(self.ohlcv, method='YZ', window=system.n_bday_in_3m, annualised=False))
        d = (hydrogen.analytics.vol(self.ohlcv, method='RS', window=system.n_bday_in_3m, annualised=False))
        res = pd.concat([a, b, c, d], axis=1)
        logger.debug(res)

    def test_adj(self):
        pass

    def test_combined_forecast_to_position(self):
        pass


if __name__ == '__main__':
    unittest.main(warnings='ignore')
