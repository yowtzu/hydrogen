import unittest
import logging
from hydrogen.instrument import Future
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
        self.future_Z_1_Index_ticker = "Z 1 Index"
        self.future_CLH14_Comdty_ticker = "CLH14 Comdty"
        self.future_CLH15_Comdty_ticker = "CLH15 Comdty"
        self.as_of_date = pd.datetime(year=2010, month=3, day=21)
        self.future_Z_1_Index = Future(self.future_Z_1_Index_ticker, as_of_date=self.as_of_date)
        pass

    def tearDown(self):
        pass

    def test_price_vol(self):
        pass

    def test_adj(self):
        pass


if __name__ == '__main__':
    unittest.main(warnings='ignore')
