# PyTrendFollow: Çalışma Prensibi ve Portföy Yapısı

## Genel Çerçeve
- Sistem tam otomatik vadeli işlem (futures) trend-following altyapısı; CTA benzeri: geniş enstrüman sepeti, kur farkı yönetimi, volatilite hedeflemesi ve taşıma (carry) + trend sinyali birleşimi.
- Strateji, kural bazlı ve tekrarlanabilir: fiyat verisi toplanır, sürekli kontrat (Panama) serileri üretilir, sinyaller normalize edilip ağırlıklandırılır, hedef volatiliteye göre pozisyon büyüklükleri çıkarılır, IB API üzerinden emirler gönderilir.
- Varsayılan hedef: yıllık ~12.5% volatilite (config/strategy.py.template) ve sermaye 500k taban alınarak ~25% beklenen volatilite ortamında ~20% yıllık getiri hedefi.

## Veri Yaşam Döngüsü
- **Kaynaklar**: `download.py` üzerinden `quandl` ve/veya `ib` sağlayıcıları (`data/providers_factory.py`).
- **Depolama**: `core/contract_store.py` -> `core.hdfstore.py`; HDF5 dosya yapısı `price_data/` altında `[provider]/[q_type]/[symbol].h5` şemasıyla tutulur.
- **Enstrüman tanımı**: `config/instruments.py` her future için takas kodu, kontrat ayları, point_value, komisyon, spread, roll günleri vb. içerir. Portföy kompozisyonu `config/portfolios.py` içinde listelenir.
- **Veri birleştirme**: `core/data_feed.get_instrument()` enstrüman bazında sağlayıcı önceliğiyle (instrument.contract_data ∩ settings.data_sources) veriyi okur ve merge eder; benzer mantık döviz (`get_currency`) ve spot serileri (`get_spot`) için geçerlidir.
- **Sürekli kontrat üretimi**: `Instrument.panama_prices()` kontrat getirilerini Panamalı kümülatif seri haline getirir; roll takvimi `core.utility.generate_roll_progression()` ile enstrüman bazında ayarlanır.
- **Validasyon**: `Portfolio.validate()` her enstrüman için veri tazeliği, volatilite, taşıma sinyali ve Panama serisi yaşı gibi kontroller yapar; sorunlu enstrümanlar blacklist’e atılır.

## Strateji Katmanı (Rules & Forecasts)
- Varsayılan kurallar `config/strategy.default_rules`: `ewmac` (trend) ve `carry`.
- **Trend (EWMAC)**: `trading.rules.ewmac` 8/16/32/64 periyotlu üssel MA farkları; `norm_forecast` ile ±20 bandına normalize edilir.
- **Carry**: `trading.rules.carry_spot` veya `carry_next` spot veya bir sonraki kontrat ile fiyat farkını vade farkına bölerek taşımayı hesaplar; 90 günlük ewm yumuşatma uygulanır.
- Diğer kurallar (kapalı varsayılan): mean reversion (`mr`), breakout, open/close vb.; gerektiğinde `instrument.rules` içine eklenebilir.
- **Ağırlıklar**: 
  - Kural ağırlıkları `config.strategy.rule_weights`; enstrüman bazlı kopyalanıp `Instrument.weights` olarak saklanır.
  - Enstrüman ağırlıkları `config.strategy.portfolio_weights` portföy seviyesinde çarpan olarak kullanılır.
- **Forecast birleşimi**: `Instrument.weighted_forecast()` -> `core.utility.weight_forecast` sinyalleri ağırlıklandırır ve ortalama mutlak değer 10 olacak şekilde normalize eder (lookahead bias uyarısı). Çıktı ±20 ile sınırlandırılır.

## Strateji Katmanı: Derinlemesine Akış
- **Fiyat Ön İşleme**: Her enstrüman için Panama serisi (`panama_prices`) kontrat getirilerinden roll takvimine göre kümüle edilir; EWM volatilite (`return_volatility`) point_value ve FX ile ölçeklenir.
- **Trend Sinyali (EWMAC)**:
  - Dört horizon: 8/16/32/64 günlük kısa EMA, her biri kendi uzun EMA’sı (4x uzun) ile fark alınır.
  - Seriler `norm_vol` ile vol-normlanır (bootstrap tabanlı ölçekleme), ardından `norm_forecast` ile ortalama mutlak 10 olacak şekilde normalize edilir ve ±20’ye kırpılır.
- **Carry Sinyali**:
  - Spot varsa `carry_spot`: spot − aktif kontrat fiyatı, vade gününe (`time_to_expiry`) bölünür, 90g EWM ile yumuşatılır, normalize edilir.
  - Spot yoksa `carry_next`: aktif kontrat ile bir sonraki (veya `carry_prev`) kontrat arasındaki 5g ortalama fiyat farkı alınır, ay farkına bölünür, normalize + 90g EWM.
- **Opsiyonel Kurallar**: `mr` (negatif EWMAC), `breakout` (40/80/160/320 lookback yüksek-düşük bandı), `open_close`, `buy_and_hold`, `sell_and_hold`. Açmak için `Instrument.rules` listesine eklenir.
- **Kural Ağırlama ve Birleştirme**:
  - Enstrüman init’inde `rule_weights` DataFrame’e alınır; bootstrap sonuçları isteğe bağlı yazılabilir (`Instrument.bootstrap`).
  - `weight_forecast`: ağırlıklı ortalama → `norm_forecast` ile yeniden ölçek → ±20 klip.
- **Pozisyon Boyutlama (Enstrüman Bazında)**:
  - Formül: `pos = forecast * (daily_vol_target * capital / 10) / return_volatility` → FX çarpanı (`Currency.rate`) → `np.around` ile kontrat sayısı tamsayılanır.
  - `forecast` mutlak 20 ile sınırlı, `daily_vol_target = annual_vol_target / sqrt(252)`.
- **Portföy Overlay ve Trade Süzgeci**:
  - `accountCurve` pozisyonları enstrüman ağırlıklarıyla çarpar; portföy toplam getirilerinin 50g EWM std’sine göre `vol_norm()` ile yeniden ölçekler (1.5x klip) → hedef vol’e uyum.
  - `chunk_trades`: log ölçekli yuvarlama ile küçük trade’leri filtreler; pozisyonlar 5 gün ffill ile veri kesintisinde korunur, sonrasında kapanır.
  - Maliyet terimleri (spread, komisyon, slippage) geri test getirilerine yansıtılır; gerçek emirler IB’de market/adaptive olarak gider.
- **Ticaret Çıktısı**: `Portfolio.frontier()` roll takviminden aktif kontratı alır, ağırlıklı pozisyonu hedef frontier olarak verir; `IBstate.sync_portfolio` mevcut pozisyon + açık emirlerle farkı alıp sadece gerekli kontratları gönderir.
- **Gözlenen Risk Varsayımları**: Vol hedefi sabit; korelasyon tabanlı risk-parite yok, drawdown tabanlı kısma yok. Spread/komisyon sabit kabul ediliyor; likidite kısıtları volume>1 filtresiyle minimal tutulmuş.

## Risk ve Portföy Yönetimi
- **Pozisyon Boyutlama**: `Instrument.position()` günlük volatilite hedefi (`daily_volatility_target`) ve sermaye (`capital`) ile risk-parite benzeri ölçekleme yapar. Formül: `forecast * (target_vol * capital / 10) / return_volatility`; döviz çarpanı `Currency.rate()` üzerinden uygulanır.
- **Volatilite Ölçümü**: `Instrument.return_volatility()` Panama getirilerini point_value ile çarpıp 36 günlük EWM std ile ölçer.
- **Portföy Birleştirme**: `Portfolio.curve()` -> `trading.accountcurve.accountCurve` pozisyonları enstrüman ağırlıklarıyla çarpar, portföy toplam volatilitesine göre `vol_norm()` ile 1.5x’e kadar kısar; trade yumuşatma `chunk_trades()` ve 5 gün ffill ile aşırı işlem engellenir.
- **Maliyet Modellemesi**: Komisyon/spread `AccountCurve.commissions()` ve `spreads()` ile trade farklarına uygulanır; slippage yarım günlük fiyat farkıyla (`transaction_returns`) simüle edilir.
- **Performans Ölçümleri**: Sharpe, Sortino, Calmar, drawdown süre/derinliği `accountCurve.stats_list()` içinde hazır gelir; `Portfolio.instrument_stats()` ve `bootstrap_rules/portfolio` araştırma amaçlı kullanılır.

## İşlem Akışı ve Yürütme
- **Frontier üretimi**: `Portfolio.frontier()` son gün için hedef kontrat ve miktarları, enstrüman ağırlıkları ve güncel roll takvimini dikkate alarak üretir.
- **IB Senkronizasyonu**: `trading.ibstate.IBstate`
  - TWS/Gateway’e bağlanır (`ib_connection.get_next_id` yardımıyla clientId), hesap ve pozisyonları çeker.
  - Açık emirleri (`open_orders`) kontrol eder, hedef-pozisyon farkından `trade` miktarını çıkarır.
  - `place_order()` adaptif market emirlerini (BUY/SELL) gönderir; emir akışı hata kodlarına göre yeniden dener.
- **Zamanlama**: `scheduler.py`
  - `config.strategy.portfolio_sync_time` (varsayılan 07:00) için günlük görev kurar; `--now` anlık, `--quit` döngüyü kapatır.
  - Her çalıştırmada portföy cache temizlenir, gerekirse validasyon yapılır ve tüm uygun hesaplar için sync çalıştırılır.
- **İşlem sırası (özet)**:
  1) `download.py [quandl|ib]` ile fiyat/kur/spot verisi çekilir ve HDF5’e yazılır.
  2) `validate.py` ile veri tazeliği ve sinyaller kontrol edilir, sorunlu enstrümanlar blacklist’e girer.
  3) `scheduler.py --now` veya zamanlanmış görev frontier hesaplar, IB pozisyonlarıyla farkı bulur, açık emir yoksa adaptif market emirleri yollar.

## CTA Benzerliği ve Notlar
- **Benzerlikler**: Çoklu vadeli işlemler, trend + carry faktörleri, risk hedefleme, pozisyonların vol/FX ayarlı olması, otomatik rollover ve veri çoklamaya karşı sağlayıcı birleşimi CTA yapısına benziyor.
- **Farklar/Sadeleştirmeler**: 
  - Varsayılan kural seti (ewmac+carry) basitleştirilmiş; opsiyonel kurallar manuel açılıyor.
  - Vol hedefi tek katman (portföy) ve 1.5x üst sınır; dinamik risk overlay veya drawdown tabanlı kısma yok.
  - Likidite kontrolleri temel (volume>1, spread/komisyon sabit); gerçek CTA’larda görülen derin slippage/market impact modellemesi sınırlı.
- **Genişletme fikirleri**: drawdown tabanlı risk overlay, cross-asset korelasyon ağırlık yeniden ayarı, execution algosu (limit/iceberg), veri kalite metriklerini scheduler öncesi bloklayıcı hale getirme.

## Konfigürasyon Dosyaları
- `config/settings.py`: veri kaynakları, depolama, IB portu, log ayarları.
- `config/strategy.py`: vol hedefi, sermaye, kural ve enstrüman ağırlıkları, senkron saat.
- `config/instruments.py`: enstrüman roll, kontrat ayları, fiyat çarpanı, komisyon, veri sağlayıcı önceliği.
- `config/portfolios.py`: işlem yapılacak sepetler (p_all, p_trade vb.).

## Hızlı Bakış: Modül Haritası
- **Çekirdek**: `core.instrument`, `core.utility`, `core.data_feed`, `core.contract_store`.
- **Strateji & Portföy**: `trading.rules`, `trading.portfolio`, `trading.accountcurve`.
- **Operasyon**: `download.py`, `validate.py`, `scheduler.py`, `trading.ibstate`.

