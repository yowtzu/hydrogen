import pandas as pd
from collections import OrderedDict
from hydrogen.instrument import InstrumentFactory, Instrument
from hydrogen.trading_rules import signal_scalar, signal_clipper, EWMAC

class Portfolio:

    def __init__(self, name: str, cache_result=True):
        self.ticker_instrument_map = {}
        self.rules = [
            ('EWMAC_2_8', EWMAC, {"fast_span": 2, "slow_span": 8} ) ,
            ('EWMAC_4_16', EWMAC, {"fast_span": 4, "slow_span": 16} ) ,
            ('EWMAC_8_32', EWMAC, {"fast_span": 8, "slow_span": 32}),
            ('EWMAC_16_64', EWMAC, {"fast_span": 16, "slow_span": 64} ) ,
            ('EWMAC_32_128', EWMAC, {"fast_span": 32, "slow_span": 128}),
            ('EWMAC_62_256', EWMAC, {"fast_span": 64, "slow_span": 256}),
            # (carry, {"span":system.n_bday_in_3m})
        ]
        self._forecast = {}

    def set_instruments(self, ticker_list: list, as_of_date):
        instrument_factory = InstrumentFactory()
        self.ticker_instrument_map = { ticker:instrument_factory.create_instrument(ticker, as_of_date=as_of_date) for ticker in ticker_list }

    def _calc_forecast(self, clip=False):
        res = OrderedDict()
        for ticker, inst in self.ticker_instrument_map.items():
            forecasts = [ signal_scalar(rule(rulename, inst, **kargs)) for rulename, rule, kargs in self.rules ]
            if clip:
                forecasts = [ (signal_clipper(forecast)) for forecast in forecasts ]

            res[ticker] = pd.concat(forecasts, axis=1)

        self._forecast = res

    def _all_tickers_if_empty(self, ticker_list):
        if type(ticker_list) is str:
            ticker_list = [ ticker_list ]

        if not ticker_list:
            ticker_list = list(self.ticker_instrument_map.keys())

        return ticker_list

    def _all_rules_if_empty(self, rule_list):
        if type(rule_list) is str:
            rule_list = [ rule_list ]

        if not rule_list:
            rule_list = [ rulename for rulename, *_ in self.rules ]

        return rule_list

        [k for k, v in port.rules]

    def forecast(self, ticker_list=[], rule_list=[]):
        if not self._forecast:
            self._calc_forecast()

        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        res = { ticker:self._forecast[ticker][rule_list] for ticker in ticker_list}

        return res

    def cost(self, ticker_list=[]):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        res = { ticker:self.ticker_instrument_map[ticker].cost_in_SR[ticker] for ticker in ticker_list }
        return res

    def forecast_weights(self, inst_name=None, rule=None, cost=False):
        pass

    def position(self, inst_name=None, rule=None):
        pass

    def pnl(self, inst_name=None, rule=None, cost=False):
        pass


    def weight(self, inst):
        pass

