# STITCH UI BRIEF

## Project
- App name: PulseSignal Pro
- App type: SaaS trading signal platform (crypto + forex) with customer app + admin backoffice
- Stack context: Next.js App Router frontend (`frontend/app`), Tailwind-based styling, client-side data fetch via React Query, charts via Recharts + lightweight-charts

## Target Users
- Primary: active retail traders who need fast signal scanning and high-density decision UI
- Secondary: team admins managing users, plans, payments, platform config, QA diagnostics
- Access tiers: trial/monthly/yearly/lifetime with role-aware navigation (user/admin/owner/superadmin)

## Current UI Style
- Dark-first panel UI with purple accent and Tailwind utility styling
- Rounded card-heavy design, many bordered blocks, basic gradients
- Mixed visual language across routes (landing/pricing differ from app shell)
- Tables and metrics are functional but not premium or data-dense enough for trading workflow

## Current UI Problems
- Too many oversized cards and vertical stacking, especially in admin + settings
- Inconsistent spacing hierarchy between pages and modules
- Table density is moderate-to-low for a trading terminal use case
- Repeated generic admin-panel patterns reduce premium feel
- Weak visual prioritization of critical trading info (confidence, risk, status, recency)
- Inconsistent token usage between app shell and public pages (`/`, `/pricing`)
- Filters and controls are fragmented and not consistently sticky/compact

## Desired Premium Direction (Stitch)
- Build a compact, data-dense, pro trading terminal aesthetic
- Preserve all current product functionality and route architecture
- Elevate visual hierarchy for: signal confidence, direction, RR, status, and timing
- Shift from card-sprawl to grid systems with tighter control bars and stronger information lanes
- Use stronger typography hierarchy and tighter spacing rhythm
- Standardize component language across dashboard/scanner/history/stats/alerts/admin
- Keep admin powerful but visually aligned with premium core app, not generic CRUD panel

## Dark/Light Mode Expectations
- Dark mode is primary and should feel flagship quality
- Light mode must remain fully supported and readable (existing theme toggle + CSS variables)
- Both modes should share the same spacing/system rules and density
- Do not redesign only one mode

## Mandatory Interaction Style
- Compact trading terminal layout
- Fast scanability under high data volume
- Reduced empty space without harming readability
- Sticky/filter toolbars where useful
- Clear state colors for LONG/SHORT, TP/SL/active/expired

## Screenshots to Capture for Stitch
- `/dashboard`: full viewport including ticker, stats chips, scanner status, filter bar, signal table, heatmap
- `/scanner`: filters closed and filters open states; full table with confidence bars
- `/history`: stats cards + sortable history table
- `/signal/[id]`: header banner, chart panel, price levels, MTF/confluences, indicator breakdown
- `/stats`: KPI strip + both charts
- `/alerts`: empty state, form-open state, populated alert cards
- `/settings`: subscription/profile/telegram/danger sections in one long capture
- `/admin`: overview cards + recent signals + plan distribution
- `/admin/users`: table + edit modal + add user modal
- `/admin/packages`: collapsed package list + expanded package editor
- `/admin/config`: scanner/auth sections and SMTP/Telegram/API wallet sections
- `/admin/qa`: each tab (`Signal Log`, `QA Stats`, `Noisy Pairs`, `Failure Analysis`) with expanded row sample
- `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/pricing`, `/`

## Highest Priority Screens
- Priority 1: `/dashboard`, `/scanner`, `/signal/[id]`, `/history`
- Priority 2: `/stats`, `/alerts`, `/settings`
- Priority 3: `/admin/users`, `/admin/config`, `/admin/qa`, `/admin/packages`, `/admin`, `/admin/analytics`, `/admin/payments`
- Priority 4: auth + marketing (`/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/pricing`, `/`)

## Recommended Redesign Order
1. Global design system + app shell (`Sidebar`, `Header`, `MobileNav`, tables, chips, badges, filters)
2. Core trading flow (`/dashboard` -> `/scanner` -> `/signal/[id]` -> `/history`)
3. Performance and automation screens (`/stats`, `/alerts`, `/settings`)
4. Admin workflow (`/admin/users` -> `/admin/config` -> `/admin/qa` -> others)
5. Auth + marketing polish last, aligned to premium core style
