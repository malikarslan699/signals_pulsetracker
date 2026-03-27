from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import require_role
from app.database import get_db
from app.models.signal import Signal
from app.models.subscription import Subscription
from app.models.user import User

router = APIRouter(
    prefix="/admin/analytics",
    tags=["Admin — Analytics"],
    dependencies=[Depends(require_role("admin"))],
)

CUSTOMER_ROLES = ("user", "premium")
STAFF_ROLES = ("admin", "owner", "superadmin", "reseller")


# ---------------------------------------------------------------------------
# GET /overview
# ---------------------------------------------------------------------------
@router.get(
    "/overview",
    summary="Platform overview statistics",
)
async def overview(
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return high-level platform metrics:
    - Total users, paid users breakdown
    - Active signals count
    - Win rate (last 90 days)
    - Revenue (active subscriptions)
    """
    # Account totals (all roles)
    total_users_result = await db.execute(select(func.count()).select_from(User))
    total_accounts: int = total_users_result.scalar_one()

    # Active accounts
    active_users_result = await db.execute(
        select(func.count()).select_from(User).where(User.is_active == True)  # noqa: E712
    )
    active_accounts: int = active_users_result.scalar_one()

    # Customer totals (non-staff service users)
    customers_total_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.role.in_(CUSTOMER_ROLES))
    )
    customers_total: int = customers_total_result.scalar_one()

    customers_active_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.role.in_(CUSTOMER_ROLES))
        .where(User.is_active == True)  # noqa: E712
    )
    customers_active: int = customers_active_result.scalar_one()

    staff_total_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.role.in_(STAFF_ROLES))
    )
    staff_total: int = staff_total_result.scalar_one()

    # Customers by plan
    plan_counts: dict[str, int] = {}
    for plan in ("trial", "monthly", "yearly", "lifetime"):
        result = await db.execute(
            select(func.count())
            .select_from(User)
            .where(User.plan == plan)
            .where(User.role.in_(CUSTOMER_ROLES))
        )
        plan_counts[plan] = result.scalar_one()

    paid_customers = plan_counts.get("monthly", 0) + plan_counts.get("yearly", 0) + plan_counts.get("lifetime", 0)

    # New customers this month
    month_start = datetime.now(tz=timezone.utc).replace(
        day=1, hour=0, minute=0, second=0, microsecond=0
    )
    new_users_result = await db.execute(
        select(func.count())
        .select_from(User)
        .where(User.created_at >= month_start)
        .where(User.role.in_(CUSTOMER_ROLES))
    )
    new_customers_this_month: int = new_users_result.scalar_one()

    # Active signals
    active_signals_result = await db.execute(
        select(func.count()).select_from(Signal).where(Signal.status == "active")
    )
    active_signals: int = active_signals_result.scalar_one()

    # Win rate last 90 days
    ninety_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=90)

    tp_result = await db.execute(
        select(func.count())
        .select_from(Signal)
        .where(Signal.fired_at >= ninety_days_ago)
        .where(Signal.status.in_(["tp1_hit", "tp2_hit", "tp3_hit"]))
    )
    tp_count: int = tp_result.scalar_one()

    sl_result = await db.execute(
        select(func.count())
        .select_from(Signal)
        .where(Signal.fired_at >= ninety_days_ago)
        .where(Signal.status == "sl_hit")
    )
    sl_count: int = sl_result.scalar_one()

    closed_total = tp_count + sl_count
    win_rate = round((tp_count / closed_total * 100) if closed_total > 0 else 0.0, 1)

    # Revenue — sum of active subscriptions
    revenue_result = await db.execute(
        select(func.sum(Subscription.price))
        .where(Subscription.status == "active")
        .where(Subscription.plan.in_(["monthly", "yearly"]))
    )
    monthly_mrr = float(revenue_result.scalar_one() or 0.0)

    yearly_result = await db.execute(
        select(func.sum(Subscription.price))
        .where(Subscription.status == "active")
        .where(Subscription.plan == "yearly")
    )
    yearly_revenue = float(yearly_result.scalar_one() or 0.0)

    lifetime_result = await db.execute(
        select(func.sum(Subscription.price))
        .where(Subscription.status == "active")
        .where(Subscription.plan == "lifetime")
    )
    lifetime_revenue = float(lifetime_result.scalar_one() or 0.0)

    return {
        "users": {
            "total_accounts": total_accounts,
            "active_accounts": active_accounts,
            "staff_total": staff_total,
            "customers_total": customers_total,
            "customers_active": customers_active,
            "paid_customers": paid_customers,
            "new_customers_this_month": new_customers_this_month,
            "by_plan_customers": plan_counts,
        },
        "signals": {
            "active": active_signals,
            "win_rate_pct_90d": win_rate,
            "tp_hits_90d": tp_count,
            "sl_hits_90d": sl_count,
            "closed_total_90d": closed_total,
        },
        "revenue": {
            "mrr_usd": round(monthly_mrr, 2),
            "yearly_total_usd": round(yearly_revenue, 2),
            "lifetime_total_usd": round(lifetime_revenue, 2),
        },
    }


# ---------------------------------------------------------------------------
# GET /signals
# ---------------------------------------------------------------------------
@router.get(
    "/signals",
    summary="Signal analytics by timeframe, direction, confidence, and top symbols",
)
async def signal_analytics(
    days: int = 30,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Return detailed signal analytics:
    - Signals grouped by timeframe
    - Signals grouped by direction
    - Average confidence score
    - Top performing symbols
    """
    from_date = datetime.now(tz=timezone.utc) - timedelta(days=days)

    # By timeframe
    tf_result = await db.execute(
        select(Signal.timeframe, func.count().label("count"))
        .where(Signal.fired_at >= from_date)
        .group_by(Signal.timeframe)
        .order_by(func.count().desc())
    )
    by_timeframe = [
        {"timeframe": row.timeframe, "count": row.count}
        for row in tf_result.all()
    ]

    # By direction
    dir_result = await db.execute(
        select(Signal.direction, func.count().label("count"))
        .where(Signal.fired_at >= from_date)
        .group_by(Signal.direction)
    )
    by_direction = [
        {"direction": row.direction, "count": row.count}
        for row in dir_result.all()
    ]

    # Average confidence
    avg_conf_result = await db.execute(
        select(func.avg(Signal.confidence)).where(Signal.fired_at >= from_date)
    )
    avg_confidence = avg_conf_result.scalar_one()
    avg_confidence = round(float(avg_confidence), 1) if avg_confidence else 0.0

    # Total signals in range
    total_result = await db.execute(
        select(func.count()).select_from(Signal).where(Signal.fired_at >= from_date)
    )
    total_signals: int = total_result.scalar_one()

    # Top symbols by signal count
    top_symbols_result = await db.execute(
        select(Signal.symbol, func.count().label("count"))
        .where(Signal.fired_at >= from_date)
        .group_by(Signal.symbol)
        .order_by(func.count().desc())
        .limit(10)
    )
    top_symbols = [
        {"symbol": row.symbol, "signal_count": row.count}
        for row in top_symbols_result.all()
    ]

    # Win rate per symbol (top 10 symbols by volume)
    symbol_win_rates = []
    for sym_data in top_symbols:
        symbol = sym_data["symbol"]

        sym_tp_result = await db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.symbol == symbol)
            .where(Signal.fired_at >= from_date)
            .where(Signal.status.in_(["tp1_hit", "tp2_hit", "tp3_hit"]))
        )
        sym_tp = sym_tp_result.scalar_one()

        sym_sl_result = await db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.symbol == symbol)
            .where(Signal.fired_at >= from_date)
            .where(Signal.status == "sl_hit")
        )
        sym_sl = sym_sl_result.scalar_one()

        sym_closed = sym_tp + sym_sl
        sym_wr = round((sym_tp / sym_closed * 100) if sym_closed > 0 else 0.0, 1)

        symbol_win_rates.append(
            {
                "symbol": symbol,
                "signal_count": sym_data["signal_count"],
                "win_rate_pct": sym_wr,
                "tp_hits": sym_tp,
                "sl_hits": sym_sl,
            }
        )

    return {
        "period_days": days,
        "total_signals": total_signals,
        "avg_confidence": avg_confidence,
        "by_timeframe": by_timeframe,
        "by_direction": by_direction,
        "top_symbols": symbol_win_rates,
    }
