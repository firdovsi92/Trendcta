# Development Guide

## Kurulum
1) Python 3.x kullanın. 
2) Bağımlılıklar: `pip install -r requirements.txt`
3) Yapılandırma kopyaları:
   - `cp config/settings.py.template config/settings.py` (IB/Quandl anahtarları, HDF5 yolu, IB portu, Mongo log URL’si)
   - `cp config/strategy.py.template config/strategy.py` (vol hedefi, kural ağırlıkları, portföy ağırlıkları, senkron saat)
4) (İsteğe bağlı) Tkinter ve arch derleme gereksinimleri için OS paketlerini kurun (README’de belirtilmiş).

## Geliştirme Akışı
- Veri indirme: 
  - `python download.py quandl --concurrent` (opsiyonel bayrak, Quandl rate limitine dikkat)
  - `python download.py ib`
- Doğrulama: `python validate.py` (indirilen enstrüman veri tutarlılığı ve güncellik kontrolü)
- Ticaret/planlama:
  - Anlık çalıştır: `python scheduler.py --now --quit`
  - Günlük zamanlanmış: `python scheduler.py`
- Yardımcı betikler: `trade.sh` (sarmalayıcı), `bootstrap.py` (başlatma yordamı), `download.sh`/`pytest.sh` (kısa yol komut dosyaları).

## Test
- Temel: `pytest` (varsayılan `pytest.ini`) 
- Test dizini: `tests/`

## Çalışma Ortamı ve Veri
- Veri dizini: HDF5 için `price_data/quotes` (settings ile belirlenir)
- IB Logları: İsteğe bağlı MongoDB (`iblog_host`)
- Not: Hızlı tarama modunda kaynak dosyaları okunmadı; yollar README ve şablonlardan türetildi.

## CI/CD
- Projede CI tanımı bulunamadı. İhtiyaç halinde `.github/workflows` veya eşdeğeri eklenmeli.
