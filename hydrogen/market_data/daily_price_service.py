from blp import blp
import logging
import pandas as pd
import os
import settings
from datetime import timedelta

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

CONFIG_FILE_NAME = os.path.join(settings.PROJECT_ROOT, 'data\config.csv')
DAILY_PRICE_DIR = os.path.join(settings.PROJECT_ROOT, 'data\ohlcv')
OHLCV_FIELDS = ['PX_OPEN', 'PX_HIGH', 'PX_LOW', 'PX_LAST', 'PX_VOLUME']

config = pd.read_csv(CONFIG_FILE_NAME, index_col='TICKER', parse_dates=[2, 3])
# config = config.tail()

blp_service = blp.BLPService()

for ticker, row in config.iterrows():
    logger.debug('Working Ticker: %s', ticker)
    file_name = os.path.join(DAILY_PRICE_DIR, ticker + '.csv')
    daily_df = pd.DataFrame(columns=['DATE'] + OHLCV_FIELDS).set_index('DATE')
    start_date = row.START_DATE
    end_date = row.END_DATE

    if os.path.isfile(file_name):
        new_df = pd.read_csv(file_name, index_col='DATE')
        new_df.index = pd.to_datetime(new_df.index)

        daily_df = daily_df.append(new_df)
        start_date = daily_df.index[-1] + timedelta(days=1)
        if start_date >= end_date:
            logging.info('Skip ticker: %s because the start date: %s >= end date: %s', ticker, start_date, end_date)
            continue

    logging.info('Downloading historical daily data for %s for dates between (%s,%s)', ticker, start_date, end_date)
    try:
        new_df = blp_service.BDH(ticker, OHLCV_FIELDS, start_date, end_date)
        # flatten the column
        print(new_df)
        new_df.columns = new_df.columns.get_level_values(1)
        new_df.index.name = 'DATE'
        daily_df = daily_df.append(new_df)
    except blp.BLPRequestError as e:
        logging.exception(e)

    if not daily_df.empty:
        daily_df.to_csv(file_name)
