import pandas as pd
from collections import OrderedDict
from hydrogen.instrument import InstrumentFactory
from hydrogen.trading_rules import signal_scalar, signal_clipper, EWMAC, carry
import hydrogen.system as system

class Portfolio:

    def __init__(self, name: str, cache_result=True):
        self.ticker_instrument_map = {}
        self.rules = [
            ('EWMAC_2_8', EWMAC, {"fast_span": 2, "slow_span": 8} ) ,
            ('EWMAC_4_16', EWMAC, {"fast_span": 4, "slow_span": 16} ) ,
            ('EWMAC_8_32', EWMAC, {"fast_span": 8, "slow_span": 32}),
            ('EWMAC_16_64', EWMAC, {"fast_span": 16, "slow_span": 64} ) ,
            ('EWMAC_32_128', EWMAC, {"fast_span": 32, "slow_span": 128}),
            ('EWMAC_64_256', EWMAC, {"fast_span": 64, "slow_span": 256}),
            ('carry', carry, {"span":32})
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

    def forecast(self, ticker_list=[], rule_list=[]):
        if not self._forecast:
            self._calc_forecast()

        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        res = { ticker:self._forecast[ticker][rule_list] for ticker in ticker_list }

        return res

    def forecast_to_position(self, ticker_list=[], rule_list=[]):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        volatility_scalar = { ticker:system.vol_target_cash_daily / self.ticker_instrument_map[ticker].instrument_value_vol for ticker in ticker_list }

        forecast = self.forecast(ticker_list, rule_list)

        position = { ticker: forecast[ticker].multiply(volatility_scalar[ticker], axis=0) / system.avg_abs_forecast for ticker in ticker_list }

        return position

    def turnover(self, ticker_list=[], rule_list=[]):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        one_way_turnover = { key:value.diff().abs() for key, value in self.forecast_to_position(ticker_list, rule_list).items() }
        return one_way_turnover

    def standardised_cost(self, ticker_list=[]):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        res = { ticker:self.ticker_instrument_map[ticker].cost_in_SR for ticker in ticker_list }
        return res

    def cost(self, ticker_list=[], rule_list=[]):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)
        one_way_turnover = self.turnover(ticker_list, rule_list)
        standardised_cost = self.standardised_cost(ticker_list)
        res = { ticker:one_way_turnover[ticker].multiply(standardised_cost[ticker], axis=0) for ticker in ticker_list }
        return res

    def pnl(self, ticker_list=[], rule_list=[]):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        position = self.forecast_to_position(ticker_list, rule_list)
        price_diff = { ticker:self.ticker_instrument_map[ticker].price_diff for ticker in ticker_list }

        pnl = { ticker:position[ticker].multiply(price_diff[ticker], axis=0) for ticker in ticker_list }
        return pnl

    def optimise_forecast(self, ticker_list=[], rule_list=[]):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        f = self.pnl(ticker_list, rule_list)
        c = self.cost(ticker_list, rule_list)
        
        ### resample bla