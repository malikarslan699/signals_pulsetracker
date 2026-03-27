from __future__ import annotations

from typing import Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, Query, status
from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.core.auth import get_current_active_user
from app.core.exceptions import NotFoundError, ServiceUnavailableError, SubscriptionRequiredError
from app.database import get_db
from app.models.pair import Pair
from app.models.user import User
from app.redis_client import RedisClient, get_redis_client
from app.schemas.scanner import AnalysisResponse, CandleResponse, PairResponse

router = APIRouter(prefix="/pairs", tags=["Pairs"])
settings = get_settings()

_DEFAULT_TIMEFRAME = "1H"
_DEFAULT_LIMIT = 100
_DEFAULT_TICKER_SYMBOLS = [
    "BTCUSDT",
    "ETHUSDT",
    "BNBUSDT",
    "SOLUSDT",
    "XRPUSDT",
    "ADAUSDT",
    "DOTUSDT",
    "MATICUSDT",
    "LINKUSDT",
    "AVAXUSDT",
]
_BINANCE_TF_MAP = {
    "1m": "1m",
    "3m": "3m",
    "5m": "5m",
    "15m": "15m",
    "30m": "30m",
    "1H": "1h",
    "4H": "4h",
    "1D": "1d",
    "1W": "1w",
}


async def _fetch_ticker_snapshot_from_binance() -> list[dict]:
    """
    Fetch 24h ticker stats from Binance Futures and normalize response shape.
    """
    url = f"{settings.BINANCE_REST_URL}/fapi/v1/ticker/24hr"
    headers = {}
    if settings.BINANCE_API_KEY:
        headers["X-MBX-APIKEY"] = settings.BINANCE_API_KEY

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            raw = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(f"Binance ticker API error: {exc.response.status_code}")
        raise ServiceUnavailableError(
            f"Binance ticker API returned error {exc.response.status_code}."
        )
    except httpx.RequestError as exc:
        logger.error(f"Binance ticker request error: {exc}")
        raise ServiceUnavailableError("Could not reach Binance ticker API.")

    if isinstance(raw, dict):
        raw = [raw]

    normalized: list[dict] = []
    for item in raw:
        symbol = str(item.get("symbol", "")).upper()
        if not symbol:
            continue
        try:
            price = float(item.get("lastPrice", item.get("price", 0.0)))
            change_pct = float(item.get("priceChangePercent", 0.0))
        except (TypeError, ValueError):
            continue
        normalized.append(
            {
                "symbol": symbol,
                "price": price,
                "change_pct": change_pct,
            }
        )

    return normalized


async def _fetch_candles_from_binance(
    symbol: str, timeframe: str, limit: int
) -> list[dict]:
    """
    Fetch OHLCV candles from Binance Futures REST API.
    Returns a list of CandleResponse-compatible dicts.
    """
    binance_interval = _BINANCE_TF_MAP.get(timeframe, "1h")
    url = f"{settings.BINANCE_REST_URL}/fapi/v1/klines"

    params = {
        "symbol": symbol.upper(),
        "interval": binance_interval,
        "limit": min(limit, 1500),
    }

    headers = {}
    if settings.BINANCE_API_KEY:
        headers["X-MBX-APIKEY"] = settings.BINANCE_API_KEY

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            raw = response.json()
    except httpx.HTTPStatusError as exc:
        logger.error(f"Binance API error for {symbol}: {exc.response.status_code}")
        raise ServiceUnavailableError(
            f"Binance API returned error {exc.response.status_code} for {symbol}."
        )
    except httpx.RequestError as exc:
        logger.error(f"Binance request error: {exc}")
        raise ServiceUnavailableError("Could not reach Binance API.")

    candles = []
    for k in raw:
        candles.append(
            {
                "symbol": symbol.upper(),
                "timeframe": timeframe,
                "timestamp": int(k[0]),
                "open": float(k[1]),
                "high": float(k[2]),
                "low": float(k[3]),
                "close": float(k[4]),
                "volume": float(k[5]),
            }
        )
    return candles


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------
@router.get(
    "/",
    response_model=list[PairResponse],
    summary="List active trading pairs",
)
async def list_pairs(
    market: Optional[str] = Query(default=None),
    search: Optional[str] = Query(default=None, max_length=20),
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> list[PairResponse]:
    """
    Public pair listing endpoint used by the UI.
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


# ---------------------------------------------------------------------------
# GET /prices
# ---------------------------------------------------------------------------
@router.get(
    "/prices",
    summary="Get latest prices and 24h change for selected symbols",
)
async def get_prices(
    symbols: str = Query(default="BTCUSDT,ETHUSDT", min_length=3, max_length=500),
) -> list[dict]:
    requested = [s.strip().upper() for s in symbols.split(",") if s.strip()]
    requested = requested[:50]
    if not requested:
        return []

    tickers = await _fetch_ticker_snapshot_from_binance()
    by_symbol = {t["symbol"]: t for t in tickers}

    out: list[dict] = []
    for sym in requested:
        if sym in by_symbol:
            out.append(by_symbol[sym])

    return out


# ---------------------------------------------------------------------------
# GET /ticker
# ---------------------------------------------------------------------------
@router.get(
    "/ticker",
    summary="Get ticker ribbon items",
)
async def get_ticker(
    limit: int = Query(default=20, ge=1, le=100),
) -> list[dict]:
    tickers = await _fetch_ticker_snapshot_from_binance()
    by_symbol = {t["symbol"]: t for t in tickers}

    ordered: list[dict] = []
    seen: set[str] = set()

    # Prioritize common top symbols first.
    for sym in _DEFAULT_TICKER_SYMBOLS:
        item = by_symbol.get(sym)
        if item:
            ordered.append(item)
            seen.add(sym)

    # Fill the rest with strongest movers.
    remaining = [t for t in tickers if t["symbol"] not in seen]
    remaining.sort(key=lambda x: abs(x["change_pct"]), reverse=True)
    ordered.extend(remaining)

    return ordered[:limit]


# ---------------------------------------------------------------------------
# GET /{symbol}/candles
# ---------------------------------------------------------------------------
@router.get(
    "/{symbol}/candles",
    response_model=list[CandleResponse],
    summary="Get OHLCV candle data for a symbol",
)
async def get_candles(
    symbol: str,
    timeframe: str = Query(default=_DEFAULT_TIMEFRAME),
    limit: int = Query(default=_DEFAULT_LIMIT, ge=1, le=1500),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> list[CandleResponse]:
    """
    Return OHLCV candles for the given symbol and timeframe.
    Checks the Redis cache first. Falls back to Binance API on a cache miss.
    """
    symbol = symbol.upper()

    # Validate timeframe
    if timeframe not in _BINANCE_TF_MAP:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid timeframe '{timeframe}'. "
                   f"Allowed: {', '.join(_BINANCE_TF_MAP.keys())}",
        )

    # Try Redis cache first
    cached = await redis.get_candles(symbol, timeframe)
    if cached:
        tail = cached[-limit:]
        return [CandleResponse(**c) for c in tail]

    # Fetch from Binance
    candles = await _fetch_candles_from_binance(symbol, timeframe, limit)

    # Cache the result for future requests
    if candles:
        await redis.set_candles(symbol, timeframe, candles)

    return [CandleResponse(**c) for c in candles[-limit:]]


# ---------------------------------------------------------------------------
# GET /{symbol}/analysis
# ---------------------------------------------------------------------------
@router.get(
    "/{symbol}/analysis",
    response_model=AnalysisResponse,
    summary="Full indicator analysis for a symbol (premium only)",
)
async def get_analysis(
    symbol: str,
    timeframe: str = Query(default=_DEFAULT_TIMEFRAME),
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    redis: RedisClient = Depends(get_redis_client),
) -> AnalysisResponse:
    """
    Run MasterScorer analysis for the given symbol and return full indicator data.
    Requires monthly or lifetime subscription.
    """
    if current_user.plan not in ("monthly", "yearly", "lifetime") and not current_user.is_admin:
        raise SubscriptionRequiredError(
            "Full indicator analysis requires a monthly or lifetime plan.",
            required_plan="monthly",
        )

    symbol = symbol.upper()

    if timeframe not in _BINANCE_TF_MAP:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid timeframe '{timeframe}'. "
                   f"Allowed: {', '.join(_BINANCE_TF_MAP.keys())}",
        )

    # Verify the pair exists in our DB
    result = await db.execute(select(Pair).where(Pair.symbol == symbol))
    pair: Optional[Pair] = result.scalar_one_or_none()
    if pair is None:
        raise NotFoundError("Pair", symbol)

    # Fetch candles (Redis → Binance)
    candles = await redis.get_candles(symbol, timeframe)
    if not candles:
        candles = await _fetch_candles_from_binance(symbol, timeframe, 500)
        if candles:
            await redis.set_candles(symbol, timeframe, candles)

    if not candles:
        raise ServiceUnavailableError(
            f"Could not retrieve candle data for {symbol}/{timeframe}."
        )

    # Run MasterScorer
    try:
        from app.analysis.master_scorer import MasterScorer  # type: ignore

        scorer = MasterScorer(symbol=symbol, timeframe=timeframe, candles=candles)
        analysis_result = await scorer.run()
        return AnalysisResponse(**analysis_result)
    except ImportError:
        logger.warning("MasterScorer not available — returning stub analysis.")
        # Return a minimal stub so the endpoint stays functional during development
        last = candles[-1] if candles else {}
        from datetime import datetime, timezone
        from app.schemas.scanner import IndicatorValues

        return AnalysisResponse(
            symbol=symbol,
            timeframe=timeframe,
            market=pair.market,
            timestamp=datetime.now(tz=timezone.utc),
            price=last.get("close", 0.0),
            indicators=IndicatorValues(),
            score_breakdown={},
            ict_zones={},
            mtf_analysis={},
            overall_direction="NEUTRAL",
            confidence=0,
            signal_triggered=False,
            signal_id=None,
        )
