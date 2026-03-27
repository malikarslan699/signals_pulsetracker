from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from fastapi import APIRouter, Query, WebSocket, WebSocketDisconnect, status
from loguru import logger

from app.core.permissions import Permission, has_permission

router = APIRouter(tags=["WebSocket"])

_HEARTBEAT_INTERVAL = 30  # seconds
_SIGNAL_PUBSUB_CHANNEL = "signals:live"
_SCANNER_PUBSUB_CHANNEL = "scanner:progress"
_ACTIVE_SIGNALS_KEY = "active_signals"
_FREE_SIGNAL_LIMIT = 5


# ---------------------------------------------------------------------------
# ConnectionManager
# ---------------------------------------------------------------------------
class ConnectionManager:
    """
    Tracks active WebSocket connections keyed by user_id.
    Supports broadcast and targeted messaging.
    """

    def __init__(self) -> None:
        # user_id (str) → list of active WebSocket connections
        self._connections: dict[str, list[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, user_id: str) -> None:
        await websocket.accept()
        self._connections.setdefault(user_id, []).append(websocket)
        logger.debug(f"WS connected: user={user_id} total_conns={self.total}")

    def disconnect(self, websocket: WebSocket, user_id: str) -> None:
        conns = self._connections.get(user_id, [])
        if websocket in conns:
            conns.remove(websocket)
        if not conns:
            self._connections.pop(user_id, None)
        logger.debug(f"WS disconnected: user={user_id} total_conns={self.total}")

    async def send_json(self, websocket: WebSocket, data: dict) -> bool:
        """Send a JSON message to a single connection. Returns False on error."""
        try:
            await websocket.send_json(data)
            return True
        except Exception:
            return False

    async def broadcast_json(self, data: dict) -> None:
        """Broadcast a JSON message to all connected clients."""
        dead: list[tuple[str, WebSocket]] = []
        for user_id, sockets in list(self._connections.items()):
            for ws in sockets:
                ok = await self.send_json(ws, data)
                if not ok:
                    dead.append((user_id, ws))
        for user_id, ws in dead:
            self.disconnect(ws, user_id)

    @property
    def total(self) -> int:
        return sum(len(v) for v in self._connections.values())


# Module-level singletons
_signal_manager = ConnectionManager()
_scanner_manager = ConnectionManager()


# ---------------------------------------------------------------------------
# Helper: authenticate WebSocket via token query param
# ---------------------------------------------------------------------------
async def _authenticate_ws(token: Optional[str]) -> Optional[object]:
    """
    Validate the Bearer token passed as a query parameter.
    Returns the User ORM object or None if authentication fails.
    """
    if not token:
        return None
    try:
        from app.core.auth import decode_token
        from app.database import AsyncSessionFactory
        from app.models.user import User
        from app.redis_client import get_redis, RedisClient
        from sqlalchemy.future import select

        payload = decode_token(token)
        if payload.get("type") != "access":
            return None

        jti: Optional[str] = payload.get("jti")
        user_id: Optional[str] = payload.get("sub")

        async with get_redis() as redis_conn:
            rc = RedisClient(redis_conn)
            if jti and await rc.is_token_blacklisted(jti):
                return None

        async with AsyncSessionFactory() as db:
            result = await db.execute(
                select(User).where(User.id == UUID(user_id))
            )
            user = result.scalar_one_or_none()
            if user and user.is_active:
                return user
    except Exception as exc:
        logger.debug(f"WS auth failed: {exc}")
    return None


# ---------------------------------------------------------------------------
# WS /ws/signals
# ---------------------------------------------------------------------------
@router.websocket("/ws/signals")
async def ws_signals(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
) -> None:
    """
    WebSocket endpoint for the live signal feed.

    - Authenticates via `?token=<access_token>`
    - Sends the current active signals batch on connect
    - Subscribes to `signals:live` Redis pubsub channel
    - Sends a heartbeat ping every 30 seconds
    - Free users receive at most {_FREE_SIGNAL_LIMIT} signals
    """
    user = await _authenticate_ws(token)

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.debug("WS /ws/signals rejected: authentication failed.")
        return

    # Check WebSocket plan permission
    from app.core.permissions import PLAN_LIMITS

    plan_limits = PLAN_LIMITS.get(user.plan, PLAN_LIMITS["trial"])
    if not plan_limits.can_use_websocket:
        await websocket.accept()
        await websocket.send_json({
            "type": "error",
            "code": "PLAN_REQUIRED",
            "message": "WebSocket access requires a trial or paid plan.",
        })
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    user_id = str(user.id)
    can_see_ict = has_permission(user, Permission.READ_ICT)
    is_free = user.plan == "trial"

    await _signal_manager.connect(websocket, user_id)

    try:
        # --- Send initial batch of active signals ---
        from app.redis_client import get_redis, RedisClient

        async with get_redis() as redis_conn:
            rc = RedisClient(redis_conn)
            initial_signals = await rc.get_all_active_signals()

        if is_free:
            initial_signals = initial_signals[:_FREE_SIGNAL_LIMIT]

        if not can_see_ict:
            cleaned = []
            for s in initial_signals:
                s = dict(s)
                s.pop("score_breakdown", None)
                s.pop("ict_zones", None)
                cleaned.append(s)
            initial_signals = cleaned

        await websocket.send_json({
            "type": "initial_batch",
            "signals": initial_signals,
            "count": len(initial_signals),
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        })

        # --- Set up pubsub listener and heartbeat concurrently ---
        async def _pubsub_listener() -> None:
            async with get_redis() as redis_conn:
                rc = RedisClient(redis_conn)
                pubsub = rc.get_pubsub()
                await pubsub.subscribe(_SIGNAL_PUBSUB_CHANNEL)
                try:
                    async for message in pubsub.listen():
                        if message["type"] != "message":
                            continue
                        try:
                            data = json.loads(message["data"])
                        except (json.JSONDecodeError, TypeError):
                            continue

                        # Filter for free users
                        if is_free:
                            # Only send if user hasn't hit limit (already sent initial batch)
                            pass

                        if not can_see_ict:
                            data = dict(data)
                            data.pop("score_breakdown", None)
                            data.pop("ict_zones", None)

                        ok = await _signal_manager.send_json(
                            websocket, {"type": "signal", "data": data}
                        )
                        if not ok:
                            break
                finally:
                    await pubsub.unsubscribe(_SIGNAL_PUBSUB_CHANNEL)

        async def _heartbeat() -> None:
            while True:
                await asyncio.sleep(_HEARTBEAT_INTERVAL)
                ok = await _signal_manager.send_json(
                    websocket,
                    {
                        "type": "heartbeat",
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    },
                )
                if not ok:
                    break

        async def _receive_loop() -> None:
            """Drain incoming messages (pings/pongs) to keep the connection alive."""
            while True:
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break

        await asyncio.gather(
            _pubsub_listener(),
            _heartbeat(),
            _receive_loop(),
            return_exceptions=True,
        )

    except WebSocketDisconnect:
        logger.debug(f"WS /ws/signals disconnected: user={user_id}")
    except Exception as exc:
        logger.error(f"WS /ws/signals error for user={user_id}: {exc}")
    finally:
        _signal_manager.disconnect(websocket, user_id)


# ---------------------------------------------------------------------------
# WS /ws/scanner
# ---------------------------------------------------------------------------
@router.websocket("/ws/scanner")
async def ws_scanner(
    websocket: WebSocket,
    token: Optional[str] = Query(default=None),
) -> None:
    """
    WebSocket endpoint for scanner progress updates.

    - Authenticates via `?token=<access_token>`
    - Subscribes to `scanner:progress` Redis pubsub channel
    - Streams real-time scanner progress events to the client
    """
    user = await _authenticate_ws(token)

    if user is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        logger.debug("WS /ws/scanner rejected: authentication failed.")
        return

    user_id = str(user.id)
    await _scanner_manager.connect(websocket, user_id)

    try:
        # Send current scanner status as initial message
        from app.redis_client import get_redis, RedisClient

        async with get_redis() as redis_conn:
            rc = RedisClient(redis_conn)
            current_status = await rc.get_scanner_status()

        await websocket.send_json({
            "type": "scanner_status",
            "data": current_status or {},
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
        })

        async def _scanner_listener() -> None:
            async with get_redis() as redis_conn:
                rc = RedisClient(redis_conn)
                pubsub = rc.get_pubsub()
                await pubsub.subscribe(_SCANNER_PUBSUB_CHANNEL)
                try:
                    async for message in pubsub.listen():
                        if message["type"] != "message":
                            continue
                        try:
                            data = json.loads(message["data"])
                        except (json.JSONDecodeError, TypeError):
                            continue

                        ok = await _scanner_manager.send_json(
                            websocket,
                            {
                                "type": "scanner_progress",
                                "data": data,
                                "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                            },
                        )
                        if not ok:
                            break
                finally:
                    await pubsub.unsubscribe(_SCANNER_PUBSUB_CHANNEL)

        async def _heartbeat() -> None:
            while True:
                await asyncio.sleep(_HEARTBEAT_INTERVAL)
                ok = await _scanner_manager.send_json(
                    websocket,
                    {
                        "type": "heartbeat",
                        "timestamp": datetime.now(tz=timezone.utc).isoformat(),
                    },
                )
                if not ok:
                    break

        async def _receive_loop() -> None:
            while True:
                try:
                    await websocket.receive_text()
                except WebSocketDisconnect:
                    break

        await asyncio.gather(
            _scanner_listener(),
            _heartbeat(),
            _receive_loop(),
            return_exceptions=True,
        )

    except WebSocketDisconnect:
        logger.debug(f"WS /ws/scanner disconnected: user={user_id}")
    except Exception as exc:
        logger.error(f"WS /ws/scanner error for user={user_id}: {exc}")
    finally:
        _scanner_manager.disconnect(websocket, user_id)
