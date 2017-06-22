import logging
import blp.blp as blp
import os
blp = blp.BLPService()
logger = logging.getLogger(__name__)
OHLCV_FIELDS_DICT = {'PX_OPEN': 'OPEN', 'PX_HIGH': 'HIGH', 'PX_LOW': 'LOW', 'PX_LAST': 'CLOSE', 'PX_VOLUME': 'VOLUME'}
ticker = 'ES1 Index'
df = blp.BDH(ticker, OHLCV_FIELDS_DICT.keys(), '20050101', '20150101')[ticker]
df = df.rename(columns=OHLCV_FIELDS_DICT)
filename= os.path.join(r'data\tests', '{}.csv'.format(ticker))
print(filename)
df.to_csv(filename)