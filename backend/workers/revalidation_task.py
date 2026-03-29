"""
Signal Revalidation Worker — PulseSignal Pro

Periodically re-checks active signals to see if the setup is still valid.
Marks signals as 'invalidated' if conditions weaken significantly.
"""
import os
import json
from datetime import datetime, timezone
from loguru import logger

from workers.celery_app import app
from app.services.signal_lifecycle import (
    CANONICAL_OPEN_STATUS_SQL,
    canonicalize_status,
)
from app.services.signal_cache_keys import (
    make_active_signal_member,
    make_legacy_signal_cache_key,
    make_signal_cache_key,
    make_signal_cache_key_from_member,
    parse_active_signal_member,
)
from workers.scanner_task import _has_twelvedata_key, _run_async


def _open_signal_key(symbol: str, direction: str, timeframe: str) -> str:
    return f"signal:open:{symbol}:{direction}:{timeframe}"


# ── Revalidation thresholds ────────────────────────────────────────────────
# If price moves this fraction toward SL, signal is considered weakening
SL_APPROACH_THRESHOLD = 0.70   # 70% of distance from entry to SL

# If entry was never touched (price stayed far from entry), signal is stale
ENTRY_MISS_THRESHOLD = 0.50    # 50% of TP1 distance away from entry in wrong direction


@app.task(name='workers.revalidation_task.revalidate_active_signals')
def revalidate_active_signals():
    """
    Re-check all active signals. For crypto signals, uses Binance price.
    Marks signals as 'invalidated' if setup degraded beyond thresholds.
    Logs reasoning for each state change.
    """
    try:
        import redis as redis_lib
        import httpx
        from engine.data_fetcher import ForexDataFetcher

        r = redis_lib.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        active_members = r.zrange('active_signals', 0, -1)

        if not active_members:
            return {'checked': 0, 'invalidated': 0}

        checked = 0
        invalidated = 0
        price_cache: dict[tuple[str, str], float] = {}
        forex_fetcher = ForexDataFetcher() if _has_twelvedata_key() else None

        for active_member in active_members:
            try:
                member_meta = parse_active_signal_member(active_member)
                cache_key = (
                    make_legacy_signal_cache_key(str(member_meta.get('symbol') or ''))
                    if member_meta.get('is_legacy')
                    else make_signal_cache_key_from_member(str(member_meta.get('member') or ''))
                )
                raw = r.get(cache_key)
                if not raw:
                    r.zrem('active_signals', active_member)
                    continue
                signal = json.loads(raw)
                symbol = signal.get('symbol', '')
                market = signal.get('market', 'crypto')
                direction = signal.get('direction', 'LONG')
                status = canonicalize_status(signal.get('status'))
                entry = float(signal.get('entry', 0))
                sl = float(signal.get('stop_loss', 0))
                tp1 = float(signal.get('take_profit_1', 0))

                if not symbol or entry <= 0 or sl <= 0 or status not in {'CREATED', 'ARMED', 'FILLED', 'TP1_REACHED'}:
                    continue

                # ── Get current price ────────────────────────────────────────
                cache_key = (str(market).lower(), symbol)
                if cache_key not in price_cache:
                    try:
                        if market == 'crypto':
                            resp = httpx.get(
                                "https://fapi.binance.com/fapi/v1/ticker/price",
                                params={"symbol": symbol},
                                timeout=5,
                            )
                            price_cache[cache_key] = float(resp.json().get("price", 0))
                        elif str(market).lower() == 'forex' and forex_fetcher is not None:
                            candles = _run_async(forex_fetcher.get_candles(symbol, '1m', limit=1))
                            latest = candles[-1] if candles else None
                            price_cache[cache_key] = float(getattr(latest, 'close', 0) or 0)
                        else:
                            price_cache[cache_key] = 0.0
                    except Exception:
                        price_cache[cache_key] = 0.0

                current_price = price_cache[cache_key]
                if current_price <= 0:
                    continue

                checked += 1

                # ── Check SL approach ────────────────────────────────────────
                risk_distance = abs(entry - sl)
                tp1_distance = abs(tp1 - entry) if tp1 > 0 else risk_distance * 2

                if direction == 'LONG':
                    # How far has price moved toward SL?
                    sl_move = entry - current_price
                    sl_approach_frac = sl_move / risk_distance if risk_distance > 0 else 0

                    # Has price completely missed the entry (moved far upward, entry invalid)?
                    entry_miss_frac = (current_price - entry) / tp1_distance if tp1_distance > 0 else 0

                elif direction == 'SHORT':
                    sl_move = current_price - entry
                    sl_approach_frac = sl_move / risk_distance if risk_distance > 0 else 0
                    entry_miss_frac = (entry - current_price) / tp1_distance if tp1_distance > 0 else 0
                else:
                    continue

                invalidation_reason = None

                if sl_approach_frac >= SL_APPROACH_THRESHOLD:
                    invalidation_reason = (
                        f"Price approached SL by {sl_approach_frac*100:.0f}% of risk distance "
                        f"(entry={entry:.5g}, current={current_price:.5g}, sl={sl:.5g})"
                    )

                if invalidation_reason:
                    _invalidate_signal(r, signal, invalidation_reason, active_member)
                    invalidated += 1

            except Exception as e:
                logger.warning(f"[REVALIDATION] Error checking signal: {e}")

        if forex_fetcher is not None:
            try:
                _run_async(forex_fetcher.close())
            except Exception:
                pass

        logger.info(f"[REVALIDATION] Checked {checked} signals, invalidated {invalidated}")
        return {'checked': checked, 'invalidated': invalidated}

    except Exception as e:
        logger.error(f"[REVALIDATION] Task error: {e}")
        return {'error': str(e)}


def _invalidate_signal(r, signal: dict, reason: str, active_member: str | None = None):
    """Mark signal as invalidated in Redis and DB."""
    signal_id = signal.get('id')
    symbol = str(signal.get('symbol', ''))
    direction = str(signal.get('direction', ''))
    timeframe = str(signal.get('timeframe', ''))
    canonical_member = make_active_signal_member(symbol, direction, timeframe, str(signal_id or ''))
    composite_key = make_signal_cache_key(symbol, direction, timeframe, str(signal_id or ''))

    # Remove from Redis active sets
    try:
        if active_member:
            r.zrem('active_signals', active_member)
        r.zrem('active_signals', canonical_member)
        r.delete(composite_key)
        r.delete(make_legacy_signal_cache_key(symbol))
        if signal_id:
            r.delete(f"signal:id:{signal_id}")
    except Exception as e:
        logger.warning(f"[REVALIDATION] Redis cleanup error: {e}")

    # Update DB
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if db_url and signal_id:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text(f"""
                    UPDATE signals
                    SET status = 'INVALIDATED',
                        closed_at = NOW()
                    WHERE id = :id AND status IN {CANONICAL_OPEN_STATUS_SQL}
                """), {"id": signal_id})
                conn.commit()
    except Exception as e:
        logger.warning(f"[REVALIDATION] DB update error: {e}")

    try:
        r.delete(
            _open_signal_key(
                signal.get('symbol', ''),
                signal.get('direction', ''),
                signal.get('timeframe', ''),
            )
        )
    except Exception:
        pass

    logger.info(f"[REVALIDATION] Signal {signal_id} invalidated: {reason}")
