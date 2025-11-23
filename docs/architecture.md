# Architecture

## Genel Yapı
- Tür: Tek parça (monolith) Python trading pipeline
- Katmanlar:
  - Veri toplama katmanı: `download.py`, `download.sh`; Quandl ve IB API’lerinden HDF5’e yazım
  - Doğrulama katmanı: `validate.py` ile veri bütünlüğü kontrolleri
  - Strateji/hesaplama katmanı: `trading/` ve `core/` altındaki kurallar, risk ve portföy mantığı (detay için kaynak okuması yapılmadı – hızlı tarama)
  - Orkestrasyon: `scheduler.py`, `trade.sh`, `bootstrap.py` ile zamanlama ve emir akışı
- Konfigürasyon: `config/settings.py` (kopya), `config/strategy.py` (kopya), enstrüman/portföy dosyaları

## Teknoloji Yığını
- Dil: Python 3
- Bağımlılıklar: numpy/pandas/scipy/matplotlib/seaborn, quandl, IbPy2, pymongo, schedule, arch, pytest
- Depolama: HDF5 (varsayılan), opsiyonel Mongo logları
- Entegrasyonlar: Interactive Brokers (TWS/Gateway, ib_port 4001), Quandl API

## Akış Özeti
1) Veri indirme (Quandl/IB) → HDF5’e yazım
2) Veri doğrulama (indirme sonrası kalite kontrol)
3) Strateji ve risk hesapları (trend takip, taşıma/ewmac kuralları)
4) Scheduler ile emir oluşturma ve gönderme

_Not: Hızlı tarama kapsamında kaynak dosyaları okunmadı; ayrıntılı sınıf/işlev haritası için derin tarama gerekir._
