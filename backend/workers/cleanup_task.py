"""
Cleanup Task — PulseSignal Pro
Removes old signals, cleans Redis, manages DB size.
"""
import os
from datetime import datetime, timezone, timedelta
from loguru import logger

from workers.celery_app import app


@app.task(name='workers.cleanup_task.cleanup_old_signals')
def cleanup_old_signals(days_to_keep: int = 30):
    """Remove signals older than `days_to_keep` days"""
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if not db_url:
            return {'error': 'No database URL'}

        cutoff = datetime.now(timezone.utc) - timedelta(days=days_to_keep)
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM signals
                WHERE fired_at < :cutoff
                  AND status IN ('sl_hit', 'tp2_hit', 'expired')
                RETURNING id
            """), {'cutoff': cutoff})
            deleted = result.rowcount
            conn.commit()

        logger.info(f"Cleanup: deleted {deleted} old signals (older than {days_to_keep} days)")

        # Clean expired entries from Redis active signals set
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        # Remove entries with score < 0 (shouldn't happen, but safety)
        r.zremrangebyscore('signals:active', '-inf', 0)

        return {'deleted': deleted, 'cutoff': cutoff.isoformat()}

    except Exception as e:
        logger.error(f"Cleanup error: {e}")
        return {'error': str(e)}


@app.task(name='workers.cleanup_task.expire_old_signals')
def expire_old_signals():
    """Mark signals as expired if their expires_at has passed"""
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if not db_url:
            return

        engine = create_engine(db_url)
        with engine.connect() as conn:
            result = conn.execute(text("""
                UPDATE signals
                SET status = 'expired'
                WHERE status = 'active'
                  AND expires_at < NOW()
            """))
            expired = result.rowcount
            conn.commit()

        if expired > 0:
            logger.info(f"Expired {expired} old signals")

        return {'expired': expired}

    except Exception as e:
        logger.error(f"expire_old_signals error: {e}")
        return {'error': str(e)}


@app.task(name='workers.cleanup_task.purge_low_quality_signals')
def purge_low_quality_signals(min_confidence: int = 75):
    """
    One-time (and periodic) purge:
    1. Remove signals below min_confidence from Redis active sets
    2. Mark them expired in PostgreSQL
    3. Deduplicate Redis: keep only highest-confidence signal per symbol+direction+timeframe
    """
    import json
    import redis as redis_lib

    r = redis_lib.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    purged_redis = 0
    expired_db = 0

    # ── Step 1: Remove low-confidence entries from signals:active ──────────
    all_entries = r.zrangebyscore('signals:active', '-inf', min_confidence - 1, withscores=True)
    if all_entries:
        r.zremrangebyscore('signals:active', '-inf', min_confidence - 1)
        purged_redis += len(all_entries)
        logger.info(f"[PURGE] Removed {len(all_entries)} low-confidence entries from Redis")

    # ── Step 2: Deduplicate signals:active — keep best per symbol+direction+timeframe
    remaining = r.zrange('signals:active', 0, -1, withscores=True)
    seen: dict[str, tuple[bytes, float]] = {}  # key → (raw, score)
    to_remove = []
    for raw, score in remaining:
        try:
            sig = json.loads(raw)
            dedup_key = f"{sig.get('symbol')}:{sig.get('direction')}:{sig.get('timeframe')}"
            if dedup_key in seen:
                # Keep higher confidence, remove lower
                existing_score = seen[dedup_key][1]
                if score >= existing_score:
                    to_remove.append(seen[dedup_key][0])
                    seen[dedup_key] = (raw, score)
                else:
                    to_remove.append(raw)
            else:
                seen[dedup_key] = (raw, score)
        except Exception:
            pass

    if to_remove:
        r.zrem('signals:active', *to_remove)
        purged_redis += len(to_remove)
        logger.info(f"[PURGE] Removed {len(to_remove)} duplicate Redis entries")

    # ── Step 3: Sync active_signals set to match signals:active ───────────
    # Rebuild active_signals (symbol→confidence) from the deduped set
    r.delete('active_signals')
    current = r.zrange('signals:active', 0, -1, withscores=True)
    if current:
        pipe = r.pipeline()
        for raw, score in current:
            try:
                sig = json.loads(raw)
                symbol = sig.get('symbol')
                if symbol:
                    pipe.zadd('active_signals', {symbol: score})
                    pipe.set(f'signal:{symbol}', raw, ex=86400)
            except Exception:
                pass
        pipe.execute()

    # ── Step 4: Expire low-confidence signals in PostgreSQL ────────────────
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if db_url:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text("""
                    UPDATE signals
                    SET status = 'expired', closed_at = NOW()
                    WHERE status = 'active'
                      AND confidence < :min_confidence
                """), {'min_confidence': min_confidence})
                expired_db = result.rowcount
                conn.commit()
            logger.info(f"[PURGE] Marked {expired_db} low-confidence DB signals as expired")
    except Exception as e:
        logger.error(f"[PURGE] DB expire error: {e}")

    return {
        'purged_redis': purged_redis,
        'expired_db': expired_db,
        'min_confidence': min_confidence,
    }
