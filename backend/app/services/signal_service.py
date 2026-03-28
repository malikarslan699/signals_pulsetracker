from __future__ import annotations

import math
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Optional
from uuid import UUID

from loguru import logger
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal
from app.config import get_settings
from app.redis_client import RedisClient
from app.schemas.signal import SignalCreate, SignalFilter
from app.services.signal_lifecycle import (
    LOSS_SIGNAL_STATUSES,
    OPEN_SIGNAL_STATUSES,
    WIN_SIGNAL_STATUSES,
    canonicalize_status,
    is_final_status,
)

settings = get_settings()


def _calc_rr(entry: float, stop_loss: float, take_profit: float | None) -> float | None:
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


class SignalService:
    """Business logic layer for trading signals."""

    def __init__(self, db: AsyncSession, redis: RedisClient) -> None:
        self._db = db
        self._redis = redis

    # ------------------------------------------------------------------
    # Create
    # ------------------------------------------------------------------
    async def create_signal(self, signal_data: dict) -> Signal:
        """
        Persist a new signal from the analysis engine.
        Also caches the signal in Redis and publishes to the live feed.
        """
        schema = SignalCreate(**signal_data)

        signal = Signal(
            pair_id=schema.pair_id,
            symbol=schema.symbol,
            market=schema.market,
            direction=schema.direction,
            timeframe=schema.timeframe,
            confidence=schema.confidence,
            setup_score=schema.setup_score,
            pwin_tp1=schema.pwin_tp1,
            pwin_tp2=schema.pwin_tp2,
            ranking_score=schema.ranking_score,
            entry=schema.entry,
            entry_zone_low=schema.entry_zone_low,
            entry_zone_high=schema.entry_zone_high,
            entry_type=schema.entry_type,
            stop_loss=schema.stop_loss,
            invalidation_price=schema.invalidation_price,
            take_profit_1=schema.take_profit_1,
            take_profit_2=schema.take_profit_2,
            take_profit_3=schema.take_profit_3,
            rr_ratio=schema.rr_ratio,
            raw_score=schema.raw_score,
            max_possible_score=schema.max_possible_score,
            score_breakdown=schema.score_breakdown,
            ict_zones=schema.ict_zones,
            candle_snapshot=schema.candle_snapshot,
            mtf_analysis=schema.mtf_analysis,
            valid_until=schema.valid_until,
            expires_at=schema.expires_at,
            status=schema.status or "CREATED",
            alert_sent=False,
        )
        self._db.add(signal)
        await self._db.flush()  # get the generated ID

        # Cache in Redis
        signal_dict = self._signal_to_dict(signal)
        await self._redis.set_signal(signal.symbol, signal_dict)
        await self._redis.publish_signal(signal_dict)

        logger.info(
            f"Signal created: {signal.symbol} {signal.direction} "
            f"confidence={signal.confidence} id={signal.id}"
        )
        return signal

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------
    async def get_signals(
        self,
        filters: SignalFilter,
        page: int = 1,
        limit: int = 20,
    ) -> tuple[list[Signal], int]:
        """
        Return a paginated list of signals matching the given filters.
        Returns (items, total_count).
        """
        query = select(Signal)
        count_query = select(func.count()).select_from(Signal)

        if filters.market:
            query = query.where(Signal.market == filters.market)
            count_query = count_query.where(Signal.market == filters.market)

        if filters.direction:
            query = query.where(Signal.direction == filters.direction)
            count_query = count_query.where(Signal.direction == filters.direction)

        if filters.timeframe:
            query = query.where(Signal.timeframe == filters.timeframe)
            count_query = count_query.where(Signal.timeframe == filters.timeframe)

        if filters.min_confidence is not None:
            query = query.where(Signal.confidence >= filters.min_confidence)
            count_query = count_query.where(
                Signal.confidence >= filters.min_confidence
            )

        if filters.symbol:
            query = query.where(
                Signal.symbol == filters.symbol.upper()
            )
            count_query = count_query.where(
                Signal.symbol == filters.symbol.upper()
            )

        if filters.status:
            query = query.where(Signal.status == filters.status)
            count_query = count_query.where(Signal.status == filters.status)

        if filters.from_date:
            query = query.where(Signal.fired_at >= filters.from_date)
            count_query = count_query.where(Signal.fired_at >= filters.from_date)

        if filters.to_date:
            query = query.where(Signal.fired_at <= filters.to_date)
            count_query = count_query.where(Signal.fired_at <= filters.to_date)

        # Count
        total_result = await self._db.execute(count_query)
        total: int = total_result.scalar_one()

        # Paginate
        offset = (page - 1) * limit
        query = query.order_by(Signal.fired_at.desc()).offset(offset).limit(limit)

        result = await self._db.execute(query)
        items = list(result.scalars().all())

        return items, total

    async def get_signal_by_id(self, signal_id: UUID) -> Signal:
        """Return a single signal by its UUID. Raises ValueError if not found."""
        result = await self._db.execute(
            select(Signal).where(Signal.id == signal_id)
        )
        signal = result.scalar_one_or_none()
        if signal is None:
            raise ValueError(f"Signal {signal_id} not found.")
        return signal

    async def get_live_signals(self, min_confidence: int = 75) -> list[dict]:
        """
        Return all currently active signals above the confidence threshold.
        Checks Redis cache first, then falls back to DB.
        """
        cached = await self._redis.get_all_active_signals()
        if cached:
            return [
                s for s in cached if s.get("confidence", 0) >= min_confidence
            ]

        # Fallback to DB
        now = datetime.now(tz=timezone.utc)
        result = await self._db.execute(
            select(Signal)
            .where(Signal.status.in_(tuple(OPEN_SIGNAL_STATUSES)))
            .where(Signal.confidence >= min_confidence)
            .where(
                (Signal.expires_at == None) | (Signal.expires_at > now)  # noqa: E711
            )
            .order_by(Signal.ranking_score.desc().nullslast(), Signal.confidence.desc())
            .limit(100)
        )
        signals = list(result.scalars().all())
        return [self._signal_to_dict(s) for s in signals]

    async def get_signal_history(
        self, user_id: UUID, days: int = 30
    ) -> list[Signal]:
        """Return closed/expired signals from the last `days` days."""
        from_date = datetime.now(tz=timezone.utc) - timedelta(days=days)
        result = await self._db.execute(
            select(Signal)
            .where(Signal.fired_at >= from_date)
            .where(~Signal.status.in_(tuple(OPEN_SIGNAL_STATUSES)))
            .order_by(Signal.fired_at.desc())
            .limit(500)
        )
        return list(result.scalars().all())

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------
    async def update_signal_status(
        self,
        signal_id: UUID,
        status: str,
        close_price: Optional[Decimal] = None,
    ) -> Signal:
        """
        Update the lifecycle status of a signal.
        Calculates PnL % when a signal closes.
        """
        signal = await self.get_signal_by_id(signal_id)
        signal.status = canonicalize_status(status)

        if close_price is not None:
            signal.close_price = close_price
            # Calculate PnL %
            entry = float(signal.entry)
            close = float(close_price)
            if entry > 0:
                if signal.direction == "LONG":
                    pnl = ((close - entry) / entry) * 100
                else:
                    pnl = ((entry - close) / entry) * 100
                signal.pnl_pct = Decimal(str(round(pnl, 4)))

        if is_final_status(signal.status):
            signal.closed_at = datetime.now(tz=timezone.utc)

        # Remove from Redis active set if closed
        if is_final_status(signal.status):
            await self._redis.remove_signal(signal.symbol)

        await self._db.flush()
        logger.info(f"Signal {signal_id} status updated to '{signal.status}'.")
        return signal

    async def mark_alert_sent(self, signal_id: UUID) -> None:
        """Mark a signal as having its alert dispatched."""
        signal = await self.get_signal_by_id(signal_id)
        signal.alert_sent = True
        await self._db.flush()

    # ------------------------------------------------------------------
    # Analytics
    # ------------------------------------------------------------------
    async def get_platform_stats(self) -> dict:
        """
        Return aggregate statistics for the platform dashboard.
        Includes total signals, win rate, avg confidence, etc.
        """
        thirty_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=30)

        # Total signals (all time)
        total_result = await self._db.execute(
            select(func.count()).select_from(Signal)
        )
        total_signals: int = total_result.scalar_one()

        # Signals last 30 days
        recent_result = await self._db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.fired_at >= thirty_days_ago)
        )
        signals_30d: int = recent_result.scalar_one()

        # Win rate (TP hits vs SL hits in last 90 days)
        ninety_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=90)
        tp_result = await self._db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.fired_at >= ninety_days_ago)
            .where(Signal.status.in_(tuple(WIN_SIGNAL_STATUSES)))
        )
        tp_count: int = tp_result.scalar_one()

        sl_result = await self._db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.fired_at >= ninety_days_ago)
            .where(Signal.status.in_(tuple(LOSS_SIGNAL_STATUSES)))
        )
        sl_count: int = sl_result.scalar_one()

        closed_total = tp_count + sl_count
        win_rate = round((tp_count / closed_total * 100) if closed_total > 0 else 0, 1)

        # Win rate (7d) for dashboard card
        seven_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=7)
        tp_7d_result = await self._db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.fired_at >= seven_days_ago)
            .where(Signal.status.in_(tuple(WIN_SIGNAL_STATUSES)))
        )
        tp_7d_count: int = tp_7d_result.scalar_one()

        sl_7d_result = await self._db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.fired_at >= seven_days_ago)
            .where(Signal.status.in_(tuple(LOSS_SIGNAL_STATUSES)))
        )
        sl_7d_count: int = sl_7d_result.scalar_one()
        closed_7d = tp_7d_count + sl_7d_count
        win_rate_7d = round((tp_7d_count / closed_7d * 100) if closed_7d > 0 else 0, 1)

        # Average confidence (last 30 days)
        avg_conf_result = await self._db.execute(
            select(func.avg(Signal.confidence))
            .where(Signal.fired_at >= thirty_days_ago)
        )
        avg_confidence = avg_conf_result.scalar_one()
        avg_confidence = round(float(avg_confidence), 1) if avg_confidence else 0.0

        # Active signals right now
        active_result = await self._db.execute(
            select(func.count())
            .select_from(Signal)
            .where(Signal.status.in_(tuple(OPEN_SIGNAL_STATUSES)))
        )
        active_signals: int = active_result.scalar_one()

        scanner_status = await self._redis.get_scanner_status() or {}
        queue_length = await self._redis.get_scanner_queue_length()
        pairs_scanned = int(
            scanner_status.get("pairs_done")
            or scanner_status.get("pairs_total")
            or 0
        )

        is_running = bool(scanner_status.get("is_running"))
        if is_running:
            next_scan_in = "Running"
        else:
            next_scan_in = f"{settings.SCANNER_INTERVAL_MINUTES}m"

        if not is_running and scanner_status.get("started_at"):
            try:
                started_at = datetime.fromisoformat(
                    str(scanner_status.get("started_at")).replace("Z", "+00:00")
                )
                if started_at.tzinfo is None:
                    started_at = started_at.replace(tzinfo=timezone.utc)
                elapsed = (datetime.now(tz=timezone.utc) - started_at).total_seconds()
                remaining = int(settings.SCANNER_INTERVAL_MINUTES * 60 - elapsed)
                if remaining > 0:
                    mins, secs = divmod(remaining, 60)
                    next_scan_in = f"{mins:02d}:{secs:02d}"
                else:
                    next_scan_in = "due"
            except Exception:
                pass

        return {
            "total_signals": total_signals,
            "signals_last_30d": signals_30d,
            "active_signals": active_signals,
            "win_rate_pct": win_rate,
            "win_rate_7d": win_rate_7d,
            "win_rate_all": win_rate,
            "avg_confidence": avg_confidence,
            "tp_hits_90d": tp_count,
            "sl_hits_90d": sl_count,
            "closed_total_90d": closed_total,
            "pairs_scanned": pairs_scanned,
            "next_scan_in": next_scan_in,
            "scanner_queue_length": queue_length,
            "scanner_is_running": is_running,
        }

    async def get_pair_analysis(self, symbol: str) -> dict:
        """
        Return recent signal history and performance for a specific pair.
        """
        symbol = symbol.upper()
        ninety_days_ago = datetime.now(tz=timezone.utc) - timedelta(days=90)

        result = await self._db.execute(
            select(Signal)
            .where(Signal.symbol == symbol)
            .where(Signal.fired_at >= ninety_days_ago)
            .order_by(Signal.fired_at.desc())
            .limit(100)
        )
        signals = list(result.scalars().all())

        if not signals:
            return {
                "symbol": symbol,
                "total_signals": 0,
                "win_rate_pct": 0.0,
                "avg_confidence": 0.0,
                "recent_signals": [],
            }

        tp_count = sum(
            1 for s in signals if s.status in WIN_SIGNAL_STATUSES
        )
        sl_count = sum(1 for s in signals if s.status in LOSS_SIGNAL_STATUSES)
        closed = tp_count + sl_count
        win_rate = round((tp_count / closed * 100) if closed > 0 else 0, 1)

        avg_conf = sum(s.confidence for s in signals) / len(signals)

        recent = [self._signal_to_dict(s) for s in signals[:10]]

        return {
            "symbol": symbol,
            "total_signals": len(signals),
            "win_rate_pct": win_rate,
            "avg_confidence": round(avg_conf, 1),
            "tp_count": tp_count,
            "sl_count": sl_count,
            "recent_signals": recent,
        }

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------
    def _signal_to_dict(self, signal: Signal) -> dict:
        """Serialize a Signal ORM object to a JSON-safe dict."""
        entry = float(signal.entry)
        stop_loss = float(signal.stop_loss)
        take_profit_1 = float(signal.take_profit_1)
        take_profit_2 = float(signal.take_profit_2) if signal.take_profit_2 else None
        return {
            "id": str(signal.id),
            "pair_id": str(signal.pair_id),
            "symbol": signal.symbol,
            "market": signal.market,
            "direction": signal.direction,
            "timeframe": signal.timeframe,
            "confidence": signal.confidence,
            "setup_score": signal.setup_score,
            "pwin_tp1": float(signal.pwin_tp1) if signal.pwin_tp1 is not None else None,
            "pwin_tp2": float(signal.pwin_tp2) if signal.pwin_tp2 is not None else None,
            "ranking_score": float(signal.ranking_score) if signal.ranking_score is not None else None,
            "entry": entry,
            "entry_zone_low": float(signal.entry_zone_low) if signal.entry_zone_low is not None else None,
            "entry_zone_high": float(signal.entry_zone_high) if signal.entry_zone_high is not None else None,
            "entry_type": signal.entry_type,
            "stop_loss": stop_loss,
            "invalidation_price": float(signal.invalidation_price) if signal.invalidation_price is not None else None,
            "take_profit_1": take_profit_1,
            "take_profit_2": take_profit_2,
            "take_profit_3": float(signal.take_profit_3) if signal.take_profit_3 else None,
            "rr_ratio": float(signal.rr_ratio) if signal.rr_ratio else None,
            "rr_tp1": _calc_rr(entry, stop_loss, take_profit_1),
            "rr_tp2": _calc_rr(entry, stop_loss, take_profit_2),
            "raw_score": signal.raw_score,
            "max_possible_score": signal.max_possible_score,
            "status": signal.status,
            "score_breakdown": signal.score_breakdown,
            "ict_zones": signal.ict_zones,
            "mtf_analysis": signal.mtf_analysis,
            "fired_at": signal.fired_at.isoformat() if signal.fired_at else None,
            "valid_until": signal.valid_until.isoformat() if signal.valid_until else None,
            "expires_at": signal.expires_at.isoformat() if signal.expires_at else None,
            "closed_at": signal.closed_at.isoformat() if signal.closed_at else None,
            "close_price": float(signal.close_price) if signal.close_price is not None else None,
            "pnl_pct": float(signal.pnl_pct) if signal.pnl_pct is not None else None,
            "alert_sent": signal.alert_sent,
        }
