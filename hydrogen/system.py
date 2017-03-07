import yaml
import logging
import numpy as np

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class System():

    @property
    def n_day_in_year(self):
        return self._cfg["n_day_in_year"]

    @property
    def root_n_day_in_year(self):
        return np.sqrt(self.n_day_in_year)

    @property
    def n_bdays_in_year(self):
        return self._cfg["n_bdays_in_year"]

    @property
    def root_n_bdays_in_year(self):
        np.sqrt(self.n_bdays_in_year)

    @property
    def n_month_in_year(self):
        return self._cfg["n_month_in_year"]

    @property
    def root_n_date_in_year(self):
            np.sqrt(self.n_date_in_year)

    @property
    def n_week_in_year(self):
        return self.n_day_in_year / 7.0

    @property
    def root_n_week_in_year(self):
            np.sqrt(self.n_week_in_year)

    @property
    def epoch(self):
        return self._cfg['epoch']

    @property
    def trading_capital(self):
        return self._cfg["trading_capital"]

    @property
    def vol_target_pct(self):
        return self._cfg["volatility_target_pct"]

    @property
    def vol_target_cash_daily(self):
        return self.trading_capital * self.vol_target_pct

    @property
    def vol_target_cash_annualised(self):
        return self.vol_target_cash_daily * self.root_n_date_in_year

    def __init__(self, filename='hydrogen/config.yml'):
        self._read_config_file(filename)

    def _read_config_file(self, filename):
        with open(filename) as ymlfile:
            self._cfg = yaml.load(ymlfile)['system']
        logging.debug(self._cfg)

