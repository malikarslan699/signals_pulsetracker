"""
Scanner Task — PulseSignal Pro

Scans all active trading pairs, runs indicator engine,
generates signals, stores in DB and Redis.
"""
import asyncio
import time
import logging
import json
from datetime import datetime, timezone, timedelta
from typing import Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import os
import sys

# Add backend root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from workers.celery_app import app
from loguru import logger


# ─── CRYPTO PAIRS (Top 100+ Binance Futures) ─────────────────────────────────
CRYPTO_PAIRS = [
    'BTCUSDT', 'ETHUSDT', 'BNBUSDT', 'SOLUSDT', 'XRPUSDT',
    'ADAUSDT', 'DOGEUSDT', 'AVAXUSDT', 'DOTUSDT', 'MATICUSDT',
    'LINKUSDT', 'UNIUSDT', 'LTCUSDT', 'ATOMUSDT', 'NEARUSDT',
    'FTMUSDT', 'SANDUSDT', 'MANAUSDT', 'AXSUSDT', 'AAVEUSDT',
    'APTUSDT', 'OPUSDT', 'ARBUSDT', 'SUIUSDT', 'INJUSDT',
    'SEIUSDT', 'TIAUSDT', 'JUPUSDT', 'WIFUSDT', 'BONKUSDT',
    'PEPEUSDT', 'FLOKIUSDT', 'SHIBUSDT', 'GALAUSDT', 'APEUSDT',
    'COMPUSDT', 'MKRUSDT', 'SNXUSDT', 'CRVUSDT', 'YFIUSDT',
    'LDOUSDT', 'STETHUSDT', 'RPLUSDT', 'FXSUSDT', 'FRAXUSDT',
    '1000SHIBUSDT', '1000BONKUSDT', '1000PEPEUSDT', '1000FLOKIUSDT',
    'WBTCUSDT', 'HBARUSDT', 'ALGOUSDT', 'XTZUSDT', 'EOSUSDT',
    'ZECUSDT', 'DASHUSDT', 'XMRUSDT', 'BCHUSDT', 'ETCUSDT',
    'TRXUSDT', 'XLMUSDT', 'VETUSDT', 'ICPUSDT', 'FILUSDT',
    'THETAUSDT', 'EGLDUSDT', 'FLOWUSDT', 'STXUSDT', 'CFXUSDT',
    'ENSUSDT', 'GMTUSDT', 'DYDXUSDT', 'GRTUSDT', 'COTIUSDT',
    'WOOUSDT', 'SPELLUSDT', 'ACHUSDT', 'IMXUSDT', 'LOOMUSDT',
    'CELOUSDT', 'ZRXUSDT', 'BANDUSDT', 'STORJUSDT', 'ANKRUSDT',
    'OCEANUSDT', 'FETUSDT', 'AGIXUSDT', 'RNDRUSDT', 'WLDUSDT',
    'CYBERUSDT', 'ARKMUSDT', 'PIXELUSDT', 'PORTALUSDT', 'STRAXUSDT',
    'BLURUSDT', 'NFPUSDT', 'AIUSDT', 'XAIUSDT', 'MANTAUSDT',
    'ALTUSDT', 'JUPUSDT', 'DYMUSDT', 'PYTHUSDT', 'STRKUSDT',
]

# ─── FOREX PAIRS ─────────────────────────────────────────────────────────────
FOREX_PAIRS = [
    'XAUUSD',   # Gold
    'XAGUSD',   # Silver
    'USOIL',    # WTI Crude Oil
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',
    'EURGBP', 'EURJPY', 'GBPJPY', 'AUDJPY', 'CADJPY', 'CHFJPY',
    'EURCAD', 'EURAUD', 'GBPAUD', 'GBPCAD', 'AUDCAD', 'AUDNZD',
    'GBPNZD', 'EURNZD',
    'US100', 'US500', 'US30',  # Indices
    'DE40', 'UK100', 'JP225',
]

SCAN_TIMEFRAMES = ['15m', '1H', '4H']
ALLOWED_SCAN_TIMEFRAMES = {'5m', '15m', '1H', '4H', '1D'}
MAX_SIGNALS_PER_SYMBOL_SCAN = 1


def _open_signal_key(symbol: str, direction: str, timeframe: str) -> str:
    return f"signal:open:{symbol}:{direction}:{timeframe}"


def _json_default(value):
    """Convert common non-JSON-native numeric types (e.g. numpy scalars)."""
    try:
        import numpy as np  # local import to avoid hard dependency at module import
        if isinstance(value, np.generic):
            return value.item()
    except Exception:
        pass

    if isinstance(value, (datetime,)):
        return value.isoformat()

    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _run_async(coro):
    """Run async coroutine in sync context"""
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


def _load_runtime_config() -> dict:
    try:
        import redis

        r = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True,
        )
        raw = r.get('admin:system_config')
        if not raw:
            return {}
        payload = json.loads(raw)
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _get_scan_min_confidence(default: int = 75) -> int:
    """
    Read scanner min confidence from runtime system config (Redis).
    Falls back to `default` on any error.
    """
    try:
        payload = _load_runtime_config()
        value = int(payload.get('min_signal_confidence', default) or default)
        return max(75, min(100, value))
    except Exception:
        return default


def _get_scan_timeframes(default: Optional[list[str]] = None) -> list[str]:
    if default is None:
        default = list(SCAN_TIMEFRAMES)
    payload = _load_runtime_config()
    raw = payload.get('scanner_timeframes')
    if not isinstance(raw, list):
        return list(default)
    cleaned: list[str] = []
    for tf in raw:
        value = str(tf or '').strip()
        if value in ALLOWED_SCAN_TIMEFRAMES and value not in cleaned:
            cleaned.append(value)
    return cleaned or list(default)


def _get_overtrading_limits() -> dict[str, int]:
    payload = _load_runtime_config()
    try:
        per_symbol = int(payload.get('per_symbol_daily_signal_limit', 2) or 0)
    except Exception:
        per_symbol = 2
    try:
        global_daily = int(payload.get('global_daily_signal_limit', 25) or 0)
    except Exception:
        global_daily = 25
    try:
        cooldown_minutes = int(payload.get('repeated_signal_cooldown_minutes', 180) or 0)
    except Exception:
        cooldown_minutes = 180
    return {
        'per_symbol_daily_signal_limit': max(0, per_symbol),
        'global_daily_signal_limit': max(0, global_daily),
        'repeated_signal_cooldown_minutes': max(0, cooldown_minutes),
    }


def _filter_pairs_for_scanning(market: str, pairs: list[str]) -> tuple[list[str], list[str]]:
    db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
    if not db_url or not pairs:
        return list(pairs), []

    try:
        from sqlalchemy import create_engine, text

        engine = create_engine(db_url)
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    """
                    SELECT symbol, is_active, auto_disabled, manual_override
                    FROM pairs
                    WHERE market = :market
                    """
                ),
                {"market": market},
            ).mappings().all()
    except Exception as exc:
        logger.warning(f"[SCANNER] Could not load pair scan policy: {exc}")
        return list(pairs), []

    by_symbol = {str(row["symbol"]).upper(): row for row in rows}
    allowed: list[str] = []
    blocked: list[str] = []
    for symbol in pairs:
        row = by_symbol.get(symbol.upper())
        if not row:
            allowed.append(symbol)
            continue
        if not bool(row.get("is_active", True)):
            blocked.append(symbol)
            continue
        if bool(row.get("auto_disabled")) and not bool(row.get("manual_override")):
            blocked.append(symbol)
            continue
        allowed.append(symbol)
    return allowed, blocked


def _has_twelvedata_key() -> bool:
    """
    Return True if TwelveData API key is configured (env or runtime config).
    """
    env_key = (os.getenv("TWELVEDATA_API_KEY", "") or "").strip()
    if env_key:
        return True
    try:
        payload = _load_runtime_config()
        key = (
            payload.get("integrations", {})
            .get("twelvedata_api_key", "")
        )
        return bool(str(key or "").strip())
    except Exception:
        return False


def _seconds_until_utc_day_end() -> int:
    now = datetime.now(timezone.utc)
    tomorrow = (now + timedelta(days=1)).replace(hour=0, minute=0, second=0, microsecond=0)
    return max(60, int((tomorrow - now).total_seconds()) + 300)


def _reserve_daily_signal_slot(r, symbol: str, limits: dict[str, int]) -> tuple[bool, dict[str, str] | None]:
    day_key = datetime.now(timezone.utc).strftime('%Y%m%d')
    global_key = f'signals:daily:{day_key}'
    symbol_key = f'signals:daily:{day_key}:{symbol}'
    ttl = _seconds_until_utc_day_end()
    script = """
local global_key = KEYS[1]
local symbol_key = KEYS[2]
local global_limit = tonumber(ARGV[1])
local symbol_limit = tonumber(ARGV[2])
local ttl = tonumber(ARGV[3])
local global_count = tonumber(redis.call('GET', global_key) or '0')
local symbol_count = tonumber(redis.call('GET', symbol_key) or '0')
if global_limit > 0 and global_count >= global_limit then
  return 0
end
if symbol_limit > 0 and symbol_count >= symbol_limit then
  return 0
end
global_count = redis.call('INCR', global_key)
if global_count == 1 then
  redis.call('EXPIRE', global_key, ttl)
end
symbol_count = redis.call('INCR', symbol_key)
if symbol_count == 1 then
  redis.call('EXPIRE', symbol_key, ttl)
end
return 1
"""
    allowed = r.eval(
        script,
        2,
        global_key,
        symbol_key,
        int(limits.get('global_daily_signal_limit', 0)),
        int(limits.get('per_symbol_daily_signal_limit', 0)),
        ttl,
    )
    if int(allowed or 0) != 1:
        return False, None
    return True, {'global_key': global_key, 'symbol_key': symbol_key}


def _release_daily_signal_slot(r, reservation: Optional[dict[str, str]]) -> None:
    if not reservation:
        return
    try:
        pipe = r.pipeline()
        pipe.decr(reservation['global_key'])
        pipe.decr(reservation['symbol_key'])
        pipe.execute()
    except Exception:
        pass


def _calc_rr(entry: float, stop_loss: float, take_profit: Optional[float]) -> Optional[float]:
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


def _update_scanner_progress(signals_added: int = 0) -> None:
    """Increment scanner progress counters in Redis."""
    try:
        import redis

        r = redis.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True,
        )
        status = (r.hget('scanner:status', 'status') or '').strip().lower()
        if status != 'running':
            return

        updated = r.hincrby('scanner:status', 'pairs_done', 1)
        if signals_added > 0:
            r.hincrby('scanner:status', 'signals_found', int(signals_added))

        total_raw = r.hget('scanner:status', 'pairs_total')
        try:
            total = int(total_raw or 0)
        except Exception:
            total = 0

        # Cap progress and mark run complete when all submitted pairs are done.
        if total > 0 and int(updated) > total:
            r.hset('scanner:status', mapping={'pairs_done': total})
            updated = total

        if total > 0 and int(updated) >= total:
            r.hset('scanner:status', mapping={
                'status': 'idle',
                'completed_at': datetime.now(timezone.utc).isoformat(),
                'is_running': 0,
            })
    except Exception:
        pass


async def _resolve_crypto_pairs() -> list[str]:
    """
    Keep scanner pairs aligned with currently tradeable Binance futures symbols.
    """
    try:
        from engine.data_fetcher import BinanceDataFetcher

        fetcher = BinanceDataFetcher()
        try:
            active_symbols = set(await fetcher.get_active_futures_symbols())
        finally:
            await fetcher.close()

        filtered = [symbol for symbol in CRYPTO_PAIRS if symbol in active_symbols]
        if filtered:
            return filtered
        if active_symbols:
            return sorted(active_symbols)
    except Exception as exc:
        logger.warning(f"[SCANNER] Could not refresh active Binance symbols: {exc}")
    return list(CRYPTO_PAIRS)


@app.task(bind=True, name='workers.scanner_task.scan_market',
          max_retries=2, default_retry_delay=60)
def scan_market(self, market: str = 'crypto'):
    """
    Main scanner task — runs every 10 minutes via Celery Beat.
    Scans all pairs for the given market.
    """
    logger.info(f"[SCANNER] Starting {market.upper()} scan...")
    start_time = time.time()

    if market == 'crypto':
        pairs = _run_async(_resolve_crypto_pairs())
    else:
        if not _has_twelvedata_key():
            logger.warning("[SCANNER] FOREX scan skipped: TWELVEDATA_API_KEY is not configured.")
            return {
                'market': market,
                'pairs_submitted': 0,
                'errors': 0,
                'skipped': True,
                'reason': 'twelvedata_api_key_missing',
            }
        pairs = FOREX_PAIRS
    pairs, blocked_pairs = _filter_pairs_for_scanning(market, pairs)
    if blocked_pairs:
        logger.info(f"[SCANNER] {len(blocked_pairs)} {market} pairs skipped by health filter/manual policy")
    min_confidence = _get_scan_min_confidence(default=75)
    signals_found = 0
    errors = 0

    # Update scanner status in Redis
    try:
        import redis
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.hset('scanner:status', mapping={
            'market': market,
            'status': 'running',
            'is_running': 1,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'completed_at': '',
            'pairs_total': len(pairs),
            'pairs_done': 0,
            'signals_found': 0,
        })
    except Exception as e:
        logger.warning(f"Redis status update failed: {e}")

    # Process pairs in batches to avoid rate limits
    batch_size = 10
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i+batch_size]

        # Submit batch jobs
        for symbol in batch:
            try:
                scan_symbol.apply_async(
                    kwargs={
                        'symbol': symbol,
                        'market': market,
                        'min_confidence': min_confidence,
                    },
                    queue='scanner',
                    countdown=0,
                )
            except Exception as e:
                logger.error(f"Failed to submit scan for {symbol}: {e}")
                errors += 1

        # Small delay between batches to avoid overwhelming the API
        time.sleep(0.5)

    duration = time.time() - start_time
    logger.info(f"[SCANNER] {market.upper()} scan submitted {len(pairs)} pairs in {duration:.1f}s")

    return {
        'market': market,
        'pairs_submitted': len(pairs),
        'errors': errors,
        'duration_ms': int(duration * 1000),
    }


@app.task(bind=True, name='workers.scanner_task.scan_symbol',
          max_retries=3, default_retry_delay=30)
def scan_symbol(
    self,
    symbol: str,
    market: str = 'crypto',
    min_confidence: int = 75,
):
    """
    Scan a single symbol across all timeframes.
    Generates signals and stores in DB/Redis.
    """
    try:
        result = _run_async(_scan_symbol_async(symbol, market, min_confidence))
        return result
    except Exception as exc:
        logger.error(f"Error scanning {symbol}: {exc}")
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return {'symbol': symbol, 'error': str(exc), 'signals': 0}


async def _scan_symbol_async(
    symbol: str,
    market: str,
    min_confidence: int = 75,
) -> dict:
    """Async implementation of symbol scanning"""
    signals_generated = []
    candidate_signals = []
    fetcher = None

    try:
        from engine.data_fetcher import BinanceDataFetcher, ForexDataFetcher
        from engine.signal_generator import SignalGenerator

        fetcher = BinanceDataFetcher() if market == 'crypto' else ForexDataFetcher()
        generator = SignalGenerator()
        generator.MIN_CONFIDENCE = max(75, min(100, int(min_confidence or 75)))
        enabled_timeframes = _get_scan_timeframes()
        overtrading_limits = _get_overtrading_limits()

        # Fetch candles for all timeframes
        candles_by_tf = {}
        for tf in enabled_timeframes:
            try:
                candles = await fetcher.get_klines(symbol, tf, limit=200)
                if candles and len(candles) >= 50:
                    candles_by_tf[tf] = candles
            except Exception as e:
                logger.warning(f"Failed to fetch {symbol} {tf}: {e}")

        if not candles_by_tf:
            return {'symbol': symbol, 'market': market, 'signals': 0, 'error': 'No data'}

        # Cooldown TTL per timeframe — prevents re-firing the same
        # pair+direction+timeframe within the window (anti-spam).
        COOLDOWN_TTL: dict[str, int] = {
            '5m':  2700,    # 45 minutes
            '15m': 7200,    # 2 hours
            '1H':  21600,   # 6 hours
            '4H':  86400,   # 24 hours
            '1D':  172800,  # 48 hours
        }

        # Redis client for cooldown checks (sync, reused across TFs for this symbol)
        import redis as _redis_lib
        _r = _redis_lib.from_url(
            os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
            decode_responses=True,
        )

        # Generate signals for each timeframe
        for tf, candles in candles_by_tf.items():
            try:
                signal = generator.generate(
                    symbol=symbol,
                    market=market,
                    candles=candles,
                    timeframe=tf,
                    candles_by_tf=candles_by_tf,
                )

                if signal:
                    open_key = _open_signal_key(symbol, signal.direction, tf)
                    if _r.exists(open_key):
                        logger.debug(
                            f"[SCANNER] Open signal already exists for {symbol} {signal.direction} {tf}"
                        )
                        continue
                    # ── Anti-spam cooldown check ────────────────────────
                    # Skip if an identical direction+TF signal was recently fired
                    cooldown_key = f'signal:cooldown:{symbol}:{signal.direction}:{tf}'
                    if _r.exists(cooldown_key):
                        logger.debug(
                            f"[SCANNER] Cooldown active for {symbol} {signal.direction} {tf} — skipped"
                        )
                        continue
                    same_direction_minutes = overtrading_limits.get(
                        'repeated_signal_cooldown_minutes',
                        0,
                    )
                    same_direction_key = f'signal:cooldown:{symbol}:{signal.direction}'
                    if same_direction_minutes > 0 and _r.exists(same_direction_key):
                        logger.debug(
                            f"[SCANNER] Direction cooldown active for {symbol} {signal.direction} — skipped"
                        )
                        continue

                    candidate_signals.append({
                        'signal': signal,
                        'tf': tf,
                        'cooldown_key': cooldown_key,
                        'same_direction_key': same_direction_key,
                    })
            except Exception as e:
                logger.error(f"Error generating signal for {symbol} {tf}: {e}")

        candidate_signals.sort(
            key=lambda item: (
                float(getattr(item['signal'], 'ranking_score', 0.0) or 0.0),
                int(getattr(item['signal'], 'pwin_tp1', 0) or 0),
                int(getattr(item['signal'], 'setup_score', 0) or 0),
            ),
            reverse=True,
        )

        shortlisted = candidate_signals[:MAX_SIGNALS_PER_SYMBOL_SCAN]
        for item in shortlisted:
            signal = item['signal']
            reserved, reservation = _reserve_daily_signal_slot(
                _r,
                symbol,
                overtrading_limits,
            )
            if not reserved:
                logger.debug(
                    f"[SCANNER] Daily signal limit reached for {symbol} or global budget exhausted"
                )
                continue

            stored = await _store_signal(signal)
            if not stored:
                _release_daily_signal_slot(_r, reservation)
                continue

            ttl = COOLDOWN_TTL.get(item['tf'], 3600)
            _r.set(item['cooldown_key'], '1', ex=ttl)
            same_direction_minutes = overtrading_limits.get(
                'repeated_signal_cooldown_minutes',
                0,
            )
            if same_direction_minutes > 0:
                _r.set(
                    item['same_direction_key'],
                    '1',
                    ex=same_direction_minutes * 60,
                )

            signals_generated.append({
                'direction': signal.direction,
                'timeframe': signal.timeframe,
                'confidence': signal.confidence,
                'setup_score': getattr(signal, 'setup_score', None),
                'pwin_tp1': getattr(signal, 'pwin_tp1', None),
                'pwin_tp2': getattr(signal, 'pwin_tp2', None),
                'ranking_score': getattr(signal, 'ranking_score', None),
            })

            from workers.alert_task import send_signal_alerts
            send_signal_alerts.apply_async(
                kwargs={'signal_id': signal.id},
                queue='alerts',
                countdown=0,
            )

        # Cache candles in Redis for WS streaming
        try:
            import redis
            r = redis.from_url(
                os.getenv('REDIS_URL', 'redis://localhost:6379/0'),
                decode_responses=True,
            )
            for tf, candles in candles_by_tf.items():
                key = f'candles:{symbol}:{tf}'
                pipe = r.pipeline()
                pipe.delete(key)
                for candle in candles[-200:]:
                    pipe.rpush(key, json.dumps(candle, default=_json_default))
                pipe.expire(key, 3600 * 6)
                pipe.execute()
        except Exception:
            pass

        return {
            'symbol': symbol,
            'market': market,
            'signals': len(signals_generated),
            'signal_details': signals_generated,
        }

    except Exception as e:
        logger.error(f"Async scan error for {symbol}: {e}")
        return {'symbol': symbol, 'market': market, 'signals': 0, 'error': str(e)}
    finally:
        _update_scanner_progress(signals_added=len(signals_generated))
        if fetcher is not None:
            try:
                await fetcher.close()
            except Exception:
                pass


async def _store_signal(signal) -> bool:
    """Store generated signal in PostgreSQL and Redis"""
    try:
        import json, redis as redis_lib
        from decimal import Decimal

        # Store in Redis for immediate access
        r = redis_lib.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

        signal_dict = {
            'id': signal.id,
            'symbol': signal.symbol,
            'market': signal.market,
            'direction': signal.direction,
            'timeframe': signal.timeframe,
            'confidence': signal.confidence,
            'setup_score': getattr(signal, 'setup_score', None),
            'pwin_tp1': getattr(signal, 'pwin_tp1', None),
            'pwin_tp2': getattr(signal, 'pwin_tp2', None),
            'ranking_score': getattr(signal, 'ranking_score', None),
            'entry': signal.entry,
            'entry_zone_low': getattr(signal, 'entry_zone_low', None),
            'entry_zone_high': getattr(signal, 'entry_zone_high', None),
            'entry_type': getattr(signal, 'entry_type', None),
            'stop_loss': signal.stop_loss,
            'invalidation_price': getattr(signal, 'invalidation_price', None),
            'take_profit_1': signal.take_profit_1,
            'take_profit_2': signal.take_profit_2,
            'take_profit_3': signal.take_profit_3,
            'rr_ratio': signal.rr_ratio,
            'rr_tp1': getattr(signal, 'rr_tp1', None) or _calc_rr(signal.entry, signal.stop_loss, signal.take_profit_1),
            'rr_tp2': getattr(signal, 'rr_tp2', None) or _calc_rr(signal.entry, signal.stop_loss, signal.take_profit_2),
            'confidence_band': signal.confidence_band,
            'top_confluences': signal.top_confluences[:5],
            'status': getattr(signal, 'status', 'CREATED'),
            'fired_at': signal.fired_at,
            'valid_until': getattr(signal, 'valid_until', None),
            'expires_at': getattr(signal, 'expires_at', None),
        }

        # Store as latest signal for symbol
        signal_payload = json.dumps(signal_dict, default=_json_default)
        r.set(f'signal:latest:{signal.symbol}:{signal.timeframe}',
              signal_payload, ex=86400)
        r.set(f'signal:id:{signal.id}', signal_payload, ex=86400)
        r.set(_open_signal_key(signal.symbol, signal.direction, signal.timeframe), signal.id, ex=86400 * 7)

        # Add to active signals sorted set (score = ranking score / calibrated quality)
        active_score = float(getattr(signal, 'ranking_score', None) or signal.confidence or 0)
        r.zadd('signals:active', {signal_payload: active_score})
        r.expire('signals:active', 86400)

        # New canonical cache keys used by API (/signals/live etc).
        r.set(f'signal:{signal.symbol}', signal_payload, ex=86400)
        r.zadd('active_signals', {signal.symbol: active_score})
        r.expire('active_signals', 86400)

        # Publish for WebSocket broadcast
        r.publish('signals:live', signal_payload)

        # Store in PostgreSQL (using sync SQLAlchemy for Celery)
        try:
            from sqlalchemy import create_engine, text
            import json as json_lib
            from datetime import datetime as dt

            db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
            if db_url:
                engine = create_engine(db_url)
                with engine.connect() as conn:
                    pair_row = conn.execute(
                        text("SELECT id FROM pairs WHERE symbol = :symbol LIMIT 1"),
                        {"symbol": signal.symbol},
                    ).mappings().first()
                    if not pair_row:
                        market = signal.market if signal.market in ("crypto", "forex") else (
                            "crypto" if signal.symbol.endswith("USDT") else "forex"
                        )
                        exchange = "binance" if market == "crypto" else "otc"
                        quote_asset = "USDT" if signal.symbol.endswith("USDT") else signal.symbol[-3:]
                        base_asset = signal.symbol[:-len(quote_asset)] if len(signal.symbol) > len(quote_asset) else signal.symbol

                        pair_row = conn.execute(
                            text(
                                """
                                INSERT INTO pairs (
                                    id, symbol, market, exchange, base_asset, quote_asset,
                                    is_active, precision_price, precision_qty, min_qty
                                ) VALUES (
                                    uuid_generate_v4(), :symbol, :market, :exchange, :base_asset, :quote_asset,
                                    true, 8, 3, 0.001
                                )
                                ON CONFLICT (symbol) DO UPDATE SET symbol = EXCLUDED.symbol
                                RETURNING id
                                """
                            ),
                            {
                                "symbol": signal.symbol,
                                "market": market,
                                "exchange": exchange,
                                "base_asset": base_asset,
                                "quote_asset": quote_asset,
                            },
                        ).mappings().first()
                        if not pair_row:
                            pair_row = conn.execute(
                                text("SELECT id FROM pairs WHERE symbol = :symbol LIMIT 1"),
                                {"symbol": signal.symbol},
                            ).mappings().first()
                        if not pair_row:
                            logger.warning(
                                f"DB store skipped for {signal.symbol}: unable to create/find pair id."
                            )
                            return True

                    expires_at = None
                    if getattr(signal, "expires_at", None):
                        try:
                            expires_at = dt.fromisoformat(
                                str(signal.expires_at).replace("Z", "+00:00")
                            )
                        except Exception:
                            expires_at = None

                    valid_until = None
                    if getattr(signal, "valid_until", None):
                        try:
                            valid_until = dt.fromisoformat(
                                str(signal.valid_until).replace("Z", "+00:00")
                            )
                        except Exception:
                            valid_until = None

                    conn.execute(text("""
                        INSERT INTO signals (
                            id, pair_id, symbol, market, direction, timeframe, confidence,
                            entry, entry_zone_low, entry_zone_high, entry_type,
                            stop_loss, invalidation_price, take_profit_1, take_profit_2, take_profit_3,
                            rr_ratio, raw_score, max_possible_score, status,
                            setup_score, pwin_tp1, pwin_tp2, ranking_score,
                            score_breakdown, ict_zones, mtf_analysis, candle_snapshot,
                            fired_at, valid_until, expires_at, alert_sent
                        ) VALUES (
                            :id, :pair_id, :symbol, :market, :direction, :timeframe, :confidence,
                            :entry, :entry_zone_low, :entry_zone_high, :entry_type,
                            :stop_loss, :invalidation_price, :tp1, :tp2, :tp3,
                            :rr, :raw_score, :max_score, :status,
                            :setup_score, :pwin_tp1, :pwin_tp2, :ranking_score,
                            :breakdown, :ict_zones, :mtf, :snapshot,
                            :fired_at, :valid_until, :expires_at, false
                        )
                        ON CONFLICT (id) DO NOTHING
                    """), {
                        'id': signal.id,
                        'pair_id': pair_row["id"],
                        'symbol': signal.symbol,
                        'market': signal.market,
                        'direction': signal.direction,
                        'timeframe': signal.timeframe,
                        'confidence': signal.confidence,
                        'entry': signal.entry,
                        'entry_zone_low': getattr(signal, 'entry_zone_low', None),
                        'entry_zone_high': getattr(signal, 'entry_zone_high', None),
                        'entry_type': getattr(signal, 'entry_type', None),
                        'stop_loss': signal.stop_loss,
                        'invalidation_price': getattr(signal, 'invalidation_price', None),
                        'tp1': signal.take_profit_1,
                        'tp2': signal.take_profit_2,
                        'tp3': signal.take_profit_3,
                        'rr': signal.rr_ratio,
                        'raw_score': signal.raw_score,
                        'max_score': signal.max_possible_score,
                        'status': getattr(signal, 'status', 'CREATED'),
                        'setup_score': getattr(signal, 'setup_score', None),
                        'pwin_tp1': getattr(signal, 'pwin_tp1', None),
                        'pwin_tp2': getattr(signal, 'pwin_tp2', None),
                        'ranking_score': getattr(signal, 'ranking_score', None),
                        'breakdown': json_lib.dumps(signal.score_breakdown, default=_json_default),
                        'ict_zones': json_lib.dumps(signal.ict_zones, default=_json_default),
                        'mtf': json_lib.dumps(signal.mtf_analysis, default=_json_default),
                        'snapshot': json_lib.dumps(signal.candle_snapshot, default=_json_default),
                        'fired_at': dt.fromisoformat(str(signal.fired_at).replace("Z", "+00:00")),
                        'valid_until': valid_until,
                        'expires_at': expires_at,
                    })
                    conn.commit()
        except Exception as db_err:
            logger.warning(f"DB store failed for {signal.symbol}: {db_err}")

        return True

    except Exception as e:
        logger.error(f"Store signal failed: {e}")
        return False


@app.task(name='workers.scanner_task.update_signal_statuses')
def update_signal_statuses():
    """
    Advance lifecycle for open signals.
    """
    try:
        import redis, json
        import httpx

        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))

        # Get all active signals from Redis
        active_raw = r.zrange('signals:active', 0, -1)

        for raw in active_raw:
            try:
                signal = json.loads(raw)
                symbol = signal.get('symbol')

                # Get current price
                try:
                    response = httpx.get(
                        f"https://fapi.binance.com/fapi/v1/ticker/price",
                        params={'symbol': symbol},
                        timeout=5
                    )
                    current_price = float(response.json().get('price', 0))
                except Exception:
                    continue

                if current_price <= 0:
                    continue

                direction = signal.get('direction')
                entry = float(signal.get('entry', 0))
                zone_low = float(signal.get('entry_zone_low') or entry or 0)
                zone_high = float(signal.get('entry_zone_high') or entry or 0)
                invalidation = float(signal.get('invalidation_price') or signal.get('stop_loss') or 0)
                sl = float(signal.get('stop_loss', 0))
                tp1 = float(signal.get('take_profit_1', 0))
                tp2 = float(signal.get('take_profit_2', tp1))
                status_now = str(signal.get('status') or 'CREATED')

                new_status = None
                is_in_zone = zone_low > 0 and zone_high >= zone_low and zone_low <= current_price <= zone_high
                zone_width = max(abs(zone_high - zone_low), abs(entry - sl) * 0.25, entry * 0.0005 if entry else 0)
                near_zone = zone_low > 0 and (zone_low - zone_width) <= current_price <= (zone_high + zone_width)

                if status_now == 'CREATED':
                    if direction == 'LONG' and invalidation > 0 and current_price < invalidation:
                        new_status = 'INVALIDATED'
                    elif direction == 'SHORT' and invalidation > 0 and current_price > invalidation:
                        new_status = 'INVALIDATED'
                    elif is_in_zone:
                        new_status = 'FILLED'
                    elif near_zone:
                        new_status = 'ARMED'
                elif status_now == 'ARMED':
                    if direction == 'LONG' and invalidation > 0 and current_price < invalidation:
                        new_status = 'INVALIDATED'
                    elif direction == 'SHORT' and invalidation > 0 and current_price > invalidation:
                        new_status = 'INVALIDATED'
                    elif is_in_zone:
                        new_status = 'FILLED'
                elif status_now == 'FILLED':
                    if direction == 'LONG':
                        if current_price >= tp2:
                            new_status = 'TP2_REACHED'
                        elif current_price >= tp1:
                            new_status = 'TP1_REACHED'
                        elif current_price <= sl:
                            new_status = 'STOPPED'
                    elif direction == 'SHORT':
                        if current_price <= tp2:
                            new_status = 'TP2_REACHED'
                        elif current_price <= tp1:
                            new_status = 'TP1_REACHED'
                        elif current_price >= sl:
                            new_status = 'STOPPED'

                # ── Expiry check ────────────────────────────────────────
                if not new_status:
                    check_key = 'valid_until' if status_now in ('CREATED', 'ARMED') else 'expires_at'
                    cutoff_raw = signal.get(check_key) or signal.get('expires_at')
                    if cutoff_raw:
                        try:
                            from datetime import datetime as _dt, timezone as _tz
                            cutoff_dt = _dt.fromisoformat(
                                str(cutoff_raw).replace('Z', '+00:00')
                            )
                            if cutoff_dt.tzinfo is None:
                                cutoff_dt = cutoff_dt.replace(tzinfo=_tz.utc)
                            if _dt.now(_tz.utc) > cutoff_dt:
                                new_status = 'EXPIRED'
                        except Exception:
                            pass

                if new_status:
                    # Update in DB
                    try:
                        from sqlalchemy import create_engine, text
                        db_url = os.getenv('DATABASE_URL', '').replace('+asyncpg', '')
                        if db_url:
                            engine = create_engine(db_url)
                            with engine.connect() as conn:
                                is_terminal = new_status in {'TP1_REACHED', 'TP2_REACHED', 'STOPPED', 'EXPIRED', 'INVALIDATED'}
                                if not is_terminal:
                                    conn.execute(text("""
                                        UPDATE signals
                                        SET status = :status
                                        WHERE id = :id AND status IN ('CREATED', 'ARMED', 'FILLED', 'active')
                                    """), {'status': new_status, 'id': signal.get('id')})
                                elif new_status == 'EXPIRED':
                                    conn.execute(text("""
                                        UPDATE signals
                                        SET status = 'EXPIRED', closed_at = NOW()
                                        WHERE id = :id AND status IN ('CREATED', 'ARMED', 'FILLED', 'active')
                                    """), {'id': signal.get('id')})
                                else:
                                    pnl = ((current_price - entry) / entry * 100) if direction == 'LONG' else ((entry - current_price) / entry * 100)
                                    conn.execute(text("""
                                        UPDATE signals
                                        SET status = :status, close_price = :price,
                                            pnl_pct = :pnl, closed_at = NOW()
                                        WHERE id = :id AND status IN ('CREATED', 'ARMED', 'FILLED', 'active')
                                    """), {'status': new_status, 'price': current_price,
                                           'pnl': round(pnl, 2), 'id': signal.get('id')})
                                conn.commit()

                        if new_status in {'TP1_REACHED', 'TP2_REACHED', 'STOPPED', 'EXPIRED', 'INVALIDATED'}:
                            r.zrem('signals:active', raw)
                            r.zrem('active_signals', symbol)
                            r.delete(f'signal:{symbol}')
                            signal_id = signal.get('id')
                            if signal_id:
                                r.delete(f'signal:id:{signal_id}')
                            r.delete(_open_signal_key(symbol, direction, signal.get('timeframe', '')))
                        else:
                            signal['status'] = new_status
                            refreshed = json.dumps(signal)
                            r.zrem('signals:active', raw)
                            r.zadd('signals:active', {refreshed: signal.get('confidence', 0)})
                            r.set(f'signal:{symbol}', refreshed, ex=86400)
                            r.set(f'signal:id:{signal.get("id")}', refreshed, ex=86400)

                        logger.info(f"Signal {signal.get('id')} -> {new_status} at {current_price}")
                    except Exception as e:
                        logger.error(f"Status update DB error: {e}")

            except Exception as e:
                logger.warning(f"Status check error: {e}")

    except Exception as e:
        logger.error(f"update_signal_statuses error: {e}")


@app.task(name='workers.scanner_task.health_check')
def health_check():
    """Ping task to verify workers are alive"""
    import redis
    try:
        r = redis.from_url(os.getenv('REDIS_URL', 'redis://localhost:6379/0'))
        r.set('scanner:last_heartbeat', datetime.now(timezone.utc).isoformat(), ex=120)
        return {'status': 'ok', 'timestamp': datetime.now(timezone.utc).isoformat()}
    except Exception as e:
        return {'status': 'error', 'error': str(e)}
