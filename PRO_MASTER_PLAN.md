# TRADING INDICATOR PRO — MASTER PRODUCTION PLAN
### Deep Dive · Professional Grade · SaaS Architecture

> Version: 1.0 | Author: AI Architect | Date: 2026-03-26
> Status: READY FOR IMPLEMENTATION
> Rule: DO NOT modify any existing project file — this is a fresh module

---

## TABLE OF CONTENTS

1. [Executive Summary](#1-executive-summary)
2. [Product Vision & USP](#2-product-vision--usp)
3. [UI/UX Design Blueprint](#3-uiux-design-blueprint)
4. [Complete Indicator Engine](#4-complete-indicator-engine)
5. [ICT Concepts Deep Dive](#5-ict-concepts-deep-dive)
6. [Signal Scoring System](#6-signal-scoring-system)
7. [System Architecture](#7-system-architecture)
8. [Backend — FastAPI Service](#8-backend--fastapi-service)
9. [Frontend — Next.js App](#9-frontend--nextjs-app)
10. [Database Schema](#10-database-schema)
11. [Real-Time Engine](#11-real-time-engine)
12. [Scanner Engine](#12-scanner-engine)
13. [Telegram Bot System](#13-telegram-bot-system)
14. [Admin Panel](#14-admin-panel)
15. [SaaS Monetization](#15-saas-monetization)
16. [Reseller System](#16-reseller-system)
17. [Security Architecture](#17-security-architecture)
18. [DevOps & Deployment](#18-devops--deployment)
19. [File & Folder Structure](#19-file--folder-structure)
20. [Phase-by-Phase Execution Plan](#20-phase-by-phase-execution-plan)

---

## 1. EXECUTIVE SUMMARY

**Product Name:** TradingSignalPro (TSP)

**What it does:**
A real-time, AI-assisted trading signal scanner for Crypto (500+ pairs via Binance Futures) and Forex (Gold, Oil, Majors). It combines the most powerful indicator stack in the market — including ICT Smart Money concepts — to produce high-confidence LONG/SHORT signals with exact Entry, Stop-Loss, and Take-Profit levels.

**Who it serves:**
- Retail traders who want professional-grade signals
- Signal resellers who want white-label SaaS
- Telegram VIP channel operators

**Revenue Model:**
Free Trial → Monthly Subscription → Lifetime Deal → Reseller Licenses

**Tech Stack Summary:**

| Layer | Technology |
|-------|-----------|
| Backend API | Python 3.12 + FastAPI |
| Task Queue | Celery 5 + Redis 7 |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Frontend | Next.js 15 + TypeScript |
| Charts | TradingView Lightweight Charts |
| Styling | Tailwind CSS + shadcn/ui |
| Real-time | WebSocket (FastAPI + Binance) |
| Deployment | Docker Compose + Nginx |
| CI/CD | GitHub Actions |
| Payments | Stripe API |
| Telegram | python-telegram-bot v21 |

---

## 2. PRODUCT VISION & USP

### Core USP (Unique Selling Points)

```
1. ICT Smart Money Engine — Only platform with full ICT suite automated
2. Multi-Confluence Scoring — 15+ conditions checked per signal
3. Live Scanner — 500+ pairs, every 10 minutes, background workers
4. Professional UI — Dark mode, Binance/Voltrex style, mobile-first
5. Telegram VIP Push — Instant alerts with chart image attached
6. Admin + Reseller Control — Full white-label capability
7. Confidence Score 1–100 — Not just BUY/SELL but HOW CONFIDENT
```

### Competitor Analysis

| Platform | ICT? | Multi-TF? | Confidence? | Reseller? |
|----------|------|-----------|-------------|-----------|
| AltFins | No | Yes | Basic | No |
| MyCryptoParadise | Partial | No | No | No |
| TradingView | No | Yes | No | No |
| **TSP (Ours)** | **YES** | **YES** | **YES (1-100)** | **YES** |

---

## 3. UI/UX DESIGN BLUEPRINT

### Design Language

- **Theme:** Deep Navy + Purple/Blue gradients (reference: Voltrex screenshot)
- **Font:** Inter (headings) + JetBrains Mono (numbers/prices)
- **Color Palette:**
  - Background: `#0B0E1A`
  - Card Surface: `#111827`
  - Border: `#1F2937`
  - Green (Long/Profit): `#10B981`
  - Red (Short/Loss): `#EF4444`
  - Gold (ICT/Premium): `#F59E0B`
  - Purple Accent: `#8B5CF6`
  - Blue Accent: `#3B82F6`
  - Text Primary: `#F9FAFB`
  - Text Muted: `#6B7280`

### Pages & Screens

#### Page 1: Landing / Marketing Page
```
Header: Logo + Nav (Features, Pricing, Login)
Hero: "Professional Trading Signals with ICT Smart Money"
      [Animated live signal card preview]
Stats Bar: 500+ Pairs | 15+ Indicators | Real-time Alerts
Features Grid: 6 cards with icons
Pricing Section: 3 tiers
Testimonials
Footer
```

#### Page 2: Dashboard (Main App)
```
┌─────────────────────────────────────────────────────────┐
│ HEADER: Logo | Market Status | BTC Price | User Avatar  │
├──────────┬──────────────────────────────────────────────┤
│          │  STATS ROW                                   │
│ SIDEBAR  │  [Active Signals] [Win Rate] [Pairs Scanned] │
│          ├──────────────────────────────────────────────┤
│ Dashboard│  SIGNAL CARDS GRID (3 columns)               │
│ Scanner  │  ┌──────────┐ ┌──────────┐ ┌──────────┐    │
│ Watchlist│  │ BTCUSDT  │ │ ETHUSDT  │ │ SOLUSDT  │    │
│ Alerts   │  │ LONG ▲   │ │ SHORT ▼  │ │ LONG ▲   │    │
│ History  │  │ 87/100   │ │ 74/100   │ │ 91/100   │    │
│ Settings │  │ 45,905   │ │ 3,120    │ │ 185.40   │    │
│          │  └──────────┘ └──────────┘ └──────────┘    │
│          ├──────────────────────────────────────────────┤
│          │  MARKET HEATMAP (color-coded by signal)      │
└──────────┴──────────────────────────────────────────────┘
```

#### Page 3: Signal Detail Page
```
┌─────────────────────────────────────────────────────────┐
│ BTCUSDT — LONG Signal — Confidence: 91/100              │
├───────────────────────────┬─────────────────────────────┤
│ TRADINGVIEW CHART         │ SIGNAL DETAILS              │
│ (Full screen with ICT     │ Entry:    45,905 USDT       │
│  zones, OB, FVG overlaid) │ SL:       44,800 USDT       │
│                           │ TP1:      47,200 USDT       │
│                           │ TP2:      49,500 USDT       │
│                           │ RR Ratio: 1:2.4             │
│                           ├─────────────────────────────┤
│                           │ INDICATOR BREAKDOWN          │
│                           │ ✅ ICT Order Block: +20      │
│                           │ ✅ BOS Confirmed: +15        │
│                           │ ✅ RSI Oversold: +10         │
│                           │ ✅ BB Lower Break: +12       │
│                           │ ✅ Volume Spike: +8          │
│                           │ ✅ EMA Stack Bull: +10       │
│                           │ ✅ VWAP Support: +8          │
│                           │ ⬜ MACD Cross: 0             │
│                           │ Total: 83/100               │
├───────────────────────────┴─────────────────────────────┤
│ MTF ANALYSIS: 5m ✅ | 15m ✅ | 1H ✅ | 4H ⬜ | 1D ✅  │
└─────────────────────────────────────────────────────────┘
```

#### Page 4: Scanner / Screener
```
Filters:
  Market: [Crypto] [Forex] [All]
  Signal: [LONG] [SHORT] [All]
  TF:     [5m] [15m] [1H] [4H] [1D]
  Min Confidence: [Slider 50–100]
  Indicators: [Multi-select checkboxes]

Table:
  Pair | Price | Signal | TF | Confidence | Entry | SL | TP1 | Time | Action
  Sortable columns, color-coded rows
```

#### Page 5: Trading Stats (Voltrex-style)
```
Balance Chart (Growth + Equity lines + Deposit/Withdrawal bars)
Advanced Statistics Panel:
  - Total Signals | Win Rate | Profit Factor
  - Longs Won % | Shorts Won %
  - Best/Worst Signal | Avg Signal Length
  - Sharpe Ratio | AHPR | Standard Deviation

Period Table: Today / This Week / This Month / This Year
```

#### Page 6: Mobile App (Mobile-first responsive)
```
Bottom Nav: Home | Scanner | Alerts | Portfolio | Profile
Signal Cards: Full-width, swipeable
Mini Chart: Sparkline per signal card (reference: mobile UI screenshot)
Bullish/Bearish meters: Progress bars per indicator
```

---

## 4. COMPLETE INDICATOR ENGINE

### Category A — Trend Indicators

#### A1. EMA Stack (Exponential Moving Averages)
```python
# EMAs: 9, 21, 50, 100, 200
# Bull Stack: EMA9 > EMA21 > EMA50 > EMA100 > EMA200
# Bear Stack: EMA9 < EMA21 < EMA50 < EMA100 < EMA200
# Score: +10 full bull stack, +5 partial (3/5 aligned)
```

#### A2. SMA Cross
```python
# Fast SMA(7) crosses above Slow SMA(25) → Bullish
# Score: +8 on golden cross, -8 on death cross
```

#### A3. DEMA / TEMA (Double/Triple EMA)
```python
# Less lag than standard EMA
# Confirms trend direction faster
```

#### A4. Hull Moving Average (HMA)
```python
# Ultra-smooth trend line
# HMA direction change = early reversal warning
# Score: +6 on direction confirmation
```

#### A5. Supertrend
```python
# ATR-based dynamic support/resistance
# Price above Supertrend = Bull, below = Bear
# Score: +10 when aligned with signal direction
```

#### A6. Ichimoku Cloud
```python
# Tenkan (9), Kijun (26), Senkou A/B, Chikou
# Price above cloud = strong bull
# Kumo twist = trend change alert
# Score: +12 price above/below cloud + +5 chikou confirm
```

---

### Category B — Momentum Indicators

#### B1. RSI (Relative Strength Index)
```python
# RSI(6) — Fast, RSI(14) — Standard
# Oversold: RSI < 30 → Long bias (+10)
# Overbought: RSI > 70 → Short bias (+10)
# RSI(6) < 20 → Extreme oversold (+15)
# RSI Divergence (price makes new low, RSI doesn't) → Reversal (+12)
```

#### B2. Stochastic RSI
```python
# K and D lines
# Stoch RSI < 20 and K crosses above D → Long (+8)
# Stoch RSI > 80 and K crosses below D → Short (+8)
```

#### B3. MACD
```python
# MACD(12, 26, 9)
# Signal line cross → +8
# Histogram direction change → +5
# MACD Divergence → +12
# Zero line cross → +6
```

#### B4. CCI (Commodity Channel Index)
```python
# CCI(20)
# CCI < -100 → Oversold (+6)
# CCI > 100 → Overbought (+6)
```

#### B5. Williams %R
```python
# %R < -80 → Oversold (+5)
# %R > -20 → Overbought (+5)
```

#### B6. Rate of Change (ROC)
```python
# Momentum strength confirmation
# ROC crossover zero line → +4
```

---

### Category C — Volatility Indicators

#### C1. Bollinger Bands (BB)
```python
# BB(20, 2.0)
# Price breaks below lower band → Long bias (+12)
# Price breaks above upper band → Short bias (+12)
# BB Squeeze (bandwidth < threshold) → Breakout imminent (+8)
# BB Walk (5+ candles outside band) → Trend continuation (+6)
```

#### C2. ATR (Average True Range)
```python
# ATR(14) — volatility measure
# Used for SL/TP calculation:
#   SL = Entry - (ATR × 1.5)
#   TP1 = Entry + (ATR × 2.0)
#   TP2 = Entry + (ATR × 3.5)
# High ATR + Signal = higher confidence in breakout (+5)
```

#### C3. Keltner Channels
```python
# EMA(20) ± ATR(10) × 1.5
# Price outside Keltner + BB squeeze = power breakout setup (+10)
```

#### C4. Donchian Channels
```python
# Highest high / Lowest low of N periods
# Breakout of channel → +7
```

---

### Category D — Volume Indicators

#### D1. Volume Spike Detection
```python
# Current volume > 2× average(20) → spike (+8)
# Volume spike on breakout candle → confirms signal (+10)
```

#### D2. OBV (On-Balance Volume)
```python
# OBV trending up with price up → confirmation (+6)
# OBV divergence → warning/reversal (+10)
```

#### D3. VWAP (Volume Weighted Average Price)
```python
# Intraday benchmark
# Price crosses above VWAP → bullish (+8)
# Price crosses below VWAP → bearish (+8)
# Price bounces off VWAP → +6
```

#### D4. CMF (Chaikin Money Flow)
```python
# CMF > 0.1 → buying pressure (+5)
# CMF < -0.1 → selling pressure (+5)
```

#### D5. MFI (Money Flow Index)
```python
# Volume-weighted RSI
# MFI < 20 → oversold (+6)
# MFI > 80 → overbought (+6)
```

---

### Category E — Market Structure

#### E1. HH / HL / LH / LL Detection
```python
# Higher High + Higher Low = Uptrend confirmed (+8)
# Lower High + Lower Low = Downtrend confirmed (+8)
# Structure break = potential reversal (+10)
```

#### E2. Break of Structure (BOS)
```python
# Price breaks previous swing high/low
# BOS bullish: price breaks last HH → Long (+12)
# BOS bearish: price breaks last LL → Short (+12)
```

#### E3. Change of Character (CHoCH)
```python
# After downtrend: first higher high = CHoCH → Early reversal (+15)
# After uptrend: first lower low = CHoCH → Early reversal (+15)
```

#### E4. Support / Resistance Zones
```python
# Auto-detected from swing points
# Test of key S/R level = +8
# S/R flip (resistance becomes support) = +10
```

---

### Category F — Fibonacci

#### F1. Fibonacci Retracement
```python
# Key levels: 0.236, 0.382, 0.5, 0.618, 0.786
# Price retraces to 0.618 (golden ratio) and holds → +10
# Price at 0.5 level with confluence → +7
```

#### F2. Fibonacci Extension
```python
# TP targets: 1.272, 1.414, 1.618, 2.0, 2.618
# Used for TP2, TP3 calculation
```

---

## 5. ICT CONCEPTS DEEP DIVE

> ICT = Inner Circle Trader methodology by Michael J. Huddleston
> Most powerful Smart Money framework available

### ICT Module 1: Order Blocks (OB)

```python
"""
Order Block Definition:
- Last bearish candle before a bullish impulse move (Bullish OB)
- Last bullish candle before a bearish impulse move (Bearish OB)

Detection Logic:
1. Find strong impulse move (3+ candle run, each > ATR)
2. Identify the last opposing candle before impulse
3. That candle's high/low range = Order Block zone
4. When price returns to OB = HIGH PROBABILITY entry

Scoring:
- Price enters fresh OB (untested) = +20
- Price enters OB with confluence = +25
- Mitigation (OB partially tapped) = +15
"""

def detect_order_blocks(candles, lookback=50):
    # Returns list of {type: 'bull'/'bear', high, low, timestamp, strength}
    pass
```

### ICT Module 2: Fair Value Gaps (FVG)

```python
"""
FVG Definition:
- 3-candle pattern where candle 1 high and candle 3 low don't overlap
- The gap = inefficiency that price will return to fill
- Bullish FVG: Candle1.high < Candle3.low (gap above)
- Bearish FVG: Candle1.low > Candle3.high (gap below)

Scoring:
- Price returns to FVG = +15
- FVG + OB confluence = +20
- Multiple timeframe FVG alignment = +25
"""

def detect_fvg(candles):
    # Returns list of {type, top, bottom, filled, timestamp}
    pass
```

### ICT Module 3: Liquidity Zones

```python
"""
Liquidity Types:
1. Buy-side liquidity: Highs where stop-losses of shorts cluster
2. Sell-side liquidity: Lows where stop-losses of longs cluster
3. Equal highs/lows: Double tops/bottoms (liquidity pools)

Detection:
- Swing highs within 0.1% of each other = Equal Highs (BSL)
- Swing lows within 0.1% of each other = Equal Lows (SSL)
- Previous day high/low = PDH/PDL liquidity

Scoring:
- Price sweeps liquidity then reverses = +20 (Liquidity Grab)
- Approaching liquidity from below (BSL) = short setup +15
- Approaching liquidity from above (SSL) = long setup +15
"""

def detect_liquidity_zones(candles):
    # Returns zones with type, price level, strength score
    pass
```

### ICT Module 4: Optimal Trade Entry (OTE)

```python
"""
OTE = 0.618–0.786 Fibonacci retracement of the impulse leg
after a structural break

Setup:
1. Price breaks structure (BOS/CHoCH)
2. Price retraces to 0.618–0.786 of the move
3. Enter at OTE level

This is the highest-probability ICT entry method

Scoring: +20 for perfect OTE entry
"""

def detect_ote(candles):
    pass
```

### ICT Module 5: Killzones (Time-Based Sessions)

```python
"""
ICT Killzones (High-probability trading times):
- London Open Killzone: 02:00–05:00 UTC
- New York Open Killzone: 07:00–10:00 UTC
- London Close Killzone: 10:00–12:00 UTC
- Asian Killzone: 20:00–00:00 UTC

Rule: Signals during killzone = higher confidence
Scoring: +8 if signal fires during a killzone
"""

KILLZONES = {
    'london_open': ('02:00', '05:00'),
    'ny_open': ('07:00', '10:00'),
    'london_close': ('10:00', '12:00'),
    'asian': ('20:00', '00:00'),
}
```

### ICT Module 6: Premium & Discount Arrays

```python
"""
Price divided into Premium (above 50% of range) and Discount (below)

Buy in Discount, Sell in Premium

Equilibrium = 0.5 Fibonacci of the current range

Scoring:
- Long signal in Discount zone = +10
- Short signal in Premium zone = +10
- Signal at Equilibrium = neutral (0)
"""
```

### ICT Module 7: Breaker Blocks

```python
"""
When an Order Block is mitigated (price trades through it),
the OB becomes a Breaker Block — now acts as opposite zone

Bullish Breaker: Failed bearish OB → now acts as support
Bearish Breaker: Failed bullish OB → now acts as resistance

Scoring: +15 on breaker block test
"""
```

### ICT Module 8: Mitigation Blocks

```python
"""
When price reverses before fully mitigating an OB,
the remaining portion = Mitigation Block

Scoring: +12 on mitigation block test
"""
```

### ICT Module 9: Inducement

```python
"""
Price creates a short-term high/low to induce retail traders
then sweeps that level before moving in the true direction

Pattern:
1. Trending move
2. Minor retracement creates a short-term level
3. Price sweeps that level (takes retail stops)
4. True move begins

Scoring: +18 on confirmed inducement + reversal
"""
```

### ICT Module 10: Daily Bias

```python
"""
HTF (Higher Timeframe) analysis to determine daily bias:
- 4H chart: Is price in premium or discount?
- Daily: Has price swept today's liquidity?
- Weekly: Which way is smart money positioned?

Scoring: +12 if signal direction matches daily bias
"""
```

---

## 6. SIGNAL SCORING SYSTEM

### Master Scoring Table

```
CATEGORY               | CONDITION                          | SCORE
-----------------------|------------------------------------|-------
ICT ORDER BLOCK        | Fresh OB test                      | +20
ICT FVG                | Price enters FVG                   | +15
ICT LIQUIDITY GRAB     | Sweep + reversal                   | +20
ICT OTE                | 0.618–0.786 retracement            | +20
ICT BREAKER            | Breaker block test                 | +15
ICT INDUCEMENT         | Confirmed inducement               | +18
ICT DAILY BIAS         | Aligned with HTF bias              | +12
ICT KILLZONE           | Signal during killzone             | +8
ICT PREMIUM/DISCOUNT   | Correct zone for direction         | +10
-----------------------|------------------------------------|-------
BOS / CHoCH            | Break of structure confirmed       | +12–15
MARKET STRUCTURE       | HH/HL or LH/LL sequence            | +8
S/R FLIP               | Resistance → Support (or vice)     | +10
-----------------------|------------------------------------|-------
EMA STACK              | Full 5-EMA alignment               | +10
SUPERTREND             | Aligned with signal                | +10
ICHIMOKU CLOUD         | Price above/below cloud            | +12
HMA DIRECTION          | Hull MA confirms                   | +6
-----------------------|------------------------------------|-------
RSI                    | Extreme level (< 30 or > 70)       | +10
RSI DIVERGENCE         | Classic divergence                 | +12
STOCH RSI CROSS        | K/D cross in extreme zone          | +8
MACD CROSS             | Signal line cross                  | +8
MACD DIVERGENCE        | Divergence from price              | +12
CCI EXTREME            | < -100 or > 100                    | +6
-----------------------|------------------------------------|-------
BB BREAKOUT            | Close outside BB                   | +12
BB SQUEEZE             | Low bandwidth + breakout           | +8
KELTNER SQUEEZE        | BB inside Keltner = power move     | +10
ATR HIGH               | High volatility confirms move      | +5
-----------------------|------------------------------------|-------
VOLUME SPIKE           | 2× average volume                  | +8
OBV CONFIRMS           | OBV trend matches direction        | +6
VWAP                   | Price cross or bounce              | +8
CMF CONFIRMS           | Money flow aligned                 | +5
-----------------------|------------------------------------|-------
FIBONACCI OTE          | Price at 0.618–0.786 retracement   | +10
FIB S/R                | Key fib level holds                | +7
-----------------------|------------------------------------|-------
MAX POSSIBLE SCORE                                          | ~300+
NORMALIZED TO 100 → confidence = (raw_score / max) × 100
```

### Confidence Bands

```
Score 90–100: ULTRA HIGH — Strong signal, all systems aligned
Score 75–89:  HIGH — Multiple confluences, act with confidence
Score 60–74:  MEDIUM — Good setup, wait for confirmation candle
Score 45–59:  LOW — Partial setup, risk management critical
Score < 45:   NO SIGNAL — Do not trade
```

---

## 7. SYSTEM ARCHITECTURE

```
┌─────────────────────────────────────────────────────────────────┐
│                     EXTERNAL DATA SOURCES                       │
│  Binance WS/REST    │  TwelveData API   │  Alpha Vantage API   │
└──────────┬──────────┴─────────┬─────────┴─────────┬────────────┘
           │                   │                     │
           ▼                   ▼                     ▼
┌─────────────────────────────────────────────────────────────────┐
│                    DATA INGESTION LAYER                         │
│  binance_ws.py  │  forex_fetcher.py  │  candle_normalizer.py   │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         REDIS CACHE                             │
│  Live candles  │  Latest signals  │  Scanner results  │  Locks  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
           ┌──────────────────┼──────────────────┐
           ▼                  ▼                  ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│  CELERY WORKER 1│ │  CELERY WORKER 2│ │  CELERY WORKER N│
│  Crypto Scanner │ │  Forex Scanner  │ │  Alert Sender   │
└────────┬────────┘ └────────┬────────┘ └────────┬────────┘
         │                  │                    │
         └──────────────────▼────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    INDICATOR ENGINE                             │
│  ict_engine.py  │  trend.py  │  momentum.py  │  volume.py      │
│  structure.py   │  scoring.py │  signal_gen.py                  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      POSTGRESQL DB                              │
│  signals │ pairs │ users │ subscriptions │ alerts │ audit_logs  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                      FASTAPI BACKEND                            │
│  /api/v1/signals  │  /api/v1/scanner  │  /api/v1/auth          │
│  /api/v1/admin    │  /api/v1/webhooks │  WebSocket /ws/signals  │
└─────────────────────────────┬───────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
     ┌────────────────┐  ┌─────────┐  ┌─────────────────┐
     │ Next.js App    │  │Telegram │  │ Webhook/Email   │
     │ (User + Admin) │  │  Bot    │  │   Alerts        │
     └────────────────┘  └─────────┘  └─────────────────┘
```

---

## 8. BACKEND — FastAPI SERVICE

### Directory: `tsp_backend/`

```
tsp_backend/
├── app/
│   ├── main.py                    # FastAPI app entry
│   ├── config.py                  # Settings / env vars
│   ├── database.py                # SQLAlchemy engine
│   ├── redis_client.py            # Redis connection
│   │
│   ├── api/
│   │   ├── v1/
│   │   │   ├── auth.py            # Login, register, JWT
│   │   │   ├── signals.py         # Signal CRUD + filter
│   │   │   ├── scanner.py         # Scanner status + results
│   │   │   ├── pairs.py           # Supported pairs
│   │   │   ├── alerts.py          # User alert config
│   │   │   ├── subscriptions.py   # Stripe webhooks + plans
│   │   │   ├── admin/
│   │   │   │   ├── users.py       # User management
│   │   │   │   ├── signals.py     # Override signals
│   │   │   │   ├── config.py      # System config
│   │   │   │   └── analytics.py   # Platform analytics
│   │   │   └── reseller/
│   │   │       ├── manage.py      # Reseller CRUD
│   │   │       └── commissions.py # Commission tracking
│   │   └── websocket.py           # WS endpoint
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── signal.py
│   │   ├── pair.py
│   │   ├── subscription.py
│   │   ├── alert.py
│   │   └── reseller.py
│   │
│   ├── schemas/
│   │   ├── signal.py              # Pydantic schemas
│   │   ├── user.py
│   │   └── scanner.py
│   │
│   ├── core/
│   │   ├── auth.py                # JWT utilities
│   │   ├── permissions.py         # Role-based access
│   │   └── exceptions.py
│   │
│   └── services/
│       ├── signal_service.py      # Business logic
│       ├── alert_service.py       # Trigger alerts
│       ├── stripe_service.py      # Payment handling
│       └── telegram_service.py    # Bot integration
│
├── engine/                        # INDICATOR ENGINE
│   ├── __init__.py
│   ├── data_fetcher.py            # Binance + Forex data
│   ├── candle_utils.py            # OHLCV normalization
│   ├── indicators/
│   │   ├── __init__.py
│   │   ├── trend.py               # EMA, SMA, HMA, Supertrend, Ichimoku
│   │   ├── momentum.py            # RSI, MACD, Stoch, CCI, Williams
│   │   ├── volatility.py          # BB, ATR, Keltner, Donchian
│   │   ├── volume.py              # OBV, VWAP, CMF, MFI, Volume Spike
│   │   ├── structure.py           # BOS, CHoCH, HH/HL/LH/LL
│   │   └── fibonacci.py           # Fib retracement + extension
│   ├── ict/
│   │   ├── __init__.py
│   │   ├── order_blocks.py        # OB detection
│   │   ├── fair_value_gaps.py     # FVG detection
│   │   ├── liquidity.py           # Liquidity zones
│   │   ├── ote.py                 # Optimal Trade Entry
│   │   ├── killzones.py           # Session killzones
│   │   ├── premium_discount.py    # P/D arrays
│   │   ├── breaker_blocks.py      # Breaker detection
│   │   └── daily_bias.py          # HTF bias analysis
│   ├── scoring/
│   │   ├── scorer.py              # Master scoring engine
│   │   └── normalizer.py          # Score → 0–100
│   └── signal_generator.py        # Final LONG/SHORT decision
│
├── workers/
│   ├── celery_app.py              # Celery config
│   ├── scanner_task.py            # Main scan task
│   ├── alert_task.py              # Alert dispatch task
│   └── cleanup_task.py            # Old signal cleanup
│
├── tests/
│   ├── test_ict.py
│   ├── test_indicators.py
│   ├── test_scoring.py
│   └── test_signals_api.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── .env.example
```

### Key API Endpoints

```python
# Authentication
POST   /api/v1/auth/register
POST   /api/v1/auth/login
POST   /api/v1/auth/refresh
POST   /api/v1/auth/logout

# Signals
GET    /api/v1/signals                   # List with filters
GET    /api/v1/signals/{id}              # Signal detail
GET    /api/v1/signals/live              # Latest live signals
GET    /api/v1/signals/history           # Historical signals

# Scanner
GET    /api/v1/scanner/status            # Scanner health
GET    /api/v1/scanner/results           # Latest scan results
POST   /api/v1/scanner/trigger           # Manual scan (admin)

# Pairs
GET    /api/v1/pairs                     # All supported pairs
GET    /api/v1/pairs/{symbol}/candles    # OHLCV data
GET    /api/v1/pairs/{symbol}/analysis   # Full indicator analysis

# Alerts
GET    /api/v1/alerts                    # User alert configs
POST   /api/v1/alerts                    # Create alert
PUT    /api/v1/alerts/{id}               # Update alert
DELETE /api/v1/alerts/{id}               # Delete alert

# Subscriptions
GET    /api/v1/subscriptions/plans       # Available plans
POST   /api/v1/subscriptions/checkout    # Create Stripe session
POST   /api/v1/subscriptions/webhook     # Stripe webhook

# WebSocket
WS     /ws/signals                       # Live signal stream
WS     /ws/scanner                       # Scanner progress

# Admin
GET    /api/v1/admin/users
PUT    /api/v1/admin/users/{id}
GET    /api/v1/admin/signals
DELETE /api/v1/admin/signals/{id}
GET    /api/v1/admin/analytics
GET    /api/v1/admin/config
PUT    /api/v1/admin/config
```

---

## 9. FRONTEND — Next.js App

### Directory: `tsp_frontend/`

```
tsp_frontend/
├── app/
│   ├── (marketing)/
│   │   ├── page.tsx               # Landing page
│   │   ├── pricing/page.tsx
│   │   └── features/page.tsx
│   ├── (app)/
│   │   ├── layout.tsx             # App shell (sidebar + header)
│   │   ├── dashboard/page.tsx
│   │   ├── scanner/page.tsx
│   │   ├── signal/[id]/page.tsx   # Signal detail
│   │   ├── watchlist/page.tsx
│   │   ├── history/page.tsx
│   │   ├── alerts/page.tsx
│   │   ├── stats/page.tsx         # Trading stats (Voltrex style)
│   │   └── settings/page.tsx
│   ├── (auth)/
│   │   ├── login/page.tsx
│   │   └── register/page.tsx
│   └── (admin)/
│       ├── layout.tsx
│       ├── dashboard/page.tsx
│       ├── users/page.tsx
│       ├── signals/page.tsx
│       ├── config/page.tsx
│       └── analytics/page.tsx
│
├── components/
│   ├── ui/                        # shadcn/ui base components
│   ├── charts/
│   │   ├── TradingViewChart.tsx   # TV lightweight chart
│   │   ├── BalanceChart.tsx       # Stats page chart
│   │   ├── HeatmapChart.tsx       # Market heatmap
│   │   └── SparklineChart.tsx     # Mini signal card chart
│   ├── signals/
│   │   ├── SignalCard.tsx         # Main signal card
│   │   ├── SignalTable.tsx        # Scanner table
│   │   ├── SignalDetail.tsx       # Full signal view
│   │   ├── SignalBadge.tsx        # LONG/SHORT badge
│   │   └── ConfidenceBar.tsx      # Score progress bar
│   ├── indicators/
│   │   ├── IndicatorBreakdown.tsx # Per-indicator scores
│   │   ├── ICTZoneOverlay.tsx     # Chart ICT overlays
│   │   └── MTFAnalysis.tsx        # Multi-TF grid
│   ├── scanner/
│   │   ├── ScannerFilters.tsx     # Filter bar
│   │   ├── ScannerStatus.tsx      # Live scan indicator
│   │   └── ScannerProgress.tsx
│   ├── layout/
│   │   ├── Sidebar.tsx
│   │   ├── Header.tsx
│   │   ├── MobileNav.tsx
│   │   └── MarketTicker.tsx       # Top scrolling ticker
│   └── common/
│       ├── PriceDisplay.tsx       # Formatted price
│       ├── TimestampDisplay.tsx
│       └── LoadingSkeleton.tsx
│
├── hooks/
│   ├── useSignals.ts              # React Query signal hooks
│   ├── useScanner.ts
│   ├── useWebSocket.ts            # Live WS connection
│   ├── usePairs.ts
│   └── useAuth.ts
│
├── store/
│   ├── signalStore.ts             # Zustand signal state
│   ├── scannerStore.ts
│   └── userStore.ts
│
├── lib/
│   ├── api.ts                     # Axios instance + interceptors
│   ├── formatters.ts              # Price, date formatters
│   └── constants.ts               # Timeframes, colors
│
├── types/
│   ├── signal.ts
│   ├── scanner.ts
│   └── user.ts
│
├── tailwind.config.ts
├── next.config.ts
└── package.json
```

### Key Components Detail

#### SignalCard Component
```tsx
// Displays: Pair, Direction (LONG/SHORT), Confidence bar,
// Entry/SL/TP, Timeframe, Mini sparkline chart, Time ago
// Color: Green card for LONG, Red card for SHORT
// Hover: Expands to show indicator breakdown
```

#### TradingViewChart Component
```tsx
// Integrates: @tradingview/lightweight-charts
// Overlays:
//   - EMA lines (9, 21, 50, 200)
//   - Bollinger Bands
//   - ICT Order Block rectangles (color-coded)
//   - ICT FVG zones (semi-transparent fill)
//   - Liquidity level lines
//   - Entry/SL/TP horizontal lines
//   - Volume bars at bottom
```

#### MTFAnalysis Component
```tsx
// Grid showing signal alignment across timeframes
// 5m | 15m | 1H | 4H | 1D
// Each cell: color (green=long, red=short, gray=neutral)
// + confidence score per TF
```

---

## 10. DATABASE SCHEMA

```sql
-- USERS
CREATE TABLE users (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email       VARCHAR(255) UNIQUE NOT NULL,
    username    VARCHAR(100) UNIQUE NOT NULL,
    password    VARCHAR(255) NOT NULL,           -- bcrypt hash
    role        VARCHAR(20) DEFAULT 'user',      -- user, admin, reseller
    plan        VARCHAR(20) DEFAULT 'free',      -- free, monthly, lifetime
    plan_expires_at TIMESTAMPTZ,
    telegram_chat_id BIGINT,
    is_active   BOOLEAN DEFAULT true,
    device_fingerprint VARCHAR(255),             -- 1 device lock
    reseller_id UUID REFERENCES users(id),       -- if sub-user
    created_at  TIMESTAMPTZ DEFAULT NOW(),
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- PAIRS
CREATE TABLE pairs (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    symbol      VARCHAR(20) NOT NULL,           -- BTCUSDT
    market      VARCHAR(20) NOT NULL,           -- crypto, forex
    exchange    VARCHAR(50) DEFAULT 'binance',
    is_active   BOOLEAN DEFAULT true,
    base        VARCHAR(10),                    -- BTC
    quote       VARCHAR(10)                     -- USDT
);

-- SIGNALS
CREATE TABLE signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    pair_id         UUID REFERENCES pairs(id),
    symbol          VARCHAR(20) NOT NULL,
    market          VARCHAR(20) NOT NULL,
    direction       VARCHAR(10) NOT NULL,        -- LONG, SHORT
    timeframe       VARCHAR(5) NOT NULL,         -- 5m, 15m, 1H, 4H, 1D
    confidence      SMALLINT NOT NULL,           -- 0–100
    entry           DECIMAL(20, 8) NOT NULL,
    stop_loss       DECIMAL(20, 8) NOT NULL,
    take_profit_1   DECIMAL(20, 8) NOT NULL,
    take_profit_2   DECIMAL(20, 8),
    take_profit_3   DECIMAL(20, 8),
    rr_ratio        DECIMAL(5, 2),
    raw_score       SMALLINT,                   -- pre-normalization score
    status          VARCHAR(20) DEFAULT 'active', -- active, tp1_hit, tp2_hit, sl_hit, expired
    score_breakdown JSONB,                       -- per-indicator scores
    ict_zones       JSONB,                       -- detected ICT elements
    candle_data     JSONB,                       -- OHLCV snapshot at signal
    fired_at        TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,
    closed_at       TIMESTAMPTZ,
    pnl_pct         DECIMAL(7, 2)               -- filled after close
);

CREATE INDEX idx_signals_symbol ON signals(symbol);
CREATE INDEX idx_signals_fired_at ON signals(fired_at DESC);
CREATE INDEX idx_signals_confidence ON signals(confidence DESC);

-- SIGNAL ALERTS (user notification config)
CREATE TABLE alert_configs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    channel         VARCHAR(20) NOT NULL,        -- telegram, email, webhook
    min_confidence  SMALLINT DEFAULT 70,
    directions      VARCHAR(20)[] DEFAULT ARRAY['LONG','SHORT'],
    timeframes      VARCHAR(5)[] DEFAULT ARRAY['1H','4H'],
    markets         VARCHAR(20)[] DEFAULT ARRAY['crypto'],
    pairs           VARCHAR(20)[],               -- NULL = all pairs
    is_active       BOOLEAN DEFAULT true
);

-- SUBSCRIPTIONS
CREATE TABLE subscriptions (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    plan            VARCHAR(20) NOT NULL,
    price           DECIMAL(10, 2) NOT NULL,
    currency        VARCHAR(5) DEFAULT 'USD',
    stripe_sub_id   VARCHAR(255),
    status          VARCHAR(20) DEFAULT 'active',
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ
);

-- RESELLERS
CREATE TABLE resellers (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID REFERENCES users(id),
    brand_name      VARCHAR(100),
    commission_pct  DECIMAL(5, 2) DEFAULT 20.00,
    total_earned    DECIMAL(12, 2) DEFAULT 0,
    is_active       BOOLEAN DEFAULT true
);

-- SCANNER RUNS
CREATE TABLE scanner_runs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    market          VARCHAR(20) NOT NULL,
    pairs_scanned   SMALLINT,
    signals_found   SMALLINT,
    duration_ms     INTEGER,
    started_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ,
    status          VARCHAR(20) DEFAULT 'running'
);

-- AUDIT LOGS
CREATE TABLE audit_logs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id         UUID,
    action          VARCHAR(100) NOT NULL,
    resource        VARCHAR(100),
    details         JSONB,
    ip_address      INET,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);
```

---

## 11. REAL-TIME ENGINE

### Binance WebSocket Manager

```python
# engine/data_fetcher.py

class BinanceWSManager:
    """
    Maintains live WebSocket connections to Binance Futures
    Handles reconnection, rate limits, and candle building

    Streams:
    - <symbol>@kline_5m  → 5-minute candles
    - <symbol>@kline_15m → 15-minute candles
    - <symbol>@kline_1h  → 1-hour candles
    - <symbol>@kline_4h  → 4-hour candles

    On each closed candle:
    1. Store in Redis (latest 500 candles per symbol per TF)
    2. Trigger indicator calculation
    3. If score threshold met → generate signal
    4. Push to Redis signal queue
    5. Alert workers pick up from queue
    """

    async def start(self, symbols: list[str], timeframes: list[str]):
        pass

    async def on_candle_close(self, symbol: str, tf: str, candle: dict):
        pass
```

### Redis Data Structure

```
# Candle data
redis_key: candles:{symbol}:{timeframe}
type: Redis List (RPUSH, max 500 entries)
value: JSON {open, high, low, close, volume, timestamp}

# Latest signal per symbol
redis_key: signal:{symbol}
type: Redis Hash
value: {direction, confidence, entry, sl, tp1, tp2, fired_at}

# Scanner queue
redis_key: scanner:queue
type: Redis List
value: symbol names to scan

# Active signals set
redis_key: signals:active
type: Redis Sorted Set (score = confidence)
value: signal JSON

# WebSocket broadcast channel
redis_key: ws:broadcast
type: Redis PubSub
```

---

## 12. SCANNER ENGINE

### Scan Flow

```python
# workers/scanner_task.py

@celery.task
def run_scanner(market: str = 'crypto'):
    """
    Runs every 10 minutes via Celery Beat

    Flow:
    1. Get all active pairs for market
    2. Split into batches of 50
    3. For each timeframe [5m, 15m, 1H, 4H]:
       a. Fetch latest candles from Redis (or Binance API)
       b. Run all indicators
       c. Run ICT analysis
       d. Calculate confidence score
       e. If score >= 60 → generate signal
       f. Store signal in PostgreSQL
       g. Push to Redis active signals
       h. Trigger alert task
    4. Update scanner_run record
    5. Broadcast scan completion via WebSocket
    """
    pass

@celery.task
def send_signal_alerts(signal_id: str):
    """
    Triggered after each new signal

    1. Find users with matching alert configs
    2. For each user:
       - If Telegram configured: send Telegram message
       - If email configured: send email
       - If webhook configured: POST to webhook URL
    """
    pass
```

### Scanner Scheduler (Celery Beat)

```python
CELERYBEAT_SCHEDULE = {
    'scan-crypto-every-10min': {
        'task': 'workers.scanner_task.run_scanner',
        'schedule': crontab(minute='*/10'),
        'args': ('crypto',)
    },
    'scan-forex-every-10min': {
        'task': 'workers.scanner_task.run_scanner',
        'schedule': crontab(minute='5-55/10'),
        'args': ('forex',)
    },
    'cleanup-old-signals': {
        'task': 'workers.cleanup_task.cleanup',
        'schedule': crontab(hour='*/6'),
    },
    'update-win-rates': {
        'task': 'workers.analytics_task.update_win_rates',
        'schedule': crontab(hour='*/1'),
    },
}
```

---

## 13. TELEGRAM BOT SYSTEM

### Signal Message Format

```
🚨 NEW SIGNAL ALERT

📊 Pair: BTCUSDT (Crypto)
📈 Direction: LONG ▲
⏱ Timeframe: 1H
🎯 Confidence: 91/100 ⚡ ULTRA HIGH

💰 Entry:     $45,905
🛑 Stop Loss: $44,800  (-2.4%)
🎯 TP1:       $47,200  (+2.8%)
🎯 TP2:       $49,500  (+7.8%)
⚖️  RR Ratio:  1:3.2

🔍 Top Confluences:
  ✅ ICT Order Block (Fresh)
  ✅ Break of Structure (Bull)
  ✅ RSI Oversold (27)
  ✅ BB Lower Band Break
  ✅ Volume Spike (3.2×)
  ✅ EMA Stack Bullish
  ✅ ICT Killzone (NY Open)

⏰ Time: 14:32 UTC
🔗 View Full Analysis → [Link]

━━━━━━━━━━━━━━━━━
⚠️ Not financial advice. DYOR.
```

### Bot Commands

```
/start       — Welcome + subscription info
/signals     — Latest 5 signals
/scanner     — Run manual scan check
/watchlist   — Your watchlist signals
/stats       — Your alert statistics
/subscribe   — Upgrade plan
/settings    — Configure alerts
/help        — Help menu
```

---

## 14. ADMIN PANEL

### Admin Dashboard Sections

```
1. OVERVIEW
   - Total users (active / inactive / trial)
   - Revenue today / MTD / YTD
   - Signals fired today
   - Scanner health status
   - Error rate

2. USER MANAGEMENT
   - Table: user list with plan, status, last login
   - Actions: ban, extend plan, reset device lock, impersonate
   - Filter: by plan, by country, by registration date

3. SIGNAL MANAGEMENT
   - Review all signals
   - Override/delete wrong signals
   - Mark signals as TP hit / SL hit manually
   - Win rate analytics per indicator

4. INDICATOR CONFIG (LIVE TUNING)
   - Sliders for each indicator threshold
   - Enable/disable specific indicators
   - Adjust scoring weights
   - Test changes on historical data before saving

5. SCANNER CONFIG
   - Scan interval (default 10 min)
   - Pairs whitelist/blacklist
   - Min confidence threshold to store signal
   - Max signals per scan

6. SUBSCRIPTION PLANS
   - Create / edit / delete plans
   - Set prices, features, limits
   - Coupon codes management

7. TELEGRAM MANAGEMENT
   - Configure VIP channel IDs
   - Message templates
   - Send manual broadcasts

8. ANALYTICS
   - Signal performance chart
   - Win rate by timeframe
   - Win rate by market
   - Win rate by indicator combination
   - Most profitable pairs
   - User conversion funnel

9. SYSTEM LOGS
   - API request logs
   - Error logs
   - Scanner run history
   - Alert delivery logs
```

---

## 15. SaaS MONETIZATION

### Plans

```
┌─────────────────────────────────────────────────────────┐
│ FREE TRIAL           │ MONTHLY PRO      │ LIFETIME      │
│ $0 / 24 hours        │ $29 / month      │ $149 one-time │
├─────────────────────────────────────────────────────────┤
│ 5 signals preview    │ Unlimited signals │ Everything    │
│ 1 pair only          │ 500+ pairs        │ + Priority    │
│ No Telegram alerts   │ Telegram alerts   │ + API Access  │
│ No history           │ Signal history    │ + Reseller    │
│ No ICT details       │ ICT breakdown     │ Option        │
└─────────────────────────────────────────────────────────┘
```

### Stripe Integration

```python
# On checkout:
# 1. Create Stripe checkout session
# 2. Redirect user to Stripe
# 3. On webhook success: update user plan in DB
# 4. Send welcome email + Telegram message
# 5. Log subscription event

# On monthly renewal:
# Stripe auto-renews, webhook updates plan_expires_at

# On cancellation:
# Plan remains until period end, then downgrade to free
```

---

## 16. RESELLER SYSTEM

```
RESELLER FLOW:
1. Admin approves reseller application
2. Reseller gets unique referral link + promo codes
3. Reseller creates sub-users (their own customers)
4. Revenue share: 20-30% commission (configurable per reseller)
5. Reseller dashboard shows:
   - Their users count
   - Revenue earned
   - Pending payouts
   - Performance stats

WHITE LABEL OPTION (Premium Reseller):
- Custom brand name on platform
- Custom Telegram bot name
- Custom domain support via CNAME
- Custom color scheme
```

---

## 17. SECURITY ARCHITECTURE

### Authentication & Authorization

```python
# JWT Tokens:
# Access token: 15 minutes
# Refresh token: 7 days (stored in Redis)
# On logout: blacklist refresh token in Redis

# Role-based access:
# user    → signals, scanner, alerts, own profile
# premium → + full ICT details, history, Telegram
# reseller → + sub-user management, commission view
# admin   → full access + config + system logs
```

### 1-Device Login Lock

```python
# On login:
# 1. Generate device fingerprint (IP + User-Agent + browser hash)
# 2. Store fingerprint in users.device_fingerprint
# 3. On next login from different device:
#    - Detect mismatch
#    - Send confirmation email to old device
#    - If confirmed: update fingerprint
#    - If not confirmed within 10 min: deny new device

# Admin can reset device lock from panel
```

### API Security

```python
# Rate limiting (Redis-based):
# /api/v1/auth/* → 5 req/min per IP
# /api/v1/signals → 60 req/min per user
# /api/v1/scanner → 10 req/min per user
# Admin endpoints → 100 req/min

# Additional:
# CORS: only allow known frontend domains
# SQL injection: SQLAlchemy ORM (no raw queries)
# XSS: sanitize all user inputs
# HTTPS only: redirect HTTP → HTTPS
# Secrets: all keys in .env, never in code
```

---

## 18. DevOps & DEPLOYMENT

### Docker Compose Stack

```yaml
# docker-compose.yml
services:
  postgres:     # PostgreSQL 16
  redis:        # Redis 7 with persistence
  backend:      # FastAPI (uvicorn)
  worker:       # Celery worker
  scheduler:    # Celery beat
  frontend:     # Next.js (standalone)
  nginx:        # Reverse proxy + SSL
```

### Nginx Configuration

```
frontend: → /
backend API: → /api/v1/
websocket: → /ws/
admin: → /admin/
```

### GitHub Actions CI/CD

```yaml
# On push to main:
# 1. Run pytest (backend tests)
# 2. Run next build (frontend)
# 3. Build Docker images
# 4. Push to registry
# 5. Deploy to VPS via SSH
# 6. Health check
# 7. Notify on Telegram if deploy fails
```

### Minimum Server Requirements

```
VPS / Cloud Server:
- RAM: 4GB minimum (8GB recommended)
- CPU: 2 vCPU minimum (4 recommended)
- Storage: 40GB SSD
- OS: Ubuntu 22.04 LTS
- Bandwidth: 1TB/month minimum

Estimated monthly cost: $20–40 (DigitalOcean/Hetzner)
```

---

## 19. FILE & FOLDER STRUCTURE

```
/srv/workspace/trading_indicator_pro/     ← existing (DO NOT TOUCH)
    myplan.md                             ← existing plan (DO NOT TOUCH)

/srv/workspace/tsp_backend/               ← NEW: Python backend
/srv/workspace/tsp_frontend/              ← NEW: Next.js frontend
/srv/workspace/tsp_docs/                  ← NEW: Documentation
    API.md
    INDICATOR_REFERENCE.md
    DEPLOYMENT.md
```

---

## 20. PHASE-BY-PHASE EXECUTION PLAN

### PHASE 1 — Foundation (Week 1–2)
```
[ ] Set up tsp_backend/ folder with FastAPI boilerplate
[ ] PostgreSQL + Redis with Docker Compose
[ ] User model + JWT auth (register, login, refresh)
[ ] Binance API connection + candle fetching
[ ] Basic signal model + DB schema
[ ] Health check endpoints
[ ] Basic tests
```

### PHASE 2 — Indicator Engine (Week 3–4)
```
[ ] Build trend.py (EMA, SMA, HMA, Supertrend, Ichimoku)
[ ] Build momentum.py (RSI, MACD, Stoch RSI, CCI)
[ ] Build volatility.py (BB, ATR, Keltner)
[ ] Build volume.py (OBV, VWAP, CMF, Volume Spike)
[ ] Build structure.py (BOS, CHoCH, HH/HL)
[ ] Build fibonacci.py (Retracement levels)
[ ] Unit tests for each indicator against known values
```

### PHASE 3 — ICT Engine (Week 5–6)
```
[ ] order_blocks.py — detection + scoring
[ ] fair_value_gaps.py — detection + fill tracking
[ ] liquidity.py — zone detection + sweep detection
[ ] ote.py — fibonacci + structure combo
[ ] killzones.py — session time check
[ ] premium_discount.py — range analysis
[ ] breaker_blocks.py — failed OB tracking
[ ] daily_bias.py — HTF analysis
[ ] ICT integration tests
```

### PHASE 4 — Scanner Engine (Week 7)
```
[ ] Signal scorer (master scoring logic)
[ ] Signal generator (LONG/SHORT decision)
[ ] Celery setup + Redis queue
[ ] Scanner task (batch scanning)
[ ] Celery beat scheduler (10 min)
[ ] Multi-timeframe scanning
[ ] Scanner run logging
```

### PHASE 5 — API Layer (Week 8)
```
[ ] Signals CRUD endpoints
[ ] Scanner status + results endpoints
[ ] Alert config endpoints
[ ] Subscription endpoints (Stripe integration)
[ ] WebSocket for live signals
[ ] Admin endpoints
[ ] Full API tests
```

### PHASE 6 — Frontend (Week 9–11)
```
[ ] Next.js setup + Tailwind + shadcn/ui
[ ] Auth pages (login, register)
[ ] Layout (sidebar, header, mobile nav)
[ ] Dashboard page
[ ] Scanner/screener page with filters
[ ] Signal detail page + TradingView chart
[ ] ICT zone overlays on chart
[ ] Trading stats page (Voltrex style)
[ ] Alert config page
[ ] Responsive mobile design
```

### PHASE 7 — Telegram + Admin (Week 12)
```
[ ] Telegram bot setup
[ ] Signal alert messages (formatted)
[ ] Bot commands (/signals, /stats, etc.)
[ ] Admin panel frontend
[ ] User management UI
[ ] Indicator config UI (live tuning)
[ ] Analytics charts
```

### PHASE 8 — SaaS + Security (Week 13)
```
[ ] Stripe payment flow
[ ] Plan enforcement (feature gating)
[ ] 1-device login lock
[ ] Rate limiting
[ ] API key management
[ ] Reseller system
[ ] White label config
```

### PHASE 9 — Testing + Polish (Week 14)
```
[ ] End-to-end testing
[ ] Performance testing (500 pairs scan time)
[ ] UI polish + animations
[ ] Mobile testing
[ ] Backtesting on historical data
[ ] Win rate validation
[ ] Documentation
```

### PHASE 10 — Deployment (Week 15)
```
[ ] Docker Compose production config
[ ] Nginx SSL setup (Let's Encrypt)
[ ] GitHub Actions CI/CD
[ ] VPS setup
[ ] Domain + DNS config
[ ] Monitoring (Uptime robot)
[ ] Launch checklist
```

---

## ESTIMATED TECH STACK VERSIONS

```
Python:              3.12+
FastAPI:             0.115+
SQLAlchemy:          2.0+
Alembic:             1.14+
Celery:              5.4+
Redis:               7.2+
PostgreSQL:          16+
pytest:              8+
httpx:               0.28+

Node.js:             20 LTS
Next.js:             15+
TypeScript:          5.5+
Tailwind CSS:        3.4+
shadcn/ui:           latest
@tradingview/lightweight-charts: 4.2+
React Query (TanStack): 5+
Zustand:             5+
Axios:               1.7+
```

---

## IMPORTANT NOTES

```
1. EXISTING FILES: Do NOT modify /srv/workspace/trading_indicator_pro/myplan.md
   or any existing files. All new code goes in tsp_backend/ and tsp_frontend/.

2. ICT ACCURACY: ICT modules must be tested against manual backtesting.
   False positives in ICT = bad signals. Quality over quantity.

3. SCORING BALANCE: Do not over-weight any single indicator.
   ICT signals are strong but should stack with technical confirmation.

4. PERFORMANCE: 500 pairs × 4 timeframes = 2000 analyses per scan.
   Target: complete scan in < 5 minutes. Use async + parallel workers.

5. DATABASE INDEXING: Add indexes on symbol, fired_at, confidence.
   Queries should be < 50ms for UI responsiveness.

6. MOBILE FIRST: Many traders use phones. Design for 375px width first.

7. LEGAL: Always show "Not Financial Advice" disclaimer on every signal.
```

---

*End of Master Plan — TradingSignalPro v1.0*
*Total Indicators: 35+ | ICT Modules: 10 | Phases: 10 | Weeks: 15*
