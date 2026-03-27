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

        r = redis_lib.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        active_raw = r.zrange('signals:active', 0, -1)

        if not active_raw:
            return {'checked': 0, 'invalidated': 0}

        checked = 0
        invalidated = 0
        price_cache: dict[str, float] = {}

        for raw in active_raw:
            try:
                signal = json.loads(raw)
                symbol = signal.get('symbol', '')
                market = signal.get('market', 'crypto')
                direction = signal.get('direction', 'LONG')
                entry = float(signal.get('entry', 0))
                sl = float(signal.get('stop_loss', 0))
                tp1 = float(signal.get('take_profit_1', 0))

                if not symbol or entry <= 0 or sl <= 0:
                    continue

                # ── Get current price ────────────────────────────────────────
                if symbol not in price_cache:
                    try:
                        if market == 'crypto':
                            resp = httpx.get(
                                "https://fapi.binance.com/fapi/v1/ticker/price",
                                params={"symbol": symbol},
                                timeout=5,
                            )
                            price_cache[symbol] = float(resp.json().get("price", 0))
                        else:
                            # Forex: skip revalidation (no free real-time price endpoint)
                            price_cache[symbol] = 0.0
                    except Exception:
                        price_cache[symbol] = 0.0

                current_price = price_cache[symbol]
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
                    _invalidate_signal(r, signal, raw, invalidation_reason)
                    invalidated += 1

            except Exception as e:
                logger.warning(f"[REVALIDATION] Error checking signal: {e}")

        logger.info(f"[REVALIDATION] Checked {checked} signals, invalidated {invalidated}")
        return {'checked': checked, 'invalidated': invalidated}

    except Exception as e:
        logger.error(f"[REVALIDATION] Task error: {e}")
        return {'error': str(e)}


def _invalidate_signal(r, signal: dict, raw_bytes, reason: str):
    """Mark signal as invalidated in Redis and DB."""
    signal_id = signal.get('id')

    # Remove from Redis active sets
    try:
        r.zrem('signals:active', raw_bytes)
        r.zrem('active_signals', signal.get('symbol', ''))
        r.delete(f"signal:{signal.get('symbol', '')}")
    except Exception as e:
        logger.warning(f"[REVALIDATION] Redis cleanup error: {e}")

    # Update DB
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if db_url and signal_id:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                conn.execute(text("""
                    UPDATE signals
                    SET status = 'expired',
                        closed_at = NOW()
                    WHERE id = :id AND status = 'active'
                """), {"id": signal_id})
                conn.commit()
    except Exception as e:
        logger.warning(f"[REVALIDATION] DB update error: {e}")

    logger.info(f"[REVALIDATION] Signal {signal_id} invalidated: {reason}")
