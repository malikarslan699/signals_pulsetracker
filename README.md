# PulseSignal Pro
### Professional Trading Signals Platform
**signals.pulsetracker.net**

Real-time crypto and forex trading signals powered by ICT Smart Money concepts and 35+ professional indicators.

## Features
- **ICT Smart Money** — Order Blocks, FVG, Liquidity Zones, OTE, Killzones
- **35+ Indicators** — EMA, RSI, MACD, BB, VWAP, Stoch, Ichimoku, Supertrend + more
- **500+ Pairs** — Binance Futures crypto + Forex (Gold, Oil, Majors)
- **Confidence Score** — 0-100 multi-confluence scoring system
- **Telegram Alerts** — Instant signal notifications
- **SaaS Platform** — Admin panel, reseller system, Stripe payments

## Quick Start

```bash
git clone <repo>
cd trading_indicator_pro
cp backend/.env.example backend/.env
# Edit backend/.env with your API keys
chmod +x scripts/setup.sh
./scripts/setup.sh
```

## Stack
- **Backend**: Python 3.12 + FastAPI + Celery + Redis + PostgreSQL
- **Frontend**: Next.js 15 + TypeScript + Tailwind CSS + TradingView Charts
- **Engine**: Custom ICT + 35+ indicator modules (numpy/pandas)
- **Infra**: Docker Compose + Nginx + SSL

## Indicator Engine
See `backend/engine/` for the full indicator implementation:
- `indicators/` — Standard technical indicators
- `ict/` — ICT Smart Money modules
- `scoring/` — Multi-confluence scoring system
- `signal_generator.py` — Signal generation engine

## API Documentation
After starting: http://localhost:8000/api/docs
