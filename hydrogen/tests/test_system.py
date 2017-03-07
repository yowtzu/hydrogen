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
        assert(system.n_day_in_year==365.25)
        assert(system.root_n_day_in_year==np.sqrt(365.25))
        assert(system.n_bday_in_year == 256.0)
        assert(system.root_n_bday_in_year == np.sqrt(256.0))
        assert(system.n_month_in_year == 12)
        assert(system.n_week_in_year == system.n_day_in_year/7.0)
        assert(system.epoch == pd.datetime(2005, 1,1).date())
        assert(system.trading_capital == 1000000)
        assert(system.vol_target_pct == 0.2)
        assert(system.vol_target_cash_annual == 200000)
        assert(system.vol_target_cash_daily == 200000/system.root_n_bday_in_year)

