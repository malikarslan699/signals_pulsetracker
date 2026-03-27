from __future__ import annotations

import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.exceptions import NotFoundError, SubscriptionRequiredError
from app.core.permissions import Permission, has_permission
from app.database import get_db
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.schemas.signal import SignalFilter, SignalListResponse, SignalResponse
from app.services.signal_service import SignalService

router = APIRouter(prefix="/signals", tags=["Signals"])

_FREE_LIVE_SIGNAL_LIMIT = 5


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=SignalListResponse,
    summary="Paginated list of signals with optional filters",
)
async def list_signals(
    direction: Optional[str] = Query(default=None, pattern=r"^(LONG|SHORT)$"),
    timeframe: Optional[str] = Query(default=None),
    market: Optional[str] = Query(default=None),
    min_confidence: int = Query(default=75, ge=0, le=100),
    max_confidence: Optional[int] = Query(default=None, ge=0, le=100),
    symbol: Optional[str] = Query(default=None),
    signal_status: Optional[str] = Query(default=None, alias="status"),
    from_date: Optional[datetime] = Query(default=None),
    to_date: Optional[datetime] = Query(default=None),
    page: int = Query(default=1, ge=1),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> SignalListResponse:
    """
    Return a paginated list of signals. All authenticated users can access
    basic signal data. ICT zone and score breakdown data is hidden for
    free/trial users.
    """
    filters = SignalFilter(
        direction=direction,
        timeframe=timeframe,
        market=market,
        min_confidence=min_confidence,
        symbol=symbol,
        status=signal_status,
        from_date=from_date,
        to_date=to_date,
    )

    service = SignalService(db, redis)
    items, total = await service.get_signals(filters, page=page, limit=limit)

    can_see_ict = has_permission(current_user, Permission.READ_ICT)

    signal_responses = []
    for signal in items:
        resp = SignalResponse.model_validate(signal)
        if not can_see_ict:
            resp.score_breakdown = None
            resp.ict_zones = None
        # Apply max_confidence filter (post-query, not supported in service layer)
        if max_confidence is not None and resp.confidence > max_confidence:
            continue
        signal_responses.append(resp)

    pages = math.ceil(total / limit) if limit > 0 else 1

    return SignalListResponse(
        items=signal_responses,
        total=total,
        page=page,
        limit=limit,
        pages=pages,
    )


# ---------------------------------------------------------------------------
# GET /live
# ---------------------------------------------------------------------------
@router.get(
    "/live",
    summary="Live signals from Redis cache",
)
async def live_signals(
    min_confidence: int = Query(default=75, ge=0, le=100),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    Return currently active signals from the Redis cache.
    Free users are limited to {_FREE_LIVE_SIGNAL_LIMIT} signals.
    """
    service = SignalService(db, redis)
    signals = await service.get_live_signals(min_confidence=min_confidence)

    is_free = current_user.plan == "trial"
    can_see_ict = has_permission(current_user, Permission.READ_ICT)

    if is_free:
        signals = signals[:_FREE_LIVE_SIGNAL_LIMIT]

    # Strip ICT/breakdown fields for free/trial users
    if not can_see_ict:
        cleaned = []
        for s in signals:
            s = dict(s)
            s.pop("score_breakdown", None)
            s.pop("ict_zones", None)
            cleaned.append(s)
        signals = cleaned

    return {
        "signals": signals,
        "count": len(signals),
        "limited": is_free,
        "limit_applied": _FREE_LIVE_SIGNAL_LIMIT if is_free else None,
    }


# ---------------------------------------------------------------------------
# GET /stats
# ---------------------------------------------------------------------------
@router.get(
    "/stats",
    summary="Platform-wide signal statistics",
)
async def signal_stats(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    Return aggregate platform statistics: win rate, active signals, pairs scanned.
    Available to all authenticated users.
    """
    service = SignalService(db, redis)
    stats = await service.get_platform_stats()

    # Add scanner queue info from Redis
    queue_len = await redis.get_scanner_queue_length()
    stats["scanner_queue_length"] = queue_len

    return stats


# ---------------------------------------------------------------------------
# GET /history
# ---------------------------------------------------------------------------
@router.get(
    "/history",
    response_model=list[SignalResponse],
    summary="Historical closed signals (premium only)",
)
async def signal_history(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> list[SignalResponse]:
    """
    Return closed/expired signals from the past N days.
    Requires monthly or lifetime subscription.
    """
    if current_user.plan not in ("monthly", "yearly", "lifetime") and not current_user.is_admin:
        raise SubscriptionRequiredError(
            "Signal history requires a monthly or lifetime plan.",
            required_plan="monthly",
        )

    service = SignalService(db, redis)
    signals = await service.get_signal_history(current_user.id, days=days)

    return [SignalResponse.model_validate(s) for s in signals]


# ---------------------------------------------------------------------------
# GET /{signal_id}
# ---------------------------------------------------------------------------
@router.get(
    "/{signal_id}",
    response_model=SignalResponse,
    summary="Get signal detail by ID",
)
async def get_signal(
    signal_id: UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> SignalResponse:
    """
    Return full signal detail.
    score_breakdown and ict_zones are hidden for free/trial users.
    """
    service = SignalService(db, redis)
    try:
        signal = await service.get_signal_by_id(signal_id)
    except ValueError:
        raise NotFoundError("Signal", signal_id)

    resp = SignalResponse.model_validate(signal)

    can_see_ict = has_permission(current_user, Permission.READ_ICT)
    if not can_see_ict:
        resp.score_breakdown = None
        resp.ict_zones = None

    return resp
