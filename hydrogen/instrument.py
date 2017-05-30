import logging
import pandas as pd
import os
import hydrogen.system as system
from pandas.tseries.offsets import BDay
import hydrogen.analytics

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class InstrumentFactory():
    ''' Instrument factory that is responsible to create instrument objects

    Ticker suffix (based on bloomberg convention) is used to determine what instrument object to create,
    e.g. Curncy is for FX. It only supports Future and FX.

    '''

    def create_instrument(self, ticker: str,
                          as_of_date=pd.datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)):
        '''Create instrument object based on the ticker suffix

        Args:
            ticker: Bloomberg ticker, e.g., ES1 Index
            as_of_date: The date of the instrument

        Returns:
            An instrument object of the given ticker with meta data and price data as of as_of_date.
        '''
        prefix, suffix = ticker.rsplit(" ", maxsplit=1)
        class_map = {"Curncy": FX,
                     "Comdty": Future,
                     "Index": Future,
                     }
        return class_map[suffix](ticker, as_of_date)

class Instrument:
    ''' Based class to model tradable instruments with bloomberg ticker serve as identifier '''

    _BBG_FIELD_MAP = {'PX_OPEN': 'OPEN',
                      'PX_LOW': 'LOW',
                      'PX_HIGH': 'HIGH',
                      'PX_LAST': 'CLOSE',
                      'PX_VOLUME': 'VOLUME',
                      'FUT_NOTICE_FIRST': 'FUT_NOTICE_FIRST',
                      }

    def __init__(self, ticker: str, as_of_date):
        self._ticker = ticker
        self._as_of_date = as_of_date
        self.b_day_list = pd.date_range('20050101', as_of_date, freq='1B')

    def __repr__(self):
        return str(self.__class__) + ":" + self._ticker + " as of " + str(self._as_of_date)

    @property
    def ccy(self):
        return self._ccy

    @property
    def ohlcv(self):
        '''
            Return the adjusted OHLCV price of the instrument

        Return:
            A data frame consists of adjusted daily prices and volume. Column names: OPEN, HIGH, LOW, CLOSE, VOLUME
        '''
        return self._ohlcv

    @property
    def unadjusted_ohlcv(self):
        '''
            Return  the unadjusted OHLCV price of the instrument

        Return:
            A data frame consists of unadjusted daily prices and volume. Column names: OPEN, HIGH, LOW, CLOSE, VOLUME
        '''
        return self._unadjusted_ohlcv

    @property
    def price_diff(self):
        return self.ohlcv.CLOSE.diff()

    @property
    def vol(self):
        return hydrogen.analytics.vol(self.ohlcv, method='YZ', window=system.n_bday_in_3m, annualised=True)

    @property
    def cont_size(self):
        return self._cont_size

    @property
    def tick_size(self):
        return self._tick_size

    @property
    def block_value(self):
        ''' The amount of PnL in local cash term  for 1% price movement '''
        return 0.01 * self.cont_size * self.unadjusted_ohlcv.CLOSE

    @property
    def daily_price_vol(self):
        '''' SD of % daily change '''
        return 100*hydrogen.analytics.vol(self.ohlcv, method='YZ', window=system.n_bday_in_3m, annualised=False)

    @property
    def instrument_currency_vol(self):
        return self.block_value * self.daily_price_vol

    @property
    def instrument_value_vol(self):
        """ convert to from local ccy to usd """
        if self.ccy=='USD':
            return self.instrument_currency_vol
        else:
            return self.instrument_currency_vol *  self.fx.ohlcv.CLOSE[self.instrument_currency_vol.index]

    @property
    def cost(self):
        execution_cost = self.tick_size / 2 * self.cont_size
        ticker_cost = execution_cost # TODO: assumption
        return execution_cost + ticker_cost

    @property
    def cost_in_SR(self):
        return 2 * self.cost / (16 * self.instrument_currency_vol)

class FX(Instrument):
    ''' FX instrument
        Note that there is no volume for this type of instrument
    '''

    def __init__(self, ticker: str, as_of_date):
        super().__init__(ticker, as_of_date)

        # TODO: START
        self._cont_size = 10000
        self._tick_size = 1
        # TODO: END

        self._ccy = None
        self._ohlcv = self._read_ohlcv(self._ticker)
        self._unadjusted_ohlcv = self._ohlcv

        prefix, suffix = self._ticker.rsplit(" ", maxsplit=1)
        carry_ticker = prefix + 'CR ' + suffix

        self._cr_ohlcv = self._read_ohlcv(carry_ticker)

    def _read_ohlcv(self, filename, resample_method='1B'):
        ohlcv_df = pd.DataFrame()

        filename = os.path.join(system.ohlcv_path, self._ticker + '.csv')

        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._BBG_FIELD_MAP)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)

            # only see data up to as of date (inclusively)
            ohlcv_df = ohlcv_df[:self._as_of_date]

            if resample_method:
                ohlcv_df = ohlcv_df.resample(resample_method).pad()

        return ohlcv_df

class Future(Instrument):
    '''Future instrument
    
    '''

    def __init__(self, ticker: str, as_of_date):
        super().__init__(ticker, as_of_date)

        # self._exact_contract, self._ticker_pattern = self._resolve_ticker(ticker)
        # logger.debug('Ticker pattern: {}'.format(self._ticker_pattern))

        read_multiple_files, self._static_df = self._read_static_csv(self._ticker)
        self._cont_size = self._static_df.FUT_CONT_SIZE.values[0]
        self._tick_size = self._static_df.FUT_TICK_SIZE.values[0]
        self._ccy = self._static_df.CRNCY.values[0]
        self._adj_info = self._get_adj_info(n_day=-1)

        instrument_factory = InstrumentFactory()
        self.fx = instrument_factory.create_instrument(self._ccy + 'USD Curncy')

        if read_multiple_files:
            self._unadjusted_ohlcv, self._ohlcv, self._adj = self._calc_ohlcv(self._adj_info, method='panama')

            back_adj_info = self._adj_info.copy()
            back_adj_info.TICKER = back_adj_info.TICKER.shift(-1)
            back_adj_info.NEXT_TICKER = back_adj_info.NEXT_TICKER.shift(-1)
            back_adj_info = back_adj_info[:-1]
            self._back_ohlcv_df = self._calc_ohlcv(back_adj_info, method='no_adj')[0]

            # calculate the days between contract
            # n_day_btw_contracts = self._adj_dates.END_DATE.diff().shift(-2).dt.days
            # n_day_btw_contracts.index = pd.to_datetime(self._adj_dates.FUT_NOTICE_FIRST)
            # self._n_day_btw_contracts = n_day_btw_contracts.asof(self._ohlcv.index)

        else:
            self._unadjusted_ohlcv = self._read_ohlcv(self._static_df.TICKER.iloc[0],
                                                      self._adj_info.START_DATE.iloc[0],
                                                      self._adj_info.END_DATE.iloc[0])
            self._ohlcv = self.unadjusted_ohlcv

    @property
    def ticker_list(self):
        return self._static_df.TICKER.values

    def _get_adj_info(self, n_day):
        ''' Calculate the start and end dates for each ticker, and the next tickers
            Args:
                n_day: day of adjustment, negative mean number of day before maturity
                
            Returns:
                return a pd.DataFrame of five columns, TICKER, FUT_NOTICE_FIRST, START_DATE, END_DATE, NEXT_TICKER
        '''

        roll_dates = self._static_df[["TICKER", "FUT_NOTICE_FIRST"]].copy()
        roll_dates['START_DATE'] = roll_dates.FUT_NOTICE_FIRST.apply(lambda x: x + (1 + n_day) * BDay()).shift(1).fillna(pd.to_datetime('20000101').date()).dt.date
        roll_dates['END_DATE'] = roll_dates.FUT_NOTICE_FIRST.apply(lambda x: x + n_day * BDay()).dt.date
        roll_dates['NEXT_TICKER'] = roll_dates.TICKER.shift(-1).fillna('')
        return roll_dates

    # def _resolve_ticker(self, ticker: str):
    #    prefix, suffix = ticker.rsplit(" ", maxsplit=1)
    #    regexp_double_digit = re.compile(r'[0-1][0-9]')
    #    # if it is format like ESH13 Index
    #    exact_contract = regexp_double_digit.search(prefix[-2:])
    #    if exact_contract:
    #        return exact_contract, ticker
    #    else:
    #        # relative: return a sorted list of tickers prior to the as of dates
    #        return exact_contract, prefix[:-1] + "[A-Z][0-9]+ " + suffix

    def _read_static_csv(self, ticker):
        static_df = pd.read_csv(system.filtered_static_filename).rename(columns=self._BBG_FIELD_MAP)
        static_df.FUT_NOTICE_FIRST = pd.to_datetime(static_df.FUT_NOTICE_FIRST).dt.date

        static_df_filter = static_df[static_df.TICKER == ticker]

        if static_df_filter.empty:
            prefix, suffix = ticker.rsplit(" ", maxsplit=1)
            ticker_pattern = prefix[:-1] + "[A-Z][0-9]+ "
            static_df_filter = static_df[static_df.TICKER.str.contains(ticker_pattern)]
            read_multiple_files = True
        else:
            read_multiple_files = False

        static_df = static_df_filter.sort_values(by='FUT_NOTICE_FIRST')

        return read_multiple_files, static_df

    def _read_ohlcv(self, ticker, start_date, end_date, resample_method='1B'):
        ohlcv_df = pd.DataFrame()
        filename = os.path.join(system.ohlcv_path, ticker + '.csv')

        if os.path.exists(filename):
            ohlcv_df = pd.read_csv(filename, index_col='DATE').rename(columns=self._BBG_FIELD_MAP)
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index)
            ohlcv_df = ohlcv_df[start_date:end_date]

            # only see data up to as of date (inclusively)
            ohlcv_df = ohlcv_df[:self._as_of_date]

            #ohlcv_df.ffill(inplace=True)
            #ohlcv_df = ohlcv_df[ohlcv_df.HIGH.notnull() & ohlcv_df.LOW.notnull() & ohlcv_df.VOLUME.notnull()]
            ohlcv_df = ohlcv_df.dropna(axis='index')

            if resample_method:
                ohlcv_df = ohlcv_df.resample(resample_method).pad()

        return ohlcv_df

    def _calc_ohlcv(self, adj_dates: pd.DataFrame = None, method='panama', resample_method='1B'):

        if method not in ['ratio', 'panama', 'no_adj']:
            raise ValueError('method is not valid: ' + method)

        if not isinstance(adj_dates, pd.DataFrame):
            raise ValueError('Calendar must be pandas DataFrame')

        df_no_adj = pd.concat([self._read_ohlcv(row.TICKER, row.START_DATE, row.END_DATE)
                        for _, row in adj_dates.iterrows()])

        if resample_method:
            df_no_adj = df_no_adj.resample(resample_method).pad()

        df = df_no_adj.copy()
        close = df.CLOSE

        next_df = pd.concat([self._read_ohlcv(row.NEXT_TICKER, row.END_DATE, row.END_DATE)
                             for _, row in adj_dates.iterrows()])

        next_close = next_df.CLOSE

        if method == 'panama':
            adj = (next_close - close.asof(next_close.index))
            adj = adj[::-1].cumsum()[::-1].reindex(df.index, method='bfill').fillna(0)
            df.OPEN = (df.OPEN + adj)
            df.HIGH = (df.HIGH + adj)
            df.LOW = (df.LOW + adj)
            df.CLOSE = (df.CLOSE + adj)
        elif method == 'ratio':
            adj = (next_close / close.asof(next_close.index))
            adj = adj[::-1].cumprod()[::-1].reindex(df.index, method='bfill').fillna(1)
            df.OPEN = (df.OPEN * adj)
            df.HIGH = (df.HIGH * adj)
            df.LOW = (df.LOW * adj)
            df.CLOSE = (df.CLOSE * adj)
        elif method == 'no_adj':
            adj = next_close  # to get the data frame shape
            adj[:] = 0

        return df_no_adj, df, adj

    def _calc_annual_yield(self):
        return (self.unadjusted_ohlcv.CLOSE - self._back_ohlcv_df.CLOSE) / (self._n_day_btw_contracts / system.n_day_in_year) /  (self.daily_price_vol * system.root_n_bday_in_year)