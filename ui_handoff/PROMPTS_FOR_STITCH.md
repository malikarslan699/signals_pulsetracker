# PROMPTS FOR STITCH

## 1) Master Prompt (Core App)
Use this project as an existing Next.js frontend and redesign the current UI into a premium, compact, data-dense AI trading terminal experience.

Constraints:
- Do not change backend logic, API contracts, business rules, or route structure.
- Keep all existing routes and user actions intact.
- Redesign only frontend presentation, spacing, hierarchy, and interaction quality.
- Maintain dark and light mode support.
- Optimize for fast scanning under heavy data density.

Must preserve:
- App shell with sidebar + top header + mobile nav.
- Core routes: `/dashboard`, `/scanner`, `/signal/[id]`, `/history`, `/stats`, `/alerts`, `/settings`.
- Admin routes: `/admin`, `/admin/users`, `/admin/packages`, `/admin/payments`, `/admin/config`, `/admin/analytics`, `/admin/qa`.
- Auth routes and public pages.

Design direction:
- Professional institutional trading terminal aesthetic.
- Stronger typography hierarchy and compact spacing rhythm.
- Unified table/filter/badge/KPI systems across pages.
- Higher visual priority for confidence, direction, RR, status, and recency.
- Premium surfaces and depth without reducing readability.

Expected output:
- Redesigned screen compositions for all app routes.
- Reusable component system definitions for: tables, filter bars, KPI chips/cards, badges, analytics panels, settings sections, admin operation modules.
- Responsive desktop + mobile behavior for each major screen.

## 2) Dashboard-Specific Prompt
Redesign `/dashboard` as the flagship trading terminal home.

Keep content and behavior:
- Live ticker
- KPI stats chips
- Scanner status strip
- Direction/timeframe quick filters + refresh
- Signal table rows
- Market heatmap

Improve:
- Data-first hierarchy and compactness
- Sticky control/filter area
- Cleaner row density and stronger status encoding
- Better visual separation between summary lane and live signal lane
- Premium look consistent with pro quant tooling

## 3) Scanner-Specific Prompt
Redesign `/scanner` as a high-performance signal discovery grid.

Keep content and behavior:
- Search
- Quick filters (direction, market)
- Advanced filters (timeframe, confidence slider)
- Sortable table with confidence bars and view action

Improve:
- Merge quick + advanced controls into a cohesive filter architecture
- Reduce duplicated labels and whitespace in table
- Increase rows visible per viewport while preserving readability
- Make confidence/direction/risk columns instantly scannable
- Create premium table ergonomics for frequent sorting/filtering

## 4) History-Specific Prompt
Redesign `/history` as a performance ledger for resolved signals.

Keep content and behavior:
- KPI summary cards
- Direction/timeframe filters
- Sortable history table with status and PnL

Improve:
- Compress KPI area into tighter performance strip
- Increase table readability and density
- Stronger positive/negative visual encoding for wins/losses
- Cleaner sticky header and sorting affordances
- Better balance between analysis summary and detailed rows

## 5) Admin-Specific Prompt
Redesign admin routes into a premium operations control center (not generic CRUD).

Routes in scope:
- `/admin`, `/admin/users`, `/admin/packages`, `/admin/payments`, `/admin/config`, `/admin/analytics`, `/admin/qa`

Keep behaviors:
- User search/pagination/modals and toggles
- Package editing with feature flags
- Payment review with explorer links and reject actions
- Full config forms and health checks (SMTP/Telegram)
- QA tabbed diagnostics and tables

Improve:
- Introduce clearer section navigation and task hierarchy
- Improve safety/clarity around high-impact actions
- Use denser but readable operations tables
- Make QA analytics easier to parse quickly
- Align all admin pages with core product premium style

## 6) Auth-Specific Prompt
Redesign auth flow screens into a premium, trustworthy onboarding/recovery experience.

Routes in scope:
- `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`

Keep behaviors:
- Existing fields, validation, and state transitions
- Verification resend flow and OTP reset flow

Improve:
- Clearer state feedback for success/error/pending states
- Better step progression for password recovery
- Tighter spacing and stronger visual hierarchy
- Visual alignment with premium app shell and brand direction
