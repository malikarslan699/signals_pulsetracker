# UI REDESIGN TARGETS

## Critical Weak Areas (Exact Targets)
- Oversized cards reduce data density on dashboard, history, settings, and most admin screens
- Weak spacing hierarchy between section headers, controls, and table bodies
- Too much empty space around KPI cards and form modules
- Generic admin-panel feel in `/admin`, `/admin/users`, `/admin/packages`, `/admin/config`
- Low premium feel due to repeated basic border-card patterns and weak visual depth
- Weak table density for scanner/history/admin workflows
- Inconsistent metrics presentation (chip style on dashboard vs large cards elsewhere)
- Filter controls are fragmented and inconsistent by page
- Chart containers are plain and visually detached from surrounding analytics context
- Auth and marketing pages use a different design language than the main app shell
- Inconsistent badge semantics for status, plans, roles, and outcomes
- Long vertical forms in admin config create cognitive overload

## Redesign Goals by Screen Group
- Core trading screens: maximize scan speed and terminal-style density
- Analytics screens: improve KPI hierarchy and chart context clarity
- Alert/settings screens: improve control grouping and reduce vertical bloat
- Admin screens: convert CRUD feel into premium operations cockpit
- Auth/marketing screens: align brand language with premium in-app experience

## Page-Specific High-Impact Targets
- `/dashboard`: compact header controls, tighter table row rhythm, stronger priority for confidence/status
- `/scanner`: unify quick and advanced filters, remove visual duplication, optimize sortable table readability
- `/signal/[id]`: make direction/confidence/risk summary the dominant focal zone; reduce equal-weight card repetition
- `/history`: compress KPI strip and increase visible table rows per viewport
- `/stats`: elevate chart framing and KPI consistency with dashboard chips
- `/alerts`: redesign rule builder into compact structured form with high scanability
- `/settings`: split account/integration/security into cleaner grouped blocks
- `/admin/users`: premium operations table + clearer modal hierarchy and safer edit affordances
- `/admin/config`: section-nav driven control center with explicit critical sections and safer destructive actions
- `/admin/qa`: improve analytical readability across tabs and dense tables

## Components to Rebuild First
- Unified table system (header, row states, sticky controls, compact mode)
- Unified filter bar system (segment + search + range + quick chips)
- Unified KPI system (chip + card variants)
- Unified badge system (direction/status/plan/role/confidence)
- Unified form section system (labels, helper text, toggles, secret fields, action bars)

## Screenshot Capture Checklist
- Capture desktop and mobile for: dashboard, scanner, signal detail, history, stats
- Capture at least one populated and one empty/loading/error state where available
- Capture admin users with add/edit modal open
- Capture admin config with SMTP and Telegram sections visible
- Capture admin QA for each tab and one expanded signal row
- Capture auth flow states (normal + error/success)

## Highest Priority Redesign Pages
1. `/dashboard`
2. `/scanner`
3. `/signal/[id]`
4. `/history`
5. `/admin/users`
6. `/admin/config`
7. `/admin/qa`

## Recommended Implementation Sequence in Stitch
1. Design tokens and shell primitives (spacing, typography, colors, table baseline)
2. Core trading flow (`/dashboard`, `/scanner`, `/signal/[id]`, `/history`)
3. Supporting user screens (`/stats`, `/alerts`, `/settings`)
4. Admin operations (`/admin/users`, `/admin/config`, `/admin/qa`, then remaining admin pages)
5. Auth and public pages aligned to the final premium language
