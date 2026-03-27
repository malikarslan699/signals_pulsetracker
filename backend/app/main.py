from __future__ import annotations

import time
from contextlib import asynccontextmanager
from typing import Callable

from fastapi import FastAPI, Request, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from loguru import logger

from app.config import get_settings
from app.core.exceptions import RateLimitError, register_exception_handlers
from app.database import check_db_health, create_tables
from app.api.v1.router import api_router, ws_router

settings = get_settings()


# ---------------------------------------------------------------------------
# Application lifespan
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup and shutdown lifecycle management."""
    # --- STARTUP ---
    logger.info("PulseSignal Pro API starting up…")

    # Ensure core schema exists on startup.
    # Alembic migrations are preferred for controlled upgrades, but this
    # keeps fresh deployments from booting with an empty DB.
    await create_tables()
    logger.info("Database tables verified.")

    # Verify Redis connectivity
    from app.redis_client import get_redis, RedisClient
    async with get_redis() as redis:
        rc = RedisClient(redis)
        ok = await rc.ping()
        if ok:
            logger.info("Redis connection established.")
        else:
            logger.warning("Redis is not reachable at startup — continuing anyway.")

    # Purge stale low-quality signals from Redis on startup
    try:
        from workers.cleanup_task import purge_low_quality_signals
        purge_low_quality_signals.apply_async(queue='default')
        logger.info("Scheduled startup purge of low-quality signals.")
    except Exception as _e:
        logger.warning(f"Could not schedule startup purge: {_e}")

    logger.info(
        f"PulseSignal Pro API ready. "
        f"Environment: {settings.ENVIRONMENT}. "
        f"Docs: {settings.BACKEND_URL}/api/docs"
    )

    yield

    # --- SHUTDOWN ---
    logger.info("PulseSignal Pro API shutting down…")

    # Close Redis pool
    from app.redis_client import _pool
    if _pool is not None:
        await _pool.aclose()
        logger.info("Redis connection pool closed.")

    logger.info("Shutdown complete.")


# ---------------------------------------------------------------------------
# FastAPI application instance
# ---------------------------------------------------------------------------
app = FastAPI(
    title="PulseSignal Pro API",
    description=(
        "Professional Trading Signal Platform — signals.pulsetracker.net\n\n"
        "Provides real-time ICT-based trading signals for crypto and forex markets."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# ---------------------------------------------------------------------------
# Middleware: CORS
# ---------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["X-Request-ID", "X-Rate-Limit-Remaining", "X-Rate-Limit-Reset"],
)

# ---------------------------------------------------------------------------
# Middleware: GZip
# ---------------------------------------------------------------------------
app.add_middleware(GZipMiddleware, minimum_size=1024)

# ---------------------------------------------------------------------------
# Exception handlers
# ---------------------------------------------------------------------------
register_exception_handlers(app)

# ---------------------------------------------------------------------------
# Middleware: Request Logging
# ---------------------------------------------------------------------------
@app.middleware("http")
async def logging_middleware(request: Request, call_next: Callable) -> Response:
    start = time.perf_counter()
    request_id = request.headers.get("X-Request-ID", "")

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"{request.method} {request.url.path} "
        f"→ {response.status_code} "
        f"[{duration_ms:.1f}ms] "
        f"ip={request.client.host if request.client else 'unknown'} "
        f"rid={request_id}"
    )
    response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
    return response


# ---------------------------------------------------------------------------
# Middleware: Rate Limiting (sliding window via Redis)
# ---------------------------------------------------------------------------
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next: Callable) -> Response:
    # Skip rate limiting for health checks and docs
    skip_paths = {"/health", "/api/docs", "/api/redoc", "/api/openapi.json"}
    if request.url.path in skip_paths:
        return await call_next(request)

    client_ip = request.client.host if request.client else "unknown"
    window_seconds = 60

    # Choose limit based on path — auth endpoints are stricter
    if request.url.path.startswith("/api/v1/auth"):
        limit = 20
    else:
        limit = 200

    redis_key = f"rate:{client_ip}:{request.url.path.split('/')[3] if len(request.url.path.split('/')) > 3 else 'root'}"

    try:
        from app.redis_client import get_redis, RedisClient
        async with get_redis() as redis_conn:
            rc = RedisClient(redis_conn)
            count = await rc.incr_rate_limit(redis_key, window_seconds)

        if count > limit:
            raise RateLimitError(retry_after=window_seconds)

        response = await call_next(request)
        response.headers["X-Rate-Limit-Limit"] = str(limit)
        response.headers["X-Rate-Limit-Remaining"] = str(max(0, limit - count))
        return response

    except RateLimitError as exc:
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "error": True,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "detail": exc.detail,
                "status_code": 429,
            },
            headers=exc.headers or {},
        )
    except Exception:
        # If Redis is down, don't block requests — just pass through
        return await call_next(request)


# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------
@app.get(
    "/health",
    tags=["Health"],
    summary="Service health check",
    response_description="Health status of the API and its dependencies",
)
async def health_check() -> JSONResponse:
    """
    Returns the operational health of the PulseSignal Pro API.
    Checks database and Redis connectivity.
    """
    db_ok = await check_db_health()

    redis_ok = False
    try:
        from app.redis_client import get_redis, RedisClient
        async with get_redis() as redis_conn:
            rc = RedisClient(redis_conn)
            redis_ok = await rc.ping()
    except Exception:
        redis_ok = False

    overall = "healthy" if (db_ok and redis_ok) else "degraded"
    http_status = status.HTTP_200_OK if overall == "healthy" else status.HTTP_503_SERVICE_UNAVAILABLE

    return JSONResponse(
        status_code=http_status,
        content={
            "status": overall,
            "version": "1.0.0",
            "environment": settings.ENVIRONMENT,
            "service": "PulseSignal Pro API",
            "domain": "signals.pulsetracker.net",
            "checks": {
                "database": "ok" if db_ok else "error",
                "redis": "ok" if redis_ok else "error",
            },
        },
    )


# ---------------------------------------------------------------------------
# Router registration
# ---------------------------------------------------------------------------
app.include_router(api_router)
app.include_router(ws_router)
