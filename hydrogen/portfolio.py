import numpy as np
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
        self._position = {}

    def set_instruments(self, ticker_list: list, as_of_date):
        instrument_factory = InstrumentFactory()
        self.ticker_instrument_map = { ticker:instrument_factory.create_instrument(ticker, as_of_date=as_of_date) for ticker in ticker_list }

    def _calc_forecast(self, clip=False):
        res = {}
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

    def _calc_position(self):
        res = {}

        ticker_list = self._forecast.keys()
        volatility_scalar = { ticker:system.vol_target_cash_daily / self.ticker_instrument_map[ticker].instrument_value_vol for ticker in ticker_list }

        position = {ticker: self._forecast[ticker].multiply(volatility_scalar[ticker], axis=0) / system.avg_abs_forecast
                    for ticker in ticker_list}

        self._position = position

    def position(self, ticker_list=[], rule_list=[], buffered_position=True, trade_to_edge=False, round_position=False):
        def apply_buffer_one_signal(opt_pos, trade_to_edge, round_position):
            """
            Apply a buffer to a position
            If position is outside the buffer, we either trade to the edge of the
            buffer, or to the optimal
            If we're rounding positions, then we floor and ceiling the buffers.
            :param opt_pos: optimal position
            :type opt_pos: pd.Series
            :param trade_to_edge: Trade to the edge (TRue) or the optimal (False)
            :type trade_to_edge: bool
            :param round_position: Produce rounded positions
            :type round_position: bool
            :returns: pd.Series
            """

            def apply_buffer_one_signal_one_period(previous_pos, opt_pos, lower_limit, upper_limit, trade_to_edge):
                """
                Apply a buffer to a position, single period
                If position is outside the buffer, we either trade to the edge of the
                buffer, or to the optimal
                :param previous_pos: last position we had
                :type previous_pos: float
                :param opt_pos: ideal position
                :type opt_pos: float
                :param upper_limit: top of buffer
                :type upper_limit: float
                :param lower_limit: bottom of buffer
                :type lower_limit: float
                :param trade_to_edge: Trade to the edge (TRue) or the optimal (False)
                :type trade_to_edge: bool
                :returns: float
                """

                if np.isnan(upper_limit) or np.isnan(lower_limit) or np.isnan(opt_pos):
                    return previous_pos

                if previous_pos > upper_limit:
                    if trade_to_edge:
                        return upper_limit
                    else:
                        return opt_pos
                elif previous_pos < lower_limit:
                    if trade_to_edge:
                        return lower_limit
                    else:
                        return opt_pos
                else:
                    return previous_pos

            buffer = opt_pos.abs() * 0.1
            lower_limit = opt_pos - buffer
            upper_limit = opt_pos + buffer

            if round_position:
                opt_pos = opt_pos.round()
                upper_limit = upper_limit.round()
                lower_limit = lower_limit.round()

            current_position = 0.0
            buffered_position_list = []

            for x, y, z in zip(opt_pos, lower_limit, upper_limit):
                current_position = apply_buffer_one_signal_one_period(current_position, x, y, z, trade_to_edge)
                buffered_position_list.append(current_position)

            buffered_position = pd.Series(buffered_position_list, index=opt_pos.index)
            buffered_position[opt_pos.isnull()] = np.nan
            return buffered_position

        if not self._position:
            self._calc_position()

        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        position = {ticker: self._position[ticker][rule_list] for ticker in ticker_list}

        if buffered_position:
            position = {ticker: df.apply(apply_buffer_one_signal, args=(trade_to_edge, round_position)) for ticker, df
                        in position.items()}

        return position

    def turnover(self, ticker_list=[], rule_list=[], buffered_position=True, trade_to_edge=False, round_position=False):
        position = self.position(ticker_list, rule_list, buffered_position, trade_to_edge, round_position)
        one_way_turnover = {key: value.diff().abs() for key, value in position.items()}
        return one_way_turnover

    def cost(self, ticker_list=[], rule_list=[], buffered_position=True, trade_to_edge=False, round_position=False):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)
        one_way_turnover = self.turnover(ticker_list, rule_list, buffered_position, trade_to_edge, round_position)
        cost = {ticker: self.ticker_instrument_map[ticker].cost for ticker in ticker_list}
        res = {ticker: one_way_turnover[ticker].multiply(cost[ticker], axis=0) for ticker in ticker_list}
        return res

    def pnl(self, ticker_list=[], rule_list=[], buffered_position=True, trade_to_edge=False, round_position=False,
            delay=0):
        ticker_list = self._all_tickers_if_empty(ticker_list)
        rule_list = self._all_rules_if_empty(rule_list)

        position = self._position
        pnl_one_contract = {
            ticker: self.ticker_instrument_map[ticker].price_diff * self.ticker_instrument_map[ticker].cont_size for
            ticker
            in ticker_list}
        gross_pnl = {ticker: position[ticker].shift(delay).multiply(pnl_one_contract[ticker], axis=0) for ticker in
                     ticker_list}

        cost = self.cost(ticker_list, rule_list, buffered_position, trade_to_edge, round_position)
        net_pnl = {ticker: gross_pnl[ticker].add(-cost[ticker]) for ticker in ticker_list}

        return gross_pnl, cost, net_pnl
