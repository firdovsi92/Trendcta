# Project Documentation Index

## Project Overview
- **Tür:** Monolith
- **Birincil Dil:** Python
- **Mimari:** Backend/service-style trading pipeline

## Quick Reference
- **Giriş Noktaları:** download.py, validate.py, scheduler.py, trade.sh, bootstrap.py
- **Veri Kaynakları:** Quandl, Interactive Brokers (IB port 4001)
- **Depolama:** HDF5 (varsayılan), opsiyonel Mongo logları

## Generated Documentation
- [Project Overview](./project-overview.md)
- [Architecture](./architecture.md)
- [Source Tree Analysis](./source-tree-analysis.md)
- [Development Guide](./development-guide.md)
- [API Contracts](./api-contracts.md) _(To be generated)_
- [Data Models](./data-models.md) _(To be generated)_
- [Component Inventory](./component-inventory.md) _(To be generated)_
- [Deployment Guide](./deployment-guide.md) _(To be generated)_
- [Integration Architecture](./integration-architecture.md) _(To be generated)_

## Existing Documentation
- [README](../README.md)
- Notebooks: `docs/*.ipynb` (Introduction, Working with Prices, Rolling & Carry, How our system works, How to test new rules, Getting started with Interactive Brokers)

## Getting Started
1) `cp config/settings.py.template config/settings.py` ve anahtarları doldur
2) `cp config/strategy.py.template config/strategy.py`
3) `pip install -r requirements.txt`
4) `python download.py quandl --concurrent` ve/veya `python download.py ib`
5) `python validate.py`
6) `python scheduler.py --now --quit` veya `python scheduler.py`
