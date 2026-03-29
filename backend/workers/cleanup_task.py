"""
Cleanup Task — PulseSignal Pro
Removes old signals, cleans Redis, manages DB size.
"""
import os
import json
from datetime import datetime, timezone, timedelta
from loguru import logger

from workers.celery_app import app
from app.services.signal_cache_keys import (
    make_active_signal_member,
    make_legacy_signal_cache_key,
    make_signal_cache_key,
    make_signal_cache_key_from_member,
    parse_active_signal_member,
)
from app.services.signal_lifecycle import (
    CANONICAL_OPEN_STATUS_SQL,
    FINAL_STATUS_SQL,
)


def _open_signal_key(symbol: str, direction: str, timeframe: str) -> str:
    return f"signal:open:{symbol}:{direction}:{timeframe}"


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
            result = conn.execute(text(f"""
                DELETE FROM signals
                WHERE fired_at < :cutoff
                  AND status IN {FINAL_STATUS_SQL}
                RETURNING id
            """), {'cutoff': cutoff})
            deleted = result.rowcount
            conn.commit()

        logger.info(f"Cleanup: deleted {deleted} old signals (older than {days_to_keep} days)")

        # Clean expired entries from Redis active signals set
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        # Remove entries with score < 0 (shouldn't happen, but safety)
        r.zremrangebyscore('active_signals', '-inf', 0)

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
        expired_rows = []
        with engine.connect() as conn:
            result = conn.execute(text(f"""
                UPDATE signals
                SET status = 'EXPIRED', closed_at = NOW()
                WHERE status IN {CANONICAL_OPEN_STATUS_SQL}
                  AND expires_at < NOW()
                RETURNING id, symbol, direction, timeframe
            """))
            expired_rows = result.fetchall()
            expired = len(expired_rows)
            conn.commit()

        if expired_rows:
            import redis

            r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
            pipe = r.pipeline()
            for row in expired_rows:
                signal_id, symbol, direction, timeframe = row
                active_member = make_active_signal_member(symbol, direction, timeframe, str(signal_id))
                pipe.zrem('active_signals', active_member)
                pipe.delete(make_signal_cache_key(symbol, direction, timeframe, str(signal_id)))
                pipe.delete(make_legacy_signal_cache_key(symbol))
                pipe.delete(f'signal:id:{signal_id}')
                pipe.delete(_open_signal_key(symbol, direction, timeframe))
            pipe.execute()

        if expired > 0:
            logger.info(f"Expired {expired} old signals")

        return {'expired': expired}

    except Exception as e:
        logger.error(f"expire_old_signals error: {e}")
        return {'error': str(e)}


@app.task(name='workers.cleanup_task.delete_stale_unverified_users')
def delete_stale_unverified_users(days: int = 7):
    """
    Delete accounts that never verified their email within `days`.
    Keeps owner/superadmin accounts as a safety guard.
    """
    try:
        from sqlalchemy import create_engine, text

        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if not db_url:
            return {'error': 'No database URL'}

        cutoff = datetime.now(timezone.utc) - timedelta(days=days)
        engine = create_engine(db_url)

        with engine.connect() as conn:
            result = conn.execute(text("""
                DELETE FROM users
                WHERE is_verified = false
                  AND created_at < :cutoff
                  AND role NOT IN ('owner', 'superadmin')
                RETURNING id
            """), {'cutoff': cutoff})
            deleted = result.rowcount
            conn.commit()

        if deleted:
            logger.info(
                f"[CLEANUP] Deleted {deleted} unverified users older than {days} days"
            )
        return {'deleted': deleted, 'cutoff': cutoff.isoformat(), 'days': days}
    except Exception as e:
        logger.error(f"delete_stale_unverified_users error: {e}")
        return {'error': str(e)}


@app.task(name='workers.cleanup_task.purge_low_quality_signals')
def purge_low_quality_signals(min_confidence: int | None = None):
    """
    One-time (and periodic) purge:
    1. Remove signals below min_confidence from Redis active sets
    2. Mark them expired in PostgreSQL
    3. Deduplicate Redis: keep only highest-confidence signal per symbol+direction+timeframe
    """
    import redis as redis_lib

    r = redis_lib.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
    if min_confidence is None:
        try:
            raw_cfg = r.get('admin:system_config')
            if raw_cfg:
                cfg = json.loads(raw_cfg)
                min_confidence = int(cfg.get('min_signal_confidence', 75) or 75)
            else:
                min_confidence = 75
        except Exception:
            min_confidence = 75
    min_confidence = max(75, min(100, int(min_confidence)))
    purged_redis = 0
    expired_db = 0

    # ── Step 1: Remove low-confidence entries from canonical active cache ──
    active_members = r.zrange('active_signals', 0, -1)
    if active_members:
        pipe = r.pipeline()
        for active_member in active_members:
            member_meta = parse_active_signal_member(active_member)
            cache_key = (
                make_legacy_signal_cache_key(str(member_meta.get('symbol') or ''))
                if member_meta.get('is_legacy')
                else make_signal_cache_key_from_member(str(member_meta.get('member') or ''))
            )
            raw = r.get(cache_key)
            if not raw:
                pipe.zrem('active_signals', active_member)
                continue
            try:
                sig = json.loads(raw)
            except Exception:
                pipe.zrem('active_signals', active_member)
                pipe.delete(cache_key)
                continue
            confidence = int(sig.get('confidence', 0) or 0)
            if confidence < min_confidence:
                canonical_member = make_active_signal_member(
                    str(sig.get('symbol', '')),
                    str(sig.get('direction', '')),
                    str(sig.get('timeframe', '')),
                    str(sig.get('id', '')),
                )
                pipe.zrem('active_signals', active_member)
                pipe.zrem('active_signals', canonical_member)
                pipe.delete(cache_key)
                pipe.delete(
                    make_signal_cache_key(
                        str(sig.get('symbol', '')),
                        str(sig.get('direction', '')),
                        str(sig.get('timeframe', '')),
                        str(sig.get('id', '')),
                    )
                )
                pipe.delete(make_legacy_signal_cache_key(str(sig.get('symbol', ''))))
                signal_id = sig.get('id')
                if signal_id:
                    pipe.delete(f'signal:id:{signal_id}')
                pipe.delete(
                    _open_signal_key(
                        str(sig.get('symbol', '')),
                        str(sig.get('direction', '')),
                        str(sig.get('timeframe', '')),
                    )
                )
                purged_redis += 1
        pipe.execute()

    # ── Step 4: Expire low-confidence signals in PostgreSQL ────────────────
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if db_url:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                result = conn.execute(text(f"""
                    UPDATE signals
                    SET status = 'EXPIRED', closed_at = NOW()
                    WHERE status IN {CANONICAL_OPEN_STATUS_SQL}
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
