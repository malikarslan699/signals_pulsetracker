from __future__ import annotations

import math
from datetime import datetime
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user
from app.core.exceptions import NotFoundError, SubscriptionRequiredError
from app.database import get_db
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.schemas.signal import SignalFilter, SignalListResponse, SignalResponse
from app.services.package_config_service import get_package, load_packages_config
from app.services.signal_service import SignalService

router = APIRouter(prefix="/signals", tags=["Signals"])

_FREE_LIVE_SIGNAL_LIMIT = 5


def _calc_rr(entry, stop_loss, take_profit):
    try:
        if take_profit is None:
            return None
        risk = abs(float(entry) - float(stop_loss))
        if risk <= 0:
            return None
        reward = abs(float(take_profit) - float(entry))
        return round(reward / risk, 2)
    except Exception:
        return None


def _attach_rr_fields(resp: SignalResponse) -> SignalResponse:
    resp.rr_tp1 = _calc_rr(resp.entry, resp.stop_loss, resp.take_profit_1)
    resp.rr_tp2 = _calc_rr(resp.entry, resp.stop_loss, resp.take_profit_2)
    if resp.top_confluences is None and resp.score_breakdown:
        ranked = []
        for key, value in (resp.score_breakdown or {}).items():
            if not isinstance(value, dict) or not value.get("triggered"):
                continue
            try:
                score = float(value.get("score", 0) or 0)
            except Exception:
                score = 0.0
            if score <= 0:
                continue
            details = str(value.get("details") or "").strip()
            label = str(key).split("/", 1)[-1]
            ranked.append((score, f"{label}: {details}" if details else label))
        ranked.sort(key=lambda item: item[0], reverse=True)
        resp.top_confluences = [item[1] for item in ranked[:6]]
    return resp


async def _get_user_package_features(current_user: User, redis: RedisClient):
    config = await load_packages_config(redis)
    pkg = get_package(config, current_user.plan) or get_package(config, "trial")
    return pkg.features if pkg else None


def _can_see_indicator_breakdown(current_user: User, features) -> bool:
    if current_user.is_admin:
        return True
    if features is None:
        return current_user.plan in ("monthly", "yearly", "lifetime")
    return bool(features.advanced_indicator_breakdown)


def _can_access_history(current_user: User, features) -> bool:
    if current_user.is_admin:
        return True
    if features is None:
        return current_user.plan in ("trial", "monthly", "yearly", "lifetime")
    return bool(features.signal_history)


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

    features = await _get_user_package_features(current_user, redis)
    can_see_ict = _can_see_indicator_breakdown(current_user, features)

    signal_responses = []
    for signal in items:
        resp = SignalResponse.model_validate(signal)
        resp = _attach_rr_fields(resp)
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
    features = await _get_user_package_features(current_user, redis)
    can_see_ict = _can_see_indicator_breakdown(current_user, features)

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
    Access and max history window are controlled by package configuration.
    """
    features = await _get_user_package_features(current_user, redis)
    if not _can_access_history(current_user, features):
        raise SubscriptionRequiredError(
            "Signal history is not included in your current package.",
            required_plan="trial",
        )

    max_days = getattr(features, "history_days", 0) if features else 0
    effective_days = min(days, max_days) if max_days > 0 else days

    service = SignalService(db, redis)
    signals = await service.get_signal_history(current_user.id, days=effective_days)

    can_see_ict = _can_see_indicator_breakdown(current_user, features)
    signal_responses: list[SignalResponse] = []
    for signal in signals:
        resp = SignalResponse.model_validate(signal)
        resp = _attach_rr_fields(resp)
        if not can_see_ict:
            resp.score_breakdown = None
            resp.ict_zones = None
        signal_responses.append(resp)
    return signal_responses


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
    resp = _attach_rr_fields(resp)

    features = await _get_user_package_features(current_user, redis)
    can_see_ict = _can_see_indicator_breakdown(current_user, features)
    if not can_see_ict:
        resp.score_breakdown = None
        resp.ict_zones = None

    return resp
