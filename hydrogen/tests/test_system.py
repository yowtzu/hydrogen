import unittest
import logging
import hydrogen.system as system
import numpy as np
import pandas as pd

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class SystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pass

    @classmethod
    def tearDownClass(cls):
        pass

    def setUp(self):
        pass

    def tearDown(self):
        pass

    def test_properties(self):
        self.assertEqual(system.n_day_in_year, 365)
        self.assertEqual(system.root_n_day_in_year, np.sqrt(365))
        self.assertEqual(system.n_bday_in_year, 256)
        self.assertEqual(system.root_n_bday_in_year, np.sqrt(256))
        self.assertEqual(system.n_month_in_year, 12)
        self.assertEqual(system.n_bday_in_3m, 64)
        self.assertEqual(system.n_week_in_year, 52)
        self.assertEqual(system.epoch, pd.datetime(2005, 1,1).date())
        self.assertEqual(system.trading_capital, 1000000)
        self.assertEqual(system.vol_target_pct, 0.2)
        self.assertEqual(system.vol_target_cash_annual, 200000)
        self.assertEqual(system.vol_target_cash_daily, 200000/system.root_n_bday_in_year)
        self.assertEqual(system.avg_abs_forecast, 10.0)