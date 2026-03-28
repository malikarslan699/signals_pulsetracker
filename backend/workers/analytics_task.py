"""
Analytics Task — PulseSignal Pro
Updates win rates, performance metrics.
"""
import os
from datetime import datetime, timezone

from loguru import logger
from workers.celery_app import app

from app.services.pair_health_service import classify_pair_health

OPEN_SQL = "('active','CREATED','ARMED','FILLED')"
WIN_SQL = "('tp1_hit','tp2_hit','tp3_hit','TP1_REACHED','TP2_REACHED')"
LOSS_SQL = "('sl_hit','STOPPED')"


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
            total = conn.execute(text(f"SELECT COUNT(*) FROM signals WHERE status NOT IN {OPEN_SQL}")).scalar()
            wins = conn.execute(text(f"SELECT COUNT(*) FROM signals WHERE status IN {WIN_SQL}")).scalar()
            losses = conn.execute(text(f"SELECT COUNT(*) FROM signals WHERE status IN {LOSS_SQL}")).scalar()

            win_rate = (wins / total * 100) if total > 0 else 0

            # By timeframe
            tf_stats_rows = conn.execute(text(f"""
                SELECT timeframe,
                       COUNT(*) as total,
                       SUM(CASE WHEN status IN {WIN_SQL} THEN 1 ELSE 0 END) as wins
                FROM signals
                WHERE status NOT IN {OPEN_SQL}
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
            dir_stats_rows = conn.execute(text(f"""
                SELECT direction,
                       COUNT(*) as total,
                       SUM(CASE WHEN status IN {WIN_SQL} THEN 1 ELSE 0 END) as wins
                FROM signals
                WHERE status NOT IN {OPEN_SQL}
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
            recent_total = conn.execute(text(f"""
                SELECT COUNT(*) FROM signals
                WHERE fired_at > NOW() - INTERVAL '7 days'
                  AND status NOT IN {OPEN_SQL}
            """)).scalar()

            recent_wins = conn.execute(text(f"""
                SELECT COUNT(*) FROM signals
                WHERE fired_at > NOW() - INTERVAL '7 days'
                  AND status IN {WIN_SQL}
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
            'updated_at': datetime.now(timezone.utc).isoformat(),
        }

        # Cache in Redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.set('analytics:win_rates', json.dumps(stats), ex=3600)

        logger.info(f"Analytics updated: {win_rate:.1f}% win rate on {total} signals")
        return stats

    except Exception as e:
        logger.error(f"update_win_rates error: {e}")
        return {'error': str(e)}


@app.task(name='workers.analytics_task.refresh_pair_health')
def refresh_pair_health(days: int = 45):
    """Update pair health, auto-disable noisy pairs, and cache health analytics."""
    try:
        from sqlalchemy import create_engine, text
        import redis
        import json

        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if not db_url:
            return {'error': 'No database URL'}

        engine = create_engine(db_url)
        cached_rows: list[dict] = []

        with engine.begin() as conn:
            rows = conn.execute(
                text(
                    f"""
                    SELECT
                        p.symbol,
                        p.market,
                        p.manual_override,
                        COUNT(s.id) FILTER (WHERE s.status NOT IN {OPEN_SQL}) AS total_closed,
                        COUNT(s.id) FILTER (WHERE s.status IN {WIN_SQL}) AS wins,
                        COUNT(s.id) FILTER (WHERE s.status IN {LOSS_SQL}) AS losses,
                        ROUND(AVG(s.pwin_tp1)::numeric, 2) AS avg_pwin_tp1,
                        ROUND(AVG(s.pnl_pct)::numeric, 2) AS avg_pnl
                    FROM pairs p
                    LEFT JOIN signals s
                      ON s.symbol = p.symbol
                     AND s.fired_at >= NOW() - (:days || ' days')::interval
                    GROUP BY p.symbol, p.market, p.manual_override
                    ORDER BY p.symbol
                    """
                ),
                {"days": str(int(days))},
            ).mappings().all()

            for row in rows:
                metrics = classify_pair_health(
                    total_closed=int(row["total_closed"] or 0),
                    wins=int(row["wins"] or 0),
                    losses=int(row["losses"] or 0),
                    avg_pwin_tp1=float(row["avg_pwin_tp1"] or 0),
                    avg_pnl=float(row["avg_pnl"] or 0),
                )
                conn.execute(
                    text(
                        """
                        UPDATE pairs
                        SET auto_disabled = :auto_disabled,
                            health_score = :health_score,
                            health_status = :health_status,
                            disable_reason = :disable_reason,
                            last_health_check_at = NOW()
                        WHERE symbol = :symbol
                        """
                    ),
                    {
                        "symbol": row["symbol"],
                        "auto_disabled": metrics["auto_disabled"],
                        "health_score": metrics["health_score"],
                        "health_status": metrics["health_status"],
                        "disable_reason": metrics["disable_reason"],
                    },
                )

                cached_rows.append(
                    {
                        "symbol": row["symbol"],
                        "market": row["market"],
                        "manual_override": bool(row["manual_override"]),
                        "total_closed": int(row["total_closed"] or 0),
                        "wins": int(row["wins"] or 0),
                        "losses": int(row["losses"] or 0),
                        "avg_pwin_tp1": float(row["avg_pwin_tp1"] or 0),
                        "avg_pnl": float(row["avg_pnl"] or 0),
                        **metrics,
                    }
                )

        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.set(
            'analytics:pair_health',
            json.dumps(
                {
                    "days": int(days),
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                    "pairs": cached_rows,
                }
            ),
            ex=3600,
        )

        disabled_count = len([row for row in cached_rows if row["auto_disabled"]])
        logger.info(f"Pair health refreshed for {len(cached_rows)} pairs ({disabled_count} auto-disabled)")
        return {
            "pairs": len(cached_rows),
            "auto_disabled": disabled_count,
            "days": int(days),
        }
    except Exception as e:
        logger.error(f"refresh_pair_health error: {e}")
        return {'error': str(e)}
