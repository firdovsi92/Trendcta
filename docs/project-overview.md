# Project Overview

## Summary
- Sistem: Sistematik vadeli işlemler trend takip stratejisi (PyTrendFollow)
- Tür: Python backend / trading pipeline (monolith)
- Amaç: IB + Quandl veri kaynaklarıyla vadeli kontrat fiyatlarını indirip, taşıma/ewmac kurallarıyla portföy oluşturmak ve otomatik emir vermek

## Temel Bileşenler
- Veri toplama: `download.py` (Quandl, IB) + HDF5 depolama (`config/settings.py.template` ile yol ve API anahtarları)
- Doğrulama: `validate.py` ile indirilen kontratların tutarlılık ve güncellik kontrolü
- Planlayıcı: `scheduler.py` ile günlük veya anlık portföy güncellemesi ve emir iletimi
- Strateji tanımı: `config/strategy.py.template` (risk hedefleri, kural ağırlıkları, portföy ağırlıkları)
- Enstrüman & portföy konfigleri: `config/instruments.py`, `config/portfolios.py`, `config/currencies.py`, `config/spots.py`
- Notebook’lar: `docs/*.ipynb` (bilgilendirici ve R&D)

## Hızlı Gerçekler
- Dil: Python 3
- Paketler: `requirements.txt` (pandas/numpy/scipy/matplotlib/seaborn, quandl, IbPy2, pymongo, pytest vb.)
- Veri depolama: HDF5 (varsayılan), isteğe bağlı MongoDB log’ları
- Çalışma modu: CLI komutları; CI/CD dosyası bulunamadı
- Giriş noktaları: `download.py`, `validate.py`, `scheduler.py`, `trade.sh`, `bootstrap.py`
