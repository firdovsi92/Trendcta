# PyTrendFollow Çalıştırma Rehberi

## Gereksinimler
- Python 3.10+ ve `python3-venv`
- Quandl API anahtarı, (opsiyonel) IB Gateway/TWS açık ve API portu (varsayılan 4001)
- Diskte veri için `config/settings.py` içindeki `hdf_path` (varsayılan `price_data/quotes`)
- Komutları çalıştırırken kök dizinde `PYTHONPATH=.` kullanın

## Kurulum Adımları
1. Sanal ortam: `python3 -m venv .venv && source .venv/bin/activate`
2. Bağımlılıklar: `pip install -r requirements.txt`
3. Yapılandırma dosyaları: `cp config/settings.py.template config/settings.py` ve `cp config/strategy.py.template config/strategy.py`
4. `config/settings.py` içini düzenle:
   - `quandl.ApiConfig.api_key` → kendi anahtarınız
   - `data_sources` → kullanacağınız kaynaklar (`quandl`, `ib`)
   - `ib_port`, `base_currency`, `hdf_path` gerektiği gibi güncellenir
5. IB kullanacaksanız Gateway/TWS’de API’yi açın ve portu `ib_port` ile eşleştirin.

## Veri İndirme
- Quandl: `PYTHONPATH=. .venv/bin/python download.py quandl --concurrent`
  - `--concurrent` yalnızca Quandl’da eşzamanlı istek hakkınız varsa kullanılmalı.
- IB: `PYTHONPATH=. .venv/bin/python download.py ib`
- Veriler `price_data/quotes/[provider]/[type]/[symbol].h5` altında toplanır.

## Veri Doğrulama
- `PYTHONPATH=. .venv/bin/python validate.py`
- Çıktıdaki `is_valid` sütunu `False` olan enstrümanlar veri eksikliği ya da eski fiyat nedeniyle işleme alınmaz.

## Hızlı Backtest / Frontier Kontrolü
```bash
PYTHONPATH=. .venv/bin/python - <<'PY'
from trading.portfolio import Portfolio
import config.portfolios

p = Portfolio(instruments=config.portfolios.p_trade)
report = p.validate()
print(report[['is_valid', 'price_age']].tail())

curve = p.curve()
print(curve.stats_list())        # Sharpe, volatilite vb.
print(curve.positions.tail(1))   # Son hedef pozisyonlar (frontier)
PY
```
- Doğrulama başarısızsa (veri yoksa) `curve()`/`frontier()` hesaplanamaz; önce veri indirip temizleyin.

## Test Çalıştırma
- `PYTHONPATH=. .venv/bin/pytest -q`
- Testlerin geçmesi için güncel Quandl/IB verisi indirilmeli; aksi hâlde fiyat/veri bulunamadı hataları oluşur.

## Operasyonel Kullanım
- Günlük tek sefer: `PYTHONPATH=. .venv/bin/python scheduler.py --now --quit`
- Sürekli planlı: `PYTHONPATH=. .venv/bin/python scheduler.py`
- Canlı emir yollamak için IB oturumu açık olmalı ve `config/settings.py` ayarları ile port/hesap bilgileri eşleşmeli.
