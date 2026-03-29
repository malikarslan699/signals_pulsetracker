from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import get_current_active_user, require_role
from app.core.exceptions import AuthorizationError, ServiceUnavailableError
from app.core.permissions import Permission, has_permission
from app.database import get_db
from app.models.pair import Pair
from app.models.scanner import ScannerRun
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.schemas.scanner import PairResponse, ScannerRunResponse, ScannerStatus

router = APIRouter(prefix="/scanner", tags=["Scanner"])


# ---------------------------------------------------------------------------
# GET /status
# ---------------------------------------------------------------------------
@router.get(
    "/status",
    response_model=ScannerStatus,
    summary="Get scanner health and latest run information",
)
async def scanner_status(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> ScannerStatus:
    """
    Return the current scanner health from Redis and the latest ScannerRun record
    from the database.
    """
    # Redis status
    redis_status = await redis.get_scanner_status()
    queue_len = await redis.get_scanner_queue_length()

    # Latest ScannerRun from DB
    result = await db.execute(
        select(ScannerRun).order_by(ScannerRun.started_at.desc()).limit(1)
    )
    latest_run: Optional[ScannerRun] = result.scalar_one_or_none()

    is_running = False
    current_market: Optional[str] = None
    pairs_total = 0
    pairs_done = 0
    signals_found = 0
    last_run_at: Optional[object] = None
    uptime_seconds: Optional[float] = None

    if redis_status:
        is_running = redis_status.get("is_running", False)
        current_market = redis_status.get("current_market")
        pairs_total = redis_status.get("pairs_total", 0)
        pairs_done = redis_status.get("pairs_done", 0)
        signals_found = redis_status.get("signals_found", 0)
        uptime_seconds = redis_status.get("uptime_seconds")

    if latest_run:
        last_run_at = latest_run.started_at

    return ScannerStatus(
        is_running=is_running,
        current_market=current_market,
        pairs_total=pairs_total,
        pairs_done=pairs_done,
        signals_found_this_run=signals_found,
        last_run_at=last_run_at,
        queue_length=queue_len,
        uptime_seconds=uptime_seconds,
    )


# ---------------------------------------------------------------------------
# GET /results
# ---------------------------------------------------------------------------
@router.get(
    "/results",
    summary="Get latest scanner results from Redis sorted set",
)
async def scanner_results(
    market: Optional[str] = Query(default=None),
    timeframe: Optional[str] = Query(default=None),
    min_confidence: int = Query(default=75, ge=0, le=100),
    limit: int = Query(default=100, ge=1, le=500),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    Return the most recent scanner results from the Redis active-signals sorted set.
    Filters by market, timeframe, and minimum confidence. ICT fields are hidden for
    free users.
    """
    if not has_permission(current_user, Permission.ACCESS_SCANNER):
        # Free users can still see limited results — just no ICT
        pass

    all_signals = await redis.get_all_active_signals()

    # Apply filters
    filtered = []
    for sig in all_signals:
        probability = sig.get("pwin_tp1")
        if probability is None:
            probability = sig.get("confidence", 0)
        if probability < min_confidence:
            continue
        if market and sig.get("market") != market:
            continue
        if timeframe and sig.get("timeframe") != timeframe:
            continue
        filtered.append(sig)

    if limit:
        filtered = filtered[:limit]

    can_see_ict = has_permission(current_user, Permission.READ_ICT)
    if not can_see_ict:
        cleaned = []
        for s in filtered:
            s = dict(s)
            s.pop("score_breakdown", None)
            s.pop("ict_zones", None)
            cleaned.append(s)
        filtered = cleaned

    return {
        "results": filtered,
        "count": len(filtered),
        "min_confidence": min_confidence,
        "market_filter": market,
        "timeframe_filter": timeframe,
        "limit": limit,
    }


# ---------------------------------------------------------------------------
# POST /trigger
# ---------------------------------------------------------------------------
@router.post(
    "/trigger",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Manually trigger a market scan (admin only)",
    dependencies=[Depends(require_role("admin"))],
)
async def trigger_scan(
    market: str = Query(default="crypto", pattern=r"^(crypto|forex|all)$"),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> dict:
    """
    Dispatch a Celery scan_market task for the specified market.
    Requires admin role.
    """
    try:
        from workers.scanner_task import scan_market  # Celery task

        task = scan_market.apply_async(kwargs={"market": market}, queue="scanner")
        logger.info(f"Admin triggered scan for market='{market}', task_id={task.id}")
        return {
            "status": "accepted",
            "task_id": task.id,
            "market": market,
            "message": f"Scan task dispatched for market: {market}",
        }
    except ImportError:
        # Celery may not be configured in all environments — fire via Redis queue
        logger.warning("Celery tasks module not available — using Redis queue fallback.")
        if market == "all":
            await redis.push_scanner_queue("crypto")
            await redis.push_scanner_queue("forex")
        else:
            await redis.push_scanner_queue(market)
        return {
            "status": "queued",
            "task_id": None,
            "market": market,
            "message": f"Market '{market}' added to scanner queue via Redis.",
        }


# ---------------------------------------------------------------------------
# GET /pairs
# ---------------------------------------------------------------------------
@router.get(
    "/pairs",
    response_model=list[PairResponse],
    summary="List active trading pairs with optional search and market filter",
)
async def list_pairs(
    market: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=20),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[PairResponse]:
    """
    Return active trading pairs. Supports search by symbol and filtering by market.
    """
    query = select(Pair).where(Pair.is_active == True)  # noqa: E712

    if market:
        query = query.where(Pair.market == market)

    if search:
        query = query.where(Pair.symbol.ilike(f"%{search.upper()}%"))

    query = query.order_by(Pair.symbol).offset(offset).limit(limit)
    result = await db.execute(query)
    pairs = list(result.scalars().all())

    return [PairResponse.model_validate(p) for p in pairs]
