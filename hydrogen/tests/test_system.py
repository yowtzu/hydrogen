import unittest
import logging
from hydrogen.system import System
import pandas as pd
import numpy as np
from pandas.util.testing import assert_frame_equal
from numpy.testing import assert_array_equal
import hydrogen.analytics

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
        self.system = System(filename='../config.yml')

    def tearDown(self):
        self.system = None

    def test_properties(self):
        assert(self.system.n_day_in_year==365.25)
        assert(self.system.root_n_day_in_year==np.sqrt(365.25))
        assert(self.system.n_bday_in_year == 256.0)
        logger.debug(self.system.root_n_bday_in_year)
        assert(self.system.root_n_bday_in_year == np.sqrt(256.0))
        assert(self.system.n_month_in_year == 12)
        assert(self.system.n_week_in_year == self.system.n_day_in_year/7.0)
        assert(self.system.epoch == pd.datetime(2005, 1,1).date())
        assert(self.system.trading_capital == 1000000)
        assert(self.system.vol_target_pct == 0.2)
        assert(self.system.vol_target_cash_annual == 200000)
        assert(self.system.vol_target_cash_daily == 200000/self.system.root_n_bday_in_year)

