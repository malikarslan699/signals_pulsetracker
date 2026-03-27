from __future__ import annotations

import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, AsyncGenerator, Optional

import redis.asyncio as aioredis
from redis.exceptions import ResponseError
from loguru import logger

from app.config import get_settings

settings = get_settings()

# ---------------------------------------------------------------------------
# Connection pool (module-level singleton)
# ---------------------------------------------------------------------------
_pool: Optional[aioredis.ConnectionPool] = None


def _get_pool() -> aioredis.ConnectionPool:
    global _pool
    if _pool is None:
        _pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=50,
            decode_responses=True,
        )
    return _pool


@asynccontextmanager
async def get_redis() -> AsyncGenerator[aioredis.Redis, None]:
    """Async context manager that yields a Redis client from the shared pool."""
    client = aioredis.Redis(connection_pool=_get_pool())
    try:
        yield client
    finally:
        await client.aclose()


# ---------------------------------------------------------------------------
# RedisClient helper class
# ---------------------------------------------------------------------------
class RedisClient:
    """High-level Redis operations for PulseSignal Pro."""

    # Key prefixes
    _CANDLES_KEY = "candles:{symbol}:{timeframe}"
    _SIGNAL_KEY = "signal:{symbol}"
    _ACTIVE_SIGNALS_KEY = "active_signals"
    _SCANNER_QUEUE_KEY = "scanner:queue"
    _SCANNER_STATUS_KEY = "scanner:status"
    _SIGNAL_PUBSUB_CHANNEL = "signals:live"
    _JWT_BLACKLIST_KEY = "jwt:blacklist:{jti}"

    def __init__(self, client: aioredis.Redis) -> None:
        self._r = client

    # ------------------------------------------------------------------
    # Candle Cache
    # ------------------------------------------------------------------
    async def set_candles(
        self,
        symbol: str,
        timeframe: str,
        candles: list[dict],
    ) -> None:
        """Store OHLCV candle list in Redis (capped at MAX_CANDLES_CACHE)."""
        key = self._CANDLES_KEY.format(symbol=symbol, timeframe=timeframe)
        max_len = settings.MAX_CANDLES_CACHE

        pipe = self._r.pipeline()
        pipe.delete(key)
        for candle in candles[-max_len:]:
            pipe.rpush(key, json.dumps(candle))
        pipe.expire(key, 3600 * 6)  # 6-hour TTL
        await pipe.execute()

    async def get_candles(self, symbol: str, timeframe: str) -> list[dict]:
        """Return cached candle list for the given symbol/timeframe."""
        key = self._CANDLES_KEY.format(symbol=symbol, timeframe=timeframe)
        raw_list = await self._r.lrange(key, 0, -1)
        return [json.loads(item) for item in raw_list]

    async def append_candle(
        self,
        symbol: str,
        timeframe: str,
        candle: dict,
    ) -> None:
        """Append a single candle and trim to MAX_CANDLES_CACHE."""
        key = self._CANDLES_KEY.format(symbol=symbol, timeframe=timeframe)
        pipe = self._r.pipeline()
        pipe.rpush(key, json.dumps(candle))
        pipe.ltrim(key, -settings.MAX_CANDLES_CACHE, -1)
        pipe.expire(key, 3600 * 6)
        await pipe.execute()

    # ------------------------------------------------------------------
    # Signal Cache
    # ------------------------------------------------------------------
    async def set_signal(self, symbol: str, signal_data: dict) -> None:
        """Store the latest signal for a symbol and add to active-signals set."""
        key = self._SIGNAL_KEY.format(symbol=symbol)
        payload = json.dumps(signal_data)

        # TTL: 24 hours for individual signal
        pipe = self._r.pipeline()
        pipe.set(key, payload, ex=86400)
        # Sorted set: score = confidence (higher = better)
        confidence = signal_data.get("confidence", 0)
        pipe.zadd(self._ACTIVE_SIGNALS_KEY, {symbol: confidence})
        pipe.expire(self._ACTIVE_SIGNALS_KEY, 86400)
        await pipe.execute()

    async def get_signal(self, symbol: str) -> Optional[dict]:
        """Return the latest cached signal for a symbol."""
        key = self._SIGNAL_KEY.format(symbol=symbol)
        raw = await self._r.get(key)
        return json.loads(raw) if raw else None

    async def get_all_active_signals(self) -> list[dict]:
        """Return all active signals sorted by confidence descending."""
        symbols = await self._r.zrevrangebyscore(
            self._ACTIVE_SIGNALS_KEY, "+inf", "-inf"
        )
        signals: list[dict] = []
        for symbol in symbols:
            data = await self.get_signal(symbol)
            if data:
                signals.append(data)
        if signals:
            return signals

        # Backward compatibility: legacy workers used a different sorted-set key
        # and stored full JSON payloads as members.
        legacy_rows = await self._r.zrevrangebyscore("signals:active", "+inf", "-inf")
        legacy_signals: list[dict] = []
        for row in legacy_rows:
            try:
                payload = json.loads(row)
            except Exception:
                continue
            if isinstance(payload, dict):
                legacy_signals.append(payload)

        if legacy_signals:
            pipe = self._r.pipeline()
            for payload in legacy_signals:
                symbol = str(payload.get("symbol", "")).upper()
                if not symbol:
                    continue
                confidence = float(payload.get("confidence", 0) or 0)
                key = self._SIGNAL_KEY.format(symbol=symbol)
                pipe.set(key, json.dumps(payload), ex=86400)
                pipe.zadd(self._ACTIVE_SIGNALS_KEY, {symbol: confidence})
            pipe.expire(self._ACTIVE_SIGNALS_KEY, 86400)
            await pipe.execute()

        return legacy_signals

    async def remove_signal(self, symbol: str) -> None:
        """Remove a signal from cache and active-signals set."""
        key = self._SIGNAL_KEY.format(symbol=symbol)
        pipe = self._r.pipeline()
        pipe.delete(key)
        pipe.zrem(self._ACTIVE_SIGNALS_KEY, symbol)
        # Clean legacy payload-based zset entries for this symbol.
        rows = await self._r.zrange("signals:active", 0, -1)
        for row in rows:
            try:
                payload = json.loads(row)
            except Exception:
                continue
            if str(payload.get("symbol", "")).upper() == symbol.upper():
                pipe.zrem("signals:active", row)
        await pipe.execute()

    # ------------------------------------------------------------------
    # Scanner Queue
    # ------------------------------------------------------------------
    async def push_scanner_queue(self, symbol: str) -> None:
        """Push a symbol onto the scanner work queue."""
        await self._r.lpush(self._SCANNER_QUEUE_KEY, symbol)

    async def pop_scanner_queue(self, timeout: int = 30) -> Optional[str]:
        """
        Blocking pop from the scanner queue.
        Returns the symbol string or None on timeout.
        """
        result = await self._r.brpop(self._SCANNER_QUEUE_KEY, timeout=timeout)
        if result:
            _key, value = result
            return value
        return None

    async def get_scanner_queue_length(self) -> int:
        """Return the current number of items in the scanner queue."""
        return await self._r.llen(self._SCANNER_QUEUE_KEY)

    # ------------------------------------------------------------------
    # Scanner Status
    # ------------------------------------------------------------------
    async def set_scanner_status(self, status_dict: dict) -> None:
        """Persist scanner health / progress status."""
        await self._r.set(
            self._SCANNER_STATUS_KEY,
            json.dumps(status_dict),
            ex=3600,
        )

    async def get_scanner_status(self) -> Optional[dict]:
        """Return the latest scanner status dict."""
        try:
            raw = await self._r.get(self._SCANNER_STATUS_KEY)
            if raw:
                return json.loads(raw)
        except ResponseError:
            # Legacy format stored scanner status as a Redis hash.
            pass

        try:
            mapping = await self._r.hgetall(self._SCANNER_STATUS_KEY)
            if not mapping:
                return None

            def _to_bool(value: str | None) -> bool:
                if value is None:
                    return False
                return str(value).lower() in {"1", "true", "yes", "on"}

            def _to_int(value: str | None) -> int:
                if value in (None, ""):
                    return 0
                try:
                    return int(float(value))
                except Exception:
                    return 0

            started_at = mapping.get("started_at")
            uptime_seconds: Optional[float] = None
            if started_at:
                try:
                    started = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                    if started.tzinfo is None:
                        started = started.replace(tzinfo=timezone.utc)
                    uptime_seconds = max(
                        0.0,
                        (datetime.now(timezone.utc) - started.astimezone(timezone.utc)).total_seconds(),
                    )
                except Exception:
                    uptime_seconds = None

            return {
                "is_running": mapping.get("status") == "running" or _to_bool(mapping.get("is_running")),
                "current_market": mapping.get("market") or mapping.get("current_market"),
                "pairs_total": _to_int(mapping.get("pairs_total")),
                "pairs_done": _to_int(mapping.get("pairs_done")),
                "signals_found": _to_int(mapping.get("signals_found")),
                "started_at": started_at,
                "uptime_seconds": uptime_seconds,
            }
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Pub/Sub (WebSocket live feed)
    # ------------------------------------------------------------------
    async def publish_signal(self, signal_data: dict) -> None:
        """Publish a signal to the live feed channel for WebSocket consumers."""
        await self._r.publish(
            self._SIGNAL_PUBSUB_CHANNEL, json.dumps(signal_data)
        )

    def get_pubsub(self) -> aioredis.client.PubSub:
        """Return a PubSub instance subscribed to the live signal channel."""
        return self._r.pubsub()

    # ------------------------------------------------------------------
    # JWT Blacklist
    # ------------------------------------------------------------------
    async def blacklist_token(self, jti: str, expires_in: int) -> None:
        """
        Add a JWT ID to the blacklist.
        expires_in — seconds until the token would naturally expire.
        """
        key = self._JWT_BLACKLIST_KEY.format(jti=jti)
        await self._r.set(key, "1", ex=max(expires_in, 1))

    async def is_token_blacklisted(self, jti: str) -> bool:
        """Return True if the token JTI is in the blacklist."""
        key = self._JWT_BLACKLIST_KEY.format(jti=jti)
        return bool(await self._r.exists(key))

    # ------------------------------------------------------------------
    # Generic helpers
    # ------------------------------------------------------------------
    async def ping(self) -> bool:
        """Return True if Redis is reachable."""
        try:
            return await self._r.ping()
        except Exception as exc:
            logger.error(f"Redis ping failed: {exc}")
            return False

    async def incr_rate_limit(self, key: str, window_seconds: int) -> int:
        """
        Sliding-window rate limit counter.
        Increments the counter at `key` and sets TTL on first call.
        Returns the current count.
        """
        pipe = self._r.pipeline()
        pipe.incr(key)
        pipe.expire(key, window_seconds, nx=True)
        results = await pipe.execute()
        return int(results[0])


# ---------------------------------------------------------------------------
# Module-level convenience: create a RedisClient from the shared pool
# ---------------------------------------------------------------------------
async def get_redis_client() -> AsyncGenerator[RedisClient, None]:
    """FastAPI dependency that yields a RedisClient."""
    async with get_redis() as client:
        yield RedisClient(client)
