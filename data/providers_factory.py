
def get_provider(name):
    if name == 'quandl':
        from data.quandl_provider import QuandlProvider
        return QuandlProvider()
    elif name == 'ib':
        from data.ib_provider import IBProvider
        return IBProvider()
    elif name == 'mt5':
        from data.mt5_provider import MT5Provider
        return MT5Provider()
    else:
        raise Exception('Unknown data provider name: %s' % name)
