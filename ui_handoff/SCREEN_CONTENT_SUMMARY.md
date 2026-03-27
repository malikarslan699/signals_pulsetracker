# SCREEN CONTENT SUMMARY

## Global Shell Content
- Left sidebar: Dashboard, Scanner, Signal History, Trading Stats, Alerts, Settings, plus Admin for staff roles
- Top header: LIVE state chip, BTC/ETH price chips, theme toggle, notifications icon, user menu
- Mobile bottom nav: Home, Scanner, Alerts, Stats, Profile (or Admin for staff)

## Public and Auth Screens
- `/`: Hero claim, feature grid, process steps, static pricing cards, footer links
- `/pricing`: Dynamic plans grid, FAQ accordion, auth-aware CTA in top nav
- `/login`: email/password, pending verification resend panel, error banner
- `/register`: username/email/password create flow
- `/forgot-password`: email capture -> success state with reset CTA
- `/reset-password`: email + OTP + new password + confirm
- `/verify-email`: loading/failure/success verification state card

## Core Trading Screens

### `/dashboard`
- Content blocks: ticker, compact KPI chips, scanner status strip, quick filters, signal table, market heatmap
- Data visibility:
- Signals: symbol, direction, timeframe, confidence bar/value, entry/SL/TP1, RR, short status, age
- Scanner: last scan, next scan countdown, pairs scanned, found count
- Platform KPIs: active, win rate, TP/SL totals, avg confidence, next scan
- Primary actions: filter by direction/timeframe, manual refresh, open signal detail

### `/scanner`
- Content blocks: header count, search, quick filters, advanced filters drawer, sortable data table
- Data visibility:
- Signal rows: pair, market, direction, timeframe, confidence bar, entry/SL/TP1, RR, age
- Advanced filters: timeframe chips, min-confidence slider
- Primary actions: search, filter, sort, view signal details

### `/signal/[id]`
- Content blocks: symbol header + status, direction/confidence banner, chart, price levels, MTF analysis, top confluences, ICT zone snippets, indicator breakdown
- Data visibility:
- Levels: entry, stop, TP1/TP2/TP3, RR, current PnL
- Analysis: aligned vs non-aligned timeframes, long/short confidence per TF, category score breakdown
- Primary actions: back, share URL, inspect detailed analysis

### `/history`
- Content blocks: summary KPI strip, directional/timeframe filters, sortable history table
- Data visibility:
- Totals: total signals, win rate, TP hits, SL hits, expired
- Table: pair, direction, timeframe, confidence, entry/TP1/SL, status, PnL, relative time
- Primary actions: filter, sort, open signal detail

### `/stats`
- Content blocks: period toggle, KPI cards, daily activity area chart, timeframe bar chart
- Data visibility:
- KPIs: win rate, signal count, active count, avg confidence
- Charts: 14-day totals/wins/losses and count by timeframe
- Primary actions: switch 7/30/90 day window

### `/alerts`
- Content blocks: info banner, test alert action, new-alert form, alert list
- Data visibility:
- Rule values: min confidence, direction, timeframe, market, active status
- Primary actions: open/close form, toggle options, create alert, delete alert, send test alert

### `/settings`
- Content blocks: subscription card, profile editor, telegram setup, danger zone
- Data visibility:
- User: email, username, verification state, plan and expiry
- Telegram: connected state or generated verification code
- Primary actions: save profile, resend verification email, generate/copy telegram code, logout

## Admin Screens

### `/admin`
- Content blocks: KPI cards, recent signals table, plan distribution list with tiny bars
- Data visibility: customer totals, active signals, MRR, monthly customer adds, recent signal statuses
- Primary actions: monitor only

### `/admin/users`
- Content blocks: search/add toolbar, paginated table, add modal, edit modal
- Data visibility: user identity, role, plan, active/verified status, join date, telegram metadata
- Primary actions: add user, edit user plan/role/password/status, toggle active, paginate

### `/admin/packages`
- Content blocks: package list with expandable editors, feature access matrix
- Data visibility: plan price, duration, badges, enabled state, feature flags and limits
- Primary actions: expand, toggle package active, edit package, save/discard

### `/admin/payments`
- Content blocks: pending payment cards with tx details and explorer links
- Data visibility: user, network, amount, expected amount, txid, submission time
- Primary actions: open explorer, reject payment, follow manual user-plan update instruction

### `/admin/config`
- Content blocks: auth/trial, scanner, notifications, SMTP, Telegram, API keys/billing keys, crypto wallets, save and purge controls
- Data visibility: all system knobs, provider health statuses, sensitive keys, wallet addresses
- Primary actions: edit config, save config, SMTP check/test email, Telegram check/test message, purge low-quality signals

### `/admin/analytics`
- Content blocks: KPI cards, by-timeframe list, top-symbol list
- Data visibility: total signals, avg confidence, top symbols and win rates
- Primary actions: monitor only

### `/admin/qa`
- Content blocks: day range controls, tabbed analytics (`Signal Log`, `QA Stats`, `Noisy Pairs`, `Failure Analysis`)
- Data visibility:
- Signal log: expandable rows with confirmations, missing signals, category score bars, assessment text
- QA stats: overall KPI cards and performance tables
- Noisy pairs: high-volume low-win-rate pair list
- Failure analysis: noisy/reliable indicators, SL by timeframe, indicator noise matrix, high-confidence losses table
- Primary actions: filter status/TF/market, switch tabs, expand rows, jump to signal detail
