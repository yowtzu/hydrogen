from blp import blp
import logging
import pandas as pd
import os
import re
from hydrogen.system import config_filename

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


FX_ROOT_TICKERS = ['EURUSD', 'GBPUSD', 'CHFUSD', 'CADUSD', 'AUDUSD', 'NZDUSD', 'KRWUSD', 'JPYUSD', 'MXNUSD',
                   'EURUSDCR', 'GBPUSDCR', 'CHFUSDCR', 'CADUSDCR', 'AUDUSDCR', 'NZDUSDCR', 'KRWUSDCR', 'JPYUSDCR', 'MXNUSDCR']

FX_SPOT_TICKERS = [ticker_root + ' Curncy' for ticker_root in FX_ROOT_TICKERS]

df_fx = pd.DataFrame({'ROOT_TICKER':FX_ROOT_TICKERS, 'TICKER': FX_SPOT_TICKERS})

FI_FUTURE_ROOT_TICKERS = ['OE', 'RX', 'UB', 'DU', 'G ', 'FV', 'TU',
                          'TY', 'WN', 'US', 'OAT', 'IK', 'CN',
                          'BTA', 'KAA', 'KE', 'XM', 'YM', 'JB',
                          'ED']

FI_FUTURE_FRONT_TICKERS = [ticker_root + '1 Comdty' for ticker_root in FI_FUTURE_ROOT_TICKERS]

EQUITY_FUTURE_ROOT_TICKERS = ['ES', 'Z ', 'YBY', 'VG', 'GX', 'UX', 'FVS', 'CF', 'AEX']
EQUITY_FUTURE_FRONT_TICKERS = [ticker_root + '1 Index' for ticker_root in EQUITY_FUTURE_ROOT_TICKERS]

COMDTY_FUTURE_ROOT_TICKERS = ['CL', 'CO', 'XB', 'HO', 'AX', 'NG', 'LA', 'HG',
                              'LL', 'LN', 'LX', 'GC', 'SI', 'W ', 'KW', 'C ',
                              'S ', 'CT', 'SB', 'KC', 'CC', 'FC', 'LC', 'LH', 'PL']

COMDTY_FUTURE_FRONT_TICKERS = [ticker_root + '1 Comdty' for ticker_root in COMDTY_FUTURE_ROOT_TICKERS]

ALL_FRONT_TICKERS = FI_FUTURE_FRONT_TICKERS + EQUITY_FUTURE_FRONT_TICKERS + COMDTY_FUTURE_FRONT_TICKERS

logging.debug('Step 1: Begin to download configurations for %i future instruments: %s', len(ALL_FRONT_TICKERS),
              ALL_FRONT_TICKERS)

blp_service = blp.BLPService()
df = blp_service.BDS(ALL_FRONT_TICKERS,
                     'FUT_CHAIN',
                     INCLUDE_EXPIRED_CONTRACTS='Y'
                     )

logging.debug('Step 1: Downloading complete')

logging.debug('Step 2: Reformatting the dataframe')
df = df.reset_index()
df = df.rename(columns={'index': 'ROOT_TICKER',
                        'Security Description': 'TICKER'})
# filter out symbols that are too old
valid_ticker_pattern = re.compile('.*[A-Z](05|06|07|08|09|10|11|12|13|14|15|16|17|18|19|5|6|7|8|9) .*')
df = df[df.TICKER.str.contains(valid_ticker_pattern)]

df_comb = pd.concat([df, df_fx])

df_comb["START_DATE"] = pd.datetime(2005, 1, 1)
df_comb["END_DATE"] = pd.datetime.today().date() - pd.datetools.timedelta(days=1)
df_comb["IS_ENABLED"] = True
df_comb["IS_ENABLED_INTRADAY"] = True
logging.debug('Step 2: complete')

logging.debug('Step 3: Storing the data to csv file: %s', config_filename)
df_comb.to_csv(config_filename, index=False)
logging.debug('Step 3: complete')
