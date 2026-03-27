# PulseSignal Pro — Project Overview

> **Live Platform:** https://signals.pulsetracker.net
> **Status:** Production · Active
> **Stack:** Next.js 15 · FastAPI · PostgreSQL · Redis · Docker

---

## What Is PulseSignal Pro?

PulseSignal Pro is an **AI-powered crypto & forex trading signal platform** built for real traders.

It automatically scans 30+ trading pairs across multiple timeframes, applies **ICT (Inner Circle Trader) methodology**, smart money concepts, and advanced technical analysis — then fires precise buy/sell signals with entry, take-profit, and stop-loss levels directly to users in real time.

Users receive signals on the web platform and via **Telegram bot**, with full historical performance tracking and analytics.

---

## Core Features

### For Traders (Users)
| Feature | Description |
|--------|-------------|
| **Live Signal Feed** | Real-time buy/sell signals with confidence scores (0–100) |
| **ICT Analysis** | Fair Value Gaps, Order Blocks, Market Structure, Liquidity Zones |
| **Signal History** | Full history with PnL tracking, win rate, TP/SL outcomes |
| **Telegram Alerts** | Instant signal delivery to personal Telegram with custom filters |
| **Market Scanner** | Scan results by pair, timeframe, direction, confidence |
| **Signal Detail** | Per-signal breakdown: entry/TP1/TP2/TP3/SL, indicators, chart zones |
| **Alert Configs** | Custom alert rules: market, direction, timeframe, minimum confidence |
| **Stats Dashboard** | Platform-wide analytics: win rate, signal volume, scanner health |

### For Administrators
| Feature | Description |
|--------|-------------|
| **User Management** | View all users, edit roles/plans/status, reset passwords |
| **Package Manager** | Edit plan prices, features, duration, badges — live without redeploy |
| **System Config** | Scanner settings, signal confidence threshold, maintenance mode |
| **Integration Config** | Telegram bot token, Stripe keys, SMTP email, Binance/TwelveData API keys |
| **Provider Health** | Live SMTP and Telegram connectivity test from admin panel |
| **Analytics Dashboard** | Revenue metrics (MRR, yearly, lifetime), plan distribution, signal stats |

---

## Subscription Plans

| Plan | Price | Duration | Key Features |
|------|-------|----------|-------------|
| **Trial** | Free | 24 hours | Delayed signals, 7-day history, crypto only |
| **Monthly Pro** | $29 | 1 month | Real-time signals, Telegram alerts, full analytics |
| **Yearly Pro** | $199 | 1 year | Monthly Pro + 180-day history, priority support |
| **Lifetime Pro** | $299 | Forever | Everything, unlimited access, no recurring fees |

> All plan prices and features are **admin-editable** from the dashboard — no code changes needed.

---

## How It Works (Technical Flow)

```
Market Data (Binance / TwelveData)
          │
          ▼
  Scanner Worker (runs every 10 min)
  ┌─────────────────────────────────┐
  │  Fetches OHLCV candles          │
  │  Runs ICT analysis              │
  │  Calculates confidence score    │
  │  Fires signal if score ≥ 60     │
  └────────────┬────────────────────┘
               │
       Saves to PostgreSQL
               │
       Publishes to Redis Pub/Sub
               │
    ┌──────────┴──────────┐
    ▼                     ▼
WebSocket Push       Alert Worker
(Browser/App)        (Telegram Bot)
```

---

## Tech Stack

### Backend
- **FastAPI** (Python 3.12) — REST API + WebSocket
- **PostgreSQL** — Primary database (users, signals, subscriptions, alerts)
- **Redis** — Live signal cache, pub/sub for real-time, config storage
- **SQLAlchemy (async)** — ORM with Alembic migrations
- **JWT Auth** — Access + refresh token system (HS256)
- **Stripe** — Payment processing (Monthly/Yearly/Lifetime checkout)
- **python-telegram-bot** — Telegram bot for alerts and account linking
- **Binance REST API** — Crypto OHLCV data
- **TwelveData API** — Forex OHLCV data

### Frontend
- **Next.js 15** (App Router, TypeScript)
- **TanStack Query v5** — Data fetching, caching, mutations
- **Zustand v5** — Auth state (persisted to localStorage)
- **Tailwind CSS** — Utility-first styling with custom design tokens
- **Lucide React** — Icons
- **React Hot Toast** — Notifications

### Infrastructure
- **Docker Compose** — All services containerized
- **Nginx** (system-level) — Reverse proxy, SSL termination
- **Certbot / Let's Encrypt** — HTTPS on `signals.pulsetracker.net`

---

## Project File Structure

```
trading_indicator_pro/
│
├── backend/
│   ├── app/
│   │   ├── api/v1/               # REST API routes
│   │   │   ├── auth.py           # Register, login, refresh, verify email
│   │   │   ├── signals.py        # Live signals, history, signal detail
│   │   │   ├── scanner.py        # Scanner status and results
│   │   │   ├── alerts.py         # Alert config CRUD
│   │   │   ├── subscriptions.py  # Plans, Stripe checkout, webhook
│   │   │   ├── pairs.py          # Watchlist, pair analysis
│   │   │   ├── websocket.py      # Real-time WebSocket endpoint
│   │   │   └── admin/
│   │   │       ├── users.py      # User management
│   │   │       ├── config.py     # System config
│   │   │       ├── packages.py   # Package/plan management
│   │   │       └── analytics.py  # Revenue and user analytics
│   │   ├── models/               # SQLAlchemy ORM models
│   │   ├── schemas/              # Pydantic request/response schemas
│   │   ├── services/             # Business logic layer
│   │   ├── core/                 # Auth, permissions, exceptions
│   │   └── main.py               # FastAPI app entry point
│   ├── workers/
│   │   ├── scanner_worker.py     # Main market scanning loop
│   │   └── alert_task.py         # Telegram alert delivery
│   ├── indicators/               # Technical analysis modules
│   │   ├── ict_analysis.py       # ICT methodology implementation
│   │   ├── trend.py              # Trend detection
│   │   └── momentum.py           # Momentum indicators
│   ├── telegram_bot.py           # Telegram bot commands
│   └── alembic/                  # Database migrations
│
├── frontend/
│   ├── app/
│   │   ├── (app)/                # Authenticated app pages
│   │   │   ├── dashboard/        # Main trading dashboard
│   │   │   ├── history/          # Signal history + sorting
│   │   │   ├── scanner/          # Market scanner view
│   │   │   ├── alerts/           # Alert configuration
│   │   │   ├── stats/            # Platform statistics
│   │   │   ├── settings/         # User account settings
│   │   │   ├── signal/[id]/      # Individual signal detail
│   │   │   └── admin/            # Admin panel (role-gated)
│   │   │       ├── (overview)
│   │   │       ├── users/
│   │   │       ├── packages/
│   │   │       ├── config/
│   │   │       └── analytics/
│   │   ├── (auth)/               # Public auth pages
│   │   │   ├── login/
│   │   │   └── register/
│   │   └── pricing/              # Public pricing page
│   ├── components/               # Reusable UI components
│   ├── hooks/                    # Custom React hooks
│   ├── lib/                      # API client, formatters, constants
│   ├── store/                    # Zustand state (auth, signals)
│   └── types/                    # TypeScript interfaces
│
├── docker-compose.yml
└── .env
```

---

## API Overview

Base URL: `https://signals.pulsetracker.net/api/v1`

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Create account |
| POST | `/auth/login` | Get JWT tokens |
| GET | `/auth/me` | Current user profile |
| GET | `/signals/live` | Live active signals |
| GET | `/signals/history` | Historical signals with PnL |
| GET | `/signals/{id}` | Single signal detail |
| GET | `/scanner/results` | Latest scanner output |
| GET | `/subscriptions/plans` | All available plans |
| POST | `/subscriptions/checkout` | Stripe checkout session |
| GET/POST | `/alerts/` | Alert config CRUD |
| WS | `/ws/signals` | Real-time signal stream |
| GET | `/admin/packages/` | Package definitions (admin) |
| PUT | `/admin/packages/{slug}` | Update package (admin) |

---

## Roles & Access

| Role | Access Level |
|------|-------------|
| `user` | Standard subscriber access based on plan |
| `premium` | Legacy premium tag |
| `admin` | Admin panel access (no sensitive config) |
| `superadmin` | Admin + can see/edit integrations config |
| `owner` | Full access including Stripe, Telegram, SMTP keys |
| `reseller` | Reseller portal access |

---

## Market Coverage

**Crypto (via Binance Futures)**
- BTC, ETH, BNB, SOL, XRP, ADA, DOGE, AVAX, DOT, LINK, and 20+ more

**Forex (via TwelveData)**
- EUR/USD, GBP/USD, USD/JPY, AUD/USD, USD/CAD, and major pairs

**Timeframes:** 5m · 15m · 1H · 4H · 1D

---

## Signal Scoring System

Each signal is scored 0–100 based on a weighted combination:

```
ICT Analysis      × weight (default 1.0)
Trend Strength    × weight (default 1.0)
Momentum          × weight (default 1.0)
─────────────────────────────────────────
Final Score → Only fired if ≥ min_confidence (default 60)
```

Weights are **admin-configurable** in real time without redeployment.

---

## Contact & Access

- **Platform:** https://signals.pulsetracker.net
- **Telegram Bot:** @pulsesignalprobot
- **Admin Panel:** https://signals.pulsetracker.net/admin (role-gated)
