"""
Analytics Task — PulseSignal Pro
Updates win rates, performance metrics.
"""
import os
from loguru import logger
from workers.celery_app import app


@app.task(name='workers.analytics_task.update_win_rates')
def update_win_rates():
    """Calculate and cache platform win rate statistics"""
    try:
        from sqlalchemy import create_engine, text
        import redis, json

        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if not db_url:
            return {'error': 'No database URL'}

        engine = create_engine(db_url)

        with engine.connect() as conn:
            # Overall stats
            total = conn.execute(text("SELECT COUNT(*) FROM signals WHERE status != 'active'")).scalar()
            wins = conn.execute(text("SELECT COUNT(*) FROM signals WHERE status IN ('tp1_hit', 'tp2_hit', 'tp3_hit')")).scalar()
            losses = conn.execute(text("SELECT COUNT(*) FROM signals WHERE status = 'sl_hit'")).scalar()

            win_rate = (wins / total * 100) if total > 0 else 0

            # By timeframe
            tf_stats_rows = conn.execute(text("""
                SELECT timeframe,
                       COUNT(*) as total,
                       SUM(CASE WHEN status IN ('tp1_hit','tp2_hit','tp3_hit') THEN 1 ELSE 0 END) as wins
                FROM signals
                WHERE status != 'active'
                GROUP BY timeframe
            """)).fetchall()

            tf_stats = {}
            for row in tf_stats_rows:
                tf_stats[row.timeframe] = {
                    'total': row.total,
                    'wins': row.wins,
                    'win_rate': round(row.wins / row.total * 100, 1) if row.total > 0 else 0,
                }

            # By direction
            dir_stats_rows = conn.execute(text("""
                SELECT direction,
                       COUNT(*) as total,
                       SUM(CASE WHEN status IN ('tp1_hit','tp2_hit','tp3_hit') THEN 1 ELSE 0 END) as wins
                FROM signals
                WHERE status != 'active'
                GROUP BY direction
            """)).fetchall()

            dir_stats = {}
            for row in dir_stats_rows:
                dir_stats[row.direction] = {
                    'total': row.total,
                    'wins': row.wins,
                    'win_rate': round(row.wins / row.total * 100, 1) if row.total > 0 else 0,
                }

            # Recent 7 days
            recent_total = conn.execute(text("""
                SELECT COUNT(*) FROM signals
                WHERE fired_at > NOW() - INTERVAL '7 days'
                  AND status != 'active'
            """)).scalar()

            recent_wins = conn.execute(text("""
                SELECT COUNT(*) FROM signals
                WHERE fired_at > NOW() - INTERVAL '7 days'
                  AND status IN ('tp1_hit','tp2_hit','tp3_hit')
            """)).scalar()

        stats = {
            'total_signals': total or 0,
            'total_wins': wins or 0,
            'total_losses': losses or 0,
            'win_rate': round(win_rate, 1),
            'by_timeframe': tf_stats,
            'by_direction': dir_stats,
            'last_7_days': {
                'total': recent_total or 0,
                'wins': recent_wins or 0,
                'win_rate': round((recent_wins / recent_total * 100) if recent_total else 0, 1),
            },
            'updated_at': __import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
        }

        # Cache in Redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.set('analytics:win_rates', json.dumps(stats), ex=3600)

        logger.info(f"Analytics updated: {win_rate:.1f}% win rate on {total} signals")
        return stats

    except Exception as e:
        logger.error(f"update_win_rates error: {e}")
        return {'error': str(e)}
