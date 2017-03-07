import yaml
import logging
import numpy as np
import os, sys

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

project_path = os.path.abspath(os.path.dirname(__file__))
logger.debug(project_path)
cfg_filename = os.path.join(project_path, 'config.yml')
logger.debug(cfg_filename)

with open(cfg_filename) as ymlfile:
    cfg = yaml.load(ymlfile)["system"]
    [ setattr(sys.modules[__name__], k, v) for k, v in cfg.items() ]

root_n_day_in_year = np.sqrt(n_day_in_year)
root_n_bday_in_year = np.sqrt(n_bday_in_year)
n_week_in_year = n_day_in_year / 7.0
vol_target_cash_annual = trading_capital * vol_target_pct
vol_target_cash_daily = vol_target_cash_annual / root_n_bday_in_year
