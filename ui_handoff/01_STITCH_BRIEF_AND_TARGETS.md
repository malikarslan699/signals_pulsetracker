# Stitch Brief + Redesign Targets (Compact)

## Product Snapshot
- App: PulseSignal Pro
- Type: Trading signal SaaS (crypto + forex) with customer app + admin backoffice
- Users: active traders + internal admins/owners
- Frontend stack: Next.js App Router + Tailwind + React Query + Recharts + lightweight-charts

## Design Direction (Must)
- Premium, compact, data-dense trading terminal style
- Keep dark + light mode both polished
- Fast scanability: confidence, direction, RR, status, recency should be visually dominant
- Keep all existing functionality and route behavior unchanged

## Current UI Issues
- Oversized cards + too much vertical space
- Weak spacing hierarchy and inconsistent component rhythm
- Tables not dense enough for trading workflow
- Generic admin-panel feel in admin routes
- Inconsistent metrics/badge/filter presentation across pages
- Auth/public visual style not fully aligned with core app shell

## High-Priority Redesign Screens
1. `/dashboard`
2. `/scanner`
3. `/signal/[id]`
4. `/history`
5. `/admin/users`
6. `/admin/config`
7. `/admin/qa`

## Redesign Order (Recommended)
1. Global system + shell (`Sidebar`, `Header`, `MobileNav`, table/filter/badge/KPI primitives)
2. Core trading flow (`/dashboard` -> `/scanner` -> `/signal/[id]` -> `/history`)
3. Supporting user pages (`/stats`, `/alerts`, `/settings`)
4. Admin operations (`/admin/users`, `/admin/config`, `/admin/qa`, then other admin pages)
5. Auth + public pages aligned with final premium language

## Screenshot Checklist for Stitch
- `/dashboard` (full screen with ticker, stats chips, scanner status, table, heatmap)
- `/scanner` (filters closed + open, full table)
- `/history` (KPI strip + table)
- `/signal/[id]` (header banner + chart + analysis blocks)
- `/stats` (KPI + both charts)
- `/alerts` (empty state + form-open + populated)
- `/settings` (all sections in one long capture)
- `/admin` (overview + tables)
- `/admin/users` (table + add modal + edit modal)
- `/admin/packages` (collapsed + expanded package editor)
- `/admin/config` (scanner/auth + SMTP/Telegram/API/wallet areas)
- `/admin/qa` (all tabs + one expanded row)
- `/login`, `/register`, `/forgot-password`, `/reset-password`, `/verify-email`, `/pricing`, `/`

## Hard Constraints for Stitch
- No backend/API/logic changes
- No route changes
- No feature removal
- UI-only redesign with existing behavior preserved
