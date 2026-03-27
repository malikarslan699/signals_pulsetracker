# COMPONENT MAP

## Layout and Navigation Components
- `Sidebar` (`components/layout/Sidebar.tsx`)
- `Header` (`components/layout/Header.tsx`)
- `MobileNav` (`components/layout/MobileNav.tsx`)
- `LiveTicker` (`components/layout/LiveTicker.tsx`)
- `ThemeToggle` (`components/ui/ThemeToggle.tsx`)
- `App layout` (`app/(app)/layout.tsx`) wires sidebar/header/mobile nav
- `Admin layout` (`app/(app)/admin/layout.tsx`) adds admin sub-navigation
- `Auth layout` (`app/(auth)/layout.tsx`) provides centered auth shell

## Signal and Trading Components
- `SignalRow`: dense row used on dashboard table
- `SignalCard`: card view for signal data (available reusable primitive)
- `SignalBadge`: direction pill component
- `ConfidenceBar`: confidence meter primitive used in scanner/detail
- `IndicatorBreakdown`: grouped indicator/category score block on signal detail
- `TradingViewChart`: candlestick chart + entry/SL/TP overlays

## Dashboard and Scanner Components
- `StatsRow`: compact KPI chips (active, win rate, TP/SL, avg conf, next scan)
- `ScannerStatus`: scanner heartbeat strip with countdown and pair stats
- `MarketHeatmap`: symbol direction heat cells

## Data/State Utility Layer (UI-facing)
- `hooks/useSignals.ts`: list/detail/live signal fetchers
- `hooks/useScanner.ts`: scanner status/results
- `hooks/useAuth.ts`: login/register/logout flow
- `lib/formatters.ts`: status, confidence, price/time format utilities
- `store/userStore.ts`: auth/user role + plan state

## Reusable UI Patterns Present
- Cards: surface card with border + rounded corners used almost everywhere
- Tables: scanner/history/admin users/admin qa/admin analytics
- Charts: lightweight-charts (signal detail), recharts (stats)
- Filters: segmented button groups, search boxes, slider/range filters
- Badges: plan badges, status badges, direction badges, confidence labels
- Toggles: custom boolean toggles in admin config and user edit modal
- Modals: admin users add/edit flows

## Route to Component Usage
- `/dashboard`: `LiveTicker`, `StatsRow`, `ScannerStatus`, `SignalRow`, `MarketHeatmap`
- `/scanner`: `ConfidenceBar` plus table/filter controls
- `/signal/[id]`: `TradingViewChart`, `ConfidenceBar`, `IndicatorBreakdown`
- `/history`: custom sortable table primitives
- `/stats`: recharts module blocks
- `/alerts`: form controls + alert cards
- `/settings`: settings cards + inline controls
- `/admin`: inline `StatCard` + table/panel blocks
- `/admin/users`: modal components + operations table
- `/admin/packages`: expandable `PackageCard` editor
- `/admin/config`: `Section`, `Toggle`, `Input`, `SecretInput`
- `/admin/qa`: `SignalQARow`, `StatCard`, multi-table diagnostics

## Component-Level Weaknesses for Redesign
- Layout shell works functionally but spacing rhythm varies by route
- Many card blocks have similar weight, reducing scan priority
- Table designs are inconsistent across scanner/history/admin pages
- Filter bars are inconsistent in placement and density
- Badge styles vary too much by page
- Admin forms rely on long vertical stacks with weak section navigation
- Chart containers are plain and not integrated into a premium data canvas

## Stitch Rebuild Focus by Component Family
- Standardize shell: header/sidebar/mobile nav spacing + token system
- Build one premium data table system reused across dashboard/scanner/history/admin
- Build one filter bar system (segmented controls + search + range + quick chips)
- Build one KPI chip/card system with compact and expanded variants
- Build one status/badge system for direction, confidence, outcome, plan, role
- Build one panel system for charts/analysis blocks with consistent headers/actions
