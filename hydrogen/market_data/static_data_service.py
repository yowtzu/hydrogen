from blp import blp
import logging
import pandas as pd
import os
from hydrogen.system import config_filename, static_filename

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

ALL_TICKERS = pd.read_csv(config_filename).TICKER.values

# remove FX Curncy as they are not future
ALL_TICKERS = [ ticker for ticker in ALL_TICKERS if not ticker.endswith(" Curncy") ]

logging.debug('Step 1: Begin to download static data for %i future instruments: %s', len(ALL_TICKERS), ALL_TICKERS)
blp_service = blp.BLPService()
df_list = []
for ticker in ALL_TICKERS:
    try:
        df = blp_service.BDP(ticker,
                             ['NAME', 'FUT_NOTICE_FIRST', 'FUT_CONT_SIZE', 'FUT_TICK_SIZE', 'FUT_GEN_MONTH', 'LAST_TRADEABLE_DT', 'CRNCY'],
                             )
        logging.debug(ticker)
        df_list.append(df)
    except blp.BLPRequestError as e:
        logging.exception('Requesting static data for %s has an issue', ticker)

df = pd.concat(df_list)
logging.debug('Step 1: Downloading complete')

logging.debug('Step 2: Reformatting the dataframe')
df.index.name = 'TICKER'
logging.debug('Step 2: complete')

logging.debug('Step 3: Storing the data to csv file: %s', static_filename)
df.to_csv(static_filename)
logging.debug('Step 3: complete')
