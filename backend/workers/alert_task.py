"""
Alert Task — PulseSignal Pro

Sends signal alerts to users via:
- Telegram (individual + VIP channels)
- Email (future)
- Webhook (future)
"""
import os
import json
import asyncio
from datetime import datetime, timezone
from loguru import logger

from workers.celery_app import app
from app.services.signal_cache_keys import make_signal_cache_key_from_member


TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_VIP_CHANNEL_ID = os.getenv('TELEGRAM_VIP_CHANNEL_ID', '')

# Direction emojis and colors
DIRECTION_EMOJI = {'LONG': '🟢', 'SHORT': '🔴'}
DIRECTION_LABEL = {'LONG': 'LONG ▲', 'SHORT': 'SHORT ▼'}

BAND_EMOJI = {
    'ULTRA_HIGH': '⚡',
    'HIGH': '✅',
    'MEDIUM': '🔶',
    'LOW': '⚠️',
}


def format_signal_message(signal: dict) -> str:
    """Format a professional Telegram signal message"""
    direction = signal.get('direction', 'LONG')
    probability_tp1 = signal.get('pwin_tp1', signal.get('confidence', 0))
    band = signal.get('confidence_band', 'HIGH')
    entry = signal.get('entry', 0)
    sl = signal.get('stop_loss', 0)
    tp1 = signal.get('take_profit_1', 0)
    tp2 = signal.get('take_profit_2', tp1)
    rr_tp1 = signal.get('rr_tp1')
    rr_tp2 = signal.get('rr_tp2')
    if rr_tp2 is None:
        rr_tp2 = signal.get('rr_ratio', 0)
    symbol = signal.get('symbol', '')
    timeframe = signal.get('timeframe', '')
    market = signal.get('market', 'crypto').upper()

    # Price formatting
    def fmt(p: float) -> str:
        if p >= 1000:
            return f"${p:,.2f}"
        elif p >= 1:
            return f"${p:.4f}"
        else:
            return f"${p:.6f}"

    # SL/TP percentage changes
    sl_pct = abs(entry - sl) / entry * 100 if entry > 0 else 0
    tp1_pct = abs(tp1 - entry) / entry * 100 if entry > 0 else 0
    tp2_pct = abs(tp2 - entry) / entry * 100 if entry > 0 else 0

    # Top confluences (max 5)
    confluences = signal.get('top_confluences', [])[:5]
    conf_text = '\n'.join(confluences) if confluences else '• Multiple indicators aligned'

    msg = f"""🚨 <b>PULSESIGNAL PRO — NEW SIGNAL</b>

{DIRECTION_EMOJI[direction]} <b>{symbol}</b> ({market}) — <b>{DIRECTION_LABEL[direction]}</b>
⏱ Timeframe: <b>{timeframe}</b>
{BAND_EMOJI.get(band, '📊')} P(TP1): <b>{probability_tp1}/100</b> — {band.replace('_', ' ')}

💰 <b>Entry:</b>     {fmt(entry)}
🛑 <b>Stop Loss:</b>  {fmt(sl)} (-{sl_pct:.1f}%)
🎯 <b>TP1:</b>        {fmt(tp1)} (+{tp1_pct:.1f}%)
🎯 <b>TP2:</b>        {fmt(tp2)} (+{tp2_pct:.1f}%)
⚖️ <b>R:R TP1:</b>    1:{float(rr_tp1 or 0):.1f}
⚖️ <b>R:R TP2:</b>    1:{float(rr_tp2 or 0):.1f}

<b>📊 Key Confluences:</b>
{conf_text}

⏰ {datetime.now(timezone.utc).strftime('%H:%M UTC')} | 🔗 signals.pulsetracker.net
━━━━━━━━━━━━━━━━━━━
<i>⚠️ Not financial advice. Manage your risk. DYOR.</i>"""

    return msg


async def _send_telegram_message(chat_id: str, text: str, parse_mode: str = 'HTML') -> bool:
    """Send a message via Telegram Bot API"""
    import httpx

    if not TELEGRAM_BOT_TOKEN:
        logger.warning("TELEGRAM_BOT_TOKEN not configured")
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(url, json={
                'chat_id': chat_id,
                'text': text,
                'parse_mode': parse_mode,
                'disable_web_page_preview': True,
            })

            if response.status_code == 200:
                return True
            else:
                logger.warning(f"Telegram API error {response.status_code}: {response.text}")
                return False

    except Exception as e:
        logger.error(f"Telegram send error: {e}")
        return False


def _run_async(coro):
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(coro)


@app.task(bind=True, name='workers.alert_task.send_signal_alerts',
          max_retries=3, default_retry_delay=60)
def send_signal_alerts(self, signal_id: str):
    """
    Send alerts for a new signal to all configured users.
    Also sends to VIP Telegram channel.
    """
    try:
        return _run_async(_send_signal_alerts_async(signal_id))
    except Exception as exc:
        logger.error(f"Alert task error for signal {signal_id}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'signal_id': signal_id, 'error': str(exc)}


async def _send_signal_alerts_async(signal_id: str) -> dict:
    """Async implementation of alert sending"""
    alerts_sent = 0

    try:
        # Get signal from Redis first (fast)
        import redis, json as json_lib
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

        # Try to find signal in Redis
        signal_data = None

        # 1) Fast path: canonical id-key cache
        raw_by_id = r.get(f'signal:id:{signal_id}')
        if raw_by_id:
            try:
                signal_data = json_lib.loads(raw_by_id)
            except Exception:
                signal_data = None

        # 2) Canonical symbol-key cache referenced by active_signals zset
        if not signal_data:
            active_members = r.zrange('active_signals', 0, -1)
            for member_raw in active_members:
                try:
                    member = (
                        member_raw.decode()
                        if isinstance(member_raw, (bytes, bytearray))
                        else str(member_raw)
                    )
                    payload = r.get(make_signal_cache_key_from_member(member))
                    if not payload:
                        continue
                    sig = json_lib.loads(payload)
                    if str(sig.get('id')) == str(signal_id):
                        signal_data = sig
                        break
                except Exception:
                    pass

        if not signal_data:
            # Fallback: get from DB
            try:
                from sqlalchemy import create_engine, text
                db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
                if db_url:
                    engine = create_engine(db_url)
                    with engine.connect() as conn:
                        row = conn.execute(text(
                            "SELECT * FROM signals WHERE id = :id"
                        ), {'id': signal_id}).fetchone()
                        if row:
                            signal_data = dict(row._mapping)
            except Exception as e:
                logger.warning(f"DB fetch failed for signal {signal_id}: {e}")

        if not signal_data:
            logger.warning(f"Signal {signal_id} not found for alerting")
            return {'signal_id': signal_id, 'alerts_sent': 0, 'error': 'Signal not found'}

        # ── Quality gate: only send ULTRA_HIGH signals ───────────────────
        # Prevents fake/manipulation entries and low-quality noise from
        # reaching users. Only signals with confidence_band == ULTRA_HIGH
        # and confidence >= 85 are dispatched to Telegram.
        confidence_band = signal_data.get('confidence_band', '')
        confidence = int(signal_data.get('pwin_tp1', signal_data.get('confidence', 0)) or 0)
        if confidence_band != 'ULTRA_HIGH' or confidence < 85:
            logger.info(
                f"[ALERT] Skipping {signal_data.get('symbol')} {signal_data.get('direction')} "
                f"— below ULTRA_HIGH threshold (band={confidence_band}, confidence={confidence})"
            )
            return {'signal_id': signal_id, 'alerts_sent': 0, 'skipped': True, 'reason': 'below_ultra_high'}

        message = format_signal_message(signal_data)

        # Send to VIP channel (already gated to ULTRA_HIGH above)
        if TELEGRAM_VIP_CHANNEL_ID:
            success = await _send_telegram_message(TELEGRAM_VIP_CHANNEL_ID, message)
            if success:
                alerts_sent += 1
                logger.info(f"[ALERT] VIP sent: {signal_data.get('symbol')} {signal_data.get('direction')} ({confidence}% ULTRA_HIGH)")

        # Send to individual users with matching alert configs
        try:
            from sqlalchemy import create_engine, text
            import json as json_lib

            db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
            if db_url:
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    # Find users with alert configs that match this signal
                    rows = conn.execute(text("""
                        SELECT u.telegram_chat_id, ac.min_confidence, ac.directions,
                               ac.timeframes, ac.markets, ac.pairs
                        FROM alert_configs ac
                        JOIN users u ON u.id = ac.user_id
                        WHERE ac.is_active = true
                          AND ac.channel = 'telegram'
                          AND u.telegram_chat_id IS NOT NULL
                          AND u.is_active = true
                          AND (u.plan = 'monthly' OR u.plan = 'yearly' OR u.plan = 'lifetime')
                          AND :confidence >= ac.min_confidence
                    """), {'confidence': confidence}).fetchall()

                    for row in rows:
                        try:
                            chat_id = str(row.telegram_chat_id)

                            # Check direction filter
                            directions = row.directions or ['LONG', 'SHORT']
                            if signal_data.get('direction') not in directions:
                                continue

                            # Check timeframe filter
                            timeframes = row.timeframes or ['1H', '4H']
                            if signal_data.get('timeframe') not in timeframes:
                                continue

                            # Check market filter
                            markets = row.markets or ['crypto']
                            if signal_data.get('market') not in markets:
                                continue

                            # Check pairs filter
                            if row.pairs:
                                if signal_data.get('symbol') not in row.pairs:
                                    continue

                            # Send alert
                            success = await _send_telegram_message(chat_id, message)
                            if success:
                                alerts_sent += 1

                        except Exception as e:
                            logger.warning(f"Alert send error for user: {e}")

                    # Mark signal as alert_sent
                    conn.execute(text(
                        "UPDATE signals SET alert_sent = true WHERE id = :id"
                    ), {'id': signal_id})
                    conn.commit()

        except Exception as e:
            logger.error(f"DB alert query error: {e}")

        logger.info(f"Signal {signal_id}: {alerts_sent} alerts sent")
        return {'signal_id': signal_id, 'alerts_sent': alerts_sent}

    except Exception as e:
        logger.error(f"Alert async error: {e}")
        return {'signal_id': signal_id, 'alerts_sent': 0, 'error': str(e)}


@app.task(name='workers.alert_task.send_custom_broadcast')
def send_custom_broadcast(message: str, min_plan: str = 'monthly',
                          chat_ids: list = None):
    """Send custom broadcast message to all premium users or specific chat_ids"""
    sent = 0

    if chat_ids:
        for chat_id in chat_ids:
            success = _run_async(_send_telegram_message(str(chat_id), message))
            if success:
                sent += 1
        return {'sent': sent}

    # Send to all premium users
    try:
        from sqlalchemy import create_engine, text
        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
        if db_url:
            engine = create_engine(db_url)
            with engine.connect() as conn:
                plan_filter = "'monthly', 'yearly', 'lifetime'" if min_plan == 'monthly' else "'yearly', 'lifetime'"
                rows = conn.execute(text(f"""
                    SELECT telegram_chat_id FROM users
                    WHERE is_active = true
                      AND telegram_chat_id IS NOT NULL
                      AND plan IN ({plan_filter})
                """)).fetchall()

                for row in rows:
                    success = _run_async(_send_telegram_message(
                        str(row.telegram_chat_id), message))
                    if success:
                        sent += 1
    except Exception as e:
        logger.error(f"Broadcast error: {e}")

    return {'sent': sent}
