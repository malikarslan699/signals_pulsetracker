"""
Celery Application — PulseSignal Pro

Workers:
- scanner_task: Scan all pairs every 10 minutes
- alert_task: Send signal alerts to users
- cleanup_task: Clean up old signals
- analytics_task: Update win rates and stats
"""
from celery import Celery
from celery.schedules import crontab
import os
from dotenv import load_dotenv

load_dotenv()

REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')

app = Celery(
    'pulsesignal',
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=[
        'workers.scanner_task',
        'workers.alert_task',
        'workers.cleanup_task',
        'workers.analytics_task',
        'workers.revalidation_task',
    ]
)

app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=300,   # 5 min soft limit
    task_time_limit=600,         # 10 min hard limit
    result_expires=3600,         # results expire after 1 hour
    task_compression='gzip',
    worker_max_tasks_per_child=100,  # restart worker after 100 tasks (memory management)
)

# Beat schedule (periodic tasks)
app.conf.beat_schedule = {
    # Crypto scan every 10 minutes
    'scan-crypto-every-10min': {
        'task': 'workers.scanner_task.scan_market',
        'schedule': crontab(minute='*/10'),
        'kwargs': {'market': 'crypto'},
        'options': {'queue': 'scanner', 'priority': 5},
    },
    # Forex scan every 10 minutes (offset by 5 min to spread load)
    'scan-forex-every-10min': {
        'task': 'workers.scanner_task.scan_market',
        'schedule': crontab(minute='5-55/10'),
        'kwargs': {'market': 'forex'},
        'options': {'queue': 'scanner', 'priority': 4},
    },
    # Update signal statuses (TP/SL hit check) every 5 minutes
    'update-signal-statuses': {
        'task': 'workers.scanner_task.update_signal_statuses',
        'schedule': crontab(minute='*/5'),
        'options': {'queue': 'default', 'priority': 3},
    },
    # Cleanup old signals every 6 hours
    'cleanup-old-signals': {
        'task': 'workers.cleanup_task.cleanup_old_signals',
        'schedule': crontab(hour='*/6'),
        'options': {'queue': 'default', 'priority': 1},
    },
    # Delete unverified accounts older than 7 days (daily)
    'delete-stale-unverified-users': {
        'task': 'workers.cleanup_task.delete_stale_unverified_users',
        'schedule': crontab(hour=3, minute=0),
        'kwargs': {'days': 7},
        'options': {'queue': 'default', 'priority': 1},
    },
    # Purge low-quality signals from Redis + DB every 30 minutes
    'purge-low-quality-signals': {
        'task': 'workers.cleanup_task.purge_low_quality_signals',
        'schedule': crontab(minute='*/30'),
        'options': {'queue': 'default', 'priority': 2},
    },
    # Revalidate active signals every 15 minutes
    'revalidate-active-signals': {
        'task': 'workers.revalidation_task.revalidate_active_signals',
        'schedule': crontab(minute='*/15'),
        'options': {'queue': 'default', 'priority': 3},
    },
    # Update win rate analytics every hour
    'update-analytics': {
        'task': 'workers.analytics_task.update_win_rates',
        'schedule': crontab(hour='*/1'),
        'options': {'queue': 'default', 'priority': 2},
    },
    # Refresh pair health and auto-filtering every hour
    'refresh-pair-health': {
        'task': 'workers.analytics_task.refresh_pair_health',
        'schedule': crontab(hour='*/1', minute=15),
        'options': {'queue': 'default', 'priority': 2},
    },
    # Health check every minute
    'health-check': {
        'task': 'workers.scanner_task.health_check',
        'schedule': crontab(minute='*/1'),
        'options': {'queue': 'default', 'priority': 1},
    },
}

# Queue routing
app.conf.task_routes = {
    'workers.scanner_task.scan_market': {'queue': 'scanner'},
    'workers.scanner_task.scan_symbol': {'queue': 'scanner'},
    'workers.alert_task.*': {'queue': 'alerts'},
    'workers.cleanup_task.*': {'queue': 'default'},
    'workers.analytics_task.*': {'queue': 'default'},
}

if __name__ == '__main__':
    app.start()
