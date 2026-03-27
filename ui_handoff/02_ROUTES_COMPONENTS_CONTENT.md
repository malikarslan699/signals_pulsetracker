# Routes + Components + Screen Content (Compact)

## Route Groups
- Public: `/`, `/pricing`
- Auth: `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`
- Core App: `/dashboard`, `/scanner`, `/signal/[id]`, `/history`, `/stats`, `/alerts`, `/settings`
- Admin: `/admin`, `/admin/users`, `/admin/packages`, `/admin/payments`, `/admin/config`, `/admin/analytics`, `/admin/qa`

## Shared Layout
- App shell: sidebar + top header + mobile bottom nav
- Admin shell: admin header + sub-nav tabs
- Auth shell: centered card on branded gradient background

## Core Pages (What to Preserve)
- `/dashboard`: ticker, KPI chips, scanner status, quick filters, compact signal table, heatmap
- `/scanner`: search, quick/advanced filters, sortable signal table, confidence bars, detail action
- `/signal/[id]`: status header, direction/confidence banner, chart with levels, MTF, confluences, indicator breakdown
- `/history`: KPI summary + filter chips + sortable historical table (PnL/status)
- `/stats`: period toggle + KPI cards + activity chart + timeframe chart
- `/alerts`: alert rule builder + test alert + alert list/empty states
- `/settings`: subscription/profile/telegram connect/danger zone

## Admin Pages (What to Preserve)
- `/admin`: overview KPIs + recent signals + plan distribution
- `/admin/users`: search/pagination/table + add/edit modals + status/plan/role controls
- `/admin/packages`: package list + expandable feature matrix editor + save/toggle
- `/admin/payments`: pending crypto payment queue + explorer links + reject action
- `/admin/config`: full system config + SMTP/Telegram health checks + API/billing/wallet configs + purge action
- `/admin/analytics`: KPI + timeframe/top-symbol summaries
- `/admin/qa`: tabs (`Signal Log`, `QA Stats`, `Noisy Pairs`, `Failure Analysis`) + expandable QA rows/tables

## Reusable Components Map
- Layout: `Sidebar`, `Header`, `MobileNav`, `LiveTicker`, `ThemeToggle`
- Trading: `SignalRow`, `SignalCard`, `SignalBadge`, `ConfidenceBar`, `IndicatorBreakdown`, `TradingViewChart`
- Dashboard/Scanner helpers: `StatsRow`, `ScannerStatus`, `MarketHeatmap`
- Admin/form patterns: table rows, toggles, input/secret fields, modal patterns

## UI Weakness by System
- Table system: inconsistent density + headers + spacing
- Filter system: fragmented controls, no unified control rail
- KPI system: mixed styles (chips vs large cards) without consistent hierarchy
- Badge/status system: inconsistent semantics/visual grammar
- Admin forms: long vertical stacks, high cognitive load

## Stitch Focus
- Build one unified data-table system across scanner/history/admin/qa
- Build one unified filter bar pattern (search + segments + ranges + quick chips)
- Build one unified KPI and badge system
- Re-layout admin config and QA for faster operational scanability
