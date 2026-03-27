# ROUTES AND PAGES

## Route Inventory
- Public marketing: `/`, `/pricing`
- Auth: `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`
- Core app: `/dashboard`, `/scanner`, `/signal/[id]`, `/history`, `/stats`, `/alerts`, `/settings`
- Admin: `/admin`, `/admin/users`, `/admin/packages`, `/admin/payments`, `/admin/config`, `/admin/analytics`, `/admin/qa`

## Shared Layout Structure
- App shell (`(app)/layout.tsx`): `Sidebar` (desktop), `Header` (top), `MobileNav` (bottom mobile), scrollable content area
- Admin shell (`(app)/admin/layout.tsx`): admin header + sub-nav tabs across admin routes
- Auth shell (`(auth)/layout.tsx`): centered auth card, gradient background, logo, footer line

## Page Specs

### `/`
- Purpose: landing + conversion funnel
- Key sections: fixed navbar, hero, stats strip, feature cards, how-it-works, pricing cards, footer
- Major components: inline section blocks (no shared component system)
- Data shown: mostly static marketing copy and static pricing examples
- Actions: anchor jump, login/register/dashboard CTA
- Weak UI: generic SaaS marketing look, low product realism, style disconnect vs app shell
- Stitch redesign target: premium quant/trading brand landing with denser live-product preview modules

### `/pricing`
- Purpose: subscription plan selection + checkout start
- Key sections: top nav, hero, dynamic pricing cards, FAQ accordion, footer
- Major components: `PricingCard`, `FaqItem`
- Data shown: dynamic plan list from `/api/v1/subscriptions/plans`, FAQ content
- Actions: start checkout, register, go dashboard, FAQ expand/collapse
- Weak UI: visual language differs from app, card sizing heavy, low comparison clarity
- Stitch redesign target: high-contrast premium pricing matrix with clearer plan deltas and stronger trust cues

### `/login`
- Purpose: authentication entry
- Key sections: header, error banner, optional email-verification resend panel, form, register link
- Major components: auth form controls (inline)
- Data shown: login errors, optional pending-verification state
- Actions: sign in, resend verification, toggle password visibility, navigate reset/register
- Weak UI: basic form-only experience, weak status hierarchy
- Stitch redesign target: polished credential panel with strong state messaging and compact spacing

### `/register`
- Purpose: account creation
- Key sections: header, error banner, username/email/password form, login link
- Major components: auth form controls (inline)
- Data shown: validation and server error states
- Actions: register, toggle password visibility
- Weak UI: plain card and minimal trust/benefit framing
- Stitch redesign target: premium onboarding form with stronger confidence and trial value framing

### `/forgot-password`
- Purpose: request OTP reset code
- Key sections: request form state, success state with CTA to reset
- Major components: auth form controls
- Data shown: entered email and success/error state
- Actions: send reset code, switch email, go login/reset page
- Weak UI: flow works but feels utilitarian
- Stitch redesign target: smoother step-based recovery feel with clearer state progression

### `/reset-password`
- Purpose: submit OTP + new password
- Key sections: form (email, OTP, password, confirm), success card
- Major components: auth form controls
- Data shown: OTP input, password validation feedback
- Actions: reset password, toggle password visibility, navigate back
- Weak UI: long form without progressive hierarchy
- Stitch redesign target: clearer two-step recovery framing with compact grouped fields

### `/verify-email`
- Purpose: email verification result
- Key sections: loading, fail, success states in centered card
- Major components: status icon card
- Data shown: verification API message
- Actions: return to login
- Weak UI: minimal and visually flat
- Stitch redesign target: branded verification state cards with stronger success/failure contrast

### `/dashboard`
- Purpose: live trading overview
- Key sections: live ticker, stats chips row, scanner status strip, direction/timeframe filters, compact signal table, market heatmap
- Major components: `LiveTicker`, `StatsRow`, `ScannerStatus`, `SignalRow`, `MarketHeatmap`
- Data shown: signals feed, scanner status, high-level platform stats, symbol direction map
- Actions: filter, refresh, open signal detail
- Weak UI: high-value info exists but hierarchy is shallow; table header density and spacing can be tighter
- Stitch redesign target: flagship terminal screen with stronger information lanes and scan-first typography

### `/scanner`
- Purpose: deep signal browsing and filtering
- Key sections: header, search, quick filters, advanced filter panel, sortable table
- Major components: `ConfidenceBar`
- Data shown: deduped signal list with symbol, direction, timeframe, confidence, entry/SL/TP1, RR, time
- Actions: search, set filters, sort columns, open details
- Weak UI: filter/control clutter, table columns repeat labels, inconsistent compactness
- Stitch redesign target: professional scanner grid with sticky control rail and denser rows

### `/signal/[id]`
- Purpose: single-signal deep analysis
- Key sections: header + status, direction banner, chart panel, price levels, MTF analysis, confluences, ICT zones, indicator breakdown
- Major components: `TradingViewChart`, `ConfidenceBar`, `IndicatorBreakdown`
- Data shown: full signal payload including targets, RR, MTF and score breakdown
- Actions: back, share URL, inspect analysis blocks
- Weak UI: many equal-weight cards; key risk/reward context not visually prioritized enough
- Stitch redesign target: premium analysis cockpit with clear primary/secondary zones and tighter data modules

### `/history`
- Purpose: resolved signal performance history
- Key sections: KPI cards, direction/timeframe filters, sortable results table
- Major components: sortable header helpers
- Data shown: historical signals with outcome status, PnL, confidence, entry/TP/SL, relative time
- Actions: filter, sort by columns, open signal detail
- Weak UI: card strip oversized, table could carry more rows per viewport
- Stitch redesign target: denser performance ledger with strong positive/negative encoding

### `/stats`
- Purpose: aggregate platform trading stats
- Key sections: date-range toggle, KPI cards, daily activity area chart, timeframe bar chart
- Major components: Recharts blocks
- Data shown: win rate, active signals, avg confidence, series over time, timeframe distribution
- Actions: change range 7/30/90d
- Weak UI: chart modules are functional but generic; insufficient visual polish and context framing
- Stitch redesign target: premium analytics board with stronger chart framing and compact KPI hierarchy

### `/alerts`
- Purpose: configure signal alert rules
- Key sections: page header with actions, setup info banner, create-rule form, rule list/empty state
- Major components: rule form controls, alert cards
- Data shown: min confidence, directions, timeframes, markets, active state
- Actions: create rule, delete rule, send test alert
- Weak UI: heavy vertical form and card blocks, weak density for power users
- Stitch redesign target: compact rule builder with structured chips and better state density

### `/settings`
- Purpose: account and integration settings
- Key sections: subscription, profile, telegram connect, danger zone
- Major components: settings cards + form controls
- Data shown: plan/expires, email/username, telegram state/code, verification status
- Actions: save profile, resend verification, generate/copy telegram code, sign out
- Weak UI: long stacked cards, weak grouping for account-critical controls
- Stitch redesign target: cleaner settings architecture with tighter grouping and clearer account status

### `/admin`
- Purpose: admin overview
- Key sections: stat cards, recent signals table, plan distribution panel
- Major components: `StatCard` (inline)
- Data shown: customer counts, active signals, MRR, new customers, recent signals, plan mix
- Actions: mostly monitoring view
- Weak UI: standard admin dashboard look, not premium, limited visual hierarchy
- Stitch redesign target: executive-grade operations dashboard aligned with core product style

### `/admin/users`
- Purpose: user management
- Key sections: toolbar (search/add/refresh), users table, pagination, add/edit modals
- Major components: `AddUserModal`, `EditUserModal`
- Data shown: username/email, plan, role, status, verification, join time, telegram details
- Actions: search, paginate, toggle active, open edit modal, create user, change role/plan/password/QA access
- Weak UI: dense function set but modal and table styling feel basic and CRUD-like
- Stitch redesign target: high-clarity operations table + premium control modals

### `/admin/packages`
- Purpose: plan package management
- Key sections: package list, expandable package editor, feature flag matrix, save/toggle actions
- Major components: `PackageCard`
- Data shown: price/duration/description/badge, active state, feature entitlements and limits
- Actions: expand/collapse, edit package fields, toggle active, save/discard
- Weak UI: long form blocks with limited hierarchy, overwhelming feature editor presentation
- Stitch redesign target: cleaner plan editor with stronger grouping and safer change affordances

### `/admin/payments`
- Purpose: manual crypto payment verification workflow
- Key sections: list of pending payments, payment detail cards, external explorer links
- Major components: payment cards with action row
- Data shown: user, plan, txid, network, amount vs expected, timestamp
- Actions: open explorer, reject payment, manual instruction to update user plan
- Weak UI: process-critical workflow presented as simple cards; weak operational cues
- Stitch redesign target: queue-style moderation UI with clearer statuses and action confidence

### `/admin/config`
- Purpose: system configuration and provider integrations
- Key sections: auth/trial, scanner, notifications, SMTP health/settings, Telegram health/settings, API keys, billing keys, crypto wallets, save + purge
- Major components: `Section`, `Toggle`, `Input`, `SecretInput`
- Data shown: core scanner controls, auth policy, provider health checks, sensitive integration keys
- Actions: edit config, save config, run SMTP/Telegram checks, send test email/message, purge low-quality signals
- Weak UI: very long monolithic form, heavy cognitive load, limited visual partitioning
- Stitch redesign target: segmented control center with strong section nav and critical-action emphasis

### `/admin/analytics`
- Purpose: concise signal analytics summary
- Key sections: KPI row, timeframe summary panel, top symbols panel
- Major components: simple stat blocks
- Data shown: total signals, avg confidence, top symbol count, by-timeframe and top-symbol rows
- Actions: monitoring only
- Weak UI: minimal and underdesigned compared to data value
- Stitch redesign target: compact analytics panel style with stronger comparative visuals

### `/admin/qa`
- Purpose: internal signal quality analysis lab
- Key sections: day filters, tabbed interface (`Signal Log`, `QA Stats`, `Noisy Pairs`, `Failure Analysis`), expandable QA rows, multiple diagnostic tables
- Major components: `SignalQARow`, `StatCard`
- Data shown: confirmations, category scores, MTF confirmations, noisy/reliable indicators, overconfident losses
- Actions: filter by status/tf/market, switch tabs, expand rows, open linked signal detail
- Weak UI: information-rich but visually dense without enough hierarchy; tab content can feel overwhelming
- Stitch redesign target: pro diagnostics workspace with clearer analytical grouping and scanable risk signals
