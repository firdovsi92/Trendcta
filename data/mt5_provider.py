# -*- coding: utf-8 -*-
import datetime

import MetaTrader5 as mt5
import pandas as pd

import config.settings
from core.contract_store import Store, QuotesType
from core.logger import get_logger
from core.utility import ConnectionException
from data.data_provider import DataProvider

logger = get_logger('mt5_provider')


class MT5Provider(DataProvider):
    """
    MetaTrader 5 data provider for downloading and storing price data.
    """

    def __init__(self):
        super().__init__()
        self.library = 'mt5'
        self.connected = False
        self.api_timeout = getattr(config.settings, 'mt5_timeout', 30)

    def connect(self):
        """Initialize MetaTrader5 terminal session."""
        if self.connected:
            return True

        init_kwargs = {}
        if getattr(config.settings, 'mt5_login', None):
            init_kwargs['login'] = config.settings.mt5_login
        if getattr(config.settings, 'mt5_password', None):
            init_kwargs['password'] = config.settings.mt5_password
        if getattr(config.settings, 'mt5_server', None):
            init_kwargs['server'] = config.settings.mt5_server
        if getattr(config.settings, 'mt5_path', None):
            init_kwargs['path'] = config.settings.mt5_path
        init_kwargs['timeout'] = self.api_timeout

        if not mt5.initialize(**init_kwargs):
            logger.warning("MT5 initialize failed: %s", str(mt5.last_error()))
            return False

        # Explicit login for some terminals requires calling mt5.login
        if getattr(config.settings, 'mt5_login', None):
            if not mt5.login(
                config.settings.mt5_login,
                password=getattr(config.settings, 'mt5_password', None),
                server=getattr(config.settings, 'mt5_server', None),
            ):
                logger.warning("MT5 login failed: %s", str(mt5.last_error()))
                return False

        self.connected = True
        return True

    def disconnect(self):
        if self.connected:
            mt5.shutdown()
            self.connected = False

    def download_instrument(self, instrument, **kwargs):
        if not self.connect():
            raise ConnectionException("Couldn't connect to MetaTrader 5")

        recent = kwargs.get('recent', False)
        contracts = self._resolve_contracts(instrument, recent)
        db = getattr(instrument, 'mt5_storage', 'MT5')
        store_symbol = getattr(instrument, 'mt5_store_symbol',
                               getattr(instrument, 'mt5_symbol', instrument.ib_code))
        timeframe = self._timeframe(instrument)

        logger.info('Downloading MT5 contracts for instrument: %s', instrument.name)
        for contract_label, symbol in contracts:
            data = self._download_symbol(symbol, timeframe, QuotesType.futures,
                                         contract_label=contract_label,
                                         start_year=getattr(instrument, 'backtest_from_year', None))
            if data is None:
                continue
            Store(self.library, QuotesType.futures, db + '_' + store_symbol).update(data)

        self.disconnect()
        return True

    def download_currency(self, currency, **kwargs):
        if not self.connect():
            raise ConnectionException("Couldn't connect to MetaTrader 5")

        fallback_symbol = None
        if getattr(currency, 'ib_symbol', None) and getattr(currency, 'ib_currency', None):
            fallback_symbol = currency.ib_symbol + currency.ib_currency
        symbol = getattr(currency, 'mt5_symbol', fallback_symbol or currency.code)
        db = getattr(currency, 'mt5_storage', 'MT5FX')
        timeframe = self._timeframe(currency)
        data = self._download_symbol(symbol, timeframe, QuotesType.currency,
                                     start_year=datetime.datetime.now().year - 6)
        if data is not None:
            Store(self.library, QuotesType.currency, db + '_' + symbol).update(data)

        self.disconnect()
        return True

    def download_spot(self, spot):
        if not self.connect():
            raise ConnectionException("Couldn't connect to MetaTrader 5")

        symbol = getattr(spot, 'mt5_symbol', getattr(spot, 'ib_symbol', None) or spot.name)
        db = getattr(spot, 'mt5_storage', 'MT5')
        timeframe = self._timeframe(spot)
        data = self._download_symbol(symbol, timeframe, QuotesType.others)
        if data is not None:
            Store(self.library, QuotesType.others, db + '_' + symbol).update(data)

        self.disconnect()
        return True

    def download_contract(self, instrument, cont_name, **kwargs):
        symbol = self._build_symbol(instrument, cont_name)
        return self.download_table(QuotesType.futures, symbol, instrument,
                                   contract_label=cont_name)

    def download_table(self, q_type, symbol, obj, contract_label=None):
        timeframe = self._timeframe(obj)
        data = self._download_symbol(symbol, timeframe, q_type, contract_label=contract_label)
        if data is None:
            return False
        db = getattr(obj, 'mt5_storage', 'MT5')
        store_symbol = getattr(obj, 'mt5_store_symbol', symbol)
        Store(self.library, q_type, db + '_' + store_symbol).update(data)
        return True

    def drop_symbol(self, q_type, database, symbol, **kwargs):
        Store(self.library, q_type, database + '_' + symbol).delete()

    def drop_instrument(self, instrument):
        store_symbol = getattr(instrument, 'mt5_store_symbol',
                               getattr(instrument, 'mt5_symbol', instrument.ib_code))
        self.drop_symbol(QuotesType.futures, getattr(instrument, 'mt5_storage', 'MT5'),
                         store_symbol)

    def drop_currency(self, currency):
        symbol = getattr(currency, 'mt5_symbol', currency.ib_symbol + currency.ib_currency)
        self.drop_symbol(QuotesType.currency, getattr(currency, 'mt5_storage', 'MT5FX'),
                         symbol)

    def _resolve_contracts(self, instrument, recent=False):
        """
        Returns list of (contract_label, mt5_symbol) tuples.
        """
        if getattr(instrument, 'mt5_contracts', None):
            return list(getattr(instrument, 'mt5_contracts').items())

        if getattr(instrument, 'mt5_symbol', None):
            label = getattr(instrument, 'mt5_symbol')
            return [(label, instrument.mt5_symbol)]

        # Fallback to IB code + contract for backfill; may need manual override per instrument
        if recent and hasattr(instrument, 'roll_progression'):
            try:
                label = instrument.roll_progression().tail(1).iloc[0] - 100
            except Exception:
                label = getattr(instrument, 'first_contract', datetime.date.today().year * 100 + 1)
        else:
            label = getattr(instrument, 'first_contract', datetime.date.today().year * 100 + 1)

        return [(label, self._build_symbol(instrument, label))]

    def _build_symbol(self, instrument, cont_name):
        if getattr(instrument, 'mt5_symbol', None):
            return instrument.mt5_symbol
        if getattr(instrument, 'mt5_symbol_prefix', None):
            return f"{instrument.mt5_symbol_prefix}{cont_name}"
        return instrument.ib_code + str(cont_name)

    def _download_symbol(self, symbol, timeframe, q_type, contract_label=None, start_year=None):
        start = datetime.datetime(start_year or (datetime.datetime.now().year - 6), 1, 1)
        end = datetime.datetime.now()
        rates = mt5.copy_rates_range(symbol, timeframe, start, end)

        if rates is None or len(rates) == 0:
            logger.warning("No MT5 data returned for symbol %s: %s", symbol, str(mt5.last_error()))
            return None

        data = pd.DataFrame(rates)
        if data.empty:
            logger.warning("Empty MT5 data for symbol %s", symbol)
            return None

        data.rename(columns={'tick_volume': 'volume', 'real_volume': 'volume'}, inplace=True)
        data['date'] = pd.to_datetime(data['time'], unit='s')
        data['date'] = data['date'].dt.tz_localize(None)

        if q_type == QuotesType.futures:
            data['contract'] = self._contract_value(contract_label or symbol)
            return data[['date', 'contract', 'open', 'high', 'low', 'close', 'volume']].copy()
        elif q_type == QuotesType.currency:
            data.rename(columns={'close': 'rate'}, inplace=True)
            return data[['date', 'rate', 'high', 'low']].copy()
        else:
            return data[['date', 'close']].copy()

    def _timeframe(self, obj):
        tf = getattr(obj, 'mt5_timeframe', 'D1')
        # Accept both MT5.TIMEFRAME_* and string values like 'D1'
        if isinstance(tf, int):
            return tf
        attr_name = 'TIMEFRAME_%s' % tf
        return getattr(mt5, attr_name, mt5.TIMEFRAME_D1)

    def _contract_value(self, contract_label):
        try:
            return int(contract_label)
        except Exception:
            return str(contract_label)
