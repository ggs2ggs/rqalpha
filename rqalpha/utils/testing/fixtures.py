import os
import pickle
from contextlib import contextmanager

from unittest.mock import MagicMock
import six


class RQAlphaFixture(object):
    def init_fixture(self):
        pass


class EnvironmentFixture(RQAlphaFixture):
    def __init__(self, *args, **kwargs):
        super(EnvironmentFixture, self).__init__(*args, **kwargs)
        self.env_config = {}
        self.env = None

    def init_fixture(self):
        from rqalpha.utils import RqAttrDict
        from rqalpha.environment import Environment

        super(EnvironmentFixture, self).init_fixture()
        self.env = Environment(RqAttrDict(self.env_config))

    @contextmanager
    def mock_env_method(self, name, mock_method):
        origin_method = getattr(self.env, name)
        setattr(self.env, name, mock_method)
        yield
        setattr(self.env, name, origin_method)

    @contextmanager
    def mock_env_get_last_price(self, *args, **kwargs):
        origin_get_last_price = self.env.get_last_price
        self.env.get_last_price = MagicMock(*args, **kwargs)
        yield
        self.env.get_last_price = origin_get_last_price


class TempDirFixture(RQAlphaFixture):
    def __init__(self, *args, **kwargs):
        super(TempDirFixture, self).__init__(*args, **kwargs)
        self.temp_dir = None

    def init_fixture(self):
        from tempfile import TemporaryDirectory

        super(TempDirFixture, self).init_fixture()
        self.temp_dir = TemporaryDirectory()


class BaseDataSourceFixture(TempDirFixture, EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(BaseDataSourceFixture, self).__init__(*args, **kwargs)

        from rqalpha.const import MARKET

        self.env_config = {
            "base": {
                "market": MARKET.CN
            }
        }
        self.bcolz_data = {key: None for key in [
            "stocks", "indexes", "futures", "funds", "original_dividends", "trading_dates",
            "yield_curve", "split_factor", "ex_cum_factor", "st_stock_days", "suspended_days"
        ]}
        self.pk_data = {"instruments": None}

        self.base_data_source = None

    def init_fixture(self):
        from rqalpha.data.base_data_source import BaseDataSource

        super(BaseDataSourceFixture, self).init_fixture()
        default_bundle_path = os.path.abspath(os.path.expanduser('~/.rqalpha/bundle'))

        for key, table in six.iteritems(self.bcolz_data):
            table_relative_path = "{}.bcolz".format(key)
            if table is None:
                os.symlink(
                    os.path.join(default_bundle_path, table_relative_path),
                    os.path.join(self.temp_dir.name, table_relative_path)
                )
            else:
                table.rootdir = os.path.join(self.temp_dir.name, "{}.bcolz".format(key))
                table.flush()

        for key, obj in six.iteritems(self.pk_data):
            pickle_raletive_path = "{}.pk".format(key)
            if obj is None:
                os.symlink(
                    os.path.join(default_bundle_path, pickle_raletive_path),
                    os.path.join(self.temp_dir.name, pickle_raletive_path)
                )
            else:
                with open(os.path.join(self.temp_dir.name, "{}.pk".format(key)), "wb+") as out:
                    pickle.dump(obj, out, protocol=2)

        # TODO: use mocked bcolz file
        self.base_data_source = BaseDataSource(self.temp_dir.name)


class BenchmarkAccountFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(BenchmarkAccountFixture, self).__init__(*args, **kwargs)

        self.benchmark_account_total_cash = 4000
        self.benchmark_account = None

    def init_fixture(self):
        from rqalpha.model.base_position import Positions
        from rqalpha.mod.rqalpha_mod_sys_accounts.position_model.stock_position import StockPosition
        from rqalpha.mod.rqalpha_mod_sys_accounts.account_model import BenchmarkAccount

        super(BenchmarkAccountFixture, self).init_fixture()

        self.benchmark_account = BenchmarkAccount(self.benchmark_account_total_cash, Positions(StockPosition))


class BarDictPriceBoardFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(BarDictPriceBoardFixture, self).__init__(*args, **kwargs)
        self.price_board = None

    def init_fixture(self):
        from rqalpha.core.bar_dict_price_board import BarDictPriceBoard

        super(BarDictPriceBoardFixture, self).init_fixture()

        self.price_board = BarDictPriceBoard()
        self.env.set_price_board(self.price_board)


class MatcherFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(MatcherFixture, self).__init__(*args, **kwargs)

        from rqalpha.mod.rqalpha_mod_sys_simulation import __config__ as mod_sys_simulation_config
        from rqalpha.const import MATCHING_TYPE

        self.env_config = {
            "mod": {
                "sys_simulation": mod_sys_simulation_config
            }
        }

        self.env_config["mod"]["sys_simulation"]["matching_type"] = MATCHING_TYPE.CURRENT_BAR_CLOSE

        self.matcher = None

    def init_fixture(self):
        from datetime import datetime
        from rqalpha.mod.rqalpha_mod_sys_simulation.matcher import Matcher

        super(MatcherFixture, self).init_fixture()

        print(Matcher, type(self.env_config["mod"]))

        self.matcher = Matcher(self.env, self.env_config["mod"].sys_simulation)
        self.matcher.update(datetime(2018, 8, 16, 11, 5), datetime(2018, 8, 16, 11, 5))


class BookingFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(BookingFixture, self).__init__(*args, **kwargs)

        from rqalpha.model.booking import BookingPositions
        from rqalpha.const import POSITION_DIRECTION

        self.long_positions = BookingPositions(POSITION_DIRECTION.LONG)
        self.short_positions = BookingPositions(POSITION_DIRECTION.SHORT)
        self.booking = None

    def init_fixture(self):
        from rqalpha.model.booking import Booking

        super(BookingFixture, self).init_fixture()

        self.booking = Booking(self.long_positions, self.short_positions)


class IndicatorFixture(EnvironmentFixture):
    def __init__(self, *args, **kwargs):
        super(IndicatorFixture, self).__init__(*args, **kwargs)

        self.indicator = None

    def init_fixture(self):
        from rqalpha_mod_indicator.indicator_board import IndicatorBoard
        from rqalpha_mod_indicator.pt_indicator_board import PTIndicatorBoard
        from rqalpha.const import RUN_TYPE

        super(IndicatorFixture, self).init_fixture()

        config = self.env.config
        if config.base.run_type in (RUN_TYPE.PAPER_TRADING, RUN_TYPE.LIVE_TRADING):
            self.indicator = PTIndicatorBoard()
        else:
            self.indicator = IndicatorBoard(config.base.start_date, config.base.end_date)
