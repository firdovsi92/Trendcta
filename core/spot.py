from core import data_feed
import config.spots
import config.settings


class Spot(object):
    """
    Object representing the underlying price for a future contract
    """
    @classmethod
    def load_all(cls):
        """Load all spots in the system into a dictionary"""
        return {v['name']: Spot(v['name']) for v in config.spots.spots_definitions}

    def __init__(self, name):
        """Initialise the spot with defaults, taking overrides from the config/currencies.py"""
        self.name = name
        self.ib_symbol = None
        self.quandl_symbol = None
        self.mt5_symbol = None
        self.mt5_storage = 'MT5'
        self.mt5_timeframe = 'D1'
        self.price_data = ['ib', 'quandl', 'mt5']
        self.multiplier = 1.0
        kwargs = config.spots.spots_all[name]
        for key, value in kwargs.items():
            setattr(self, key, value)

        if 'mt5' not in self.price_data and 'mt5' in config.settings.data_sources:
            self.price_data = list(self.price_data) + ['mt5']

    def __repr__(self):
        return self.name + ' (spot)'

    def get(self):
        """
        :return: close price as pd.Series
        """
        data = data_feed.get_spot(self)
        if data is None or data.empty:
            raise Exception("No price data for symbol: %s" % self)
        return data['close']
